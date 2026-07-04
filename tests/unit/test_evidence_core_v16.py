from __future__ import annotations

from qcchem.core.evidence import summarize_artifact_payload
from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary


def test_run_evidence_summary_uses_legacy_exact_benchmark_as_strong_baseline() -> None:
    payload = {
        "run_id": "h2_legacy",
        "problem": {"molecule_name": "H2", "basis": "sto3g"},
        "backend": {"kind": "statevector"},
        "energy": {"total_energy": -1.137306034631007, "energy_units": "Hartree"},
        "benchmark": {
            "exact_available": True,
            "absolute_error": 1.12e-9,
            "absolute_error_threshold": 1e-6,
            "meets_threshold": True,
        },
    }

    summary = summarize_artifact_payload(payload)
    evidence = summary["evidence_summary"]

    assert evidence["primary_baseline"]["baseline_kind"] == "exact"
    assert evidence["primary_baseline"]["baseline_strength"] == "strong"
    assert evidence["chemical_accuracy_status"] == "met"
    assert evidence["primary_error_metric"]["value"] == 1.12e-9


def test_legacy_benchmark_suite_without_dashboard_summary_is_not_summarized_as_run() -> None:
    payload = {
        "suite_name": "benchmark_suite_v1",
        "summary": {"status_counts": {"validated": 1, "unstable": 1}, "total_cases": 2},
        "cases": [
            {
                "name": "h2_exact_reference",
                "kind": "run",
                "status": "validated",
                "expected_status": "validated",
                "absolute_error": 3.3e-15,
                "metrics": {"comparison_target": "exact_baseline"},
            },
            {
                "name": "h2_noisy",
                "kind": "run",
                "status": "unstable",
                "expected_status": "unstable",
                "absolute_error": 0.02,
                "metrics": {"comparison_target": "noisy_baseline"},
            },
        ],
    }

    summary = summarize_artifact_payload(payload)
    evidence = summary["evidence_summary"]

    assert summary["artifact_kind"] == "benchmark_suite"
    assert "Benchmark suite benchmark_suite_v1" in evidence["primary_scientific_claim"]
    assert "None Hartree" not in evidence["primary_scientific_claim"]
    assert evidence["trust_tier"] == "exploratory"
    assert evidence["primary_baseline"]["baseline_kind"] == "benchmark_suite_reference"
    assert evidence["primary_baseline"]["baseline_strength"] == "strong"
    assert evidence["primary_error_metric"]["metric_kind"] == "best_case_absolute_error_hartree"
    assert evidence["primary_error_metric"]["value"] == 3.3e-15


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
