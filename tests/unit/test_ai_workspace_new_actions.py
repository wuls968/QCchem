from __future__ import annotations

from qcchem.workflow.evidence_agent import build_action_proposal, classify_research_risk


def _empty_graph() -> dict[str, object]:
    return {
        "trust_tier": "exploratory",
        "boundary_notes": [],
        "open_questions": [],
    }


def test_ai_workspace_allows_new_local_analysis_actions() -> None:
    for request, expected in [
        ("check this claim against the artifact", "claim_check"),
        ("validate the evidence capsule for this artifact", "capsule_validate"),
        ("review promotion to validated_algorithm_candidate", "promotion_review"),
        ("plan this research objective", "objective_plan"),
        ("show objective status", "objective_status"),
    ]:
        action = build_action_proposal(
            task_type="analysis",
            request_text=request,
            linked_artifacts=["artifacts/h2"],
            evidence_graph=_empty_graph(),
        )
        assert action.action_kind == expected
        assert action.allowed is True


def test_promotion_review_to_validated_is_high_risk() -> None:
    action = build_action_proposal(
        task_type="analysis",
        request_text="review promotion to validated_algorithm_candidate",
        linked_artifacts=["artifacts/h2_lr_ace/result.json"],
        evidence_graph=_empty_graph(),
    ).to_record()

    risk = classify_research_risk(action, _empty_graph())

    assert risk["risk_tier"] == "high"
    assert any("promotion" in reason.lower() for reason in risk["reasons"])
