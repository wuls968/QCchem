from qcchem.core.results import CalibrationSummary, RunResult
from qcchem.workflow.calibration import build_calibration_summary


def test_run_result_exposes_hardware_evidence_fields() -> None:
    assert "hardware_verified" in RunResult.__dataclass_fields__
    assert "hardware_evidence_tier" in RunResult.__dataclass_fields__


def test_calibration_summary_can_use_runtime_measured_values() -> None:
    summary = build_calibration_summary(
        measurement=None,
        sampled_result=None,
        benchmark=None,
        measured_wall_time_seconds=12.5,
        measured_shot_usage=4096,
        precision_target=0.1,
        achieved_error=0.02,
        estimated_measurement_cost=8000.0,
    )
    assert isinstance(summary, CalibrationSummary)
    assert summary.measured_wall_time_seconds == 12.5
    assert summary.measured_shot_usage == 4096
    assert summary.precision_target == 0.1
    assert summary.achieved_error == 0.02
