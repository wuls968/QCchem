from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.io.serialization import to_primitive
from qcchem.reporting.aggregate import render_benchmark_report, write_hardware_calibration_report
from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sample_run_payload(tmp_path: Path) -> dict[str, object]:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "report_visual_run",
    )
    payload = to_primitive(result)
    payload["hardware_verified"] = True
    payload["hardware_evidence_tier"] = "retrieved_result"
    payload["runtime_submission"] = {
        "attempted": True,
        "submitted": True,
        "succeeded": True,
        "service": "qiskit-runtime",
        "backend_name": "ibm_kyiv",
        "provider": "ibm_quantum",
        "job_id": "job-visual-001",
        "transpiled_depth": 146,
        "transpiled_two_qubit_gate_count": 42,
        "selected_layout": [12, 15, 18, 19],
        "verification_status": "retrieved_result",
    }
    payload["runtime_chemical_accuracy"] = {
        "available": True,
        "assessment_target": "runtime_derived",
        "status": "exploratory",
        "meets_chemical_accuracy": False,
        "absolute_error_hartree": 0.0137,
        "absolute_error_kcal_mol": 8.59608,
        "threshold_hartree": 0.0016,
        "threshold_kcal_mol": 1.0040151584,
        "statistical_error": 0.0021,
        "notes": ["Runtime-derived chemistry estimate remains above the target."],
    }
    return payload


def _sample_benchmark_payload() -> dict[str, object]:
    return {
        "suite_name": "visual_benchmark_suite",
        "summary": {
            "total_cases": 3,
            "status_counts": {"validated": 2, "exploratory": 1},
        },
        "calibration_summary": {"available": 2},
        "dashboard_summary": {"hardware_verified": 1},
        "cases": [
            {
                "name": "h2_best_case",
                "kind": "run",
                "status": "validated",
                "expected_status": "validated",
                "absolute_error": 0.0012,
                "metrics": {"wall_time_seconds": 1.2},
            },
            {
                "name": "lih_preview",
                "kind": "run",
                "status": "validated",
                "expected_status": "validated",
                "absolute_error": 0.0048,
                "metrics": {"wall_time_seconds": 2.5},
            },
            {
                "name": "h2_noise_probe",
                "kind": "noise",
                "status": "exploratory",
                "expected_status": "exploratory",
                "absolute_error": 0.021,
                "metrics": {"wall_time_seconds": 3.8},
            },
        ],
    }


def _sample_hardware_campaign_summary() -> dict[str, object]:
    return {
        "summary": {
            "total_cases": 3,
            "runtime_evidence_status_counts": {"retrieved_result": 2, "submitted": 1},
            "hardware_verified_cases": ["h2_best_case"],
        },
        "cases": [
            {
                "name": "h2_best_case",
                "backend_name": "ibm_kyiv",
                "runtime_evidence_status": "retrieved_result",
                "runtime_evidence_tier": "retrieved_result",
                "runtime_submission_status": "succeeded",
                "runtime_submission_wall_time_seconds": 12.4,
                "runtime_shots": 44,
                "runtime_usage_seconds": 2,
                "runtime_usage_quantum_seconds": 1,
                "transpiled_depth": 146,
                "transpiled_two_qubit_gate_count": 42,
                "requested_precision_target": 0.05,
                "requested_budget_strategy": "shot_budget",
                "achieved_error": 0.0137,
                "achieved_error_status": "derived_from_runtime_result",
                "chemical_accuracy_target_hartree": 0.0016,
                "meets_chemical_accuracy": False,
                "distance_to_chemical_accuracy": 0.0121,
                "hardware_verified": True,
            },
            {
                "name": "lih_followup",
                "backend_name": "ibm_fez",
                "runtime_evidence_status": "retrieved_result",
                "runtime_evidence_tier": "retrieved_result",
                "runtime_submission_status": "succeeded",
                "runtime_submission_wall_time_seconds": 18.0,
                "runtime_shots": 88,
                "runtime_usage_seconds": 4,
                "runtime_usage_quantum_seconds": 3,
                "transpiled_depth": 152,
                "transpiled_two_qubit_gate_count": 44,
                "requested_precision_target": 0.05,
                "requested_budget_strategy": "shot_budget",
                "achieved_error": 0.0202,
                "achieved_error_status": "derived_from_runtime_result",
                "chemical_accuracy_target_hartree": 0.0016,
                "meets_chemical_accuracy": False,
                "distance_to_chemical_accuracy": 0.0186,
                "hardware_verified": True,
            },
            {
                "name": "h2_submission_only",
                "backend_name": "ibm_brisbane",
                "runtime_evidence_status": "submitted",
                "runtime_evidence_tier": "submitted",
                "runtime_submission_status": "submitted",
                "runtime_submission_wall_time_seconds": 9.1,
                "runtime_shots": None,
                "runtime_usage_seconds": None,
                "runtime_usage_quantum_seconds": None,
                "transpiled_depth": 161,
                "transpiled_two_qubit_gate_count": 47,
                "requested_precision_target": 0.05,
                "requested_budget_strategy": "shot_budget",
                "achieved_error": None,
                "achieved_error_status": "runtime_result_not_retrieved",
                "chemical_accuracy_target_hartree": 0.0016,
                "meets_chemical_accuracy": None,
                "distance_to_chemical_accuracy": None,
                "hardware_verified": False,
            },
        ],
    }


@pytest.mark.integration
def test_run_report_includes_cover_hero_and_runtime_accuracy_frames(tmp_path: Path) -> None:
    report = render_markdown_report(_sample_run_payload(tmp_path))

    assert "## Report Cover" in report
    assert "## Hero" in report
    assert "## Chemical Accuracy Frame" in report
    assert "## Runtime Evidence" in report
    assert "job-visual-001" in report
    assert "ibm_kyiv" in report


@pytest.mark.integration
def test_benchmark_report_highlights_best_case_and_distance_to_chemical_accuracy() -> None:
    report = render_benchmark_report(_sample_benchmark_payload())

    assert "## Report Cover" in report
    assert "## Best Case" in report
    assert "h2_best_case" in report
    assert "distance_to_chemical_accuracy" in report


@pytest.mark.integration
def test_hardware_campaign_report_calls_out_best_case_and_distance(tmp_path: Path) -> None:
    output_path = tmp_path / "hardware_campaign_report.md"

    write_hardware_calibration_report(_sample_hardware_campaign_summary(), output_path)
    report = output_path.read_text(encoding="utf-8")

    assert "## Best Case" in report
    assert "h2_best_case" in report
    assert "distance_to_chemical_accuracy" in report
    assert "retrieved_result" in report
