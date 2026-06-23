from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from dash import dcc, html

from qcchem.io.workflow_config import workflow_template
from qcchem.workflow.custom_workflow import workflow_plugins_summary
from qcchem.workbench.components.cards import metric_card, status_card

DEFAULT_WORKFLOW_STUDIO_EXPORT = "artifacts/workflows/studio/workflow.yaml"


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _count_jsonl_events(path: Path) -> int:
    try:
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    except Exception:
        return 0


def _first_blocking_failure(acceptance: dict[str, Any]) -> str:
    failures = acceptance.get("blocking_failures")
    if not isinstance(failures, list) or not failures:
        return ""
    first = failures[0]
    if not isinstance(first, dict):
        return str(first)
    step = first.get("step_id")
    reason = first.get("reason") or "blocked"
    error = first.get("error")
    prefix = f"{step}: {reason}" if step else str(reason)
    return f"{prefix} - {error}" if error else prefix


def _step_status_counts(steps: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for step in steps:
        if not isinstance(step, dict):
            continue
        status = str(step.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _workflow_results(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    workflows_root = root / "artifacts" / "workflows"
    if not workflows_root.exists():
        return results
    for path in sorted(workflows_root.glob("**/workflow_result.json")):
        payload = _safe_read_json(path)
        if not payload:
            continue
        sidecar_root = path.parent
        graph = _safe_read_json(sidecar_root / "workflow_graph.json")
        graph_nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
        graph_edges = graph.get("edges") if isinstance(graph.get("edges"), list) else []
        acceptance = payload.get("acceptance_summary") if isinstance(payload.get("acceptance_summary"), dict) else {}
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        steps = payload.get("steps") if isinstance(payload.get("steps"), list) else []
        outputs = payload.get("outputs") if isinstance(payload.get("outputs"), dict) else {}
        results.append(
            {
                "path": str(path),
                "workflow_name": payload.get("workflow_name"),
                "status": payload.get("status"),
                "summary": summary,
                "artifact_root": payload.get("artifact_root"),
                "accepted": acceptance.get("accepted"),
                "recommended_action": acceptance.get("recommended_action"),
                "blocking_failure_count": len(acceptance.get("blocking_failures") or []),
                "first_blocking_failure": _first_blocking_failure(acceptance),
                "step_status_counts": _step_status_counts(steps),
                "graph_node_count": len(graph_nodes),
                "graph_edge_count": len(graph_edges),
                "provenance_event_count": _count_jsonl_events(sidecar_root / "provenance.jsonl"),
                "has_workflow_graph": (sidecar_root / "workflow_graph.json").exists(),
                "has_workflow_provenance": (sidecar_root / "provenance.jsonl").exists(),
                "has_workflow_registry": (sidecar_root / "registry.json").exists(),
                "workflow_report_markdown": outputs.get("workflow_report_markdown") or str(sidecar_root / "workflow_report.md"),
                "mtime": path.stat().st_mtime if path.exists() else 0,
            }
        )
    results.sort(key=lambda item: float(item.get("mtime") or 0))
    return results[-6:]


def _plugin_card(plugin: dict[str, Any]) -> html.Div:
    capabilities = plugin.get("capabilities") or []
    return html.Div(
        className="qcchem-workflow-studio__plugin",
        children=[
            html.Div(
                className="qcchem-ai-workspace-page__ticket-topline",
                children=[
                    html.Strong(str(plugin.get("kind", "plugin"))),
                    html.Span(str(plugin.get("package") or "qcchem"), className="qcchem-context-bar__chip"),
                ],
            ),
            html.P(str(plugin.get("summary") or "No summary registered."), className="qcchem-card-note qcchem-card-note--compact"),
            html.P(", ".join(str(item) for item in capabilities) or "local", className="qcchem-ai-workspace-page__ticket-meta"),
        ],
    )


def _result_card(result: dict[str, Any]) -> html.Div:
    summary = result.get("summary") or {}
    step_status_counts = result.get("step_status_counts") if isinstance(result.get("step_status_counts"), dict) else {}
    accepted = result.get("accepted")
    accepted_label = "accepted" if accepted is True else "not accepted" if accepted is False else "not reviewed"
    missing_sidecars = [
        label
        for label, present in (
            ("graph", result.get("has_workflow_graph")),
            ("provenance", result.get("has_workflow_provenance")),
            ("registry", result.get("has_workflow_registry")),
        )
        if not present
    ]
    sidecar_label = "complete" if not missing_sidecars else "missing " + ", ".join(missing_sidecars)
    return html.Div(
        className="qcchem-workflow-studio__run",
        children=[
            html.Div(
                className="qcchem-ai-workspace-page__ticket-topline",
                children=[
                    html.Strong(str(result.get("workflow_name") or "workflow")),
                    html.Span(str(result.get("status") or "unknown"), className="qcchem-context-bar__chip"),
                ],
            ),
            html.Div(
                className="qcchem-ai-workspace-page__ticket-grid",
                children=[
                    html.Div([html.Span("Completed"), html.Strong(str(summary.get("completed_steps", 0)))]),
                    html.Div([html.Span("Failed"), html.Strong(str(summary.get("failed_steps", 0)))]),
                    html.Div([html.Span("Generated"), html.Strong(str(summary.get("generated_steps", 0)))]),
                    html.Div([html.Span("Acceptance"), html.Strong(accepted_label)]),
                    html.Div([html.Span("Graph"), html.Strong(f"{result.get('graph_node_count', 0)} nodes / {result.get('graph_edge_count', 0)} edges")]),
                    html.Div([html.Span("Provenance"), html.Strong(f"{result.get('provenance_event_count', 0)} events")]),
                ],
            ),
            html.Div(
                className="qcchem-workflow-studio__run-facts",
                children=[
                    html.Span(f"step statuses: {step_status_counts or {}}"),
                    html.Span(f"recommended action: {result.get('recommended_action') or 'n/a'}"),
                    html.Span(f"sidecars: {sidecar_label}"),
                ],
            ),
            (
                html.P(
                    str(result.get("first_blocking_failure")),
                    className="qcchem-workflow-studio__run-blocker",
                )
                if result.get("first_blocking_failure")
                else None
            ),
            html.P(str(result.get("path")), className="qcchem-card-note qcchem-card-note--compact"),
            html.P(str(result.get("workflow_report_markdown")), className="qcchem-card-note qcchem-card-note--compact"),
        ],
    )


def _template_yaml() -> str:
    workspace_root = Path.cwd()
    return yaml.safe_dump(
        workflow_template(source_path=workspace_root / DEFAULT_WORKFLOW_STUDIO_EXPORT, workspace_root=workspace_root),
        sort_keys=False,
    )


def graph_nodes_from_steps(steps: list[Any]) -> list[html.Div]:
    """Render compact graph nodes for the Workflow Studio canvas."""
    if not steps:
        return [html.Div("No steps", className="qcchem-workflow-studio__empty-graph")]
    nodes: list[html.Div] = []
    for step in steps:
        step_id = getattr(step, "id", str(step))
        kind = getattr(step, "kind", "step")
        needs = getattr(step, "needs", []) or []
        generated_by = getattr(step, "generated_by", None)
        nodes.append(
            html.Div(
                className="qcchem-workflow-studio__node",
                children=[
                    html.Strong(str(step_id)),
                    html.Span(str(kind)),
                    html.Small("needs: " + ", ".join(str(item) for item in needs) if needs else "root step"),
                    html.Small(f"generated by: {generated_by}") if generated_by else None,
                ],
            )
        )
    return nodes


def layout() -> html.Div:
    root = Path.cwd()
    plugins = workflow_plugins_summary()["plugins"]
    results = _workflow_results(root)
    builtins = [plugin for plugin in plugins if plugin.get("package") == "qcchem"]
    installed = [plugin for plugin in plugins if plugin.get("package") != "qcchem"]

    return html.Div(
        className="qcchem-page qcchem-workflow-studio",
        children=[
            html.Section(
                className="qcchem-card qcchem-workflow-studio__hero",
                children=[
                    html.P("Custom Workflow Surface", className="qcchem-card-eyebrow"),
                    html.H1("Workflow Studio", className="qcchem-card-title"),
                    html.P(
                        "Build plugin-backed QCchem workflows from a YAML source of truth, inspect the graph, and keep every execution tied to artifacts and provenance.",
                        className="qcchem-panel__note",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Built-in steps", str(len(builtins)), "QCchem-native workflow actions", tone="compact"),
                            metric_card("Installed plugins", str(len(installed)), "Entry points under qcchem.workflow_steps", tone="compact"),
                            metric_card("Workflow runs", str(len(results)), "Recent workflow_result.json artifacts", tone="compact"),
                            metric_card("Source of truth", "YAML", "The graph and inspector derive from the workflow file", tone="compact"),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-workflow-studio__split",
                children=[
                    html.Section(
                        className="qcchem-card qcchem-workflow-studio__palette",
                        children=[
                            html.P("Step Palette", className="qcchem-card-eyebrow"),
                            html.H2("Plugins", className="qcchem-card-title"),
                            html.P(
                                "Built-ins and installed step plugins expose metadata through describe().",
                                className="qcchem-panel__note",
                            ),
                            html.Div([_plugin_card(plugin) for plugin in plugins], className="qcchem-workflow-studio__plugin-list"),
                        ],
                    ),
                    html.Section(
                        className="qcchem-card qcchem-workflow-studio__canvas",
                        children=[
                            html.P("Graph Canvas", className="qcchem-card-eyebrow"),
                            html.H2("YAML And Derived Graph", className="qcchem-card-title"),
                            dcc.Textarea(
                                id="qcchem-workflow-studio-yaml",
                                value=_template_yaml(),
                                spellCheck=False,
                                className="qcchem-workflow-studio__yaml",
                            ),
                            html.Div(
                                className="qcchem-workflow-studio__editor-actions",
                                children=[
                                    html.Button("Validate", id="qcchem-workflow-studio-validate", n_clicks=0),
                                    dcc.Input(
                                        id="qcchem-workflow-studio-export-path",
                                        value=DEFAULT_WORKFLOW_STUDIO_EXPORT,
                                        type="text",
                                        debounce=True,
                                    ),
                                    html.Button("Export YAML", id="qcchem-workflow-studio-export", n_clicks=0),
                                ],
                            ),
                            html.Div(id="qcchem-workflow-studio-export-status", className="qcchem-workflow-studio__status-line"),
                            html.Div(
                                id="qcchem-workflow-studio-graph",
                                className="qcchem-workflow-studio__graph",
                                children=graph_nodes_from_steps([]),
                            ),
                        ],
                    ),
                    html.Section(
                        className="qcchem-card qcchem-workflow-studio__inspector",
                        children=[
                            html.P("Inspector", className="qcchem-card-eyebrow"),
                            html.H2("Policy And Runs", className="qcchem-card-title"),
                            status_card(
                                "Execution boundary",
                                "Trusted installed plugins",
                                "Runtime and hardware submission still use existing QCchem confirmation gates.",
                                tone="informational",
                            ),
                            html.Div(id="qcchem-workflow-studio-validation", className="qcchem-workflow-studio__validation"),
                            html.Div(
                                className="qcchem-workflow-studio__run-list",
                                children=[_result_card(item) for item in results]
                                or [html.Div("No workflow_result.json artifacts found yet.", className="qcchem-ai-workspace-page__empty-state")],
                            ),
                            html.Div(
                                className="qcchem-workflow-studio__commands",
                                children=[
                                    html.P("CLI", className="qcchem-ai-workspace-page__ticket-meta"),
                                    html.Code("qcchem workflow validate -c examples/workflows/h2_trust_first_workflow.yaml"),
                                    html.Code("qcchem workflow run -c examples/workflows/h2_trust_first_workflow.yaml"),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
