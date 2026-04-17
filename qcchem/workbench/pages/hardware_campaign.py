from __future__ import annotations

from typing import Any

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary
from qcchem.workbench.components.cards import callout_card, detail_card, metric_card


def sample_hardware_campaign_model() -> dict[str, Any]:
    payload = {
        "suite_name": "hardware_calibration_suite_v1",
        "summary": {
            "total_cases": 4,
            "runtime_evidence_status_counts": {"retrieved": 2, "submitted": 1, "failed": 1},
        },
        "cases": [
            {
                "name": "h2_runtime_hardware_probe_puccd_layout",
                "achieved_error": 0.0137,
                "meets_chemical_accuracy": False,
                "backend_name": "ibm_kyiv",
                "runtime_evidence_status": "retrieved",
                "runtime_usage_seconds": 132.0,
                "transpiled_depth": 146,
                "transpiled_two_qubit_gate_count": 42,
                "layout_strategy": "sabre",
                "hardware_verified": True,
            },
            {
                "name": "h2_runtime_hardware_probe_ca_layout",
                "achieved_error": 0.0186,
                "meets_chemical_accuracy": False,
                "backend_name": "ibm_kyiv",
                "runtime_evidence_status": "retrieved",
                "runtime_usage_seconds": 141.2,
                "transpiled_depth": 153,
                "transpiled_two_qubit_gate_count": 44,
                "layout_strategy": "noise_adaptive",
                "hardware_verified": True,
            },
            {
                "name": "h2_runtime_hardware_probe_puccd_layout_highshots",
                "achieved_error": 0.0221,
                "meets_chemical_accuracy": False,
                "backend_name": "ibm_kyiv",
                "runtime_evidence_status": "submitted",
                "runtime_usage_seconds": 166.4,
                "transpiled_depth": 149,
                "transpiled_two_qubit_gate_count": 45,
                "layout_strategy": "sabre",
                "hardware_verified": False,
            },
            {
                "name": "h2_runtime_hardware_probe_puccd_layout_mitigated",
                "achieved_error": 0.0314,
                "meets_chemical_accuracy": False,
                "backend_name": "ibm_kyiv",
                "runtime_evidence_status": "failed",
                "runtime_usage_seconds": 0.0,
                "transpiled_depth": 172,
                "transpiled_two_qubit_gate_count": 51,
                "layout_strategy": "mitigated",
                "hardware_verified": False,
            },
        ],
    }
    return build_hardware_campaign_summary(payload)


def _select_best_retrieved_case(cases: list[dict[str, Any]]) -> dict[str, Any]:
    retrieved_cases = [
        case
        for case in cases
        if case.get("achieved_error") is not None
        and str(case.get("runtime_evidence_status") or "").lower() in {"retrieved", "retrieved_result"}
    ]
    if retrieved_cases:
        return min(retrieved_cases, key=lambda case: float(case.get("achieved_error") or 0.0))

    ranked_cases = [case for case in cases if case.get("achieved_error") is not None]
    if ranked_cases:
        return min(ranked_cases, key=lambda case: float(case.get("achieved_error") or 0.0))
    return {}


def _runtime_error_figure(model: dict[str, Any]) -> go.Figure:
    cases = sorted(model.get("cases") or [], key=lambda case: float(case.get("achieved_error") or 0.0))
    figure = go.Figure()
    figure.add_bar(
        x=[case.get("name") for case in cases],
        y=[case.get("achieved_error") for case in cases],
        marker_color=["#20334a", "#46607a", "#93a18a", "#c58742"][: len(cases)],
    )
    target = float(model.get("chemical_accuracy_target_hartree") or 0.0016)
    figure.add_hline(
        y=target,
        line_dash="dash",
        line_color="#9a6b3f",
        annotation_text="Chemical accuracy target",
        annotation_position="top left",
    )
    figure.update_layout(
        title={"text": "Runtime error ladder across the current hardware campaign", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 52},
        yaxis_title="Achieved error (Hartree)",
        font={"color": "#2d2216"},
    )
    return figure


def _runtime_usage_figure(model: dict[str, Any]) -> go.Figure:
    cases = model.get("cases") or []
    figure = go.Figure()
    figure.add_scatter(
        x=[case.get("transpiled_depth") for case in cases],
        y=[case.get("runtime_usage_seconds") for case in cases],
        mode="markers+text",
        text=[case.get("name") for case in cases],
        textposition="top center",
        marker={"size": 13, "color": "#20334a"},
    )
    figure.update_layout(
        title={"text": "Runtime usage versus compiled depth for campaign cases", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title="Transpiled depth",
        yaxis_title="Runtime usage (s)",
        font={"color": "#2d2216"},
    )
    return figure


def build_hardware_campaign_page(model: dict[str, Any]) -> html.Div:
    cases = list(model.get("cases") or [])
    best_case = _select_best_retrieved_case(cases)
    recommended_case_name = str(best_case.get("name") or model.get("recommended_case_name") or "n/a")
    worst_case = model.get("worst_case") or {}
    status_counts = model.get("runtime_evidence_status_counts") or {}
    target = float(model.get("chemical_accuracy_target_hartree") or 0.0016)
    best_distance_to_target = float(best_case.get("achieved_error") or 0.0) - target if best_case else 0.0
    return html.Div(
        className="qcchem-page qcchem-page--hardware-campaign",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Aggregate Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Hardware Campaign", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "A runtime campaign control surface that ranks cases by achieved error, surfaces the current best retrieved evidence, and keeps runtime-evidence status visible while Task 7 wiring is still pending.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Suite", str(model.get("suite_name", "n/a")), "Hardware runtime campaign"),
                            metric_card("Best retrieved case", str(best_case.get("name", "n/a")), f'{float(best_case.get("achieved_error") or 0.0):.4f} Ha'),
                            metric_card("Runtime evidence status", str(status_counts), "Retrieved / submitted / failed"),
                            metric_card("Recommended case", recommended_case_name, "Closest defended runtime result"),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "minmax(0, 1.15fr) minmax(260px, 0.85fr)", "gap": "1rem"},
                children=[
                    html.Section(className="qcchem-card", children=[dcc.Graph(figure=_runtime_error_figure(model), config={"displayModeBar": False})]),
                    detail_card(
                        "Best retrieved case",
                        [
                            ("Case", str(best_case.get("name", "n/a"))),
                            ("Achieved error", f'{float(best_case.get("achieved_error") or 0.0):.4f} Ha'),
                            ("Backend", str(best_case.get("backend_name", "n/a"))),
                            ("Layout strategy", str(best_case.get("layout_strategy", "n/a"))),
                            ("Hardware verified", str(best_case.get("hardware_verified", False))),
                        ],
                        eyebrow="Best Case",
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "minmax(0, 1.15fr) minmax(260px, 0.85fr)", "gap": "1rem"},
                children=[
                    html.Section(className="qcchem-card", children=[dcc.Graph(figure=_runtime_usage_figure(model), config={"displayModeBar": False})]),
                    detail_card(
                        "Campaign posture",
                        [
                            ("Total cases", str(model.get("total_cases", 0))),
                            ("Best distance to target", f"{best_distance_to_target:.4f} Ha"),
                            ("Worst case", str(worst_case.get("name", "n/a"))),
                            ("Worst error", f'{float(worst_case.get("achieved_error") or 0.0):.4f} Ha'),
                        ],
                        eyebrow="Runtime Evidence",
                    ),
                ],
            ),
            callout_card(
                "Campaign readout",
                "The page treats the campaign like a ranking problem: which case is currently the cleanest retrieved evidence, how far is it from chemical accuracy, and which runtime status buckets still gate the claim.",
                accent="copper",
            ),
        ],
    )


def layout() -> html.Div:
    return build_hardware_campaign_page(sample_hardware_campaign_model())
