from __future__ import annotations

from dash import dcc, html


def _status_chip(label: str, tone: str) -> html.Span:
    return html.Span(label, className=f"qcchem-ai-chip qcchem-ai-chip--{tone}")


def build_floating_assistant() -> html.Div:
    return html.Div(
        id="qcchem-ai-assistant-window",
        className="qcchem-ai-assistant-window",
        children=[
            dcc.Store(
                id="qcchem-ai-shell-ui-state",
                data={"minimized": False, "provider_drawer_open": False},
            ),
            html.Div(
                className="qcchem-ai-assistant-window__header",
                children=[
                    html.Div(
                        children=[
                            html.P("Workbench Copilot", className="qcchem-ai-assistant-window__eyebrow"),
                            html.H2("Research Copilot", className="qcchem-ai-assistant-window__title"),
                        ]
                    ),
                    html.Div(
                        className="qcchem-ai-assistant-window__controls",
                        children=[
                            html.Button(
                                "Providers",
                                id="qcchem-ai-provider-toggle",
                                className="qcchem-ai-assistant-window__control",
                                type="button",
                            ),
                            html.Button(
                                "Minimize",
                                id="qcchem-ai-assistant-minimize",
                                className="qcchem-ai-assistant-window__control",
                                type="button",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="qcchem-ai-assistant-body",
                className="qcchem-ai-assistant-window__body",
                children=[
                    html.Div(
                        className="qcchem-ai-assistant-window__status-row",
                        children=[
                            _status_chip("Plan first", "informational"),
                            _status_chip("Execution guarded", "exploratory"),
                            _status_chip("Workbench shell", "validated"),
                        ],
                    ),
                    dcc.Textarea(
                        id="qcchem-ai-request-input",
                        className="qcchem-ai-assistant-window__input",
                        placeholder="Ask a research question or sketch a task ticket before execution.",
                    ),
                    html.Div(
                        id="qcchem-ai-current-ticket-preview",
                        className="qcchem-ai-assistant-window__ticket-preview",
                        children=[
                            html.P("Draft Ticket Preview", className="qcchem-ai-assistant-window__preview-title"),
                            html.P(
                                "No persisted draft yet. This shell is ready for Task 6 wiring.",
                                className="qcchem-ai-assistant-window__preview-body",
                            ),
                        ],
                    ),
                    html.Div(
                        className="qcchem-ai-assistant-window__actions",
                        children=[
                            html.Button(
                                "Draft Ticket",
                                id="qcchem-ai-draft-ticket",
                                className="qcchem-ai-assistant-window__action",
                                type="button",
                            ),
                        ],
                    ),
                ],
            ),
            html.Aside(
                id="qcchem-ai-provider-drawer",
                className="qcchem-ai-provider-drawer",
                hidden=True,
                children=[
                    html.Div(
                        className="qcchem-ai-provider-drawer__header",
                        children=[
                            html.P("Provider Drawer", className="qcchem-ai-provider-drawer__eyebrow"),
                            html.H3("Provider Settings", className="qcchem-ai-provider-drawer__title"),
                            html.P(
                                "Placeholder controls only for now. Real state binding lands in the next task.",
                                className="qcchem-ai-provider-drawer__note",
                            ),
                        ],
                    ),
                    html.Div(
                        className="qcchem-ai-provider-drawer__fields",
                        children=[
                            dcc.Input(
                                id="qcchem-ai-provider-base-url",
                                className="qcchem-ai-provider-drawer__input",
                                placeholder="base_url",
                                type="text",
                            ),
                            dcc.Input(
                                id="qcchem-ai-provider-model",
                                className="qcchem-ai-provider-drawer__input",
                                placeholder="model",
                                type="text",
                            ),
                            dcc.Input(
                                id="qcchem-ai-provider-key-ref",
                                className="qcchem-ai-provider-drawer__input",
                                placeholder="api_key_ref",
                                type="text",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
