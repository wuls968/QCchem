from __future__ import annotations

from pathlib import Path

from dash import html

from qcchem.core.ai_workspace import (
    AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_LANE_RETURNED,
    AI_WORKSPACE_TICKET_LANE_RUNNING,
    AI_WORKSPACE_TICKET_LANE_SUBMITTED,
)
from qcchem.workflow.ai_store import list_delivery_records, list_ticket_records, workspace_root
from qcchem.workbench.components.cards import callout_card, metric_card, status_card
from qcchem.workbench.evidence_console import format_action_label


def _ticket_card(record: dict[str, object]) -> html.Div:
    linked_artifacts = record.get("linked_artifacts") or []
    if not isinstance(linked_artifacts, list):
        linked_artifacts = []
    expected_outputs = record.get("expected_outputs") or []
    if not isinstance(expected_outputs, list):
        expected_outputs = []
    evidence_context = record.get("evidence_context") if isinstance(record.get("evidence_context"), dict) else {}
    action_plan = record.get("action_plan") if isinstance(record.get("action_plan"), dict) else {}
    risk_assessment = record.get("risk_assessment") if isinstance(record.get("risk_assessment"), dict) else {}
    return html.Div(
        className="qcchem-ai-workspace-page__ticket",
        children=[
            html.Div(
                className="qcchem-ai-workspace-page__ticket-topline",
                children=[
                    html.Strong(str(record.get("title", "Untitled Task"))),
                    html.Span(str(record.get("status", "draft")).replace("_", " "), className="qcchem-context-bar__chip"),
                ],
            ),
            html.Div(str(record.get("task_type", "unknown")).title(), className="qcchem-ai-workspace-page__ticket-meta"),
            html.P(str(record.get("plan_summary") or record.get("request_text") or "No task brief recorded."), className="qcchem-card-note"),
            html.Div(
                className="qcchem-ai-workspace-page__ticket-grid",
                children=[
                    html.Div([html.Span("Artifacts"), html.Strong(str(len(linked_artifacts)))]),
                    html.Div([html.Span("Outputs"), html.Strong(str(len(expected_outputs)))]),
                    html.Div([html.Span("Ticket"), html.Strong(str(record.get("task_id", "")))]),
                    html.Div([html.Span("Trust"), html.Strong(str(evidence_context.get("trust_tier") or "n/a"))]),
                    html.Div([html.Span("Action"), html.Strong(str(action_plan.get("action_kind") or "n/a"))]),
                    html.Div([html.Span("Risk"), html.Strong(str(risk_assessment.get("risk_tier") or "standard"))]),
                ],
            ),
        ],
    )


def _delivery_card(record: dict[str, object]) -> html.Div:
    evidence = record.get("evidence_summary") or record.get("linked_evidence_summary") or {}
    outputs = record.get("linked_outputs") or []
    if not isinstance(outputs, list):
        outputs = []
    limitation_notes = record.get("limitation_notes") or []
    if isinstance(limitation_notes, str):
        limitation_notes = [limitation_notes]
    if not isinstance(limitation_notes, list):
        limitation_notes = []
    recommended_action = record.get("recommended_action") or evidence.get("recommended_action") or "n/a"
    recommended_action_text = format_action_label(recommended_action)
    if str(recommended_action) != recommended_action_text:
        recommended_action_text = f"{recommended_action_text} ({recommended_action})"
    return html.Div(
        className="qcchem-ai-workspace-page__ticket",
        children=[
            html.Div(
                className="qcchem-ai-workspace-page__ticket-topline",
                children=[
                    html.Strong(str(record.get("summary", "Untitled delivery"))),
                    html.Span(str(record.get("review_status", "pending_review")), className="qcchem-context-bar__chip"),
                ],
            ),
            html.Div(str(record.get("delivery_kind", "delivery")), className="qcchem-ai-workspace-page__ticket-meta"),
            html.Div(
                className="qcchem-ai-workspace-page__ticket-grid",
                children=[
                    html.Div([html.Span("Trust tier"), html.Strong(str(evidence.get("trust_tier") or "n/a"))]),
                    html.Div([html.Span("Next action"), html.Strong(recommended_action_text)]),
                    html.Div([html.Span("Outputs"), html.Strong(str(len(outputs)))]),
                ],
            ),
            html.Div(
                className="qcchem-ai-workspace-page__ticket-grid",
                children=[
                    html.Div([html.Span("Evidence scope"), html.Strong(str(record.get("evidence_scope") or "Artifact evidence not scoped"))]),
                    html.Div([html.Span("Evidence claim"), html.Strong(str(evidence.get("primary_scientific_claim") or "n/a"))]),
                ],
            ),
            html.P("Limitation notes", className="qcchem-ai-workspace-page__ticket-meta"),
            html.P("; ".join(str(note) for note in limitation_notes) or "No limitation notes recorded.", className="qcchem-card-note qcchem-card-note--compact"),
            html.P(str(record.get("task_id", "")), className="qcchem-card-note qcchem-card-note--compact"),
        ],
    )


def _lane(section_id: str, title: str, note: str, tickets: list[dict[str, object]]) -> html.Section:
    body = [_ticket_card(ticket) for ticket in tickets] or [
        html.Div("No persisted items in this lane yet.", className="qcchem-ai-workspace-page__empty-state")
    ]
    return html.Section(
        id=section_id,
        className="qcchem-ai-workspace-page__lane",
        children=[
            html.P("Task Lane", className="qcchem-panel__eyebrow"),
            html.H2(title, className="qcchem-panel__title"),
            html.P(note, className="qcchem-panel__note"),
            html.Div(body, className="qcchem-ai-workspace-page__placeholder"),
        ],
    )


def layout() -> html.Div:
    root = workspace_root(Path.cwd(), create=False)
    inbox = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX)
    running = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RUNNING)
    submitted = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_SUBMITTED)
    completed = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_COMPLETED)
    returned = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RETURNED)
    deliveries = list_delivery_records(root)
    pending_analysis = [ticket for ticket in inbox if str(ticket.get("task_type", "")).lower() == "analysis"]
    research_os_actions = {
        "claim_check",
        "capsule_validate",
        "promotion_review",
        "objective_plan",
        "objective_status",
    }
    all_tickets = [*inbox, *running, *submitted, *completed, *returned]
    research_os_ticket_count = sum(
        1
        for ticket in all_tickets
        if str(((ticket.get("action_plan") or {}) if isinstance(ticket.get("action_plan"), dict) else {}).get("action_kind"))
        in research_os_actions
    )

    return html.Div(
        className="qcchem-page qcchem-ai-workspace-page",
        children=[
            html.Section(
                className="qcchem-ai-workspace-page__hero qcchem-card",
                children=[
                    html.P("Operational Surface", className="qcchem-card-eyebrow"),
                    html.H1("AI Workspace", className="qcchem-card-title"),
                    html.P(
                        "Treat the copilot as an evidence-first research operator: explain the current boundary, stage the ticket, and only then move work into execution or delivery.",
                        className="qcchem-ai-workspace-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-ai-workspace-page__hero-chips",
                        children=[
                            html.Span("Evidence-aware", className="qcchem-context-bar__chip"),
                            html.Span("Ticket-mediated", className="qcchem-context-bar__chip"),
                            html.Span("Artifact-grounded", className="qcchem-context-bar__chip"),
                        ],
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Inbox", str(len(inbox)), "Requests waiting for explicit acceptance", tone="compact"),
                            metric_card("Pending analysis", str(len(pending_analysis)), "Analysis work still waiting to be framed", tone="compact"),
                            metric_card("Completed", str(len(completed)), "Completed tickets ready for downstream use", tone="compact"),
                            metric_card("Deliveries", str(len(deliveries)), "Persisted outputs and review objects", tone="compact"),
                            metric_card(
                                "Research OS actions",
                                str(research_os_ticket_count),
                                "claim_check / capsule_validate / promotion_review / objective_plan / objective_status",
                                tone="compact",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    callout_card(
                        "Evidence-first operating rule",
                        "Every meaningful assistant action should begin with claim, baseline, trust tier, and recommended next action. Chat is not the authority; persisted artifacts are.",
                        eyebrow="Copilot protocol",
                    ),
                    status_card(
                        "Returned work",
                        str(len(returned)),
                        "Returned tickets remain visible so scope corrections and caution survive beyond a single chat turn.",
                        tone="exploratory" if returned else "informational",
                    ),
                ],
            ),
            html.Div(
                className="qcchem-ai-workspace-page__board",
                children=[
                    _lane(
                        "qcchem-ai-task-inbox",
                        "Inbox",
                        "New requests wait here for confirmation before any execution path is allowed.",
                        inbox,
                    ),
                    _lane(
                        "qcchem-ai-task-running",
                        "Running",
                        "Active work stays separate from drafts so the shell can show motion without implying persistence.",
                        running,
                    ),
                    _lane(
                        "qcchem-ai-task-submitted",
                        "Submitted",
                        "Submitted tickets preserve the handoff boundary between analysis and delivery.",
                        submitted,
                    ),
                    _lane(
                        "qcchem-ai-task-completed",
                        "Completed",
                        "Completed tickets become reportable outcomes once their delivery records are available.",
                        completed,
                    ),
                    _lane(
                        "qcchem-ai-task-returned",
                        "Returned",
                        "Returned tasks preserve scope corrections and cautionary notes instead of hiding them.",
                        returned,
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-ai-workspace-page__delivery-history",
                children=[
                    html.P("Delivery Surface", className="qcchem-card-eyebrow"),
                    html.H2("Delivery History", className="qcchem-card-title"),
                    html.P(
                        "Deliveries are the durable handoff object: summary, linked outputs, review status, and the evidence posture that produced them.",
                        className="qcchem-panel__note",
                    ),
                    html.Div(
                        id="qcchem-ai-delivery-history",
                        className="qcchem-ai-workspace-page__placeholder",
                        children=[_delivery_card(delivery) for delivery in deliveries]
                        or [html.Div("No persisted deliveries yet.", className="qcchem-ai-workspace-page__empty-state")],
                    ),
                ],
            ),
        ],
    )
