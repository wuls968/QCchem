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
from qcchem.workflow.ai_store import list_ticket_records, workspace_root


def _ticket_card(record: dict[str, object]) -> html.Div:
    return html.Div(
        className="qcchem-ai-workspace-page__ticket",
        children=[
            html.Strong(str(record.get("title", "Untitled Task"))),
            html.Div(str(record.get("task_type", "unknown"))),
            html.Div(str(record.get("status", "draft"))),
            html.Div(str(record.get("task_id", ""))),
        ],
    )


def _lane(section_id: str, title: str, note: str, tickets: list[dict[str, object]]) -> html.Section:
    return html.Section(
        id=section_id,
        className="qcchem-ai-workspace-page__lane",
        children=[
            html.P("Task Lane", className="qcchem-panel__eyebrow"),
            html.H2(title, className="qcchem-panel__title"),
            html.P(note, className="qcchem-panel__note"),
            html.Div([_ticket_card(ticket) for ticket in tickets], className="qcchem-ai-workspace-page__placeholder"),
        ],
    )


def layout() -> html.Div:
    root = workspace_root(Path.cwd(), create=False)
    return html.Div(
        className="qcchem-page qcchem-ai-workspace-page",
        children=[
            html.Section(
                className="qcchem-ai-workspace-page__hero qcchem-card",
                children=[
                    html.P("Secondary Surface", className="qcchem-card-eyebrow"),
                    html.H1("AI Workspace", className="qcchem-card-title"),
                    html.P(
                        "Stage research requests as bounded tickets, keep provider context visible, and review task flow against persisted workspace state.",
                        className="qcchem-ai-workspace-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-ai-workspace-page__hero-chips",
                        children=[
                            html.Span("Ticket drafting shell", className="qcchem-context-bar__chip"),
                            html.Span("Provider drawer placeholder", className="qcchem-context-bar__chip"),
                            html.Span(
                                f"{len(list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX))} inbox tickets",
                                className="qcchem-context-bar__chip",
                            ),
                        ],
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
                        list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX),
                    ),
                    _lane(
                        "qcchem-ai-task-running",
                        "Running",
                        "Active work stays separate from drafts so the shell can show motion without implying persistence.",
                        list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RUNNING),
                    ),
                    _lane(
                        "qcchem-ai-task-submitted",
                        "Submitted",
                        "Submitted tickets surface here once review and delivery wiring are connected.",
                        list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_SUBMITTED),
                    ),
                    _lane(
                        "qcchem-ai-task-completed",
                        "Completed",
                        "Completed tickets become reportable outcomes after state-backed delivery records land.",
                        list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_COMPLETED),
                    ),
                    _lane(
                        "qcchem-ai-task-returned",
                        "Returned",
                        "Returned tasks preserve scope corrections and cautionary notes instead of hiding them.",
                        list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RETURNED),
                    ),
                ],
            ),
        ],
    )
