"""1D scan workflow orchestration."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import numpy as np

from qcchem.core import ScanArtifactPaths, ScanPointResult, ScanResult, StudySummary
from qcchem.core.evidence import build_scan_evidence_summary, build_scan_point_evidence_summary
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.io.scan_config import load_scan_spec
from qcchem.reporting import write_result_json
from qcchem.reporting.aggregate import write_aggregate_report
from qcchem.workflow.common import clone_spec_with_overrides, resolve_artifact_root
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.runner import run_spec

SCHEMA_VERSION = "qcchem.scan.v0.3-alpha"


def _prepare_scan_artifacts(root: Path) -> ScanArtifactPaths:
    resolved_root = resolve_artifact_root(root)
    if resolved_root.exists():
        shutil.rmtree(resolved_root)
    resolved_root.mkdir(parents=True, exist_ok=True)
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


def run_scan_from_spec(spec, *, source_config: str, output_dir: Path | None = None) -> ScanResult:
    """Run a 1D scan from an already-parsed ScanSpec."""
    scan_root = output_dir or Path("artifacts") / spec.name
    artifacts = _prepare_scan_artifacts(Path(scan_root))
    points_root = artifacts.root / "points"
    points_root.mkdir(parents=True, exist_ok=True)

    point_results: list[ScanPointResult] = []
    registry_entries = []

    for index, value in enumerate(spec.parameter.values):
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
        result = run_spec(
            point_spec,
            source_config=str(spec.base_config),
            output_dir=points_root / point_label,
        )
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
            )
        )
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

    with artifacts.scan_table_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([spec.parameter.name, "total_energy", "verification_status", "absolute_error"])
        for point in point_results:
            writer.writerow([point.parameter_value, point.total_energy, point.verification_status, point.exact_error])

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
        summary=StudySummary(total_runs=len(point_results), status_counts=status_counts, comparison_axes=[spec.parameter.name]),
        points=point_results,
        registry_entries=registry_entries,
        artifacts=artifacts,
    )
    result.evidence_summary = build_scan_evidence_summary(to_primitive(result))
    write_result_json(result, artifacts.result_json)
    write_registry(registry_entries, artifacts.registry_json)
    write_aggregate_report(result, artifacts.report_markdown, kind="scan")
    return result


def run_scan_from_config(path: Path, output_dir: Path | None = None) -> ScanResult:
    """Load and run a scan configuration."""
    spec = load_scan_spec(path)
    return run_scan_from_spec(spec, source_config=str(path), output_dir=output_dir)
