from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.aggregate import render_study_report
from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary
from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.agent import summarize_agent_target
from qcchem.workflow.runner import run_from_config
from qcchem.workbench.pages.overview import build_overview_page
from qcchem.workbench.viewmodels import build_run_view_model

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_run_result_publishes_evidence_summary(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_exact_evidence_summary",
    )

    evidence = result.evidence_summary

    assert evidence is not None
    assert evidence.trust_tier == result.verification_status
    assert evidence.primary_scientific_claim
    assert evidence.primary_baseline.baseline_kind == "exact"
    assert evidence.primary_baseline.baseline_strength == "strong"
    assert evidence.primary_error_metric["metric_kind"] == "absolute_error_hartree"
    assert evidence.chemical_accuracy_status in {"met", "not_met", "unavailable"}
    assert evidence.runtime_evidence_status == "none"
    assert evidence.recommended_action


@pytest.mark.integration
def test_markdown_report_includes_claim_chain_proof_and_evidence_summary(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_exact_report_evidence",
    )

    report_text = render_markdown_report(result)

    assert "## Evidence Summary" in report_text
    assert "## Claim" in report_text
    assert "## Chain" in report_text
    assert "## Proof" in report_text
    assert "primary_scientific_claim" in report_text
    assert "recommended_action" in report_text


@pytest.mark.integration
def test_hardware_campaign_summary_emits_decision_worthiness_and_recommended_action() -> None:
    payload = {
        "suite_name": "hardware_calibration_suite_v1",
        "summary": {
            "total_cases": 2,
            "runtime_evidence_status_counts": {"retrieved_result": 1, "submitted": 1},
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
            },
            {
                "name": "h2_runtime_probe_highshots",
                "achieved_error": 0.0533,
                "meets_chemical_accuracy": False,
                "distance_to_chemical_accuracy": 0.0517,
                "runtime_evidence_status": "submitted",
                "runtime_submission_status": "submitted",
                "hardware_verified": False,
                "backend_name": "ibm_kingston",
            },
        ],
    }

    summary = build_hardware_campaign_summary(payload)

    assert summary["evidence_summary"]["trust_tier"] == "hardware_verified"
    assert summary["recommended_case_name"] == "h2_runtime_probe"
    assert summary["decision_worthiness"]["recommended_action"] in {
        "worth_one_more_controlled_attempt",
        "pause",
        "not_worth_additional_budget",
        "continue",
    }
    assert summary["evidence_summary"]["recommended_action"] == summary["decision_worthiness"]["recommended_action"]


@pytest.mark.integration
def test_agent_summary_includes_evidence_summary_for_run_artifact(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_exact_agent_summary",
    )

    summary = summarize_agent_target(result.artifacts.root)

    assert summary["artifact_kind"] == "run"
    assert summary["evidence_summary"]["trust_tier"] == result.verification_status
    assert summary["evidence_summary"]["recommended_action"]
    assert summary["summary_json"]
    assert summary["report_markdown"]


@pytest.mark.integration
def test_run_view_model_and_overview_use_evidence_summary_when_available() -> None:
    payload = {
        "problem": {
            "molecule_name": "H2",
            "basis": "sto-3g",
        },
        "energy": {
            "total_energy": -1.1373,
            "electronic_energy": -1.8573,
            "nuclear_repulsion_energy": 0.72,
        },
        "mapping": {"kind": "jordan_wigner", "num_qubits": 4, "qubit_term_count": 15},
        "benchmark": {
            "absolute_error": 0.0002,
            "relative_error": 0.0001,
            "meets_threshold": True,
            "within_uncertainty": True,
            "threshold": 0.0016,
            "comparison_target": "exact diagonalization",
        },
        "runtime_submission": {
            "backend_name": "ibm_marrakesh",
            "result_provenance": {"attempt_stage": "result_retrieved"},
        },
        "verification_status": "validated",
        "hardware_verified": False,
        "chemical_accuracy": {
            "available": True,
            "meets_chemical_accuracy": True,
            "absolute_error_hartree": 0.0002,
            "threshold_hartree": 0.0016,
        },
        "runtime_chemical_accuracy": {
            "available": False,
            "meets_chemical_accuracy": None,
            "absolute_error_hartree": None,
            "threshold_hartree": 0.0016,
        },
        "evidence_summary": {
            "result_identity": {"artifact_kind": "run", "artifact_name": "h2_exact"},
            "primary_scientific_claim": "H2 exact run is chemically accurate against the exact baseline.",
            "primary_baseline": {
                "baseline_kind": "exact",
                "baseline_source": "exact_diagonalization",
                "baseline_scope": "single_run",
                "baseline_strength": "strong",
            },
            "primary_error_metric": {
                "metric_kind": "absolute_error_hartree",
                "value": 0.0002,
                "units": "Hartree",
                "threshold": 0.0016,
            },
            "chemical_accuracy_status": "met",
            "runtime_evidence_status": "none",
            "trust_tier": "validated",
            "recommended_action": "promote_validated_result",
            "decision_worthiness": {
                "recommended_action": "promote_validated_result",
            },
        },
    }

    view = build_run_view_model(payload)
    page = build_overview_page(view)
    page_text = " ".join(str(item) for item in page.children)

    assert view["evidence_summary"]["recommended_action"] == "promote_validated_result"
    assert view["hero"]["primary_claim"] == payload["evidence_summary"]["primary_scientific_claim"]
    assert "promote_validated_result" in page_text


@pytest.mark.integration
def test_study_report_uses_evidence_summary_language() -> None:
    payload = {
        "study_name": "mini_comparison_study",
        "summary": {
            "total_runs": 2,
            "status_counts": {"validated": 2},
            "comparison_axes": ["backend.kind"],
        },
        "run_records": [
            {
                "name": "h2_exact_reference",
                "verification_status": "validated",
                "backend_kind": "statevector",
                "mapping_kind": "jordan_wigner",
                "total_energy": -1.1373,
                "absolute_error": 0.0,
                "evidence_summary": {
                    "trust_tier": "validated",
                    "primary_scientific_claim": "Exact reference is the strongest local evidence in this study.",
                    "recommended_action": "promote_validated_result",
                },
            },
            {
                "name": "h2_variational_reference",
                "verification_status": "validated",
                "backend_kind": "statevector",
                "mapping_kind": "jordan_wigner",
                "total_energy": -1.1372,
                "absolute_error": 0.0001,
                "evidence_summary": {
                    "trust_tier": "validated",
                    "primary_scientific_claim": "Variational reference remains within defended study scope.",
                    "recommended_action": "compare_against_best_evidence",
                },
            },
        ],
        "evidence_summary": {
            "trust_tier": "validated",
            "primary_scientific_claim": "This study supports a validated comparison between exact and variational H2 local workflows.",
            "recommended_action": "promote_validated_result",
            "result_identity": {"artifact_kind": "study", "artifact_name": "mini_comparison_study"},
        },
    }

    report = render_study_report(payload)

    assert "Best Evidence" in report
    assert "recommended_action" in report
    assert "promote_validated_result" in report
