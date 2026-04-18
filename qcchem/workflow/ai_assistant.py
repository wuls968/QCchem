"""OpenAI-compatible AI workspace helpers."""

from __future__ import annotations

import os
import uuid
from typing import Any

from qcchem.core.ai_workspace import AIProviderSpec, AITaskTicket


def _normalize_ticket_list(value: Any, *, field_name: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    raise ValueError(f"{field_name} must be a string, null, or list-like value")


def build_openai_client_kwargs(spec: AIProviderSpec) -> dict[str, Any]:
    """Build keyword arguments for an OpenAI-compatible client."""
    api_key = os.environ.get(spec.api_key_ref, "")
    if not api_key:
        raise ValueError(f"Missing API key environment variable: {spec.api_key_ref}")
    return {
        "api_key": api_key,
        "base_url": spec.base_url,
        "timeout": spec.timeout_seconds,
    }


def draft_analysis_ticket(
    *,
    request_text: str,
    structured_payload: dict[str, Any],
    linked_artifacts: list[str],
) -> AITaskTicket:
    """Draft a structured analysis ticket from a payload."""
    return AITaskTicket(
        task_id=f"analysis-{uuid.uuid4().hex[:10]}",
        task_type="analysis",
        title=str(structured_payload.get("title", "Research Analysis")).strip(),
        request_text=request_text,
        plan_summary=str(structured_payload.get("plan_summary", "")).strip(),
        expected_outputs=_normalize_ticket_list(
            structured_payload.get("expected_outputs"), field_name="expected_outputs"
        ),
        risk_notes=_normalize_ticket_list(structured_payload.get("risk_notes"), field_name="risk_notes"),
        linked_artifacts=linked_artifacts,
        status="needs_confirmation",
        execution_target="analysis_only_assistant",
    )
