"""AI workspace domain objects owned by QCchem."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


AI_WORKSPACE_TICKET_STATUS_DRAFT = "draft"
AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION = "needs_confirmation"
AI_WORKSPACE_TICKET_STATUS_ACCEPTED = "accepted"
AI_WORKSPACE_TICKET_STATUS_RUNNING = "running"
AI_WORKSPACE_TICKET_STATUS_BLOCKED = "blocked"
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
    AI_WORKSPACE_TICKET_STATUS_BLOCKED: AI_WORKSPACE_TICKET_LANE_RETURNED,
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
class EvidenceSourceRecord:
    """One normalized evidence source consumed by the research agent."""

    source_id: str
    artifact_kind: str
    artifact_path: str
    artifact_root: str
    path_hash: str
    payload_hash: str
    trust_tier: str
    verification_status: str | None = None
    primary_scientific_claim: str = ""
    primary_baseline: dict[str, Any] = field(default_factory=dict)
    primary_error_metric: dict[str, Any] = field(default_factory=dict)
    chemical_accuracy_status: str = "unavailable"
    runtime_evidence_status: str = "none"
    hardware_verified: bool = False
    hardware_evidence_tier: str | None = None
    recommended_action: str = "review_evidence_boundary"
    output_links: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        """Convert the evidence record into JSON-safe data."""
        return asdict(self)


@dataclass(slots=True)
class EvidenceGraphSummary:
    """Bounded evidence graph used to ground AI tickets and reviews."""

    graph_id: str
    sources: list[EvidenceSourceRecord] = field(default_factory=list)
    best_chemistry_evidence: dict[str, Any] | None = None
    best_runtime_evidence: dict[str, Any] | None = None
    trust_tier: str = "exploratory"
    recommended_action: str = "review_evidence_boundary"
    trust_gap: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    boundary_notes: list[str] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        """Convert the graph into JSON-safe data."""
        payload = asdict(self)
        payload["sources"] = [source.to_record() for source in self.sources]
        return payload


@dataclass(slots=True)
class ResearchActionProposal:
    """A single explicit action that may be routed by the AI workspace."""

    action_id: str
    action_kind: str
    title: str
    rationale: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = True
    risk_tier: str = "standard"
    allowed: bool = True
    blocked_reason: str = ""
    route: str = "analysis_only_assistant"

    def to_record(self) -> dict[str, Any]:
        """Convert the action proposal into JSON-safe data."""
        return asdict(self)


@dataclass(slots=True)
class AIModelCallRecord:
    """Provenance for one optional model call."""

    call_id: str
    provider_name: str
    provider_kind: str
    model: str
    request_hash: str
    response_hash: str | None = None
    status: str = "not_called"
    created_at: str = ""
    fallback_used: bool = False
    error: str = ""

    def to_record(self) -> dict[str, Any]:
        """Convert the call record into JSON-safe data."""
        return asdict(self)


@dataclass(slots=True)
class AIProvenanceEvent:
    """Append-only provenance event for AI workspace actions."""

    event_id: str
    timestamp: str
    event_type: str
    actor: str
    summary: str
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        """Convert the provenance event into JSON-safe data."""
        return asdict(self)


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
    evidence_context: dict[str, Any] = field(default_factory=dict)
    action_plan: dict[str, Any] = field(default_factory=dict)
    risk_assessment: dict[str, Any] = field(default_factory=dict)
    cost_estimate: dict[str, Any] = field(default_factory=dict)
    model_provenance: list[dict[str, Any]] = field(default_factory=list)
    execution_provenance: list[dict[str, Any]] = field(default_factory=list)

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
