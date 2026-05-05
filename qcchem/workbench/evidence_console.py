"""Shared Evidence Console view-model helpers for the Dash workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qcchem.core.ai_workspace import AI_WORKSPACE_TICKET_LANE_INBOX, AI_WORKSPACE_TICKET_LANE_RETURNED
from qcchem.workflow.ai_store import list_ticket_records, workspace_root


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_action_label(value: object) -> str:
    """Return a human-readable action label while preserving deterministic semantics."""
    return str(value or "review_evidence_boundary").replace("_", " ")


def _workspace_counts(base: Path | str | None) -> dict[str, int]:
    root = workspace_root(Path(base) if base is not None else Path.cwd(), create=False)
    inbox = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX)
    returned = list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_RETURNED)
    pending_analysis = [ticket for ticket in inbox if str(ticket.get("task_type", "")).lower() == "analysis"]
    return {
        "inbox": len(inbox),
        "pending_analysis": len(pending_analysis),
        "returned": len(returned),
        "total_open": len(inbox) + len(returned),
    }


def _submission_health(runtime: dict[str, Any]) -> str:
    if runtime.get("succeeded"):
        return "succeeded"
    if runtime.get("submitted"):
        return "submitted_pending_collection"
    if runtime.get("attempted"):
        return "attempted_without_result"
    if runtime.get("failure_category"):
        return "failed"
    return "not_attempted"


def build_evidence_console_model(
    run_model: dict[str, Any],
    *,
    hardware_model: dict[str, Any] | None = None,
    workspace_base: Path | str | None = None,
) -> dict[str, Any]:
    """Build the common evidence-decision model shared across workbench pages."""
    evidence_summary = _safe_dict(run_model.get("evidence_summary"))
    confidence = _safe_dict(run_model.get("confidence"))
    runtime = _safe_dict(run_model.get("runtime"))
    benchmark = _safe_dict(run_model.get("benchmark"))
    chemical_accuracy = _safe_dict(confidence.get("chemical_accuracy"))
    runtime_accuracy = _safe_dict(confidence.get("runtime_chemical_accuracy"))

    threshold = _safe_float(
        chemical_accuracy.get("threshold_hartree")
        or confidence.get("threshold")
        or benchmark.get("threshold")
        or 1.6e-3,
        1.6e-3,
    )
    simulator_error = _safe_float(benchmark.get("absolute_error") or confidence.get("absolute_error"), 0.0)
    hardware_error = _safe_float(runtime_accuracy.get("absolute_error_hartree"), simulator_error)
    chemical_gap = max(hardware_error - threshold, 0.0)
    returned_metadata = _safe_dict(runtime.get("returned_job_metadata"))
    returned_metadata_inner = _safe_dict(returned_metadata.get("metadata"))
    options_snapshot = _safe_dict(runtime.get("options_snapshot"))
    shots = returned_metadata_inner.get("shots", options_snapshot.get("shots"))
    usage_seconds = returned_metadata_inner.get("usage_seconds")
    action = evidence_summary.get("recommended_action") or confidence.get("recommended_action") or "review_evidence_boundary"

    best_evidence = {
        "claim": evidence_summary.get("primary_scientific_claim")
        or run_model.get("hero", {}).get("primary_claim")
        or "No primary scientific claim declared.",
        "trust_tier": evidence_summary.get("trust_tier") or confidence.get("trust_tier") or confidence.get("verification_status") or "exploratory",
        "recommended_action": action,
        "runtime_evidence_status": evidence_summary.get("runtime_evidence_status")
        or runtime.get("verification_status")
        or runtime.get("result_provenance", {}).get("attempt_stage")
        or "unknown",
    }

    hardware_cases = list((_safe_dict(hardware_model).get("cases") or [])) if hardware_model else []
    best_hardware_case = min(
        [case for case in hardware_cases if isinstance(case, dict) and case.get("achieved_error") is not None],
        key=lambda case: _safe_float(case.get("achieved_error")),
        default=None,
    )

    return {
        "best_evidence": best_evidence,
        "trust_gap": {
            "chemical_accuracy_gap_hartree": chemical_gap,
            "threshold_hartree": threshold,
            "hardware_error_hartree": hardware_error,
            "simulator_error_hartree": simulator_error,
        },
        "runtime_boundary": {
            "submission_health": _submission_health(runtime),
            "hardware_gap_hartree": abs(hardware_error - simulator_error),
            "budget_note": f"{shots if shots is not None else 'n/a'} shots / {usage_seconds if usage_seconds is not None else 'n/a'} usage seconds",
            "precision_target": options_snapshot.get("precision_target"),
            "recommended_action": action,
        },
        "open_tasks": _workspace_counts(workspace_base),
        "hardware_campaign": {
            "best_case": best_hardware_case or {},
            "recommended_action": (_safe_dict(hardware_model).get("decision_worthiness") or {}).get("recommended_action")
            if hardware_model
            else action,
        },
    }
