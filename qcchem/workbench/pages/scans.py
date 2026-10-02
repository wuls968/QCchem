from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.theme import THEME
from qcchem.workbench.aggregates import energy_label, finite_value


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
        "evidence_summary": {
            "primary_scientific_claim": "The H2 short scan defines a validated minimum-energy path across the defended bond-length window.",
            "trust_tier": "validated",
            "recommended_action": "promote_validated_result",
        },
    }


def _scan_curve_figure(model: dict[str, object]) -> go.Figure:
    points = list(model.get("points") or [])
    measured = [point for point in points if finite_value(point.get("total_energy")) is not None
                and finite_value(point.get("parameter_value")) is not None]
    best_point = min(measured, key=lambda point: point["total_energy"]) if measured else {}
    figure = go.Figure()
    figure.add_scatter(
        x=[finite_value(point.get("parameter_value")) for point in points],
        y=[finite_value(point.get("total_energy")) for point in points],
        connectgaps=False,
        mode="lines+markers",
        line={"color": THEME["accent"]["deep_blue"], "width": 3},
        marker={"size": 10, "color": THEME["accent"]["deep_blue"], "line": {"color": THEME["surface"]["paper"], "width": 1.4}},
        customdata=[point.get("point_label", "Unnamed point") for point in points],
        hovertemplate="%{customdata}<br>%{x:.3f}<br>%{y:.6f} Ha<extra></extra>",
    )
    if best_point:
        figure.add_scatter(
            x=[best_point["parameter_value"]],
            y=[best_point["total_energy"]],
            mode="markers+text",
            marker={
                "size": 15,
                "color": THEME["surface"]["card"],
                "line": {"color": THEME["accent"]["copper"], "width": 2.4},
                "symbol": "diamond",
            },
            text=["Lowest sampled energy"],
            textposition="top center",
            hovertemplate="Lowest sampled energy<br>%{x:.3f}<br>%{y:.6f} Ha<extra></extra>",
            showlegend=False,
        )
    apply_chart_theme(
        figure,
        title="Energy sweep across the current scan path",
        xaxis_title=str(model.get("parameter_name", "parameter")) + (f" ({model['parameter_unit']})" if model.get("parameter_unit") else ""),
        yaxis_title="Total energy (Hartree)",
        height=430,
    )
    return figure


def build_scans_page(model: dict[str, object]) -> html.Div:
    points = list(model.get("points") or [])
    summary = model.get("summary") or {}
    evidence_summary = model.get("evidence_summary") or {}
    measured = [point for point in points if finite_value(point.get("total_energy")) is not None
                and finite_value(point.get("parameter_value")) is not None]
    best_point = min(measured, key=lambda point: point["total_energy"]) if measured else {}
    validated_points = sum(1 for point in points if point.get("verification_status") == "validated")
    return html.Div(
        className="qcchem-page qcchem-page--scans",
        children=[
            html.Section(
                className="qcchem-card qcchem-scans__hero",
                children=[
                    html.P("Aggregate atlas", className="qcchem-card-eyebrow"),
                    html.H1("Scans", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "Review sampled energies, point validation, and scan coverage. The lowest sampled point does not establish a converged equilibrium geometry.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Scan", str(model.get("scan_name", "n/a")), "Aggregate sweep"),
                            metric_card("Parameter", str(model.get("parameter_name", "n/a")), "Named control axis"),
                            status_card("Validated points", str(validated_points), "On the defended curve", tone="validated" if validated_points else "informational"),
                            metric_card("Total points", str(summary.get("total_runs", len(points))), "Registered scan samples"),
                            status_card(
                                "Recommended action",
                                str(evidence_summary.get("recommended_action", "compare_against_best_evidence")),
                                str(evidence_summary.get("primary_scientific_claim", "Use the defended sweep to decide whether broader scanning is worth it.")),
                                tone="validated" if evidence_summary.get("trust_tier") == "validated" else "informational",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-scans__chart",
                children=[
                    html.P("Energy path", className="qcchem-card-eyebrow"),
                    html.H2("Scan curve", className="qcchem-card-title"),
                    html.P(
                        "Gaps indicate unavailable values. Only committed points appear for an incomplete scan.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_scan_curve_figure(model), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    detail_card(
                        "Scan points",
                        [
                            (point.get("point_label", "Unnamed point"), f'{point.get("parameter_value") if finite_value(point.get("parameter_value")) is not None else "Unavailable"} / {energy_label(point.get("total_energy"))} / {point.get("verification_status", "unknown")}')
                            for point in points
                        ],
                        eyebrow="Defended sweep",
                    ),
                    detail_card(
                        "Sweep posture",
                        [
                            ("Parameter name", str(model.get("parameter_name", "n/a"))),
                            ("Total points", str(summary.get("total_runs", 0))),
                            ("Status counts", str(summary.get("status_counts", {}))),
                            ("Lowest sampled point", str(best_point.get("point_label", "Unavailable"))),
                            ("Lowest sampled energy", energy_label(best_point.get("total_energy"))),
                            ("Parameter unit", str(model.get("parameter_unit") or "Not recorded")),
                        ],
                        eyebrow="Research scope",
                    ),
                    callout_card(
                        "Interpretation rule",
                        "Inspect point status, parameter units, and sampling coverage before drawing conclusions from the curve. A sparse sweep alone does not prove convergence.",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    from qcchem.workbench.pages.aggregate_browser import aggregate_layout

    return aggregate_layout("scan")
