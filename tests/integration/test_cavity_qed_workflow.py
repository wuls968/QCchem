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
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Pauli-Fierz Cavity-QED Model" in report
    assert "photon occupation" in report.lower()


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
