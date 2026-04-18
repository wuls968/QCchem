from pathlib import Path

import pytest

from qcchem.core.ai_workspace import AIProviderSpec, AITaskTicket
from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.workflow.ai_store import read_ticket_record, workspace_root, write_ticket_record


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
