"""Shared source chooser for the scan and study pages."""

from __future__ import annotations

from typing import Any

from pathlib import Path

from dash import Input, Output, dcc, html, no_update

from qcchem.workbench.aggregates import aggregate_selection


def aggregate_content(kind: str, model: dict[str, Any]) -> html.Div:
    from qcchem.workbench.pages.scans import build_scans_page
    from qcchem.workbench.pages.studies import build_studies_page

    if model.get("source_error"):
        return html.Div([html.H1("Scans" if kind == "scan" else "Studies"),
                         html.P(model["source_error"], role="status")], className="qcchem-card")
    label = "Demo data: bundled example." if model.get("demo") else f"Source: {model['source_path']}"
    notice = f"Checkpoint: {model.get('artifact_status')} · {len(model.get('points') or [])} committed points"
    if model.get("expected_points") is not None:
        notice += f" / {model['expected_points']} planned"
    return html.Div([
        html.P(label, className="qcchem-card-note qcchem-aggregate__source"),
        html.P(notice, className="qcchem-card-note", role="status") if model.get("partial") else None,
        build_scans_page(model) if kind == "scan" else build_studies_page(model),
    ])


def aggregate_layout(kind: str) -> html.Div:
    options, selected, model = aggregate_selection(kind, None)
    return html.Div([
        html.Section([
            html.Label("Data source", htmlFor=f"qcchem-{kind}-source"),
            dcc.Dropdown(id=f"qcchem-{kind}-source", options=options, value=selected, clearable=False),
            html.Button("Refresh artifacts", id=f"qcchem-{kind}-refresh", n_clicks=0),
        ], className="qcchem-card qcchem-aggregate__chooser"),
        html.Div(aggregate_content(kind, model), id=f"qcchem-{kind}-content"),
        dcc.Interval(id=f"qcchem-{kind}-poll", interval=5000, n_intervals=0),
    ], className=f"qcchem-page qcchem-page--{kind}s")


def register_aggregate_callbacks(app, artifact_root: Path) -> None:
    def register(kind: str):
        @app.callback(
            Output(f"qcchem-{kind}-source", "options"), Output(f"qcchem-{kind}-source", "value"),
            Output(f"qcchem-{kind}-content", "children"),
            Input(f"qcchem-{kind}-source", "value"), Input(f"qcchem-{kind}-refresh", "n_clicks"),
            Input(f"qcchem-{kind}-poll", "n_intervals"),
        )
        def refresh(selection, _clicks, _intervals):
            options, selected, model = aggregate_selection(kind, selection, artifact_root)
            return options, selected if selected != selection else no_update, aggregate_content(kind, model)

    for kind in ("scan", "study"):
        register(kind)
