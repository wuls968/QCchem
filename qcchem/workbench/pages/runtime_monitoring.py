from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.evidence_console import build_evidence_console_model, format_action_label
from qcchem.workbench.pages.overview import build_sample_view_model
from qcchem.workbench.theme import THEME
from qcchem.workbench.viewmodels import build_runtime_comparison_model


def _runtime_figure(runtime: dict[str, object]) -> go.Figure:
    usage_seconds = float(runtime.get("returned_job_metadata", {}).get("metadata", {}).get("usage_seconds", 0) or 0)
    shots = float(runtime.get("returned_job_metadata", {}).get("metadata", {}).get("shots", 0) or 0)
    precision_target = float(runtime.get("options_snapshot", {}).get("precision_target", 0) or 0)
    transpiled_depth = float(runtime.get("transpiled_depth") or 0)
    two_qubit_gates = float(runtime.get("transpiled_two_qubit_gate_count") or 0)
    figure = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "xy"}, {"secondary_y": True}]],
        column_widths=[0.5, 0.5],
        horizontal_spacing=0.12,
        subplot_titles=("Execution footprint", "Compilation posture"),
    )
    figure.add_bar(
        x=["Shots", "Usage s", "2Q gates"],
        y=[shots, usage_seconds, two_qubit_gates],
        marker={
            "color": [THEME["accent"]["sage"], THEME["accent"]["copper"], THEME["accent"]["signal"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f"{shots:.0f}", f"{usage_seconds:.1f}", f"{two_qubit_gates:.0f}"],
        textposition="outside",
        hovertemplate="%{x}: %{y}<extra></extra>",
        name="Execution footprint",
        row=1,
        col=1,
    )
    figure.add_bar(
        x=["Compiled depth", "2Q gates"],
        y=[transpiled_depth, two_qubit_gates],
        marker={
            "color": [THEME["accent"]["deep_blue"], THEME["status"]["informational"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f"{transpiled_depth:.0f}", f"{two_qubit_gates:.0f}"],
        textposition="outside",
        hovertemplate="%{x}: %{y}<extra></extra>",
        name="Compilation scale",
        row=1,
        col=2,
        secondary_y=False,
    )
    figure.add_scatter(
        x=["Precision target"],
        y=[precision_target],
        mode="markers+text",
        text=[f"{precision_target:.4f}"],
        textposition="top center",
        marker={
            "size": 14,
            "color": THEME["surface"]["card"],
            "line": {"color": THEME["accent"]["copper"], "width": 2.4},
            "symbol": "diamond",
        },
        line={"color": THEME["accent"]["copper"], "width": 2, "dash": "dot"},
        hovertemplate="Precision target: %{y:.4f}<extra></extra>",
        name="Precision target",
        row=1,
        col=2,
        secondary_y=True,
    )
    status_items = [
        ("Attempted", bool(runtime.get("attempted")), THEME["accent"]["deep_blue"]),
        ("Submitted", bool(runtime.get("submitted")), THEME["accent"]["copper"]),
        ("Succeeded", bool(runtime.get("succeeded")), THEME["status"]["validated"]),
    ]
    figure.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=1.15,
        showarrow=False,
        align="left",
        font={"size": 12, "color": THEME["text"]["secondary"]},
        text=" · ".join(f"{label}: {'yes' if value else 'no'}" for label, value, _color in status_items),
    )
    apply_chart_theme(
        figure,
        title="Observed runtime and compilation telemetry for the current representative job",
        yaxis_title="Observed execution scale",
        height=460,
    )
    figure.update_xaxes(tickangle=0, row=1, col=1)
    figure.update_xaxes(tickangle=0, row=1, col=2)
    figure.update_yaxes(title_text="Observed execution scale", row=1, col=1)
    figure.update_yaxes(title_text="Depth / gate count", row=1, col=2, secondary_y=False)
    figure.update_yaxes(title_text="Precision target", row=1, col=2, secondary_y=True)
    figure.update_layout(legend={"orientation": "h", "x": 0, "y": 1.2})
    return figure


def _comparison_figure(model: dict[str, object]) -> go.Figure:
    benchmark = model.get("benchmark") or {}
    confidence = model.get("confidence") or {}
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    runtime_chemical_accuracy = confidence.get("runtime_chemical_accuracy") or {}
    simulator_error = float(benchmark.get("absolute_error") or confidence.get("absolute_error") or 0.0)
    hardware_error = float(runtime_chemical_accuracy.get("absolute_error_hartree") or simulator_error)
    threshold = float(chemical_accuracy.get("threshold_hartree") or confidence.get("threshold") or benchmark.get("threshold") or 0.02)
    distance_to_threshold = max(hardware_error - threshold, 0.0)
    figure = go.Figure()
    figure.add_bar(
        x=["Simulator", "Hardware"],
        y=[simulator_error, hardware_error],
        marker={
            "color": [THEME["accent"]["copper"], THEME["accent"]["sage"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f"{simulator_error:.4f}", f"{hardware_error:.4f}"],
        textposition="outside",
        hovertemplate="%{x}: %{y:.4f} Ha<extra></extra>",
    )
    figure.add_hrect(y0=0, y1=threshold, fillcolor="rgba(49, 95, 74, 0.08)", line_width=0)
    figure.add_hline(
        y=threshold,
        line_dash="dash",
        line_color=THEME["accent"]["deep_blue"],
        annotation_text="Chemical accuracy threshold",
        annotation_position="top left",
    )
    figure.add_annotation(
        xref="paper",
        yref="paper",
        x=0.99,
        y=0.98,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        align="right",
        bgcolor="rgba(255, 255, 255, 0.88)",
        bordercolor=THEME["surface"]["line"],
        borderwidth=1,
        font={"size": 11, "color": THEME["text"]["secondary"]},
        text=f"Hardware distance to target: {distance_to_threshold:.4f} Ha",
    )
    apply_chart_theme(
        figure,
        title="Simulator vs Hardware comparison for the current runtime-backed result",
        yaxis_title="Absolute error (Hartree)",
        height=420,
    )
    return figure


def build_runtime_monitoring_page(model: dict[str, object]) -> html.Div:
    runtime = model["runtime"]
    comparison = build_runtime_comparison_model(model)
    simulator_error = float(comparison["simulator_error_hartree"])
    hardware_error = float(comparison["hardware_error_hartree"])
    error_gap = float(comparison["error_gap_hartree"])
    threshold = float(comparison["threshold_hartree"])
    verification_status = str(runtime.get("verification_status", "pending"))
    runtime_verdict = str(comparison["hardware_verdict"])
    evidence_console = build_evidence_console_model(model)

    def _tone(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"passed", "validated", "retrieved", "retrieved result", "success", "succeeded"}:
            return "validated"
        if normalized in {"submitted", "queued", "review", "pending"}:
            return "exploratory"
        if normalized in {"failed", "unstable", "not met", "error"}:
            return "unstable"
        return "informational"

    return html.Div(
        className="qcchem-page qcchem-page--runtime",
        children=[
            html.Section(
                className="qcchem-card qcchem-runtime__hero",
                children=[
                    html.P("Operational telemetry", className="qcchem-card-eyebrow"),
                    html.H1("Runtime Monitoring", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "Separate operational success from scientific success. This page keeps job telemetry, compiled burden, and the simulator-versus-hardware deviation in one review surface before a hardware claim is trusted.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Backend", str(runtime.get("backend_name", "n/a")), str(runtime.get("backend_version", ""))),
                            metric_card("Job id", str(runtime.get("job_id", "n/a")), str(runtime.get("service", "runtime service"))),
                            status_card(
                                "Submission evidence",
                                verification_status.title(),
                                f"attempted={runtime.get('attempted', False)} | submitted={runtime.get('submitted', False)} | succeeded={runtime.get('succeeded', False)}",
                                tone=_tone(verification_status),
                            ),
                            status_card(
                                "Scientific verdict",
                                runtime_verdict,
                                f"Simulator {simulator_error:.4f} Ha | hardware {hardware_error:.4f} Ha | gap {error_gap:.4f} Ha",
                                tone=_tone(runtime_verdict),
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-runtime__decision",
                children=[
                    html.P("Decision cockpit", className="qcchem-card-eyebrow"),
                    html.H2("Runtime Decision", className="qcchem-card-title"),
                    html.P(
                        "Read this as the action layer: first check submission health, then hardware-derived accuracy, then budget pressure, and only then decide whether to collect, pause, or spend another controlled probe.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            status_card(
                                "Submission health",
                                str(evidence_console["runtime_boundary"]["submission_health"]).replace("_", " "),
                                f"attempted={runtime.get('attempted', False)} | submitted={runtime.get('submitted', False)} | succeeded={runtime.get('succeeded', False)}",
                                tone=_tone(evidence_console["runtime_boundary"]["submission_health"]),
                            ),
                            status_card(
                                "Hardware-derived accuracy",
                                runtime_verdict,
                                f"hardware {hardware_error:.4f} Ha vs threshold {threshold:.4f} Ha",
                                tone=_tone(runtime_verdict),
                            ),
                            metric_card(
                                "Simulator-vs-hardware gap",
                                f"{error_gap:.4f} Ha",
                                f"simulator {simulator_error:.4f} Ha",
                            ),
                            metric_card(
                                "Budget / shot usage",
                                str(evidence_console["runtime_boundary"]["budget_note"]),
                                f"precision target {evidence_console['runtime_boundary'].get('precision_target', 'n/a')}",
                            ),
                            status_card(
                                "Action gate",
                                format_action_label(evidence_console["runtime_boundary"]["recommended_action"]),
                                "High-cost runtime actions stay behind explicit ticket confirmation.",
                                tone=_tone(evidence_console["best_evidence"]["trust_tier"]),
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-runtime__comparison",
                children=[
                    html.P("Runtime comparison", className="qcchem-card-eyebrow"),
                    html.H2("Simulator vs Hardware", className="qcchem-card-title"),
                    html.P(
                        "Read this section as a judgment layer: how much of the observed error comes from backend reality rather than the underlying chemistry model.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Simulator reference", str(comparison["simulator_reference"]), f"Simulator error {simulator_error:.4f} Ha"),
                            metric_card("Hardware backend", str(comparison["hardware_backend"]), str(comparison["shot_note"])),
                            metric_card("Hardware verdict", str(comparison["hardware_verdict"]), str(comparison["hardware_verdict_note"])),
                            metric_card("Error gap", f"{error_gap:.4f} Ha", f"Threshold {threshold:.4f} Ha"),
                        ],
                    ),
                    html.Div(
                        className="qcchem-page__analysis-grid",
                        children=[
                            dcc.Graph(figure=_comparison_figure(model), config={"displayModeBar": False}),
                            detail_card(
                                "Comparison evidence",
                                [
                                    ("Simulator reference", str(comparison["simulator_reference"])),
                                    ("Hardware backend", str(comparison["hardware_backend_label"])),
                                    ("Hardware verdict", str(comparison["hardware_verdict"])),
                                    ("Hardware error", f"{hardware_error:.4f} Ha"),
                                    ("Simulator error", f"{simulator_error:.4f} Ha"),
                                    ("Queue stage", str(comparison["queue_stage"])),
                                ],
                                eyebrow="Side-by-Side Evidence",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-runtime__telemetry",
                children=[
                    html.P("Telemetry trace", className="qcchem-card-eyebrow"),
                    html.H2("Observed runtime and compilation telemetry", className="qcchem-card-title"),
                    html.P(
                        "Use these traces to understand whether queue, shots, compiled depth, and two-qubit burden make the runtime outcome unsurprising or suspicious.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_runtime_figure(runtime), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
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
                        "How to read this page",
                        "First decide whether the submission chain succeeded, then judge the simulator-versus-hardware gap, and only after that use the telemetry panel to diagnose whether the backend burden explains the result.",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_runtime_monitoring_page(build_sample_view_model())
