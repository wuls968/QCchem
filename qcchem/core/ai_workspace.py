"""AI workspace domain objects owned by QCchem."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


AI_WORKSPACE_TICKET_STATUS_DRAFT = "draft"
AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION = "needs_confirmation"
AI_WORKSPACE_TICKET_STATUS_ACCEPTED = "accepted"
AI_WORKSPACE_TICKET_STATUS_RUNNING = "running"
AI_WORKSPACE_TICKET_STATUS_SUBMITTED = "submitted"
AI_WORKSPACE_TICKET_STATUS_COMPLETED = "completed"
AI_WORKSPACE_TICKET_STATUS_RETURNED = "returned"

AI_WORKSPACE_TICKET_LANE_INBOX = "inbox"
AI_WORKSPACE_TICKET_LANE_RUNNING = "running"
AI_WORKSPACE_TICKET_LANE_SUBMITTED = "submitted"
AI_WORKSPACE_TICKET_LANE_COMPLETED = "completed"
AI_WORKSPACE_TICKET_LANE_RETURNED = "returned"

AI_WORKSPACE_TICKET_LANES = (
    AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_LANE_RUNNING,
    AI_WORKSPACE_TICKET_LANE_SUBMITTED,
    AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_LANE_RETURNED,
)

AI_WORKSPACE_TICKET_STATUS_TO_LANE = {
    AI_WORKSPACE_TICKET_STATUS_DRAFT: AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION: AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_STATUS_ACCEPTED: AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_STATUS_RUNNING: AI_WORKSPACE_TICKET_LANE_RUNNING,
    AI_WORKSPACE_TICKET_STATUS_SUBMITTED: AI_WORKSPACE_TICKET_LANE_SUBMITTED,
    AI_WORKSPACE_TICKET_STATUS_COMPLETED: AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_STATUS_RETURNED: AI_WORKSPACE_TICKET_LANE_RETURNED,
}


def ticket_lane_for_status(status: str | None) -> str | None:
    """Return the canonical lane for a ticket status."""
    if status is None:
        return None
    return AI_WORKSPACE_TICKET_STATUS_TO_LANE.get(status)


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

    def to_record(self) -> dict[str, Any]:
        """Convert the ticket into a JSON-safe record."""
        return asdict(self)


@dataclass(slots=True)
class AIDeliveryRecord:
    """Delivery metadata persisted for completed or submitted task work."""

    delivery_id: str
    task_id: str
    delivery_kind: str
    summary: str
    linked_outputs: list[str] = field(default_factory=list)
    submitted_by: str = "assistant"
    submitted_to: str = "user"
    review_status: str = "submitted"
    return_notes: str = ""
    evidence_summary: dict[str, Any] | None = None

    def to_record(self) -> dict[str, Any]:
        """Convert the delivery into a JSON-safe record."""
        return asdict(self)
