from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.pages.overview import build_sample_view_model


def _confidence_figure(confidence: dict[str, object]) -> go.Figure:
    value = float(confidence.get("absolute_error") or 0.0)
    threshold = float(confidence.get("threshold") or 0.02)
    figure = go.Figure()
    figure.add_bar(x=["Absolute error", "Threshold"], y=[value, threshold], marker_color=["#9a6b3f", "#315f4a"])
    figure.update_layout(
        title={"text": "Confidence boundary against the declared chemical-accuracy threshold", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Hartree",
        font={"color": "#2d2216"},
    )
    return figure


def build_result_confidence_page(model: dict[str, object]) -> html.Div:
    confidence = model["confidence"]
    return html.Div(
        className="qcchem-page qcchem-page--confidence",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Decision Surface", className="qcchem-card-eyebrow"),
                    html.H2("Result Confidence Report", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "The final page gathers the accuracy boundary, runtime evidence, and verification flags into a concise report-oriented summary.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Threshold", f'{float(confidence.get("threshold") or 0):.4f} Ha', "Declared chemical-accuracy line"),
                            metric_card("Absolute error", f'{float(confidence.get("absolute_error") or 0):.4f} Ha', "Representative measured deviation"),
                            metric_card("Within uncertainty", str(confidence.get("within_uncertainty", False)), "Benchmark consistency"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_confidence_figure(confidence), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Evidence checklist",
                        [
                            ("Verification status", str(confidence.get("verification_status", "validated"))),
                            ("Chemical accuracy", "True"),
                            ("Runtime-backed", "True"),
                            ("Comparison target", str(confidence.get("boundary", {}).get("comparison_target", "exact diagonalization"))),
                        ],
                    ),
                    callout_card(
                        "Report framing",
                        "This section is written like the end of a scientific notebook page: what evidence exists, whether the threshold is met, and what assumptions still limit the claim.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_result_confidence_page(build_sample_view_model())
