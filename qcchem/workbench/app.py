from __future__ import annotations

from pathlib import Path

import dash
from dash import Dash, Input, Output, State, ctx, dcc, html

from qcchem.workbench.components.cards import callout_card
from qcchem.workbench.components.layout import build_shell, ordered_pages, page_focus
from qcchem.workbench.pages._registry import build_validation_pages, ensure_pages_registered
from qcchem.core.ai_workspace import (
    AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_LANE_RETURNED,
    AI_WORKSPACE_TICKET_LANE_RUNNING,
    AI_WORKSPACE_TICKET_LANE_SUBMITTED,
)
from qcchem.workflow.ai_store import list_ticket_records, workspace_root
from qcchem.workflow.ai_workspace import handle_ticket_editor_action

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def build_validation_layout() -> html.Div:
    from qcchem.workbench.pages.ai_workspace import layout as ai_workspace_layout

    return html.Div(
        [
            dcc.Location(id="qcchem-url"),
            build_shell(),
            ai_workspace_layout(),
            *build_validation_pages(),
        ]
    )


def create_app() -> Dash:
    app = Dash(
        __name__,
        use_pages=True,
        pages_folder="",
        assets_folder=str(ASSETS_DIR),
        suppress_callback_exceptions=True,
        title="QCchem Visual Workbench",
    )
    ensure_pages_registered()
    app.page_registry = dash.page_registry
    app.layout = build_shell
    app.validation_layout = build_validation_layout

    nav_pages = ordered_pages()
    nav_outputs = [Output(f"qcchem-nav-link--{index}", "className") for index, _page in enumerate(nav_pages)]

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

    def _lane_children(title: str, note: str, tickets: list[dict[str, object]]):
        return [
            html.P("Task Lane", className="qcchem-panel__eyebrow"),
            html.H2(title, className="qcchem-panel__title"),
            html.P(note, className="qcchem-panel__note"),
            html.Div([_ticket_card(ticket) for ticket in tickets], className="qcchem-ai-workspace-page__placeholder"),
        ]

    def _current_workspace_root() -> Path:
        return workspace_root(Path.cwd(), create=False)

    @app.callback(
        Output("qcchem-context-current-route", "children"),
        Output("qcchem-context-current-summary", "children"),
        Output("qcchem-rail-page-title", "children"),
        Output("qcchem-rail-page-note", "children"),
        Output("qcchem-rail-callout", "children"),
        Output("qcchem-rail-checklist", "children"),
        *nav_outputs,
        Input("qcchem-shell-location", "pathname"),
    )
    def _update_shell_focus(pathname: str | None):
        active_path = pathname or "/overview"
        focus = page_focus(active_path)
        nav_classes = [
            "qcchem-research-navigator__link qcchem-research-navigator__link--active"
            if page.get("path") == active_path
            else "qcchem-research-navigator__link qcchem-research-navigator__link--inactive"
            for page in nav_pages
        ]
        rail_callout = callout_card(str(focus["callout_title"]), str(focus["callout_body"]))
        checklist = [
            html.Div(className="qcchem-rail-checklist__item", children=[html.Span(label), html.Strong(value)])
            for label, value in focus["checklist"]
        ]
        return (
            focus["route_label"],
            focus["summary"],
            focus["rail_title"],
            focus["rail_note"],
            [rail_callout],
            checklist,
            *nav_classes,
        )

    @app.callback(
        Output("qcchem-ai-shell-ui-state", "data"),
        Input("qcchem-ai-assistant-minimize", "n_clicks"),
        Input("qcchem-ai-provider-toggle", "n_clicks"),
        State("qcchem-ai-shell-ui-state", "data"),
    )
    def _update_ai_shell_state(
        _minimize_clicks: int | None,
        _provider_clicks: int | None,
        current_state: dict[str, object] | None,
    ) -> dict[str, object]:
        state = {
            "minimized": bool((current_state or {}).get("minimized", False)),
            "provider_drawer_open": bool((current_state or {}).get("provider_drawer_open", False)),
        }
        if ctx.triggered_id == "qcchem-ai-assistant-minimize":
            state["minimized"] = not bool(state["minimized"])
        elif ctx.triggered_id == "qcchem-ai-provider-toggle":
            state["provider_drawer_open"] = not bool(state["provider_drawer_open"])
        return state

    @app.callback(
        Output("qcchem-ai-assistant-body", "hidden"),
        Input("qcchem-ai-shell-ui-state", "data"),
    )
    def _render_ai_assistant_body_visibility(state: dict[str, object] | None) -> bool:
        return bool((state or {}).get("minimized", False))

    @app.callback(
        Output("qcchem-ai-provider-drawer", "hidden"),
        Input("qcchem-ai-shell-ui-state", "data"),
    )
    def _render_ai_provider_drawer_visibility(state: dict[str, object] | None) -> bool:
        return not bool((state or {}).get("provider_drawer_open", False))

    @app.callback(
        Output("qcchem-ai-current-ticket-preview", "children"),
        Input("qcchem-ai-current-ticket-record", "data"),
        Input("qcchem-ai-task-type", "value"),
        Input("qcchem-ai-title-input", "value"),
        Input("qcchem-ai-request-input", "value"),
        Input("qcchem-ai-linked-artifacts-input", "value"),
        Input("qcchem-ai-plan-summary-input", "value"),
        Input("qcchem-ai-expected-outputs-input", "value"),
        Input("qcchem-ai-risk-notes-input", "value"),
    )
    def _render_ticket_preview(
        current_ticket_record: dict[str, object] | None,
        task_type: str | None,
        title: str | None,
        request_text: str | None,
        linked_artifacts_text: str | None,
        plan_summary: str | None,
        expected_outputs_text: str | None,
        risk_notes_text: str | None,
    ):
        if current_ticket_record:
            preview_body = (
                f"{current_ticket_record.get('task_type', 'ticket')} | "
                f"{current_ticket_record.get('title', 'Untitled Task')} | "
                f"status: {current_ticket_record.get('status', 'draft')}"
            )
        else:
            summary_bits = [
                part
                for part in [
                    f"type={task_type}" if task_type else "",
                    f"title={title}" if title else "",
                    f"request={request_text[:80]}" if request_text else "",
                    f"artifacts={linked_artifacts_text.splitlines()[0]}" if linked_artifacts_text else "",
                    f"plan={plan_summary[:80]}" if plan_summary else "",
                    f"outputs={expected_outputs_text.splitlines()[0]}" if expected_outputs_text else "",
                    f"risk={risk_notes_text.splitlines()[0]}" if risk_notes_text else "",
                ]
                if part
            ]
            preview_body = " | ".join(summary_bits) if summary_bits else "Fill the editor to stage a ticket."
        return html.Div(
            children=[
                html.P("Draft Ticket Preview", className="qcchem-ai-assistant-window__preview-title"),
                html.P(preview_body, className="qcchem-ai-assistant-window__preview-body"),
            ],
        )

    @app.callback(
        Output("qcchem-ai-run-guard", "hidden"),
        Output("qcchem-ai-run-guard-body", "children"),
        Input("qcchem-ai-ticket-guard-state", "data"),
    )
    def _render_run_guard(state: dict[str, object] | None):
        normalized = state or {}
        visible = bool(normalized.get("visible", False))
        if not visible:
            return True, []
        risk = normalized.get("risk") or {}
        reasons = risk.get("reasons") or []
        body = [
            html.P(
                normalized.get("message", "High-risk execution requires confirmation."),
                className="qcchem-ai-assistant-window__preview-body",
            )
        ]
        if reasons:
            body.append(html.Ul([html.Li(str(reason)) for reason in reasons]))
        return False, body

    @app.callback(
        Output("qcchem-ai-current-ticket-record", "data"),
        Output("qcchem-ai-current-ticket-path", "data"),
        Output("qcchem-ai-ticket-guard-state", "data"),
        Input("qcchem-ai-draft-ticket", "n_clicks"),
        Input("qcchem-ai-accept-ticket", "n_clicks"),
        Input("qcchem-ai-run-ticket", "n_clicks"),
        Input("qcchem-ai-confirm-run", "n_clicks"),
        Input("qcchem-ai-return-ticket", "n_clicks"),
        State("qcchem-ai-task-type", "value"),
        State("qcchem-ai-title-input", "value"),
        State("qcchem-ai-request-input", "value"),
        State("qcchem-ai-linked-artifacts-input", "value"),
        State("qcchem-ai-plan-summary-input", "value"),
        State("qcchem-ai-expected-outputs-input", "value"),
        State("qcchem-ai-risk-notes-input", "value"),
        State("qcchem-ai-current-ticket-path", "data"),
        State("qcchem-ai-current-ticket-record", "data"),
        State("qcchem-ai-ticket-guard-state", "data"),
        prevent_initial_call=True,
    )
    def _handle_ticket_record_update(
        _draft_clicks: int | None,
        _accept_clicks: int | None,
        _run_clicks: int | None,
        _confirm_run_clicks: int | None,
        _return_clicks: int | None,
        task_type: str | None,
        title: str | None,
        request_text: str | None,
        linked_artifacts_text: str | None,
        plan_summary: str | None,
        expected_outputs_text: str | None,
        risk_notes_text: str | None,
        current_ticket_path: str | None,
        current_ticket_record: dict[str, object] | None,
        guard_state: dict[str, object] | None,
    ):
        action_map = {
            "qcchem-ai-draft-ticket": "draft",
            "qcchem-ai-accept-ticket": "accept",
            "qcchem-ai-run-ticket": "run",
            "qcchem-ai-confirm-run": "confirm_run",
            "qcchem-ai-return-ticket": "return",
        }
        action = action_map.get(ctx.triggered_id)
        if action is None:
            return current_ticket_record, current_ticket_path, guard_state or {"visible": False}
        result = handle_ticket_editor_action(
            action=action,
            task_type=str(task_type or "analysis"),
            title=str(title or ""),
            request_text=str(request_text or ""),
            linked_artifacts_text=str(linked_artifacts_text or ""),
            plan_summary=str(plan_summary or ""),
            expected_outputs_text=str(expected_outputs_text or ""),
            risk_notes_text=str(risk_notes_text or ""),
            current_ticket_path=current_ticket_path,
            current_ticket_record=current_ticket_record,
            guard_state=guard_state,
            workspace_base=Path.cwd(),
        )
        return result["current_ticket_record"], result["current_ticket_path"], result["guard_state"]

    @app.callback(
        Output("qcchem-ai-task-inbox", "children"),
        Input("qcchem-ai-current-ticket-record", "data"),
    )
    def _render_ticket_inbox(_current_ticket_record: dict[str, object] | None):
        root = _current_workspace_root()
        inbox = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX)
        return _lane_children(
            "Inbox",
            "New requests wait here for confirmation before any execution path is allowed.",
            inbox,
        )

    @app.callback(
        Output("qcchem-ai-task-running", "children"),
        Input("qcchem-ai-current-ticket-record", "data"),
    )
    def _render_ticket_running(_current_ticket_record: dict[str, object] | None):
        root = _current_workspace_root()
        running = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RUNNING)
        return _lane_children(
            "Running",
            "Active work stays separate from drafts so the shell can show motion without implying persistence.",
            running,
        )

    @app.callback(
        Output("qcchem-ai-task-submitted", "children"),
        Input("qcchem-ai-current-ticket-record", "data"),
    )
    def _render_ticket_submitted(_current_ticket_record: dict[str, object] | None):
        root = _current_workspace_root()
        submitted = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_SUBMITTED)
        return _lane_children(
            "Submitted",
            "Submitted tickets surface here once review and delivery wiring are connected.",
            submitted,
        )

    @app.callback(
        Output("qcchem-ai-task-completed", "children"),
        Input("qcchem-ai-current-ticket-record", "data"),
    )
    def _render_ticket_completed(_current_ticket_record: dict[str, object] | None):
        root = _current_workspace_root()
        completed = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_COMPLETED)
        return _lane_children(
            "Completed",
            "Completed tickets become reportable outcomes after state-backed delivery records land.",
            completed,
        )

    @app.callback(
        Output("qcchem-ai-task-returned", "children"),
        Input("qcchem-ai-current-ticket-record", "data"),
    )
    def _render_ticket_returned(_current_ticket_record: dict[str, object] | None):
        root = _current_workspace_root()
        returned = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RETURNED)
        return _lane_children(
            "Returned",
            "Returned tasks preserve scope corrections and cautionary notes instead of hiding them.",
            returned,
        )

    return app
