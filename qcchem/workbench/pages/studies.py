from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


def sample_study_model() -> dict[str, object]:
    run_records = [
        {
            "name": "h2_exact_reference",
            "verification_status": "validated",
            "backend_kind": "statevector",
            "mapping_kind": "jordan_wigner",
            "policy_name": "benchmark",
            "total_energy": -1.1373060357534057,
            "absolute_error": 0.0,
        },
        {
            "name": "h2_variational_reference",
            "verification_status": "validated",
            "backend_kind": "statevector",
            "mapping_kind": "jordan_wigner",
            "policy_name": "benchmark",
            "total_energy": -1.1373060346305747,
            "absolute_error": 0.000001,
        },
    ]
    return {
        "study_name": "mini_comparison_study",
        "description": "Minimal study comparing exact and variational H2 workflows with shared reporting semantics.",
        "summary": {
            "total_runs": len(run_records),
            "status_counts": {"validated": 2},
            "comparison_axes": ["backend.kind", "mapping.kind", "policy.name"],
        },
        "run_records": run_records,
    }


def _study_energy_figure(model: dict[str, object]) -> go.Figure:
    run_records = list(model.get("run_records") or [])
    statuses = [str(run.get("verification_status") or "unknown") for run in run_records]
    figure = go.Figure()
    figure.add_bar(
        x=[run["name"] for run in run_records],
        y=[run["total_energy"] for run in run_records],
        marker_color=[
            "#20334a" if status == "validated" else "#c58742" if status == "exploratory" else "#7a3f3f"
            for status in statuses
        ],
        customdata=statuses,
        hovertemplate="%{x}<br>Total energy %{y:.6f} Ha<br>Status %{customdata}<extra></extra>",
    )
    figure.update_layout(
        title={"text": "Study energy stack across registered run records", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 56},
        yaxis_title="Total energy (Hartree)",
        font={"color": "#2d2216"},
        xaxis_title="Run record",
    )
    return figure


def build_studies_page(model: dict[str, object]) -> html.Div:
    run_records = list(model.get("run_records") or [])
    summary = model.get("summary") or {}
    comparison_axes = summary.get("comparison_axes") or []
    best_record = min(run_records, key=lambda run: float(run.get("total_energy") or 0.0)) if run_records else {}

    return html.Div(
        className="qcchem-page qcchem-page--studies",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Aggregate Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Studies", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(str(model.get("description") or ""), className="qcchem-card-note"),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Study", str(model.get("study_name", "n/a")), "Aggregate comparison set"),
                            metric_card("Total runs", str(summary.get("total_runs", 0)), "Across all scopes"),
                            metric_card("Validated runs", str(sum(1 for run in run_records if run.get("verification_status") == "validated")), "Ready for defended comparison"),
                            metric_card("Comparison axes", str(len(comparison_axes)), "Explicit cross-run dimensions"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_study_energy_figure(model), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Run records",
                        [
                            (
                                run["name"],
                                f'{run.get("backend_kind", "n/a")} / {run.get("mapping_kind", "n/a")} / {run.get("verification_status", "n/a")}',
                            )
                            for run in run_records
                        ],
                        eyebrow="Defended Scope",
                    ),
                    detail_card(
                        "Study posture",
                        [
                            ("Axes", ", ".join(str(axis) for axis in comparison_axes) or "n/a"),
                            ("Status counts", str(summary.get("status_counts", {}))),
                            ("Best run", str(best_record.get("name", "n/a"))),
                            ("Best total energy", f'{float(best_record.get("total_energy") or 0.0):.6f} Ha'),
                        ],
                    ),
                    callout_card(
                        "Study readout",
                        "This page is meant to feel like a campaign console: enough structure to compare runs quickly, enough narrative to remind the reader which comparison axes are carrying the study.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_studies_page(sample_study_model())
