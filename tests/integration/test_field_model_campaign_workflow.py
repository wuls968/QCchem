from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.workflow.benchmark import run_benchmark_suite_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_field_model_local_campaign_config_covers_required_case_families() -> None:
    spec = load_benchmark_suite_spec(REPO_ROOT / "benchmarks" / "field_model_qft_local_campaign_v1.yaml")
    names = {case.name for case in spec.cases}

    assert "h2_lattice_qed_2site_exact" in names
    assert "h2_lattice_qed_4site_sparse_exact" in names
    assert "h2_lattice_qed_2d_projected_exact" in names
    assert "h2_lattice_qed_2site_runtime_preview" in names
    assert "h2_cavity_pf_exact_cutoff_1" in names
    assert "h2_cavity_pf_exact_cutoff_2" in names
    assert "h2_cavity_pf_vqe_cutoff_1" in names
    assert any(
        case.overrides.get("problem.qft.dynamics.evolution.trotter_step") == 0.2
        for case in spec.cases
    )
    assert any(
        case.overrides.get("problem.cavity_qed.modes.0.coupling_strength") == 0.10
        for case in spec.cases
    )


@pytest.mark.integration
def test_field_model_mini_campaign_writes_metrics_and_report(tmp_path: Path) -> None:
    config_path = tmp_path / "mini_field_model_campaign.yaml"
    config_path.write_text(
        """
benchmark_suite:
  name: mini_field_model_campaign
  description: Small integration campaign for field-model metrics.
  registry_name: mini_field_model_campaign
  tags: [field_model, integration]
  cases:
    - name: lattice_exact
      kind: run
      config: configs/exploratory/h2_lattice_qed_exact.yaml
      expected_status: exploratory
    - name: cavity_cutoff_1
      kind: run
      config: configs/exploratory/h2_cavity_pf_exact.yaml
      expected_status: exploratory
    - name: cavity_cutoff_2
      kind: run
      config: configs/exploratory/h2_cavity_pf_cutoff_convergence.yaml
      expected_status: exploratory
""",
        encoding="utf-8",
    )

    result = run_benchmark_suite_from_config(
        config_path,
        output_dir=tmp_path / "mini_field_model_campaign",
    )

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    campaign = payload["dashboard_summary"]["field_model_campaign"]
    assert campaign["case_count"] == 3
    assert "lattice_qed" in campaign["by_model"]
    assert "pauli_fierz_cavity_qed" in campaign["by_model"]

    cases = {case["name"]: case for case in payload["cases"]}
    assert cases["lattice_exact"]["metrics"]["field_model_kind"] == "lattice_qed"
    cavity_metrics = cases["cavity_cutoff_1"]["metrics"]
    assert cavity_metrics["field_model_kind"] == "pauli_fierz_cavity_qed"
    assert cavity_metrics["photon_occupation"]
    assert cavity_metrics["photon_physical_subspace_leakage"] is not None
    assert cavity_metrics["photon_cutoff_delta_hartree"] is not None

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Field-Model Campaign" in report
    assert "Field Model: lattice_qed" in report
    assert "Field Model: pauli_fierz_cavity_qed" in report
