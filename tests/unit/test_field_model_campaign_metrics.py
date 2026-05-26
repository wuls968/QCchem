from __future__ import annotations

from types import SimpleNamespace

import pytest

from qcchem.field_models.campaign import (
    PHOTON_CUTOFF_DELTA_HARTREE_THRESHOLD,
    TROTTER_MAX_OBSERVABLE_ERROR_THRESHOLD,
    apply_field_model_cross_case_decisions,
    build_field_model_campaign_summary,
    build_field_model_decision_summary,
    extract_field_model_case_metrics,
)


def test_extract_lattice_field_model_metrics_and_preview_gate() -> None:
    result = SimpleNamespace(
        field_model=SimpleNamespace(
            model_kind="lattice_qed",
            registry_name="finite_cutoff_lattice_qed",
            capability_tier="exploratory",
            observables=["gauss_law"],
            resource_estimate={},
            error_budget={},
            risk_notes=[],
        ),
        qft_model=SimpleNamespace(
            matter_qubits=2,
            gauge_qubits=2,
            total_qubits=4,
            term_counts_by_sector={"hopping": 3},
            constraints={"gauss_law_tolerance": 1.0e-8},
            constraint_residuals={
                "reference_state_max_abs_gauss_law": 0.0,
                "max_hamiltonian_gauge_commutator_norm": 0.0,
            },
            engine={
                "actual_representation": "sparse_projected",
                "projected_dimension": 3,
                "full_dimension": 16,
                "pauli_materialization": "skipped",
            },
            physical_sector={"basis_index_count": 3},
        ),
        qft_dynamics={
            "trotter_error_summary": {
                "available": True,
                "max_loschmidt_abs_error": 5.0e-3,
            },
            "trotter": {
                "circuit_resources": {
                    "trotter_step": 0.1,
                    "max_depth": 20,
                    "max_operation_count": 30,
                    "max_two_qubit_gate_count": 4,
                }
            },
            "runtime_batch": {
                "attempted": True,
                "submitted": False,
                "failure_category": "runtime_submission_disabled",
                "pub_count": 4,
                "pubs_preview": [{"circuit_depth": 20}],
                "transpiled_pub_resources": [],
            },
        },
        field_evidence=SimpleNamespace(
            hamiltonian={
                "sector_energy_closure_available": True,
                "sector_energy_closure_error": 0.0,
            },
            observables={"ground_state_expectations_available": True},
            constraints={"physical_sector": {"basis_index_count": 3}},
            resources={"num_qubits": 4},
            error_budget={"finite_cutoff_boundary": True},
        ),
        cavity_qed_model=None,
        mapping=SimpleNamespace(num_qubits=4, qubit_term_count=12),
        exact_baseline=SimpleNamespace(available=True),
        benchmark=SimpleNamespace(absolute_error=0.0),
        runtime_submission=None,
        hardware_verified=False,
    )

    metrics = extract_field_model_case_metrics(result)

    assert metrics["field_model_kind"] == "lattice_qed"
    assert metrics["projected_dimension"] == 3
    assert metrics["field_sector_energy_closure_available"] is True
    assert metrics["field_physical_sector"]["basis_index_count"] == 3
    assert metrics["max_trotter_observable_error"] == 5.0e-3
    assert metrics["runtime_preview_available"] is True
    assert metrics["field_model_decision"]["hardware_candidate"] is True


def test_field_model_gate_flags_cutoff_trotter_and_ansatz_limits() -> None:
    metrics = {
        "field_model_kind": "pauli_fierz_cavity_qed",
        "local_exact_baseline_available": True,
        "photon_physical_subspace_leakage": 0.0,
        "photon_cutoff_delta_hartree": PHOTON_CUTOFF_DELTA_HARTREE_THRESHOLD * 2.0,
        "max_trotter_observable_error": TROTTER_MAX_OBSERVABLE_ERROR_THRESHOLD * 2.0,
        "vqe_vs_exact_error": 2.0e-3,
        "qubits": 6,
        "runtime_preview_available": True,
        "runtime_preview_submitted": False,
        "runtime_preview": {"max_logical_depth": 50, "max_transpiled_two_qubit_gate_count": 10},
    }

    decision = build_field_model_decision_summary(metrics)

    assert decision["cutoff_sensitive"] is True
    assert decision["trotter_limited"] is True
    assert decision["ansatz_limited"] is True
    assert decision["hardware_candidate"] is False
    assert "photon_cutoff_delta_above_gate" in decision["hardware_skip_reasons"]


def test_cross_case_cutoff_delta_refreshes_decisions_and_campaign_summary() -> None:
    cutoff_1 = SimpleNamespace(
        name="h2_cavity_cutoff_1",
        total_energy=-1.0,
        notes=[],
        metrics={
            "field_model_kind": "pauli_fierz_cavity_qed",
            "photon_cutoff_max_occupation": 1,
            "local_exact_baseline_available": True,
            "photon_physical_subspace_leakage": 0.0,
            "qubits": 6,
            "runtime_preview_available": True,
            "runtime_preview_submitted": False,
            "runtime_preview": {"max_logical_depth": 50},
        },
    )
    cutoff_2 = SimpleNamespace(
        name="h2_cavity_cutoff_2",
        total_energy=-1.01,
        notes=[],
        metrics={
            "field_model_kind": "pauli_fierz_cavity_qed",
            "photon_cutoff_max_occupation": 2,
            "local_exact_baseline_available": True,
            "photon_physical_subspace_leakage": 0.0,
            "qubits": 7,
            "runtime_preview_available": True,
            "runtime_preview_submitted": False,
            "runtime_preview": {"max_logical_depth": 50},
        },
    )
    trotter_ok = SimpleNamespace(
        name="h2_lattice_trotter_0p10",
        total_energy=0.0,
        notes=[],
        metrics={
            "field_model_kind": "lattice_qed",
            "trotter_step": 0.1,
            "max_trotter_observable_error": 1.0e-3,
            "field_model_decision": {"hardware_candidate": False},
        },
    )

    cases = [cutoff_1, cutoff_2, trotter_ok]
    apply_field_model_cross_case_decisions(cases)
    summary = build_field_model_campaign_summary(cases)

    assert cutoff_1.metrics["photon_cutoff_delta_hartree"] == pytest.approx(0.01)
    assert cutoff_1.metrics["field_model_decision"]["cutoff_sensitive"] is True
    assert summary["case_count"] == 3
    assert summary["recommended_trotter_step"]["case"] == "h2_lattice_trotter_0p10"
