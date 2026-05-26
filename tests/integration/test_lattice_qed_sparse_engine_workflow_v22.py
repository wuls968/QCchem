from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_h2_4site_lattice_qed_sparse_exact_writes_projected_engine_artifact(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_4site_lattice_qed_sparse_exact.yaml",
        output_dir=tmp_path / "h2_4site_lattice_qed_sparse_exact",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.energy.exact_ground_energy is not None
    assert result.qft_model is not None
    assert result.qft_model.engine["actual_representation"] == "sparse_projected"
    assert result.qft_model.engine["projected_dimension"] > 0
    assert result.qft_model.engine["pauli_materialization"] == "skipped"
    assert result.qft_model.physical_sector["basis_hash"]
    assert result.qft_model.physical_sector["basis_index_count"] == result.qft_model.engine["projected_dimension"]
    assert result.artifacts.quantum_evidence_json is not None

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    sidecar = json.loads(result.artifacts.quantum_evidence_json.read_text(encoding="utf-8"))
    chemical_accuracy = payload["chemical_accuracy"]
    assert chemical_accuracy["finite_model_exactness"]["status"] == "passed"
    assert chemical_accuracy["continuum_chemistry_accuracy"]["status"] == "not_claimed"
    assert chemical_accuracy["hardware_accuracy"]["status"] == "unavailable"
    assert chemical_accuracy["meets_chemical_accuracy"] is None
    assert payload["evidence_summary"]["chemical_accuracy_status"] == "not_claimed"

    result_hamiltonian = payload["quantum_evidence"]["hamiltonian"]
    sidecar_hamiltonian = sidecar["hamiltonian"]
    assert result_hamiltonian["pauli_terms_available"] is False
    assert sidecar_hamiltonian["pauli_terms_available"] is False
    assert sidecar_hamiltonian["pauli_terms"] == []
    assert result_hamiltonian["pauli_term_count"] is None
    assert sidecar_hamiltonian["pauli_term_count"] is None
    assert result_hamiltonian["projected_matrix_dimension"] == result.qft_model.engine["projected_dimension"]
    assert result_hamiltonian["projected_hamiltonian_nnz"] == result.qft_model.engine["projected_hamiltonian_nnz"]
    assert result_hamiltonian["physical_sector_dimension"] == result.qft_model.physical_sector["basis_index_count"]
    assert result_hamiltonian["basis_hash"] == result.qft_model.physical_sector["basis_hash"]

    for validation in (
        payload["qft_model"]["sparse_exact_validation"],
        payload["quantum_evidence"]["sparse_exact_validation"],
        sidecar["sparse_exact_validation"],
    ):
        assert validation["available"] is True
        assert validation["eigen_residual_norm"] <= 1.0e-8
        assert validation["relative_eigen_residual"] <= 1.0e-8
        assert validation["ground_state_gap"] is not None
        assert validation["lowest_eigenvalues"]
        assert validation["projected_matrix_sha256"]
        assert validation["projected_matrix_dimension"] == result.qft_model.engine["projected_dimension"]
        assert validation["projected_hamiltonian_nnz"] == result.qft_model.engine["projected_hamiltonian_nnz"]

    observable_keys = {
        "site_density",
        "link_electric_flux",
        "electric_energy_by_link",
        "onsite_energy_by_site",
        "hopping_energy_by_link",
        "gauss_law_residual_by_site",
        "dominant_physical_sector_configurations",
    }
    observables = payload["qft_model"]["observables"]
    assert observable_keys <= set(observables)
    for key in observable_keys:
        assert "available" in observables[key]
        if observables[key]["available"] is False:
            assert observables[key]["reason"]

    measurement = sidecar["measurement"]
    assert measurement["measurement_group_count_scope"] == "sparse_exploratory_estimate"
    assert measurement["estimated_measurement_cost_scope"] == "sparse_exploratory_estimate"
    assert measurement["estimated_measurement_cost_is_hardware_cost"] is False

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Trust Boundary Summary / 可信边界摘要" in report
    assert "本次结果不证明 continuum chemistry accuracy" in report
    assert "QFT Physical-Sector Engine Audit" in report
    assert "pauli_terms_available" in report
    assert "eigen_residual_norm" in report
    assert "projected_matrix_sha256" in report


@pytest.mark.integration
def test_h2_4site_lattice_qed_sparse_dynamics_uses_projected_exact_curves(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_4site_lattice_qed_sparse_dynamics.yaml",
        output_dir=tmp_path / "h2_4site_lattice_qed_sparse_dynamics",
        exploratory_command=True,
    )

    assert result.qft_dynamics is not None
    exact = result.qft_dynamics["exact"]
    assert exact["available"] is True
    assert exact["operator_representation"] == "sparse_projected"
    assert exact["evolution_space"] == "physical_sector"
    assert exact["projected_dimension"] == result.qft_model.engine["projected_dimension"]
    assert max(exact["observables"]["total_gauss_violation"]) <= 1.0e-8
    assert result.qft_dynamics["trotter_error_summary"]["max_loschmidt_abs_error"] is not None


@pytest.mark.integration
def test_h2_2d_lattice_qed_projected_exact_records_plaquette_without_dense_pauli(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_2d_lattice_qed_projected_exact.yaml",
        output_dir=tmp_path / "h2_2d_lattice_qed_projected_exact",
        exploratory_command=True,
    )

    assert result.qft_model is not None
    assert result.qft_model.dimensions == 2
    assert result.qft_model.plaquette_count > 0
    assert result.qft_model.engine["actual_representation"] == "sparse_projected"
    assert result.qft_model.engine["pauli_materialization"] == "skipped"
    assert result.qft_model.engine["dense_full_matrix_materialized"] is False
    assert result.qft_model.physical_sector["basis_index_count"] == result.qft_model.engine["projected_dimension"]

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["qft_model"]["engine"]["projected_dimension"] > 0
    assert payload["qft_model"]["engine"]["pauli_materialization"] == "skipped"
