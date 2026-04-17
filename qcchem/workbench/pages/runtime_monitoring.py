from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.pages.overview import build_sample_view_model
from qcchem.workbench.viewmodels import build_runtime_comparison_model


def _runtime_figure(runtime: dict[str, object]) -> go.Figure:
    usage_seconds = float(runtime.get("returned_job_metadata", {}).get("metadata", {}).get("usage_seconds", 0) or 0)
    shots = float(runtime.get("returned_job_metadata", {}).get("metadata", {}).get("shots", 0) or 0)
    precision_target = float(runtime.get("options_snapshot", {}).get("precision_target", 0) or 0)
    transpiled_depth = float(runtime.get("transpiled_depth") or 0)
    figure = go.Figure()
    figure.add_scatter(
        x=["Attempted", "Shots", "Usage seconds", "Precision target", "Transpiled depth"],
        y=[
            1.0 if runtime.get("attempted") else 0.0,
            shots,
            usage_seconds,
            precision_target,
            transpiled_depth,
        ],
        mode="lines+markers",
        line={"color": "#20334a", "width": 3},
        marker={"size": 10, "color": "#93a18a"},
    )
    figure.update_layout(
        title={"text": "Observed runtime and compilation telemetry for the current representative job", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Observed value",
        font={"color": "#2d2216"},
    )
    return figure


def _comparison_figure(model: dict[str, object]) -> go.Figure:
    benchmark = model.get("benchmark") or {}
    confidence = model.get("confidence") or {}
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    runtime_chemical_accuracy = confidence.get("runtime_chemical_accuracy") or {}
    simulator_error = float(benchmark.get("absolute_error") or confidence.get("absolute_error") or 0.0)
    hardware_error = float(runtime_chemical_accuracy.get("absolute_error_hartree") or simulator_error)
    threshold = float(chemical_accuracy.get("threshold_hartree") or confidence.get("threshold") or benchmark.get("threshold") or 0.02)
    figure = go.Figure()
    figure.add_bar(
        x=["Simulator", "Hardware"],
        y=[simulator_error, hardware_error],
        marker_color=["#9a6b3f", "#93a18a"],
    )
    figure.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="#20334a",
        annotation_text="Chemical accuracy threshold",
        annotation_position="top left",
    )
    figure.update_layout(
        title={"text": "Simulator vs Hardware comparison for the current runtime-backed result", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Absolute error (Hartree)",
        font={"color": "#2d2216"},
    )
    return figure


def build_runtime_monitoring_page(model: dict[str, object]) -> html.Div:
    runtime = model["runtime"]
    comparison = build_runtime_comparison_model(model)
    simulator_error = float(comparison["simulator_error_hartree"])
    hardware_error = float(comparison["hardware_error_hartree"])
    error_gap = float(comparison["error_gap_hartree"])
    threshold = float(comparison["threshold_hartree"])
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
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Runtime Comparison", className="qcchem-card-eyebrow"),
                    html.H2("Simulator vs Hardware", className="qcchem-card-title", style={"fontSize": "2rem"}),
                    html.P(
                        "The defended simulator reference and the runtime-backed hardware result are called out explicitly here so backend drift is visible before the telemetry trace.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Simulator reference", str(comparison["simulator_reference"]), f"Simulator error {simulator_error:.4f} Ha"),
                            metric_card("Hardware backend", str(comparison["hardware_backend"]), str(comparison["shot_note"])),
                            metric_card("Hardware verdict", str(comparison["hardware_verdict"]), str(comparison["hardware_verdict_note"])),
                            metric_card("Error gap", f"{error_gap:.4f} Ha", f"Threshold {threshold:.4f} Ha"),
                        ],
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "minmax(0, 1.15fr) minmax(260px, 0.85fr)", "gap": "1rem", "marginTop": "1rem"},
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
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_runtime_figure(runtime), config={"displayModeBar": False})]),
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
                        "Later artifact selection will swap in the live runtime sidecar, but this page now pairs backend telemetry with a direct simulator-versus-hardware reading before the deeper operational trace.",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_runtime_monitoring_page(build_sample_view_model())
