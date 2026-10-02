from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme, case_label
from qcchem.workbench.theme import THEME
from qcchem.workbench.aggregates import energy_label, finite_value


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
        "evidence_summary": {
            "primary_scientific_claim": "This study supports a validated comparison between exact and variational H2 local workflows.",
            "trust_tier": "validated",
            "recommended_action": "promote_validated_result",
        },
    }


def _study_energy_figure(model: dict[str, object]) -> go.Figure:
    run_records = list(model.get("run_records") or [])
    statuses = [str(run.get("verification_status") or "unknown") for run in run_records]
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_bar(
        x=[run["name"] for run in run_records],
        y=[finite_value(run.get("total_energy")) for run in run_records],
        marker={
            "color": [
                THEME["accent"]["deep_blue"] if status == "validated" else THEME["accent"]["copper"] if status == "exploratory" else THEME["status"]["unstable"]
                for status in statuses
            ],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f'{finite_value(run.get("total_energy")):.4f}' if finite_value(run.get("total_energy")) is not None else "Unavailable" for run in run_records],
        textposition="outside",
        customdata=statuses,
        hovertemplate="%{x}<br>Total energy %{y:.6f} Ha<br>Status %{customdata}<extra></extra>",
        name="Total energy",
        secondary_y=False,
    )
    figure.add_scatter(
        x=[run["name"] for run in run_records],
        y=[finite_value(run.get("absolute_error")) for run in run_records],
        connectgaps=False,
        mode="lines+markers",
        line={"color": THEME["accent"]["sage"], "width": 2.5},
        marker={"size": 8, "color": THEME["accent"]["sage"]},
        hovertemplate="%{x}<br>Absolute error %{y:.6f} Ha<extra></extra>",
        name="Absolute error",
        secondary_y=True,
    )
    apply_chart_theme(
        figure,
        title="Study energy stack across registered run records",
        xaxis_title="Run record",
        yaxis_title="Total energy (Hartree)",
        yaxis2_title="Absolute error (Hartree)",
        height=430,
        legend=True,
    )
    figure.update_xaxes(ticktext=[case_label(run["name"]) for run in run_records], tickvals=[run["name"] for run in run_records])
    figure.update_layout(legend={"orientation": "h", "x": 0, "y": 1.18})
    return figure


def build_studies_page(model: dict[str, object]) -> html.Div:
    run_records = list(model.get("run_records") or [])
    summary = model.get("summary") or {}
    evidence_summary = model.get("evidence_summary") or {}
    comparison_axes = summary.get("comparison_axes") or []
    measured = [run for run in run_records if finite_value(run.get("total_energy")) is not None]
    best_record = min(measured, key=lambda run: run["total_energy"]) if measured else {}
    validated_runs = sum(1 for run in run_records if run.get("verification_status") == "validated")
    return html.Div(
        className="qcchem-page qcchem-page--studies",
        children=[
            html.Section(
                className="qcchem-card qcchem-studies__hero",
                children=[
                    html.P("Aggregate atlas", className="qcchem-card-eyebrow"),
                    html.H1("Studies", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        str(model.get("description") or "Compare recorded energies and errors alongside their backend, mapping, and execution policy."),
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Study", str(model.get("study_name", "n/a")), "Aggregate comparison set"),
                            metric_card("Total runs", str(summary.get("total_runs", 0)), "Across all scopes"),
                            status_card("Validated runs", str(validated_runs), "Ready for defended comparison", tone="validated" if validated_runs else "informational"),
                            metric_card("Comparison axes", str(len(comparison_axes)), ", ".join(str(axis) for axis in comparison_axes) or "n/a"),
                            status_card(
                                "Recommended action",
                                str(evidence_summary.get("recommended_action", "compare_against_best_evidence")),
                                str(evidence_summary.get("primary_scientific_claim", "Evidence-guided study next step.")),
                                tone="validated" if evidence_summary.get("trust_tier") == "validated" else "informational",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-studies__chart",
                children=[
                    html.P("Campaign trace", className="qcchem-card-eyebrow"),
                    html.H2("Study energy stack", className="qcchem-card-title"),
                    html.P(
                        "Missing energy or error values remain unavailable. Compare energies only for compatible systems and conventions.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_study_energy_figure(model), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    detail_card(
                        "Run records",
                        [
                            (run["name"], f'{run.get("backend_kind", "n/a")} / {run.get("mapping_kind", "n/a")} / {run.get("verification_status", "n/a")}')
                            for run in run_records
                        ],
                        eyebrow="Defended scope",
                    ),
                    detail_card(
                        "Study posture",
                        [
                            ("Axes", ", ".join(str(axis) for axis in comparison_axes) or "n/a"),
                            ("Status counts", str(summary.get("status_counts", {}))),
                            ("Lowest energy record", str(best_record.get("name", "Unavailable"))),
                            ("Lowest recorded energy", energy_label(best_record.get("total_energy"))),
                            ("Its absolute error", energy_label(best_record.get("absolute_error"))),
                        ],
                    ),
                    callout_card(
                        "Interpretation rule",
                        "The lowest recorded energy is not automatically the most accurate result. Check the baseline, error, and comparison axes before selecting a workflow.",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    from qcchem.workbench.pages.aggregate_browser import aggregate_layout

    return aggregate_layout("study")
