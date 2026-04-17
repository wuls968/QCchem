from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.aggregate import write_hardware_calibration_report
from qcchem.reporting.markdown import render_markdown_report
from qcchem.io.serialization import to_primitive
from qcchem.workflow.benchmark import build_hardware_calibration_suite
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
    assert result.hardware_verified is False
    assert result.hardware_evidence_tier is None

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
                "hardware_evidence_tier": "retrieved_result",
                "runtime_evidence_status": "retrieved_result",
            },
            {
                "name": "h2_local_reference",
                "estimated_measurement_cost": 1000,
                "measured_shot_usage": None,
                "measured_wall_time_seconds": 1.0,
                "achieved_error": 0.0,
                "hardware_verified": False,
                "hardware_evidence_tier": None,
                "runtime_evidence_status": "none",
            }
        ]
    }

    output = tmp_path / "hardware_dashboard.md"
    write_hardware_calibration_report(dashboard, output)
    text = output.read_text(encoding="utf-8")
    assert "estimated vs measured cost" in text.lower()
    assert "h2_runtime_probe" in text
    assert "retrieved_result" in text
    assert "h2_local_reference" in text
    assert "| none |" in text.lower()


@pytest.mark.integration
def test_hardware_suite_builder_uses_runtime_submission_evidence(tmp_path: Path) -> None:
    h2_result = {
        "run_id": "h2_runtime_probe",
        "hardware_verified": True,
        "hardware_evidence_tier": "retrieved_result",
        "calibration": {
            "measured_wall_time_seconds": 1.5,
            "measured_shot_usage": 9999,
            "achieved_error": 9.9,
        },
        "benchmark": {"absolute_error": 0.0195},
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": True,
            "submission_wall_time_seconds": 388.7,
            "job_id": "job-h2",
            "backend_name": "ibm_marrakesh",
            "returned_job_metadata": {"metadata": {"shots": 44}},
        },
    }
    lih_result = {
        "run_id": "lih_runtime_probe",
        "hardware_verified": False,
        "hardware_evidence_tier": None,
        "calibration": {
            "measured_wall_time_seconds": 2.5,
            "measured_shot_usage": 8888,
            "achieved_error": 8.8,
        },
        "benchmark": {"absolute_error": 0.0025},
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": False,
            "submission_wall_time_seconds": 22.4,
            "job_id": "job-lih",
            "backend_name": "ibm_fez",
            "failure_category": "job_result_failed",
        },
    }

    h2_path = tmp_path / "h2_runtime_probe" / "result.json"
    h2_path.parent.mkdir(parents=True, exist_ok=True)
    h2_path.write_text(json.dumps(h2_result), encoding="utf-8")
    lih_path = tmp_path / "lih_runtime_probe" / "result.json"
    lih_path.parent.mkdir(parents=True, exist_ok=True)
    lih_path.write_text(json.dumps(lih_result), encoding="utf-8")

    summary = build_hardware_calibration_suite(
        [h2_path, lih_path],
        output_root=tmp_path / "hardware_calibration_suite_v1",
    )

    summary_path = tmp_path / "hardware_calibration_suite_v1" / "hardware_calibration_summary.json"
    report_path = tmp_path / "hardware_calibration_suite_v1" / "hardware_calibration_report.md"
    assert summary_path.exists()
    assert report_path.exists()

    cases_by_name = {case["name"]: case for case in summary["cases"]}
    assert cases_by_name["h2_runtime_probe"]["runtime_evidence_status"] == "retrieved_result"
    assert cases_by_name["h2_runtime_probe"]["runtime_evidence_tier"] == "retrieved_result"
    assert cases_by_name["h2_runtime_probe"]["runtime_submission_wall_time_seconds"] == pytest.approx(388.7)
    assert cases_by_name["h2_runtime_probe"]["runtime_shots"] == 44
    assert cases_by_name["h2_runtime_probe"]["achieved_error"] == pytest.approx(0.0195)
    assert cases_by_name["lih_runtime_probe"]["runtime_evidence_status"] == "submitted"
    assert cases_by_name["lih_runtime_probe"]["runtime_evidence_tier"] == "submitted"
    assert cases_by_name["lih_runtime_probe"]["runtime_submission_status"] == "job_result_failed"
    assert cases_by_name["lih_runtime_probe"]["runtime_submission_wall_time_seconds"] == pytest.approx(22.4)
    assert cases_by_name["lih_runtime_probe"]["runtime_shots"] is None
    assert cases_by_name["lih_runtime_probe"]["achieved_error"] is None

    report_text = report_path.read_text(encoding="utf-8")
    assert "Runtime Evidence Status" in report_text
    assert "h2_runtime_probe" in report_text
    assert "lih_runtime_probe" in report_text
