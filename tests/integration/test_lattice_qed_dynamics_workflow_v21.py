from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_h2_lattice_qed_dynamics_writes_exact_trotter_curves_and_report(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lattice_qed_dynamics.yaml",
        output_dir=tmp_path / "h2_lattice_qed_dynamics",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.qft_dynamics is not None
    assert result.qft_dynamics["enabled"] is True
    assert len(result.qft_dynamics["exact"]["time_points"]) == 41
    assert result.qft_dynamics["trotter"]["circuit_resources"]["time_point_count"] == 41
    assert max(result.qft_dynamics["exact"]["observables"]["total_gauss_violation"]) <= 1.0e-8

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["qft_dynamics"]["quench"]["kind"] == "local_hopping_pulse"
    paths = result.artifacts.field_evidence
    assert paths is not None
    field_dynamics = json.loads(paths.dynamics_json.read_text(encoding="utf-8"))
    assert field_dynamics["available"] is True
    assert field_dynamics["dynamics"]["exact"]["available"] is True
    assert field_dynamics["dynamics"]["trotter"]["available"] is True
    assert field_dynamics["exact_vs_trotter_error_matrix"]["available"] is True
    assert field_dynamics["exact_vs_trotter_error_matrix"]["rows"]
    assert {"time", "observable", "exact", "trotter", "abs_error"} <= set(
        field_dynamics["exact_vs_trotter_error_matrix"]["rows"][0]
    )
    field_observables = json.loads(paths.observables_json.read_text(encoding="utf-8"))
    assert field_observables["gauss"]["total_gauss_violation"]
    assert field_observables["electric"]["total_electric_energy"]
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "QFT Real-Time Dynamics" in report
    assert "Field Evidence Artifacts" in report


@pytest.mark.integration
def test_h2_lattice_qed_dynamics_runtime_writes_guarded_batch_preview(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lattice_qed_dynamics_runtime.yaml",
        output_dir=tmp_path / "h2_lattice_qed_dynamics_runtime",
        exploratory_command=True,
    )

    assert result.qft_dynamics is not None
    runtime_batch = result.qft_dynamics["runtime_batch"]
    assert runtime_batch["attempted"] is True
    assert runtime_batch["submitted"] is False
    assert runtime_batch["failure_category"] == "runtime_submission_disabled"
    assert runtime_batch["pub_count"] > 0
    assert runtime_batch["observable_policy"] == "aggregate_gauge"


@pytest.mark.integration
def test_h2_2d_lattice_qed_dynamics_records_plaquette_wilson_curves(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_2d_lattice_qed_plaquette_dynamics.yaml",
        output_dir=tmp_path / "h2_2d_lattice_qed_plaquette_dynamics",
        exploratory_command=True,
    )

    assert result.qft_model is not None
    assert result.qft_model.dimensions == 2
    assert result.qft_model.plaquette_count > 0
    assert result.qft_dynamics is not None
    assert result.qft_dynamics["observables"]["plaquette_wilson_count"] > 0
    assert result.qft_dynamics["exact"]["skipped_reason"] is None
    assert result.qft_dynamics["exact"]["observables"]["total_wilson"]
    assert result.artifacts.field_evidence is not None
    field_observables = json.loads(result.artifacts.field_evidence.observables_json.read_text(encoding="utf-8"))
    assert field_observables["wilson"]["plaquette_count"] > 0
    assert field_observables["wilson"]["exact_curve"]
