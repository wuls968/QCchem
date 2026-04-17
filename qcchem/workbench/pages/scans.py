from __future__ import annotations

from typing import Any

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


def sample_scan_model() -> dict[str, Any]:
    validated_points = [
        {"point_label": "0.5 A", "parameter_value": 0.5, "total_energy": -1.0912, "verification_status": "validated"},
        {"point_label": "0.7 A", "parameter_value": 0.7, "total_energy": -1.1178, "verification_status": "validated"},
    ]
    exploratory_points = [
        {"point_label": "0.9 A", "parameter_value": 0.9, "total_energy": -1.0836, "verification_status": "exploratory"},
    ]
    return {
        "scan_name": "h2_short_scan",
        "parameter_name": "bond_length_angstrom",
        "summary": {
            "total_runs": len(validated_points) + len(exploratory_points),
            "status_counts": {"validated": 2, "exploratory": 1},
        },
        "validated_points": validated_points,
        "exploratory_points": exploratory_points,
    }


def _scan_curve_figure(model: dict[str, Any]) -> go.Figure:
    validated_points = model.get("validated_points") or []
    exploratory_points = model.get("exploratory_points") or []
    figure = go.Figure()
    figure.add_scatter(
        x=[point["parameter_value"] for point in validated_points],
        y=[point["total_energy"] for point in validated_points],
        mode="lines+markers",
        name="Validated-like",
        line={"color": "#20334a", "width": 3},
        marker={"size": 10, "color": "#20334a"},
    )
    if exploratory_points:
        figure.add_scatter(
            x=[point["parameter_value"] for point in exploratory_points],
            y=[point["total_energy"] for point in exploratory_points],
            mode="markers",
            name="Exploratory",
            marker={"size": 12, "color": "#c58742", "symbol": "diamond"},
        )
    figure.update_layout(
        title={"text": "Energy sweep across the defended scan window", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title=str(model.get("parameter_name", "parameter")),
        yaxis_title="Total energy (Hartree)",
        font={"color": "#2d2216"},
        legend={"orientation": "h", "x": 0.02, "y": 1.12},
    )
    return figure


def build_scans_page(model: dict[str, Any]) -> html.Div:
    validated_points = model.get("validated_points") or []
    exploratory_points = model.get("exploratory_points") or []
    summary = model.get("summary") or {}
    return html.Div(
        className="qcchem-page qcchem-page--scans",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Aggregate Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Scans", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "A scan control surface for parameter sweeps: the defended curve stays legible, exploratory points remain visible, and the parameter axis is called out as a first-class research control.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Scan", str(model.get("scan_name", "n/a")), "Aggregate sweep"),
                            metric_card("Parameter", str(model.get("parameter_name", "n/a")), "Named control axis"),
                            metric_card("Validated-like points", str(len(validated_points)), "On the defended curve"),
                            metric_card("Exploratory points", str(len(exploratory_points)), "Held out from the defended sweep"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_scan_curve_figure(model), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Validated-like points",
                        [
                            (
                                point["point_label"],
                                f'{point["parameter_value"]} / {point["total_energy"]:.4f} Ha / {point["verification_status"]}',
                            )
                            for point in validated_points
                        ],
                        eyebrow="Defended Sweep",
                    ),
                    detail_card(
                        "Exploratory points",
                        [
                            (
                                point["point_label"],
                                f'{point["parameter_value"]} / {point["total_energy"]:.4f} Ha / {point["verification_status"]}',
                            )
                            for point in exploratory_points
                        ]
                        or [("None", "No exploratory points in this scan aggregate")],
                        eyebrow="Research Scope",
                    ),
                    detail_card(
                        "Sweep posture",
                        [
                            ("Parameter name", str(model.get("parameter_name", "n/a"))),
                            ("Total points", str(summary.get("total_runs", 0))),
                            ("Status counts", str(summary.get("status_counts", {}))),
                            ("Leading point", str(validated_points[0]["point_label"]) if validated_points else "n/a"),
                        ],
                    ),
                    callout_card(
                        "Scan framing",
                        "Scan pages work best when they read like steering surfaces rather than CSV previews, so the chart is centered and the status split stays visible beside the parameter narrative.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_scans_page(sample_scan_model())
