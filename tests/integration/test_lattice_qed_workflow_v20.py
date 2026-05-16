from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_h2_lattice_qed_exact_generates_exploratory_artifact(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lattice_qed_exact.yaml",
        output_dir=tmp_path / "h2_lattice_qed_exact",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.exact_baseline.available is True
    assert result.qft_model is not None
    assert result.qft_model.model == "lattice_qed_minimal_coupling"
    assert result.qft_model.dimensions == 1
    assert result.mapping.num_qubits == result.qft_model.total_qubits
    assert result.energy.exact_ground_energy == pytest.approx(result.energy.solver_energy, abs=1.0e-9)

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["qft_model"]["gauge_group"] == "u1"
    assert payload["qft_model"]["term_counts_by_sector"]["electric"] > 0
    assert "Lattice QED Field Model" in result.artifacts.report_markdown.read_text(encoding="utf-8")


@pytest.mark.integration
def test_lattice_qed_external_point_charges_are_reported_as_scalar_potential(tmp_path: Path) -> None:
    config_path = tmp_path / "h2_lattice_external.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-lattice-external
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.74]
  unit: angstrom
policy:
  allow_exploratory: true
exploratory:
  enabled: true
  modules: [lattice_qed]
problem:
  external_point_charges:
    enabled: true
    unit: angstrom
    charges:
      - label: mm_probe
        coords: [0.0, 0.0, 2.0]
        charge: -0.5
  qft:
    enabled: true
    dimensions: 1
    grid:
      shape: [2]
      spacing: [0.75]
      softening: 0.35
    matter:
      spin_components: 2
      target_electrons: auto
    gauge:
      electric_cutoff: 1
    constraints:
      gauss_law_penalty: 10.0
      particle_number_penalty: 10.0
      padding_penalty: 50.0
      max_sector_enumeration_qubits: 8
mapping:
  kind: jordan_wigner
backend:
  kind: statevector
solver:
  kind: exact
benchmark:
  enabled: true
  exact_baseline_qubit_limit: 12
run:
  output_dir: artifacts/h2_lattice_external
  overwrite: true
        """.strip(),
        encoding="utf-8",
    )

    result = run_from_config(
        config_path,
        output_dir=tmp_path / "h2-lattice-external",
        exploratory_command=True,
    )

    assert result.external_point_charges is not None
    assert result.external_point_charges.adapter_strategy == "lattice_qed.scalar_potential_only"
    assert result.qft_model is not None
    assert result.qft_model.term_counts_by_sector["external_point_charge"] > 0
    assert result.qft_model.external_point_charges["gauss_law_background_modified"] is False
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["external_point_charges"]["includes_mm_self_energy"] is False
    assert payload["qft_model"]["external_point_charges"]["gauss_law_background_modified"] is False
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "External Point Charges" in report
    assert "scalar_potential_only" in report


@pytest.mark.integration
def test_h2_lattice_qed_vqe_records_variational_qft_metadata(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lattice_qed_vqe.yaml",
        output_dir=tmp_path / "h2_lattice_qed_vqe",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.variational_result is not None
    assert result.variational_result.solver_kind == "vqe"
    assert result.qft_model is not None
    assert result.qft_model.site_count == 2
    assert result.qft_model.link_count == 1
    assert result.measurement is not None
    assert result.measurement.term_count == result.mapping.qubit_term_count
    assert any("finite cutoff" in note for note in result.scientific_risk_notes)


@pytest.mark.integration
def test_h2_lattice_qed_sector_audit_writes_physical_sector(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lattice_qed_sector_audit.yaml",
        output_dir=tmp_path / "h2_lattice_qed_sector_audit",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.qft_model is not None
    assert result.qft_model.physical_sector["enumerated"] is True
    assert result.qft_model.physical_sector["physical_sector_dimension"] > 0
    assert result.qft_model.hamiltonian_gauge_commutator_norms

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["qft_model"]["physical_sector"]["target_charge_sector"] == "neutral"
    assert "Gauge Constraint Audit" in result.artifacts.report_markdown.read_text(encoding="utf-8")


@pytest.mark.integration
def test_h2_lattice_qed_givqe_records_gauge_invariant_ansatz(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lattice_qed_givqe.yaml",
        output_dir=tmp_path / "h2_lattice_qed_givqe",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.variational_result is not None
    assert result.variational_result.solver_kind == "lattice_qed_givqe"
    assert result.qft_model is not None
    assert result.qft_model.gauge_invariant_ansatz["selected_generator_count"] > 0
    assert result.qft_model.constraint_expectations["gauss_law_violation_expectation"] <= 1.0e-8

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Gauge Constraint Audit" in report
    assert "finite-cutoff QFT correctness" in report
