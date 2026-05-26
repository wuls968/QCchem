"""AI workspace ticket orchestration built on the existing agent workflow."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from qcchem.core.ai_workspace import AIDeliveryRecord, AITaskTicket
from qcchem.core.ai_workspace import (
    AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
    AI_WORKSPACE_TICKET_STATUS_BLOCKED,
    AI_WORKSPACE_TICKET_STATUS_COMPLETED,
    AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
    AI_WORKSPACE_TICKET_STATUS_RETURNED,
    AI_WORKSPACE_TICKET_STATUS_RUNNING,
    AI_WORKSPACE_TICKET_STATUS_SUBMITTED,
)
from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.io.config import resolve_user_path
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_markdown_report
from qcchem.reporting.jsonio import write_result_json
from qcchem.workflow.ai_assistant import draft_analysis_ticket
from qcchem.workflow.ai_store import workspace_root, write_delivery_record, write_ticket_record
from qcchem.workflow.agent import run_analysis_ticket
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.claim_compiler import compile_claim_review, write_claim_review_outputs
from qcchem.workflow.evidence_capsule import build_and_write_evidence_capsule
from qcchem.workflow.evidence_agent import (
    append_ai_provenance_event,
    build_action_proposal,
    build_cost_estimate,
    classify_research_risk,
    draft_ticket_payload_with_optional_model,
    review_claims,
    summarize_evidence_artifacts,
    write_review_outputs,
)
from qcchem.workflow.hardware_optimization import run_hardware_optimization_from_config
from qcchem.workflow.objective import plan_research_objective, status_research_objective
from qcchem.workflow.promotion import review_exploratory_promotion, write_promotion_outputs
from qcchem.workflow.runtime_collect import collect_runtime_artifact
from qcchem.workflow.runner import run_from_config
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.study import run_study_from_config


def _ticket_record(ticket: AITaskTicket) -> dict[str, Any]:
    return asdict(ticket)


def _sanitized_ticket_record(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = set(AITaskTicket.__dataclass_fields__.keys())
    return {key: value for key, value in payload.items() if key in allowed}


def _normalize_text_lines(value: str | None) -> list[str]:
    if value is None:
        return []
    lines = [line.strip() for line in value.splitlines()]
    return [line for line in lines if line]


def _ticket_workspace_base(path: Path) -> Path:
    resolved_path = path.expanduser().resolve()
    if (
        resolved_path.parent.name == "tickets"
        and resolved_path.parent.parent.name == "ai_workspace"
        and resolved_path.parent.parent.parent.name == "artifacts"
    ):
        return resolved_path.parents[3]
    return resolved_path.parent


def _resolved_ticket_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    base_dir = _ticket_workspace_base(path)
    linked_artifacts = payload.get("linked_artifacts") or []
    resolved_payload = dict(payload)
    resolved_payload["linked_artifacts"] = [
        str(resolve_user_path(base_dir, str(artifact))) for artifact in linked_artifacts
    ]
    return resolved_payload


def _delivery_outputs_from_result(result: dict[str, Any]) -> list[str]:
    outputs: list[str] = []
    for output in result.get("linked_outputs") or []:
        if isinstance(output, str) and output:
            outputs.append(output)
    for key in (
        "summary_json",
        "report_markdown",
        "review_findings_json",
        "review_findings_markdown",
        "claim_review_json",
        "claim_review_markdown",
        "capsule_json",
        "capsule_markdown",
        "promotion_review_json",
        "promotion_review_markdown",
        "plan_json",
        "status_json",
    ):
        output = result.get(key)
        if isinstance(output, str) and output:
            outputs.append(output)
    summaries = result.get("summaries") or []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        for key in ("summary_json", "report_markdown"):
            output = summary.get(key)
            if isinstance(output, str) and output:
                outputs.append(output)
    return sorted(set(outputs))


def _execution_root_for_ticket(path: Path, ticket: AITaskTicket, action: dict[str, Any]) -> Path:
    base_dir = _ticket_workspace_base(path)
    action_id = str(action.get("action_id") or "action")
    explicit_output = (action.get("inputs") or {}).get("output_dir")
    if explicit_output:
        return resolve_user_path(base_dir, str(explicit_output))
    return base_dir / "artifacts" / "ai_workspace" / "executions" / ticket.task_id / action_id


def _render_evidence_graph_markdown(payload: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- trust_tier: `{payload.get('trust_tier')}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        f"- sources: `{len(payload.get('sources') or [])}`",
        "",
        "## Best Chemistry Evidence",
        "",
        f"`{payload.get('best_chemistry_evidence')}`",
        "",
        "## Best Runtime Evidence",
        "",
        f"`{payload.get('best_runtime_evidence')}`",
        "",
        "## Open Questions",
        "",
    ]
    questions = payload.get("open_questions") or []
    lines.extend([f"- {item}" for item in questions] or ["- None"])
    lines.extend(["", "## Boundary Notes", ""])
    lines.extend([f"- {item}" for item in payload.get("boundary_notes") or []] or ["- None"])
    return "\n".join(lines)


def _write_evidence_graph_outputs(payload: dict[str, Any], output_dir: Path, *, title: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evidence_summary.json"
    md_path = output_dir / "evidence_summary.md"
    write_result_json(payload, json_path)
    md_path.write_text(_render_evidence_graph_markdown(payload, title=title), encoding="utf-8")
    return {"summary_json": str(json_path), "report_markdown": str(md_path)}


def _require_action_allowed(ticket: AITaskTicket, action: dict[str, Any], path: Path) -> None:
    action_kind = str(action.get("action_kind") or "")
    if action.get("allowed") is False:
        raise PermissionError(str(action.get("blocked_reason") or "Action is blocked by local policy."))
    if action_kind in {"hardware_optimize_submit", "hardware_submit", "runtime_submit"}:
        raise PermissionError("Real hardware/runtime submission is blocked by the v1 AI route.")
    if action_kind == "runtime_collect":
        inputs = action.get("inputs") or {}
        artifact_root = resolve_user_path(_ticket_workspace_base(path), str(inputs.get("artifact_root", "")))
        sidecar = artifact_root / "runtime_submission.json"
        if not sidecar.exists():
            raise FileNotFoundError(f"runtime_collect requires runtime_submission.json under '{artifact_root}'.")
        sidecar_payload = json.loads(sidecar.read_text(encoding="utf-8"))
        if not sidecar_payload.get("job_id"):
            raise ValueError("runtime_collect requires an existing runtime sidecar with job_id.")
        confirmed = bool(ticket.risk_assessment.get("confirmed_high_risk") or inputs.get("confirm_runtime_collect"))
        if not confirmed:
            raise PermissionError("runtime_collect requires explicit high-risk confirmation in the ticket.")


def _run_action_ticket(ticket: AITaskTicket, path: Path) -> dict[str, Any]:
    action = dict(ticket.action_plan or {})
    _require_action_allowed(ticket, action, path)
    action_kind = str(action.get("action_kind") or "")
    inputs = dict(action.get("inputs") or {})
    base_dir = _ticket_workspace_base(path)
    output_root = _execution_root_for_ticket(path, ticket, action)
    output_root.mkdir(parents=True, exist_ok=True)
    provenance_start = append_ai_provenance_event(
        workspace_base=base_dir,
        event_type="workflow_started",
        summary=f"Started AI action {action_kind}.",
        artifacts=ticket.linked_artifacts,
        metadata={"task_id": ticket.task_id, "action_plan": action},
    )

    if action_kind == "run_config":
        config = resolve_user_path(base_dir, str(inputs["config"]))
        result = run_from_config(config, output_dir=output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            "artifact_root": str(result.artifacts.root),
            "verification_status": result.verification_status,
            "total_energy": result.energy.total_energy,
            "evidence_summary": to_primitive(result.evidence_summary),
        }
    elif action_kind == "benchmark_suite":
        config = resolve_user_path(base_dir, str(inputs["config"]))
        result = run_benchmark_suite_from_config(config, output_dir=output_root)
        result_payload = to_primitive(result)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            "artifact_root": result_payload.get("artifact_root") or str(getattr(getattr(result, "artifacts", None), "root", output_root)),
            "summary": result_payload.get("summary"),
            "evidence_summary": result_payload.get("evidence_summary"),
        }
    elif action_kind == "study":
        config = resolve_user_path(base_dir, str(inputs["config"]))
        result = run_study_from_config(config, output_dir=output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            "artifact_root": str(result.artifacts.root) if result.artifacts else str(output_root),
            "summary": to_primitive(result.summary),
            "evidence_summary": to_primitive(result.evidence_summary),
        }
    elif action_kind == "scan":
        config = resolve_user_path(base_dir, str(inputs["config"]))
        result = run_scan_from_config(config, output_dir=output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            "artifact_root": str(result.artifacts.root) if result.artifacts else str(output_root),
            "summary": to_primitive(result.summary),
            "evidence_summary": to_primitive(result.evidence_summary),
        }
    elif action_kind == "runtime_collect":
        artifact_root = resolve_user_path(base_dir, str(inputs["artifact_root"]))
        collect_summary = collect_runtime_artifact(artifact_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            "runtime_collect_summary": collect_summary,
            "artifact_root": collect_summary.get("artifact_root"),
        }
    elif action_kind == "hardware_optimize_preview":
        config = resolve_user_path(base_dir, str(inputs["config"]))
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            **run_hardware_optimization_from_config(config, output_dir=output_root, mode="preview"),
        }
    elif action_kind == "report":
        result_json = resolve_user_path(base_dir, str(inputs["result_json"]))
        report_path = output_root / "report.md"
        write_markdown_report(json.loads(result_json.read_text(encoding="utf-8")), report_path)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "artifact_bundle",
            "action_kind": action_kind,
            "linked_outputs": [str(report_path)],
        }
    elif action_kind == "compare_artifacts":
        artifacts = [str(item) for item in inputs.get("artifacts") or ticket.linked_artifacts]
        graph = summarize_evidence_artifacts(artifacts, workspace_base=base_dir)
        outputs = _write_evidence_graph_outputs(graph, output_root, title="QCchem AI Evidence Comparison")
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "evidence_graph": graph,
            "linked_outputs": list(outputs.values()),
            **outputs,
        }
    elif action_kind == "review_claims":
        targets = [str(item) for item in inputs.get("targets") or ticket.linked_artifacts]
        review = review_claims(
            targets=targets,
            claim_text=inputs.get("claim_text") or ticket.request_text,
            workspace_base=base_dir,
        )
        outputs = write_review_outputs(review, output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "review": review,
            "linked_outputs": list(outputs.values()),
            **outputs,
        }
    elif action_kind == "claim_check":
        targets = [str(item) for item in inputs.get("targets") or inputs.get("artifacts") or ticket.linked_artifacts]
        claim_text = str(inputs.get("claim_text") or ticket.request_text)
        review = compile_claim_review(
            claim_text=claim_text,
            targets=targets,
            workspace_base=base_dir,
        )
        outputs = write_claim_review_outputs(review, output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "claim_review": review,
            "evidence_summary": review,
            "linked_outputs": list(outputs.values()),
            **outputs,
        }
    elif action_kind == "capsule_validate":
        artifact_root = inputs.get("artifact_root") or inputs.get("artifact") or (ticket.linked_artifacts[0] if ticket.linked_artifacts else "")
        root = resolve_user_path(base_dir, str(artifact_root))
        capsule = build_and_write_evidence_capsule(root, output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "evidence_capsule": capsule,
            "evidence_summary": capsule,
            "linked_outputs": list((capsule.get("outputs") or {}).values()),
            **dict(capsule.get("outputs") or {}),
        }
    elif action_kind == "promotion_review":
        artifact = inputs.get("artifact") or (ticket.linked_artifacts[0] if ticket.linked_artifacts else "")
        target = str(inputs.get("target") or "validated_algorithm_candidate")
        review = review_exploratory_promotion(
            artifact=resolve_user_path(base_dir, str(artifact)),
            target=target,
        )
        outputs = write_promotion_outputs(review, output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "promotion_review": review,
            "evidence_summary": review,
            "linked_outputs": list(outputs.values()),
            **outputs,
        }
    elif action_kind == "objective_plan":
        config = inputs.get("config") or inputs.get("objective") or inputs.get("objective_config") or (ticket.linked_artifacts[0] if ticket.linked_artifacts else "")
        plan = plan_research_objective(resolve_user_path(base_dir, str(config)), output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "objective_plan": plan,
            "evidence_summary": plan,
            "linked_outputs": list((plan.get("outputs") or {}).values()),
            "plan_json": (plan.get("outputs") or {}).get("json"),
            "report_markdown": (plan.get("outputs") or {}).get("markdown"),
        }
    elif action_kind == "objective_status":
        config = inputs.get("config") or inputs.get("objective") or inputs.get("objective_config") or (ticket.linked_artifacts[0] if ticket.linked_artifacts else "")
        status = status_research_objective(resolve_user_path(base_dir, str(config)), output_root)
        payload = {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "action_kind": action_kind,
            "objective_status": status,
            "evidence_summary": status,
            "linked_outputs": list((status.get("outputs") or {}).values()),
            "status_json": (status.get("outputs") or {}).get("json"),
            "report_markdown": (status.get("outputs") or {}).get("markdown"),
        }
    else:
        raise ValueError(f"Unsupported AI action kind: {action_kind}")

    output_json = output_root / "execution_result.json"
    write_result_json(payload, output_json)
    payload.setdefault("linked_outputs", [])
    if str(output_json) not in payload["linked_outputs"]:
        payload["linked_outputs"].append(str(output_json))
    provenance_done = append_ai_provenance_event(
        workspace_base=base_dir,
        event_type="workflow_completed",
        summary=f"Completed AI action {action_kind}.",
        artifacts=payload.get("linked_outputs") or [],
        metadata={"task_id": ticket.task_id, "action_kind": action_kind, "started_event": provenance_start["event_id"]},
    )
    payload["execution_provenance"] = [provenance_start, provenance_done]
    return payload


def _ticket_workspace_root(path: Path) -> Path:
    return workspace_root(_ticket_workspace_base(path))


def _write_ticket_status(path: Path, payload: dict[str, Any], status: str) -> Path:
    root = _ticket_workspace_root(path)
    updated_payload = dict(payload)
    updated_payload["status"] = status
    return write_ticket_record(root, updated_payload)


def _empty_evidence_context(linked_artifacts: list[str]) -> dict[str, Any]:
    return {
        "graph_id": "evidence-empty",
        "sources": [],
        "best_chemistry_evidence": None,
        "best_runtime_evidence": None,
        "trust_tier": "exploratory",
        "recommended_action": "review_evidence_boundary",
        "trust_gap": [],
        "open_questions": [
            "No readable QCchem artifacts were linked to this ticket."
            if linked_artifacts
            else "No QCchem artifacts were linked to this ticket."
        ],
        "boundary_notes": [
            "LLM output is not authoritative for trust tier, hardware boundary, budget permission, or validated/exploratory promotion."
        ],
    }


def _evidence_context_for_ticket(
    *,
    base_dir: Path,
    linked_artifacts: list[str],
) -> dict[str, Any]:
    if not linked_artifacts:
        return _empty_evidence_context(linked_artifacts)
    try:
        return summarize_evidence_artifacts(linked_artifacts, workspace_base=base_dir)
    except Exception as exc:
        context = _empty_evidence_context(linked_artifacts)
        context["open_questions"].append(f"Evidence loading failed: {type(exc).__name__}: {exc}")
        return context


def _enrich_ticket_payload(
    payload: dict[str, Any],
    *,
    base_dir: Path,
    provider: Any = None,
) -> dict[str, Any]:
    enriched = dict(payload)
    linked_artifacts = [str(item) for item in enriched.get("linked_artifacts") or []]
    evidence_context = enriched.get("evidence_context")
    if not isinstance(evidence_context, dict) or not evidence_context:
        evidence_context = _evidence_context_for_ticket(base_dir=base_dir, linked_artifacts=linked_artifacts)
        enriched["evidence_context"] = evidence_context
    action_plan = enriched.get("action_plan")
    if not isinstance(action_plan, dict) or not action_plan:
        action = build_action_proposal(
            task_type=str(enriched.get("task_type") or "analysis"),
            request_text=str(enriched.get("request_text") or ""),
            linked_artifacts=linked_artifacts,
            evidence_graph=evidence_context,
        ).to_record()
        enriched["action_plan"] = action
    else:
        action = dict(action_plan)
    risk_assessment = enriched.get("risk_assessment")
    if not isinstance(risk_assessment, dict) or not risk_assessment:
        enriched["risk_assessment"] = classify_research_risk(action, evidence_context)
    cost_estimate = enriched.get("cost_estimate")
    if not isinstance(cost_estimate, dict) or not cost_estimate:
        enriched["cost_estimate"] = build_cost_estimate(action, evidence_context)
    if not enriched.get("boundary_notes"):
        enriched["boundary_notes"] = list(evidence_context.get("boundary_notes") or [])
    if provider is not None:
        drafted = draft_ticket_payload_with_optional_model(
            provider=provider,
            task_type=str(enriched.get("task_type") or "analysis"),
            request_text=str(enriched.get("request_text") or ""),
            linked_artifacts=linked_artifacts,
            evidence_graph=evidence_context,
        )
        for key in ("title", "plan_summary", "expected_outputs", "risk_notes", "boundary_notes", "model_provenance"):
            if key in {"title", "plan_summary"} and enriched.get(key):
                continue
            if drafted.get(key):
                enriched[key] = drafted[key]
        for key in ("evidence_context", "action_plan", "risk_assessment", "cost_estimate"):
            enriched.setdefault(key, drafted.get(key))
    return _sanitized_ticket_record(enriched)


def _resolved_linked_artifacts(path: Path, payload: dict[str, Any]) -> list[str]:
    return list(_resolved_ticket_payload(path, payload).get("linked_artifacts") or [])


def _default_title(task_type: str) -> str:
    if task_type == "analysis":
        return "Research Analysis Ticket"
    if task_type == "execution":
        return "Research Execution Ticket"
    if task_type == "delivery":
        return "Research Delivery Ticket"
    return "Research Ticket"


def _build_ticket_payload(
    *,
    task_type: str,
    title: str,
    request_text: str,
    linked_artifacts_text: str,
    plan_summary: str,
    expected_outputs_text: str,
    risk_notes_text: str,
) -> dict[str, Any]:
    linked_artifacts = _normalize_text_lines(linked_artifacts_text)
    expected_outputs = _normalize_text_lines(expected_outputs_text)
    risk_notes = _normalize_text_lines(risk_notes_text)
    normalized_title = title.strip() or _default_title(task_type)
    return {
        "task_type": task_type,
        "title": normalized_title,
        "request_text": request_text.strip(),
        "plan_summary": plan_summary.strip(),
        "expected_outputs": expected_outputs,
        "risk_notes": risk_notes,
        "linked_artifacts": linked_artifacts,
    }


def build_ticket_from_form(
    *,
    task_type: str,
    title: str,
    request_text: str,
    linked_artifacts_text: str,
    plan_summary: str,
    expected_outputs_text: str,
    risk_notes_text: str,
) -> AITaskTicket:
    payload = _build_ticket_payload(
        task_type=task_type,
        title=title,
        request_text=request_text,
        linked_artifacts_text=linked_artifacts_text,
        plan_summary=plan_summary,
        expected_outputs_text=expected_outputs_text,
        risk_notes_text=risk_notes_text,
    )
    status = AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION
    if payload["task_type"] == "analysis":
        return draft_analysis_ticket(
            request_text=payload["request_text"],
            structured_payload={
                "title": payload["title"],
                "plan_summary": payload["plan_summary"],
                "expected_outputs": payload["expected_outputs"],
                "risk_notes": payload["risk_notes"],
            },
            linked_artifacts=payload["linked_artifacts"],
        )
    return AITaskTicket(
        task_id=f"{task_type}-{uuid.uuid4().hex[:10]}",
        task_type=task_type,
        title=payload["title"],
        request_text=payload["request_text"],
        plan_summary=payload["plan_summary"],
        expected_outputs=payload["expected_outputs"],
        risk_notes=payload["risk_notes"],
        linked_artifacts=payload["linked_artifacts"],
        status=status,
        execution_target="analysis_only_assistant",
    )


def classify_execution_risk(payload: dict[str, Any]) -> dict[str, Any]:
    existing = payload.get("risk_assessment")
    if (
        isinstance(existing, dict)
        and existing.get("is_high_risk") is True
        and "risk_tier" in existing
    ):
        return existing

    task_type = str(payload.get("task_type", "")).strip().lower()
    action_plan = payload.get("action_plan") if isinstance(payload.get("action_plan"), dict) else {}
    action_kind = str((action_plan or {}).get("action_kind") or "").strip()
    if (
        task_type != "execution"
        and action_kind not in {"runtime_collect", "hardware_optimize_preview"}
        and not (
            action_kind == "promotion_review"
            and "validated" in str((action_plan or {}).get("inputs", {}).get("target") or payload.get("request_text") or "").lower()
        )
    ):
        return {
            "is_high_risk": False,
            "risk_tier": "standard",
            "reasons": [],
            "confirm_run": False,
        }

    text_sources = [
        str(payload.get("title", "")),
        str(payload.get("request_text", "")),
        str(payload.get("plan_summary", "")),
        " ".join(str(item) for item in payload.get("expected_outputs") or []),
        " ".join(str(item) for item in payload.get("risk_notes") or []),
        " ".join(str(item) for item in payload.get("linked_artifacts") or []),
        action_kind,
    ]
    lowered = " ".join(text_sources).lower()
    reasons: list[str] = []
    if isinstance(existing, dict):
        reasons.extend(str(reason) for reason in existing.get("reasons") or [])
    keyword_reasons = {
        "runtime": "mentions runtime-backed execution",
        "benchmark": "mentions benchmark execution",
        "hardware": "references hardware-facing execution",
        "submit": "suggests an externally submitted run",
        "production": "touches production-sensitive work",
        "deploy": "touches deployment-sensitive work",
        "destructive": "contains destructive language",
        "execute": "explicitly requests execution",
        "run": "explicitly requests a run",
        "queue": "references a queued execution path",
        "promotion": "requests a trust-tier promotion review",
        "validated": "mentions validated evidence language",
    }
    if action_plan.get("allowed") is False:
        reasons.append(str(action_plan.get("blocked_reason") or "action is blocked by local policy"))
    if action_kind == "runtime_collect":
        reasons.append("runtime_collect requires an existing sidecar and high-risk confirmation")
    if action_kind == "hardware_optimize_preview":
        reasons.append("hardware optimization preview touches hardware-facing planning state")
    for keyword, reason in keyword_reasons.items():
        if keyword in lowered:
            reasons.append(reason)

    if not reasons and payload.get("linked_artifacts"):
        reasons.append("links artifacts that may be execution-sensitive")

    return {
        "is_high_risk": bool(reasons),
        "risk_tier": "high" if reasons else "standard",
        "reasons": sorted(set(reasons)),
        "confirm_run": bool(reasons),
    }


def _load_ticket_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def accept_ticket(path: Path) -> dict[str, Any]:
    payload = _load_ticket_payload(path)
    updated_path = _write_ticket_status(path, payload, AI_WORKSPACE_TICKET_STATUS_ACCEPTED)
    accepted = dict(payload)
    accepted["status"] = AI_WORKSPACE_TICKET_STATUS_ACCEPTED
    accepted["ticket_path"] = str(updated_path)
    return accepted


def return_ticket(path: Path) -> dict[str, Any]:
    payload = _load_ticket_payload(path)
    updated_path = _write_ticket_status(path, payload, AI_WORKSPACE_TICKET_STATUS_RETURNED)
    returned = dict(payload)
    returned["status"] = AI_WORKSPACE_TICKET_STATUS_RETURNED
    returned["ticket_path"] = str(updated_path)
    return returned


def _write_delivery(
    ticket: AITaskTicket,
    *,
    root: Path,
    delivery_kind: str,
    summary: str,
    outputs: list[str],
    evidence_summary: dict[str, Any] | None = None,
) -> dict[str, object]:
    delivery = AIDeliveryRecord(
        delivery_id=f"delivery-{uuid.uuid4().hex[:10]}",
        task_id=ticket.task_id,
        delivery_kind=delivery_kind,
        summary=summary,
        linked_outputs=outputs,
        evidence_summary=evidence_summary,
    )
    path = write_delivery_record(root, delivery.to_record())
    return {
        "delivery_record": str(path),
        "linked_outputs": delivery.linked_outputs,
        "review_status": delivery.review_status,
    }


def draft_ticket_from_form(
    *,
    task_type: str,
    title: str,
    request_text: str,
    linked_artifacts_text: str,
    plan_summary: str,
    expected_outputs_text: str,
    risk_notes_text: str,
    workspace_base: Path | str | None = None,
) -> Path:
    ticket = build_ticket_from_form(
        task_type=task_type,
        title=title,
        request_text=request_text,
        linked_artifacts_text=linked_artifacts_text,
        plan_summary=plan_summary,
        expected_outputs_text=expected_outputs_text,
        risk_notes_text=risk_notes_text,
    )
    root = workspace_root(Path(workspace_base) if workspace_base is not None else Path.cwd())
    return write_ticket_record(root, _ticket_record(ticket))


def draft_ticket_from_request(
    *,
    provider_config: Path,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
) -> Path:
    """Draft one AI workspace ticket from a free-form request."""
    provider = load_ai_provider_spec(provider_config)
    ticket = build_ticket_from_form(
        task_type=task_type,
        title="",
        request_text=request_text,
        linked_artifacts_text="\n".join(linked_artifacts),
        plan_summary="",
        expected_outputs_text="",
        risk_notes_text="",
    )
    root = workspace_root(Path.cwd())
    payload = _enrich_ticket_payload(
        _ticket_record(ticket),
        base_dir=Path.cwd(),
        provider=provider,
    )
    return write_ticket_record(root, payload)


def _materialize_ticket_payload(
    *,
    task_type: str,
    title: str,
    request_text: str,
    linked_artifacts_text: str,
    plan_summary: str,
    expected_outputs_text: str,
    risk_notes_text: str,
    workspace_base: Path | str | None,
    current_ticket_path: str | None,
    current_ticket_record: dict[str, Any] | None,
) -> tuple[Path, dict[str, Any]]:
    workspace_base_path = Path(workspace_base) if workspace_base is not None else Path.cwd()
    ticket_root = workspace_root(workspace_base_path)
    payload = _build_ticket_payload(
        task_type=task_type,
        title=title,
        request_text=request_text,
        linked_artifacts_text=linked_artifacts_text,
        plan_summary=plan_summary,
        expected_outputs_text=expected_outputs_text,
        risk_notes_text=risk_notes_text,
    )
    if current_ticket_record is not None:
        ticket_payload = dict(current_ticket_record)
        ticket_payload.update(payload)
        ticket_payload.setdefault("execution_target", "analysis_only_assistant")
        ticket_payload.setdefault("status", AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION)
        ticket_payload = _enrich_ticket_payload(
            ticket_payload,
            base_dir=workspace_base_path,
        )
        ticket_path = (
            Path(current_ticket_path)
            if current_ticket_path
            else ticket_root / "tickets" / f"{ticket_payload['task_id']}.json"
        )
        return ticket_path, ticket_payload
    ticket = build_ticket_from_form(
        task_type=task_type,
        title=title,
        request_text=request_text,
        linked_artifacts_text=linked_artifacts_text,
        plan_summary=plan_summary,
        expected_outputs_text=expected_outputs_text,
        risk_notes_text=risk_notes_text,
    )
    ticket_path = write_ticket_record(ticket_root, _ticket_record(ticket))
    ticket_payload = _enrich_ticket_payload(
        _ticket_record(ticket),
        base_dir=workspace_base_path,
    )
    write_ticket_record(ticket_root, ticket_payload)
    return ticket_path, ticket_payload


def _editor_noop(
    *,
    action: str,
    message: str,
    task_type: str,
    title: str,
    request_text: str,
    linked_artifacts_text: str,
    plan_summary: str,
    expected_outputs_text: str,
    risk_notes_text: str,
    current_ticket_path: str | None,
    current_ticket_record: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = _build_ticket_payload(
        task_type=task_type,
        title=title,
        request_text=request_text,
        linked_artifacts_text=linked_artifacts_text,
        plan_summary=plan_summary,
        expected_outputs_text=expected_outputs_text,
        risk_notes_text=risk_notes_text,
    )
    fallback_record = dict(current_ticket_record or payload)
    fallback_record.setdefault("status", AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION)
    return {
        "action": action,
        "current_ticket_path": current_ticket_path,
        "current_ticket_record": fallback_record,
        "guard_state": {
            "visible": True,
            "confirmed": False,
            "risk": classify_execution_risk(fallback_record),
            "message": message,
        },
        "did_change_workspace": False,
    }


def handle_ticket_editor_action(
    *,
    action: str,
    task_type: str,
    title: str,
    request_text: str,
    linked_artifacts_text: str,
    plan_summary: str,
    expected_outputs_text: str,
    risk_notes_text: str,
    current_ticket_path: str | None = None,
    current_ticket_record: dict[str, Any] | None = None,
    guard_state: dict[str, Any] | None = None,
    workspace_base: Path | str | None = None,
) -> dict[str, Any]:
    if action != "draft" and current_ticket_record is None:
        return _editor_noop(
            action=action,
            message="Draft the ticket first so QCchem has a persisted record to accept or execute.",
            task_type=task_type,
            title=title,
            request_text=request_text,
            linked_artifacts_text=linked_artifacts_text,
            plan_summary=plan_summary,
            expected_outputs_text=expected_outputs_text,
            risk_notes_text=risk_notes_text,
            current_ticket_path=current_ticket_path,
            current_ticket_record=current_ticket_record,
        )
    ticket_path, ticket_record = _materialize_ticket_payload(
        task_type=task_type,
        title=title,
        request_text=request_text,
        linked_artifacts_text=linked_artifacts_text,
        plan_summary=plan_summary,
        expected_outputs_text=expected_outputs_text,
        risk_notes_text=risk_notes_text,
        workspace_base=workspace_base,
        current_ticket_path=current_ticket_path,
        current_ticket_record=current_ticket_record,
    )
    risk = classify_execution_risk(ticket_record)
    guard_visible = bool((guard_state or {}).get("visible", False))

    if action == "draft":
        result_record = dict(ticket_record)
        result_record["status"] = AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION
        persisted_path = ticket_path
        if current_ticket_record is not None:
            persisted_path = write_ticket_record(
                _ticket_workspace_root(ticket_path),
                _sanitized_ticket_record(result_record),
            )
        return {
            "action": action,
            "current_ticket_path": str(persisted_path),
            "current_ticket_record": result_record,
            "guard_state": {"visible": False, "risk": risk},
            "did_change_workspace": True,
        }

    if action == "return":
        persisted_path = write_ticket_record(_ticket_workspace_root(ticket_path), _sanitized_ticket_record(ticket_record))
        if persisted_path.exists():
            returned = return_ticket(persisted_path)
        else:
            returned = dict(ticket_record)
            returned["status"] = AI_WORKSPACE_TICKET_STATUS_RETURNED
        return {
            "action": action,
            "current_ticket_path": str(persisted_path),
            "current_ticket_record": returned,
            "guard_state": {"visible": False, "risk": risk},
            "did_change_workspace": True,
        }

    if action == "accept":
        persisted_path = write_ticket_record(_ticket_workspace_root(ticket_path), _sanitized_ticket_record(ticket_record))
        if ticket_record.get("status") != AI_WORKSPACE_TICKET_STATUS_ACCEPTED:
            accepted = accept_ticket(persisted_path)
        else:
            accepted = dict(ticket_record)
            accepted["ticket_path"] = str(persisted_path)
        return {
            "action": action,
            "current_ticket_path": str(persisted_path),
            "current_ticket_record": accepted,
            "guard_state": {"visible": False, "risk": risk},
            "did_change_workspace": True,
        }

    if action in {"run", "confirm_run"}:
        persisted_path = ticket_path
        if ticket_record.get("status") != AI_WORKSPACE_TICKET_STATUS_ACCEPTED:
            return _editor_noop(
                action=action,
                message="Accept the draft ticket before QCchem starts any execution path.",
                task_type=task_type,
                title=title,
                request_text=request_text,
                linked_artifacts_text=linked_artifacts_text,
                plan_summary=plan_summary,
                expected_outputs_text=expected_outputs_text,
                risk_notes_text=risk_notes_text,
                current_ticket_path=str(persisted_path),
                current_ticket_record=ticket_record,
            )
        if action == "run" and risk["is_high_risk"]:
            return {
                "action": action,
                "current_ticket_path": str(persisted_path),
                "current_ticket_record": ticket_record,
                "guard_state": {
                    "visible": True,
                    "confirmed": False,
                    "risk": risk,
                    "message": "High-risk execution requires confirmation before the run can start.",
                },
                "did_change_workspace": False,
            }
        if action == "confirm_run" and not guard_visible and risk["is_high_risk"]:
            return _editor_noop(
                action=action,
                message="Open the guarded run confirmation from the Run button before confirming execution.",
                task_type=task_type,
                title=title,
                request_text=request_text,
                linked_artifacts_text=linked_artifacts_text,
                plan_summary=plan_summary,
                expected_outputs_text=expected_outputs_text,
                risk_notes_text=risk_notes_text,
                current_ticket_path=str(persisted_path),
                current_ticket_record=ticket_record,
            )
        if action == "confirm_run" or not risk["is_high_risk"]:
            if action == "confirm_run":
                ticket_record = dict(ticket_record)
                ticket_record["risk_assessment"] = {
                    **dict(ticket_record.get("risk_assessment") or risk),
                    "confirmed_high_risk": True,
                }
            persisted_path = write_ticket_record(
                _ticket_workspace_root(ticket_path),
                _sanitized_ticket_record(ticket_record),
            )
        executed = run_ticket(persisted_path)
        refreshed_record = _load_ticket_payload(persisted_path)
        return {
            "action": action,
            "current_ticket_path": str(persisted_path),
            "current_ticket_record": refreshed_record,
            "guard_state": {"visible": False, "confirmed": True, "risk": risk},
            "did_change_workspace": True,
            "execution_result": executed,
        }

    raise ValueError(f"Unsupported ticket editor action: {action}")


def run_ticket(path: Path) -> dict[str, object]:
    """Execute one accepted AI workspace ticket."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    ticket = AITaskTicket(**payload)
    if ticket.status != AI_WORKSPACE_TICKET_STATUS_ACCEPTED:
        raise ValueError("Only accepted AI workspace tickets can be executed.")
    ticket_root = _ticket_workspace_root(path)
    _write_ticket_status(path, payload, AI_WORKSPACE_TICKET_STATUS_RUNNING)
    if ticket.action_plan:
        try:
            result = _run_action_ticket(ticket, path)
        except Exception as exc:
            blocked_payload = dict(payload)
            blocked_payload["status"] = AI_WORKSPACE_TICKET_STATUS_BLOCKED
            blocked_payload.setdefault("execution_provenance", [])
            blocked_payload["execution_provenance"].append(
                append_ai_provenance_event(
                    workspace_base=_ticket_workspace_base(path),
                    event_type="workflow_blocked",
                    summary=f"AI action blocked or failed: {type(exc).__name__}: {exc}",
                    artifacts=ticket.linked_artifacts,
                    metadata={"task_id": ticket.task_id, "action_plan": ticket.action_plan},
                )
            )
            write_ticket_record(ticket_root, _sanitized_ticket_record(blocked_payload))
            raise
        delivery_kind = str(result.get("delivery_kind") or "artifact_bundle")
        delivery = _write_delivery(
            ticket,
            root=ticket_root,
            delivery_kind=delivery_kind,
            summary=f"{ticket.title} completed.",
            outputs=_delivery_outputs_from_result(result),
            evidence_summary=(
                result.get("evidence_summary")
                if isinstance(result.get("evidence_summary"), dict)
                else (result.get("evidence_graph") if isinstance(result.get("evidence_graph"), dict) else None)
            ),
        )
        completed_payload = dict(payload)
        completed_payload["status"] = AI_WORKSPACE_TICKET_STATUS_COMPLETED
        completed_payload["execution_provenance"] = result.get("execution_provenance", [])
        write_ticket_record(ticket_root, _sanitized_ticket_record(completed_payload))
        return {**result, **delivery}
    if ticket.task_type in {"analysis", "execution"}:
        result = run_analysis_ticket(_resolved_ticket_payload(path, payload))
        delivery_kind = "analysis_note" if ticket.task_type == "analysis" else "artifact_bundle"
        delivery_summary = (
            "Analysis ticket completed."
            if ticket.task_type == "analysis"
            else "Execution ticket completed."
        )
        delivery = _write_delivery(
            ticket,
            root=ticket_root,
            delivery_kind=delivery_kind,
            summary=delivery_summary,
            outputs=_delivery_outputs_from_result(result),
            evidence_summary=(result.get("summary") or {}).get("evidence_summary")
            if isinstance(result.get("summary"), dict)
            else None,
        )
        result["delivery_kind"] = delivery_kind
        _write_ticket_status(path, payload, AI_WORKSPACE_TICKET_STATUS_COMPLETED)
        return {**result, **delivery}
    if ticket.task_type == "delivery":
        delivery = _write_delivery(
            ticket,
            root=ticket_root,
            delivery_kind="artifact_bundle",
            summary="Delivery ticket submitted.",
            outputs=_resolved_linked_artifacts(path, payload),
            evidence_summary=None,
        )
        _write_ticket_status(path, payload, AI_WORKSPACE_TICKET_STATUS_SUBMITTED)
        return {
            "task_id": ticket.task_id,
            "status": "submitted",
            "delivery_kind": "artifact_bundle",
            **delivery,
        }
    raise ValueError(f"Unsupported ticket execution path: {ticket.task_type}")
