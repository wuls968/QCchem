from __future__ import annotations

from dash import dcc, html


def _status_chip(label: str, tone: str) -> html.Span:
    return html.Span(label, className=f"qcchem-ai-chip qcchem-ai-chip--{tone}")


def _field_label(label: str, for_id: str) -> html.Label:
    return html.Label(label, htmlFor=for_id, className="qcchem-ai-assistant-window__field-label")


def build_floating_assistant() -> html.Div:
    return html.Div(
        id="qcchem-ai-assistant-window",
        className="qcchem-ai-assistant-window",
        children=[
            dcc.Store(
                id="qcchem-ai-shell-ui-state",
                data={"minimized": False, "provider_drawer_open": False},
            ),
            dcc.Store(id="qcchem-ai-current-ticket-path", data=None),
            dcc.Store(id="qcchem-ai-current-ticket-record", data=None),
            dcc.Store(id="qcchem-ai-ticket-guard-state", data={"visible": False}),
            html.Div(
                className="qcchem-ai-assistant-window__header",
                children=[
                    html.Div(
                        children=[
                            html.P("Workbench Copilot", className="qcchem-ai-assistant-window__eyebrow"),
                            html.H2("Research Ticket Editor", className="qcchem-ai-assistant-window__title"),
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
                            _status_chip("Draft, then decide", "informational"),
                            _status_chip("Run is guarded for high risk", "exploratory"),
                            _status_chip("State persists to workspace tickets", "validated"),
                        ],
                    ),
                    html.Div(
                        className="qcchem-ai-assistant-window__form",
                        children=[
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Task type", "qcchem-ai-task-type"),
                                    dcc.Dropdown(
                                        id="qcchem-ai-task-type",
                                        options=[
                                            {"label": "Analysis", "value": "analysis"},
                                            {"label": "Execution", "value": "execution"},
                                        ],
                                        value="analysis",
                                        clearable=False,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Title", "qcchem-ai-title-input"),
                                    dcc.Input(
                                        id="qcchem-ai-title-input",
                                        className="qcchem-ai-assistant-window__input",
                                        placeholder="Summarize the task in one line",
                                        type="text",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Task brief", "qcchem-ai-request-input"),
                                    dcc.Textarea(
                                        id="qcchem-ai-request-input",
                                        className="qcchem-ai-assistant-window__input",
                                        placeholder="Describe the request, constraints, and why it matters.",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Linked artifacts", "qcchem-ai-linked-artifacts-input"),
                                    dcc.Textarea(
                                        id="qcchem-ai-linked-artifacts-input",
                                        className="qcchem-ai-assistant-window__input",
                                        placeholder="One artifact path per line",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Plan summary", "qcchem-ai-plan-summary-input"),
                                    dcc.Textarea(
                                        id="qcchem-ai-plan-summary-input",
                                        className="qcchem-ai-assistant-window__input",
                                        placeholder="What should happen next?",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Expected outputs", "qcchem-ai-expected-outputs-input"),
                                    dcc.Textarea(
                                        id="qcchem-ai-expected-outputs-input",
                                        className="qcchem-ai-assistant-window__input",
                                        placeholder="One expected output per line",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__field",
                                children=[
                                    _field_label("Risk notes", "qcchem-ai-risk-notes-input"),
                                    dcc.Textarea(
                                        id="qcchem-ai-risk-notes-input",
                                        className="qcchem-ai-assistant-window__input",
                                        placeholder="Call out any execution or review concerns",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        id="qcchem-ai-current-ticket-preview",
                        className="qcchem-ai-assistant-window__ticket-preview",
                        children=[
                            html.P("Draft Ticket Preview", className="qcchem-ai-assistant-window__preview-title"),
                            html.P(
                                "No persisted draft yet. Fill the ticket editor to stage a workspace record.",
                                className="qcchem-ai-assistant-window__preview-body",
                            ),
                        ],
                    ),
                    html.Div(
                        id="qcchem-ai-run-guard",
                        className="qcchem-ai-assistant-window__run-guard",
                        hidden=True,
                        children=[
                            html.Div(id="qcchem-ai-run-guard-body"),
                            html.Div(
                                className="qcchem-ai-assistant-window__actions",
                                children=[
                                    html.Button(
                                        "Confirm Run",
                                        id="qcchem-ai-confirm-run",
                                        className="qcchem-ai-assistant-window__action",
                                        type="button",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="qcchem-ai-assistant-window__actions",
                        children=[
                            html.Button(
                                "Draft",
                                id="qcchem-ai-draft-ticket",
                                className="qcchem-ai-assistant-window__action",
                                type="button",
                            ),
                            html.Button(
                                "Accept",
                                id="qcchem-ai-accept-ticket",
                                className="qcchem-ai-assistant-window__action",
                                type="button",
                            ),
                            html.Button(
                                "Run",
                                id="qcchem-ai-run-ticket",
                                className="qcchem-ai-assistant-window__action",
                                type="button",
                            ),
                            html.Button(
                                "Return",
                                id="qcchem-ai-return-ticket",
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
