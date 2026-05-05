from __future__ import annotations

from typing import Any

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary
from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme, case_label
from qcchem.workbench.evidence_console import format_action_label
from qcchem.workbench.theme import THEME


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
    status_colors = {
        "retrieved": THEME["status"]["validated"],
        "retrieved_result": THEME["status"]["validated"],
        "submitted": THEME["accent"]["copper"],
        "failed": THEME["status"]["unstable"],
    }
    figure = go.Figure()
    figure.add_bar(
        x=[float(case.get("achieved_error") or 0.0) for case in cases],
        y=[case_label(case.get("name")) for case in cases],
        orientation="h",
        marker={
            "color": [
                status_colors.get(str(case.get("runtime_evidence_status") or "").lower(), THEME["status"]["informational"])
                for case in cases
            ],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f'{float(case.get("achieved_error") or 0.0):.4f} Ha' for case in cases],
        textposition="outside",
        customdata=[
            [
                case.get("name"),
                case.get("backend_name"),
                case.get("runtime_evidence_status"),
                case.get("layout_strategy"),
            ]
            for case in cases
        ],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Achieved error: %{x:.4f} Ha<br>"
            "Backend: %{customdata[1]}<br>"
            "Evidence: %{customdata[2]}<br>"
            "Layout: %{customdata[3]}<extra></extra>"
        ),
    )
    target = float(model.get("chemical_accuracy_target_hartree") or 0.0016)
    figure.add_vrect(x0=0, x1=target, fillcolor="rgba(49, 95, 74, 0.08)", line_width=0)
    figure.add_hline(y=0, line_width=0)
    figure.add_vline(
        x=target,
        line_dash="dash",
        line_color=THEME["accent"]["copper"],
        annotation_text="Chemical accuracy target",
        annotation_position="top right",
    )
    apply_chart_theme(
        figure,
        title="Runtime error ladder across the current hardware campaign",
        xaxis_title="Achieved error (Hartree)",
        yaxis_title="Campaign case",
        height=430,
    )
    figure.update_yaxes(autorange="reversed")
    figure.update_layout(bargap=0.28)
    return figure


def _runtime_usage_figure(model: dict[str, Any]) -> go.Figure:
    cases = model.get("cases") or []
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    status_groups = [
        ("retrieved", THEME["status"]["validated"]),
        ("submitted", THEME["accent"]["copper"]),
        ("failed", THEME["status"]["unstable"]),
    ]
    for status, color in status_groups:
        subset = [case for case in cases if str(case.get("runtime_evidence_status") or "").lower() == status]
        if not subset:
            continue
        figure.add_scatter(
            x=[float(case.get("transpiled_depth") or 0.0) for case in subset],
            y=[float(case.get("runtime_usage_seconds") or 0.0) for case in subset],
            mode="markers",
            marker={
                "size": [10 + float(case.get("transpiled_two_qubit_gate_count") or 0.0) * 0.25 for case in subset],
                "color": color,
                "line": {"color": THEME["surface"]["paper"], "width": 1.4},
                "opacity": 0.92,
            },
            customdata=[
                [
                    case.get("name"),
                    case.get("layout_strategy"),
                    case.get("transpiled_two_qubit_gate_count"),
                    case.get("runtime_usage_seconds"),
                ]
                for case in subset
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Depth: %{x:.0f}<br>"
                "Runtime usage: %{y:.1f} s<br>"
                "2Q gates: %{customdata[2]}<br>"
                "Layout: %{customdata[1]}<extra></extra>"
            ),
            name=status.title(),
            secondary_y=False,
        )
    figure.add_scatter(
        x=[float(case.get("transpiled_depth") or 0.0) for case in cases],
        y=[float(case.get("achieved_error") or 0.0) for case in cases],
        mode="lines+markers",
        line={"color": THEME["accent"]["deep_blue"], "width": 2.2, "dash": "dot"},
        marker={"size": 7, "color": THEME["accent"]["deep_blue"]},
        hovertemplate="Error trace: %{y:.4f} Ha at depth %{x:.0f}<extra></extra>",
        name="Achieved error",
        secondary_y=True,
    )
    best_case = _select_best_retrieved_case(list(cases))
    if best_case:
        figure.add_annotation(
            x=float(best_case.get("transpiled_depth") or 0.0),
            y=float(best_case.get("runtime_usage_seconds") or 0.0),
            text=f"Best retrieved<br>{case_label(best_case.get('name'))}",
            showarrow=True,
            arrowcolor=THEME["accent"]["deep_blue"],
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=THEME["surface"]["line"],
            borderwidth=1,
            ax=54,
            ay=-38,
            font={"size": 11, "color": THEME["text"]["secondary"]},
        )
    apply_chart_theme(
        figure,
        title="Runtime usage versus compiled depth for campaign cases",
        xaxis_title="Transpiled depth",
        yaxis_title="Runtime usage (s)",
        yaxis2_title="Achieved error (Hartree)",
        height=430,
        legend=True,
    )
    figure.update_layout(legend={"orientation": "h", "x": 0, "y": 1.18})
    return figure


def build_hardware_campaign_page(model: dict[str, Any]) -> html.Div:
    cases = list(model.get("cases") or [])
    best_case = _select_best_retrieved_case(cases)
    recommended_case_name = str(best_case.get("name") or model.get("recommended_case_name") or "n/a")
    worst_case = model.get("worst_case") or {}
    status_counts = model.get("runtime_evidence_status_counts") or {}
    evidence_summary = model.get("evidence_summary") or {}
    decision_worthiness = model.get("decision_worthiness") or {}
    budget_action = decision_worthiness.get("recommended_action") or evidence_summary.get("recommended_action") or "pause"
    target = float(model.get("chemical_accuracy_target_hartree") or 0.0016)
    best_distance_to_target = float(best_case.get("achieved_error") or 0.0) - target if best_case else 0.0
    hardware_optimization = model.get("hardware_optimization") or {}
    empirical_best_attempt = hardware_optimization.get("empirical_best_attempt") or model.get("empirical_best_attempt") or {}
    prior_reference = (
        hardware_optimization.get("best_existing_reference_summary")
        or model.get("best_existing_reference_summary")
        or {}
    )
    optimization_delta = hardware_optimization.get("runtime_accuracy_delta_vs_best_existing")
    if optimization_delta is None:
        optimization_delta = model.get("runtime_accuracy_delta_vs_best_existing")

    def _tone(status: object) -> str:
        normalized = str(status or "").lower()
        if normalized in {"retrieved", "retrieved_result", "passed", "validated"}:
            return "validated"
        if normalized in {"submitted", "queued", "pending"}:
            return "exploratory"
        if normalized in {"failed", "error", "unstable"}:
            return "unstable"
        return "informational"

    return html.Div(
        className="qcchem-page qcchem-page--hardware-campaign",
        children=[
            html.Section(
                className="qcchem-card qcchem-hardware__hero",
                children=[
                    html.P("Aggregate atlas", className="qcchem-card-eyebrow"),
                    html.H1("Hardware Campaign", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "Hardware evidence should stay comparative and restrained. This page ranks cases by achieved error, isolates the best retrieved evidence, and keeps runtime status separate from scientific quality.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Suite", str(model.get("suite_name", "n/a")), "Hardware runtime campaign"),
                            metric_card("Best retrieved case", str(best_case.get("name", "n/a")), f'{float(best_case.get("achieved_error") or 0.0):.4f} Ha'),
                            status_card("Runtime evidence status", str(status_counts), "Retrieved / submitted / failed", tone="informational"),
                            status_card(
                                "Closest retrieved evidence",
                                recommended_case_name,
                                f"distance to target: {best_distance_to_target:.4f} Ha",
                                tone=_tone(best_case.get("runtime_evidence_status")),
                            ),
                            status_card(
                                "Recommended action",
                                str(evidence_summary.get("recommended_action", decision_worthiness.get("recommended_action", "pause"))),
                                str(evidence_summary.get("primary_scientific_claim", "Use retrieved runtime evidence to decide whether additional budget is justified.")),
                                tone=_tone(evidence_summary.get("trust_tier")),
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-hardware__budget-decision",
                children=[
                    html.P("Reality boundary", className="qcchem-card-eyebrow"),
                    html.H2("Budget Decision", className="qcchem-card-title"),
                    html.P(
                        "Treat hardware minutes as a scarce calibration instrument. This block separates the best retrieved runtime evidence from the question of whether another controlled probe is worth the budget.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            status_card(
                                "Recommended budget action",
                                format_action_label(budget_action),
                                str((decision_worthiness.get("why") or ["No decision rationale recorded."])[0]),
                                tone=_tone(evidence_summary.get("trust_tier")),
                            ),
                            metric_card(
                                "Best Retrieved Evidence",
                                str(best_case.get("name", "n/a")),
                                f'{float(best_case.get("achieved_error") or 0.0):.4f} Ha achieved error',
                            ),
                            metric_card(
                                "Distance to chemical accuracy",
                                f"{best_distance_to_target:.4f} Ha",
                                f"Target {target:.4f} Ha",
                            ),
                            status_card(
                                "Mitigation / high-shot lesson",
                                "No automatic improvement",
                                "Current campaign shows deeper mitigation or more shots must still be judged by retrieved error.",
                                tone="exploratory",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-hardware__optimization-trial",
                children=[
                    html.P("Algorithm-to-hardware loop", className="qcchem-card-eyebrow"),
                    html.H2("Optimization Trial", className="qcchem-card-title"),
                    html.P(
                        "This block tracks whether the current campaign is improving the actual hardware workload, not just increasing shots. It should stay conservative until a retrieved runtime result closes the chemical-accuracy gap.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card(
                                "Candidate",
                                str(hardware_optimization.get("candidate_id", "not planned")),
                                f"score={hardware_optimization.get('selection_score', 'n/a')}",
                            ),
                            status_card(
                                "Local accuracy gate",
                                str(hardware_optimization.get("local_accuracy_pass", "n/a")),
                                "Only locally accurate candidates should spend real runtime budget.",
                                tone="validated" if hardware_optimization.get("local_accuracy_pass") is True else "exploratory",
                            ),
                            metric_card(
                                "Compiled burden",
                                f"{hardware_optimization.get('transpiled_two_qubit_gate_count', 'n/a')} 2Q gates",
                                f"depth={hardware_optimization.get('transpiled_depth', 'n/a')}",
                            ),
                            metric_card(
                                "Budget used",
                                str((hardware_optimization.get("runtime_budget_ledger") or {}).get("total_budgeted_shots", "n/a")),
                                f"max={(hardware_optimization.get('runtime_budget_ledger') or {}).get('max_total_budgeted_shots', 'n/a')} shots",
                            ),
                            status_card(
                                "Optimization stop reason",
                                str(hardware_optimization.get("stop_reason", "not_started")),
                                str(hardware_optimization.get("recommended_action", "Stop immediately if chemical accuracy is reached or quota guard is hit.")),
                                tone="informational",
                            ),
                            metric_card(
                                "Best optimization result",
                                str(empirical_best_attempt.get("candidate_id", "not collected")),
                                f"error={empirical_best_attempt.get('runtime_error_hartree', 'n/a')} Ha",
                            ),
                            metric_card(
                                "Prior hardware reference",
                                str(prior_reference.get("candidate_id", "n/a")),
                                f"error={prior_reference.get('runtime_error_hartree', 'n/a')} Ha",
                            ),
                            status_card(
                                "Delta vs prior reference",
                                str(optimization_delta if optimization_delta is not None else "n/a"),
                                "Negative means this optimization trial improved the previous best hardware result.",
                                tone="validated" if isinstance(optimization_delta, (int, float)) and optimization_delta < 0 else "exploratory",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-page__analysis-grid",
                children=[
                    html.Section(
                        className="qcchem-card qcchem-hardware__ladder",
                        children=[
                            html.P("Campaign ranking", className="qcchem-card-eyebrow"),
                            html.H2("Runtime error ladder", className="qcchem-card-title"),
                            html.P(
                                "Rank the campaign by achieved error, but only treat retrieved cases as defensible evidence. Everything else stays operationally interesting, not scientifically confirmed.",
                                className="qcchem-card-note",
                            ),
                            dcc.Graph(figure=_runtime_error_figure(model), config={"displayModeBar": False}),
                        ],
                    ),
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
                className="qcchem-page__analysis-grid",
                children=[
                    html.Section(
                        className="qcchem-card qcchem-hardware__usage",
                        children=[
                            html.P("Operational burden", className="qcchem-card-eyebrow"),
                            html.H2("Runtime usage versus compiled depth", className="qcchem-card-title"),
                            html.P(
                                "Use the operational plot to diagnose whether a case failed because of hardware burden, mitigation choices, or simply because the chemistry error remained too large.",
                                className="qcchem-card-note",
                            ),
                            dcc.Graph(figure=_runtime_usage_figure(model), config={"displayModeBar": False}),
                        ],
                    ),
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
                "Interpretation rule",
                "A hardware campaign page should answer three questions in order: which cases were truly retrieved, which retrieved case is best, and how far that best case still sits from chemical accuracy.",
                accent="copper",
                eyebrow="Review protocol",
            ),
        ],
    )


def layout() -> html.Div:
    return build_hardware_campaign_page(sample_hardware_campaign_model())
