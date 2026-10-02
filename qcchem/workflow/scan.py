"""1D scan workflow orchestration."""

from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path

import numpy as np

from qcchem.core import BaselineDescriptorSummary, EvidenceSummary, RegistryEntry, ScanArtifactPaths, ScanPointResult, ScanResult, StudySummary
from qcchem.core.evidence import build_scan_evidence_summary, build_scan_point_evidence_summary
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.io.scan_config import load_scan_spec
from qcchem.io.checkpoint import read_checkpoint, write_checkpoint
from qcchem.reporting import write_result_json
from qcchem.reporting.aggregate import write_aggregate_report
from qcchem.workflow.common import clone_spec_with_overrides, prepare_clean_output_root, resolve_artifact_root
from qcchem.workflow.computation_control import (
    check_control, computation_identity, computation_locks, run_input_paths,
    validate_recovery_identity,
)
from qcchem.workflow.continuity import (
    attach_initial_point_candidate,
    ContinuityRecord,
    build_continuity_record,
    build_initial_point_candidate,
    summarize_initial_point_continuity,
)
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.runner import run_spec
from qcchem.workflow.workflow_control import file_manifest, verify_manifest

SCHEMA_VERSION = "qcchem.scan.v0.3-alpha"


def _prepare_scan_artifacts(root: Path, *, overwrite: bool) -> ScanArtifactPaths:
    resolved_root = prepare_clean_output_root(root, workflow_name="Scan", overwrite=overwrite)
    return ScanArtifactPaths(
        root=resolved_root,
        result_json=resolved_root / "scan_result.json",
        report_markdown=resolved_root / "scan_report.md",
        scan_table_csv=resolved_root / "scan_table.csv",
        registry_json=resolved_root / "registry.json",
    )


def _apply_bond_distance(spec, atom_indices: tuple[int, int], value: float, axis: tuple[float, float, float]) -> None:
    vector = np.asarray(axis, dtype=float)
    norm = float(np.linalg.norm(vector))
    if norm <= 1.0e-12:
        raise ValueError("Scan axis must be non-zero.")
    direction = vector / norm
    anchor = np.asarray(spec.molecule.geometry[atom_indices[0]].coords, dtype=float)
    target = anchor + direction * value
    spec.molecule.geometry[atom_indices[1]].coords = (float(target[0]), float(target[1]), float(target[2]))


def run_scan_from_spec(
    spec,
    *,
    source_config: str,
    output_dir: Path | None = None,
    overwrite: bool = False,
    control_check=None,
    resume_from: Path | None = None,
) -> ScanResult:
    """Run or resume a scan into a dedicated new bundle."""
    from qcchem.workflow.common import guard_output_path_symlinks

    root = resolve_artifact_root(Path(output_dir or Path("artifacts") / spec.name))
    guard_output_path_symlinks(root, workflow_name="Scan")
    root = root.resolve()
    source = Path(resume_from).expanduser() if resume_from is not None else None
    if source is not None:
        guard_output_path_symlinks(source, workflow_name="Scan recovery")
        source = source.resolve()
    with computation_locks(root, source):
        check_control(control_check)
        base = load_run_spec(spec.base_config)
        if source is not None and (base.backend.runtime.enabled or base.backend.kind.strip().lower() not in {
                "statevector", "shot_estimator", "aer_shot_estimator"}):
            raise ValueError("Scan recovery supports local statevector/shot_estimator with runtime disabled.")
        identity = computation_identity(spec, run_input_paths(base, str(spec.base_config)) +
                                        ([Path(source_config)] if Path(source_config).is_file() else []))
        state = None
        source_manifest = None
        if source is not None:
            state = read_checkpoint(source / "scan_checkpoint.json", schema="qcchem.scan_checkpoint.v1")
            validate_recovery_identity(state, identity)
            if root.exists() and (not root.is_dir() or any(root.iterdir())):
                raise FileExistsError("Scan recovery requires an empty new output directory.")
            try:
                if state["status"] not in {"running", "interrupted", "completed"} or not isinstance(state["points"], list):
                    raise ValueError("invalid scan checkpoint status or point list")
                active = state.get("active_point")
                if active is not None and (not isinstance(active, dict) or type(active.get("index")) is not int
                        or active["index"] != len(state["points"]) or not isinstance(active.get("artifact_root"), str)):
                    raise ValueError("invalid active scan point")
                if state["status"] == "completed" and (active is not None or len(state["points"]) != len(spec.parameter.values)):
                    raise ValueError("incomplete point list in completed scan checkpoint")
                for index, point in enumerate(state["points"]):
                    if (point["summary"]["parameter_value"] != spec.parameter.values[index]
                            or point["summary"]["point_label"] != f"point_{index:02d}_{spec.parameter.values[index]:.3f}"):
                        raise ValueError("scan point order changed")
                    verify_manifest(point["manifest"], label=f"scan point {index}")
                if len(state["points"]) > len(spec.parameter.values):
                    raise ValueError("too many scan points")
            except (KeyError, TypeError, IndexError) as exc:
                raise ValueError("Invalid scan checkpoint fields.") from exc
            source_manifest = file_manifest([source / "scan_checkpoint.json"])
        result = _run_scan(
            spec, source_config=source_config, output_dir=root, overwrite=overwrite,
            control_check=control_check, checkpoint_state=state, checkpoint_identity=identity,
            parameter_unit=base.molecule.unit if spec.parameter.kind == "bond_distance" else None,
        )
        verify_manifest(identity["inputs"], label="scan inputs")
        if source_manifest is not None:
            verify_manifest(source_manifest, label="scan recovery checkpoint")
        return result


def _run_scan(
    spec, *, source_config: str, output_dir: Path | None = None, overwrite: bool = False,
    control_check=None, checkpoint_state=None, checkpoint_identity=None,
    parameter_unit=None,
) -> ScanResult:
    scan_root = output_dir or Path("artifacts") / spec.name
    artifacts = _prepare_scan_artifacts(Path(scan_root), overwrite=overwrite)
    points_root = artifacts.root / "points"
    points_root.mkdir(parents=True, exist_ok=True)

    point_results: list[ScanPointResult] = []
    registry_entries = []
    continuity_records = []
    state = deepcopy(checkpoint_state) if checkpoint_state else {
        "schema_version": "qcchem.scan_checkpoint.v1", "identity": checkpoint_identity,
        "points": [], "active_point": None,
    }
    state.update(scan_name=spec.name, parameter_name=spec.parameter.name,
                 parameter_values=list(spec.parameter.values), parameter_unit=parameter_unit)
    prior_active = state.get("active_point")
    state["status"] = "running"
    checkpoint_path = artifacts.root / "scan_checkpoint.json"
    write_checkpoint(checkpoint_path, state)
    for saved in state["points"]:
        summary = dict(saved["summary"])
        summary["run_artifact_root"] = Path(summary["run_artifact_root"])
        if summary.get("evidence_summary"):
            summary["evidence_summary"]["primary_baseline"] = BaselineDescriptorSummary(**summary["evidence_summary"]["primary_baseline"])
            summary["evidence_summary"] = EvidenceSummary(**summary["evidence_summary"])
        point_results.append(ScanPointResult(**summary))
        entry = dict(saved["registry_entry"])
        entry["artifact_root"] = Path(entry["artifact_root"])
        registry_entries.append(RegistryEntry(**entry))
        if saved.get("continuity"):
            continuity_records.append(ContinuityRecord(**saved["continuity"]))

    for index, value in enumerate(spec.parameter.values):
        if index < len(point_results):
            continue
        check_control(control_check)
        point_spec = load_run_spec(spec.base_config)
        if spec.policy_name:
            point_spec.policy.name = spec.policy_name
        if spec.parameter.kind == "bond_distance":
            _apply_bond_distance(point_spec, spec.parameter.atom_indices, value, spec.parameter.axis)
        elif spec.parameter.kind == "config_override":
            if not spec.parameter.target:
                raise ValueError("config_override scan parameters require a target dotted path.")
            point_spec = clone_spec_with_overrides(point_spec, {spec.parameter.target: value})
        else:
            raise ValueError(f"Unsupported scan parameter kind: {spec.parameter.kind}")
        point_label = f"point_{index:02d}_{value:.3f}"
        initial_point_candidate = build_initial_point_candidate(
            continuity_records,
            spec.continuity,
            target_parameter_value=float(value),
        )
        attach_initial_point_candidate(point_spec, initial_point_candidate)
        prior_root = None
        if prior_active and prior_active.get("index") == index:
            prior_root = Path(prior_active["artifact_root"])
            if not (prior_root / "run_checkpoint.json").is_file():
                prior_root = Path(prior_active["resume_from"]) if prior_active.get("resume_from") else None
            if str(point_spec.solver.kind).lower() != "vqe":
                prior_root = None
        state["active_point"] = {"index": index, "artifact_root": str(points_root / point_label),
                                 "resume_from": str(prior_root) if prior_root else None}
        write_checkpoint(checkpoint_path, state)
        try:
            result = run_spec(
                point_spec,
                source_config=str(spec.base_config),
                output_dir=points_root / point_label,
                control_check=control_check, resume_from=prior_root,
            )
        except BaseException as exc:
            state["status"] = "interrupted"
            try:
                write_checkpoint(checkpoint_path, state)
            except (OSError, ValueError, TypeError) as failure:
                if hasattr(exc, "add_note"):
                    exc.add_note(f"Could not publish the final scan checkpoint: {failure}")
            raise
        continuity_summary = summarize_initial_point_continuity(result)
        point_results.append(
            ScanPointResult(
                point_label=point_label,
                parameter_value=float(value),
                total_energy=result.energy.total_energy,
                verification_status=result.verification_status,
                run_artifact_root=result.artifacts.root,
                exact_error=result.benchmark.absolute_error,
                evidence_summary=build_scan_point_evidence_summary(
                    {
                        "point_label": point_label,
                        "parameter_value": float(value),
                        "total_energy": result.energy.total_energy,
                        "verification_status": result.verification_status,
                        "exact_error": result.benchmark.absolute_error,
                    },
                    parameter_name=spec.parameter.name,
                ),
                initial_point_reused=continuity_summary["initial_point_reused"],
                initial_point_source=continuity_summary["initial_point_source"],
                initial_point_strategy=continuity_summary["initial_point_strategy"],
                history_sources=continuity_summary["history_sources"],
                fallback_reason=continuity_summary["fallback_reason"],
                iterations=continuity_summary["iterations"],
                evaluations=continuity_summary["evaluations"],
                parameter_count=continuity_summary["parameter_count"],
            )
        )
        continuity_record = build_continuity_record(
            result,
            source_label=point_label,
            parameter_value=float(value),
        )
        if continuity_record is not None:
            continuity_records.append(continuity_record)
        registry_entries.append(
            make_registry_entry(
                name=point_label,
                kind="scan_point",
                status=result.verification_status,
                artifact_root=result.artifacts.root,
                source=str(spec.base_config),
                tags=spec.tags,
            )
        )
        state["points"].append({
            "summary": to_primitive(point_results[-1]),
            "registry_entry": to_primitive(registry_entries[-1]),
            "continuity": to_primitive(continuity_record) if continuity_record else None,
            "manifest": file_manifest([result.artifacts.root]),
        })
        state["active_point"] = None
        write_checkpoint(checkpoint_path, state)
        check_control(control_check)

    for index, saved in enumerate(state["points"]):
        verify_manifest(saved["manifest"], label=f"scan point {index}")
    check_control(control_check)

    with artifacts.scan_table_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                spec.parameter.name,
                "total_energy",
                "verification_status",
                "absolute_error",
                "initial_point_reused",
                "initial_point_source",
                "initial_point_strategy",
                "candidate_source",
                "effective_strategy",
                "history_sources",
                "fallback_reason",
                "iterations",
                "evaluations",
                "parameter_count",
            ]
        )
        for point in point_results:
            writer.writerow(
                [
                    point.parameter_value,
                    point.total_energy,
                    point.verification_status,
                    point.exact_error,
                    point.initial_point_reused,
                    point.initial_point_source,
                    point.initial_point_strategy,
                    point.initial_point_source,
                    point.initial_point_strategy,
                    ";".join(point.history_sources),
                    point.fallback_reason,
                    point.iterations,
                    point.evaluations,
                    point.parameter_count,
                ]
            )

    status_counts: dict[str, int] = {}
    for point in point_results:
        status_counts[point.verification_status] = status_counts.get(point.verification_status, 0) + 1

    registry_entries.append(
        make_registry_entry(
            name=spec.name,
            kind="scan",
            status="validated" if all(point.verification_status == "validated" for point in point_results) else "exploratory",
            artifact_root=artifacts.root,
            source=source_config,
            tags=spec.tags,
        )
    )

    result = ScanResult(
        schema_version=SCHEMA_VERSION,
        scan_name=spec.name,
        parameter_name=spec.parameter.name,
        parameter_unit=parameter_unit,
        summary=StudySummary(total_runs=len(point_results), status_counts=status_counts, comparison_axes=[spec.parameter.name]),
        points=point_results,
        registry_entries=registry_entries,
        artifacts=artifacts,
    )
    result.evidence_summary = build_scan_evidence_summary(to_primitive(result))
    write_result_json(result, artifacts.result_json)
    write_registry(registry_entries, artifacts.registry_json)
    write_aggregate_report(result, artifacts.report_markdown, kind="scan")
    state["status"] = "completed"
    write_checkpoint(checkpoint_path, state)
    return result


def run_scan_from_config(
    path: Path, output_dir: Path | None = None, *, overwrite: bool = False,
    control_check=None, resume_from: Path | None = None,
) -> ScanResult:
    """Load and run a scan configuration."""
    spec = load_scan_spec(path)
    return run_scan_from_spec(spec, source_config=str(path), output_dir=output_dir, overwrite=overwrite,
                              control_check=control_check, resume_from=resume_from)
