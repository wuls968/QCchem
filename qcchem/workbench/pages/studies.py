from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme, case_label
from qcchem.workbench.theme import THEME


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
        y=[run["total_energy"] for run in run_records],
        marker={
            "color": [
                THEME["accent"]["deep_blue"] if status == "validated" else THEME["accent"]["copper"] if status == "exploratory" else THEME["status"]["unstable"]
                for status in statuses
            ],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f'{float(run.get("total_energy") or 0.0):.4f}' for run in run_records],
        textposition="outside",
        customdata=statuses,
        hovertemplate="%{x}<br>Total energy %{y:.6f} Ha<br>Status %{customdata}<extra></extra>",
        name="Total energy",
        secondary_y=False,
    )
    figure.add_scatter(
        x=[run["name"] for run in run_records],
        y=[float(run.get("absolute_error") or 0.0) for run in run_records],
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
    best_record = min(run_records, key=lambda run: float(run.get("total_energy") or 0.0)) if run_records else {}
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
                        "A study page should read like a campaign review. It needs to preserve the comparison axes, show the best record clearly, and still make it obvious what kind of comparison the reader is actually making.",
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
                        "Use the chart to identify the best run quickly, but keep the axes in view so the result remains attached to the conditions that produced it.",
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
                            ("Best run", str(best_record.get("name", "n/a"))),
                            ("Best total energy", f'{float(best_record.get("total_energy") or 0.0):.6f} Ha'),
                            ("Best absolute error", f'{float(best_record.get("absolute_error") or 0.0):.6f} Ha'),
                        ],
                    ),
                    callout_card(
                        "Interpretation rule",
                        "Read a study in two passes: first identify the strongest record, then verify that the comparison axes explain why that record is strongest instead of treating the study like a flat list of runs.",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_studies_page(sample_study_model())
