from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.aggregate import (
    render_benchmark_report,
    render_scan_report,
    render_study_report,
)
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.study import run_study_from_config
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_study_workflow_aggregates_runs_and_writes_registry(tmp_path: Path) -> None:
    result = run_study_from_config(
        Path("configs/studies/mini_comparison.yaml"),
        output_dir=tmp_path / "study-mini",
    )

    assert result.run_records
    assert len(result.run_records) == 2
    assert result.summary.total_runs == 2
    assert result.artifacts.study_result_json.exists()
    assert result.artifacts.study_report_markdown.exists()
    assert result.artifacts.registry_json.exists()
    regenerated = render_study_report(json.loads(result.artifacts.study_result_json.read_text()))
    assert "Study Summary" in regenerated


@pytest.mark.integration
def test_benchmark_suite_runs_and_generates_aggregate_report(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/mini_suite.yaml"),
        output_dir=tmp_path / "bench-mini",
    )

    assert result.cases
    assert result.summary.total_cases >= 3
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    regenerated = render_benchmark_report(json.loads(result.artifacts.result_json.read_text()))
    assert "Benchmark Suite Summary" in regenerated


@pytest.mark.integration
def test_scan_workflow_generates_point_runs_and_scan_table(tmp_path: Path) -> None:
    result = run_scan_from_config(
        Path("configs/scans/h2_short_scan.yaml"),
        output_dir=tmp_path / "scan-mini",
    )

    assert len(result.points) == 3
    assert result.artifacts.scan_table_csv.exists()
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    assert all(point.run_artifact_root.exists() for point in result.points)
    regenerated = render_scan_report(json.loads(result.artifacts.result_json.read_text()))
    assert "Scan Summary" in regenerated


@pytest.mark.integration
def test_excited_state_and_property_tasks_persist_in_run_artifact(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2_multitask.yaml"), output_dir=tmp_path / "h2-multitask")

    assert result.excited_state_result is not None
    assert result.excited_state_result.states
    assert result.excited_state_result.verification_status in {"validated", "exploratory"}
    assert result.property_result is not None
    assert any(item.property_name == "dipole_moment" for item in result.property_result.properties)
    assert result.backend_capability.runtime_ready is True
    assert result.execution_policy.name == "publication"
    assert result.mitigation.symmetry_check["requested"] is True
    assert result.artifacts.result_json.exists()
    payload = json.loads(result.artifacts.result_json.read_text())
    assert "excited_state_result" in payload
    assert "property_result" in payload
