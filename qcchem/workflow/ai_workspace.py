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


def _draft_ticket(
    *,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
) -> AITaskTicket:
    if task_type == "analysis":
        return draft_analysis_ticket(
            request_text=request_text,
            structured_payload={
                "title": "Research Analysis Ticket",
                "plan_summary": "Read the linked QCchem artifacts, summarize the main findings, and produce a recommendation.",
                "expected_outputs": ["analysis summary", "follow-up recommendation"],
                "risk_notes": ["Respect validated, exploratory, and unstable boundaries in the write-up."],
            },
            linked_artifacts=linked_artifacts,
        )
    if task_type == "execution":
        return AITaskTicket(
            task_id=f"execution-{uuid.uuid4().hex[:10]}",
            task_type="execution",
            title="Research Execution Ticket",
            request_text=request_text,
            plan_summary="Run the linked QCchem artifacts through the existing execution path and bundle the outputs.",
            expected_outputs=["execution summary", "artifact bundle"],
            risk_notes=["Respect validated, exploratory, and unstable boundaries in the write-up."],
            linked_artifacts=linked_artifacts,
            status="needs_confirmation",
            execution_target="analysis_only_assistant",
        )
    if task_type == "delivery":
        return AITaskTicket(
            task_id=f"delivery-{uuid.uuid4().hex[:10]}",
            task_type="delivery",
            title="Research Delivery Ticket",
            request_text=request_text,
            plan_summary="Prepare the linked QCchem artifacts for delivery and record the submission.",
            expected_outputs=["delivery record", "linked outputs"],
            risk_notes=["Respect validated, exploratory, and unstable boundaries in the write-up."],
            linked_artifacts=linked_artifacts,
            status="needs_confirmation",
            execution_target="analysis_only_assistant",
        )
    raise ValueError(f"Unsupported AI workspace task type: {task_type}")


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


def draft_ticket_from_request(
    *,
    provider_config: Path,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
) -> Path:
    """Draft one AI workspace ticket from a free-form request."""
    _provider = load_ai_provider_spec(provider_config)
    ticket = _draft_ticket(
        task_type=task_type,
        request_text=request_text,
        linked_artifacts=linked_artifacts,
    )
    return write_ticket_record(workspace_root(Path.cwd()), _ticket_record(ticket))


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
