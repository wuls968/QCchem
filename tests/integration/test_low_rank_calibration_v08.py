from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.config import load_run_spec
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config


def test_h2_hardware_probe_config_has_runtime_submission_enabled() -> None:
    spec = load_run_spec(Path("/Users/a0000/QCchem/configs/h2_runtime_hardware_probe.yaml"))
    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.options["submit_real_job"] is True


def test_lih_hardware_probe_v2_config_uses_compression() -> None:
    spec = load_run_spec(Path("/Users/a0000/QCchem/configs/lih_active_runtime_hardware_probe_v2.yaml"))
    assert spec.problem.compression.enabled is True
    assert spec.problem.measurement.strategy == "low_rank_commuting"


@pytest.mark.integration
def test_low_rank_run_persists_empirical_calibration_and_runtime_attempt(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_active_shot_runtime_ready_compressed.yaml"),
        output_dir=tmp_path / "lih-low-rank-calibration",
    )

    assert result.calibration is not None
    assert result.calibration.measured_wall_time_seconds > 0.0
    assert result.calibration.measured_shot_usage is not None
    assert result.calibration.precision_target == pytest.approx(5.0e-3, abs=1e-12)
    assert result.calibration.achieved_error is not None
    assert result.calibration.estimated_vs_measured_cost is not None

    assert result.runtime_submission is not None
    assert result.runtime_submission.attempted is True
    assert result.runtime_submission.service in {
        "runtime_placeholder",
        "ibm_runtime",
        "ibm_cloud",
        "ibm_quantum_platform",
    }
    assert result.runtime_submission.options_snapshot
    assert (
        result.runtime_submission.submitted is True
        or result.runtime_submission.failure_category is not None
    )

    assert result.artifacts.calibration_json is not None and result.artifacts.calibration_json.exists()
    assert (
        result.artifacts.calibration_report_markdown is not None
        and result.artifacts.calibration_report_markdown.exists()
    )
    assert (
        result.artifacts.runtime_submission_json is not None
        and result.artifacts.runtime_submission_json.exists()
    )

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert "calibration" in payload
    assert "runtime_submission" in payload


@pytest.mark.integration
def test_low_rank_benchmark_dashboard_reports_estimated_and_measured_costs(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/low_rank_suite_v1.yaml"),
        output_dir=tmp_path / "low-rank-dashboard",
    )

    assert result.artifacts is not None
    calibration_json = result.artifacts.root / "calibration_summary.json"
    calibration_report = result.artifacts.root / "calibration_report.md"
    assert calibration_json.exists()
    assert calibration_report.exists()

    suite_payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert "dashboard_summary" in suite_payload
    assert "calibration_summary" in suite_payload

    runtime_case = next(case for case in result.cases if "runtime" in case.name)
    assert runtime_case.metrics.get("estimated_measurement_cost") is not None
    assert runtime_case.metrics.get("measured_shot_usage") is not None
    assert runtime_case.metrics.get("achieved_error") is not None
    assert runtime_case.metrics.get("runtime_submission_status") is not None

    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "estimated_cost" in report_text
    assert "measured_cost" in report_text
    assert "achieved_error" in report_text
