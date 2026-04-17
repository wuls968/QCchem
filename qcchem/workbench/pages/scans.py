from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


def sample_scan_model() -> dict[str, object]:
    points = [
        {"point_label": "point_00_0.500", "parameter_value": 0.5, "total_energy": -1.0551597944706248, "verification_status": "validated"},
        {"point_label": "point_01_0.735", "parameter_value": 0.735, "total_energy": -1.1373060357534048, "verification_status": "validated"},
        {"point_label": "point_02_1.000", "parameter_value": 1.0, "total_energy": -1.101150330232619, "verification_status": "validated"},
    ]
    return {
        "scan_name": "h2_short_scan",
        "parameter_name": "bond_length",
        "summary": {"total_runs": len(points), "status_counts": {"validated": 3}, "comparison_axes": ["bond_length"]},
        "points": points,
    }


def _scan_curve_figure(model: dict[str, object]) -> go.Figure:
    points = list(model.get("points") or [])
    figure = go.Figure()
    figure.add_scatter(
        x=[point["parameter_value"] for point in points],
        y=[point["total_energy"] for point in points],
        mode="lines+markers",
        line={"color": "#20334a", "width": 3},
        marker={"size": 10, "color": "#20334a"},
        customdata=[point["point_label"] for point in points],
        hovertemplate="%{customdata}<br>%{x:.3f}<br>%{y:.6f} Ha<extra></extra>",
    )
    figure.update_layout(
        title={"text": "Energy sweep across the current scan path", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title=str(model.get("parameter_name", "parameter")),
        yaxis_title="Total energy (Hartree)",
        font={"color": "#2d2216"},
    )
    return figure


def build_scans_page(model: dict[str, object]) -> html.Div:
    points = list(model.get("points") or [])
    summary = model.get("summary") or {}
    best_point = min(points, key=lambda point: float(point.get("total_energy") or 0.0)) if points else {}

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
                        "A scan control surface for parameter sweeps: the defended curve stays legible, point labels stay visible, and the parameter axis remains a first-class research control.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Scan", str(model.get("scan_name", "n/a")), "Aggregate sweep"),
                            metric_card("Parameter", str(model.get("parameter_name", "n/a")), "Named control axis"),
                            metric_card("Validated points", str(sum(1 for point in points if point.get("verification_status") == "validated")), "On the defended curve"),
                            metric_card("Total points", str(summary.get("total_runs", len(points))), "Registered scan samples"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_scan_curve_figure(model), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Scan points",
                        [
                            (
                                point["point_label"],
                                f'{point["parameter_value"]} / {point["total_energy"]:.4f} Ha / {point["verification_status"]}',
                            )
                            for point in points
                        ],
                        eyebrow="Defended Sweep",
                    ),
                    detail_card(
                        "Sweep posture",
                        [
                            ("Parameter name", str(model.get("parameter_name", "n/a"))),
                            ("Total points", str(summary.get("total_runs", 0))),
                            ("Status counts", str(summary.get("status_counts", {}))),
                            ("Leading point", str(best_point.get("point_label", "n/a"))),
                        ],
                        eyebrow="Research Scope",
                    ),
                    callout_card(
                        "Scan framing",
                        "Scan pages work best when they read like steering surfaces rather than CSV previews, so the chart is centered and the path remains chemically legible.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_scans_page(sample_scan_model())
