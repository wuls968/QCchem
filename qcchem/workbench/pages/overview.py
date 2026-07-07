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
from qcchem.workbench.data import load_featured_run_view_model, load_research_os_snapshot
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
    research_os = load_research_os_snapshot()
    objective = research_os.get("objective") or {}
    claim_review = research_os.get("claim_review") or {}
    promotion_review = research_os.get("promotion_review") or {}
    release_verification = research_os.get("release_verification") or {}
    release_history_summary = research_os.get("release_history_summary") or {}
    release_history_handoff = research_os.get("release_history_handoff") or {}
    release_matrix_summary = research_os.get("release_matrix_summary") or {}
    release_evidence_handoff = research_os.get("release_evidence_handoff") or {}
    release_verification_summary = (
        release_verification.get("summary")
        if isinstance(release_verification.get("summary"), dict)
        else {}
    )
    open_gaps = research_os.get("open_evidence_gaps") or []
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
    release_verification_status = str(release_verification.get("status") or "No verification report")
    release_verification_detail = (
        f"{release_verification_summary.get('release_status_count', 0)} status bundles / "
        f"{release_verification_summary.get('diagnostics_manifest_count', 0)} manifests / "
        f"{release_verification_summary.get('acceptance_status_count', 0)} sidecar reports; "
        f"{release_verification_summary.get('failure_count', 0)} failures"
        if release_verification
        else "No downloaded CI diagnostics verification report has been indexed."
    )
    release_verification_path = release_verification.get("source_path")
    if release_verification_path:
        release_verification_detail = f"{release_verification_detail} | {release_verification_path}"
    release_history_status = str(release_history_summary.get("status") or "No release history summary")
    release_history_delta_counts = (
        release_history_summary.get("matrix_delta_status_counts")
        if isinstance(release_history_summary.get("matrix_delta_status_counts"), dict)
        else {}
    )
    release_history_delta_text = (
        ", ".join(f"{key}={value}" for key, value in sorted(release_history_delta_counts.items()))
        if release_history_delta_counts
        else "no matrix delta counts"
    )
    release_history_detail = (
        f"{release_history_summary.get('run_count', 0)} retained runs / "
        f"{release_history_summary.get('passed_run_count', 0)} passed / "
        f"{release_history_summary.get('failed_run_count', 0)} failed / "
        f"{release_history_summary.get('incomplete_run_count', 0)} incomplete; "
        f"{release_history_delta_text}"
        if release_history_summary
        else "Run qcchem release history summarize --history-root <history-dir> -o release_history_summary.json."
    )
    release_history_path = release_history_summary.get("source_path")
    if release_history_path:
        release_history_detail = f"{release_history_detail} | {release_history_path}"
    release_history_handoff_status = str(release_history_handoff.get("status") or "No release history handoff")
    release_history_handoff_delta_counts = (
        release_history_handoff.get("matrix_delta_status_counts")
        if isinstance(release_history_handoff.get("matrix_delta_status_counts"), dict)
        else {}
    )
    release_history_handoff_delta_text = (
        ", ".join(f"{key}={value}" for key, value in sorted(release_history_handoff_delta_counts.items()))
        if release_history_handoff_delta_counts
        else "no matrix delta counts"
    )
    release_history_handoff_detail = (
        f"{release_history_handoff.get('recommended_action') or 'review_release_history'}; "
        f"{release_history_handoff.get('run_count', 0)} retained runs / "
        f"{release_history_handoff.get('passed_run_count', 0)} passed / "
        f"{release_history_handoff.get('failed_run_count', 0)} failed / "
        f"{release_history_handoff.get('incomplete_run_count', 0)} incomplete; "
        f"{release_history_handoff_delta_text}"
        if release_history_handoff
        else "Run qcchem release history export-markdown --history-summary <json> -o release_history_summary.md."
    )
    release_history_handoff_entry = release_history_handoff.get("artifact_index_entry")
    release_history_handoff_summary_path = (
        release_history_handoff_entry.get("release_history_handoff_summary_json")
        if isinstance(release_history_handoff_entry, dict)
        else None
    )
    if release_history_handoff_summary_path:
        release_history_handoff_detail = f"{release_history_handoff_detail} | summary {release_history_handoff_summary_path}"
    release_history_handoff_path = release_history_handoff.get("source_path")
    if release_history_handoff_path:
        release_history_handoff_detail = f"{release_history_handoff_detail} | {release_history_handoff_path}"
    release_matrix_artifacts = (
        release_matrix_summary.get("artifacts")
        if isinstance(release_matrix_summary.get("artifacts"), list)
        else []
    )
    release_matrix_failed_count = release_matrix_summary.get("failed_artifact_count")
    release_matrix_failed_count = (
        int(release_matrix_failed_count)
        if isinstance(release_matrix_failed_count, int)
        else sum(1 for item in release_matrix_artifacts if isinstance(item, dict) and item.get("status") != "passed")
    )
    release_matrix_status = (
        "passed"
        if release_matrix_summary and release_matrix_failed_count == 0
        else "failed"
        if release_matrix_summary
        else "No release matrix baseline"
    )
    release_matrix_artifact_count = release_matrix_summary.get("artifact_count")
    if not isinstance(release_matrix_artifact_count, int):
        release_matrix_artifact_count = len(release_matrix_artifacts)
    release_matrix_detail = (
        f"{release_matrix_artifact_count} matrix artifacts / {release_matrix_failed_count} failed"
        if release_matrix_summary
        else "Run qcchem release collect-evidence to write release_matrix_summary.json."
    )
    release_matrix_path = release_matrix_summary.get("source_path")
    if release_matrix_path:
        release_matrix_detail = f"{release_matrix_detail} | {release_matrix_path}"
    release_handoff_status = str(release_evidence_handoff.get("status") or "No release evidence handoff")
    release_handoff_first_failure = (
        release_evidence_handoff.get("first_failure")
        if isinstance(release_evidence_handoff.get("first_failure"), dict)
        else None
    )
    release_handoff_failure_text = (
        str(release_handoff_first_failure.get("reason") or "unknown")
        if release_handoff_first_failure
        else "no first failure"
    )
    release_handoff_verification = (
        release_evidence_handoff.get("release_artifact_verification")
        if isinstance(release_evidence_handoff.get("release_artifact_verification"), dict)
        else {}
    )
    release_handoff_matrix_artifacts = (
        release_handoff_verification.get("matrix_artifacts")
        if isinstance(release_handoff_verification.get("matrix_artifacts"), list)
        else []
    )
    release_handoff_failed_matrix_artifacts = [
        item
        for item in release_handoff_matrix_artifacts
        if isinstance(item, dict) and item.get("status") != "passed"
    ]
    release_handoff_matrix_text = (
        f"{len(release_handoff_matrix_artifacts)} matrix artifacts / "
        f"{len(release_handoff_failed_matrix_artifacts)} failed"
        if release_handoff_matrix_artifacts
        else "no matrix artifact summary"
    )
    release_handoff_matrix_delta = (
        release_evidence_handoff.get("release_matrix_delta")
        if isinstance(release_evidence_handoff.get("release_matrix_delta"), dict)
        else {}
    )
    release_handoff_delta_added = (
        release_handoff_matrix_delta.get("added") if isinstance(release_handoff_matrix_delta.get("added"), list) else []
    )
    release_handoff_delta_removed = (
        release_handoff_matrix_delta.get("removed")
        if isinstance(release_handoff_matrix_delta.get("removed"), list)
        else []
    )
    release_handoff_delta_changed = (
        release_handoff_matrix_delta.get("changed")
        if isinstance(release_handoff_matrix_delta.get("changed"), list)
        else []
    )
    release_handoff_delta_text = (
        f"delta={release_handoff_matrix_delta.get('status')} "
        f"({len(release_handoff_delta_changed)} changed, "
        f"{len(release_handoff_delta_added)} added, {len(release_handoff_delta_removed)} removed)"
        if release_handoff_matrix_delta
        else "delta=not available"
    )
    release_handoff_detail = (
        f"{release_evidence_handoff.get('recommended_action') or 'review_release_evidence'}; "
        f"{release_handoff_failure_text}; {release_handoff_matrix_text}; {release_handoff_delta_text}"
        if release_evidence_handoff
        else "Run qcchem release collect-evidence after downloading CI diagnostics."
    )
    release_handoff_path = release_evidence_handoff.get("source_path")
    if release_handoff_path:
        release_handoff_detail = f"{release_handoff_detail} | {release_handoff_path}"
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
                        "Research Objective",
                        str(objective.get("objective_name") or "No objective yet"),
                        str(objective.get("recommended_action") or "Create an objective plan to connect claim, evidence, and next action."),
                        tone=_status_tone(objective.get("status")),
                    ),
                    metric_card(
                        "Open evidence gaps",
                        str(len(open_gaps)),
                        ", ".join(str(item) for item in open_gaps[:3]) if open_gaps else "No objective evidence gaps recorded.",
                    ),
                    status_card(
                        "Claim compiler",
                        str(claim_review.get("support_level") or "No review yet"),
                        str(claim_review.get("safe_rewrite") or "Run qcchem claim check to persist a claim boundary review."),
                        tone=_status_tone("unstable" if claim_review.get("support_level") == "overclaimed" else claim_review.get("status")),
                    ),
                    status_card(
                        "Promotion gate",
                        str(promotion_review.get("status") or "No gate review yet"),
                        str(promotion_review.get("recommended_action") or "Exploratory artifacts require a promotion gate before candidate language."),
                        tone=_status_tone(promotion_review.get("status")),
                    ),
                    status_card(
                        "Release verification",
                        release_verification_status,
                        release_verification_detail,
                        tone=_status_tone(release_verification.get("status")),
                    ),
                    status_card(
                        "Release history",
                        release_history_status,
                        release_history_detail,
                        tone=_status_tone(release_history_summary.get("status")),
                    ),
                    status_card(
                        "Release history handoff",
                        release_history_handoff_status,
                        release_history_handoff_detail,
                        tone=_status_tone(release_history_handoff.get("status")),
                    ),
                    status_card(
                        "Release matrix baseline",
                        str(release_matrix_status),
                        release_matrix_detail,
                        tone=_status_tone(release_matrix_status),
                    ),
                    status_card(
                        "Release evidence handoff",
                        release_handoff_status,
                        release_handoff_detail,
                        tone=_status_tone(release_evidence_handoff.get("status")),
                    ),
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
