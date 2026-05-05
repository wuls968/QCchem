from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.theme import THEME


def sample_benchmark_suite_model() -> dict[str, object]:
    cases = [
        {"name": "h2_exact_reference", "kind": "run", "status": "validated", "absolute_error": 0.0},
        {"name": "lih_exact_reference", "kind": "run", "status": "validated", "absolute_error": 0.0},
        {"name": "lih_active_vqe", "kind": "run", "status": "validated", "absolute_error": 0.0001},
        {"name": "h2o_active_space_exact", "kind": "run", "status": "validated", "absolute_error": 0.0},
        {"name": "jw_bk_consistency", "kind": "consistency", "status": "validated", "absolute_error": 0.0},
        {"name": "optimizer_stability", "kind": "stability", "status": "validated", "absolute_error": 0.0002},
        {"name": "h2_shot_vqe", "kind": "shot", "status": "unstable", "absolute_error": 0.0137},
        {"name": "h2_noisy_local", "kind": "noise", "status": "unstable", "absolute_error": 0.1741},
        {"name": "h2_runtime_ready", "kind": "runtime", "status": "unstable", "absolute_error": 0.0533},
        {"name": "shot_scaling", "kind": "scaling", "status": "unstable", "absolute_error": 0.2673},
    ]
    return {
        "suite_name": "benchmark_suite_v1",
        "description": "QCchem Benchmark Suite v1 covering validated, exploratory, unstable, and noise-aware execution paths.",
        "summary": {"total_cases": len(cases), "status_counts": {"validated": 6, "exploratory": 0, "unstable": 4}},
        "cases": cases,
        "evidence_summary": {
            "primary_scientific_claim": "The benchmark suite currently defends QCchem's local validated scope while isolating unstable runtime-facing paths.",
            "trust_tier": "exploratory",
            "recommended_action": "compare_against_best_evidence",
        },
    }


def _status_band_figure(model: dict[str, object]) -> go.Figure:
    summary = model.get("summary") or {}
    evidence_summary = model.get("evidence_summary") or {}
    status_counts = summary.get("status_counts") or {}
    cases = list(model.get("cases") or [])
    status_order = list(status_counts.keys())
    mean_errors = []
    for status in status_order:
        matching = [float(case.get("absolute_error") or 0.0) for case in cases if case.get("status") == status]
        mean_errors.append(sum(matching) / len(matching) if matching else 0.0)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_bar(
        x=status_order,
        y=list(status_counts.values()),
        marker={
            "color": [THEME["status"]["validated"], THEME["accent"]["copper"], THEME["status"]["unstable"]][: len(status_counts)],
            "line": {"color": THEME["surface"]["paper"], "width": 1.2},
        },
        text=list(status_counts.values()),
        textposition="outside",
        hovertemplate="%{x}: %{y} cases<extra></extra>",
        name="Case count",
        secondary_y=False,
    )
    figure.add_scatter(
        x=status_order,
        y=mean_errors,
        mode="lines+markers",
        line={"color": THEME["accent"]["deep_blue"], "width": 2.5},
        marker={"size": 8, "color": THEME["accent"]["deep_blue"]},
        hovertemplate="%{x}: mean error %{y:.4f} Ha<extra></extra>",
        name="Mean absolute error",
        secondary_y=True,
    )
    apply_chart_theme(
        figure,
        title="Benchmark status bands across validated, exploratory, and unstable scope",
        xaxis_title="Status band",
        yaxis_title="Case count",
        yaxis2_title="Mean absolute error (Hartree)",
        height=410,
        legend=True,
    )
    figure.update_layout(legend={"orientation": "h", "x": 0, "y": 1.18})
    return figure


def build_benchmarks_page(model: dict[str, object]) -> html.Div:
    summary = model.get("summary") or {}
    evidence_summary = model.get("evidence_summary") or {}
    status_counts = summary.get("status_counts") or {}
    cases = list(model.get("cases") or [])
    best_case = min(cases, key=lambda case: float(case.get("absolute_error") or 0.0)) if cases else {}
    return html.Div(
        className="qcchem-page qcchem-page--benchmarks",
        children=[
            html.Section(
                className="qcchem-card qcchem-benchmarks__hero",
                children=[
                    html.P("Aggregate atlas", className="qcchem-card-eyebrow"),
                    html.H1("Benchmarks", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "Benchmark pages define trust. They should make the validated scope obvious, keep exploratory and unstable cases visibly distinct, and prevent the suite from feeling like one flattened list of successful runs.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Suite", str(model.get("suite_name", "n/a")), "Benchmark aggregate"),
                            status_card("Validated", str(status_counts.get("validated", 0)), "Defended benchmark scope", tone="validated"),
                            status_card("Exploratory", str(status_counts.get("exploratory", 0)), "Interesting but not defended", tone="exploratory"),
                            status_card("Unstable", str(status_counts.get("unstable", 0)), "Known weak edge or runtime-limited path", tone="unstable"),
                            status_card(
                                "Recommended action",
                                str(evidence_summary.get("recommended_action", "compare_against_best_evidence")),
                                str(evidence_summary.get("primary_scientific_claim", "Keep benchmark scope aligned with the strongest defended evidence.")),
                                tone="exploratory" if evidence_summary.get("trust_tier") == "exploratory" else "informational",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-benchmarks__chart",
                children=[
                    html.P("Status bands", className="qcchem-card-eyebrow"),
                    html.H2("Benchmark credibility bands", className="qcchem-card-title"),
                    html.P(
                        "Use the band chart to compare not just how many cases exist in each tier, but also how the average error profile shifts as the suite moves from validated toward unstable territory.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_status_band_figure(model), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    detail_card(
                        "Benchmark highlights",
                        [
                            ("Total cases", str(summary.get("total_cases", len(cases)))),
                            ("Best case", str(best_case.get("name", "n/a"))),
                            ("Best absolute error", f'{float(best_case.get("absolute_error") or 0.0):.4f} Ha'),
                            ("Status band split", str(status_counts)),
                        ],
                        eyebrow="Status bands",
                    ),
                    detail_card(
                        "Higher-risk cases",
                        [
                            (case["name"], f'{case["status"]} / {case["kind"]} / {float(case.get("absolute_error") or 0.0):.4f} Ha')
                            for case in cases
                            if case.get("status") in {"exploratory", "unstable"}
                        ]
                        or [("None", "No exploratory or unstable cases in this benchmark aggregate")],
                        eyebrow="Research scope",
                    ),
                    callout_card(
                        "Interpretation rule",
                        "Treat benchmark pages as credibility ledgers: first identify what QCchem can defend today, then inspect exploratory and unstable cases as pressure tests rather than as equal evidence.",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_benchmarks_page(sample_benchmark_suite_model())
