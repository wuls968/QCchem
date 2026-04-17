from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.pages.overview import build_sample_view_model


def _runtime_figure() -> go.Figure:
    figure = go.Figure()
    figure.add_scatter(
        x=["Submission", "Queue", "Execution", "Retrieval", "Verification"],
        y=[3, 24, 132, 9, 18],
        mode="lines+markers",
        line={"color": "#20334a", "width": 3},
        marker={"size": 10, "color": "#93a18a"},
    )
    figure.update_layout(
        title={"text": "Observed runtime path for the current representative job", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Seconds",
        font={"color": "#2d2216"},
    )
    return figure


def layout() -> html.Div:
    runtime = build_sample_view_model()["runtime"]
    return html.Div(
        className="qcchem-page qcchem-page--runtime",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Operational Telemetry", className="qcchem-card-eyebrow"),
                    html.H2("Runtime Monitoring", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "Submission status, compile posture, and retrieval evidence for the representative runtime-backed chemistry result.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Backend", str(runtime.get("backend_name", "n/a")), str(runtime.get("backend_version", ""))),
                            metric_card("Job id", str(runtime.get("job_id", "n/a")), "Runtime estimator"),
                            metric_card("Verification", str(runtime.get("verification_status", "pending")).title(), str(runtime.get("service", "n/a"))),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_runtime_figure(), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Runtime evidence",
                        [
                            ("Attempted", str(runtime.get("attempted", False))),
                            ("Submitted", str(runtime.get("submitted", False))),
                            ("Succeeded", str(runtime.get("succeeded", False))),
                            ("Shots", str(runtime.get("returned_job_metadata", {}).get("metadata", {}).get("shots", "n/a"))),
                        ],
                    ),
                    detail_card(
                        "Execution options",
                        [
                            ("Precision target", str(runtime.get("options_snapshot", {}).get("precision_target", "n/a"))),
                            ("Resilience level", str(runtime.get("options_snapshot", {}).get("resilience_level", "n/a"))),
                            ("Queue stage", str(runtime.get("result_provenance", {}).get("attempt_stage", "n/a"))),
                            ("Depth", str(runtime.get("transpiled_depth", "n/a"))),
                        ],
                        eyebrow="Runtime Options",
                    ),
                    callout_card(
                        "Operational signal",
                        "Later artifact selection will swap in the live runtime sidecar, but this page already mirrors the telemetry vocabulary used by current QCchem runtime outputs.",
                    ),
                ],
            ),
        ],
    )
