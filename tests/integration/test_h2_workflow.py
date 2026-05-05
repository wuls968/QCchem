from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_h2_workflow_generates_benchmarkable_artifacts(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2.yaml"), output_dir=tmp_path / "h2-run")

    assert result.energy.energy_units == "Hartree"
    assert result.schema_version == "qcchem.result.v0.8-alpha"
    assert result.execution_policy.name == "benchmark"
    assert result.backend_capability.statevector is True
    assert "constant_energy_correction" in result.energy.energy_formula
    assert result.reduction_audit is not None
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy,
        abs=1e-10,
    )
    assert result.energy.hf_reference_energy == pytest.approx(-1.1169989967540044, abs=1e-10)
    assert result.energy.exact_ground_energy == pytest.approx(-1.8572750302023824, abs=1e-8)
    assert result.benchmark.absolute_error < 1e-6
    assert result.benchmark.meets_threshold is True
    assert result.problem.transformers_applied == []
    assert result.problem.active_space_metadata is None
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    assert result.artifacts.resolved_config.exists()
    assert result.artifacts.log_file.exists()
    assert result.artifacts.exact_result_json.exists()

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    regenerated_report = render_markdown_report(payload)
    assert "Field Definitions" in regenerated_report
    assert "exact_ground_energy" in regenerated_report
    assert "Exact Baseline" in regenerated_report
