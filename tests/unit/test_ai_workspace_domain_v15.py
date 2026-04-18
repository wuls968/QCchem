from pathlib import Path

import pytest

from qcchem.core.ai_workspace import (
    AIProviderSpec,
    AITaskTicket,
    AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
    AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
    AI_WORKSPACE_TICKET_STATUS_RETURNED,
)
from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.workflow.ai_store import read_ticket_record, workspace_root, write_ticket_record
from qcchem.workflow.ai_workspace import (
    accept_ticket,
    build_ticket_from_form,
    classify_execution_risk,
    handle_ticket_editor_action,
    return_ticket,
)


def test_load_ai_provider_spec_openai_compatible(tmp_path: Path) -> None:
    config = tmp_path / "provider.yaml"
    config.write_text(
        """
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
  timeout_seconds: 60
  default_temperature: 0.1
  default_max_tokens: 2000
  enabled: true
""".strip(),
        encoding="utf-8",
    )

    spec = load_ai_provider_spec(config)

    assert spec.provider_kind == "openai_compatible"
    assert spec.base_url == "https://api.example.com/v1"
    assert spec.api_key_ref == "OPENAI_API_KEY"


def test_load_ai_provider_spec_defaults_provider_kind(tmp_path: Path) -> None:
    config = tmp_path / "provider.yaml"
    config.write_text(
        """
ai_provider:
  provider_name: research-openai
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
""".strip(),
        encoding="utf-8",
    )

    spec = load_ai_provider_spec(config)

    assert spec.provider_kind == "openai_compatible"


def test_load_ai_provider_spec_parses_false_enabled_string(tmp_path: Path) -> None:
    config = tmp_path / "provider.yaml"
    config.write_text(
        """
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
  enabled: "false"
""".strip(),
        encoding="utf-8",
    )

    spec = load_ai_provider_spec(config)

    assert spec.enabled is False


def test_ai_task_ticket_slots_dataclass() -> None:
    ticket = AITaskTicket(
        task_id="ticket-001",
        task_type="analysis",
        title="Compare H2 hardware probes",
        request_text="Summarize the recent H2 campaign.",
    )

    assert isinstance(ticket, AITaskTicket)
    assert ticket.status == "draft"
    assert ticket.confirmation_required is True


def test_write_and_read_ticket_record_roundtrip(tmp_path: Path) -> None:
    root = workspace_root(tmp_path)
    record = {
        "task_id": "ticket-001",
        "task_type": "analysis",
        "title": "Compare H2 hardware probes",
        "status": "needs_confirmation",
    }

    path = write_ticket_record(root, record)
    loaded = read_ticket_record(path)

    assert path.name == "ticket-001.json"
    assert loaded["title"] == "Compare H2 hardware probes"


def test_load_ai_provider_spec_rejects_unknown_provider_kind(tmp_path: Path) -> None:
    config = tmp_path / "provider.yaml"
    config.write_text(
        """
ai_provider:
  provider_name: invalid
  provider_kind: unsupported
  base_url: https://api.example.com/v1
  api_key_ref: BAD_KEY
  model: bad-model
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="provider_kind"):
        load_ai_provider_spec(config)


def test_build_ticket_from_form_normalizes_multiline_fields() -> None:
    ticket = build_ticket_from_form(
        task_type="execution",
        title="",
        request_text="Run the LiH runtime benchmark and bundle the outputs.",
        linked_artifacts_text="artifacts/lih_active_vqe\nartifacts/benchmark_suite_v1",
        plan_summary="",
        expected_outputs_text="execution summary\nartifact bundle",
        risk_notes_text="Respect validated boundaries\nConfirm runtime spend",
    )

    assert ticket.task_type == "execution"
    assert ticket.title == "Research Execution Ticket"
    assert ticket.status == AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION
    assert ticket.linked_artifacts == ["artifacts/lih_active_vqe", "artifacts/benchmark_suite_v1"]
    assert ticket.expected_outputs == ["execution summary", "artifact bundle"]
    assert ticket.risk_notes == ["Respect validated boundaries", "Confirm runtime spend"]


def test_classify_execution_risk_flags_runtime_facing_execution() -> None:
    risk = classify_execution_risk(
        {
            "task_type": "execution",
            "title": "Run benchmark on IBM runtime",
            "request_text": "Collect runtime benchmark evidence from the hardware queue.",
            "linked_artifacts": ["artifacts/benchmark_suite_v1"],
        }
    )

    assert risk["is_high_risk"] is True
    assert risk["risk_tier"] == "high"
    assert any("runtime" in reason.lower() or "benchmark" in reason.lower() for reason in risk["reasons"])


def test_classify_execution_risk_leaves_analysis_tickets_low_risk() -> None:
    risk = classify_execution_risk(
        {
            "task_type": "analysis",
            "title": "Summarize the H2 campaign",
            "request_text": "Compare the recent H2 hardware probes.",
            "linked_artifacts": ["artifacts/hardware_calibration_suite_v1"],
        }
    )

    assert risk["is_high_risk"] is False
    assert risk["risk_tier"] == "standard"


def test_accept_ticket_persists_accepted_status(tmp_path: Path) -> None:
    root = workspace_root(tmp_path)
    path = write_ticket_record(
        root,
        {
            "task_id": "ticket-accept-001",
            "task_type": "analysis",
            "title": "Explain H2 runtime gap",
            "request_text": "Explain the recent runtime gap",
            "status": AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
        },
    )

    payload = accept_ticket(path)

    assert payload["status"] == AI_WORKSPACE_TICKET_STATUS_ACCEPTED
    assert read_ticket_record(path)["status"] == AI_WORKSPACE_TICKET_STATUS_ACCEPTED


def test_return_ticket_persists_returned_status(tmp_path: Path) -> None:
    root = workspace_root(tmp_path)
    path = write_ticket_record(
        root,
        {
            "task_id": "ticket-return-001",
            "task_type": "analysis",
            "title": "Explain H2 runtime gap",
            "request_text": "Explain the recent runtime gap",
            "status": AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
        },
    )

    payload = return_ticket(path)

    assert payload["status"] == AI_WORKSPACE_TICKET_STATUS_RETURNED
    assert read_ticket_record(path)["status"] == AI_WORKSPACE_TICKET_STATUS_RETURNED


def test_run_requires_explicit_accept_even_for_analysis_ticket(tmp_path: Path) -> None:
    result = handle_ticket_editor_action(
        action="run",
        task_type="analysis",
        title="Explain H2 runtime gap",
        request_text="Summarize the current hardware campaign.",
        linked_artifacts_text="artifacts/hardware_calibration_suite_v1",
        plan_summary="Compare the current runtime probes.",
        expected_outputs_text="analysis summary",
        risk_notes_text="Respect validated boundaries",
        workspace_base=tmp_path,
    )

    assert result["did_change_workspace"] is False
    assert result["guard_state"]["visible"] is True
    assert "Draft the ticket first" in result["guard_state"]["message"]
