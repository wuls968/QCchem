"""Integrated method-evidence sidecar construction."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from qcchem.core import (
    EADAPTResultSummary,
    FTQPEResourceEstimateSummary,
    KQPBCResultSummary,
    MethodEvidenceSummary,
    OrbitalOptimizationSummary,
    PostCorrelationSummary,
    QSCIPlusResultSummary,
)
from qcchem.io.serialization import to_primitive

SCHEMA = "qcchem.method_evidence.v1"


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _e_adapt_summary(solver_outcome: Any) -> EADAPTResultSummary | None:
    payload = (getattr(solver_outcome, "metadata", {}) or {}).get("e_adapt_result")
    if not isinstance(payload, dict):
        return None
    return EADAPTResultSummary(
        available=True,
        selected_operators=list(payload.get("selected_operators", [])),
        rejected_operators=list(payload.get("rejected_operators", [])),
        gradient_history=list(payload.get("gradient_history", [])),
        depth_growth=list(payload.get("depth_growth", [])),
        adaptive_optimization=dict(payload.get("adaptive_optimization", {})),
        symmetry_audit=dict(payload.get("symmetry_audit", {})),
        low_rank_priority_scores={
            str(key): float(value)
            for key, value in dict(payload.get("low_rank_priority_scores", {})).items()
        },
        ansatz_trust_gate=str(payload.get("ansatz_trust_gate", "exploratory")),
        notes=[
            "E-ADAPT evidence is exploratory and does not promote the run by itself.",
        ],
    )


def _orbital_summary(solver_outcome: Any) -> OrbitalOptimizationSummary | None:
    payload = (getattr(solver_outcome, "metadata", {}) or {}).get("orbital_optimization")
    if not isinstance(payload, dict):
        return None
    return OrbitalOptimizationSummary(
        available=True,
        macro_iterations=list(payload.get("macro_iterations", [])),
        orbital_rotation_norm=float(payload.get("orbital_rotation_norm", 0.0)),
        rdm_source=str(payload.get("rdm_source", "unavailable")),
        energy_lowering_hartree=float(payload.get("energy_lowering_hartree", 0.0)),
        active_space_changed=bool(payload.get("active_space_changed", False)),
        reference_diagnostics=dict(payload.get("reference_diagnostics", {})),
        active_space_resolve=dict(payload.get("active_space_resolve", {})),
        orbital_transfer_audit=dict(payload.get("orbital_transfer_audit", {})),
        energy_scope_audit=dict(payload.get("energy_scope_audit", {})),
        promotion_readiness_audit=dict(payload.get("promotion_readiness_audit", {})),
        energy_replaces_primary=bool(payload.get("energy_replaces_primary", False)),
        trust_gate=str(payload.get("trust_gate", "exploratory")),
        notes=[
            "OO-QCASSCF evidence is a v1 PySCF CASSCF reference diagnostic and remains exploratory.",
            "The delegated QCchem solver energy remains primary unless an OO-QCASSCF solver is explicitly validated for replacement.",
        ],
    )


def _qsci_summary(payload: dict[str, Any] | None) -> QSCIPlusResultSummary | None:
    if not isinstance(payload, dict):
        return None
    return QSCIPlusResultSummary(
        available=True,
        sampler=str(payload.get("sampler", "unknown")),
        raw_bitstrings=dict(payload.get("raw_bitstrings", {})),
        repaired_determinants=list(payload.get("repaired_determinants", [])),
        selected_subspace_size=int(payload.get("selected_subspace_size", 0)),
        ci_energy=(
            float(payload["ci_energy"])
            if payload.get("ci_energy") is not None
            else None
        ),
        variance_estimate=(
            float(payload["variance_estimate"])
            if payload.get("variance_estimate") is not None
            else None
        ),
        excited_state_energies=[float(value) for value in payload.get("excited_state_energies", [])],
        selection_bias_audit=dict(payload.get("selection_bias_audit", {})),
        subspace_audit=dict(payload.get("subspace_audit", {})),
        variational_upper_bound=bool(payload.get("variational_upper_bound", True)),
        notes=list(payload.get("notes", [])),
    )


def _ci_coefficient_rows(leading_coefficients: Any) -> list[dict[str, Any]]:
    if not isinstance(leading_coefficients, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in leading_coefficients:
        if not isinstance(item, dict) or item.get("determinant") is None:
            continue
        real = float(item.get("coefficient_real", 0.0) or 0.0)
        imag = float(item.get("coefficient_imag", 0.0) or 0.0)
        determinant = int(item["determinant"])
        coefficient = complex(real, imag)
        rows.append(
            {
                "determinant": determinant,
                "coefficient_real": real,
                "coefficient_imag": imag,
                "coefficient_abs": float(abs(coefficient)),
                "_coefficient": coefficient,
            }
        )
    return rows


def _tcc_amplitude_mapping_audit(leading_coefficients: Any) -> dict[str, Any]:
    rows = _ci_coefficient_rows(leading_coefficients)
    if not rows:
        return {
            "schema": "qcchem.qsci_tcc_amplitude_mapping_audit.v1",
            "status": "missing_ci_coefficients",
            "coefficient_count": 0,
            "mapped_single_count": 0,
            "mapped_double_count": 0,
            "unsupported_excitation_count": 0,
            "energy_correction_backend_executable": False,
            "energy_replaces_primary": False,
        }
    reference = max(rows, key=lambda item: float(item["coefficient_abs"]))
    reference_coefficient = complex(reference["_coefficient"])
    reference_abs = float(abs(reference_coefficient))
    coefficient_norm = float(math.sqrt(sum(float(item["coefficient_abs"]) ** 2 for item in rows)))
    if reference_abs <= 1.0e-12:
        return {
            "schema": "qcchem.qsci_tcc_amplitude_mapping_audit.v1",
            "status": "reference_coefficient_too_small",
            "coefficient_count": len(rows),
            "coefficient_norm": coefficient_norm,
            "reference_determinant": int(reference["determinant"]),
            "reference_coefficient_abs": reference_abs,
            "mapped_single_count": 0,
            "mapped_double_count": 0,
            "unsupported_excitation_count": max(len(rows) - 1, 0),
            "energy_correction_backend_executable": False,
            "energy_replaces_primary": False,
        }

    singles: list[dict[str, Any]] = []
    doubles: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    negligible: list[dict[str, Any]] = []
    reference_determinant = int(reference["determinant"])
    for row in rows:
        determinant = int(row["determinant"])
        if determinant == reference_determinant:
            continue
        coefficient = complex(row["_coefficient"])
        amplitude = coefficient / reference_coefficient
        hamming_distance = int((determinant ^ reference_determinant).bit_count())
        excitation_rank = hamming_distance // 2 if hamming_distance % 2 == 0 else None
        entry = {
            "determinant": determinant,
            "reference_determinant": reference_determinant,
            "hamming_distance": hamming_distance,
            "excitation_rank": excitation_rank,
            "coefficient_abs": float(row["coefficient_abs"]),
            "amplitude_real": float(amplitude.real),
            "amplitude_imag": float(amplitude.imag),
            "amplitude_abs": float(abs(amplitude)),
        }
        if float(row["coefficient_abs"]) <= 1.0e-12:
            negligible.append(entry)
            continue
        if hamming_distance == 2:
            singles.append(entry)
        elif hamming_distance == 4:
            doubles.append(entry)
        else:
            unsupported.append(entry)

    mapped = singles + doubles
    return {
        "schema": "qcchem.qsci_tcc_amplitude_mapping_audit.v1",
        "status": (
            "constructed_for_audit_only"
            if mapped
            else "no_single_double_excitation_amplitudes"
        ),
        "reference_policy": "largest_abs_selected_ci_coefficient",
        "reference_determinant": reference_determinant,
        "reference_coefficient_abs": reference_abs,
        "coefficient_count": len(rows),
        "coefficient_norm": coefficient_norm,
        "mapped_single_count": len(singles),
        "mapped_double_count": len(doubles),
        "unsupported_excitation_count": len(unsupported),
        "negligible_coefficient_count": len(negligible),
        "max_mapped_amplitude_abs": (
            max(float(item["amplitude_abs"]) for item in mapped) if mapped else None
        ),
        "singles": singles,
        "doubles": doubles,
        "unsupported_excitations": unsupported,
        "negligible_coefficients": negligible,
        "energy_correction_backend_executable": False,
        "energy_replaces_primary": False,
        "notes": [
            "Selected-CI coefficients are mapped to relative single/double amplitudes for audit only.",
            "No QSCI-derived TCC energy is emitted without an executable external-correlation backend.",
        ],
    }


def _post_correlation_summary(spec: Any, qsci: QSCIPlusResultSummary | None) -> PostCorrelationSummary | None:
    task = spec.tasks.perturbative_correction
    method = str(task.method).strip().lower()
    if method not in {"qsci_tcc", "qsci_nevpt2"}:
        return None
    if qsci is None or qsci.ci_energy is None:
        return PostCorrelationSummary(
            available=True,
            method=method,
            source_wavefunction="qsci_plus",
            trust_gate="unsupported_for_claim",
            notes=["QSCI post-correlation requested but no QSCI++ wavefunction evidence is available."],
        )
    leading_coefficients = qsci.selection_bias_audit.get("leading_coefficients", [])
    coefficient_count = len(leading_coefficients) if isinstance(leading_coefficients, list) else 0
    amplitude_mapping = (
        _tcc_amplitude_mapping_audit(leading_coefficients)
        if method == "qsci_tcc"
        else {
            "schema": "qcchem.qsci_tcc_amplitude_mapping_audit.v1",
            "status": "not_applicable_to_nevpt2",
            "coefficient_count": coefficient_count,
            "mapped_single_count": 0,
            "mapped_double_count": 0,
            "unsupported_excitation_count": 0,
            "energy_correction_backend_executable": False,
            "energy_replaces_primary": False,
        }
    )
    method_missing_inputs = {
        "qsci_tcc": [
            "external orbital-space partition",
            "executable QSCI-to-TCC amplitude backend",
            "cluster-amplitude contraction equations",
            "double-counting correction model",
        ],
        "qsci_nevpt2": [
            "active-space one- and two-particle density matrices",
            "contracted perturber-space intermediates",
            "executable QSCI-to-NEVPT2 backend",
            "double-counting correction model",
        ],
    }
    required_inputs_missing = method_missing_inputs[method]
    eligibility_status = (
        "tcc_amplitude_mapping_audit_only"
        if method == "qsci_tcc"
        and amplitude_mapping.get("status") == "constructed_for_audit_only"
        else "coefficient_provenance_only"
    )
    correction_eligibility_audit = {
        "schema": "qcchem.qsci_post_correlation_eligibility.v1",
        "status": eligibility_status,
        "method": method,
        "source_wavefunction": "qsci_plus",
        "selected_subspace_size": qsci.selected_subspace_size,
        "eligible_coefficient_count": coefficient_count,
        "ci_coefficients_digest": str(qsci.selection_bias_audit.get("ci_coefficients_digest")),
        "ci_energy_hartree": qsci.ci_energy,
        "variance_estimate": qsci.variance_estimate,
        "amplitude_mapping_status": amplitude_mapping.get("status"),
        "backend_executable": False,
        "correction_energy_emitted": False,
        "total_corrected_energy_emitted": False,
        "energy_replaces_primary": False,
        "required_inputs_missing": required_inputs_missing,
        "required_input_missing_count": len(required_inputs_missing),
        "promotion_blockers": [
            "external_correlation_energy_not_emitted",
            "double_counting_not_evaluated",
            "qcchem_qsci_correction_backend_missing",
            *required_inputs_missing,
        ],
    }
    return PostCorrelationSummary(
        available=True,
        method=method,
        source_wavefunction="qsci_plus",
        active_ci_coefficients_digest=str(qsci.selection_bias_audit.get("ci_coefficients_digest")),
        correction_eligibility_audit=correction_eligibility_audit,
        amplitude_mapping_audit=amplitude_mapping,
        tailored_amplitudes={
            "status": amplitude_mapping.get("status")
            if method == "qsci_tcc"
            else "not_constructed",
            "source": "selected_ci_coefficients_digest",
            "eligible_coefficient_count": coefficient_count,
            "selected_subspace_size": qsci.selected_subspace_size,
            "mapped_single_count": amplitude_mapping.get("mapped_single_count"),
            "mapped_double_count": amplitude_mapping.get("mapped_double_count"),
            "required_inputs_missing": required_inputs_missing,
        },
        external_correlation_energy=None,
        total_corrected_energy=None,
        double_counting_audit={
            "status": "not_evaluated",
            "active_space_energy_available": True,
            "active_space_ci_energy_hartree": qsci.ci_energy,
            "dynamic_correlation_energy_emitted": False,
            "energy_replaces_primary": False,
            "backend_executable": False,
            "required_input_missing_count": len(required_inputs_missing),
            "reason": "No executable QSCI-derived TCC/NEVPT2 correction model is available in v1.",
        },
        classical_solver=None,
        trust_gate="unsupported_for_claim",
        notes=[
            "QSCI post-correlation v1 records coefficient provenance and correction eligibility only.",
            "No external-correlation or corrected-total energy is emitted without an executable QSCI-derived TCC/NEVPT2 backend.",
            "Use the validated classical NEVPT2 perturbative-correction task for PySCF-backed NEVPT2 corrections.",
        ],
    )


def _kq_pbc_summary(spec: Any, *, solver_energy: float | None) -> KQPBCResultSummary | None:
    pbc = spec.problem.pbc
    if str(pbc.mode).strip().lower() != "kq_pbc":
        return None
    kpoints = list(pbc.kpoints or ["gamma"])
    requested_mesh = [int(value) for value in getattr(pbc, "kpoint_mesh", [])]
    requested_kpoint_count = 1
    for value in requested_mesh:
        requested_kpoint_count *= max(int(value), 1)
    execution_mesh = [1, 1, 1]
    execution_kpoint_count = 1
    executed_named_kpoints = ["gamma"]
    executed_requested_named_kpoints = [
        kpoint for kpoint in executed_named_kpoints if kpoint in kpoints
    ]
    twist_energies = [
        {
            "kpoint": kpoint,
            "requested_twist_index": index,
            "solver_energy_hartree": None,
            "energy_status": "not_evaluated",
            "execution_reference": "gamma_reference_hamiltonian",
            "mapping_status": "audit_only",
            "reason": "kQ-PBC v1 records requested non-Gamma/twist metadata but does not execute non-Gamma quantum mappings.",
        }
        for index, kpoint in enumerate(kpoints)
    ]
    available_twist_energy_count = sum(
        1 for item in twist_energies if item["solver_energy_hartree"] is not None
    )
    required_twist_energy_count = len(twist_energies)
    missing_twist_energy_count = required_twist_energy_count - available_twist_energy_count
    named_kpoint_coverage_fraction = (
        float(len(executed_requested_named_kpoints) / len(kpoints))
        if kpoints
        else None
    )
    mesh_kpoint_coverage_fraction = (
        float(execution_kpoint_count / requested_kpoint_count)
        if requested_kpoint_count
        else None
    )
    twist_energy_coverage_fraction = (
        float(available_twist_energy_count / required_twist_energy_count)
        if required_twist_energy_count
        else None
    )
    missing_twist_energy_fraction = (
        float(missing_twist_energy_count / required_twist_energy_count)
        if required_twist_energy_count
        else None
    )
    promotion_blockers = [
        "non_gamma_quantum_mapping_not_executed",
        "twist_energies_not_evaluated",
        "finite_size_correction_not_evaluated",
        "forces_stress_cell_optimization_out_of_scope",
    ]
    unsupported_claims = [
        "non_gamma_materials_accuracy",
        "twist_averaged_energy",
        "finite_size_corrected_energy",
        "forces_or_stress",
    ]
    coverage_audit = {
        "status": "gamma_reference_only_coverage_gap",
        "requested_named_kpoint_count": len(kpoints),
        "executed_named_kpoint_count": len(executed_named_kpoints),
        "executed_requested_named_kpoint_count": len(executed_requested_named_kpoints),
        "named_kpoint_execution_coverage_fraction": named_kpoint_coverage_fraction,
        "requested_mesh_kpoint_count": requested_kpoint_count,
        "execution_mesh_kpoint_count": execution_kpoint_count,
        "mesh_kpoint_execution_coverage_fraction": mesh_kpoint_coverage_fraction,
        "required_twist_energy_count": required_twist_energy_count,
        "available_twist_energy_count": available_twist_energy_count,
        "missing_twist_energy_count": missing_twist_energy_count,
        "twist_energy_coverage_fraction": twist_energy_coverage_fraction,
        "missing_twist_energy_fraction": missing_twist_energy_fraction,
        "proxy_energy_present": False,
    }
    promotion_readiness_audit = {
        "status": "blocked_exploratory_audit_only",
        "readiness_level": "not_ready_for_validated_non_gamma_claim",
        "coverage_audit": coverage_audit,
        "promotion_blocker_count": len(promotion_blockers),
        "unsupported_claim_count": len(unsupported_claims),
        "promotion_blockers": promotion_blockers,
        "unsupported_claims": unsupported_claims,
        "energy_replaces_primary": False,
        "runtime_submission_allowed": False,
        "required_promotion_evidence": [
            "executable_non_gamma_quantum_mapping",
            "evaluated_twist_energies",
            "finite_size_correction_model",
            "forces_stress_cell_optimization_support",
        ],
    }
    return KQPBCResultSummary(
        available=True,
        kpoints=kpoints,
        twist_energies=twist_energies,
        finite_size_correction={
            "status": "not_evaluated",
            "twist_average_requested": bool(pbc.twist_average),
            "energy_correction_hartree": None,
            "required_twist_energy_count": required_twist_energy_count,
            "available_twist_energy_count": available_twist_energy_count,
            "missing_twist_energy_count": missing_twist_energy_count,
            "twist_energy_coverage_fraction": twist_energy_coverage_fraction,
            "missing_twist_energy_fraction": missing_twist_energy_fraction,
            "reason": "No non-Gamma/twist energies are available for finite-size correction in kQ-PBC v1.",
        },
        band_window_metadata=dict(pbc.active_space_per_k),
        non_gamma_mapping_audit={
            "status": "audit_only",
            "requested_kpoint_mesh": requested_mesh,
            "execution_kpoint_mesh": execution_mesh,
            "requested_kpoint_count": requested_kpoint_count,
            "execution_kpoint_count": execution_kpoint_count,
            "mesh_mismatch": requested_mesh != execution_mesh,
            "requested_named_kpoints": kpoints,
            "executed_named_kpoints": executed_named_kpoints,
            "executed_requested_named_kpoints": executed_requested_named_kpoints,
            "named_kpoint_execution_coverage_fraction": named_kpoint_coverage_fraction,
            "mesh_kpoint_execution_coverage_fraction": mesh_kpoint_coverage_fraction,
            "gamma_reference_energy_hartree": solver_energy,
            "non_gamma_energy_available": False,
            "energy_replaces_primary": False,
            "runtime_submission_allowed": False,
            "forces_stress_cell_optimization": "out_of_scope",
            "executable_scope": "gamma_reference_hamiltonian_only",
            "promotion_blockers": promotion_blockers,
            "promotion_blocker_count": len(promotion_blockers),
            "unsupported_claims": unsupported_claims,
            "unsupported_claim_count": len(unsupported_claims),
            "coverage_audit": coverage_audit,
        },
        promotion_readiness_audit=promotion_readiness_audit,
        pbc_trust_tier="exploratory",
        notes=[
            "kQ-PBC v1 is an exploratory audit and does not validate non-Gamma materials accuracy.",
            "Requested k/twist entries do not contain proxy energies; only the Gamma reference Hamiltonian is executed.",
        ],
    )


def _ft_qpe_summary(spec: Any, physical_mapping: Any) -> FTQPEResourceEstimateSummary | None:
    ft = spec.fault_tolerant
    if not ft.enabled:
        return None
    operator = physical_mapping.qubit_hamiltonian
    coeff_l1 = float(sum(abs(complex(coeff)) for coeff in operator.coeffs))
    num_qubits = int(operator.num_qubits)
    precision = max(float(ft.precision_hartree), 1.0e-12)
    lambda_norms: dict[str, float] = {}
    toffoli_counts: dict[str, float] = {}
    logical_qubits: dict[str, int] = {}
    physical_qubits: dict[str, int] = {}
    runtime_estimates: dict[str, float] = {}
    phase_estimation_steps: dict[str, int] = {}
    surface_code_overhead_factor = max(int(round(1.0 / max(float(ft.physical_error_rate), 1.0e-12))), 1)
    encoding_scale = {
        "double_factorization": 1.0,
        "symmetry_compressed_double_factorization": 0.75,
        "tensor_hypercontraction": 0.65,
        "first_quantization_active_basis": 0.85,
    }
    encoding_formula_components: dict[str, dict[str, Any]] = {}
    for encoding in ft.encodings:
        scale = float(encoding_scale.get(encoding, 1.0))
        lam = coeff_l1 * scale
        lambda_norms[encoding] = lam
        phase_estimation_steps[encoding] = int(math.ceil(lam / precision))
        toffoli = lam / precision * max(num_qubits, 1)
        toffoli_counts[encoding] = float(toffoli)
        logical_qubits[encoding] = int(num_qubits + 4 + len(operator))
        physical_qubits[encoding] = int(logical_qubits[encoding] * surface_code_overhead_factor)
        runtime_estimates[encoding] = float(toffoli * float(ft.cycle_time_ns) * 1.0e-9)
        encoding_formula_components[encoding] = {
            "encoding_scale_assumption": scale,
            "lambda_norm": lambda_norms[encoding],
            "phase_estimation_steps": phase_estimation_steps[encoding],
            "toffoli_count": toffoli_counts[encoding],
            "logical_qubits": logical_qubits[encoding],
            "physical_qubits": physical_qubits[encoding],
            "runtime_seconds": runtime_estimates[encoding],
        }
    recommended = min(toffoli_counts, key=toffoli_counts.get) if toffoli_counts else None
    reference = "double_factorization" if "double_factorization" in toffoli_counts else None
    best_to_reference_ratio = (
        float(toffoli_counts[recommended]) / float(toffoli_counts[reference])
        if recommended is not None and reference is not None and float(toffoli_counts[reference]) > 0.0
        else None
    )
    lambda_reduction = (
        (float(lambda_norms[reference]) - float(lambda_norms[recommended])) / float(lambda_norms[reference])
        if recommended is not None and reference is not None and float(lambda_norms[reference]) > 0.0
        else None
    )
    toffoli_reduction = (
        1.0 - best_to_reference_ratio if best_to_reference_ratio is not None else None
    )
    promotion_blockers = [
        "encoding_scale_assumptions_not_derived_from_integral_factorization",
        "no_compiled_fault_tolerant_circuit",
        "surface_code_distance_not_estimated",
        "logical_error_budget_not_allocated",
        "hardware_architecture_cycle_model_not_calibrated",
    ]
    required_promotion_evidence = [
        "executable_integral_factorization_for_each_encoding",
        "compiled_fault_tolerant_phase_estimation_circuit",
        "surface_code_distance_and_physical_qubit_layout",
        "logical_error_budget_allocation",
        "hardware_architecture_specific_cycle_model",
    ]
    resource_formula_audit = {
        "schema": "qcchem.ft_qpe_resource_formula_audit.v1",
        "scope": "coarse_pauli_l1_phase_estimation_scaling",
        "input_terms": {
            "coefficient_l1_norm": coeff_l1,
            "num_qubits": num_qubits,
            "pauli_term_count": len(operator),
            "precision_hartree": precision,
            "cycle_time_ns": float(ft.cycle_time_ns),
            "physical_error_rate": float(ft.physical_error_rate),
            "surface_code_overhead_factor": surface_code_overhead_factor,
        },
        "formulae": {
            "lambda_norm": "coefficient_l1_norm * encoding_scale_assumption",
            "phase_estimation_steps": "ceil(lambda_norm / precision_hartree)",
            "toffoli_count": "lambda_norm / precision_hartree * max(num_qubits, 1)",
            "logical_qubits": "num_qubits + 4 + pauli_term_count",
            "physical_qubits": "logical_qubits * surface_code_overhead_factor",
            "runtime_seconds": "toffoli_count * cycle_time_ns * 1e-9",
            "surface_code_overhead_factor": "round(1 / physical_error_rate)",
        },
        "encoding_scale_assumptions": dict(encoding_scale),
        "encoding_formula_components": encoding_formula_components,
        "reference_encoding": reference,
        "best_encoding": recommended,
        "encoding_comparison_count": len(list(ft.encodings)),
    }
    promotion_readiness_audit = {
        "schema": "qcchem.ft_qpe_promotion_readiness.v1",
        "status": "blocked_missing_compiled_fault_tolerant_evidence",
        "readiness_level": "resource_model_only_not_compiled",
        "resource_model_claim_allowed": True,
        "validated_resource_advantage_claim_allowed": False,
        "compiled_fault_tolerant_circuit_available": False,
        "surface_code_distance_available": False,
        "logical_error_budget_available": False,
        "executable_factorization_available": False,
        "reference_encoding": reference,
        "best_encoding": recommended,
        "encoding_comparison_count": len(list(ft.encodings)),
        "best_to_reference_toffoli_ratio": best_to_reference_ratio,
        "toffoli_reduction_vs_reference": toffoli_reduction,
        "lambda_reduction_vs_reference": lambda_reduction,
        "promotion_blockers": promotion_blockers,
        "promotion_blocker_count": len(promotion_blockers),
        "required_promotion_evidence": required_promotion_evidence,
        "required_promotion_evidence_count": len(required_promotion_evidence),
    }
    resource_model_audit = {
        "model_scope": "coarse_pauli_l1_phase_estimation_scaling",
        "resource_claim_status": "resource_model_only",
        "promotion_readiness_status": promotion_readiness_audit["status"],
        "readiness_level": promotion_readiness_audit["readiness_level"],
        "compiled_fault_tolerant_circuit_available": False,
        "surface_code_distance_available": False,
        "logical_error_budget_available": False,
        "validated_resource_advantage_claim_allowed": False,
        "reference_encoding": reference,
        "recommended_encoding": recommended,
        "best_encoding": recommended,
        "encoding_comparison_count": len(list(ft.encodings)),
        "best_to_reference_toffoli_ratio": best_to_reference_ratio,
        "toffoli_reduction_vs_reference": toffoli_reduction,
        "lambda_reduction_vs_reference": lambda_reduction,
        "phase_estimation_steps": phase_estimation_steps,
        "encoding_scale_assumptions": encoding_scale,
        "surface_code_overhead_model": "logical_qubits * round(1 / physical_error_rate)",
        "surface_code_overhead_factor": surface_code_overhead_factor,
        "cycle_time_ns": float(ft.cycle_time_ns),
        "physical_error_rate": float(ft.physical_error_rate),
        "required_promotion_evidence": required_promotion_evidence,
        "required_promotion_evidence_count": len(required_promotion_evidence),
        "promotion_blockers": promotion_blockers,
        "promotion_blocker_count": len(promotion_blockers),
    }
    return FTQPEResourceEstimateSummary(
        available=True,
        encodings_compared=list(ft.encodings),
        lambda_norms=lambda_norms,
        toffoli_counts=toffoli_counts,
        logical_qubits=logical_qubits,
        physical_qubits=physical_qubits,
        runtime_estimates=runtime_estimates,
        dominant_cost_terms={
            "pauli_term_count": len(operator),
            "qubit_count": num_qubits,
            "precision_hartree": precision,
            "coefficient_l1_norm": coeff_l1,
            "phase_estimation_steps": phase_estimation_steps,
            "surface_code_overhead_factor": surface_code_overhead_factor,
        },
        recommended_encoding=recommended,
        resource_formula_audit=resource_formula_audit,
        resource_model_audit=resource_model_audit,
        promotion_readiness_audit=promotion_readiness_audit,
        notes=[
            "FT-QPE planner is a coarse resource estimator, not a compiled fault-tolerant circuit.",
            "Encoding reductions are model assumptions until backed by executable factorization and logical-resource gates.",
        ],
    )


def _trust_qem_payload(mitigation: Any) -> dict[str, Any] | None:
    mitigation_payload = to_primitive(mitigation)
    if not isinstance(mitigation_payload, dict):
        return None

    component_payloads = {
        "symmetry_check": (
            mitigation_payload.get("symmetry_check")
            if isinstance(mitigation_payload.get("symmetry_check"), dict)
            else {}
        ),
        "readout_mitigation": (
            mitigation_payload.get("readout_mitigation")
            if isinstance(mitigation_payload.get("readout_mitigation"), dict)
            else {}
        ),
        "zne": mitigation_payload.get("zne") if isinstance(mitigation_payload.get("zne"), dict) else {},
        "pec": mitigation_payload.get("pec") if isinstance(mitigation_payload.get("pec"), dict) else {},
    }
    requested_methods = list(mitigation_payload.get("requested_methods") or [])
    if not requested_methods:
        requested_methods = [
            label
            for label, payload in component_payloads.items()
            if isinstance(payload, dict)
            and payload.get("effective_requested", payload.get("requested"))
        ]
    claim_allowed_methods = list(mitigation_payload.get("claim_allowed_methods") or [])
    if not claim_allowed_methods:
        claim_allowed_methods = [
            label
            for label, payload in component_payloads.items()
            if isinstance(payload, dict) and payload.get("allowed_for_claim")
        ]
    applied_methods = list(mitigation_payload.get("applied_methods") or [])

    if requested_methods or applied_methods:
        claim_status = str(mitigation_payload.get("claim_status") or "")
        if not claim_status:
            claim_status = "claim_limited" if claim_allowed_methods else "unsupported_for_claim"
        return {
            **mitigation_payload,
            "requested_methods": requested_methods,
            "applied_methods": applied_methods,
            "claim_allowed_methods": claim_allowed_methods,
            "claim_disallowed_methods": [
                label for label in requested_methods if label not in set(claim_allowed_methods)
            ],
            "claim_status": claim_status,
            "trust_gate": str(mitigation_payload.get("trust_gate") or claim_status),
            "energy_replaces_primary": False,
            "mitigated_energy_replaces_primary": False,
            "primary_energy_policy": "raw_solver_energy_remains_primary",
            "notes": [
                "Trust-QEM v1 records requested/performed mitigation evidence beside the raw solver energy.",
                "Readout, ZNE, and symmetry entries are not treated as claim-eligible energy corrections without executable calibrated application.",
                "PEC claim use requires an executable qcchem.pec_calibration_model.v1 JSON calibration model.",
            ],
        }

    symmetry = mitigation_payload.get("symmetry_check") if isinstance(mitigation_payload.get("symmetry_check"), dict) else {}
    requested_checks = (
        symmetry.get("requested_checks")
        if isinstance(symmetry.get("requested_checks"), dict)
        else {}
    )
    symmetry_requested = bool(symmetry.get("requested") and any(requested_checks.values()))

    readout = (
        mitigation_payload.get("readout_mitigation")
        if isinstance(mitigation_payload.get("readout_mitigation"), dict)
        else {}
    )
    readout_method = str(readout.get("method", "none")).strip().lower()
    readout_requested = bool(
        readout.get("requested")
        and readout_method not in {"none", "placeholder"}
        and int(readout.get("calibration_shots") or 0) > 0
    )

    zne = mitigation_payload.get("zne") if isinstance(mitigation_payload.get("zne"), dict) else {}
    zne_method = str(zne.get("method", "none")).strip().lower()
    zne_requested = bool(zne.get("requested") and zne_method not in {"none", "placeholder"})

    pec = mitigation_payload.get("pec") if isinstance(mitigation_payload.get("pec"), dict) else {}
    pec_requested = bool(pec.get("requested") and pec.get("calibration_model"))
    if symmetry_requested or readout_requested or zne_requested or pec_requested:
        return mitigation_payload
    return None


def _q_sc_eom_property_audit(property_result: Any) -> dict[str, Any]:
    properties = getattr(property_result, "properties", []) if property_result is not None else []
    transition_properties = []
    for item in properties or []:
        name = str(getattr(item, "property_name", ""))
        if name not in {"transition_dipole", "oscillator_strength"}:
            continue
        transition_properties.append(to_primitive(item))

    validated = [
        item
        for item in transition_properties
        if item.get("implementation_status") == "validated"
    ]
    transition_dipoles = [
        float(item["value"])
        for item in validated
        if item.get("property_name") == "transition_dipole"
        and isinstance(item.get("value"), int | float)
    ]
    oscillator_strengths = [
        float(item["value"])
        for item in validated
        if item.get("property_name") == "oscillator_strength"
        and isinstance(item.get("value"), int | float)
    ]
    requested_names = sorted({str(item.get("property_name")) for item in transition_properties})
    status = (
        "validated_transition_properties_linked"
        if transition_properties and len(validated) == len(transition_properties)
        else "transition_properties_missing"
        if not transition_properties
        else "partial_transition_property_linkage"
    )
    return {
        "status": status,
        "property_bundle_status": getattr(property_result, "verification_status", None)
        if property_result is not None
        else None,
        "requested_transition_property_count": len(transition_properties),
        "validated_transition_property_count": len(validated),
        "property_names": requested_names,
        "state_pairs": [
            list(item.get("state_indices") or [])
            for item in transition_properties
            if item.get("state_indices") is not None
        ],
        "transition_dipole_magnitudes": transition_dipoles,
        "max_transition_dipole_magnitude": max(transition_dipoles)
        if transition_dipoles
        else None,
        "oscillator_strengths": oscillator_strengths,
        "max_oscillator_strength": max(oscillator_strengths)
        if oscillator_strengths
        else None,
        "properties": transition_properties,
        "energy_replaces_primary": False,
        "evidence_role": "linked_property_task_output",
    }


def _q_sc_eom_conditioning_audit(payload: dict[str, Any]) -> dict[str, Any]:
    states = payload.get("states") if isinstance(payload.get("states"), list) else []
    root_audits: list[dict[str, Any]] = []
    overlap_condition_numbers: list[float] = []
    regularization_actions: set[str] = set()
    for state in states:
        if not isinstance(state, dict):
            continue
        metadata = state.get("solver_metadata")
        if not isinstance(metadata, dict) or metadata.get("method") != "q_sc_eom":
            continue
        root_audit = metadata.get("root_residual_audit")
        if isinstance(root_audit, dict):
            root_audits.append(root_audit)
        overlap = metadata.get("overlap_condition_number")
        if isinstance(overlap, int | float):
            overlap_condition_numbers.append(float(overlap))
        regularization_actions.update(
            str(item)
            for item in metadata.get("regularization_actions", [])
            if item
        )

    residuals = [
        float(item["residual_norm"])
        for item in root_audits
        if isinstance(item.get("residual_norm"), int | float)
    ]
    neighbor_gaps = [
        abs(float(item["min_neighbor_gap_hartree"]))
        for item in root_audits
        if isinstance(item.get("min_neighbor_gap_hartree"), int | float)
    ]
    root_tracking_statuses = sorted(
        {
            str(item.get("root_tracking_status"))
            for item in root_audits
            if item.get("root_tracking_status") is not None
        }
    )
    degenerate_root_count = sum(
        1
        for item in root_audits
        if item.get("root_tracking_status") == "degenerate_subspace"
    )
    max_condition = (
        max(overlap_condition_numbers) if overlap_condition_numbers else None
    )
    conditioning_status = (
        "regularization_required"
        if "overlap_conditioning_requires_regularization" in regularization_actions
        else "degenerate_subspace_tracking_required"
        if degenerate_root_count
        else "well_conditioned_reference_roots"
        if root_audits
        else "not_evaluated"
    )
    return {
        "status": conditioning_status,
        "root_count": len(root_audits),
        "max_root_residual_norm": max(residuals) if residuals else None,
        "min_neighbor_gap_hartree": min(neighbor_gaps) if neighbor_gaps else None,
        "root_tracking_statuses": root_tracking_statuses,
        "degenerate_root_count": degenerate_root_count,
        "overlap_condition_number": max_condition,
        "overlap_condition_threshold": 1.0e8,
        "regularization_actions": sorted(regularization_actions),
        "energy_replaces_primary": False,
        "evidence_role": "exact_root_conditioning_reference_audit",
    }


def _q_sc_eom_payload(
    spec: Any,
    excited_state_result: Any,
    property_result: Any = None,
) -> dict[str, Any] | None:
    task = getattr(getattr(spec, "tasks", None), "excited_state", None)
    if task is None:
        return None
    if not getattr(task, "enabled", False) or str(task.method).strip().lower() != "q_sc_eom":
        return None
    payload = to_primitive(excited_state_result)
    if not isinstance(payload, dict) or not payload:
        return None
    conditioning_audit = _q_sc_eom_conditioning_audit(payload)
    transition_property_audit = _q_sc_eom_property_audit(property_result)
    return {
        **payload,
        "trust_gate": "exploratory",
        "energy_replaces_primary": False,
        "conditioning_audit": conditioning_audit,
        "transition_property_audit": transition_property_audit,
        "overlap_condition_number": conditioning_audit.get("overlap_condition_number"),
        "conditioning_status": conditioning_audit.get("status"),
        "max_root_residual_norm": conditioning_audit.get("max_root_residual_norm"),
        "min_neighbor_gap_hartree": conditioning_audit.get("min_neighbor_gap_hartree"),
        "root_tracking_statuses": conditioning_audit.get("root_tracking_statuses"),
        "transition_property_status": transition_property_audit.get("status"),
        "transition_property_count": transition_property_audit.get(
            "requested_transition_property_count"
        ),
        "validated_transition_property_count": transition_property_audit.get(
            "validated_transition_property_count"
        ),
        "transition_property_names": transition_property_audit.get("property_names"),
        "max_transition_dipole_magnitude": transition_property_audit.get(
            "max_transition_dipole_magnitude"
        ),
        "max_oscillator_strength": transition_property_audit.get(
            "max_oscillator_strength"
        ),
    }


def _q_embed_payload(spec: Any, embedding_result: Any) -> dict[str, Any] | None:
    embedding = getattr(getattr(spec, "problem", None), "embedding", None)
    if embedding is None:
        return None
    if not getattr(embedding, "enabled", False) or str(embedding.method).strip().lower() != "q_dmet":
        return None
    payload = to_primitive(embedding_result)
    if not isinstance(payload, dict) or not payload:
        return None
    environment = (
        payload.get("environment_metadata")
        if isinstance(payload.get("environment_metadata"), dict)
        else {}
    )
    boundary = (
        environment.get("embedding_boundary_audit")
        if isinstance(environment.get("embedding_boundary_audit"), dict)
        else {}
    )
    density_history = (
        environment.get("density_mismatch_history")
        if isinstance(environment.get("density_mismatch_history"), list)
        else []
    )
    first_density_audit = (
        density_history[0]
        if density_history and isinstance(density_history[0], dict)
        else {}
    )
    density_mismatch_audit = (
        environment.get("density_mismatch_audit")
        if isinstance(environment.get("density_mismatch_audit"), dict)
        else {}
    )
    fragment_coverage_audit = (
        environment.get("fragment_coverage_audit")
        if isinstance(environment.get("fragment_coverage_audit"), dict)
        else {}
    )
    return {
        **payload,
        "trust_gate": "exploratory",
        "energy_replaces_primary": False,
        "embedding_execution_status": environment.get("embedding_execution_status"),
        "density_mismatch_status": first_density_audit.get("status"),
        "density_mismatch_audit_status": density_mismatch_audit.get("status")
        or first_density_audit.get("mismatch_status"),
        "fragment_population_delta_norm": boundary.get("fragment_population_delta_norm"),
        "fragment_population_delta_l1_norm": boundary.get("fragment_population_delta_l1_norm"),
        "fragment_population_delta_signed_sum": boundary.get("fragment_population_delta_signed_sum"),
        "max_fragment_population_delta_abs": boundary.get("max_fragment_population_delta_abs"),
        "density_mismatch_threshold": density_mismatch_audit.get("threshold")
        or first_density_audit.get("density_mismatch_threshold"),
        "fragment_energy_sum_gap_hartree": boundary.get("fragment_energy_sum_gap_hartree"),
        "fragment_energy_sum_gap_abs_hartree": boundary.get("fragment_energy_sum_gap_abs_hartree"),
        "fragment_energy_sum_gap_per_fragment_hartree": boundary.get(
            "fragment_energy_sum_gap_per_fragment_hartree"
        ),
        "self_consistency_loop_executed": bool(
            boundary.get("self_consistency_loop_executed", False)
        ),
        "self_consistency_iteration_count": boundary.get("self_consistency_iteration_count"),
        "density_matching_performed": bool(boundary.get("density_matching_performed", False)),
        "density_matching_iteration_count": boundary.get("density_matching_iteration_count"),
        "correlation_potential_parameter_count": boundary.get(
            "correlation_potential_parameter_count"
        ),
        "fragment_ao_coverage_fraction": fragment_coverage_audit.get("ao_coverage_fraction"),
        "fragment_atom_coverage_fraction": fragment_coverage_audit.get("atom_coverage_fraction"),
        "fragment_coverage_status": fragment_coverage_audit.get("status"),
        "missing_self_consistency_components": list(
            boundary.get("missing_self_consistency_components") or []
        ),
        "fragment_energy_sum_replaces_primary": bool(
            boundary.get("fragment_energy_sum_replaces_primary", False)
        ),
    }


def _method_promotion_gate_audit(spec: Any, active_methods: dict[str, Any]) -> dict[str, Any]:
    """Summarize which method-evidence entries can support which claim types."""

    solver_kind = str(getattr(getattr(spec, "solver", None), "kind", "")).strip().lower()
    records: dict[str, dict[str, Any]] = {}

    for name, raw_payload in sorted(active_methods.items()):
        payload = raw_payload if isinstance(raw_payload, dict) else {}
        record: dict[str, Any] = {
            "method": name,
            "primary_solver_selected": False,
            "energy_replacement_allowed": False,
            "accuracy_claim_allowed": False,
            "hardware_claim_allowed": False,
            "planning_metric_allowed": False,
            "resource_model_claim_allowed": False,
            "claim_status": str(
                payload.get("trust_gate")
                or payload.get("claim_status")
                or payload.get("pbc_trust_tier")
                or "exploratory"
            ),
            "evidence_role": "sidecar_evidence",
            "promotion_required_for_validated_claim": True,
            "promotion_blockers": ["benchmark_gate_required_for_validated_claim"],
        }

        if name == "e_adapt_result":
            record.update(
                {
                    "primary_solver_selected": solver_kind in {"adapt_vqe", "e_adapt_vqe"},
                    "claim_status": (
                        "primary_solver_exploratory"
                        if solver_kind in {"adapt_vqe", "e_adapt_vqe"}
                        else "sidecar_evidence_only"
                    ),
                    "evidence_role": "adaptive_solver_trace",
                    "promotion_blockers": ["accuracy_benchmark_gate_required"],
                }
            )
        elif name == "orbital_optimization":
            readiness = (
                payload.get("promotion_readiness_audit")
                if isinstance(payload.get("promotion_readiness_audit"), dict)
                else {}
            )
            transfer = (
                payload.get("orbital_transfer_audit")
                if isinstance(payload.get("orbital_transfer_audit"), dict)
                else {}
            )
            record.update(
                {
                    "claim_status": "reference_diagnostic_only",
                    "evidence_role": "casscf_reference_diagnostic",
                    "promotion_readiness_status": readiness.get("status"),
                    "readiness_level": readiness.get("readiness_level"),
                    "solver_replacement_allowed": readiness.get("solver_replacement_allowed"),
                    "energy_replacement_allowed": readiness.get("energy_replacement_allowed"),
                    "optimized_orbitals_applied_to_primary_solver": transfer.get(
                        "optimized_orbitals_applied_to_primary_solver"
                    ),
                    "primary_hamiltonian_rebuilt_from_optimized_orbitals": transfer.get(
                        "primary_hamiltonian_rebuilt_from_optimized_orbitals"
                    ),
                    "required_promotion_evidence_count": readiness.get(
                        "required_promotion_evidence_count"
                    ),
                    "promotion_blocker_count": readiness.get("promotion_blocker_count"),
                    "promotion_blockers": list(
                        readiness.get("promotion_blockers")
                        or [
                            "casscf_reference_does_not_replace_primary_energy",
                            "active_space_resolve_not_applied_to_primary_solver",
                        ]
                    ),
                }
            )
        elif name == "qsci_plus_result":
            record.update(
                {
                    "claim_status": "selected_ci_subspace_audit",
                    "evidence_role": "selected_ci_variational_audit",
                    "promotion_blockers": [
                        "selected_subspace_benchmark_gate_required",
                        "primary_energy_replacement_disallowed",
                    ],
                }
            )
        elif name == "post_correlation":
            blockers = [
                "external_correlation_energy_not_emitted",
                "double_counting_not_evaluated",
                "qcchem_qsci_correction_backend_missing",
            ]
            tailored = payload.get("tailored_amplitudes") if isinstance(payload.get("tailored_amplitudes"), dict) else {}
            eligibility = (
                payload.get("correction_eligibility_audit")
                if isinstance(payload.get("correction_eligibility_audit"), dict)
                else {}
            )
            mapping = (
                payload.get("amplitude_mapping_audit")
                if isinstance(payload.get("amplitude_mapping_audit"), dict)
                else {}
            )
            blockers.extend(str(item) for item in tailored.get("required_inputs_missing", []) if item)
            record.update(
                {
                    "claim_status": str(payload.get("trust_gate") or "unsupported_for_claim"),
                    "evidence_role": "correction_eligibility_audit",
                    "correction_eligibility_status": eligibility.get("status"),
                    "eligible_coefficient_count": eligibility.get("eligible_coefficient_count"),
                    "amplitude_mapping_status": mapping.get("status"),
                    "mapped_single_count": mapping.get("mapped_single_count"),
                    "mapped_double_count": mapping.get("mapped_double_count"),
                    "backend_executable": eligibility.get("backend_executable"),
                    "correction_energy_emitted": eligibility.get("correction_energy_emitted"),
                    "energy_replaces_primary": eligibility.get("energy_replaces_primary"),
                    "required_input_missing_count": eligibility.get(
                        "required_input_missing_count"
                    ),
                    "promotion_blockers": sorted(set(blockers)),
                }
            )
        elif name == "q_sc_eom":
            record.update(
                {
                    "claim_status": "conditioning_reference_audit",
                    "evidence_role": "excited_state_conditioning_audit",
                    "conditioning_status": payload.get("conditioning_status"),
                    "overlap_condition_number": payload.get("overlap_condition_number"),
                    "transition_property_status": payload.get("transition_property_status"),
                    "validated_transition_property_count": payload.get(
                        "validated_transition_property_count"
                    ),
                    "transition_property_names": list(
                        payload.get("transition_property_names") or []
                    ),
                    "promotion_blockers": [
                        "exact_root_audit_not_general_eom_solver",
                        "excited_state_benchmark_gate_required",
                    ],
                }
            )
        elif name == "q_embed":
            record.update(
                {
                    "claim_status": str(
                        payload.get("embedding_execution_status")
                        or "fragment_reference_only"
                    ),
                    "evidence_role": "embedding_fragment_reference_audit",
                    "density_mismatch_audit_status": payload.get("density_mismatch_audit_status"),
                    "fragment_coverage_status": payload.get("fragment_coverage_status"),
                    "fragment_ao_coverage_fraction": payload.get("fragment_ao_coverage_fraction"),
                    "fragment_atom_coverage_fraction": payload.get("fragment_atom_coverage_fraction"),
                    "self_consistency_iteration_count": payload.get(
                        "self_consistency_iteration_count"
                    ),
                    "density_matching_iteration_count": payload.get(
                        "density_matching_iteration_count"
                    ),
                    "correlation_potential_parameter_count": payload.get(
                        "correlation_potential_parameter_count"
                    ),
                    "missing_self_consistency_components": list(
                        payload.get("missing_self_consistency_components") or []
                    ),
                    "promotion_blockers": [
                        "q_dmet_self_consistency_not_executed",
                        "density_matching_not_performed",
                        "fragment_energy_sum_does_not_replace_primary",
                    ],
                }
            )
        elif name == "kq_pbc_result":
            audit = (
                payload.get("non_gamma_mapping_audit")
                if isinstance(payload.get("non_gamma_mapping_audit"), dict)
                else {}
            )
            readiness = (
                payload.get("promotion_readiness_audit")
                if isinstance(payload.get("promotion_readiness_audit"), dict)
                else {}
            )
            coverage = (
                readiness.get("coverage_audit")
                if isinstance(readiness.get("coverage_audit"), dict)
                else audit.get("coverage_audit")
                if isinstance(audit.get("coverage_audit"), dict)
                else {}
            )
            record.update(
                {
                    "claim_status": str(audit.get("status") or "audit_only"),
                    "evidence_role": "pbc_k_twist_audit",
                    "promotion_readiness_status": readiness.get("status"),
                    "readiness_level": readiness.get("readiness_level"),
                    "named_kpoint_execution_coverage_fraction": coverage.get(
                        "named_kpoint_execution_coverage_fraction"
                    ),
                    "mesh_kpoint_execution_coverage_fraction": coverage.get(
                        "mesh_kpoint_execution_coverage_fraction"
                    ),
                    "twist_energy_coverage_fraction": coverage.get(
                        "twist_energy_coverage_fraction"
                    ),
                    "missing_twist_energy_fraction": coverage.get(
                        "missing_twist_energy_fraction"
                    ),
                    "promotion_blocker_count": readiness.get("promotion_blocker_count")
                    or audit.get("promotion_blocker_count"),
                    "unsupported_claim_count": readiness.get("unsupported_claim_count")
                    or audit.get("unsupported_claim_count"),
                    "promotion_blockers": list(audit.get("promotion_blockers") or []),
                }
            )
        elif name == "ft_qpe_resource_estimate":
            resource = (
                payload.get("resource_model_audit")
                if isinstance(payload.get("resource_model_audit"), dict)
                else {}
            )
            readiness = (
                payload.get("promotion_readiness_audit")
                if isinstance(payload.get("promotion_readiness_audit"), dict)
                else {}
            )
            formula = (
                payload.get("resource_formula_audit")
                if isinstance(payload.get("resource_formula_audit"), dict)
                else {}
            )
            record.update(
                {
                    "claim_status": str(resource.get("resource_claim_status") or "resource_model_only"),
                    "evidence_role": "fault_tolerant_resource_model",
                    "resource_model_claim_allowed": True,
                    "validated_resource_advantage_claim_allowed": bool(
                        readiness.get("validated_resource_advantage_claim_allowed")
                    ),
                    "planning_metric_allowed": True,
                    "promotion_readiness_status": readiness.get("status")
                    or resource.get("promotion_readiness_status"),
                    "readiness_level": readiness.get("readiness_level")
                    or resource.get("readiness_level"),
                    "resource_formula_scope": formula.get("scope")
                    or resource.get("model_scope"),
                    "reference_encoding": readiness.get("reference_encoding")
                    or resource.get("reference_encoding"),
                    "best_encoding": readiness.get("best_encoding")
                    or resource.get("best_encoding")
                    or resource.get("recommended_encoding"),
                    "encoding_comparison_count": readiness.get("encoding_comparison_count")
                    or resource.get("encoding_comparison_count"),
                    "logical_error_budget_available": readiness.get("logical_error_budget_available")
                    if "logical_error_budget_available" in readiness
                    else resource.get("logical_error_budget_available"),
                    "required_promotion_evidence_count": readiness.get(
                        "required_promotion_evidence_count"
                    )
                    or resource.get("required_promotion_evidence_count"),
                    "required_promotion_evidence": list(
                        readiness.get("required_promotion_evidence")
                        or resource.get("required_promotion_evidence")
                        or []
                    ),
                    "promotion_blockers": list(resource.get("promotion_blockers") or []),
                    "promotion_blocker_count": readiness.get("promotion_blocker_count")
                    or resource.get("promotion_blocker_count"),
                }
            )
        elif name == "trust_qem":
            allowed = list(payload.get("claim_allowed_methods") or [])
            disallowed = list(payload.get("claim_disallowed_methods") or [])
            pec = payload.get("pec") if isinstance(payload.get("pec"), dict) else {}
            pec_audit = (
                pec.get("calibration_model_audit")
                if isinstance(pec.get("calibration_model_audit"), dict)
                else {}
            )
            record.update(
                {
                    "claim_status": str(payload.get("claim_status") or "unsupported_for_claim"),
                    "evidence_role": "mitigation_provenance_audit",
                    "mitigation_claim_allowed_methods": allowed,
                    "mitigation_claim_disallowed_methods": disallowed,
                    "pec_status": pec.get("status"),
                    "pec_executable_calibration_model": pec.get(
                        "executable_calibration_model"
                    ),
                    "pec_calibrated_operation_count": pec_audit.get(
                        "calibrated_operation_count"
                    ),
                    "pec_quasi_probability_entry_count": pec_audit.get(
                        "quasi_probability_entry_count"
                    ),
                    "pec_max_operation_l1_overhead": pec_audit.get(
                        "max_operation_l1_overhead"
                    ),
                    "pec_sampling_overhead": pec.get("sampling_overhead"),
                    "promotion_blockers": (
                        ["no_mitigation_component_allowed_for_energy_claim"]
                        if not allowed
                        else ["mitigated_energy_does_not_replace_primary"]
                    ),
                }
            )
        elif name == "shadow_lr":
            cost_model = (
                payload.get("measurement_cost_model")
                if isinstance(payload.get("measurement_cost_model"), dict)
                else {}
            )
            record.update(
                {
                    "claim_status": "planning_metric_only",
                    "evidence_role": "measurement_planning_cost_model",
                    "planning_metric_allowed": True,
                    "estimated_cost_claim_status": "planning_metric_only",
                    "hardware_cost_claim_allowed": False,
                    "allocated_shots": cost_model.get("allocated_shots"),
                    "grouped_precision_baseline_shots": cost_model.get(
                        "grouped_precision_baseline_shots"
                    ),
                    "basis_l1_coverage_fraction": cost_model.get(
                        "basis_l1_coverage_fraction"
                    ),
                    "unselected_basis_count": cost_model.get("unselected_basis_count"),
                    "max_allocated_shot_fraction": cost_model.get(
                        "max_allocated_shot_fraction"
                    ),
                    "allocation_entropy": cost_model.get("allocation_entropy"),
                    "grouped_precision_variance_proxy": cost_model.get(
                        "grouped_precision_variance_proxy"
                    ),
                    "variance_inflation_vs_grouped_precision_proxy": cost_model.get(
                        "variance_inflation_vs_grouped_precision_proxy"
                    ),
                    "plan_digest": cost_model.get("plan_digest"),
                    "promotion_blockers": [
                        "not_hardware_calibrated",
                        "accuracy_claim_not_supported_by_measurement_plan_alone",
                    ],
                }
            )

        records[name] = record

    sidecar_energy_replacement_allowed = [
        name for name, record in records.items() if record.get("energy_replacement_allowed")
    ]
    accuracy_claim_allowed = [
        name for name, record in records.items() if record.get("accuracy_claim_allowed")
    ]
    hardware_claim_allowed = [
        name for name, record in records.items() if record.get("hardware_claim_allowed")
    ]
    planning_metric_methods = [
        name for name, record in records.items() if record.get("planning_metric_allowed")
    ]
    resource_model_only_methods = [
        name
        for name, record in records.items()
        if record.get("claim_status") == "resource_model_only"
    ]
    unsupported_for_claim_methods = [
        name
        for name, record in records.items()
        if record.get("claim_status") == "unsupported_for_claim"
    ]

    return {
        "schema": "qcchem.method_promotion_gate_audit.v1",
        "primary_solver_kind": solver_kind or None,
        "primary_energy_policy": "raw_solver_energy_remains_primary",
        "sidecar_energy_replacement_allowed_methods": sidecar_energy_replacement_allowed,
        "accuracy_claim_allowed_methods": accuracy_claim_allowed,
        "hardware_claim_allowed_methods": hardware_claim_allowed,
        "planning_metric_methods": planning_metric_methods,
        "resource_model_only_methods": resource_model_only_methods,
        "unsupported_for_claim_methods": unsupported_for_claim_methods,
        "method_records": records,
        "overall_claim_status": "promotion_required",
        "promotion_required_for_validated_claims": True,
        "notes": [
            "Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.",
            "Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.",
        ],
    }


def build_and_write_method_evidence(
    *,
    sidecar_path: Path | None,
    spec: Any,
    solver_outcome: Any,
    physical_mapping: Any,
    solver_energy: float | None,
    mitigation: Any,
    measurement: Any,
    qsci_payload: dict[str, Any] | None,
    excited_state_result: Any = None,
    property_result: Any = None,
    embedding_result: Any = None,
) -> tuple[
    MethodEvidenceSummary | None,
    EADAPTResultSummary | None,
    OrbitalOptimizationSummary | None,
    QSCIPlusResultSummary | None,
    PostCorrelationSummary | None,
    KQPBCResultSummary | None,
    FTQPEResourceEstimateSummary | None,
]:
    """Build and persist the method-evidence sidecar."""
    e_adapt = _e_adapt_summary(solver_outcome)
    orbital = _orbital_summary(solver_outcome)
    qsci = _qsci_summary(qsci_payload)
    post = _post_correlation_summary(spec, qsci)
    kq_pbc = _kq_pbc_summary(spec, solver_energy=solver_energy)
    ft_qpe = _ft_qpe_summary(spec, physical_mapping)
    trust_qem_payload = _trust_qem_payload(mitigation)

    methods = {
        "e_adapt_result": to_primitive(e_adapt),
        "orbital_optimization": to_primitive(orbital),
        "qsci_plus_result": to_primitive(qsci),
        "post_correlation": to_primitive(post),
        "q_sc_eom": _q_sc_eom_payload(spec, excited_state_result, property_result),
        "q_embed": _q_embed_payload(spec, embedding_result),
        "kq_pbc_result": to_primitive(kq_pbc),
        "ft_qpe_resource_estimate": to_primitive(ft_qpe),
        "trust_qem": trust_qem_payload,
        "shadow_lr": to_primitive(measurement) if getattr(measurement, "planner", "") == "shadow_lr" else None,
    }
    active_methods = {key: value for key, value in methods.items() if value not in (None, {}, [])}
    if not active_methods:
        return None, e_adapt, orbital, qsci, post, kq_pbc, ft_qpe

    promotion_gate_audit = _method_promotion_gate_audit(spec, active_methods)
    payload = {
        "schema": SCHEMA,
        "methods": active_methods,
        "promotion_gate_audit": promotion_gate_audit,
        "trust_tier": "exploratory",
        "notes": [
            "Method evidence is reported alongside the primary solver result.",
            "Exploratory method sections do not promote chemical-accuracy claims by themselves.",
        ],
    }
    digest = _json_sha256(payload)
    if sidecar_path is not None:
        sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    summary = MethodEvidenceSummary(
        available=True,
        schema=SCHEMA,
        sidecar_path=(str(sidecar_path) if sidecar_path is not None else None),
        sidecar_sha256=digest,
        methods={
            key: {
                "available": True,
                "trust_tier": (value.get("trust_gate") if isinstance(value, dict) else None)
                or (value.get("pbc_trust_tier") if isinstance(value, dict) else None)
                or "exploratory",
            }
            for key, value in active_methods.items()
        },
        promotion_gate_audit=promotion_gate_audit,
        trust_tier="exploratory",
        notes=list(payload["notes"]),
    )
    return summary, e_adapt, orbital, qsci, post, kq_pbc, ft_qpe
