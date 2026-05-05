"""Study workflow orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path

from qcchem.core import RunRecord, StudyArtifactPaths, StudyResult, StudySummary
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.io.study_config import load_study_spec
from qcchem.reporting import write_result_json
from qcchem.reporting.aggregate import write_aggregate_report
from qcchem.core.evidence import build_study_evidence_summary
from qcchem.workflow.common import clone_spec_with_overrides, resolve_artifact_root
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.runner import run_spec

SCHEMA_VERSION = "qcchem.study.v0.3-alpha"


def _prepare_study_artifacts(root: Path, overwrite: bool) -> StudyArtifactPaths:
    resolved_root = resolve_artifact_root(root)
    if resolved_root.exists() and overwrite:
        shutil.rmtree(resolved_root)
    resolved_root.mkdir(parents=True, exist_ok=True)
    return StudyArtifactPaths(
        root=resolved_root,
        study_result_json=resolved_root / "study_result.json",
        study_report_markdown=resolved_root / "study_report.md",
        registry_json=resolved_root / "registry.json",
    )


def run_study_from_spec(spec, *, source_config: str, output_dir: Path | None = None) -> StudyResult:
    """Run a study from an already-parsed StudySpec."""
    study_root = output_dir or Path("artifacts") / spec.name
    artifacts = _prepare_study_artifacts(Path(study_root), overwrite=True)

    run_records: list[RunRecord] = []
    registry_entries = []
    runs_root = artifacts.root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    for run_entry in spec.runs:
        run_spec_obj = load_run_spec(run_entry.config)
        if spec.policy_name:
            run_spec_obj.policy.name = spec.policy_name
        if run_entry.overrides:
            run_spec_obj = clone_spec_with_overrides(run_spec_obj, run_entry.overrides)
        result = run_spec(
            run_spec_obj,
            source_config=str(run_entry.config),
            output_dir=runs_root / run_entry.name,
        )
        run_records.append(
            RunRecord(
                name=run_entry.name,
                source_config=str(run_entry.config),
                artifact_root=result.artifacts.root,
                verification_status=result.verification_status,
                mapping_kind=result.mapping.kind,
                backend_kind=result.backend.kind,
                policy_name=result.execution_policy.name,
                total_energy=result.energy.total_energy,
                absolute_error=result.benchmark.absolute_error,
                tags=run_entry.tags,
                evidence_summary=result.evidence_summary,
            )
        )
        registry_entries.append(
            make_registry_entry(
                name=run_entry.name,
                kind="run",
                status=result.verification_status,
                artifact_root=result.artifacts.root,
                source=str(run_entry.config),
                tags=run_entry.tags,
            )
        )

    status_counts: dict[str, int] = {}
    for item in run_records:
        status_counts[item.verification_status] = status_counts.get(item.verification_status, 0) + 1

    study_status = "validated" if all(item.verification_status == "validated" for item in run_records) else "exploratory"
    registry_entries.append(
        make_registry_entry(
            name=spec.name,
            kind="study",
            status=study_status,
            artifact_root=artifacts.root,
            source=source_config,
            tags=spec.tags,
        )
    )

    result = StudyResult(
        schema_version=SCHEMA_VERSION,
        study_name=spec.name,
        description=spec.description,
        summary=StudySummary(
            total_runs=len(run_records),
            status_counts=status_counts,
            comparison_axes=["backend.kind", "mapping.kind", "policy.name"],
        ),
        run_records=run_records,
        registry_entries=registry_entries,
        artifacts=artifacts,
    )
    result.evidence_summary = build_study_evidence_summary(to_primitive(result))
    write_result_json(result, artifacts.study_result_json)
    write_registry(registry_entries, artifacts.registry_json)
    write_aggregate_report(result, artifacts.study_report_markdown, kind="study")
    return result


def run_study_from_config(path: Path, output_dir: Path | None = None) -> StudyResult:
    """Load and run a study configuration."""
    spec = load_study_spec(path)
    return run_study_from_spec(spec, source_config=str(path), output_dir=output_dir)
