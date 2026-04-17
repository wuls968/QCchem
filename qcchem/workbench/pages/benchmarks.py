from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


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
    }


def _status_band_figure(model: dict[str, object]) -> go.Figure:
    summary = model.get("summary") or {}
    status_counts = summary.get("status_counts") or {}
    figure = go.Figure()
    figure.add_bar(
        x=list(status_counts.keys()),
        y=list(status_counts.values()),
        marker_color=["#315f4a", "#9a6b3f", "#7a3f3f"][: len(status_counts)],
    )
    figure.update_layout(
        title={"text": "Benchmark status bands across validated, exploratory, and unstable scope", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title="Status band",
        yaxis_title="Case count",
        font={"color": "#2d2216"},
    )
    return figure


def build_benchmarks_page(model: dict[str, object]) -> html.Div:
    summary = model.get("summary") or {}
    status_counts = summary.get("status_counts") or {}
    cases = list(model.get("cases") or [])
    best_case = min(cases, key=lambda case: float(case.get("absolute_error") or 0.0)) if cases else {}

    return html.Div(
        className="qcchem-page qcchem-page--benchmarks",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Aggregate Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Benchmarks", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(str(model.get("description") or ""), className="qcchem-card-note"),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Suite", str(model.get("suite_name", "n/a")), "Benchmark aggregate"),
                            metric_card("Validated", str(status_counts.get("validated", 0)), "Benchmark status band"),
                            metric_card("Exploratory", str(status_counts.get("exploratory", 0)), "Benchmark status band"),
                            metric_card("Unstable", str(status_counts.get("unstable", 0)), "Benchmark status band"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_status_band_figure(model), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Benchmark highlights",
                        [
                            ("Total cases", str(summary.get("total_cases", len(cases)))),
                            ("Best case", str(best_case.get("name", "n/a"))),
                            ("Best absolute error", f'{float(best_case.get("absolute_error") or 0.0):.4f} Ha'),
                            ("Status band split", str(status_counts)),
                        ],
                        eyebrow="Status Bands",
                    ),
                    detail_card(
                        "Higher-risk cases",
                        [
                            (
                                case["name"],
                                f'{case["status"]} / {case["kind"]} / {float(case.get("absolute_error") or 0.0):.4f} Ha',
                            )
                            for case in cases
                            if case.get("status") in {"exploratory", "unstable"}
                        ]
                        or [("None", "No exploratory or unstable cases in this benchmark aggregate")],
                        eyebrow="Research Scope",
                    ),
                    callout_card(
                        "Benchmark framing",
                        "The page keeps status bands explicit because a benchmark suite loses credibility quickly when validated, exploratory, and unstable cases are visually flattened into one bucket.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_benchmarks_page(sample_benchmark_suite_model())
