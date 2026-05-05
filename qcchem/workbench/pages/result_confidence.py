from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import add_chart_note, add_threshold_line, apply_chart_theme
from qcchem.workbench.pages.overview import build_sample_view_model
from qcchem.workbench.theme import THEME


def _confidence_figure(confidence: dict[str, object]) -> go.Figure:
    value = float(confidence.get("absolute_error") or 0.0)
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    chemical_accuracy_threshold = chemical_accuracy.get("threshold_hartree")
    threshold = float(chemical_accuracy_threshold or confidence.get("threshold") or 0.02)
    threshold_label = "Chemical accuracy threshold" if chemical_accuracy_threshold is not None else "Benchmark threshold"
    figure = go.Figure()
    figure.add_hrect(y0=0, y1=threshold, fillcolor="rgba(49, 95, 74, 0.08)", line_width=0)
    figure.add_bar(
        x=["Absolute error", threshold_label],
        y=[value, threshold],
        marker={
            "color": [THEME["accent"]["copper"], THEME["status"]["validated"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f"{value:.4f}", f"{threshold:.4f}"],
        textposition="outside",
        hovertemplate="%{x}: %{y:.4f} Ha<extra></extra>",
    )
    apply_chart_theme(
        figure,
        title=(
            "Confidence boundary against the chemical-accuracy threshold"
            if chemical_accuracy_threshold is not None
            else "Confidence boundary against the benchmark threshold"
        ),
        yaxis_title="Hartree",
        height=400,
    )
    add_threshold_line(figure, value=threshold, label=threshold_label)
    add_chart_note(figure, text=f"Observed gap above threshold: {max(value - threshold, 0.0):.4f} Ha")
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

    def _tone_for_accuracy(value: object) -> str:
        if value is True:
            return "validated"
        if value is False:
            return "unstable"
        return "informational"

    return html.Div(
        className="qcchem-page qcchem-page--confidence",
        children=[
            html.Section(
                className="qcchem-card qcchem-confidence__hero",
                children=[
                    html.P("Decision surface", className="qcchem-card-eyebrow"),
                    html.H1("Result Confidence Report", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "This page should read like the last paragraph of a scientific review note: what threshold matters, what evidence exists, and whether the current claim is genuinely defended.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card(threshold_label, f"{threshold_value:.4f} Ha", threshold_note),
                            metric_card("Absolute error", f'{float(confidence.get("absolute_error") or 0):.4f} Ha', "Representative measured deviation"),
                            status_card(
                                "Chemical accuracy",
                                chemical_accuracy_display,
                                f"comparison target: {comparison_target}",
                                tone=_tone_for_accuracy(chemical_accuracy_met),
                            ),
                            status_card(
                                "Runtime chemical accuracy",
                                runtime_chemical_accuracy_display,
                                f"runtime evidence available: {runtime_evidence_available}",
                                tone=_tone_for_accuracy(runtime_chemical_accuracy_met),
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-confidence__boundary",
                children=[
                    html.P("Threshold framing", className="qcchem-card-eyebrow"),
                    html.H2("Boundary against threshold", className="qcchem-card-title"),
                    html.P(
                        "The boundary chart makes the decision legible: how far the current result sits above the accepted line, and whether the runtime-backed path is helping or hurting that position.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_confidence_figure(confidence), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    detail_card(
                        "Evidence checklist",
                        [
                            ("Verification status", str(confidence.get("verification_status", "validated"))),
                            ("Chemical accuracy", chemical_accuracy_display),
                            (threshold_label, f"{threshold_value:.4f} Ha"),
                            ("Runtime evidence available", str(runtime_evidence_available)),
                            ("Runtime chemical accuracy", runtime_chemical_accuracy_display),
                            ("Comparison target", str(comparison_target)),
                            ("Distance to threshold", f"{max(float(confidence.get('absolute_error') or 0.0) - threshold_value, 0.0):.4f} Ha"),
                        ],
                    ),
                    callout_card(
                        "Conclusion rule",
                        "Do not let runtime retrieval be mistaken for scientific validation. A retrieved job, a benchmark threshold, and a chemical-accuracy threshold are different kinds of evidence and should stay visibly separate here.",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_result_confidence_page(build_sample_view_model())
