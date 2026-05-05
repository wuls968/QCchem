from __future__ import annotations

import json
from pathlib import Path

from dash import dcc, html

from qcchem.workbench.data import load_artifact_bundle
from qcchem.workbench.evidence_console import format_action_label


def _status_chip(label: str, tone: str) -> html.Span:
    return html.Span(label, className=f"qcchem-ai-chip qcchem-ai-chip--{tone}")


def _field_label(label: str, for_id: str) -> html.Label:
    return html.Label(label, htmlFor=for_id, className="qcchem-ai-assistant-window__field-label")


def _route_label(pathname: str | None) -> str:
    mapping = {
        "/overview": "Overview",
        "/result-confidence": "Result Confidence",
        "/benchmarks": "Benchmarks",
        "/hardware-campaign": "Hardware Campaign",
        "/ai-workspace": "AI Workspace",
        "/runtime-monitoring": "Runtime Monitoring",
    }
    return mapping.get(pathname or "/overview", "Research Console")


def _normalize_lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_evidence_summary(path_text: str | None, workspace_base: Path | str | None) -> tuple[str | None, dict[str, object] | None]:
    if not path_text:
        return None, None
    base = Path(workspace_base) if workspace_base is not None else Path.cwd()
    raw = Path(path_text.strip()).expanduser()
    resolved = raw if raw.is_absolute() else (base / raw).resolve()
    if resolved.is_dir():
        bundle = load_artifact_bundle(resolved)
        run = bundle.get("run") or {}
        evidence = run.get("evidence_summary")
        if isinstance(evidence, dict):
            return str(resolved), evidence
        for filename in ("benchmark_result.json", "study_result.json", "scan_result.json", "hardware_calibration_summary.json"):
            payload = _read_json(resolved / filename)
            if payload and isinstance(payload.get("evidence_summary"), dict):
                return str(resolved), payload["evidence_summary"]
        return str(resolved), None
    if resolved.name == "result.json":
        bundle = load_artifact_bundle(resolved.parent)
        run = bundle.get("run") or {}
        evidence = run.get("evidence_summary")
        return str(resolved.parent), evidence if isinstance(evidence, dict) else None
    payload = _read_json(resolved)
    if payload and isinstance(payload.get("evidence_summary"), dict):
        return str(resolved), payload["evidence_summary"]
    return str(resolved), None


def build_ticket_preview_content(
    *,
    current_ticket_record: dict[str, object] | None,
    task_type: str | None,
    title: str | None,
    request_text: str | None,
    linked_artifacts_text: str | None,
    plan_summary: str | None,
    expected_outputs_text: str | None,
    risk_notes_text: str | None,
    workspace_base: Path | str | None,
    current_route: str | None,
) -> html.Div:
    record = dict(current_ticket_record or {})
    task_type_value = str(record.get("task_type") or task_type or "analysis")
    title_value = str(record.get("title") or title or "Untitled Task")
    request_value = str(record.get("request_text") or request_text or "").strip()
    plan_value = str(record.get("plan_summary") or plan_summary or "").strip()
    status_value = str(record.get("status") or "draft")
    linked_artifacts = record.get("linked_artifacts")
    if not isinstance(linked_artifacts, list):
        linked_artifacts = _normalize_lines(linked_artifacts_text)
    expected_outputs = record.get("expected_outputs")
    if not isinstance(expected_outputs, list):
        expected_outputs = _normalize_lines(expected_outputs_text)
    risk_notes = record.get("risk_notes")
    if not isinstance(risk_notes, list):
        risk_notes = _normalize_lines(risk_notes_text)

    first_artifact = str(linked_artifacts[0]) if linked_artifacts else None
    resolved_artifact, evidence = _artifact_evidence_summary(first_artifact, workspace_base)
    recommended_action = (evidence or {}).get("recommended_action") or record.get("recommended_action") or "review_evidence_boundary"
    limitation_notes = [str(item) for item in risk_notes]
    if (evidence or {}).get("trust_tier") == "hardware_verified":
        limitation_notes.append("hardware_verified records runtime retrieval; it does not by itself prove publication-grade chemistry validation.")
    evidence_children: list[html.Component] = []
    if evidence:
        evidence_children = [
            html.P("Evidence-first context", className="qcchem-ai-assistant-window__preview-title"),
            html.Div(
                className="qcchem-ai-assistant-window__preview-grid",
                children=[
                    html.Div([html.Span("Claim"), html.Strong(str(evidence.get("primary_scientific_claim") or "No claim declared"))]),
                    html.Div([html.Span("Trust tier"), html.Strong(str(evidence.get("trust_tier") or "unknown"))]),
                    html.Div([html.Span("Runtime evidence"), html.Strong(str(evidence.get("runtime_evidence_status") or "unknown"))]),
                    html.Div([html.Span("Recommended action"), html.Strong(str(evidence.get("recommended_action") or "review_evidence_boundary"))]),
                ],
            ),
        ]
    else:
        evidence_children = [
            html.P("Evidence-first context", className="qcchem-ai-assistant-window__preview-title"),
            html.P(
                "Link a QCchem artifact to pull its claim, trust tier, and recommended action into the ticket review flow.",
                className="qcchem-ai-assistant-window__preview-body",
            ),
        ]

    return html.Div(
        children=[
            html.P("Draft Ticket Preview", className="qcchem-ai-assistant-window__preview-title"),
            html.Div(
                className="qcchem-ai-assistant-window__preview-grid",
                children=[
                    html.Div([html.Span("Current route"), html.Strong(_route_label(current_route))]),
                    html.Div([html.Span("Task type"), html.Strong(task_type_value.title())]),
                    html.Div([html.Span("Status"), html.Strong(status_value.replace("_", " ").title())]),
                    html.Div([html.Span("Artifacts"), html.Strong(str(len(linked_artifacts)))]),
                ],
            ),
            html.Div(
                className="qcchem-ai-assistant-window__preview-block",
                children=[
                    html.Strong(title_value, className="qcchem-ai-assistant-window__preview-heading"),
                    html.P(request_value or "Describe the request to stage a persistent ticket.", className="qcchem-ai-assistant-window__preview-body"),
                    html.P(plan_value or "No execution or analysis plan summary yet.", className="qcchem-ai-assistant-window__preview-body"),
                ],
            ),
            html.Div(
                className="qcchem-ai-assistant-window__preview-grid",
                children=[
                    html.Div([html.Span("Expected outputs"), html.Strong(", ".join(expected_outputs) or "None yet")]),
                    html.Div([html.Span("Risk notes"), html.Strong(", ".join(risk_notes) or "None yet")]),
                ],
            ),
            html.Div(
                className="qcchem-ai-assistant-window__preview-block",
                children=[
                    html.P("Linked evidence", className="qcchem-ai-assistant-window__preview-title"),
                    html.P(resolved_artifact or "No linked artifact selected yet.", className="qcchem-ai-assistant-window__preview-body"),
                ],
            ),
            html.Div(
                className="qcchem-ai-assistant-window__preview-grid",
                children=[
                    html.Div([html.Span("Evidence Scope"), html.Strong(resolved_artifact or "No artifact scope selected")]),
                    html.Div([html.Span("Recommended Action"), html.Strong(format_action_label(recommended_action))]),
                    html.Div(
                        [
                            html.Span("Limitation Notes"),
                            html.Strong("; ".join(limitation_notes) or "No explicit limitation notes yet"),
                        ]
                    ),
                ],
            ),
            html.Div(className="qcchem-ai-assistant-window__preview-block", children=evidence_children),
        ],
    )


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
                        id="qcchem-ai-assistant-drag-handle",
                        className="qcchem-ai-assistant-window__drag-handle",
                        children=[
                            html.Div(
                                className="qcchem-ai-assistant-window__drag-grip",
                                children=[html.Span() for _ in range(3)],
                            ),
                            html.Div(
                                className="qcchem-ai-assistant-window__title-group",
                                children=[
                                    html.P("Assistant", className="qcchem-ai-assistant-window__eyebrow"),
                                    html.H2("Ticket Console", className="qcchem-ai-assistant-window__title"),
                                ],
                            ),
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
                                "Reset",
                                id="qcchem-ai-assistant-reset-position",
                                className="qcchem-ai-assistant-window__control qcchem-ai-assistant-window__control--subtle",
                                type="button",
                                title="Move the assistant back to a safe bottom-right position.",
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
                            _status_chip("Draft before execution", "informational"),
                            _status_chip("High-risk runs stay guarded", "exploratory"),
                            _status_chip("Workspace state is persisted", "validated"),
                        ],
                    ),
                    html.Div(
                        className="qcchem-ai-assistant-window__form",
                        children=[
                            html.Section(
                                className="qcchem-ai-assistant-window__section",
                                children=[
                                    html.P("Request", className="qcchem-ai-assistant-window__section-title"),
                                    html.Div(
                                        className="qcchem-ai-assistant-window__field-grid",
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
                                                        className="qcchem-ai-assistant-window__input qcchem-ai-assistant-window__input--single-line",
                                                        placeholder="Summarize the task in one line",
                                                        type="text",
                                                    ),
                                                ],
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
                                ],
                            ),
                            html.Section(
                                className="qcchem-ai-assistant-window__section",
                                children=[
                                    html.P("Execution framing", className="qcchem-ai-assistant-window__section-title"),
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
                                                placeholder="Call out execution or review concerns",
                                            ),
                                        ],
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
            html.Div(
                id="qcchem-ai-assistant-resize-handle",
                className="qcchem-ai-assistant-window__resize-handle",
                children=html.Span("Resize", className="qcchem-ai-assistant-window__resize-label"),
            ),
        ],
    )
