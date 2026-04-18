"""AI workspace domain objects owned by QCchem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AIProviderSpec:
    """Provider configuration for an OpenAI-compatible workspace backend."""

    provider_name: str
    provider_kind: str = "openai_compatible"
    base_url: str = ""
    api_key_ref: str = ""
    model: str = ""
    timeout_seconds: int = 60
    default_temperature: float = 0.1
    default_max_tokens: int = 2000
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass(slots=True)
class AITaskTicket:
    """Structured task ticket used by the AI workspace flow."""

    task_id: str
    task_type: str
    title: str
    request_text: str
    plan_summary: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    boundary_notes: list[str] = field(default_factory=list)
    confirmation_required: bool = True
    execution_target: str = "analysis_only_assistant"
    linked_artifacts: list[str] = field(default_factory=list)
    linked_session_id: str | None = None
    status: str = "draft"
