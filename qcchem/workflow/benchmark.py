"""Benchmark-suite workflow orchestration."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from qcchem.core.chemical_accuracy import CHEMICAL_ACCURACY_HARTREE
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
from qcchem.core.evidence import (
    build_benchmark_case_evidence_summary,
    build_benchmark_suite_evidence_summary,
    build_hardware_campaign_evidence_summary,
)
from qcchem.workflow.common import clone_spec_with_overrides, prepare_clean_output_root
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.acceptance import build_benchmark_acceptance_summary
from qcchem.workflow.hardware_diagnostics import build_hardware_error_diagnostic

SCHEMA_VERSION = "qcchem.benchmark.v0.4-alpha"

METHOD_EVIDENCE_CONTRACTS: dict[str, dict[str, Any]] = {
    "e_adapt_result": {
        "display_name": "E-ADAPT",
        "result_field": "e_adapt_result",
        "report_tokens": ["## E-ADAPT"],
        "metric_keys": [
            "e_adapt_selected_operator_count",
            "e_adapt_pool_origins",
            "e_adapt_adaptive_energy_replaces_delegate",
            "e_adapt_replacement_min_improvement_hartree",
            "e_adapt_min_selected_energy_lowering_hartree",
            "e_adapt_no_improvement_rejection_count",
            "e_adapt_operator_acceptance_min_improvement_hartree",
            "e_adapt_optimization_signal_present",
            "e_adapt_adaptive_improvement_status",
            "e_adapt_delegate_improvement_to_replacement_threshold_ratio",
            "e_adapt_cumulative_selected_energy_lowering_hartree",
            "e_adapt_final_cumulative_two_qubit_increment",
        ],
    },
    "orbital_optimization": {
        "display_name": "OO-QCASSCF",
        "result_field": "orbital_optimization",
        "report_tokens": ["## OO-QCASSCF"],
        "metric_keys": [
            "orbital_optimization_reference_status",
            "orbital_optimization_energy_replaces_primary",
            "orbital_optimization_active_space_resolve_status",
            "orbital_optimization_energy_scope_consistent",
            "orbital_optimization_promotion_readiness_status",
            "orbital_optimization_readiness_level",
            "orbital_optimization_solver_replacement_allowed",
            "orbital_optimization_optimized_orbitals_applied",
            "orbital_optimization_primary_hamiltonian_rebuilt",
            "orbital_optimization_required_promotion_evidence_count",
            "orbital_optimization_promotion_blocker_count",
        ],
    },
    "qsci_plus_result": {
        "display_name": "QSCI++",
        "result_field": "qsci_plus_result",
        "report_tokens": ["## QSCI++"],
        "metric_keys": [
            "qsci_selected_subspace_size",
            "qsci_variance_estimate",
            "qsci_ground_state_residual_norm",
            "qsci_selected_origin_counts",
            "qsci_variational_upper_bound_margin_hartree",
            "qsci_residual_expansion_added_determinant_count",
        ],
    },
    "post_correlation": {
        "display_name": "QSCI post-correlation",
        "result_field": "post_correlation",
        "report_tokens": ["## QSCI Post-Correlation"],
        "metric_keys": [
            "post_correlation_method",
            "post_correlation_trust_gate",
            "post_correlation_double_counting_status",
            "post_correlation_eligibility_status",
            "post_correlation_amplitude_mapping_status",
            "post_correlation_backend_executable",
            "post_correlation_correction_energy_emitted",
            "post_correlation_required_input_missing_count",
        ],
    },
    "q_sc_eom": {
        "display_name": "q-sc-EOM",
        "result_field": "excited_state_result",
        "report_tokens": ["q_sc_eom"],
        "metric_keys": [
            "q_sc_eom_state_count",
            "q_sc_eom_max_root_residual_norm",
            "q_sc_eom_conditioning_status",
            "q_sc_eom_overlap_condition_number",
            "q_sc_eom_root_tracking_statuses",
            "q_sc_eom_transition_property_status",
            "q_sc_eom_validated_transition_property_count",
            "q_sc_eom_transition_property_names",
        ],
    },
    "q_embed": {
        "display_name": "Q-Embed/q-DMET",
        "result_field": "embedding_result",
        "report_tokens": ["## Embedding Audit"],
        "metric_keys": [
            "q_embed_execution_status",
            "q_embed_self_consistency_loop_executed",
            "q_embed_self_consistency_iteration_count",
            "q_embed_density_matching_performed",
            "q_embed_density_matching_iteration_count",
            "q_embed_density_mismatch_status",
            "q_embed_density_mismatch_audit_status",
            "q_embed_density_mismatch_l1_norm",
            "q_embed_density_mismatch_signed_sum",
            "q_embed_density_mismatch_threshold",
            "q_embed_max_fragment_population_delta_abs",
            "q_embed_correlation_potential_parameter_count",
            "q_embed_fragment_ao_coverage_fraction",
            "q_embed_fragment_atom_coverage_fraction",
            "q_embed_fragment_coverage_status",
            "q_embed_fragment_energy_sum_gap_abs_hartree",
            "q_embed_fragment_energy_sum_gap_per_fragment_hartree",
            "q_embed_fragment_energy_sum_replaces_primary",
        ],
    },
    "kq_pbc_result": {
        "display_name": "kQ-PBC",
        "result_field": "kq_pbc_result",
        "report_tokens": ["## kQ-PBC"],
        "metric_keys": [
            "kq_pbc_non_gamma_status",
            "kq_pbc_mesh_mismatch",
            "kq_pbc_named_kpoint_coverage_fraction",
            "kq_pbc_mesh_kpoint_coverage_fraction",
            "kq_pbc_twist_energy_coverage_fraction",
            "kq_pbc_missing_twist_energy_fraction",
            "kq_pbc_promotion_readiness_status",
            "kq_pbc_readiness_level",
            "kq_pbc_executable_scope",
            "kq_pbc_finite_size_status",
            "kq_pbc_promotion_blocker_count",
            "kq_pbc_unsupported_claim_count",
            "kq_pbc_energy_replaces_primary",
            "kq_pbc_runtime_submission_allowed",
            "kq_pbc_proxy_energy_present",
        ],
    },
    "trust_qem": {
        "display_name": "Trust-QEM",
        "result_field": "mitigation",
        "report_tokens": ["## Trust-QEM"],
        "metric_keys": [
            "trust_qem_claim_status",
            "trust_qem_energy_replaces_primary",
            "trust_qem_pec_status",
            "trust_qem_pec_executable_calibration_model",
            "trust_qem_pec_allowed_for_claim",
            "trust_qem_pec_calibrated_operation_count",
            "trust_qem_pec_sampling_overhead",
        ],
    },
    "shadow_lr": {
        "display_name": "Shadow-LR",
        "result_field": "measurement",
        "report_tokens": ["shadow_lr"],
        "metric_keys": [
            "shadow_lr_allocated_shots",
            "shadow_lr_grouped_precision_baseline_shots",
            "shadow_lr_cost_reduction_vs_grouped_precision",
            "shadow_lr_basis_l1_coverage_fraction",
            "shadow_lr_variance_inflation_vs_grouped_precision_proxy",
            "shadow_lr_plan_digest",
        ],
    },
    "ft_qpe_resource_estimate": {
        "display_name": "FT-QPE Planner",
        "result_field": "ft_qpe_resource_estimate",
        "report_tokens": ["## FT-QPE Planner"],
        "metric_keys": [
            "ft_qpe_resource_claim_status",
            "ft_qpe_resource_model_scope",
            "ft_qpe_compiled_circuit_available",
            "ft_qpe_surface_code_distance_available",
            "ft_qpe_promotion_readiness_status",
            "ft_qpe_readiness_level",
            "ft_qpe_reference_encoding",
            "ft_qpe_encoding_comparison_count",
            "ft_qpe_resource_formula_scope",
            "ft_qpe_logical_error_budget_available",
            "ft_qpe_required_promotion_evidence_count",
        ],
    },
}


def build_electronic_structure_context(*args, **kwargs):
    from qcchem.chem.problem_builder import build_electronic_structure_context as impl

    return impl(*args, **kwargs)


def run_spec(*args, **kwargs):
    from qcchem.workflow.runner import run_spec as impl

    return impl(*args, **kwargs)


def run_qmmm_embedding_validation(*args, **kwargs):
    from qcchem.validation import run_qmmm_embedding_validation as impl

    return impl(*args, **kwargs)


def run_pbc_qmmm_validation(*args, **kwargs):
    from qcchem.validation import run_pbc_qmmm_validation as impl

    return impl(*args, **kwargs)


def _prepare_benchmark_artifacts(root: Path, *, overwrite: bool) -> BenchmarkArtifactPaths:
    resolved_root = prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=overwrite)
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


def _method_evidence_case_metrics(result: Any) -> dict[str, Any]:
    evidence = getattr(result, "method_evidence", None)
    method_map = getattr(evidence, "methods", {}) if evidence is not None else {}
    method_names = sorted(method_map.keys()) if isinstance(method_map, dict) else []
    promotion_gate_audit = (
        getattr(evidence, "promotion_gate_audit", {}) if evidence is not None else {}
    )
    measurement = getattr(result, "measurement", None)
    mitigation = getattr(result, "mitigation", None)
    measurement_cost_model = (
        getattr(measurement, "measurement_cost_model", {}) if measurement is not None else {}
    )
    e_adapt = getattr(result, "e_adapt_result", None)
    e_adapt_selected = getattr(e_adapt, "selected_operators", []) if e_adapt is not None else []
    e_adapt_adaptive = getattr(e_adapt, "adaptive_optimization", {}) if e_adapt is not None else {}
    orbital = getattr(result, "orbital_optimization", None)
    orbital_reference = getattr(orbital, "reference_diagnostics", {}) if orbital is not None else {}
    orbital_resolve = getattr(orbital, "active_space_resolve", {}) if orbital is not None else {}
    orbital_scope_audit = getattr(orbital, "energy_scope_audit", {}) if orbital is not None else {}
    orbital_transfer_audit = (
        getattr(orbital, "orbital_transfer_audit", {}) if orbital is not None else {}
    )
    orbital_readiness_audit = (
        getattr(orbital, "promotion_readiness_audit", {}) if orbital is not None else {}
    )
    qsci = getattr(result, "qsci_plus_result", None)
    qsci_subspace_audit = getattr(qsci, "subspace_audit", {}) if qsci is not None else {}
    qsci_selection_audit = getattr(qsci, "selection_bias_audit", {}) if qsci is not None else {}
    qsci_residual_expansion = (
        qsci_selection_audit.get("residual_expansion")
        if isinstance(qsci_selection_audit, dict)
        and isinstance(qsci_selection_audit.get("residual_expansion"), dict)
        else {}
    )
    post = getattr(result, "post_correlation", None)
    embedding = getattr(result, "embedding_result", None)
    kq_pbc = getattr(result, "kq_pbc_result", None)
    ft_qpe = getattr(result, "ft_qpe_resource_estimate", None)
    excited_state = getattr(result, "excited_state_result", None)
    property_result = getattr(result, "property_result", None)
    excited_states = getattr(excited_state, "states", []) if excited_state is not None else []
    q_sc_eom_root_audits = [
        state.solver_metadata.get("root_residual_audit")
        for state in excited_states
        if isinstance(getattr(state, "solver_metadata", None), dict)
        and state.solver_metadata.get("method") == "q_sc_eom"
        and isinstance(state.solver_metadata.get("root_residual_audit"), dict)
    ]
    q_sc_eom_residuals = [
        _float_metric(audit.get("residual_norm"))
        for audit in q_sc_eom_root_audits
        if _float_metric(audit.get("residual_norm")) is not None
    ]
    q_sc_eom_gaps = [
        _float_metric(audit.get("min_neighbor_gap_hartree"))
        for audit in q_sc_eom_root_audits
        if _float_metric(audit.get("min_neighbor_gap_hartree")) is not None
    ]
    q_sc_eom_overlap_condition_numbers = [
        float(state.solver_metadata["overlap_condition_number"])
        for state in excited_states
        if isinstance(getattr(state, "solver_metadata", None), dict)
        and state.solver_metadata.get("method") == "q_sc_eom"
        and isinstance(state.solver_metadata.get("overlap_condition_number"), int | float)
    ]
    q_sc_eom_regularization_actions = sorted(
        {
            str(action)
            for state in excited_states
            if isinstance(getattr(state, "solver_metadata", None), dict)
            and state.solver_metadata.get("method") == "q_sc_eom"
            for action in state.solver_metadata.get("regularization_actions", [])
            if action
        }
    )
    q_sc_eom_degenerate_root_count = sum(
        1
        for audit in q_sc_eom_root_audits
        if audit.get("root_tracking_status") == "degenerate_subspace"
    )
    q_sc_eom_conditioning_status = (
        "regularization_required"
        if "overlap_conditioning_requires_regularization" in q_sc_eom_regularization_actions
        else "degenerate_subspace_tracking_required"
        if q_sc_eom_degenerate_root_count
        else "well_conditioned_reference_roots"
        if q_sc_eom_root_audits
        else None
    )
    property_values = getattr(property_result, "properties", []) if property_result is not None else []
    q_sc_eom_transition_properties = [
        item
        for item in property_values
        if getattr(item, "property_name", None) in {"transition_dipole", "oscillator_strength"}
    ]
    q_sc_eom_validated_transition_properties = [
        item
        for item in q_sc_eom_transition_properties
        if getattr(item, "implementation_status", None) == "validated"
    ]
    q_sc_eom_transition_dipoles = [
        float(getattr(item, "value"))
        for item in q_sc_eom_validated_transition_properties
        if getattr(item, "property_name", None) == "transition_dipole"
        and isinstance(getattr(item, "value", None), int | float)
    ]
    q_sc_eom_oscillator_strengths = [
        float(getattr(item, "value"))
        for item in q_sc_eom_validated_transition_properties
        if getattr(item, "property_name", None) == "oscillator_strength"
        and isinstance(getattr(item, "value", None), int | float)
    ]
    q_sc_eom_transition_property_status = (
        "validated_transition_properties_linked"
        if q_sc_eom_transition_properties
        and len(q_sc_eom_validated_transition_properties) == len(q_sc_eom_transition_properties)
        else "transition_properties_missing"
        if not q_sc_eom_transition_properties
        else "partial_transition_property_linkage"
    )
    embedding_environment = getattr(embedding, "environment_metadata", {}) if embedding is not None else {}
    embedding_boundary = (
        embedding_environment.get("embedding_boundary_audit")
        if isinstance(embedding_environment, dict)
        and isinstance(embedding_environment.get("embedding_boundary_audit"), dict)
        else {}
    )
    embedding_density_history = (
        embedding_environment.get("density_mismatch_history")
        if isinstance(embedding_environment, dict)
        and isinstance(embedding_environment.get("density_mismatch_history"), list)
        else []
    )
    embedding_density_audit = (
        embedding_environment.get("density_mismatch_audit")
        if isinstance(embedding_environment, dict)
        and isinstance(embedding_environment.get("density_mismatch_audit"), dict)
        else {}
    )
    embedding_fragment_coverage = (
        embedding_environment.get("fragment_coverage_audit")
        if isinstance(embedding_environment, dict)
        and isinstance(embedding_environment.get("fragment_coverage_audit"), dict)
        else {}
    )
    embedding_first_density_audit = (
        embedding_density_history[0]
        if embedding_density_history and isinstance(embedding_density_history[0], dict)
        else {}
    )
    kq_twist_energies = getattr(kq_pbc, "twist_energies", []) if kq_pbc is not None else []
    kq_finite_size = getattr(kq_pbc, "finite_size_correction", {}) if kq_pbc is not None else {}
    kq_non_gamma_audit = getattr(kq_pbc, "non_gamma_mapping_audit", {}) if kq_pbc is not None else {}
    kq_promotion_readiness = (
        getattr(kq_pbc, "promotion_readiness_audit", {}) if kq_pbc is not None else {}
    )
    kq_coverage_audit = (
        kq_promotion_readiness.get("coverage_audit")
        if isinstance(kq_promotion_readiness, dict)
        and isinstance(kq_promotion_readiness.get("coverage_audit"), dict)
        else kq_non_gamma_audit.get("coverage_audit")
        if isinstance(kq_non_gamma_audit, dict)
        and isinstance(kq_non_gamma_audit.get("coverage_audit"), dict)
        else {}
    )
    mitigation_pec = getattr(mitigation, "pec", {}) if mitigation is not None else {}
    mitigation_pec_audit = (
        mitigation_pec.get("calibration_model_audit")
        if isinstance(mitigation_pec, dict)
        and isinstance(mitigation_pec.get("calibration_model_audit"), dict)
        else {}
    )
    e_adapt_rejected = (
        getattr(e_adapt, "rejected_operators", []) if e_adapt is not None else []
    )
    e_adapt_selected_lowerings = [
        lowering
        for lowering in (
            _float_metric(entry.get("energy_lowering_hartree"))
            for entry in (e_adapt_selected or [])
            if isinstance(entry, dict)
        )
        if lowering is not None
    ]
    e_adapt_no_improvement_rejection_count = len(
        [
            entry
            for entry in (e_adapt_rejected or [])
            if isinstance(entry, dict)
            and entry.get("reason") == "adaptive_optimization_no_improvement"
        ]
    )

    ft_toffoli_counts = getattr(ft_qpe, "toffoli_counts", {}) if ft_qpe is not None else {}
    ft_lambda_norms = getattr(ft_qpe, "lambda_norms", {}) if ft_qpe is not None else {}
    ft_resource_audit = getattr(ft_qpe, "resource_model_audit", {}) if ft_qpe is not None else {}
    ft_formula_audit = getattr(ft_qpe, "resource_formula_audit", {}) if ft_qpe is not None else {}
    ft_readiness_audit = (
        getattr(ft_qpe, "promotion_readiness_audit", {}) if ft_qpe is not None else {}
    )
    ft_best_encoding = getattr(ft_qpe, "recommended_encoding", None) if ft_qpe is not None else None
    ft_reference_encoding = (
        ft_resource_audit.get("reference_encoding")
        if isinstance(ft_resource_audit, dict)
        else None
    )
    if (
        ft_reference_encoding is None
        and isinstance(ft_toffoli_counts, dict)
        and "double_factorization" in ft_toffoli_counts
    ):
        ft_reference_encoding = "double_factorization"
    ft_best_toffoli = (
        ft_toffoli_counts.get(ft_best_encoding)
        if isinstance(ft_toffoli_counts, dict) and ft_best_encoding is not None
        else None
    )
    ft_reference_toffoli = (
        ft_toffoli_counts.get(ft_reference_encoding)
        if isinstance(ft_toffoli_counts, dict)
        else None
    )
    ft_reduction = (
        (float(ft_reference_toffoli) - float(ft_best_toffoli)) / float(ft_reference_toffoli)
        if ft_reference_toffoli and ft_best_toffoli is not None
        else None
    )
    ft_reference_lambda = (
        ft_lambda_norms.get(ft_reference_encoding) if isinstance(ft_lambda_norms, dict) else None
    )
    ft_best_lambda = (
        ft_lambda_norms.get(ft_best_encoding)
        if isinstance(ft_lambda_norms, dict) and ft_best_encoding is not None
        else None
    )
    ft_lambda_reduction = (
        (float(ft_reference_lambda) - float(ft_best_lambda)) / float(ft_reference_lambda)
        if ft_reference_lambda and ft_best_lambda is not None
        else None
    )

    return {
        "method_evidence_available": bool(evidence and getattr(evidence, "available", False)),
        "method_evidence_methods": method_names,
        "method_evidence_method_count": len(method_names),
        "method_evidence_trust_tier": getattr(evidence, "trust_tier", None) if evidence is not None else None,
        "method_evidence_sidecar_path": getattr(evidence, "sidecar_path", None) if evidence is not None else None,
        "method_evidence_promotion_gate_status": (
            promotion_gate_audit.get("overall_claim_status")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_promotion_required": (
            promotion_gate_audit.get("promotion_required_for_validated_claims")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_sidecar_energy_replacement_allowed_methods": (
            promotion_gate_audit.get("sidecar_energy_replacement_allowed_methods")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_accuracy_claim_allowed_methods": (
            promotion_gate_audit.get("accuracy_claim_allowed_methods")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_hardware_claim_allowed_methods": (
            promotion_gate_audit.get("hardware_claim_allowed_methods")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_planning_metric_methods": (
            promotion_gate_audit.get("planning_metric_methods")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_resource_model_only_methods": (
            promotion_gate_audit.get("resource_model_only_methods")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "method_evidence_unsupported_for_claim_methods": (
            promotion_gate_audit.get("unsupported_for_claim_methods")
            if isinstance(promotion_gate_audit, dict)
            else None
        ),
        "e_adapt_selected_operator_count": (
            len(e_adapt_selected or []) if e_adapt is not None else None
        ),
        "e_adapt_rejected_operator_count": (
            len(e_adapt_rejected or []) if e_adapt is not None else None
        ),
        "e_adapt_trust_gate": getattr(e_adapt, "ansatz_trust_gate", None) if e_adapt is not None else None,
        "e_adapt_pool_origins": (
            sorted(
                {
                    str(entry.get("pool_origin"))
                    for entry in e_adapt_selected
                    if isinstance(entry, dict) and entry.get("pool_origin") is not None
                }
            )
            if e_adapt is not None
            else None
        ),
        "e_adapt_adaptive_energy_replaces_delegate": (
            e_adapt_adaptive.get("energy_replaces_delegate") if isinstance(e_adapt_adaptive, dict) else None
        ),
        "e_adapt_delegate_energy_improvement_hartree": (
            e_adapt_adaptive.get("delegate_energy_improvement_hartree")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_replacement_min_improvement_hartree": (
            e_adapt_adaptive.get("replacement_min_improvement_hartree")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_min_selected_energy_lowering_hartree": (
            min(e_adapt_selected_lowerings) if e_adapt_selected_lowerings else None
        ),
        "e_adapt_no_improvement_rejection_count": (
            e_adapt_adaptive.get(
                "no_improvement_rejection_count",
                e_adapt_no_improvement_rejection_count,
            )
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_operator_acceptance_min_improvement_hartree": (
            e_adapt_adaptive.get("operator_acceptance_min_improvement_hartree")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_optimization_signal_present": (
            e_adapt_adaptive.get("optimization_signal_present")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_adaptive_improvement_status": (
            e_adapt_adaptive.get("adaptive_improvement_status")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_delegate_improvement_to_replacement_threshold_ratio": (
            e_adapt_adaptive.get("delegate_improvement_to_replacement_threshold_ratio")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_cumulative_selected_energy_lowering_hartree": (
            e_adapt_adaptive.get("cumulative_selected_energy_lowering_hartree")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_max_selected_energy_lowering_hartree": (
            e_adapt_adaptive.get("max_selected_energy_lowering_hartree")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_final_cumulative_two_qubit_increment": (
            e_adapt_adaptive.get("final_cumulative_two_qubit_increment")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "e_adapt_adaptive_evaluations_per_selected_operator": (
            e_adapt_adaptive.get("adaptive_evaluations_per_selected_operator")
            if isinstance(e_adapt_adaptive, dict)
            else None
        ),
        "orbital_optimization_macro_iteration_count": (
            len(getattr(orbital, "macro_iterations", []) or []) if orbital is not None else None
        ),
        "orbital_optimization_energy_lowering_hartree": (
            getattr(orbital, "energy_lowering_hartree", None) if orbital is not None else None
        ),
        "orbital_optimization_reference_status": (
            orbital_reference.get("status") if isinstance(orbital_reference, dict) else None
        ),
        "orbital_optimization_reference_backend": (
            orbital_reference.get("backend") if isinstance(orbital_reference, dict) else None
        ),
        "orbital_optimization_casscf_converged": (
            orbital_reference.get("converged") if isinstance(orbital_reference, dict) else None
        ),
        "orbital_optimization_energy_replaces_primary": (
            getattr(orbital, "energy_replaces_primary", None) if orbital is not None else None
        ),
        "orbital_optimization_active_space_resolve_status": (
            orbital_resolve.get("status") if isinstance(orbital_resolve, dict) else None
        ),
        "orbital_optimization_energy_scope_consistent": (
            orbital_scope_audit.get("energy_scope_consistent_for_total_gap")
            if isinstance(orbital_scope_audit, dict)
            else None
        ),
        "orbital_optimization_promotion_readiness_status": (
            orbital_readiness_audit.get("status")
            if isinstance(orbital_readiness_audit, dict)
            else None
        ),
        "orbital_optimization_readiness_level": (
            orbital_readiness_audit.get("readiness_level")
            if isinstance(orbital_readiness_audit, dict)
            else None
        ),
        "orbital_optimization_solver_replacement_allowed": (
            orbital_readiness_audit.get("solver_replacement_allowed")
            if isinstance(orbital_readiness_audit, dict)
            else None
        ),
        "orbital_optimization_optimized_orbitals_applied": (
            orbital_transfer_audit.get("optimized_orbitals_applied_to_primary_solver")
            if isinstance(orbital_transfer_audit, dict)
            else None
        ),
        "orbital_optimization_primary_hamiltonian_rebuilt": (
            orbital_transfer_audit.get("primary_hamiltonian_rebuilt_from_optimized_orbitals")
            if isinstance(orbital_transfer_audit, dict)
            else None
        ),
        "orbital_optimization_required_promotion_evidence_count": (
            orbital_readiness_audit.get("required_promotion_evidence_count")
            if isinstance(orbital_readiness_audit, dict)
            else None
        ),
        "orbital_optimization_promotion_blocker_count": (
            orbital_readiness_audit.get("promotion_blocker_count")
            if isinstance(orbital_readiness_audit, dict)
            else None
        ),
        "orbital_optimization_casscf_total_energy": (
            orbital_resolve.get("casscf_reference_total_energy_hartree")
            if isinstance(orbital_resolve, dict)
            else None
        ),
        "orbital_optimization_casscf_electronic_energy": (
            orbital_resolve.get("casscf_reference_electronic_energy_hartree")
            if isinstance(orbital_resolve, dict)
            else None
        ),
        "orbital_optimization_primary_total_energy_estimate": (
            orbital_resolve.get("delegated_solver_total_energy_estimate_hartree")
            if isinstance(orbital_resolve, dict)
            else None
        ),
        "orbital_optimization_casscf_minus_primary_total_energy": (
            orbital_resolve.get("casscf_minus_primary_total_energy_hartree")
            if isinstance(orbital_resolve, dict)
            else None
        ),
        "orbital_optimization_abs_casscf_primary_total_gap": (
            orbital_resolve.get("abs_casscf_primary_total_gap_hartree")
            if isinstance(orbital_resolve, dict)
            else None
        ),
        "orbital_optimization_casscf_reference_lower_than_primary_total": (
            orbital_resolve.get("casscf_reference_lower_than_primary_total")
            if isinstance(orbital_resolve, dict)
            else None
        ),
        "qsci_selected_subspace_size": (
            getattr(qsci, "selected_subspace_size", None) if qsci is not None else None
        ),
        "qsci_ci_energy": getattr(qsci, "ci_energy", None) if qsci is not None else None,
        "qsci_variance_estimate": getattr(qsci, "variance_estimate", None) if qsci is not None else None,
        "qsci_selected_origin_counts": (
            qsci_selection_audit.get("selected_origin_counts")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_selected_multi_origin_counts": (
            qsci_selection_audit.get("selected_multi_origin_counts")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_hartree_fock_selected": (
            qsci_selection_audit.get("hartree_fock_selected")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_sector_rejected_count": (
            qsci_selection_audit.get("sector_rejected_count")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_hamming_expansion_radius": (
            qsci_selection_audit.get("hamming_expansion_radius")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_initial_selected_subspace_size": (
            qsci_selection_audit.get("initial_selected_subspace_size")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_max_selected_subspace_size": (
            qsci_selection_audit.get("max_selected_subspace_size")
            if isinstance(qsci_selection_audit, dict)
            else None
        ),
        "qsci_residual_expansion_enabled": (
            qsci_residual_expansion.get("enabled")
            if isinstance(qsci_residual_expansion, dict)
            else None
        ),
        "qsci_residual_expansion_added_determinant_count": (
            qsci_residual_expansion.get("added_determinant_count")
            if isinstance(qsci_residual_expansion, dict)
            else None
        ),
        "qsci_residual_expansion_iteration_count": (
            qsci_residual_expansion.get("iteration_count")
            if isinstance(qsci_residual_expansion, dict)
            else None
        ),
        "qsci_ground_state_residual_norm": (
            qsci_subspace_audit.get("ground_state_residual_norm")
            if isinstance(qsci_subspace_audit, dict)
            else None
        ),
        "qsci_external_coupling_residual_norm": (
            qsci_subspace_audit.get("ground_state_external_coupling_residual_norm")
            if isinstance(qsci_subspace_audit, dict)
            else None
        ),
        "qsci_variational_upper_bound_margin_hartree": (
            qsci_subspace_audit.get("variational_upper_bound_margin_hartree")
            if isinstance(qsci_subspace_audit, dict)
            else None
        ),
        "qsci_selected_sector_coverage_fraction": (
            qsci_subspace_audit.get("selected_sector_coverage_fraction")
            if isinstance(qsci_subspace_audit, dict)
            else None
        ),
        "qsci_variational_upper_bound": (
            getattr(qsci, "variational_upper_bound", None) if qsci is not None else None
        ),
        "post_correlation_method": getattr(post, "method", None) if post is not None else None,
        "post_correlation_trust_gate": getattr(post, "trust_gate", None) if post is not None else None,
        "post_correlation_double_counting_status": (
            (getattr(post, "double_counting_audit", {}) or {}).get("status")
            if post is not None
            else None
        ),
        "post_correlation_eligibility_status": (
            (getattr(post, "correction_eligibility_audit", {}) or {}).get("status")
            if post is not None
            else None
        ),
        "post_correlation_active_ci_coefficient_count": (
            (getattr(post, "correction_eligibility_audit", {}) or {}).get(
                "eligible_coefficient_count"
            )
            if post is not None
            else None
        ),
        "post_correlation_amplitude_mapping_status": (
            (getattr(post, "amplitude_mapping_audit", {}) or {}).get("status")
            if post is not None
            else None
        ),
        "post_correlation_mapped_single_count": (
            (getattr(post, "amplitude_mapping_audit", {}) or {}).get("mapped_single_count")
            if post is not None
            else None
        ),
        "post_correlation_mapped_double_count": (
            (getattr(post, "amplitude_mapping_audit", {}) or {}).get("mapped_double_count")
            if post is not None
            else None
        ),
        "post_correlation_backend_executable": (
            (getattr(post, "correction_eligibility_audit", {}) or {}).get("backend_executable")
            if post is not None
            else None
        ),
        "post_correlation_correction_energy_emitted": (
            (getattr(post, "correction_eligibility_audit", {}) or {}).get(
                "correction_energy_emitted"
            )
            if post is not None
            else None
        ),
        "post_correlation_energy_replaces_primary": (
            (getattr(post, "correction_eligibility_audit", {}) or {}).get(
                "energy_replaces_primary"
            )
            if post is not None
            else None
        ),
        "post_correlation_required_input_missing_count": (
            (getattr(post, "correction_eligibility_audit", {}) or {}).get(
                "required_input_missing_count"
            )
            if post is not None
            else None
        ),
        "post_correlation_external_energy": (
            getattr(post, "external_correlation_energy", None) if post is not None else None
        ),
        "post_correlation_total_corrected_energy": (
            getattr(post, "total_corrected_energy", None) if post is not None else None
        ),
        "q_sc_eom_state_count": (
            len(q_sc_eom_root_audits) if excited_state is not None else None
        ),
        "q_sc_eom_max_root_residual_norm": (
            max(q_sc_eom_residuals) if q_sc_eom_residuals else None
        ),
        "q_sc_eom_min_neighbor_gap_hartree": (
            min(q_sc_eom_gaps) if q_sc_eom_gaps else None
        ),
        "q_sc_eom_conditioning_status": q_sc_eom_conditioning_status,
        "q_sc_eom_overlap_condition_number": (
            max(q_sc_eom_overlap_condition_numbers)
            if q_sc_eom_overlap_condition_numbers
            else None
        ),
        "q_sc_eom_regularization_actions": q_sc_eom_regularization_actions,
        "q_sc_eom_degenerate_root_count": (
            q_sc_eom_degenerate_root_count if q_sc_eom_root_audits else None
        ),
        "q_sc_eom_root_tracking_statuses": (
            sorted(
                {
                    str(audit.get("root_tracking_status"))
                    for audit in q_sc_eom_root_audits
                    if audit.get("root_tracking_status") is not None
                }
            )
            if q_sc_eom_root_audits
            else None
        ),
        "q_sc_eom_transition_property_status": (
            q_sc_eom_transition_property_status
            if excited_state is not None
            else None
        ),
        "q_sc_eom_transition_property_count": (
            len(q_sc_eom_transition_properties) if excited_state is not None else None
        ),
        "q_sc_eom_validated_transition_property_count": (
            len(q_sc_eom_validated_transition_properties)
            if excited_state is not None
            else None
        ),
        "q_sc_eom_transition_property_names": (
            sorted(
                {
                    str(getattr(item, "property_name"))
                    for item in q_sc_eom_transition_properties
                    if getattr(item, "property_name", None) is not None
                }
            )
            if excited_state is not None
            else None
        ),
        "q_sc_eom_transition_state_pairs": (
            [
                list(getattr(item, "state_indices", []) or [])
                for item in q_sc_eom_transition_properties
            ]
            if excited_state is not None
            else None
        ),
        "q_sc_eom_max_transition_dipole_magnitude": (
            max(q_sc_eom_transition_dipoles)
            if q_sc_eom_transition_dipoles
            else None
        ),
        "q_sc_eom_max_oscillator_strength": (
            max(q_sc_eom_oscillator_strengths)
            if q_sc_eom_oscillator_strengths
            else None
        ),
        "trust_qem_requested_methods": (
            getattr(mitigation, "requested_methods", None) if mitigation is not None else None
        ),
        "trust_qem_applied_methods": (
            getattr(mitigation, "applied_methods", None) if mitigation is not None else None
        ),
        "trust_qem_claim_allowed_methods": (
            getattr(mitigation, "claim_allowed_methods", None) if mitigation is not None else None
        ),
        "trust_qem_claim_status": (
            getattr(mitigation, "claim_status", None) if mitigation is not None else None
        ),
        "trust_qem_energy_replaces_primary": (
            getattr(mitigation, "energy_replaces_primary", None) if mitigation is not None else None
        ),
        "trust_qem_pec_status": (
            mitigation_pec.get("status") if isinstance(mitigation_pec, dict) else None
        ),
        "trust_qem_pec_executable_calibration_model": (
            mitigation_pec.get("executable_calibration_model")
            if isinstance(mitigation_pec, dict)
            else None
        ),
        "trust_qem_pec_allowed_for_claim": (
            mitigation_pec.get("allowed_for_claim") if isinstance(mitigation_pec, dict) else None
        ),
        "trust_qem_pec_calibration_model_digest": (
            mitigation_pec_audit.get("digest") if isinstance(mitigation_pec_audit, dict) else None
        ),
        "trust_qem_pec_calibrated_operation_count": (
            mitigation_pec_audit.get("calibrated_operation_count")
            if isinstance(mitigation_pec_audit, dict)
            else None
        ),
        "trust_qem_pec_quasi_probability_entry_count": (
            mitigation_pec_audit.get("quasi_probability_entry_count")
            if isinstance(mitigation_pec_audit, dict)
            else None
        ),
        "trust_qem_pec_max_operation_l1_overhead": (
            mitigation_pec_audit.get("max_operation_l1_overhead")
            if isinstance(mitigation_pec_audit, dict)
            else None
        ),
        "trust_qem_pec_sampling_overhead": (
            mitigation_pec.get("sampling_overhead") if isinstance(mitigation_pec, dict) else None
        ),
        "q_embed_verification_status": (
            getattr(embedding, "verification_status", None) if embedding is not None else None
        ),
        "q_embed_fragment_count": (
            len(getattr(embedding, "fragments", []) or []) if embedding is not None else None
        ),
        "q_embed_execution_status": (
            embedding_environment.get("embedding_execution_status")
            if isinstance(embedding_environment, dict)
            else None
        ),
        "q_embed_self_consistency_loop_executed": (
            embedding_boundary.get("self_consistency_loop_executed")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_self_consistency_iteration_count": (
            embedding_boundary.get("self_consistency_iteration_count")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_density_matching_performed": (
            embedding_boundary.get("density_matching_performed")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_density_matching_iteration_count": (
            embedding_boundary.get("density_matching_iteration_count")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_density_mismatch_status": embedding_first_density_audit.get("status"),
        "q_embed_density_mismatch_audit_status": (
            embedding_density_audit.get("status")
            or embedding_first_density_audit.get("mismatch_status")
        ),
        "q_embed_fragment_population_delta_norm": (
            embedding_boundary.get("fragment_population_delta_norm")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_density_mismatch_l1_norm": (
            embedding_boundary.get("fragment_population_delta_l1_norm")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_density_mismatch_signed_sum": (
            embedding_boundary.get("fragment_population_delta_signed_sum")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_density_mismatch_threshold": (
            embedding_density_audit.get("threshold")
            or embedding_first_density_audit.get("density_mismatch_threshold")
        ),
        "q_embed_max_fragment_population_delta_abs": (
            embedding_boundary.get("max_fragment_population_delta_abs")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_correlation_potential_parameter_count": (
            embedding_boundary.get("correlation_potential_parameter_count")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_fragment_ao_coverage_fraction": embedding_fragment_coverage.get(
            "ao_coverage_fraction"
        ),
        "q_embed_fragment_atom_coverage_fraction": embedding_fragment_coverage.get(
            "atom_coverage_fraction"
        ),
        "q_embed_fragment_coverage_status": embedding_fragment_coverage.get("status"),
        "q_embed_fragment_energy_sum_gap_hartree": (
            embedding_boundary.get("fragment_energy_sum_gap_hartree")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_fragment_energy_sum_gap_abs_hartree": (
            embedding_boundary.get("fragment_energy_sum_gap_abs_hartree")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_fragment_energy_sum_gap_per_fragment_hartree": (
            embedding_boundary.get("fragment_energy_sum_gap_per_fragment_hartree")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "q_embed_fragment_energy_sum_replaces_primary": (
            embedding_boundary.get("fragment_energy_sum_replaces_primary")
            if isinstance(embedding_boundary, dict)
            else None
        ),
        "kq_pbc_kpoint_count": (
            len(getattr(kq_pbc, "kpoints", []) or []) if kq_pbc is not None else None
        ),
        "kq_pbc_kpoints": getattr(kq_pbc, "kpoints", None) if kq_pbc is not None else None,
        "kq_pbc_trust_tier": getattr(kq_pbc, "pbc_trust_tier", None) if kq_pbc is not None else None,
        "kq_pbc_twist_energy_statuses": (
            sorted(
                {
                    str(item.get("energy_status"))
                    for item in kq_twist_energies
                    if isinstance(item, dict) and item.get("energy_status") is not None
                }
            )
            if kq_pbc is not None
            else None
        ),
        "kq_pbc_non_gamma_status": (
            kq_non_gamma_audit.get("status") if isinstance(kq_non_gamma_audit, dict) else None
        ),
        "kq_pbc_mesh_mismatch": (
            kq_non_gamma_audit.get("mesh_mismatch") if isinstance(kq_non_gamma_audit, dict) else None
        ),
        "kq_pbc_named_kpoint_coverage_fraction": (
            kq_coverage_audit.get("named_kpoint_execution_coverage_fraction")
            if isinstance(kq_coverage_audit, dict)
            else None
        ),
        "kq_pbc_mesh_kpoint_coverage_fraction": (
            kq_coverage_audit.get("mesh_kpoint_execution_coverage_fraction")
            if isinstance(kq_coverage_audit, dict)
            else None
        ),
        "kq_pbc_twist_energy_coverage_fraction": (
            kq_coverage_audit.get("twist_energy_coverage_fraction")
            if isinstance(kq_coverage_audit, dict)
            else None
        ),
        "kq_pbc_missing_twist_energy_fraction": (
            kq_coverage_audit.get("missing_twist_energy_fraction")
            if isinstance(kq_coverage_audit, dict)
            else None
        ),
        "kq_pbc_promotion_readiness_status": (
            kq_promotion_readiness.get("status")
            if isinstance(kq_promotion_readiness, dict)
            else None
        ),
        "kq_pbc_readiness_level": (
            kq_promotion_readiness.get("readiness_level")
            if isinstance(kq_promotion_readiness, dict)
            else None
        ),
        "kq_pbc_requested_kpoint_count": (
            kq_non_gamma_audit.get("requested_kpoint_count") if isinstance(kq_non_gamma_audit, dict) else None
        ),
        "kq_pbc_execution_kpoint_count": (
            kq_non_gamma_audit.get("execution_kpoint_count") if isinstance(kq_non_gamma_audit, dict) else None
        ),
        "kq_pbc_executable_scope": (
            kq_non_gamma_audit.get("executable_scope") if isinstance(kq_non_gamma_audit, dict) else None
        ),
        "kq_pbc_promotion_blockers": (
            kq_non_gamma_audit.get("promotion_blockers") if isinstance(kq_non_gamma_audit, dict) else None
        ),
        "kq_pbc_promotion_blocker_count": (
            kq_promotion_readiness.get("promotion_blocker_count")
            if isinstance(kq_promotion_readiness, dict)
            else kq_non_gamma_audit.get("promotion_blocker_count")
            if isinstance(kq_non_gamma_audit, dict)
            else None
        ),
        "kq_pbc_unsupported_claim_count": (
            kq_promotion_readiness.get("unsupported_claim_count")
            if isinstance(kq_promotion_readiness, dict)
            else kq_non_gamma_audit.get("unsupported_claim_count")
            if isinstance(kq_non_gamma_audit, dict)
            else None
        ),
        "kq_pbc_energy_replaces_primary": (
            kq_non_gamma_audit.get("energy_replaces_primary")
            if isinstance(kq_non_gamma_audit, dict)
            else None
        ),
        "kq_pbc_runtime_submission_allowed": (
            kq_non_gamma_audit.get("runtime_submission_allowed")
            if isinstance(kq_non_gamma_audit, dict)
            else None
        ),
        "kq_pbc_finite_size_status": (
            kq_finite_size.get("status") if isinstance(kq_finite_size, dict) else None
        ),
        "kq_pbc_missing_twist_energy_count": (
            kq_finite_size.get("missing_twist_energy_count") if isinstance(kq_finite_size, dict) else None
        ),
        "kq_pbc_proxy_energy_present": (
            any(
                isinstance(item, dict) and "solver_energy_proxy_hartree" in item
                for item in kq_twist_energies
            )
            if kq_pbc is not None
            else None
        ),
        "ft_qpe_recommended_encoding": ft_best_encoding,
        "ft_qpe_reference_encoding": ft_reference_encoding if ft_qpe is not None else None,
        "ft_qpe_encoding_comparison_count": (
            ft_readiness_audit.get("encoding_comparison_count")
            if isinstance(ft_readiness_audit, dict)
            else None
        ),
        "ft_qpe_best_toffoli_count": ft_best_toffoli,
        "ft_qpe_double_factorization_toffoli_count": ft_reference_toffoli,
        "ft_qpe_reduction_vs_double_factorization": ft_reduction,
        "ft_qpe_best_to_reference_toffoli_ratio": (
            ft_resource_audit.get("best_to_reference_toffoli_ratio")
            if isinstance(ft_resource_audit, dict)
            else None
        ),
        "ft_qpe_lambda_reduction_vs_double_factorization": ft_lambda_reduction,
        "ft_qpe_resource_model_scope": (
            ft_resource_audit.get("model_scope") if isinstance(ft_resource_audit, dict) else None
        ),
        "ft_qpe_resource_formula_scope": (
            ft_formula_audit.get("scope") if isinstance(ft_formula_audit, dict) else None
        ),
        "ft_qpe_resource_claim_status": (
            ft_resource_audit.get("resource_claim_status") if isinstance(ft_resource_audit, dict) else None
        ),
        "ft_qpe_promotion_readiness_status": (
            ft_readiness_audit.get("status") if isinstance(ft_readiness_audit, dict) else None
        ),
        "ft_qpe_readiness_level": (
            ft_readiness_audit.get("readiness_level")
            if isinstance(ft_readiness_audit, dict)
            else None
        ),
        "ft_qpe_compiled_circuit_available": (
            ft_resource_audit.get("compiled_fault_tolerant_circuit_available")
            if isinstance(ft_resource_audit, dict)
            else None
        ),
        "ft_qpe_surface_code_distance_available": (
            ft_resource_audit.get("surface_code_distance_available")
            if isinstance(ft_resource_audit, dict)
            else None
        ),
        "ft_qpe_logical_error_budget_available": (
            ft_readiness_audit.get("logical_error_budget_available")
            if isinstance(ft_readiness_audit, dict)
            else None
        ),
        "ft_qpe_validated_resource_advantage_claim_allowed": (
            ft_readiness_audit.get("validated_resource_advantage_claim_allowed")
            if isinstance(ft_readiness_audit, dict)
            else None
        ),
        "ft_qpe_required_promotion_evidence_count": (
            ft_readiness_audit.get("required_promotion_evidence_count")
            if isinstance(ft_readiness_audit, dict)
            else None
        ),
        "ft_qpe_surface_code_overhead_factor": (
            ft_resource_audit.get("surface_code_overhead_factor")
            if isinstance(ft_resource_audit, dict)
            else None
        ),
        "ft_qpe_promotion_blockers": (
            ft_resource_audit.get("promotion_blockers") if isinstance(ft_resource_audit, dict) else None
        ),
        "shadow_lr_basis_count": (
            len(getattr(measurement, "shadow_bases", []) or [])
            if measurement is not None and getattr(measurement, "planner", "") == "shadow_lr"
            else None
        ),
        "shadow_lr_predicted_variance": (
            getattr(measurement, "predicted_variance", None)
            if measurement is not None and getattr(measurement, "planner", "") == "shadow_lr"
            else None
        ),
        "shadow_lr_allocated_shots": (
            measurement_cost_model.get("allocated_shots")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_grouped_precision_baseline_shots": (
            measurement_cost_model.get("grouped_precision_baseline_shots")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_cost_reduction_vs_grouped_precision": (
            getattr(measurement, "cost_reduction_ratio", None)
            if measurement is not None and getattr(measurement, "planner", "") == "shadow_lr"
            else None
        ),
        "shadow_lr_basis_l1_coverage_fraction": (
            measurement_cost_model.get("basis_l1_coverage_fraction")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_unselected_basis_count": (
            measurement_cost_model.get("unselected_basis_count")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_max_allocated_shot_fraction": (
            measurement_cost_model.get("max_allocated_shot_fraction")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_allocation_entropy": (
            measurement_cost_model.get("allocation_entropy")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_grouped_precision_variance_proxy": (
            measurement_cost_model.get("grouped_precision_variance_proxy")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_variance_inflation_vs_grouped_precision_proxy": (
            measurement_cost_model.get("variance_inflation_vs_grouped_precision_proxy")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
        "shadow_lr_plan_digest": (
            measurement_cost_model.get("plan_digest")
            if measurement is not None
            and getattr(measurement, "planner", "") == "shadow_lr"
            and isinstance(measurement_cost_model, dict)
            else None
        ),
    }


def _float_metric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _accuracy_outcome(
    baseline_error: float | None,
    method_error: float | None,
    *,
    tolerance: float = 1.0e-12,
) -> str:
    if baseline_error is None or method_error is None:
        return "unavailable"
    if baseline_error == 0.0:
        return "matches_exact_within_tolerance" if method_error <= tolerance else "no_accuracy_advantage"
    if method_error < baseline_error - tolerance:
        return "lower_error"
    if abs(method_error - baseline_error) <= tolerance:
        return "tied_with_baseline"
    return "higher_error"


def _method_evidence_comparison_pair(
    *,
    method_case: BenchmarkCaseResult,
    baseline_case: BenchmarkCaseResult,
) -> dict[str, Any]:
    baseline_error = _float_metric(baseline_case.absolute_error)
    method_error = _float_metric(method_case.absolute_error)
    method_specific_error = None
    method_specific_metric = None
    method_case_methods = _string_list(method_case.metrics.get("method_evidence_methods"))
    if "qsci_plus_result" in method_case_methods:
        qsci_margin = _float_metric(method_case.metrics.get("qsci_variational_upper_bound_margin_hartree"))
        if qsci_margin is not None:
            method_specific_error = abs(qsci_margin)
            method_specific_metric = "qsci_variational_upper_bound_margin_hartree_abs"
    baseline_cost = _float_metric(baseline_case.metrics.get("estimated_measurement_cost"))
    method_cost = _float_metric(method_case.metrics.get("estimated_measurement_cost"))
    baseline_wall = _float_metric(baseline_case.metrics.get("wall_time_seconds"))
    method_wall = _float_metric(method_case.metrics.get("wall_time_seconds"))
    primary_case_accuracy_outcome = _accuracy_outcome(baseline_error, method_error)
    return {
        "baseline_case": baseline_case.name,
        "method_case": method_case.name,
        "baseline_status": baseline_case.status,
        "method_status": method_case.status,
        "method_evidence_methods": method_case_methods,
        "baseline_absolute_error": baseline_error,
        "method_primary_case_absolute_error": method_error,
        "method_specific_absolute_error": method_specific_error,
        "method_specific_accuracy_metric": method_specific_metric,
        "method_absolute_error": (
            method_specific_error if method_specific_error is not None else method_error
        ),
        "primary_case_accuracy_outcome": primary_case_accuracy_outcome,
        "accuracy_outcome": _accuracy_outcome(
            baseline_error,
            method_specific_error if method_specific_error is not None else method_error,
        ),
        "absolute_error_ratio_method_over_baseline": (
            (method_specific_error if method_specific_error is not None else method_error) / baseline_error
            if baseline_error not in (None, 0.0)
            and (method_specific_error if method_specific_error is not None else method_error) is not None
            else None
        ),
        "baseline_estimated_measurement_cost": baseline_cost,
        "method_estimated_measurement_cost": method_cost,
        "estimated_cost_ratio_method_over_baseline": (
            method_cost / baseline_cost
            if baseline_cost not in (None, 0.0) and method_cost is not None
            else None
        ),
        "baseline_wall_time_seconds": baseline_wall,
        "method_wall_time_seconds": method_wall,
        "wall_time_ratio_method_over_baseline": (
            method_wall / baseline_wall
            if baseline_wall not in (None, 0.0) and method_wall is not None
            else None
        ),
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _has_present_payload(payload: dict[str, Any], key: str | None) -> bool:
    if key is None:
        return False
    value = payload.get(key)
    if key == "measurement" and isinstance(value, dict):
        return value.get("planner") == "shadow_lr"
    if key == "mitigation" and isinstance(value, dict):
        return bool(value.get("requested_methods") or value.get("applied_methods"))
    return value not in (None, {}, [])


def _build_method_contract_matrix(method_cases: list[BenchmarkCaseResult]) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    for method_key, contract in METHOD_EVIDENCE_CONTRACTS.items():
        rows: list[dict[str, Any]] = []
        metric_keys = [str(item) for item in contract.get("metric_keys", [])]
        report_tokens = [str(item) for item in contract.get("report_tokens", [])]
        result_field = str(contract.get("result_field"))
        for case in method_cases:
            case_methods = case.metrics.get("method_evidence_methods") or []
            if method_key not in case_methods:
                continue
            artifact_root = Path(str(case.artifact_root)) if case.artifact_root is not None else None
            result_payload: dict[str, Any] = {}
            sidecar_payload: dict[str, Any] = {}
            qcschema_payload: dict[str, Any] = {}
            report_text = ""
            if artifact_root is not None:
                result_payload = _read_json_object(artifact_root / "result.json")
                sidecar_payload = _read_json_object(artifact_root / "method_evidence.json")
                qcschema_payload = _read_json_object(artifact_root / "qcschema.json")
                try:
                    report_text = (artifact_root / "report.md").read_text(encoding="utf-8")
                except OSError:
                    report_text = ""
            result_method_summary = (
                ((result_payload.get("method_evidence") or {}).get("methods") or {})
                if isinstance(result_payload.get("method_evidence"), dict)
                else {}
            )
            sidecar_methods = (
                sidecar_payload.get("methods")
                if isinstance(sidecar_payload.get("methods"), dict)
                else {}
            )
            promotion_records = (
                (sidecar_payload.get("promotion_gate_audit") or {}).get("method_records") or {}
                if isinstance(sidecar_payload.get("promotion_gate_audit"), dict)
                else {}
            )
            qcschema_extras = (
                qcschema_payload.get("extras")
                if isinstance(qcschema_payload.get("extras"), dict)
                else {}
            )
            qcschema_method_summary = (
                ((qcschema_extras.get("method_evidence") or {}).get("methods") or {})
                if isinstance(qcschema_extras.get("method_evidence"), dict)
                else {}
            )
            row = {
                "case_name": case.name,
                "artifact_root": str(artifact_root) if artifact_root is not None else None,
                "status": case.status,
                "result_method_summary_present": method_key in result_method_summary,
                "result_detail_present": _has_present_payload(result_payload, result_field),
                "sidecar_method_present": method_key in sidecar_methods,
                "promotion_gate_record_present": method_key in promotion_records,
                "report_mentions_method": all(token in report_text for token in report_tokens),
                "qcschema_file_present": bool(qcschema_payload),
                "qcschema_method_summary_present": method_key in qcschema_method_summary,
                "metric_keys_present": all(case.metrics.get(key) is not None for key in metric_keys),
            }
            row["contract_passed"] = all(
                bool(row[key])
                for key in (
                    "result_method_summary_present",
                    "result_detail_present",
                    "sidecar_method_present",
                    "promotion_gate_record_present",
                    "report_mentions_method",
                    "qcschema_file_present",
                    "qcschema_method_summary_present",
                    "metric_keys_present",
                )
            )
            rows.append(row)
        matrix[method_key] = {
            "display_name": contract.get("display_name"),
            "result_field": result_field,
            "metric_keys": metric_keys,
            "report_tokens": report_tokens,
            "case_count": len(rows),
            "passing_case_count": sum(1 for row in rows if row.get("contract_passed")),
            "contract_passed": bool(rows) and all(row.get("contract_passed") for row in rows),
            "cases": rows,
        }

    missing_methods = [
        method for method, entry in matrix.items() if not entry.get("contract_passed")
    ]
    return {
        "schema_version": "qcchem.method_evidence_contract_matrix.v0.1-alpha",
        "expected_method_count": len(METHOD_EVIDENCE_CONTRACTS),
        "covered_method_count": len(METHOD_EVIDENCE_CONTRACTS) - len(missing_methods),
        "status": "complete" if not missing_methods else "incomplete",
        "missing_methods": missing_methods,
        "methods": matrix,
        "required_surfaces": [
            "result.method_evidence.methods",
            "result.<method_detail>",
            "method_evidence.json.methods",
            "method_evidence.json.promotion_gate_audit.method_records",
            "report.md",
            "qcschema.json.extras.method_evidence.methods",
            "benchmark_case.metrics",
        ],
    }


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list | tuple):
        return [str(item) for item in value]
    if isinstance(value, set):
        return sorted(str(item) for item in value)
    return []


def _build_method_superiority_audit(
    *,
    method_cases: list[BenchmarkCaseResult],
    cases_by_name: dict[str, BenchmarkCaseResult],
    comparison_pairs: dict[str, dict[str, Any]],
    contract_matrix: dict[str, Any],
) -> dict[str, Any]:
    methods: dict[str, dict[str, Any]] = {}
    claim_allowed_methods: list[str] = []

    for method_key, contract in METHOD_EVIDENCE_CONTRACTS.items():
        related_cases = [
            case
            for case in method_cases
            if method_key in _string_list(case.metrics.get("method_evidence_methods"))
        ]
        related_pairs = {
            name: pair
            for name, pair in comparison_pairs.items()
            if method_key in _string_list(pair.get("method_evidence_methods"))
        }
        accuracy_advantage_pair_names = [
            name
            for name, pair in related_pairs.items()
            if pair.get("accuracy_outcome") == "lower_error"
        ]
        exact_match_pair_names = [
            name
            for name, pair in related_pairs.items()
            if pair.get("accuracy_outcome") == "matches_exact_within_tolerance"
        ]
        no_accuracy_advantage_pair_names = [
            name
            for name, pair in related_pairs.items()
            if pair.get("accuracy_outcome")
            in {"higher_error", "tied_with_baseline", "no_accuracy_advantage"}
        ]
        estimated_cost_advantage_pair_names = [
            name
            for name, pair in related_pairs.items()
            if (
                _float_metric(pair.get("estimated_cost_ratio_method_over_baseline")) is not None
                and float(pair["estimated_cost_ratio_method_over_baseline"]) < 1.0
            )
        ]

        def _method_case_metric_list(pair: dict[str, Any], metric_key: str) -> list[str]:
            method_case = cases_by_name.get(str(pair.get("method_case")))
            if method_case is None:
                return []
            return _string_list(method_case.metrics.get(metric_key))

        method_specific_estimated_cost_advantage_pair_names = [
            name
            for name, pair in related_pairs.items()
            if (
                _float_metric(pair.get("estimated_cost_ratio_method_over_baseline")) is not None
                and float(pair["estimated_cost_ratio_method_over_baseline"]) < 1.0
                and (
                    method_key
                    in _method_case_metric_list(
                        pair,
                        "method_evidence_planning_metric_methods",
                    )
                    or method_key
                    in _method_case_metric_list(
                        pair,
                        "method_evidence_resource_model_only_methods",
                    )
                    or len(_string_list(pair.get("method_evidence_methods"))) == 1
                )
            )
        ]
        pair_level_only_estimated_cost_advantage_pair_names = sorted(
            set(estimated_cost_advantage_pair_names)
            - set(method_specific_estimated_cost_advantage_pair_names)
        )
        planning_metric_cost_advantage_pair_names = [
            name
            for name, pair in related_pairs.items()
            if (
                _float_metric(pair.get("estimated_cost_ratio_method_over_baseline")) is not None
                and float(pair["estimated_cost_ratio_method_over_baseline"]) < 1.0
                and cases_by_name.get(str(pair.get("method_case"))) is not None
                and method_key
                in _string_list(
                    cases_by_name[str(pair["method_case"])].metrics.get(
                        "method_evidence_planning_metric_methods"
                    )
                )
            )
        ]
        resource_model_case_names = [
            case.name
            for case in related_cases
            if method_key
            in _string_list(case.metrics.get("method_evidence_resource_model_only_methods"))
        ]
        unsupported_case_names = [
            case.name
            for case in related_cases
            if method_key
            in _string_list(case.metrics.get("method_evidence_unsupported_for_claim_methods"))
        ]
        optimization_signal_case_names = [
            case.name
            for case in related_cases
            if method_key == "e_adapt_result"
            and case.metrics.get("e_adapt_optimization_signal_present") is True
        ]
        energy_replacement_allowed = any(
            method_key
            in _string_list(
                case.metrics.get("method_evidence_sidecar_energy_replacement_allowed_methods")
            )
            for case in related_cases
        )
        accuracy_claim_allowed = any(
            method_key
            in _string_list(case.metrics.get("method_evidence_accuracy_claim_allowed_methods"))
            for case in related_cases
        )
        hardware_claim_allowed = any(
            method_key
            in _string_list(case.metrics.get("method_evidence_hardware_claim_allowed_methods"))
            for case in related_cases
        )
        if energy_replacement_allowed or accuracy_claim_allowed or hardware_claim_allowed:
            claim_allowed_methods.append(method_key)

        contract_entry = (contract_matrix.get("methods") or {}).get(method_key, {})
        promotion_blockers = ["promotion_gate_required_for_validated_claim"]
        if not contract_entry.get("contract_passed"):
            promotion_blockers.append("method_contract_incomplete")
        if not energy_replacement_allowed:
            promotion_blockers.append("sidecar_energy_replacement_not_allowed")
        if not accuracy_claim_allowed:
            promotion_blockers.append("accuracy_claim_not_allowed")
        if not hardware_claim_allowed:
            promotion_blockers.append("hardware_claim_not_allowed")
        if not accuracy_advantage_pair_names:
            promotion_blockers.append("no_accuracy_advantage_pair")
        if planning_metric_cost_advantage_pair_names:
            promotion_blockers.append("planning_metric_not_hardware_validation")
        if pair_level_only_estimated_cost_advantage_pair_names:
            promotion_blockers.append("pair_level_cost_advantage_not_method_specific")
        if optimization_signal_case_names:
            promotion_blockers.append("optimization_signal_requires_accuracy_gate")
        if resource_model_case_names:
            promotion_blockers.append("resource_model_only_no_compiled_circuit")
        if unsupported_case_names:
            promotion_blockers.append("unsupported_for_claim_path_present")

        if energy_replacement_allowed or accuracy_claim_allowed or hardware_claim_allowed:
            conclusion = "claim_allowed_by_promotion_gate"
        elif accuracy_advantage_pair_names:
            conclusion = "accuracy_signal_requires_promotion"
        elif optimization_signal_case_names:
            conclusion = "optimization_signal_requires_promotion"
        elif resource_model_case_names:
            conclusion = "resource_model_advantage_only"
        elif planning_metric_cost_advantage_pair_names:
            conclusion = "planning_cost_advantage_only"
        elif exact_match_pair_names:
            conclusion = "matches_exact_smoke_not_superior"
        elif method_specific_estimated_cost_advantage_pair_names:
            conclusion = "estimated_cost_difference_without_method_claim"
        elif related_pairs:
            conclusion = "no_superiority_observed"
        else:
            conclusion = "evidence_present_not_comparative"

        methods[method_key] = {
            "display_name": contract.get("display_name"),
            "case_names": [case.name for case in related_cases],
            "case_count": len(related_cases),
            "contract_passed": bool(contract_entry.get("contract_passed")),
            "comparison_pair_names": sorted(related_pairs),
            "accuracy_outcome_counts": {
                outcome: sum(
                    1
                    for pair in related_pairs.values()
                    if pair.get("accuracy_outcome") == outcome
                )
                for outcome in sorted(
                    {
                        str(pair.get("accuracy_outcome"))
                        for pair in related_pairs.values()
                        if pair.get("accuracy_outcome") is not None
                    }
                )
            },
            "accuracy_advantage_pair_names": accuracy_advantage_pair_names,
            "exact_match_pair_names": exact_match_pair_names,
            "no_accuracy_advantage_pair_names": no_accuracy_advantage_pair_names,
            "estimated_cost_advantage_pair_names": estimated_cost_advantage_pair_names,
            "method_specific_estimated_cost_advantage_pair_names": (
                method_specific_estimated_cost_advantage_pair_names
            ),
            "pair_level_only_estimated_cost_advantage_pair_names": (
                pair_level_only_estimated_cost_advantage_pair_names
            ),
            "planning_metric_cost_advantage_pair_names": (
                planning_metric_cost_advantage_pair_names
            ),
            "optimization_signal_case_names": optimization_signal_case_names,
            "resource_model_case_names": resource_model_case_names,
            "unsupported_for_claim_case_names": unsupported_case_names,
            "energy_replacement_allowed": energy_replacement_allowed,
            "accuracy_claim_allowed": accuracy_claim_allowed,
            "hardware_claim_allowed": hardware_claim_allowed,
            "superiority_conclusion": conclusion,
            "promotion_blockers": sorted(set(promotion_blockers)),
        }

    return {
        "schema_version": "qcchem.method_superiority_audit.v0.1-alpha",
        "status": "claim_allowed" if claim_allowed_methods else "promotion_required",
        "method_count": len(methods),
        "claim_allowed_methods": sorted(claim_allowed_methods),
        "scope": (
            "fast_gate_pairwise_accuracy_cost_resource_audit; no hardware or "
            "validated chemistry promotion is implied"
        ),
        "methods": methods,
    }


def _build_method_evidence_campaign_summary(case_results: list[BenchmarkCaseResult]) -> dict[str, Any]:
    cases_by_name = {case.name: case for case in case_results}
    method_cases = [
        case
        for case in case_results
        if case.metrics.get("method_evidence_available")
        or case.metrics.get("method_evidence_methods")
    ]
    method_counts: dict[str, int] = {}
    for case in method_cases:
        for method in case.metrics.get("method_evidence_methods") or []:
            method_counts[str(method)] = method_counts.get(str(method), 0) + 1

    comparison_specs = [
        ("h2_qsci_plus", "h2_exact_baseline"),
        ("h2_trust_qem", "h2_exact_baseline"),
        ("h2_q_sc_eom", "h2_exact_baseline"),
        ("h2_q_embed", "h2_exact_baseline"),
        ("h2_method_evidence_smoke", "h2_exact_baseline"),
        ("lih_shadow_lr_e_adapt", "lih_active_vqe_statevector_baseline"),
        ("h2_oo_qcasscf", "h2_exact_baseline"),
    ]
    comparison_pairs: dict[str, dict[str, Any]] = {}
    for method_name, baseline_name in comparison_specs:
        method_case = cases_by_name.get(method_name)
        baseline_case = cases_by_name.get(baseline_name)
        if method_case is None or baseline_case is None:
            continue
        comparison_pairs[f"{method_name}_vs_{baseline_name}"] = _method_evidence_comparison_pair(
            method_case=method_case,
            baseline_case=baseline_case,
        )
    method_case_suffixes = (
        "_qsci_plus",
        "_trust_qem",
        "_q_sc_eom",
        "_q_embed",
        "_method_evidence_smoke",
        "_shadow_lr_e_adapt",
        "_oo_qcasscf",
        "_ft_qpe_planner",
        "_kq_pbc",
    )
    for method_case in method_cases:
        for suffix in method_case_suffixes:
            if not method_case.name.endswith(suffix):
                continue
            prefix = method_case.name[: -len(suffix)]
            for baseline_name in (
                f"{prefix}_exact_baseline",
                f"{prefix}_statevector_baseline",
                f"{prefix}_baseline",
            ):
                baseline_case = cases_by_name.get(baseline_name)
                if baseline_case is None:
                    continue
                pair_name = f"{method_case.name}_vs_{baseline_name}"
                comparison_pairs.setdefault(
                    pair_name,
                    _method_evidence_comparison_pair(
                        method_case=method_case,
                        baseline_case=baseline_case,
                    ),
                )
                break
            break

    ft_resource_findings: dict[str, dict[str, Any]] = {}
    for case in method_cases:
        reduction = _float_metric(case.metrics.get("ft_qpe_reduction_vs_double_factorization"))
        if reduction is None:
            continue
        ft_resource_findings[case.name] = {
            "recommended_encoding": case.metrics.get("ft_qpe_recommended_encoding"),
            "reference_encoding": case.metrics.get("ft_qpe_reference_encoding"),
            "encoding_comparison_count": case.metrics.get("ft_qpe_encoding_comparison_count"),
            "toffoli_reduction_vs_double_factorization": reduction,
            "best_to_reference_toffoli_ratio": case.metrics.get(
                "ft_qpe_best_to_reference_toffoli_ratio"
            ),
            "lambda_reduction_vs_double_factorization": case.metrics.get(
                "ft_qpe_lambda_reduction_vs_double_factorization"
            ),
            "best_toffoli_count": case.metrics.get("ft_qpe_best_toffoli_count"),
            "double_factorization_toffoli_count": case.metrics.get(
                "ft_qpe_double_factorization_toffoli_count"
            ),
            "resource_model_scope": case.metrics.get("ft_qpe_resource_model_scope"),
            "resource_formula_scope": case.metrics.get("ft_qpe_resource_formula_scope"),
            "resource_claim_status": case.metrics.get("ft_qpe_resource_claim_status"),
            "promotion_readiness_status": case.metrics.get(
                "ft_qpe_promotion_readiness_status"
            ),
            "readiness_level": case.metrics.get("ft_qpe_readiness_level"),
            "compiled_circuit_available": case.metrics.get("ft_qpe_compiled_circuit_available"),
            "surface_code_distance_available": case.metrics.get(
                "ft_qpe_surface_code_distance_available"
            ),
            "logical_error_budget_available": case.metrics.get(
                "ft_qpe_logical_error_budget_available"
            ),
            "validated_resource_advantage_claim_allowed": case.metrics.get(
                "ft_qpe_validated_resource_advantage_claim_allowed"
            ),
            "required_promotion_evidence_count": case.metrics.get(
                "ft_qpe_required_promotion_evidence_count"
            ),
            "surface_code_overhead_factor": case.metrics.get(
                "ft_qpe_surface_code_overhead_factor"
            ),
            "promotion_blockers": case.metrics.get("ft_qpe_promotion_blockers"),
            "trust_boundary": "resource_model_only",
        }

    promotion_gate_summary = {
        "case_count": sum(
            1
            for case in method_cases
            if case.metrics.get("method_evidence_promotion_gate_status") is not None
        ),
        "energy_replacement_allowed_cases": [
            case.name
            for case in method_cases
            if case.metrics.get("method_evidence_sidecar_energy_replacement_allowed_methods")
        ],
        "accuracy_claim_allowed_cases": [
            case.name
            for case in method_cases
            if case.metrics.get("method_evidence_accuracy_claim_allowed_methods")
        ],
        "hardware_claim_allowed_cases": [
            case.name
            for case in method_cases
            if case.metrics.get("method_evidence_hardware_claim_allowed_methods")
        ],
        "planning_metric_cases": {
            case.name: case.metrics.get("method_evidence_planning_metric_methods")
            for case in method_cases
            if case.metrics.get("method_evidence_planning_metric_methods")
        },
        "resource_model_only_cases": {
            case.name: case.metrics.get("method_evidence_resource_model_only_methods")
            for case in method_cases
            if case.metrics.get("method_evidence_resource_model_only_methods")
        },
        "unsupported_for_claim_cases": {
            case.name: case.metrics.get("method_evidence_unsupported_for_claim_methods")
            for case in method_cases
            if case.metrics.get("method_evidence_unsupported_for_claim_methods")
        },
        "overall_claim_status": "promotion_required",
        "primary_energy_policy": "raw_solver_energy_remains_primary",
    }
    contract_matrix = _build_method_contract_matrix(method_cases)
    superiority_audit = _build_method_superiority_audit(
        method_cases=method_cases,
        cases_by_name=cases_by_name,
        comparison_pairs=comparison_pairs,
        contract_matrix=contract_matrix,
    )

    accuracy_advantage_pairs = [
        name
        for name, pair in comparison_pairs.items()
        if pair.get("accuracy_outcome") == "lower_error"
    ]
    exact_match_pairs = [
        name
        for name, pair in comparison_pairs.items()
        if pair.get("accuracy_outcome") == "matches_exact_within_tolerance"
    ]
    estimated_cost_advantage_pairs = [
        name
        for name, pair in comparison_pairs.items()
        if (
            _float_metric(pair.get("estimated_cost_ratio_method_over_baseline")) is not None
            and float(pair["estimated_cost_ratio_method_over_baseline"]) < 1.0
        )
    ]
    planning_metric_cost_advantage_pairs = [
        name
        for name, pair in comparison_pairs.items()
        if (
            _float_metric(pair.get("estimated_cost_ratio_method_over_baseline")) is not None
            and float(pair["estimated_cost_ratio_method_over_baseline"]) < 1.0
            and cases_by_name.get(str(pair.get("method_case"))) is not None
            and cases_by_name[str(pair["method_case"])].metrics.get(
                "method_evidence_planning_metric_methods"
            )
        )
    ]
    headline_findings: list[str] = [
        "Method Evidence benchmark summaries do not promote exploratory methods by themselves.",
    ]
    if accuracy_advantage_pairs:
        headline_findings.append(
            "Some method cases lower exact-baseline error relative to their configured baseline."
        )
    else:
        headline_findings.append(
            "No method-evidence case in this stable fast gate beats its ideal exact/statevector baseline."
        )
    if exact_match_pairs:
        headline_findings.append(
            "Some H2 method cases match the exact baseline within numerical tolerance."
        )
    if estimated_cost_advantage_pairs:
        headline_findings.append(
            "Some method cases reduce estimated measurement cost; this is a planning metric, not hardware validation."
        )
    if planning_metric_cost_advantage_pairs:
        headline_findings.append(
            "Planning-metric cost advantages are tracked separately from configuration-only estimated-cost differences."
        )
    if ft_resource_findings:
        headline_findings.append(
            "FT-QPE Planner reports resource-model reductions; these are not compiled fault-tolerant circuits."
        )
    if promotion_gate_summary["case_count"]:
        headline_findings.append(
            "Method promotion gates keep sidecar evidence separate from energy replacement and validated-claim promotion."
        )
    if contract_matrix["status"] == "complete":
        headline_findings.append(
            "All 10 Method Evidence entries are covered across result, sidecar, report, QCSchema, promotion-gate, and benchmark metric surfaces."
        )

    return {
        "available": bool(method_cases),
        "schema_version": "qcchem.method_evidence_benchmark_summary.v0.1-alpha",
        "method_case_count": len(method_cases),
        "method_counts": dict(sorted(method_counts.items())),
        "contract_matrix": contract_matrix,
        "comparison_pairs": comparison_pairs,
        "accuracy_advantage_pairs": accuracy_advantage_pairs,
        "exact_match_pairs": exact_match_pairs,
        "estimated_cost_advantage_pairs": estimated_cost_advantage_pairs,
        "planning_metric_cost_advantage_pairs": planning_metric_cost_advantage_pairs,
        "ft_qpe_resource_findings": ft_resource_findings,
        "promotion_gate_summary": promotion_gate_summary,
        "method_superiority_audit": superiority_audit,
        "headline_findings": headline_findings,
        "promotion_boundary": (
            "Exploratory method evidence, post-correlation, mitigation, PBC audit, "
            "and resource estimates require separate benchmark gates before promotion."
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
    method_evidence_metrics = _method_evidence_case_metrics(result)
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
            **method_evidence_metrics,
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
                    "method_evidence_methods": method_evidence_metrics["method_evidence_methods"],
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


def _pbc_qmmm_validation_case_metrics(summary: dict[str, Any], *, profile: str) -> dict[str, Any]:
    metrics = list(summary.get("metrics") or [])
    artifacts = dict(summary.get("artifacts") or {})
    failed_cases = [item.get("case") for item in metrics if not item.get("passed")]
    return {
        "comparison_target": "pbc_qmmm_validation",
        "pbc_qmmm_validation_profile": profile,
        "pbc_qmmm_validation_overall_status": summary.get("overall_status"),
        "pbc_qmmm_validation_case_count": summary.get("case_count"),
        "pbc_qmmm_validation_passed_cases": summary.get("passed_cases"),
        "pbc_qmmm_validation_failed_cases": failed_cases,
        "pbc_qmmm_validation_artifacts": artifacts,
        "pbc_qmmm_validation_json": artifacts.get("json"),
        "pbc_qmmm_validation_markdown": artifacts.get("markdown"),
        "pbc_qmmm_validation_csv": artifacts.get("csv"),
        "pbc_qmmm_gamma_cases": sum(
            1 for item in metrics if item.get("kpoint_grid") == [1, 1, 1]
        ),
        "pbc_qmmm_ewald_cases": sum(
            1 for item in metrics if item.get("embedding_mode") == "ewald"
        ),
        "pbc_qmmm_rejected_cases": sum(
            1 for item in metrics if item.get("status") == "rejected"
        ),
    }


def _pbc_qmmm_validation_case(case, case_root: Path) -> BenchmarkCaseResult:
    profile = (case.profile or "smoke").strip().lower()
    summary = run_pbc_qmmm_validation(case_root, profile=profile)
    status = "validated" if summary.get("overall_status") == "passed" else "failed"
    metrics = _pbc_qmmm_validation_case_metrics(summary, profile=profile)
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
            "schema_version": "qcchem.pbc_qmmm_validation_benchmark_case.v1",
            "run_id": case.name,
            "kind": case.kind,
            "verification_status": status,
            "expected_status": case.expected_status,
            "profile": profile,
            "artifact_root": str(case_root),
            "metrics": metrics,
            "pbc_qmmm_validation": summary,
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


def _normalize_tag_filter(values: str | list[str] | tuple[str, ...] | set[str] | None) -> set[str]:
    if isinstance(values, str):
        values = [values]
    return {str(value).strip() for value in (values or []) if str(value).strip()}


def _select_benchmark_cases(
    cases: list[Any],
    *,
    include_tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
    exclude_tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> tuple[list[Any], dict[str, Any]]:
    include = _normalize_tag_filter(include_tags)
    exclude = _normalize_tag_filter(exclude_tags)
    selected = []
    skipped = []
    for case in cases:
        case_tags = set(getattr(case, "tags", []) or [])
        include_miss = bool(include) and not bool(case_tags & include)
        exclude_hit = bool(exclude) and bool(case_tags & exclude)
        if include_miss or exclude_hit:
            skipped.append(
                {
                    "name": case.name,
                    "tags": sorted(case_tags),
                    "reason": "include_tags_not_matched" if include_miss else "exclude_tags_matched",
                }
            )
            continue
        selected.append(case)
    if not selected:
        raise ValueError(
            "Benchmark tag filters selected no cases "
            f"(include_tags={sorted(include)}, exclude_tags={sorted(exclude)})."
        )
    return selected, {
        "include_tags": sorted(include),
        "exclude_tags": sorted(exclude),
        "selected_cases": [case.name for case in selected],
        "skipped_cases": skipped,
    }


def run_benchmark_suite_from_spec(
    spec,
    *,
    source_config: str,
    output_dir: Path | None = None,
    confirm_runtime_budget: str | None = None,
    include_tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
    exclude_tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
    overwrite: bool = False,
) -> BenchmarkSuiteResult:
    """Run a benchmark suite from an already-parsed spec."""
    suite_root = output_dir or Path("artifacts") / spec.name
    artifacts = _prepare_benchmark_artifacts(Path(suite_root), overwrite=overwrite)
    cases_root = artifacts.root / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)
    selected_cases, case_filter_summary = _select_benchmark_cases(
        list(spec.cases),
        include_tags=include_tags,
        exclude_tags=exclude_tags,
    )

    case_results: list[BenchmarkCaseResult] = []
    registry_entries = []
    for case in selected_cases:
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
        elif case.kind == "pbc_qmmm_validation":
            outcome = _pbc_qmmm_validation_case(case, case_root)
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
    method_evidence_campaign_summary = _build_method_evidence_campaign_summary(case_results)

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
        "case_filter": case_filter_summary,
        "cases_with_measured_cost": len(measured_costs),
        "cases_with_estimated_cost": len(estimated_costs),
        "mean_estimated_cost": (sum(estimated_costs) / len(estimated_costs) if estimated_costs else None),
        "mean_measured_cost": (sum(measured_costs) / len(measured_costs) if measured_costs else None),
        "mean_achieved_error": (sum(achieved_errors) / len(achieved_errors) if achieved_errors else None),
        "field_model_campaign": field_model_campaign_summary,
        "method_evidence_campaign": method_evidence_campaign_summary,
    }
    dashboard_summary = {
        "case_filter": case_filter_summary,
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
        "method_evidence_campaign": method_evidence_campaign_summary,
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
    write_result_json(result.acceptance_summary, artifacts.root / "acceptance_summary.json")
    write_result_json(calibration_summary, artifacts.root / "calibration_summary.json")
    write_result_json(method_evidence_campaign_summary, artifacts.root / "method_evidence_summary.json")
    result.artifact_index_entry = build_artifact_index_entry(
        artifacts.result_json,
        payload=to_primitive(result),
    )
    write_result_json(result, artifacts.result_json)
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
                f"- method_evidence_campaign: `{method_evidence_campaign_summary}`",
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
    overwrite: bool = False,
) -> dict[str, Any]:
    """Build a compact hardware-calibration dashboard from run result artifacts."""
    resolved_output_root = prepare_clean_output_root(
        output_root,
        workflow_name="Hardware calibration suite",
        overwrite=overwrite,
    )

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
    overwrite: bool = False,
) -> dict[str, Any]:
    return build_hardware_calibration_suite(
        [case.result_json for case in spec.cases],
        output_root=(output_dir or spec.output_root),
        overwrite=overwrite,
    )


def run_benchmark_suite_from_config(
    path: Path,
    output_dir: Path | None = None,
    *,
    confirm_runtime_budget: str | None = None,
    include_tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
    exclude_tags: str | list[str] | tuple[str, ...] | set[str] | None = None,
    overwrite: bool = False,
) -> BenchmarkSuiteResult | dict[str, Any]:
    """Load and run a benchmark suite from YAML."""
    spec = load_benchmark_entry_spec(path)
    if isinstance(spec, HardwareCalibrationSuiteSpec):
        return _run_hardware_calibration_suite_from_spec(spec, output_dir=output_dir, overwrite=overwrite)
    return run_benchmark_suite_from_spec(
        spec,
        source_config=str(path),
        output_dir=output_dir,
        confirm_runtime_budget=confirm_runtime_budget,
        include_tags=include_tags,
        exclude_tags=exclude_tags,
        overwrite=overwrite,
    )
