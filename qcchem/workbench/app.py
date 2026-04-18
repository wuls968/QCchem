from __future__ import annotations

from pathlib import Path

import dash
from dash import Dash, Input, Output, State, ctx, dcc, html

from qcchem.workbench.components.cards import callout_card
from qcchem.workbench.components.layout import build_shell, ordered_pages, page_focus
from qcchem.workbench.pages._registry import build_validation_pages, ensure_pages_registered

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
        Input("qcchem-ai-request-input", "value"),
    )
    def _render_ticket_preview(value: str | None):
        preview_body = "No persisted draft yet. This shell is ready for Task 6 wiring."
        if value:
            preview_body = f"Draft task preview: {value[:120]}"
        return html.Div(
            children=[
                html.P("Draft Ticket Preview", className="qcchem-ai-assistant-window__preview-title"),
                html.P(preview_body, className="qcchem-ai-assistant-window__preview-body"),
            ],
        )

    return app
