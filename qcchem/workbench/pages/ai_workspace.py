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


LANE_NEXT_ACTIONS = {
    AI_WORKSPACE_TICKET_LANE_INBOX: "Draft or accept a ticket before execution.",
    AI_WORKSPACE_TICKET_LANE_RUNNING: "Review active tickets before starting another run.",
    AI_WORKSPACE_TICKET_LANE_SUBMITTED: "Inspect delivery records before closing the handoff.",
    AI_WORKSPACE_TICKET_LANE_COMPLETED: "Use completed tickets as the evidence-backed outcome list.",
    AI_WORKSPACE_TICKET_LANE_RETURNED: "Resolve returned scope notes before retrying execution.",
}


def _compact_record_label(record: dict[str, object] | None, *, fallback: str) -> str:
    if not record:
        return fallback
    record_id = str(record.get("task_id") or record.get("delivery_id") or "").strip()
    title = str(record.get("title") or record.get("summary") or "").strip()
    if record_id and title:
        return f"{record_id} - {title}"
    return record_id or title or fallback


def build_ticket_card(record: dict[str, object]) -> html.Div:
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


def _workflow_delivery_summary(record: dict[str, object]) -> dict[str, object]:
    workflow_summary = record.get("workflow_summary") if isinstance(record.get("workflow_summary"), dict) else {}
    run_summary = workflow_summary.get("summary") if isinstance(workflow_summary.get("summary"), dict) else {}
    workflow_run_summary = record.get("workflow_run_summary")
    if not run_summary and isinstance(workflow_run_summary, dict):
        run_summary = workflow_run_summary
    acceptance = workflow_summary.get("acceptance_summary") if isinstance(workflow_summary.get("acceptance_summary"), dict) else {}
    record_acceptance = record.get("acceptance_summary")
    if not acceptance and isinstance(record_acceptance, dict):
        acceptance = record_acceptance
    workflow_name = workflow_summary.get("workflow_name") or record.get("workflow_name")
    status = workflow_summary.get("status") or record.get("workflow_status")
    result_json = workflow_summary.get("workflow_result_json") or record.get("workflow_result_json")
    report_markdown = workflow_summary.get("workflow_report_markdown") or record.get("workflow_report_markdown")
    if not any([workflow_name, status, run_summary, acceptance, result_json, report_markdown]):
        return {}
    accepted = acceptance.get("accepted") if isinstance(acceptance, dict) else None
    accepted_label = "accepted" if accepted is True else "not accepted" if accepted is False else "not reviewed"
    return {
        "workflow_name": workflow_name or "workflow",
        "status": status or "unknown",
        "accepted_label": accepted_label,
        "completed_steps": (run_summary or {}).get("completed_steps", 0),
        "failed_steps": (run_summary or {}).get("failed_steps", 0),
        "generated_steps": (run_summary or {}).get("generated_steps", 0),
        "recommended_action": (acceptance or {}).get("recommended_action") or "n/a",
        "workflow_result_json": result_json or "n/a",
        "workflow_report_markdown": report_markdown or "n/a",
    }


def _compact_string(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        item = value.strip()
        return [item] if item else []
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def _action_text(action: object) -> str:
    raw_action = _compact_string(action) or "n/a"
    action_label = format_action_label(raw_action)
    if raw_action != action_label:
        return f"{action_label} ({raw_action})"
    return action_label


def _delivery_review_action(
    record: dict[str, object],
    evidence: dict[str, object],
    workflow: dict[str, object],
    outputs: list[str],
) -> str:
    explicit_action = _compact_string(record.get("review_action"))
    if explicit_action:
        return explicit_action
    review_status = _compact_string(record.get("review_status")).lower()
    if _compact_string(record.get("return_notes")) or review_status in {
        "returned",
        "needs_revision",
        "changes_requested",
    }:
        return "address_return_notes"
    if workflow and workflow.get("accepted_label") == "not accepted":
        return "review_workflow_acceptance"
    if outputs:
        return "review_linked_outputs"
    recommended_action = _compact_string(
        record.get("recommended_action") or evidence.get("recommended_action")
    )
    return recommended_action or "attach_delivery_outputs"


def _delivery_artifact_rows(
    record: dict[str, object],
    workflow: dict[str, object],
    outputs: list[str],
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen_paths: set[str] = set()

    def append_row(label: str, value: object) -> None:
        path = _compact_string(value)
        if not path or path == "n/a" or path in seen_paths:
            return
        rows.append((label, path))
        seen_paths.add(path)

    evidence_scope = _compact_string(record.get("evidence_scope"))
    if evidence_scope and evidence_scope != "Artifact evidence not scoped":
        append_row("Evidence scope", evidence_scope)
    append_row("Artifact root", record.get("artifact_root"))
    if workflow:
        append_row("Workflow result", workflow.get("workflow_result_json"))
        append_row("Workflow report", workflow.get("workflow_report_markdown"))
    for index, output in enumerate(outputs, start=1):
        label = "Linked output" if len(outputs) == 1 else f"Linked output {index}"
        append_row(label, output)
    return rows


def _delivery_artifact_list(rows: list[tuple[str, str]]) -> html.Div:
    if not rows:
        return html.Div(
            "No linked output paths recorded.",
            className="qcchem-ai-workspace-page__artifact-empty",
        )
    return html.Div(
        className="qcchem-ai-workspace-page__artifact-list",
        children=[
            html.Div(
                className="qcchem-ai-workspace-page__artifact-row",
                children=[html.Span(label), html.Code(path)],
            )
            for label, path in rows
        ],
    )


def build_delivery_card(record: dict[str, object]) -> html.Div:
    raw_evidence = record.get("evidence_summary") or record.get("linked_evidence_summary") or {}
    evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
    outputs = _string_list(record.get("linked_outputs"))
    limitation_notes = _string_list(record.get("limitation_notes"))
    recommended_action = record.get("recommended_action") or evidence.get("recommended_action") or "n/a"
    recommended_action_text = _action_text(recommended_action)
    workflow = _workflow_delivery_summary(record)
    review_action_text = _action_text(_delivery_review_action(record, evidence, workflow, outputs))
    artifact_rows = _delivery_artifact_rows(record, workflow, outputs)
    return_notes = _compact_string(record.get("return_notes"))
    return_note_children = (
        [
            html.P("Return notes", className="qcchem-ai-workspace-page__ticket-meta"),
            html.P(return_notes, className="qcchem-card-note qcchem-card-note--compact"),
        ]
        if return_notes
        else []
    )
    workflow_children: list[object] = []
    if workflow:
        workflow_children = [
            html.P("Workflow summary", className="qcchem-ai-workspace-page__ticket-meta"),
            html.Div(
                className="qcchem-ai-workspace-page__ticket-grid",
                children=[
                    html.Div([html.Span("Workflow"), html.Strong(str(workflow["workflow_name"]))]),
                    html.Div([html.Span("Status"), html.Strong(str(workflow["status"]))]),
                    html.Div([html.Span("Acceptance"), html.Strong(str(workflow["accepted_label"]))]),
                    html.Div(
                        [
                            html.Span("Steps"),
                            html.Strong(
                                f"{workflow['completed_steps']} completed / "
                                f"{workflow['failed_steps']} failed / "
                                f"{workflow['generated_steps']} generated"
                            ),
                        ]
                    ),
                    html.Div([html.Span("Workflow action"), html.Strong(str(workflow["recommended_action"]))]),
                ],
            ),
        ]
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
                    html.Div([html.Span("Review action"), html.Strong(review_action_text)]),
                ],
            ),
            html.Div(
                className="qcchem-ai-workspace-page__ticket-grid",
                children=[
                    html.Div([html.Span("Evidence scope"), html.Strong(str(record.get("evidence_scope") or "Artifact evidence not scoped"))]),
                    html.Div([html.Span("Evidence claim"), html.Strong(str(evidence.get("primary_scientific_claim") or "n/a"))]),
                ],
            ),
            *workflow_children,
            html.P("Review artifacts", className="qcchem-ai-workspace-page__ticket-meta"),
            _delivery_artifact_list(artifact_rows),
            html.P("Limitation notes", className="qcchem-ai-workspace-page__ticket-meta"),
            html.P("; ".join(str(note) for note in limitation_notes) or "No limitation notes recorded.", className="qcchem-card-note qcchem-card-note--compact"),
            *return_note_children,
            html.P(str(record.get("task_id", "")), className="qcchem-card-note qcchem-card-note--compact"),
        ],
    )


def build_lane_children(
    title: str,
    note: str,
    tickets: list[dict[str, object]],
    *,
    lane: str,
    workspace_root_path: Path | None = None,
) -> list[object]:
    tickets_dir = (workspace_root_path / "tickets") if workspace_root_path is not None else Path("artifacts/ai_workspace/tickets")
    latest_ticket = tickets[-1] if tickets else None
    empty_message = (
        f"0 persisted {title.lower()} tickets found under {tickets_dir}. "
        f"{LANE_NEXT_ACTIONS.get(lane, 'Create or move a ticket to populate this lane.')}"
    )
    return [
        html.P("Task Lane", className="qcchem-panel__eyebrow"),
        html.H2(title, className="qcchem-panel__title"),
        html.P(note, className="qcchem-panel__note"),
        html.Div(
            className="qcchem-ai-workspace-page__state-card",
            children=[
                html.Div(
                    className="qcchem-ai-workspace-page__ticket-grid",
                    children=[
                        html.Div([html.Span("Records"), html.Strong(str(len(tickets)))]),
                        html.Div([html.Span("Latest"), html.Strong(_compact_record_label(latest_ticket, fallback="none"))]),
                        html.Div([html.Span("Source"), html.Strong(str(tickets_dir))]),
                    ],
                ),
            ],
        ),
        html.Div(
            [build_ticket_card(ticket) for ticket in tickets] or [html.Div(empty_message, className="qcchem-ai-workspace-page__empty-state")],
            className="qcchem-ai-workspace-page__lane-stack",
        ),
    ]


def _lane(
    section_id: str,
    title: str,
    note: str,
    tickets: list[dict[str, object]],
    *,
    lane: str,
    workspace_root_path: Path,
) -> html.Section:
    return html.Section(
        id=section_id,
        className="qcchem-ai-workspace-page__lane",
        children=build_lane_children(title, note, tickets, lane=lane, workspace_root_path=workspace_root_path),
    )


def build_delivery_history_children(deliveries: list[dict[str, object]], *, workspace_root_path: Path | None = None) -> list[object]:
    deliveries_dir = (workspace_root_path / "deliveries") if workspace_root_path is not None else Path("artifacts/ai_workspace/deliveries")
    latest_delivery = deliveries[-1] if deliveries else None
    review_statuses: dict[str, int] = {}
    for delivery in deliveries:
        status = str(delivery.get("review_status") or "pending_review")
        review_statuses[status] = review_statuses.get(status, 0) + 1
    status_text = ", ".join(f"{status}={count}" for status, count in sorted(review_statuses.items())) or "none"
    empty_message = (
        f"0 persisted delivery records found under {deliveries_dir}. "
        "Run an accepted ticket or submit a delivery to create a durable handoff."
    )
    return [
        html.Div(
            className="qcchem-ai-workspace-page__state-card",
            children=[
                html.Div(
                    className="qcchem-ai-workspace-page__ticket-grid",
                    children=[
                        html.Div([html.Span("Records"), html.Strong(str(len(deliveries)))]),
                        html.Div([html.Span("Latest"), html.Strong(_compact_record_label(latest_delivery, fallback="none"))]),
                        html.Div([html.Span("Review"), html.Strong(status_text)]),
                        html.Div([html.Span("Source"), html.Strong(str(deliveries_dir))]),
                    ],
                )
            ],
        ),
        html.Div(
            [build_delivery_card(delivery) for delivery in deliveries]
            or [html.Div(empty_message, className="qcchem-ai-workspace-page__empty-state")],
            className="qcchem-ai-workspace-page__delivery-stack",
        ),
    ]


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
                        lane=AI_WORKSPACE_TICKET_LANE_INBOX,
                        workspace_root_path=root,
                    ),
                    _lane(
                        "qcchem-ai-task-running",
                        "Running",
                        "Active work stays separate from drafts so the shell can show motion without implying persistence.",
                        running,
                        lane=AI_WORKSPACE_TICKET_LANE_RUNNING,
                        workspace_root_path=root,
                    ),
                    _lane(
                        "qcchem-ai-task-submitted",
                        "Submitted",
                        "Submitted tickets preserve the handoff boundary between analysis and delivery.",
                        submitted,
                        lane=AI_WORKSPACE_TICKET_LANE_SUBMITTED,
                        workspace_root_path=root,
                    ),
                    _lane(
                        "qcchem-ai-task-completed",
                        "Completed",
                        "Completed tickets become reportable outcomes once their delivery records are available.",
                        completed,
                        lane=AI_WORKSPACE_TICKET_LANE_COMPLETED,
                        workspace_root_path=root,
                    ),
                    _lane(
                        "qcchem-ai-task-returned",
                        "Returned",
                        "Returned tasks preserve scope corrections and cautionary notes instead of hiding them.",
                        returned,
                        lane=AI_WORKSPACE_TICKET_LANE_RETURNED,
                        workspace_root_path=root,
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
                        className="qcchem-ai-workspace-page__delivery-history-body",
                        children=build_delivery_history_children(deliveries, workspace_root_path=root),
                    ),
                ],
            ),
        ],
    )
