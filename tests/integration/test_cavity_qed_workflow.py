from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.scan_config import load_scan_spec
from qcchem.workflow.runner import run_from_config
from qcchem.workflow.scan import run_scan_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_h2_cavity_pf_exact_writes_field_model_artifact(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_cavity_pf_exact.yaml",
        output_dir=tmp_path / "h2_cavity_pf_exact",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.field_model is not None
    assert result.field_model.model_kind == "pauli_fierz_cavity_qed"
    assert result.cavity_qed_model is not None
    assert result.cavity_qed_model.observables["photon_occupation"]
    assert result.cavity_qed_model.observables["polaritonic_state_composition"]

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["field_model"]["model_kind"] == "pauli_fierz_cavity_qed"
    assert payload["cavity_qed_model"]["mode_count"] == 1
    assert payload["quantum_evidence"]["error_budget"]["field_model"]["finite_cutoff_boundary"] is True
    assert payload["quantum_evidence"]["resources"]["num_qubits"] == payload["cavity_qed_model"]["total_qubits"]
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Pauli-Fierz Cavity-QED Model" in report
    assert "Quantum Evidence" in report
    assert "photon occupation" in report.lower()


@pytest.mark.integration
def test_cavity_qed_inherits_static_point_charge_embedding(tmp_path: Path) -> None:
    config_path = tmp_path / "h2_cavity_external.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-cavity-external
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
policy:
  allow_exploratory: true
exploratory:
  enabled: true
  modules: [cavity_qed]
problem:
  external_point_charges:
    enabled: true
    charges:
      - label: mm_probe
        coords: [0.0, 0.0, 2.0]
        charge: -0.5
  cavity_qed:
    enabled: true
    modes:
      - frequency: 0.4
        coupling_strength: 0.02
        polarization: [0.0, 0.0, 1.0]
        max_occupation: 1
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
  output_dir: artifacts/h2_cavity_external
  overwrite: true
        """.strip(),
        encoding="utf-8",
    )

    result = run_from_config(
        config_path,
        output_dir=tmp_path / "h2-cavity-external",
        exploratory_command=True,
    )

    assert result.external_point_charges is not None
    assert "pauli_fierz" in result.external_point_charges.adapter_strategy
    assert result.environment_embedding is not None
    assert result.environment_embedding.active_space_projection["environment_qubit_growth"] == 0
    assert result.cavity_qed_model is not None
    assert result.verification_status == "exploratory"
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["external_point_charges"]["charge_count"] == 1
    assert payload["environment_embedding"]["one_body_environment"]["available"] is True
    assert payload["field_model"]["model_kind"] == "pauli_fierz_cavity_qed"
    assert payload["quantum_evidence"]["error_budget"]["qmmm_embedding"]["available"] is True
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "External Point Charges" in report
    assert "Environment Effective Hamiltonian" in report
    assert "Pauli-Fierz Cavity-QED Model" in report


@pytest.mark.integration
def test_h2_cavity_pf_vqe_compares_against_exact_baseline(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_cavity_pf_vqe.yaml",
        output_dir=tmp_path / "h2_cavity_pf_vqe",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.variational_result is not None
    assert result.exact_baseline.available is True
    assert result.benchmark.absolute_error is not None
    assert result.cavity_qed_model is not None
    assert result.cavity_qed_model.observables["vqe_vs_exact_error"] == pytest.approx(
        result.benchmark.absolute_error
    )


@pytest.mark.integration
def test_cavity_coupling_scan_uses_dotted_list_override(tmp_path: Path) -> None:
    scan_config = REPO_ROOT / "configs" / "scans" / "h2_cavity_coupling_scan.yaml"
    spec = load_scan_spec(scan_config)
    assert spec.parameter.kind == "config_override"
    assert spec.parameter.target == "problem.cavity_qed.modes.0.coupling_strength"

    result = run_scan_from_config(
        scan_config,
        output_dir=tmp_path / "h2_cavity_coupling_scan",
    )

    assert len(result.points) == 3
    assert all(point.verification_status == "exploratory" for point in result.points)
    values = []
    for point in result.points:
        payload = json.loads((point.run_artifact_root / "result.json").read_text(encoding="utf-8"))
        values.append(payload["cavity_qed_model"]["modes"][0]["coupling_strength"])
    assert values == pytest.approx([0.0, 0.04, 0.08])
