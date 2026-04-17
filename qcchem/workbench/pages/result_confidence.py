from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.pages.overview import build_sample_view_model


def _confidence_figure(confidence: dict[str, object]) -> go.Figure:
    value = float(confidence.get("absolute_error") or 0.0)
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    chemical_accuracy_threshold = chemical_accuracy.get("threshold_hartree")
    threshold = float(chemical_accuracy_threshold or confidence.get("threshold") or 0.02)
    threshold_label = "Chemical accuracy threshold" if chemical_accuracy_threshold is not None else "Benchmark threshold"
    figure = go.Figure()
    figure.add_bar(x=["Absolute error", threshold_label], y=[value, threshold], marker_color=["#9a6b3f", "#315f4a"])
    figure.update_layout(
        title={
            "text": (
                "Confidence boundary against the chemical-accuracy threshold"
                if chemical_accuracy_threshold is not None
                else "Confidence boundary against the benchmark threshold"
            ),
            "x": 0.04,
        },
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Hartree",
        font={"color": "#2d2216"},
    )
    return figure


def build_result_confidence_page(model: dict[str, object]) -> html.Div:
    confidence = model["confidence"]
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    runtime_chemical_accuracy = confidence.get("runtime_chemical_accuracy") or {}
    chemical_accuracy_met = chemical_accuracy.get("meets_chemical_accuracy")
    chemical_accuracy_display = "Unknown" if chemical_accuracy_met is None else str(chemical_accuracy_met)
    runtime_evidence_available = runtime_chemical_accuracy.get("available", False)
    runtime_chemical_accuracy_met = runtime_chemical_accuracy.get("meets_chemical_accuracy")
    runtime_chemical_accuracy_display = "Unknown" if runtime_chemical_accuracy_met is None else str(runtime_chemical_accuracy_met)
    chemical_accuracy_threshold = chemical_accuracy.get("threshold_hartree")
    threshold_label = "Chemical accuracy threshold" if chemical_accuracy_threshold is not None else "Benchmark threshold"
    threshold_note = (
        "Declared chemical-accuracy line" if chemical_accuracy_threshold is not None else "Benchmark acceptance threshold"
    )
    threshold_value = float(chemical_accuracy_threshold or confidence.get("threshold") or 0.0)
    comparison_target = confidence.get("comparison_target") or confidence.get("boundary", {}).get(
        "comparison_target", "exact diagonalization"
    )
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
                            metric_card(threshold_label, f"{threshold_value:.4f} Ha", threshold_note),
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
                            (
                                "Chemical accuracy",
                                chemical_accuracy_display,
                            ),
                            (threshold_label, f"{threshold_value:.4f} Ha"),
                            (
                                "Runtime evidence available",
                                str(runtime_evidence_available),
                            ),
                            (
                                "Runtime chemical accuracy",
                                runtime_chemical_accuracy_display,
                            ),
                            ("Comparison target", str(comparison_target)),
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
