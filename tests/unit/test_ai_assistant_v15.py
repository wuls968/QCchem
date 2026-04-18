from __future__ import annotations

from qcchem.core.ai_workspace import AIProviderSpec
from qcchem.workflow.ai_assistant import build_openai_client_kwargs, draft_analysis_ticket


def test_build_openai_client_kwargs_uses_base_url_and_key_ref(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret-token")
    spec = AIProviderSpec(
        provider_name="research-openai",
        provider_kind="openai_compatible",
        base_url="https://api.example.com/v1",
        api_key_ref="OPENAI_API_KEY",
        model="gpt-5.4-mini",
    )

    kwargs = build_openai_client_kwargs(spec)

    assert kwargs["base_url"] == "https://api.example.com/v1"
    assert kwargs["api_key"] == "secret-token"
    assert kwargs["timeout"] == 60


def test_build_openai_client_kwargs_rejects_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    spec = AIProviderSpec(
        provider_name="research-openai",
        provider_kind="openai_compatible",
        base_url="https://api.example.com/v1",
        api_key_ref="OPENAI_API_KEY",
        model="gpt-5.4-mini",
    )

    try:
        build_openai_client_kwargs(spec)
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected build_openai_client_kwargs to raise ValueError")


def test_draft_analysis_ticket_returns_structured_ticket() -> None:
    payload = {
        "title": "Summarize H2 campaign",
        "plan_summary": "Compare runtime artifacts and produce a next-step recommendation.",
        "expected_outputs": ["summary.json", "markdown note"],
        "risk_notes": ["Do not overstate chemical accuracy."],
    }

    ticket = draft_analysis_ticket(
        request_text="Summarize the recent H2 campaign.",
        structured_payload=payload,
        linked_artifacts=["artifacts/hardware_calibration_suite_v1"],
    )

    assert ticket.task_type == "analysis"
    assert ticket.status == "needs_confirmation"
    assert ticket.execution_target == "analysis_only_assistant"
    assert ticket.request_text == "Summarize the recent H2 campaign."
    assert ticket.plan_summary == payload["plan_summary"]
    assert "summary.json" in ticket.expected_outputs
    assert ticket.linked_artifacts == ["artifacts/hardware_calibration_suite_v1"]
    assert ticket.title == "Summarize H2 campaign"
    assert ticket.task_id.startswith("analysis-")


def test_draft_analysis_ticket_normalizes_scalar_sequence_fields() -> None:
    payload = {
        "title": "Summarize H2 campaign",
        "expected_outputs": "summary.json",
        "risk_notes": None,
    }

    ticket = draft_analysis_ticket(
        request_text="Summarize the recent H2 campaign.",
        structured_payload=payload,
        linked_artifacts=[],
    )

    assert ticket.expected_outputs == ["summary.json"]
    assert ticket.risk_notes == []
