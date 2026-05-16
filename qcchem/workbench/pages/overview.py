from __future__ import annotations

from pathlib import Path
from typing import Any

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.core.ai_workspace import AI_WORKSPACE_TICKET_LANE_INBOX, AI_WORKSPACE_TICKET_LANE_RETURNED
from qcchem.workflow.ai_store import list_ticket_records, workspace_root
from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.components.molecule import build_molecule_viewer
from qcchem.workbench.data import load_featured_run_view_model
from qcchem.workbench.evidence_console import build_evidence_console_model, format_action_label
from qcchem.workbench.theme import THEME
from qcchem.workbench.viewmodels import build_run_view_model

SAMPLE_MOLECULE_PAYLOAD: dict[str, Any] = {
    "name": "LiH fragment",
    "title": "LiH active fragment",
    "caption": "Representative fragment and anchor labels used throughout the workbench while full artifact-driven selection lands in Task 7.",
    "atoms": [
        {"elem": "Li", "x": 0.0, "y": 0.0, "z": 0.0},
        {"elem": "H", "x": 0.0, "y": 0.0, "z": 1.62},
    ],
    "style": {"stick": {"radius": 0.18}, "sphere": {"scale": 0.28}},
    "labels": [
        {"text": "Li", "position": {"x": 0.0, "y": 0.0, "z": 0.0}},
        {"text": "H", "position": {"x": 0.0, "y": 0.0, "z": 1.62}},
    ],
}

SAMPLE_RUN_PAYLOAD: dict[str, Any] = {
    "problem": {
        "molecule_name": "LiH Active Fragment",
        "basis": "sto-3g",
        "charge": 0,
        "multiplicity": 1,
        "active_space_metadata": {
            "num_active_orbitals": 4,
            "num_active_electrons": 2,
            "orbital_window": "1 sigma to 3 sigma*",
            "orbital_levels_ev": [-21.4, -10.2, -1.4, 0.6],
        },
    },
    "energy": {
        "total_energy": -7.8823,
        "electronic_energy": -8.8761,
        "nuclear_repulsion_energy": 0.9938,
    },
    "mapping": {
        "kind": "bravyi_kitaev",
        "num_qubits": 8,
        "qubit_term_count": 128,
        "symmetry_tapered_qubits": 2,
    },
    "benchmark": {
        "absolute_error": 0.0118,
        "relative_error": 0.0015,
        "meets_threshold": True,
        "within_uncertainty": True,
        "threshold": 0.02,
        "comparison_target": "exact diagonalization",
        "compressed_vs_uncompressed": "compressed",
    },
    "runtime_submission": {
        "backend_name": "ibm_kyiv",
        "backend_version": "1.7.2",
        "provider": "ibm",
        "job_id": "job-lih-2048",
        "attempted": True,
        "submitted": True,
        "succeeded": True,
        "runtime_kind": "runtime_estimator",
        "mode": "runtime",
        "service": "ibm_runtime",
        "failure_category": None,
        "failure_message": None,
        "options_snapshot": {"shots": 4096, "resilience_level": 1, "precision_target": 0.015},
        "result_provenance": {"attempt_stage": "result_retrieved", "queue_hours": 0.4},
        "returned_job_metadata": {"metadata": {"shots": 4096, "usage_seconds": 132}},
        "verification_status": "passed",
        "transpiled_depth": 312,
        "transpiled_two_qubit_gate_count": 74,
        "transpilation": {"optimization_level": 2, "layout": "sabre"},
    },
    "reduction_audit": {
        "selection_mode": "auto",
        "selected_active_orbitals_original": [2, 3, 4, 5],
        "frozen_orbitals": [0, 1],
    },
    "compression_result": {
        "method": "double_factorization",
        "rank": 11,
        "post_term_count": 44,
        "pre_term_count": 128,
    },
    "verification_status": "validated",
    "hardware_verified": True,
    "chemical_accuracy": {
        "available": True,
        "meets_chemical_accuracy": False,
        "absolute_error_hartree": 0.0118,
        "threshold_hartree": 0.0016,
    },
    "runtime_chemical_accuracy": {
        "available": True,
        "meets_chemical_accuracy": False,
        "absolute_error_hartree": 0.0142,
        "threshold_hartree": 0.0016,
    },
    "evidence_summary": {
        "primary_scientific_claim": "LiH compressed active-space workflow remains the leading defended local claim in the current campaign.",
        "trust_tier": "validated",
        "recommended_action": "review_runtime_gap",
        "decision_worthiness": {"why": ["runtime-derived path still sits above the chemical-accuracy line."]},
    },
}


def build_sample_view_model() -> dict[str, Any]:
    view = build_run_view_model(SAMPLE_RUN_PAYLOAD)
    view["molecule_viewer"] = SAMPLE_MOLECULE_PAYLOAD
    return view


def _overview_figure(view: dict[str, Any]) -> go.Figure:
    total_energy = float(view["hero"].get("total_energy") or 0.0)
    absolute_error = float(view["hero"].get("absolute_error") or 0.0)
    runtime_absolute_error = float(
        (view.get("confidence", {}).get("runtime_chemical_accuracy") or {}).get("absolute_error_hartree", absolute_error)
        or absolute_error
    )
    threshold = float(
        (
            view.get("confidence", {}).get("chemical_accuracy") or {}
        ).get("threshold_hartree")
        or view.get("confidence", {}).get("threshold")
        or view.get("benchmark", {}).get("threshold")
        or 0.02
    )
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.18,
        row_heights=[0.42, 0.58],
        subplot_titles=("Reported total energy", "Absolute-error evidence"),
    )
    figure.add_bar(
        x=["Compressed VQE"],
        y=[total_energy],
        marker={
            "color": [THEME["accent"]["copper"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f"{total_energy:.4f}"],
        textposition="outside",
        hovertemplate="Total energy: %{y:.4f} Ha<extra></extra>",
        row=1,
        col=1,
    )
    figure.add_bar(
        x=["Benchmark absolute error", "Runtime absolute error"],
        y=[absolute_error, runtime_absolute_error],
        marker={
            "color": [THEME["accent"]["deep_blue"], THEME["accent"]["sage"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[f"{absolute_error:.4f}", f"{runtime_absolute_error:.4f}"],
        textposition="outside",
        hovertemplate="%{x}: %{y:.4f} Ha<extra></extra>",
        row=2,
        col=1,
    )
    figure.add_hrect(
        y0=0,
        y1=threshold,
        fillcolor="rgba(49, 95, 74, 0.08)",
        line_width=0,
        row=2,
        col=1,
    )
    figure.add_hline(
        y=threshold,
        line_dash="dash",
        line_color=THEME["status"]["informational"],
        annotation_text="Threshold",
        annotation_position="top right",
        row=2,
        col=1,
    )
    apply_chart_theme(
        figure,
        title="Energy and absolute-error evidence across the current evidence stack",
        height=460,
    )
    figure.update_yaxes(title_text="Total energy (Hartree)", row=1, col=1)
    figure.update_yaxes(title_text="Absolute error (Hartree)", row=2, col=1)
    figure.add_annotation(
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.16,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        align="right",
        bgcolor="rgba(255, 250, 243, 0.88)",
        bordercolor=THEME["surface"]["line"],
        borderwidth=1,
        font={"size": 11, "color": THEME["text"]["secondary"]},
        text=f"Runtime gap to target: {max(runtime_absolute_error - threshold, 0.0):.4f} Ha",
    )
    return figure


def _status_tone(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"validated", "passed", "retrieved_result", "result_retrieved", "success", "succeeded"}:
        return "validated"
    if normalized in {"submitted", "queued", "running", "exploratory", "review"}:
        return "exploratory"
    if normalized in {"failed", "unstable", "not met", "error"}:
        return "unstable"
    return "informational"


def _overview_threshold(view: dict[str, Any], benchmark: dict[str, Any]) -> float:
    return float(
        (
            view.get("confidence", {}).get("chemical_accuracy") or {}
        ).get("threshold_hartree")
        or view.get("confidence", {}).get("threshold")
        or benchmark.get("threshold")
        or 0.02
    )


def _workspace_snapshot() -> dict[str, int]:
    root = workspace_root(Path.cwd(), create=False)
    inbox = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX)
    returned = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RETURNED)
    pending_analysis = [ticket for ticket in inbox if str(ticket.get("task_type", "")).lower() == "analysis"]
    return {
        "pending_analysis": len(pending_analysis),
        "returned": len(returned),
        "inbox": len(inbox),
    }


def build_overview_page(model: dict[str, Any]) -> html.Div:
    view = model
    molecule_model = view.get("molecule_viewer") or SAMPLE_MOLECULE_PAYLOAD
    active_space_metadata = view.get("structure", {}).get("active_space_metadata") or {}
    compression = view.get("compression") or {}
    mapping = view.get("mapping") or {}
    benchmark = view.get("benchmark") or {}
    confidence = view.get("confidence") or {}
    evidence_summary = view.get("evidence_summary") or {}
    evidence_console = build_evidence_console_model(view)
    artifact_entry = view.get("artifact_index_entry") or {}
    artifact_entry_path = artifact_entry.get("result_json") or artifact_entry.get("artifact_root") or "sample fallback"
    workspace_snapshot = _workspace_snapshot()
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    runtime_chemical_accuracy = confidence.get("runtime_chemical_accuracy") or {}
    threshold = _overview_threshold(view, benchmark)
    chemical_available = bool(chemical_accuracy.get("available"))
    chemical_met = chemical_accuracy.get("meets_chemical_accuracy")
    chemical_value = "Met" if chemical_met else "Not met" if chemical_available else "Unavailable"
    chemical_observed_error = float(chemical_accuracy.get("absolute_error_hartree") or view["hero"]["absolute_error"] or 0.0)
    runtime_status_raw = (
        view.get("runtime", {}).get("verification_status")
        or confidence.get("verification_status")
        or view.get("runtime", {}).get("result_provenance", {}).get("attempt_stage")
        or "unknown"
    )
    runtime_status_label = str(runtime_status_raw).replace("_", " ").title()
    runtime_gap = float(runtime_chemical_accuracy.get("absolute_error_hartree") or view["hero"]["absolute_error"] or 0.0)
    return html.Div(
        className="qcchem-page qcchem-page--overview",
        children=[
            html.Section(
                className="qcchem-card qcchem-overview__hero",
                children=[
                    html.P("Evidence Console v2", className="qcchem-card-eyebrow"),
                    html.H1("Campaign Overview", className="qcchem-card-title qcchem-overview__hero-title"),
                    html.P(
                        "Lead with the claim you can defend now, then keep the chemistry window, reduction posture, and runtime provenance close enough to audit without opening another page.",
                        className="qcchem-card-note qcchem-overview__hero-body",
                    ),
                    html.Div(
                        className="qcchem-overview__summary-grid",
                        children=[
                            metric_card(
                                "Current defended claim",
                                f'{view["hero"]["total_energy"]:.4f} Ha',
                                (
                                    f"{view['hero']['molecule_name']} | {view['hero'].get('primary_claim')}"
                                    if view["hero"].get("primary_claim")
                                    else f'{view["hero"]["molecule_name"]} in {view["hero"]["basis"]}'
                                ),
                            ),
                            metric_card(
                                "Benchmark gap",
                                f'{view["hero"]["absolute_error"]:.4f} Ha',
                                f'Against {benchmark.get("comparison_target", "exact diagonalization")}',
                            ),
                            status_card(
                                "Chemical accuracy target",
                                chemical_value,
                                (
                                    f"{chemical_observed_error:.4f} Ha observed versus {threshold:.4f} Ha target"
                                    if chemical_available
                                    else "The current artifact bundle does not publish a chemical-accuracy threshold."
                                ),
                                tone=_status_tone("validated" if chemical_met else "not met" if chemical_available else None),
                            ),
                            status_card(
                                "Runtime evidence status",
                                runtime_status_label,
                                f'{view["runtime"]["backend_name"]} | {view["runtime"]["job_id"] or "job id unavailable"}',
                                tone=_status_tone(runtime_status_raw),
                            ),
                            status_card(
                                "Recommended action",
                                str(evidence_summary.get("recommended_action", "review_evidence_boundary")),
                                str((evidence_summary.get("decision_worthiness") or {}).get("why", "Evidence-guided next step.")),
                                tone=_status_tone(confidence.get("trust_tier") or confidence.get("verification_status")),
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-overview__summary-grid",
                children=[
                    status_card(
                        "Evidence Console",
                        str(evidence_console["best_evidence"]["trust_tier"]),
                        str(evidence_console["best_evidence"]["claim"]),
                        tone=_status_tone(evidence_console["best_evidence"]["trust_tier"]),
                    ),
                    metric_card(
                        "Chemical accuracy gap",
                        f'{float(evidence_console["trust_gap"]["chemical_accuracy_gap_hartree"]):.4f} Ha',
                        f'Threshold {float(evidence_console["trust_gap"]["threshold_hartree"]):.4f} Ha',
                    ),
                    status_card(
                        "Runtime boundary",
                        str(evidence_console["runtime_boundary"]["submission_health"]).replace("_", " "),
                        str(evidence_console["runtime_boundary"]["budget_note"]),
                        tone=_status_tone(evidence_console["runtime_boundary"]["submission_health"]),
                    ),
                    metric_card(
                        "Open AI work",
                        str(evidence_console["open_tasks"]["total_open"]),
                        f'{evidence_console["open_tasks"]["pending_analysis"]} pending analysis / {evidence_console["open_tasks"]["returned"]} returned',
                    ),
                    status_card(
                        "Next action",
                        format_action_label(evidence_console["best_evidence"]["recommended_action"]),
                        "Use AI Workspace to turn this into a persistent analysis or execution ticket.",
                        tone=_status_tone(evidence_console["best_evidence"]["trust_tier"]),
                    ),
                ],
            ),
            html.Div(
                className="qcchem-overview__summary-grid",
                children=[
                    status_card(
                        "Best Evidence Desk",
                        str(evidence_summary.get("trust_tier", "validated")),
                        str(
                            evidence_summary.get(
                                "primary_scientific_claim",
                                "No primary scientific claim has been surfaced for this artifact.",
                            )
                        ),
                        tone=_status_tone(evidence_summary.get("trust_tier")),
                    ),
                    metric_card(
                        "Trust gap to close",
                        f"{max(runtime_gap - threshold, 0.0):.4f} Ha",
                        "Runtime-derived path still above the declared chemical-accuracy line.",
                    ),
                    metric_card(
                        "Pending analysis",
                        str(workspace_snapshot["pending_analysis"]),
                        "Inbox analysis tickets still waiting for a defended interpretation pass.",
                    ),
                    status_card(
                        "Recommended next action",
                        str(evidence_summary.get("recommended_action", "review_evidence_boundary")),
                        "Use this as the default next move unless a stronger artifact shifts the evidence stack.",
                        tone=_status_tone(evidence_summary.get("trust_tier") or confidence.get("verification_status")),
                    ),
                ],
            ),
            html.Div(
                className="qcchem-overview__analysis-grid",
                children=[
                    html.Section(
                        className="qcchem-card qcchem-overview__chart-card",
                        children=[
                            html.P("Evidence trace", className="qcchem-card-eyebrow"),
                            html.H2("How the claim compares to thresholds", className="qcchem-card-title"),
                            html.P(
                                "Keep the reported energy and the benchmark-versus-runtime gap in one frame so the opening judgment stays constrained by the evidence stack.",
                                className="qcchem-card-note",
                            ),
                            dcc.Graph(figure=_overview_figure(view), config={"displayModeBar": False, "responsive": True}),
                        ],
                    ),
                    build_molecule_viewer(
                        molecule_model,
                        viewer_id="overview-molecule",
                        title="Structure context",
                        caption="Structural anchor for the active-space decision and the downstream resource posture.",
                    ),
                ],
            ),
            html.Div(
                className="qcchem-overview__detail-grid",
                children=[
                    detail_card(
                        "Decision summary",
                        [
                            (
                                "Active space",
                                f'{active_space_metadata.get("num_active_electrons", "?")} electrons / {active_space_metadata.get("num_active_orbitals", "?")} orbitals',
                            ),
                            (
                                "Compression",
                                f'{compression.get("method", "n/a")} rank {compression.get("rank", "n/a")}',
                            ),
                            (
                                "Mapping",
                                f'{str(mapping.get("kind", "n/a")).replace("_", "-")} with {mapping.get("symmetry_tapered_qubits", 0)} tapered qubits',
                            ),
                            (
                                "Qubit operator",
                                f'{mapping.get("num_qubits", "?")} qubits / {mapping.get("qubit_term_count", "?")} terms',
                            ),
                            ("Confidence state", "Validated against threshold" if benchmark.get("meets_threshold") else "Threshold not yet met"),
                        ],
                    ),
                    detail_card(
                        "Artifact browser",
                        [
                            ("Selected artifact", str(artifact_entry.get("artifact_name", "sample model"))),
                            ("Kind", str(artifact_entry.get("artifact_kind", "sample"))),
                            ("Trust tier", str(artifact_entry.get("trust_tier", evidence_summary.get("trust_tier", "sample")))),
                            ("Runtime sidecar", str(artifact_entry.get("runtime_submission_status", "not indexed"))),
                            ("Path", str(artifact_entry_path)),
                        ],
                        eyebrow="Read-only Index",
                    ),
                    detail_card(
                        "Execution posture",
                        [
                            ("Benchmark target", str(benchmark.get("comparison_target", "exact diagonalization"))),
                            ("Threshold", f"{threshold:.4f} Ha"),
                            ("Compressed vs uncompressed", str(benchmark.get("compressed_vs_uncompressed", "n/a"))),
                            ("Runtime backing", f'{view["runtime"]["backend_name"]} / {runtime_status_label}'),
                            ("Runtime gap", f"{runtime_gap:.4f} Ha"),
                        ],
                        eyebrow="Operational Posture",
                    ),
                    callout_card(
                        "Next review path",
                        "Use the structure page to defend the orbital window, the compression page to audit operator reduction, and the runtime page to decide whether backend evidence strengthens or constrains the claim.",
                        accent="copper",
                        eyebrow="Interpretation",
                    ),
                    detail_card(
                        "Operations queue",
                        [
                            ("Inbox tickets", str(workspace_snapshot["inbox"])),
                            ("Pending analysis", str(workspace_snapshot["pending_analysis"])),
                            ("Returned items", str(workspace_snapshot["returned"])),
                            ("Hardware decision", str(evidence_summary.get("recommended_action", "review_evidence_boundary"))),
                            ("Best evidence anchor", str(evidence_summary.get("trust_tier", "validated"))),
                        ],
                        eyebrow="Task Pressure",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_overview_page(load_featured_run_view_model() or build_sample_view_model())
