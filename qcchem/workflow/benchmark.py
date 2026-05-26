"""Benchmark-suite workflow orchestration."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

from qcchem.core.chemical_accuracy import CHEMICAL_ACCURACY_HARTREE
from qcchem.chem import build_electronic_structure_context
from qcchem.core import (
    BenchmarkArtifactPaths,
    BenchmarkCaseResult,
    BenchmarkSuiteResult,
    BenchmarkSuiteSummary,
    NoiseModelSpec,
)
from qcchem.field_models import (
    apply_field_model_cross_case_decisions,
    build_field_model_campaign_summary,
    extract_field_model_case_metrics,
)
from qcchem.io.benchmark_config import (
    HardwareCalibrationSuiteSpec,
    load_benchmark_entry_spec,
)
from qcchem.io.artifact_index import build_artifact_index_entry
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.reporting import write_result_json
from qcchem.reporting.aggregate import write_aggregate_report, write_hardware_calibration_report
from qcchem.solvers import ExactDiagonalizationSolver
from qcchem.validation import run_qmmm_embedding_validation
from qcchem.core.evidence import (
    build_benchmark_case_evidence_summary,
    build_benchmark_suite_evidence_summary,
    build_hardware_campaign_evidence_summary,
)
from qcchem.workflow.common import clone_spec_with_overrides, resolve_artifact_root
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.runner import run_spec
from qcchem.workflow.acceptance import build_benchmark_acceptance_summary
from qcchem.workflow.hardware_diagnostics import build_hardware_error_diagnostic

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


def _runtime_submission_value(runtime_submission: Any, key: str) -> Any:
    if runtime_submission is None:
        return None
    if isinstance(runtime_submission, dict):
        return runtime_submission.get(key)
    return getattr(runtime_submission, key, None)


def _runtime_evidence_status_from_submission(runtime_submission: Any) -> str:
    if not runtime_submission:
        return "none"
    if _runtime_submission_value(runtime_submission, "submitted") and _runtime_submission_value(runtime_submission, "succeeded"):
        return "retrieved_result"
    if _runtime_submission_value(runtime_submission, "submitted"):
        return "submitted"
    if _runtime_submission_value(runtime_submission, "attempted"):
        return "runtime_attempt"
    return "none"


def _runtime_submission_status_from_submission(runtime_submission: Any) -> str | None:
    if not runtime_submission:
        return None
    failure_category = _runtime_submission_value(runtime_submission, "failure_category")
    if failure_category:
        return str(failure_category)
    if _runtime_submission_value(runtime_submission, "submitted") and _runtime_submission_value(runtime_submission, "succeeded"):
        return "succeeded"
    if _runtime_submission_value(runtime_submission, "submitted"):
        return "submitted"
    if _runtime_submission_value(runtime_submission, "attempted"):
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


def _runtime_usage_value(runtime_submission: dict[str, Any] | None, *keys: str) -> float | int | None:
    if not runtime_submission:
        return None
    current: Any = runtime_submission
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    return current


def _runtime_submission_list(runtime_submission: dict[str, Any] | None, key: str) -> list[Any] | None:
    if not runtime_submission:
        return None
    value = runtime_submission.get(key)
    return value if isinstance(value, list) else None


def _runtime_returned_expectation_value(runtime_submission: dict[str, Any] | None) -> float | None:
    if not runtime_submission:
        return None
    returned_job_metadata = runtime_submission.get("returned_job_metadata")
    if not isinstance(returned_job_metadata, dict):
        return None
    evs = returned_job_metadata.get("evs")
    if not isinstance(evs, list) or not evs:
        return None
    return float(evs[0])


def _runtime_achieved_error_from_payload(payload: dict[str, Any]) -> tuple[float | None, str]:
    runtime_submission = payload.get("runtime_submission")
    if not isinstance(runtime_submission, dict):
        return None, "no_runtime_submission"
    if not runtime_submission.get("attempted"):
        return None, "no_runtime_submission"
    if not runtime_submission.get("submitted"):
        return None, "runtime_not_submitted"
    if not runtime_submission.get("succeeded"):
        return None, "runtime_result_not_retrieved"

    runtime_expectation_value = _runtime_returned_expectation_value(runtime_submission)
    if runtime_expectation_value is None:
        return None, "runtime_result_missing_expectation"

    energy = payload.get("energy")
    if not isinstance(energy, dict):
        return None, "missing_energy_components"
    constant_energy_correction = energy.get("constant_energy_correction")
    nuclear_repulsion_energy = energy.get("nuclear_repulsion_energy")
    if constant_energy_correction is None or nuclear_repulsion_energy is None:
        return None, "missing_energy_components"

    exact_baseline = payload.get("exact_baseline")
    if not isinstance(exact_baseline, dict) or not exact_baseline.get("available", False):
        return None, "missing_exact_baseline"
    exact_total = exact_baseline.get("total_energy")
    if exact_total is None:
        return None, "missing_exact_baseline"

    runtime_total_energy = (
        runtime_expectation_value
        + float(constant_energy_correction)
        + float(nuclear_repulsion_energy)
    )
    return abs(runtime_total_energy - float(exact_total)), "derived_from_runtime_result"


def _summarize_hardware_calibration_case(payload: dict[str, Any], result_json_path: Path) -> dict[str, Any]:
    runtime_submission = payload.get("runtime_submission")
    runtime_submission = runtime_submission if isinstance(runtime_submission, dict) else None
    runtime_evidence_status = _runtime_evidence_status_from_submission(runtime_submission)
    runtime_evidence_tier = None if runtime_evidence_status == "none" else runtime_evidence_status
    achieved_error, achieved_error_status = _runtime_achieved_error_from_payload(payload)
    meets_chemical_accuracy = (
        None if achieved_error is None else bool(achieved_error <= CHEMICAL_ACCURACY_HARTREE)
    )
    distance_to_chemical_accuracy = (
        None if achieved_error is None else float(max(achieved_error - CHEMICAL_ACCURACY_HARTREE, 0.0))
    )
    diagnostic = build_hardware_error_diagnostic(payload)
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
        "layout_strategy": (runtime_submission.get("layout_strategy") if runtime_submission else None),
        "selected_layout": _runtime_submission_list(runtime_submission, "selected_layout"),
        "layout_score": (runtime_submission.get("layout_score") if runtime_submission else None),
        "transpiled_depth": (runtime_submission.get("transpiled_depth") if runtime_submission else None),
        "transpiled_two_qubit_gate_count": (
            runtime_submission.get("transpiled_two_qubit_gate_count") if runtime_submission else None
        ),
        "runtime_shots": _runtime_returned_shots(runtime_submission),
        "runtime_usage_seconds": _runtime_usage_value(runtime_submission, "job_metrics", "usage", "seconds"),
        "runtime_usage_quantum_seconds": _runtime_usage_value(runtime_submission, "job_metrics", "usage", "quantum_seconds"),
        "runtime_estimated_quantum_seconds": _runtime_usage_value(runtime_submission, "usage_estimation", "quantum_seconds"),
        "requested_precision_target": _runtime_usage_value(runtime_submission, "options_snapshot", "precision_target"),
        "requested_budget_strategy": _runtime_usage_value(runtime_submission, "options_snapshot", "budget_strategy"),
        "requested_budgeted_shots": _runtime_usage_value(runtime_submission, "options_snapshot", "max_budgeted_shots"),
        "achieved_error": achieved_error,
        "achieved_error_status": achieved_error_status,
        "chemical_accuracy_target_hartree": CHEMICAL_ACCURACY_HARTREE,
        "meets_chemical_accuracy": meets_chemical_accuracy,
        "distance_to_chemical_accuracy": distance_to_chemical_accuracy,
        "hardware_verified": bool(runtime_submission and runtime_submission.get("submitted") and runtime_submission.get("succeeded")),
        "hardware_error_diagnostic": diagnostic,
    }


def _environment_embedding_case_metrics(result: Any) -> dict[str, Any]:
    embedding = getattr(result, "environment_embedding", None)
    if embedding is None:
        return {}
    one_body = getattr(embedding, "one_body_environment", {}) or {}
    cache_validation = getattr(embedding, "cache_validation", {}) or {}
    cache_paths = getattr(embedding, "cache_paths", {}) or {}
    projection = getattr(embedding, "active_space_projection", {}) or {}
    boundary = getattr(embedding, "boundary", None)
    mapping = getattr(result, "mapping", None)
    mapping_num_qubits = getattr(mapping, "num_qubits", None)
    mapping_raw_num_qubits = getattr(mapping, "raw_num_qubits", None)
    mapping_qubit_term_count = getattr(mapping, "qubit_term_count", None)
    mapping_raw_qubit_term_count = getattr(mapping, "raw_qubit_term_count", None)
    return {
        "environment_embedding_enabled": bool(getattr(embedding, "enabled", False)),
        "environment_embedding_mode": getattr(embedding, "mode", None),
        "environment_solver_surface": getattr(embedding, "solver_surface", None),
        "environment_hcore_delta_frobenius_norm": one_body.get("frobenius_norm"),
        "environment_hcore_delta_max_abs": one_body.get("max_abs"),
        "environment_hcore_delta_hermitian_deviation": one_body.get("hermitian_deviation"),
        "environment_cache_enabled": bool(getattr(embedding, "cache_enabled", False)),
        "environment_cache_hit": bool(getattr(embedding, "cache_hit", False)),
        "environment_cache_fingerprint": getattr(embedding, "cache_fingerprint", None),
        "environment_cache_metadata_json": cache_paths.get("metadata_json"),
        "environment_cache_matrices_npz": cache_paths.get("matrices_npz"),
        "environment_cache_validated": cache_validation.get("validated"),
        "environment_cache_reload_matrix_error": cache_validation.get("reload_matrix_error"),
        "environment_cache_boundary_reload_matrix_error": cache_validation.get("boundary_reload_matrix_error"),
        "environment_boundary_enabled": bool(getattr(boundary, "enabled", False)) if boundary is not None else False,
        "environment_boundary_max_leakage": (
            getattr(boundary, "max_boundary_leakage", None) if boundary is not None else None
        ),
        "environment_qubit_growth": projection.get("environment_qubit_growth"),
        "environment_original_num_spatial_orbitals": projection.get("original_num_spatial_orbitals"),
        "environment_reduced_num_spatial_orbitals": projection.get("reduced_num_spatial_orbitals"),
        "environment_mapping_num_qubits": mapping_num_qubits,
        "environment_mapping_raw_num_qubits": mapping_raw_num_qubits,
        "environment_mapping_tapered_qubit_delta": (
            int(mapping_raw_num_qubits) - int(mapping_num_qubits)
            if mapping_raw_num_qubits is not None and mapping_num_qubits is not None
            else None
        ),
        "environment_mapping_qubit_term_count": mapping_qubit_term_count,
        "environment_mapping_raw_qubit_term_count": mapping_raw_qubit_term_count,
        "environment_mapping_tapered_term_delta": (
            int(mapping_raw_qubit_term_count) - int(mapping_qubit_term_count)
            if mapping_raw_qubit_term_count is not None and mapping_qubit_term_count is not None
            else None
        ),
    }


def _run_case(
    case,
    case_root: Path,
    *,
    confirm_runtime_budget: str | None = None,
) -> BenchmarkCaseResult:
    spec = load_run_spec(case.config)
    if case.overrides:
        spec = clone_spec_with_overrides(spec, case.overrides)
    if confirm_runtime_budget:
        spec.backend.runtime.options["runtime_budget_confirmation"] = confirm_runtime_budget
    result = run_spec(spec, source_config=str(case.config), output_dir=case_root)
    runtime_evidence_status = _runtime_evidence_status_from_submission(result.runtime_submission)
    field_model_metrics = extract_field_model_case_metrics(result)
    environment_metrics = _environment_embedding_case_metrics(result)
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
            "runtime_submission_status": _runtime_submission_status_from_submission(result.runtime_submission),
            "compressed_vs_uncompressed": result.benchmark.compressed_vs_uncompressed,
            "wall_time_seconds": result.provenance.wall_time_seconds,
            **field_model_metrics,
            **environment_metrics,
        },
        evidence_summary=build_benchmark_case_evidence_summary(
            {
                "name": case.name,
                "kind": case.kind,
                "status": result.verification_status,
                "expected_status": case.expected_status,
                "absolute_error": result.benchmark.absolute_error,
                "metrics": {
                    "comparison_target": result.benchmark.comparison_target,
                    "runtime_evidence_status": runtime_evidence_status,
                },
            }
        ),
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
        evidence_summary=build_benchmark_case_evidence_summary(
            {
                "name": case.name,
                "kind": case.kind,
                "status": status,
                "expected_status": case.expected_status,
                "absolute_error": diff,
                "metrics": {"comparison_target": "jw_bk_consistency"},
            }
        ),
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
        evidence_summary=build_benchmark_case_evidence_summary(
            {
                "name": case.name,
                "kind": case.kind,
                "status": status,
                "expected_status": case.expected_status,
                "absolute_error": ordered_errors[-1] if ordered_errors else None,
                "metrics": {"comparison_target": "shot_scaling"},
            }
        ),
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
        evidence_summary=build_benchmark_case_evidence_summary(
            {
                "name": case.name,
                "kind": case.kind,
                "status": status,
                "expected_status": case.expected_status,
                "absolute_error": spread,
                "metrics": {"comparison_target": "optimizer_spread"},
            }
        ),
    )
    case_root.mkdir(parents=True, exist_ok=True)
    write_result_json(outcome, case_root / "result.json")
    return outcome


def _metric_values(metrics: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for item in metrics:
        value = item.get(key)
        if value is not None:
            values.append(float(value))
    return values


def _qmmm_validation_case_metrics(summary: dict[str, Any], *, profile: str) -> dict[str, Any]:
    metrics = list(summary.get("metrics") or [])
    artifacts = dict(summary.get("artifacts") or {})
    failed_cases = [item.get("case") for item in metrics if not item.get("passed")]
    symmetry_statuses = sorted(
        {
            str(item.get("symmetry_reduction_status"))
            for item in metrics
            if item.get("symmetry_reduction_status") is not None
        }
    )
    return {
        "comparison_target": "qmmm_environment_embedding_validation",
        "qmmm_validation_profile": profile,
        "qmmm_validation_overall_status": summary.get("overall_status"),
        "qmmm_validation_case_count": summary.get("case_count"),
        "qmmm_validation_passed_cases": summary.get("passed_cases"),
        "qmmm_validation_failed_cases": failed_cases,
        "qmmm_validation_artifacts": artifacts,
        "qmmm_validation_json": artifacts.get("json"),
        "qmmm_validation_markdown": artifacts.get("markdown"),
        "qmmm_validation_csv": artifacts.get("csv"),
        "qmmm_formula_closure_max_hartree": (
            max(_metric_values(metrics, "formula_closure_error_hartree")) if metrics else None
        ),
        "qmmm_pyscf_nuclear_delta_max_hartree": (
            max(_metric_values(metrics, "pyscf_nuclear_delta_error_hartree")) if metrics else None
        ),
        "qmmm_hcore_hermiticity_max": (
            max(_metric_values(metrics, "hcore_hermiticity_deviation")) if metrics else None
        ),
        "qmmm_cache_reload_max_error": (
            max(_metric_values(metrics, "cache_reload_matrix_error")) if metrics else None
        ),
        "qmmm_environment_qubit_growth_max": (
            max(_metric_values(metrics, "environment_qubit_growth")) if metrics else None
        ),
        "qmmm_pauli_term_delta_max": (
            max(_metric_values(metrics, "pauli_term_delta_raw_to_executed"))
            if metrics
            else None
        ),
        "qmmm_symmetry_reduction_statuses": symmetry_statuses,
        "qmmm_z2_validated_cases": sum(
            1
            for item in metrics
            if item.get("symmetry_reduction_validation_absolute_delta") is not None
        ),
        "qmmm_cache_validated_cases": sum(1 for item in metrics if item.get("cache_validated")),
    }


def _qmmm_validation_case(case, case_root: Path) -> BenchmarkCaseResult:
    profile = (case.profile or "smoke").strip().lower()
    summary = run_qmmm_embedding_validation(case_root, profile=profile)
    status = "validated" if summary.get("overall_status") == "passed" else "failed"
    metrics = _qmmm_validation_case_metrics(summary, profile=profile)
    evidence_summary = build_benchmark_case_evidence_summary(
        {
            "name": case.name,
            "kind": case.kind,
            "status": status,
            "expected_status": case.expected_status,
            "metrics": metrics,
        }
    )
    outcome = BenchmarkCaseResult(
        name=case.name,
        kind=case.kind,
        status=status,
        expected_status=case.expected_status,
        artifact_root=case_root,
        metrics=metrics,
        evidence_summary=evidence_summary,
    )
    write_result_json(
        {
            "schema_version": "qcchem.qmmm_validation_benchmark_case.v1",
            "run_id": case.name,
            "kind": case.kind,
            "verification_status": status,
            "expected_status": case.expected_status,
            "profile": profile,
            "artifact_root": str(case_root),
            "metrics": metrics,
            "qmmm_validation": summary,
            "evidence_summary": to_primitive(evidence_summary),
        },
        case_root / "result.json",
    )
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
        evidence_summary=build_benchmark_case_evidence_summary(
            {
                "name": case.name,
                "kind": case.kind,
                "status": status,
                "expected_status": case.expected_status,
                "absolute_error": noisy_abs,
                "metrics": {"comparison_target": "noise_comparison"},
            }
        ),
    )
    case_root.mkdir(parents=True, exist_ok=True)
    write_result_json(outcome, case_root / "result.json")
    return outcome


def run_benchmark_suite_from_spec(
    spec,
    *,
    source_config: str,
    output_dir: Path | None = None,
    confirm_runtime_budget: str | None = None,
) -> BenchmarkSuiteResult:
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
            outcome = _run_case(
                case,
                case_root,
                confirm_runtime_budget=confirm_runtime_budget,
            )
        elif case.kind == "consistency":
            outcome = _jw_bk_consistency_case(case, case_root)
        elif case.kind == "shot_scaling":
            outcome = _shot_scaling_case(case, case_root)
        elif case.kind == "optimizer_stability":
            outcome = _optimizer_stability_case(case, case_root)
        elif case.kind == "noise_comparison":
            outcome = _noise_comparison_case(case, case_root)
        elif case.kind == "qmmm_validation":
            outcome = _qmmm_validation_case(case, case_root)
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

    apply_field_model_cross_case_decisions(case_results)
    field_model_campaign_summary = build_field_model_campaign_summary(case_results)

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
        "field_model_campaign": field_model_campaign_summary,
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
        "field_model_campaign": field_model_campaign_summary,
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
    result.evidence_summary = build_benchmark_suite_evidence_summary(to_primitive(result))
    if spec.acceptance.enabled:
        result.acceptance_summary = build_benchmark_acceptance_summary(
            to_primitive(result),
            benchmark_result_path=artifacts.result_json,
            required_files=spec.acceptance.required_files,
            require_evidence_summary=spec.acceptance.require_evidence_summary,
            require_runtime_sidecar_for_hardware_verified=(
                spec.acceptance.require_runtime_sidecar_for_hardware_verified
            ),
            fail_on_runtime_accuracy_promotion=spec.acceptance.fail_on_runtime_accuracy_promotion,
            strict_exit_code=spec.acceptance.strict_exit_code,
        )
    else:
        result.acceptance_summary = {
            "schema_version": "qcchem.benchmark_acceptance.v0.1-alpha",
            "suite_name": spec.name,
            "accepted": True,
            "blocking_failures": [],
            "warnings": [{"reason": "acceptance_disabled"}],
            "recommended_action": "review_acceptance_warnings",
        }
    write_result_json(result, artifacts.result_json)
    result.artifact_index_entry = build_artifact_index_entry(artifacts.result_json)
    write_result_json(result, artifacts.result_json)
    write_result_json(result.acceptance_summary, artifacts.root / "acceptance_summary.json")
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
                f"- field_model_campaign: `{field_model_campaign_summary}`",
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
        sidecar_path = resolved_path.parent / "runtime_submission.json"
        if sidecar_path.exists():
            payload["runtime_submission"] = json.loads(sidecar_path.read_text(encoding="utf-8"))
        cases.append(_summarize_hardware_calibration_case(payload, resolved_path))

    runtime_status_counts: dict[str, int] = {}
    for case in cases:
        status = str(case["runtime_evidence_status"])
        runtime_status_counts[status] = runtime_status_counts.get(status, 0) + 1

    summary = {
        "suite_name": resolved_output_root.name,
        "artifact_root": str(resolved_output_root),
        "summary": {
            "total_cases": len(cases),
            "runtime_evidence_status_counts": runtime_status_counts,
            "hardware_verified_cases": [case["name"] for case in cases if case["hardware_verified"]],
        },
        "cases": cases,
    }
    evidence_summary, decision_worthiness = build_hardware_campaign_evidence_summary(summary)
    summary["evidence_summary"] = to_primitive(evidence_summary)
    summary["decision_worthiness"] = decision_worthiness

    write_result_json(summary, resolved_output_root / "hardware_calibration_summary.json")
    write_hardware_calibration_report(summary, resolved_output_root / "hardware_calibration_report.md")
    return summary


def _run_hardware_calibration_suite_from_spec(
    spec: HardwareCalibrationSuiteSpec,
    *,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    return build_hardware_calibration_suite(
        [case.result_json for case in spec.cases],
        output_root=(output_dir or spec.output_root),
    )


def run_benchmark_suite_from_config(
    path: Path,
    output_dir: Path | None = None,
    *,
    confirm_runtime_budget: str | None = None,
) -> BenchmarkSuiteResult | dict[str, Any]:
    """Load and run a benchmark suite from YAML."""
    spec = load_benchmark_entry_spec(path)
    if isinstance(spec, HardwareCalibrationSuiteSpec):
        return _run_hardware_calibration_suite_from_spec(spec, output_dir=output_dir)
    return run_benchmark_suite_from_spec(
        spec,
        source_config=str(path),
        output_dir=output_dir,
        confirm_runtime_budget=confirm_runtime_budget,
    )
