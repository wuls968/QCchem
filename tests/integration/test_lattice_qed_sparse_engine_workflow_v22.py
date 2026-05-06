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
    assert "QFT Physical-Sector Engine Audit" in result.artifacts.report_markdown.read_text(encoding="utf-8")


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
