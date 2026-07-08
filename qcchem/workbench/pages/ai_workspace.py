from __future__ import annotations

from pathlib import Path

from dash import dcc, html

from qcchem.core.ai_workspace import (
    AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_LANE_RETURNED,
    AI_WORKSPACE_TICKET_LANE_RUNNING,
    AI_WORKSPACE_TICKET_LANE_SUBMITTED,
)
from qcchem.workflow.ai_store import list_delivery_records, list_ticket_records, workspace_root
from qcchem.workflow.ai_workspace import review_delivery_record
from qcchem.workbench.components.cards import callout_card, metric_card, status_card
from qcchem.workbench.evidence_console import format_action_label


LANE_NEXT_ACTIONS = {
    AI_WORKSPACE_TICKET_LANE_INBOX: "Draft or accept a ticket before execution.",
    AI_WORKSPACE_TICKET_LANE_RUNNING: "Review active tickets before starting another run.",
    AI_WORKSPACE_TICKET_LANE_SUBMITTED: "Inspect delivery records before closing the handoff.",
    AI_WORKSPACE_TICKET_LANE_COMPLETED: "Use completed tickets as the evidence-backed outcome list.",
    AI_WORKSPACE_TICKET_LANE_RETURNED: "Resolve returned scope notes before retrying execution.",
}

DELIVERY_FILTER_ALL = "__all__"
DELIVERY_REVIEW_ACTION_TYPE = "qcchem-ai-delivery-review-action"
DELIVERY_REVIEWER_TYPE = "qcchem-ai-delivery-reviewer"
DELIVERY_RETURN_NOTES_TYPE = "qcchem-ai-delivery-return-notes"


def _compact_record_label(record: dict[str, object] | None, *, fallback: str) -> str:
    if not record:
        return fallback
    record_id = str(record.get("task_id") or record.get("delivery_id") or "").strip()
    title = str(record.get("title") or record.get("summary") or "").strip()
    if record_id and title:
        return f"{record_id} - {title}"
    return record_id or title or fallback


def _compact_delivery_label(record: dict[str, object] | None, *, fallback: str) -> str:
    if not record:
        return fallback
    record_id = _compact_string(record.get("delivery_id") or record.get("task_id"))
    summary = _compact_string(record.get("summary"))
    if record_id and summary:
        return f"{record_id} - {summary}"
    return record_id or summary or fallback


def _delivery_record_path(
    record: dict[str, object],
    *,
    workspace_root_path: Path | None = None,
) -> str:
    existing = _compact_string(record.get("delivery_record"))
    if existing:
        return existing
    delivery_id = _compact_string(record.get("delivery_id"))
    if delivery_id and workspace_root_path is not None:
        return str((workspace_root_path / "deliveries" / f"{delivery_id}.json").resolve())
    return ""


def _resolve_workbench_delivery_path(delivery_record_path: str, workspace_root_path: Path) -> Path:
    deliveries_dir = (workspace_root_path / "deliveries").expanduser().resolve()
    raw_path = Path(delivery_record_path).expanduser()
    resolved = raw_path if raw_path.is_absolute() else (Path.cwd() / raw_path)
    resolved = resolved.resolve()
    if not resolved.is_relative_to(deliveries_dir):
        raise ValueError("Workbench delivery review path must stay under the current AI workspace deliveries directory.")
    if resolved.suffix != ".json":
        raise ValueError("Workbench delivery review path must point to a JSON delivery record.")
    return resolved


def handle_delivery_review_action(
    *,
    delivery_record_path: str,
    review_status: str,
    return_notes: str | None,
    reviewed_by: str | None,
    workspace_root_path: Path,
) -> dict[str, object]:
    delivery_path = _resolve_workbench_delivery_path(delivery_record_path, workspace_root_path)
    return review_delivery_record(
        delivery_path,
        review_status=review_status,
        return_notes=return_notes,
        reviewed_by=reviewed_by or "workbench-user",
        review_source="workbench",
    )


def _linked_return_delivery_for_ticket(
    record: dict[str, object],
    deliveries: list[dict[str, object]],
) -> dict[str, object] | None:
    task_id = _compact_string(record.get("task_id"))
    if not task_id:
        return None
    matches = [delivery for delivery in deliveries if _compact_string(delivery.get("task_id")) == task_id]
    if not matches:
        return None
    returned_matches = [
        delivery
        for delivery in matches
        if _compact_string(delivery.get("return_notes"))
        or _compact_string(delivery.get("review_status")).lower() in {"returned", "needs_revision", "changes_requested"}
    ]
    return (returned_matches or matches)[-1]


def _ticket_return_handoff_children(
    record: dict[str, object],
    linked_return_delivery: dict[str, object] | None,
) -> list[object]:
    return_notes = _compact_string(record.get("return_notes"))
    if linked_return_delivery is not None and not return_notes:
        return_notes = _compact_string(linked_return_delivery.get("return_notes"))
    if not return_notes and linked_return_delivery is None:
        return []
    delivery_label = _compact_delivery_label(linked_return_delivery, fallback="none")
    review_status = (
        _compact_string((linked_return_delivery or {}).get("review_status"))
        or _compact_string(record.get("status"))
        or "returned"
    )
    raw_evidence = (linked_return_delivery or {}).get("evidence_summary") or {}
    evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
    outputs = _string_list((linked_return_delivery or {}).get("linked_outputs"))
    workflow = _workflow_delivery_summary(linked_return_delivery or {})
    review_action = _delivery_review_action(linked_return_delivery or record, evidence, workflow, outputs)
    return [
        html.P("Return handoff", className="qcchem-ai-workspace-page__ticket-meta"),
        html.Div(
            className="qcchem-ai-workspace-page__ticket-grid",
            children=[
                html.Div([html.Span("Linked delivery"), html.Strong(delivery_label)]),
                html.Div([html.Span("Review"), html.Strong(review_status)]),
                html.Div([html.Span("Review action"), html.Strong(_action_text(review_action))]),
            ],
        ),
        html.P(return_notes or "No return notes recorded.", className="qcchem-card-note qcchem-card-note--compact"),
    ]


def build_ticket_card(
    record: dict[str, object],
    *,
    linked_return_delivery: dict[str, object] | None = None,
) -> html.Div:
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
            *_ticket_return_handoff_children(record, linked_return_delivery),
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


def delivery_filter_options(
    deliveries: list[dict[str, object]],
    *,
    field: str,
    all_label: str,
) -> list[dict[str, str]]:
    values = sorted({_compact_string(record.get(field)) for record in deliveries if _compact_string(record.get(field))})
    return [{"label": all_label, "value": DELIVERY_FILTER_ALL}, *[{"label": value, "value": value} for value in values]]


def filter_delivery_records(
    deliveries: list[dict[str, object]],
    *,
    review_status: str | None = None,
    delivery_kind: str | None = None,
) -> list[dict[str, object]]:
    review_filter = _compact_string(review_status)
    kind_filter = _compact_string(delivery_kind)
    if review_filter == DELIVERY_FILTER_ALL:
        review_filter = ""
    if kind_filter == DELIVERY_FILTER_ALL:
        kind_filter = ""
    filtered: list[dict[str, object]] = []
    for delivery in deliveries:
        if review_filter and _compact_string(delivery.get("review_status")) != review_filter:
            continue
        if kind_filter and _compact_string(delivery.get("delivery_kind")) != kind_filter:
            continue
        filtered.append(delivery)
    return filtered


def build_delivery_handoff_summary(
    deliveries: list[dict[str, object]],
    *,
    workspace_root_path: Path | None = None,
    handoff_limit: int = 5,
) -> dict[str, object]:
    deliveries_dir = (workspace_root_path / "deliveries") if workspace_root_path is not None else Path("artifacts/ai_workspace/deliveries")
    review_statuses: dict[str, int] = {}
    delivery_kinds: dict[str, int] = {}
    handoffs: list[dict[str, object]] = []
    total_output_paths = 0
    return_note_count = 0
    for delivery in deliveries:
        raw_evidence = delivery.get("evidence_summary") or delivery.get("linked_evidence_summary") or {}
        evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
        outputs = _string_list(delivery.get("linked_outputs"))
        workflow = _workflow_delivery_summary(delivery)
        review_status = _compact_string(delivery.get("review_status")) or "pending_review"
        delivery_kind = _compact_string(delivery.get("delivery_kind")) or "delivery"
        review_statuses[review_status] = review_statuses.get(review_status, 0) + 1
        delivery_kinds[delivery_kind] = delivery_kinds.get(delivery_kind, 0) + 1
        total_output_paths += len(outputs)
        return_notes = _compact_string(delivery.get("return_notes"))
        if return_notes:
            return_note_count += 1
        if len(handoffs) < handoff_limit:
            artifact_rows = _delivery_artifact_rows(delivery, workflow, outputs)
            handoff = {
                "delivery_id": delivery.get("delivery_id"),
                "task_id": delivery.get("task_id"),
                "summary": delivery.get("summary"),
                "delivery_kind": delivery_kind,
                "review_status": review_status,
                "review_action": _delivery_review_action(delivery, evidence, workflow, outputs),
                "artifact_count": len(artifact_rows),
                "artifacts": [
                    {"label": label, "path": path}
                    for label, path in artifact_rows[:handoff_limit]
                ],
                "artifacts_truncated": len(artifact_rows) > handoff_limit,
                "return_notes": return_notes or None,
            }
            for field in ("reviewed_at", "reviewed_by", "review_source"):
                value = _compact_string(delivery.get(field))
                if value:
                    handoff[field] = value
            handoffs.append(handoff)
    latest_delivery = deliveries[-1] if deliveries else None
    return {
        "available": bool(deliveries),
        "source_path": str(deliveries_dir),
        "delivery_count": len(deliveries),
        "review_status_counts": review_statuses,
        "delivery_kind_counts": delivery_kinds,
        "linked_output_path_count": total_output_paths,
        "return_note_count": return_note_count,
        "latest": _compact_record_label(latest_delivery, fallback="none"),
        "handoffs": handoffs,
        "handoffs_truncated": len(deliveries) > handoff_limit,
    }


def _delivery_review_controls(record: dict[str, object], delivery_record_path: str) -> list[object]:
    if not delivery_record_path:
        return []
    current_reviewer = _compact_string(record.get("reviewed_by")) or "workbench-user"
    current_notes = _compact_string(record.get("return_notes"))
    return [
        html.P("Review decision", className="qcchem-ai-workspace-page__ticket-meta"),
        html.Div(
            className="qcchem-ai-workspace-page__review-controls",
            children=[
                html.Div(
                    className="qcchem-ai-workspace-page__review-field",
                    children=[
                        html.Label("Reviewer"),
                        dcc.Input(
                            id={
                                "type": DELIVERY_REVIEWER_TYPE,
                                "delivery_record": delivery_record_path,
                            },
                            className="qcchem-ai-workspace-page__review-input",
                            type="text",
                            value=current_reviewer,
                            debounce=True,
                        ),
                    ],
                ),
                html.Div(
                    className="qcchem-ai-workspace-page__review-field qcchem-ai-workspace-page__review-field--wide",
                    children=[
                        html.Label("Return notes"),
                        dcc.Textarea(
                            id={
                                "type": DELIVERY_RETURN_NOTES_TYPE,
                                "delivery_record": delivery_record_path,
                            },
                            className="qcchem-ai-workspace-page__review-textarea",
                            value=current_notes,
                        ),
                    ],
                ),
                html.Div(
                    className="qcchem-ai-workspace-page__review-actions",
                    children=[
                        html.Button(
                            "Accept",
                            id={
                                "type": DELIVERY_REVIEW_ACTION_TYPE,
                                "delivery_record": delivery_record_path,
                                "review_status": "accepted",
                            },
                            className="qcchem-ai-workspace-page__review-button",
                            type="button",
                        ),
                        html.Button(
                            "Return",
                            id={
                                "type": DELIVERY_REVIEW_ACTION_TYPE,
                                "delivery_record": delivery_record_path,
                                "review_status": "returned",
                            },
                            className="qcchem-ai-workspace-page__review-button qcchem-ai-workspace-page__review-button--return",
                            type="button",
                        ),
                    ],
                ),
            ],
        ),
    ]


def build_delivery_card(
    record: dict[str, object],
    *,
    workspace_root_path: Path | None = None,
) -> html.Div:
    raw_evidence = record.get("evidence_summary") or record.get("linked_evidence_summary") or {}
    evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
    outputs = _string_list(record.get("linked_outputs"))
    limitation_notes = _string_list(record.get("limitation_notes"))
    recommended_action = record.get("recommended_action") or evidence.get("recommended_action") or "n/a"
    recommended_action_text = _action_text(recommended_action)
    workflow = _workflow_delivery_summary(record)
    review_action_text = _action_text(_delivery_review_action(record, evidence, workflow, outputs))
    artifact_rows = _delivery_artifact_rows(record, workflow, outputs)
    reviewed_at = _compact_string(record.get("reviewed_at")) or "not reviewed"
    reviewed_by = _compact_string(record.get("reviewed_by")) or "n/a"
    review_source = _compact_string(record.get("review_source")) or "n/a"
    delivery_record_path = _delivery_record_path(record, workspace_root_path=workspace_root_path)
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
                    html.Div([html.Span("Reviewed"), html.Strong(reviewed_at)]),
                    html.Div([html.Span("Reviewer"), html.Strong(f"{reviewed_by} via {review_source}")]),
                ],
            ),
            *workflow_children,
            html.P("Review artifacts", className="qcchem-ai-workspace-page__ticket-meta"),
            _delivery_artifact_list(artifact_rows),
            html.P("Limitation notes", className="qcchem-ai-workspace-page__ticket-meta"),
            html.P("; ".join(str(note) for note in limitation_notes) or "No limitation notes recorded.", className="qcchem-card-note qcchem-card-note--compact"),
            *return_note_children,
            *_delivery_review_controls(record, delivery_record_path),
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
    deliveries: list[dict[str, object]] | None = None,
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
            [
                build_ticket_card(
                    ticket,
                    linked_return_delivery=_linked_return_delivery_for_ticket(ticket, deliveries or []),
                )
                for ticket in tickets
            ]
            or [html.Div(empty_message, className="qcchem-ai-workspace-page__empty-state")],
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
    deliveries: list[dict[str, object]] | None = None,
) -> html.Section:
    return html.Section(
        id=section_id,
        className="qcchem-ai-workspace-page__lane",
        children=build_lane_children(
            title,
            note,
            tickets,
            lane=lane,
            workspace_root_path=workspace_root_path,
            deliveries=deliveries,
        ),
    )


def build_delivery_filter_controls(deliveries: list[dict[str, object]]) -> html.Div:
    return html.Div(
        className="qcchem-ai-workspace-page__filter-bar",
        children=[
            html.Div(
                className="qcchem-ai-workspace-page__filter-control",
                children=[
                    html.Label("Review status", htmlFor="qcchem-ai-delivery-review-filter"),
                    dcc.Dropdown(
                        id="qcchem-ai-delivery-review-filter",
                        options=delivery_filter_options(
                            deliveries,
                            field="review_status",
                            all_label="All review states",
                        ),
                        value=DELIVERY_FILTER_ALL,
                        clearable=False,
                        searchable=False,
                    ),
                ],
            ),
            html.Div(
                className="qcchem-ai-workspace-page__filter-control",
                children=[
                    html.Label("Delivery kind", htmlFor="qcchem-ai-delivery-kind-filter"),
                    dcc.Dropdown(
                        id="qcchem-ai-delivery-kind-filter",
                        options=delivery_filter_options(
                            deliveries,
                            field="delivery_kind",
                            all_label="All delivery kinds",
                        ),
                        value=DELIVERY_FILTER_ALL,
                        clearable=False,
                        searchable=False,
                    ),
                ],
            ),
        ],
    )


def build_delivery_history_children(
    deliveries: list[dict[str, object]],
    *,
    workspace_root_path: Path | None = None,
    review_status_filter: str | None = None,
    delivery_kind_filter: str | None = None,
) -> list[object]:
    deliveries_dir = (workspace_root_path / "deliveries") if workspace_root_path is not None else Path("artifacts/ai_workspace/deliveries")
    filtered_deliveries = filter_delivery_records(
        deliveries,
        review_status=review_status_filter,
        delivery_kind=delivery_kind_filter,
    )
    summary = build_delivery_handoff_summary(deliveries, workspace_root_path=workspace_root_path)
    latest_delivery = filtered_deliveries[-1] if filtered_deliveries else None
    review_statuses = summary["review_status_counts"] if isinstance(summary["review_status_counts"], dict) else {}
    delivery_kinds = summary["delivery_kind_counts"] if isinstance(summary["delivery_kind_counts"], dict) else {}
    status_text = ", ".join(f"{status}={count}" for status, count in sorted(review_statuses.items())) or "none"
    kind_text = ", ".join(f"{kind}={count}" for kind, count in sorted(delivery_kinds.items())) or "none"
    active_filters = []
    if _compact_string(review_status_filter) not in {"", DELIVERY_FILTER_ALL}:
        active_filters.append(f"review={review_status_filter}")
    if _compact_string(delivery_kind_filter) not in {"", DELIVERY_FILTER_ALL}:
        active_filters.append(f"kind={delivery_kind_filter}")
    filter_text = ", ".join(active_filters) if active_filters else "all"
    empty_message = (
        f"0 persisted delivery records found under {deliveries_dir}. "
        "Run an accepted ticket or submit a delivery to create a durable handoff."
    )
    if deliveries and not filtered_deliveries:
        empty_message = f"0 delivery records match filters {filter_text} under {deliveries_dir}."
    return [
        html.Div(
            className="qcchem-ai-workspace-page__state-card",
            children=[
                html.Div(
                    className="qcchem-ai-workspace-page__ticket-grid",
                    children=[
                        html.Div([html.Span("Records"), html.Strong(f"{len(filtered_deliveries)} / {len(deliveries)}")]),
                        html.Div([html.Span("Latest"), html.Strong(_compact_record_label(latest_delivery, fallback="none"))]),
                        html.Div([html.Span("Review"), html.Strong(status_text)]),
                        html.Div([html.Span("Kinds"), html.Strong(kind_text)]),
                        html.Div([html.Span("Filter"), html.Strong(filter_text)]),
                        html.Div([html.Span("Source"), html.Strong(str(deliveries_dir))]),
                    ],
                )
            ],
        ),
        html.Div(
            [
                build_delivery_card(delivery, workspace_root_path=workspace_root_path)
                for delivery in filtered_deliveries
            ]
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
                        deliveries=deliveries,
                    ),
                    _lane(
                        "qcchem-ai-task-running",
                        "Running",
                        "Active work stays separate from drafts so the shell can show motion without implying persistence.",
                        running,
                        lane=AI_WORKSPACE_TICKET_LANE_RUNNING,
                        workspace_root_path=root,
                        deliveries=deliveries,
                    ),
                    _lane(
                        "qcchem-ai-task-submitted",
                        "Submitted",
                        "Submitted tickets preserve the handoff boundary between analysis and delivery.",
                        submitted,
                        lane=AI_WORKSPACE_TICKET_LANE_SUBMITTED,
                        workspace_root_path=root,
                        deliveries=deliveries,
                    ),
                    _lane(
                        "qcchem-ai-task-completed",
                        "Completed",
                        "Completed tickets become reportable outcomes once their delivery records are available.",
                        completed,
                        lane=AI_WORKSPACE_TICKET_LANE_COMPLETED,
                        workspace_root_path=root,
                        deliveries=deliveries,
                    ),
                    _lane(
                        "qcchem-ai-task-returned",
                        "Returned",
                        "Returned tasks preserve scope corrections and cautionary notes instead of hiding them.",
                        returned,
                        lane=AI_WORKSPACE_TICKET_LANE_RETURNED,
                        workspace_root_path=root,
                        deliveries=deliveries,
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-ai-workspace-page__delivery-history",
                children=[
                    dcc.Store(id="qcchem-ai-delivery-review-state", data=None),
                    html.P("Delivery Surface", className="qcchem-card-eyebrow"),
                    html.H2("Delivery History", className="qcchem-card-title"),
                    html.P(
                        "Deliveries are the durable handoff object: summary, linked outputs, review status, and the evidence posture that produced them.",
                        className="qcchem-panel__note",
                    ),
                    html.Div(
                        id="qcchem-ai-delivery-review-feedback",
                        className="qcchem-ai-workspace-page__review-feedback",
                        children=[],
                    ),
                    build_delivery_filter_controls(deliveries),
                    html.Div(
                        id="qcchem-ai-delivery-history",
                        className="qcchem-ai-workspace-page__delivery-history-body",
                        children=build_delivery_history_children(deliveries, workspace_root_path=root),
                    ),
                ],
            ),
        ],
    )
