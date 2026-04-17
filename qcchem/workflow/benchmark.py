"""Benchmark-suite workflow orchestration."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

from qcchem.chem import build_electronic_structure_context
from qcchem.core import (
    BenchmarkArtifactPaths,
    BenchmarkCaseResult,
    BenchmarkSuiteResult,
    BenchmarkSuiteSummary,
    NoiseModelSpec,
)
from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.io.config import load_run_spec
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.reporting import write_result_json
from qcchem.reporting.aggregate import write_aggregate_report, write_hardware_calibration_report
from qcchem.solvers import ExactDiagonalizationSolver
from qcchem.workflow.common import clone_spec_with_overrides, resolve_artifact_root
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.runner import run_spec

SCHEMA_VERSION = "qcchem.benchmark.v0.4-alpha"


def _prepare_benchmark_artifacts(root: Path) -> BenchmarkArtifactPaths:
    resolved_root = resolve_artifact_root(root)
    if resolved_root.exists():
        shutil.rmtree(resolved_root)
    resolved_root.mkdir(parents=True, exist_ok=True)
    return BenchmarkArtifactPaths(
        root=resolved_root,
        result_json=resolved_root / "benchmark_result.json",
        report_markdown=resolved_root / "benchmark_report.md",
        registry_json=resolved_root / "registry.json",
    )


def _runtime_evidence_status_from_submission(runtime_submission: dict[str, Any] | None) -> str:
    if not runtime_submission:
        return "none"
    if runtime_submission.get("submitted") and runtime_submission.get("succeeded"):
        return "retrieved_result"
    if runtime_submission.get("submitted"):
        return "submitted"
    if runtime_submission.get("attempted"):
        return "runtime_attempt"
    return "none"


def _runtime_submission_status_from_submission(runtime_submission: dict[str, Any] | None) -> str | None:
    if not runtime_submission:
        return None
    if runtime_submission.get("failure_category"):
        return str(runtime_submission["failure_category"])
    if runtime_submission.get("submitted") and runtime_submission.get("succeeded"):
        return "succeeded"
    if runtime_submission.get("submitted"):
        return "submitted"
    if runtime_submission.get("attempted"):
        return "attempted"
    return None


def _runtime_returned_shots(runtime_submission: dict[str, Any] | None) -> int | None:
    if not runtime_submission:
        return None
    returned_job_metadata = runtime_submission.get("returned_job_metadata")
    if not isinstance(returned_job_metadata, dict):
        return None
    metadata = returned_job_metadata.get("metadata")
    if not isinstance(metadata, dict):
        return None
    shots = metadata.get("shots")
    return int(shots) if shots is not None else None


def _runtime_achieved_error_from_payload(payload: dict[str, Any]) -> float | None:
    runtime_submission = payload.get("runtime_submission")
    if not isinstance(runtime_submission, dict):
        return None
    if not runtime_submission.get("submitted") or not runtime_submission.get("succeeded"):
        return None

    benchmark = payload.get("benchmark")
    if isinstance(benchmark, dict) and benchmark.get("absolute_error") is not None:
        return float(benchmark["absolute_error"])

    exact_baseline = payload.get("exact_baseline")
    sampled_result = payload.get("sampled_result")
    if not isinstance(exact_baseline, dict) or not isinstance(sampled_result, dict):
        return None
    exact_total = exact_baseline.get("total_energy")
    sampled_total = sampled_result.get("sampled_total_energy_mean")
    if exact_total is None or sampled_total is None:
        return None
    return abs(float(sampled_total) - float(exact_total))


def _summarize_hardware_calibration_case(payload: dict[str, Any], result_json_path: Path) -> dict[str, Any]:
    runtime_submission = payload.get("runtime_submission")
    runtime_submission = runtime_submission if isinstance(runtime_submission, dict) else None
    runtime_evidence_status = _runtime_evidence_status_from_submission(runtime_submission)
    runtime_evidence_tier = payload.get("hardware_evidence_tier")
    if runtime_evidence_tier is None and runtime_evidence_status != "none":
        runtime_evidence_tier = runtime_evidence_status
    return {
        "name": str(payload.get("run_id") or result_json_path.parent.name),
        "artifact_root": str(result_json_path.parent),
        "result_json": str(result_json_path),
        "backend_name": (runtime_submission.get("backend_name") if runtime_submission else None),
        "job_id": (runtime_submission.get("job_id") if runtime_submission else None),
        "runtime_evidence_status": runtime_evidence_status,
        "runtime_evidence_tier": runtime_evidence_tier,
        "runtime_submission_status": _runtime_submission_status_from_submission(runtime_submission),
        "runtime_submission_wall_time_seconds": (
            runtime_submission.get("submission_wall_time_seconds") if runtime_submission else None
        ),
        "runtime_shots": _runtime_returned_shots(runtime_submission),
        "achieved_error": _runtime_achieved_error_from_payload(payload),
        "hardware_verified": bool(payload.get("hardware_verified")),
    }


def _run_case(case, case_root: Path) -> BenchmarkCaseResult:
    spec = load_run_spec(case.config)
    if case.overrides:
        spec = clone_spec_with_overrides(spec, case.overrides)
    result = run_spec(spec, source_config=str(case.config), output_dir=case_root)
    runtime_evidence_status = "none"
    if result.runtime_submission is not None and result.runtime_submission.submitted and result.runtime_submission.succeeded:
        runtime_evidence_status = "retrieved_result"
    elif result.runtime_submission is not None and result.runtime_submission.submitted:
        runtime_evidence_status = "submitted"
    elif result.runtime_submission is not None and result.runtime_submission.attempted:
        runtime_evidence_status = "runtime_attempt"
    return BenchmarkCaseResult(
        name=case.name,
        kind=case.kind,
        status=result.verification_status,
        expected_status=case.expected_status,
        artifact_root=result.artifacts.root,
        total_energy=result.energy.total_energy,
        absolute_error=result.benchmark.absolute_error,
        relative_error=result.benchmark.relative_error,
        metrics={
            "comparison_target": result.benchmark.comparison_target,
            "within_uncertainty": result.benchmark.within_uncertainty,
            "policy": result.execution_policy.name,
            "compression_method": (result.compression_result.method if result.compression_result is not None else None),
            "execution_enabled": (
                result.compression_result.execution_enabled if result.compression_result is not None else False
            ),
            "compression_rank": (result.compression_result.rank if result.compression_result is not None else None),
            "compression_pre_term_count": (
                result.compression_result.pre_term_count if result.compression_result is not None else None
            ),
            "compression_post_term_count": (
                result.compression_result.post_term_count if result.compression_result is not None else None
            ),
            "compression_verification_status": (
                result.compression_result.verification_status if result.compression_result is not None else None
            ),
            "measurement_strategy": (
                result.measurement.strategy if result.measurement is not None else None
            ),
            "measurement_group_count": (
                result.measurement.group_count if result.measurement is not None else None
            ),
            "estimated_measurement_cost": (
                result.measurement.estimated_shot_cost if result.measurement is not None else None
            ),
            "measurement_execution_mode": (
                result.measurement.execution_mode if result.measurement is not None else None
            ),
            "precision_target": (
                result.calibration.precision_target if result.calibration is not None else None
            ),
            "measured_wall_time_seconds": (
                result.calibration.measured_wall_time_seconds if result.calibration is not None else None
            ),
            "measured_shot_usage": (
                result.calibration.measured_shot_usage if result.calibration is not None else None
            ),
            "achieved_error": (
                result.calibration.achieved_error if result.calibration is not None else None
            ),
            "estimated_vs_measured_cost": (
                result.calibration.estimated_vs_measured_cost if result.calibration is not None else None
            ),
            "runtime_service": (
                result.runtime_options.service if result.runtime_options is not None else None
            ),
            "runtime_grouping_policy": (
                result.runtime_options.grouping_policy if result.runtime_options is not None else None
            ),
            "runtime_resilience_level": (
                result.runtime_options.resilience_level if result.runtime_options is not None else None
            ),
            "runtime_low_rank_workload": (
                result.runtime_options.low_rank_workload if result.runtime_options is not None else None
            ),
            "hardware_verified": result.hardware_verified,
            "hardware_evidence_tier": result.hardware_evidence_tier,
            "runtime_evidence_status": runtime_evidence_status,
            "runtime_submission_status": (
                (
                    "submitted"
                    if result.runtime_submission is not None and result.runtime_submission.submitted
                    else (
                        result.runtime_submission.failure_category
                        if result.runtime_submission is not None
                        else None
                    )
                )
            ),
            "compressed_vs_uncompressed": result.benchmark.compressed_vs_uncompressed,
            "wall_time_seconds": result.provenance.wall_time_seconds,
        },
    )


def _jw_bk_consistency_case(case, case_root: Path) -> BenchmarkCaseResult:
    spec = load_run_spec(case.config)
    chemistry = build_electronic_structure_context(spec)
    solver = ExactDiagonalizationSolver()
    jw = map_fermionic_hamiltonian(chemistry.fermionic_hamiltonian, "jordan_wigner")
    bk = map_fermionic_hamiltonian(chemistry.fermionic_hamiltonian, "bravyi_kitaev")
    jw_energy = solver.solve(jw.qubit_hamiltonian).total_energy
    bk_energy = solver.solve(bk.qubit_hamiltonian).total_energy
    diff = abs(jw_energy - bk_energy)
    status = "validated" if diff <= 1.0e-10 else "failed"
    case_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": case.name,
        "jw_energy": jw_energy,
        "bk_energy": bk_energy,
        "absolute_difference": diff,
        "status": status,
    }
    write_result_json(payload, case_root / "result.json")
    return BenchmarkCaseResult(
        name=case.name,
        kind=case.kind,
        status=status,
        expected_status=case.expected_status,
        artifact_root=case_root,
        absolute_error=diff,
        metrics={"jw_energy": jw_energy, "bk_energy": bk_energy, "absolute_difference": diff},
    )


def _shot_scaling_case(case, case_root: Path) -> BenchmarkCaseResult:
    errors: dict[str, float | None] = {}
    stderrs: dict[str, float | None] = {}
    statuses: dict[str, str] = {}
    for shot in case.shots:
        spec = load_run_spec(case.config)
        spec = clone_spec_with_overrides(spec, {"backend.shots": shot})
        result = run_spec(
            spec,
            source_config=str(case.config),
            output_dir=case_root / f"shot_{shot}",
        )
        errors[str(shot)] = result.benchmark.absolute_error
        stderrs[str(shot)] = result.sampled_result.standard_error if result.sampled_result is not None else None
        statuses[str(shot)] = result.verification_status
    ordered_errors = [value for _, value in sorted(errors.items(), key=lambda item: int(item[0])) if value is not None]
    if any(value == "failed" for value in statuses.values()):
        status = "failed"
    elif any(value == "unstable" for value in statuses.values()):
        status = "unstable"
    elif ordered_errors and ordered_errors[-1] <= ordered_errors[0]:
        status = "validated"
    else:
        status = "exploratory"
    outcome = BenchmarkCaseResult(
        name=case.name,
        kind=case.kind,
        status=status,
        expected_status=case.expected_status,
        artifact_root=case_root,
        metrics={"absolute_errors": errors, "standard_errors": stderrs, "statuses": statuses},
    )
    case_root.mkdir(parents=True, exist_ok=True)
    write_result_json(outcome, case_root / "result.json")
    return outcome


def _optimizer_stability_case(case, case_root: Path) -> BenchmarkCaseResult:
    energies: dict[str, float] = {}
    statuses: dict[str, str] = {}
    for optimizer in case.optimizers:
        spec = load_run_spec(case.config)
        spec = clone_spec_with_overrides(spec, {"solver.optimizer.kind": optimizer})
        result = run_spec(
            spec,
            source_config=str(case.config),
            output_dir=case_root / optimizer.lower(),
        )
        energies[optimizer] = result.energy.total_energy
        statuses[optimizer] = result.verification_status
    spread = max(energies.values()) - min(energies.values()) if energies else math.inf
    status = "validated" if spread <= 1.0e-4 and all(value != "failed" for value in statuses.values()) else "unstable"
    outcome = BenchmarkCaseResult(
        name=case.name,
        kind=case.kind,
        status=status,
        expected_status=case.expected_status,
        artifact_root=case_root,
        metrics={"energies": energies, "spread": spread, "statuses": statuses},
    )
    case_root.mkdir(parents=True, exist_ok=True)
    write_result_json(outcome, case_root / "result.json")
    return outcome


def _noise_comparison_case(case, case_root: Path) -> BenchmarkCaseResult:
    spec = load_run_spec(case.config)
    noisy_result = run_spec(spec, source_config=str(case.config), output_dir=case_root / "noisy")
    ideal_spec = clone_spec_with_overrides(
        spec,
        {
            "backend.noise": NoiseModelSpec(),
            "backend.runtime.enabled": False,
            "backend.runtime.runtime_ready": False,
            "backend.runtime.session_ready": False,
            "backend.runtime.batch_ready": False,
        },
    )
    ideal_result = run_spec(ideal_spec, source_config=str(case.config), output_dir=case_root / "ideal")

    exact_total = noisy_result.exact_baseline.total_energy or ideal_result.exact_baseline.total_energy
    noisy_total = (
        noisy_result.sampled_result.sampled_total_energy_mean
        if noisy_result.sampled_result is not None
        else noisy_result.energy.total_energy
    )
    ideal_total = (
        ideal_result.sampled_result.sampled_total_energy_mean
        if ideal_result.sampled_result is not None
        else ideal_result.energy.total_energy
    )
    noisy_abs = abs(noisy_total - exact_total) if exact_total is not None and noisy_total is not None else None
    ideal_abs = abs(ideal_total - exact_total) if exact_total is not None and ideal_total is not None else None
    noisy_minus_ideal = (noisy_total - ideal_total) if noisy_total is not None and ideal_total is not None else None

    if exact_total is None:
        status = "failed"
    elif noisy_result.verification_status in {"failed", "unstable"} or ideal_result.verification_status in {"failed", "unstable"}:
        status = "unstable"
    elif noisy_abs is not None and ideal_abs is not None and noisy_abs >= ideal_abs:
        status = "exploratory"
    else:
        status = "validated"

    outcome = BenchmarkCaseResult(
        name=case.name,
        kind=case.kind,
        status=status,
        expected_status=case.expected_status,
        artifact_root=case_root,
        total_energy=noisy_total,
        absolute_error=noisy_abs,
        relative_error=((noisy_abs / max(abs(exact_total), 1.0e-12)) if noisy_abs is not None and exact_total is not None else None),
        metrics={
            "exact_total_energy": exact_total,
            "ideal_total_energy": ideal_total,
            "noisy_total_energy": noisy_total,
            "ideal_absolute_error": ideal_abs,
            "noisy_absolute_error": noisy_abs,
            "noisy_minus_ideal": noisy_minus_ideal,
            "ideal_status": ideal_result.verification_status,
            "noisy_status": noisy_result.verification_status,
        },
    )
    case_root.mkdir(parents=True, exist_ok=True)
    write_result_json(outcome, case_root / "result.json")
    return outcome


def run_benchmark_suite_from_spec(spec, *, source_config: str, output_dir: Path | None = None) -> BenchmarkSuiteResult:
    """Run a benchmark suite from an already-parsed spec."""
    suite_root = output_dir or Path("artifacts") / spec.name
    artifacts = _prepare_benchmark_artifacts(Path(suite_root))
    cases_root = artifacts.root / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)

    case_results: list[BenchmarkCaseResult] = []
    registry_entries = []
    for case in spec.cases:
        case_root = cases_root / case.name
        if case.kind == "run":
            outcome = _run_case(case, case_root)
        elif case.kind == "consistency":
            outcome = _jw_bk_consistency_case(case, case_root)
        elif case.kind == "shot_scaling":
            outcome = _shot_scaling_case(case, case_root)
        elif case.kind == "optimizer_stability":
            outcome = _optimizer_stability_case(case, case_root)
        elif case.kind == "noise_comparison":
            outcome = _noise_comparison_case(case, case_root)
        else:
            raise ValueError(f"Unsupported benchmark case kind: {case.kind}")
        case_results.append(outcome)
        registry_entries.append(
            make_registry_entry(
                name=case.name,
                kind=f"benchmark:{case.kind}",
                status=outcome.status,
                artifact_root=outcome.artifact_root or case_root,
                source=str(case.config) if case.config is not None else source_config,
                tags=case.tags,
            )
        )

    status_counts: dict[str, int] = {}
    for item in case_results:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1

    measured_costs = [
        case.metrics.get("measured_shot_usage")
        for case in case_results
        if case.metrics.get("measured_shot_usage") is not None
    ]
    estimated_costs = [
        case.metrics.get("estimated_measurement_cost")
        for case in case_results
        if case.metrics.get("estimated_measurement_cost") is not None
    ]
    achieved_errors = [
        case.metrics.get("achieved_error")
        for case in case_results
        if case.metrics.get("achieved_error") is not None
    ]
    calibration_summary = {
        "cases_with_measured_cost": len(measured_costs),
        "cases_with_estimated_cost": len(estimated_costs),
        "mean_estimated_cost": (sum(estimated_costs) / len(estimated_costs) if estimated_costs else None),
        "mean_measured_cost": (sum(measured_costs) / len(measured_costs) if measured_costs else None),
        "mean_achieved_error": (sum(achieved_errors) / len(achieved_errors) if achieved_errors else None),
    }
    dashboard_summary = {
        "compressed_cases": [
            case.name for case in case_results if case.metrics.get("compression_method") is not None
        ],
        "runtime_cases": [
            case.name for case in case_results if case.metrics.get("runtime_service") is not None
        ],
        "estimated_vs_measured_cost_ratios": {
            case.name: case.metrics.get("estimated_vs_measured_cost")
            for case in case_results
            if case.metrics.get("estimated_vs_measured_cost") is not None
        },
        "precision_targets": {
            case.name: case.metrics.get("precision_target")
            for case in case_results
            if case.metrics.get("precision_target") is not None
        },
        "grouping_policies": {
            case.name: case.metrics.get("runtime_grouping_policy")
            for case in case_results
            if case.metrics.get("runtime_grouping_policy") is not None
        },
        "resilience_levels": {
            case.name: case.metrics.get("runtime_resilience_level")
            for case in case_results
            if case.metrics.get("runtime_resilience_level") is not None
        },
        "achieved_errors": {
            case.name: case.metrics.get("achieved_error")
            for case in case_results
            if case.metrics.get("achieved_error") is not None
        },
        "hardware_verified_cases": [
            case.name for case in case_results if case.metrics.get("hardware_verified")
        ],
        "cases": [
            {
                "name": case.name,
                "estimated_measurement_cost": case.metrics.get("estimated_measurement_cost"),
                "measured_shot_usage": case.metrics.get("measured_shot_usage"),
                "measured_wall_time_seconds": case.metrics.get("measured_wall_time_seconds"),
                "achieved_error": case.metrics.get("achieved_error"),
                "hardware_verified": case.metrics.get("hardware_verified"),
                "hardware_evidence_tier": case.metrics.get("hardware_evidence_tier"),
                "runtime_evidence_status": case.metrics.get("runtime_evidence_status", "none"),
            }
            for case in case_results
            if case.metrics.get("estimated_measurement_cost") is not None
            or case.metrics.get("measured_shot_usage") is not None
            or case.metrics.get("achieved_error") is not None
        ],
    }

    suite_status = "validated" if all(item.status == "validated" for item in case_results) else "exploratory"
    registry_entries.append(
        make_registry_entry(
            name=spec.name,
            kind="benchmark_suite",
            status=suite_status,
            artifact_root=artifacts.root,
            source=source_config,
            tags=spec.tags,
        )
    )

    result = BenchmarkSuiteResult(
        schema_version=SCHEMA_VERSION,
        suite_name=spec.name,
        description=spec.description,
        summary=BenchmarkSuiteSummary(total_cases=len(case_results), status_counts=status_counts),
        cases=case_results,
        calibration_summary=calibration_summary,
        dashboard_summary=dashboard_summary,
        registry_entries=registry_entries,
        artifacts=artifacts,
    )
    write_result_json(result, artifacts.result_json)
    write_result_json(calibration_summary, artifacts.root / "calibration_summary.json")
    (artifacts.root / "calibration_report.md").write_text(
        "\n".join(
            [
                f"# Calibration Summary: {spec.name}",
                "",
                "## Aggregate",
                "",
                f"- cases_with_estimated_cost: `{calibration_summary['cases_with_estimated_cost']}`",
                f"- cases_with_measured_cost: `{calibration_summary['cases_with_measured_cost']}`",
                f"- mean_estimated_cost: `{calibration_summary['mean_estimated_cost']}`",
                f"- mean_measured_cost: `{calibration_summary['mean_measured_cost']}`",
                f"- mean_achieved_error: `{calibration_summary['mean_achieved_error']}`",
                "",
                "## Dashboard",
                "",
                f"- precision_targets: `{dashboard_summary['precision_targets']}`",
                f"- grouping_policies: `{dashboard_summary['grouping_policies']}`",
                f"- resilience_levels: `{dashboard_summary['resilience_levels']}`",
                f"- achieved_errors: `{dashboard_summary['achieved_errors']}`",
                f"- estimated_vs_measured_cost_ratios: `{dashboard_summary['estimated_vs_measured_cost_ratios']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_registry(registry_entries, artifacts.registry_json)
    write_aggregate_report(result, artifacts.report_markdown, kind="benchmark")
    write_hardware_calibration_report(dashboard_summary, artifacts.root / "hardware_dashboard.md")
    return result


def build_hardware_calibration_suite(
    result_json_paths: list[Path],
    *,
    output_root: Path,
) -> dict[str, Any]:
    """Build a compact hardware-calibration dashboard from run result artifacts."""
    resolved_output_root = resolve_artifact_root(output_root)
    resolved_output_root.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    for result_json_path in result_json_paths:
        resolved_path = result_json_path.resolve()
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
        cases.append(_summarize_hardware_calibration_case(payload, resolved_path))

    runtime_status_counts: dict[str, int] = {}
    for case in cases:
        status = str(case["runtime_evidence_status"])
        runtime_status_counts[status] = runtime_status_counts.get(status, 0) + 1

    summary = {
        "suite_name": resolved_output_root.name,
        "summary": {
            "total_cases": len(cases),
            "runtime_evidence_status_counts": runtime_status_counts,
            "hardware_verified_cases": [case["name"] for case in cases if case["hardware_verified"]],
        },
        "cases": cases,
    }

    write_result_json(summary, resolved_output_root / "hardware_calibration_summary.json")
    write_hardware_calibration_report(summary, resolved_output_root / "hardware_calibration_report.md")
    return summary


def run_benchmark_suite_from_config(path: Path, output_dir: Path | None = None) -> BenchmarkSuiteResult:
    """Load and run a benchmark suite from YAML."""
    spec = load_benchmark_suite_spec(path)
    return run_benchmark_suite_from_spec(spec, source_config=str(path), output_dir=output_dir)
