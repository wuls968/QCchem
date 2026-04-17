from __future__ import annotations

from typing import Any

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


def sample_study_model() -> dict[str, Any]:
    validated_runs = [
        {
            "name": "lih_statevector_reference",
            "verification_status": "validated",
            "backend_kind": "statevector",
            "mapping_kind": "bravyi_kitaev",
            "total_energy": -7.8823,
            "absolute_error": 0.0004,
        },
        {
            "name": "mini_comparison_study",
            "verification_status": "validated",
            "backend_kind": "runtime",
            "mapping_kind": "parity",
            "total_energy": -7.8751,
            "absolute_error": 0.0118,
        },
    ]
    exploratory_runs = [
        {
            "name": "lih_puccd_probe",
            "verification_status": "exploratory",
            "backend_kind": "runtime",
            "mapping_kind": "jordan_wigner",
            "total_energy": -7.8619,
            "absolute_error": 0.0214,
        },
        {
            "name": "lih_layout_stress_probe",
            "verification_status": "exploratory",
            "backend_kind": "runtime",
            "mapping_kind": "parity",
            "total_energy": -7.8548,
            "absolute_error": 0.0286,
        },
    ]
    return {
        "study_name": "mini_comparison_study",
        "summary": {
            "total_runs": len(validated_runs) + len(exploratory_runs),
            "status_counts": {"validated": 2, "exploratory": 2},
            "comparison_axes": ["backend_kind", "mapping_kind", "ansatz_family"],
        },
        "validated_runs": validated_runs,
        "exploratory_runs": exploratory_runs,
    }


def _study_energy_figure(model: dict[str, Any]) -> go.Figure:
    validated_runs = model.get("validated_runs") or []
    exploratory_runs = model.get("exploratory_runs") or []
    figure = go.Figure()
    figure.add_bar(
        x=[run["name"] for run in validated_runs],
        y=[run["total_energy"] for run in validated_runs],
        name="Validated-like",
        marker_color="#20334a",
    )
    if exploratory_runs:
        figure.add_bar(
            x=[run["name"] for run in exploratory_runs],
            y=[run["total_energy"] for run in exploratory_runs],
            name="Exploratory",
            marker_color="#c58742",
        )
    figure.update_layout(
        title={"text": "Study energy stack across defended and exploratory runs", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 52},
        barmode="group",
        yaxis_title="Total energy (Hartree)",
        font={"color": "#2d2216"},
        legend={"orientation": "h", "x": 0.02, "y": 1.12},
    )
    return figure


def build_studies_page(model: dict[str, Any]) -> html.Div:
    validated_runs = model.get("validated_runs") or []
    exploratory_runs = model.get("exploratory_runs") or []
    summary = model.get("summary") or {}
    comparison_axes = summary.get("comparison_axes") or []
    return html.Div(
        className="qcchem-page qcchem-page--studies",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Aggregate Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Studies", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "A research-control surface for cross-run comparisons: defended runs stay visible, exploratory probes stay nearby, and the comparison axes are explicit instead of implicit.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Study", str(model.get("study_name", "n/a")), "Aggregate comparison set"),
                            metric_card("Total runs", str(summary.get("total_runs", 0)), "Across all scopes"),
                            metric_card("Validated-like runs", str(len(validated_runs)), "Ready for defended comparison"),
                            metric_card("Exploratory runs", str(len(exploratory_runs)), "Held separate from defended evidence"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_study_energy_figure(model), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Validated-like runs",
                        [
                            (run["name"], f'{run["backend_kind"]} / {run["mapping_kind"]} / {run["total_energy"]:.4f} Ha')
                            for run in validated_runs
                        ],
                        eyebrow="Defended Scope",
                    ),
                    detail_card(
                        "Exploratory runs",
                        [
                            (run["name"], f'{run["backend_kind"]} / {run["mapping_kind"]} / {run["absolute_error"]:.4f} Ha error')
                            for run in exploratory_runs
                        ]
                        or [("None", "No exploratory runs in this aggregate")],
                        eyebrow="Research Scope",
                    ),
                    detail_card(
                        "Comparison axes",
                        [
                            ("Axis count", str(len(comparison_axes))),
                            ("Axes", ", ".join(str(axis) for axis in comparison_axes) or "n/a"),
                            ("Status counts", str(summary.get("status_counts", {}))),
                            ("Lead comparison", "Backend and mapping choices remain jointly visible"),
                        ],
                    ),
                    callout_card(
                        "Study readout",
                        "This page is meant to feel like a campaign console: enough structure to compare runs quickly, enough narrative to remind the reader why exploratory probes are nearby but not mixed into the defended claim.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_studies_page(sample_study_model())
