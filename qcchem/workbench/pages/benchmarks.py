from __future__ import annotations

from typing import Any

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


def sample_benchmark_suite_model() -> dict[str, Any]:
    validated_like_cases = [
        {
            "name": "lih_exact_reference",
            "kind": "exact",
            "status": "validated",
            "expected_status": "validated",
            "metrics": {"wall_time_seconds": 2.4, "achieved_error": 0.0001, "measurement_group_count": 0},
        },
        {
            "name": "lih_runtime_probe",
            "kind": "runtime",
            "status": "validated",
            "expected_status": "validated",
            "metrics": {"wall_time_seconds": 131.8, "achieved_error": 0.0118, "measurement_group_count": 6},
        },
        {
            "name": "lih_compression_df",
            "kind": "compression",
            "status": "calibrated",
            "expected_status": "validated",
            "metrics": {"wall_time_seconds": 14.6, "achieved_error": 0.0093, "measurement_group_count": 4},
        },
    ]
    exploratory_cases = [
        {
            "name": "h2_vqd_probe",
            "kind": "excited_state",
            "status": "exploratory",
            "expected_status": "exploratory",
            "metrics": {"wall_time_seconds": 22.5, "achieved_error": 0.0274, "measurement_group_count": 5},
        },
        {
            "name": "lih_layout_probe",
            "kind": "runtime",
            "status": "exploratory",
            "expected_status": "exploratory",
            "metrics": {"wall_time_seconds": 148.0, "achieved_error": 0.0321, "measurement_group_count": 8},
        },
    ]
    return {
        "suite_name": "mini_suite",
        "summary": {
            "total_cases": len(validated_like_cases) + len(exploratory_cases),
            "status_counts": {"validated": 2, "calibrated": 1, "exploratory": 2},
        },
        "validated_like_cases": validated_like_cases,
        "exploratory_cases": exploratory_cases,
    }


def _status_band_figure(model: dict[str, Any]) -> go.Figure:
    summary = model.get("summary") or {}
    status_counts = summary.get("status_counts") or {}
    figure = go.Figure()
    figure.add_bar(
        x=list(status_counts.keys()),
        y=list(status_counts.values()),
        marker_color=["#20334a", "#46607a", "#c58742"][: len(status_counts)],
    )
    figure.update_layout(
        title={"text": "Benchmark status bands across validated-like and exploratory scope", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title="Status band",
        yaxis_title="Case count",
        font={"color": "#2d2216"},
    )
    return figure


def build_benchmarks_page(model: dict[str, Any]) -> html.Div:
    validated_like_cases = model.get("validated_like_cases") or []
    exploratory_cases = model.get("exploratory_cases") or []
    summary = model.get("summary") or {}
    status_counts = summary.get("status_counts") or {}
    return html.Div(
        className="qcchem-page qcchem-page--benchmarks",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Aggregate Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Benchmarks", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "A benchmark control surface that keeps status bands visible, separates defended cases from exploratory work, and highlights how much of the suite is truly ready to anchor a claim.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Suite", str(model.get("suite_name", "n/a")), "Benchmark aggregate"),
                            metric_card("Validated", str(status_counts.get("validated", 0)), "Benchmark status band"),
                            metric_card("Calibrated", str(status_counts.get("calibrated", 0)), "Benchmark status band"),
                            metric_card("Exploratory", str(status_counts.get("exploratory", 0)), "Benchmark status band"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_status_band_figure(model), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Validated-like cases",
                        [
                            (
                                case["name"],
                                f'{case["status"]} / {case["kind"]} / {case["metrics"].get("achieved_error", 0.0):.4f} Ha',
                            )
                            for case in validated_like_cases
                        ],
                        eyebrow="Status Bands",
                    ),
                    detail_card(
                        "Exploratory cases",
                        [
                            (
                                case["name"],
                                f'{case["status"]} / {case["kind"]} / {case["metrics"].get("wall_time_seconds", 0.0):.1f} s',
                            )
                            for case in exploratory_cases
                        ]
                        or [("None", "No exploratory cases in this benchmark aggregate")],
                        eyebrow="Research Scope",
                    ),
                    detail_card(
                        "Suite posture",
                        [
                            ("Total cases", str(summary.get("total_cases", 0))),
                            ("Validated-like count", str(len(validated_like_cases))),
                            ("Exploratory count", str(len(exploratory_cases))),
                            ("Status band split", str(status_counts)),
                        ],
                    ),
                    callout_card(
                        "Benchmark framing",
                        "The page keeps status bands explicit because a benchmark suite loses credibility quickly when validated, calibrated, and exploratory cases are visually flattened into one bucket.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_benchmarks_page(sample_benchmark_suite_model())
