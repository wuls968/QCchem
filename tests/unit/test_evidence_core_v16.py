from __future__ import annotations

from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary


def test_hardware_campaign_summary_marks_budget_pause_for_weak_retrieved_case() -> None:
    payload = {
        "suite_name": "hardware_calibration_suite_v1",
        "summary": {
            "total_cases": 1,
            "runtime_evidence_status_counts": {"retrieved_result": 1},
            "hardware_verified_cases": ["h2_runtime_probe"],
        },
        "cases": [
            {
                "name": "h2_runtime_probe",
                "achieved_error": 0.2673,
                "meets_chemical_accuracy": False,
                "distance_to_chemical_accuracy": 0.2657,
                "runtime_evidence_status": "retrieved_result",
                "runtime_submission_status": "succeeded",
                "hardware_verified": True,
                "backend_name": "ibm_marrakesh",
            }
        ],
    }

    summary = build_hardware_campaign_summary(payload)

    assert summary["decision_worthiness"]["recommended_action"] == "not_worth_additional_budget"
    assert summary["evidence_summary"]["recommended_action"] == "not_worth_additional_budget"


def test_hardware_campaign_summary_marks_follow_up_for_close_retrieved_case() -> None:
    payload = {
        "suite_name": "hardware_calibration_suite_v1",
        "summary": {
            "total_cases": 1,
            "runtime_evidence_status_counts": {"retrieved_result": 1},
            "hardware_verified_cases": ["h2_runtime_probe"],
        },
        "cases": [
            {
                "name": "h2_runtime_probe",
                "achieved_error": 0.0137,
                "meets_chemical_accuracy": False,
                "distance_to_chemical_accuracy": 0.0121,
                "runtime_evidence_status": "retrieved_result",
                "runtime_submission_status": "succeeded",
                "hardware_verified": True,
                "backend_name": "ibm_kingston",
            }
        ],
    }

    summary = build_hardware_campaign_summary(payload)

    assert summary["decision_worthiness"]["recommended_action"] == "worth_one_more_controlled_attempt"
    assert summary["evidence_summary"]["runtime_evidence_status"] == "retrieved_result"
