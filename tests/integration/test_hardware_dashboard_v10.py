from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.reporting.aggregate import write_hardware_calibration_report
from qcchem.reporting.markdown import render_markdown_report
from qcchem.io.serialization import to_primitive
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_hardware_run_report_mentions_hardware_sections(tmp_path: Path) -> None:
    result = run_from_config(
        Path("/Users/a0000/QCchem/configs/lih_active_shot_runtime_ready_compressed.yaml"),
        output_dir=tmp_path / "lih_runtime_preview",
    )

    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Hardware Execution" in report_text
    assert "Calibration Summary" in report_text


@pytest.mark.integration
def test_hardware_run_report_keeps_hardware_sections_when_data_is_unavailable(tmp_path: Path) -> None:
    result = run_from_config(
        Path("/Users/a0000/QCchem/configs/h2_exact.yaml"),
        output_dir=tmp_path / "h2_exact_preview",
    )
    payload = to_primitive(result)
    payload["calibration"] = None
    payload["runtime_submission"] = None
    payload["hardware_verified"] = False
    payload["hardware_evidence_tier"] = None
    report_text = render_markdown_report(payload)

    assert "Calibration Summary" in report_text
    assert "- available: `False`" in report_text
    assert "Hardware Execution" in report_text
    assert "- hardware_verified: `False`" in report_text
    assert "- attempted: `None`" in report_text


@pytest.mark.integration
def test_hardware_dashboard_serializes_summary(tmp_path: Path) -> None:
    dashboard = {
        "cases": [
            {
                "name": "h2_runtime_probe",
                "estimated_measurement_cost": 8000,
                "measured_shot_usage": 4096,
                "measured_wall_time_seconds": 15.0,
                "achieved_error": 0.03,
                "hardware_verified": True,
            }
        ]
    }

    output = tmp_path / "hardware_dashboard.md"
    write_hardware_calibration_report(dashboard, output)
    text = output.read_text(encoding="utf-8")
    assert "estimated vs measured cost" in text.lower()
    assert "h2_runtime_probe" in text
