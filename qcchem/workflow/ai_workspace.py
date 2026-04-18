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
    AI_WORKSPACE_TICKET_STATUS_COMPLETED,
    AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
    AI_WORKSPACE_TICKET_STATUS_RETURNED,
    AI_WORKSPACE_TICKET_STATUS_RUNNING,
    AI_WORKSPACE_TICKET_STATUS_SUBMITTED,
)
from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.io.config import resolve_user_path
from qcchem.workflow.ai_assistant import draft_analysis_ticket
from qcchem.workflow.ai_store import workspace_root, write_delivery_record, write_ticket_record
from qcchem.workflow.agent import run_analysis_ticket


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
    summaries = result.get("summaries") or []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        for key in ("summary_json", "report_markdown"):
            output = summary.get(key)
            if isinstance(output, str) and output:
                outputs.append(output)
    return outputs


def _ticket_workspace_root(path: Path) -> Path:
    return workspace_root(_ticket_workspace_base(path))


def _write_ticket_status(path: Path, payload: dict[str, Any], status: str) -> Path:
    root = _ticket_workspace_root(path)
    updated_payload = dict(payload)
    updated_payload["status"] = status
    return write_ticket_record(root, updated_payload)


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
    task_type = str(payload.get("task_type", "")).strip().lower()
    if task_type != "execution":
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
    ]
    lowered = " ".join(text_sources).lower()
    reasons: list[str] = []
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
    }
    for keyword, reason in keyword_reasons.items():
        if keyword in lowered:
            reasons.append(reason)

    if not reasons and payload.get("linked_artifacts"):
        reasons.append("links artifacts that may be execution-sensitive")

    return {
        "is_high_risk": bool(reasons),
        "risk_tier": "high" if reasons else "standard",
        "reasons": reasons,
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
) -> dict[str, object]:
    delivery = AIDeliveryRecord(
        delivery_id=f"delivery-{uuid.uuid4().hex[:10]}",
        task_id=ticket.task_id,
        delivery_kind=delivery_kind,
        summary=summary,
        linked_outputs=outputs,
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
    _provider = load_ai_provider_spec(provider_config)
    ticket = build_ticket_from_form(
        task_type=task_type,
        title="",
        request_text=request_text,
        linked_artifacts_text="\n".join(linked_artifacts),
        plan_summary="",
        expected_outputs_text="",
        risk_notes_text="",
    )
    return write_ticket_record(workspace_root(Path.cwd()), _ticket_record(ticket))


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
        ticket_payload = _sanitized_ticket_record(ticket_payload)
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
    return ticket_path, _ticket_record(ticket)


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
    did_change_workspace = False

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
        )
        _write_ticket_status(path, payload, AI_WORKSPACE_TICKET_STATUS_SUBMITTED)
        return {
            "task_id": ticket.task_id,
            "status": "submitted",
            "delivery_kind": "artifact_bundle",
            **delivery,
        }
    raise ValueError(f"Unsupported ticket execution path: {ticket.task_type}")
