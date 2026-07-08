from __future__ import annotations

import importlib
import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from qcchem.core.ai_workspace import (
    AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_LANE_RETURNED,
    AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
    AI_WORKSPACE_TICKET_STATUS_COMPLETED,
    AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
    AI_WORKSPACE_TICKET_STATUS_RETURNED,
)
from qcchem.workflow.ai_store import (
    list_delivery_records,
    list_ticket_records,
    workspace_root,
    write_delivery_record,
    write_ticket_record,
)
from qcchem.workflow.ai_workspace import (
    accept_ticket,
    draft_ticket_from_form,
    handle_ticket_editor_action,
    run_ticket,
)
from qcchem.workbench.app import create_app
from qcchem.workbench.components.assistant import build_provider_config, build_provider_summary_content

REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve_layout(layout: object) -> object:
    return layout() if callable(layout) else layout


def _walk_components(component: object) -> Iterable[object]:
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from _walk_components(child)
    else:
        yield from _walk_components(children)


def _find_component(component: object, target_id: str) -> object | None:
    for candidate in _walk_components(component):
        if getattr(candidate, "id", None) == target_id:
            return candidate
    return None


@pytest.mark.integration
def test_workbench_registers_ai_workspace_page() -> None:
    app = create_app()

    paths = {page["path"] for page in app.page_registry.values()}

    assert "/ai-workspace" in paths


@pytest.mark.integration
def test_workbench_shell_contains_floating_assistant_ids() -> None:
    app = create_app()
    layout = _resolve_layout(app.layout)
    rendered = str(layout)

    assert "qcchem-ai-assistant-window" in rendered
    assert "qcchem-ai-provider-drawer" in rendered
    assert "qcchem-ai-provider-config" in rendered
    assert "qcchem-ai-provider-summary" in rendered
    assert "qcchem-ai-current-ticket-preview" in rendered
    assert "Placeholder controls only for now" not in rendered


@pytest.mark.integration
def test_workbench_shell_contains_ticket_editor_controls() -> None:
    app = create_app()
    layout = _resolve_layout(app.layout)
    rendered = str(layout)

    assert "qcchem-ai-assistant-drag-handle" in rendered
    assert "qcchem-ai-assistant-resize-handle" in rendered
    assert "qcchem-ai-task-type" in rendered
    assert "qcchem-ai-title-input" in rendered
    assert "qcchem-ai-linked-artifacts-input" in rendered
    assert "qcchem-ai-plan-summary-input" in rendered
    assert "qcchem-ai-expected-outputs-input" in rendered
    assert "qcchem-ai-risk-notes-input" in rendered
    assert "qcchem-ai-accept-ticket" in rendered
    assert "qcchem-ai-run-ticket" in rendered
    assert "qcchem-ai-confirm-run" in rendered
    assert "qcchem-ai-return-ticket" in rendered
    assert "qcchem-ai-run-guard" in rendered


@pytest.mark.integration
def test_workbench_shell_registers_dash_owned_ai_shell_state_callbacks() -> None:
    app = create_app()
    layout = _resolve_layout(app.layout)
    store_ids = {
        component.id
        for component in _walk_components(layout)
        if getattr(component, "id", None) == "qcchem-ai-shell-ui-state"
    }

    assert "qcchem-ai-shell-ui-state" in store_ids
    assert "qcchem-ai-shell-ui-state.data" in app.callback_map
    assert "qcchem-ai-assistant-body.hidden" in app.callback_map
    assert "qcchem-ai-assistant-minimize.children" in app.callback_map
    assert "qcchem-ai-provider-drawer.hidden" in app.callback_map
    assert "qcchem-ai-provider-config.data" in app.callback_map
    assert "qcchem-ai-provider-summary.children" in app.callback_map


@pytest.mark.integration
def test_provider_drawer_normalizes_state_without_secret_storage() -> None:
    config = build_provider_config(
        " https://api.example.com/v1 ",
        " gpt-5.4 ",
        " OPENAI_API_KEY ",
    )

    assert config == {
        "provider_kind": "openai_compatible",
        "base_url": "https://api.example.com/v1",
        "model": "gpt-5.4",
        "api_key_ref": "OPENAI_API_KEY",
        "status": "reference_ready",
    }

    summary = str(build_provider_summary_content(config))
    assert "Reference ready" in summary
    assert "https://api.example.com/v1" in summary
    assert "gpt-5.4" in summary
    assert "OPENAI_API_KEY" in summary
    assert "sk-" not in summary


@pytest.mark.integration
def test_provider_drawer_marks_partial_profiles() -> None:
    config = build_provider_config("", "gpt-5.4", "")

    assert config["status"] == "partial"
    assert "Partial" in str(build_provider_summary_content(config))


@pytest.mark.integration
def test_workbench_shell_registers_ticket_editor_callbacks() -> None:
    app = create_app()
    callback_outputs = "\n".join(app.callback_map.keys())

    assert "qcchem-ai-current-ticket-preview.children" in app.callback_map
    assert "qcchem-ai-current-ticket-record.data" in callback_outputs
    assert "qcchem-ai-current-ticket-path.data" in callback_outputs
    assert "qcchem-ai-task-inbox.children" in app.callback_map
    assert "qcchem-ai-delivery-history.children" in app.callback_map
    assert "qcchem-ai-delivery-review-filter.options" in callback_outputs
    assert "qcchem-ai-delivery-kind-filter.options" in callback_outputs


@pytest.mark.integration
def test_assistant_window_asset_supports_drag_and_resize_behavior() -> None:
    script = (REPO_ROOT / "qcchem" / "workbench" / "assets" / "assistant-window.js").read_text(encoding="utf-8")

    assert "qcchem-ai-assistant-drag-handle" in script
    assert "qcchem-ai-assistant-resize-handle" in script
    assert "qcchem-ai-assistant-reset-position" in script
    assert "safeViewportTop" in script
    assert "minWindowWidth" in script
    assert "COMPACT_MIN_HEIGHT" in script
    assert "allowCompactHeight" in script
    assert "localStorage" in script
    assert "pointerdown" in script
    assert "dblclick" in script
    assert "clamp" in script or "Math.min" in script
    assert "MutationObserver" in script or "requestAnimationFrame" in script


@pytest.mark.integration
def test_ai_workspace_page_exposes_state_backed_task_lanes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    rendered = str(page)

    assert "AI Workspace" in rendered
    assert "qcchem-ai-task-inbox" in rendered
    assert "qcchem-ai-task-running" in rendered
    assert "qcchem-ai-task-submitted" in rendered
    assert "qcchem-ai-task-completed" in rendered
    assert "qcchem-ai-task-returned" in rendered
    assert "qcchem-ai-workspace-page__placeholder" not in rendered
    assert "Records" in rendered
    assert "Latest" in rendered
    assert "Source" in rendered
    assert "0 persisted inbox tickets found" in rendered
    assert "artifacts/ai_workspace/tickets" in rendered


@pytest.mark.integration
def test_ai_workspace_page_reads_persisted_ticket_inbox(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = workspace_root(tmp_path)
    write_ticket_record(
        root,
        {
            "task_id": "ticket-inbox-001",
            "task_type": "analysis",
            "title": "Explain H2 runtime gap",
            "request_text": "Explain the recent runtime gap",
            "status": AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
        },
    )

    app = create_app()
    rendered = str(_resolve_layout(app.validation_layout))

    assert "ticket-inbox-001" in rendered or "Explain H2 runtime gap" in rendered
    assert "ticket-inbox-001 - Explain H2 runtime gap" in rendered
    assert "Records" in rendered
    assert list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX)[0]["task_id"] == "ticket-inbox-001"


@pytest.mark.integration
def test_ai_workspace_page_render_does_not_create_workspace_directories(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")

    assert not (tmp_path / "artifacts" / "ai_workspace").exists()

    rendered = str(_resolve_layout(page_module.layout))

    assert not (tmp_path / "artifacts" / "ai_workspace").exists()
    assert "0 persisted inbox tickets found" in rendered
    assert "0 persisted delivery records found" in rendered


@pytest.mark.integration
def test_ai_workspace_page_reads_completed_ticket_after_execution(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    workspace = tmp_path
    suite_dir = workspace / "artifacts" / "suite_a"
    suite_dir.mkdir(parents=True, exist_ok=True)
    (suite_dir / "hardware_calibration_summary.json").write_text(
        """
{
  "suite_name": "suite_a",
  "artifact_root": "",
  "summary": {
    "total_cases": 1,
    "runtime_evidence_status_counts": {"retrieved_result": 1}
  },
  "cases": [
    {
      "name": "case_a",
      "achieved_error": 0.012,
      "meets_chemical_accuracy": false
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    ticket_root = workspace_root(workspace)
    ticket_dir = ticket_root / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = ticket_dir / "analysis-003.json"
    write_ticket_record(
        ticket_root,
        {
            "task_id": "analysis-003",
            "task_type": "analysis",
            "title": "Compare hardware campaign",
            "request_text": "Compare hardware campaign results",
            "plan_summary": "Summarize suite status and best case.",
            "expected_outputs": ["summary"],
            "risk_notes": ["Do not overstate validated status."],
            "linked_artifacts": ["artifacts/suite_a"],
            "status": AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
            "execution_target": "analysis_only_assistant",
        },
    )

    run_ticket(ticket_path)

    persisted_ticket = next(iter(list_ticket_records(ticket_root, lane=AI_WORKSPACE_TICKET_LANE_COMPLETED)))
    assert persisted_ticket["status"] == AI_WORKSPACE_TICKET_STATUS_COMPLETED
    assert persisted_ticket["task_id"] == "analysis-003"

    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    completed_lane = _find_component(page, "qcchem-ai-task-completed")
    inbox_lane = _find_component(page, "qcchem-ai-task-inbox")

    assert completed_lane is not None
    assert inbox_lane is not None
    assert "analysis-003" in str(completed_lane)
    assert "Compare hardware campaign" in str(completed_lane)
    assert "analysis-003" not in str(inbox_lane)


@pytest.mark.integration
def test_ai_workspace_delivery_renders_workflow_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    workflow_root = tmp_path / "artifacts" / "workflows" / "demo_flow"
    workflow_root.mkdir(parents=True)
    (workflow_root / "workflow_result.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.workflow_run.v0.1-alpha",
                "workflow_name": "demo_flow",
                "status": "completed",
                "summary": {"completed_steps": 2, "failed_steps": 0, "generated_steps": 1},
                "acceptance_summary": {
                    "accepted": True,
                    "recommended_action": "promote_workflow_outputs",
                    "blocking_failures": [],
                    "warnings": [],
                },
                "outputs": {"workflow_report_markdown": str(workflow_root / "workflow_report.md")},
            }
        ),
        encoding="utf-8",
    )

    ticket_root = workspace_root(tmp_path)
    write_ticket_record(
        ticket_root,
        {
            "task_id": "workflow-summary-001",
            "task_type": "analysis",
            "title": "Summarize workflow",
            "request_text": "Summarize the demo workflow artifact",
            "linked_artifacts": ["artifacts/workflows/demo_flow"],
            "status": AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
            "action_plan": {
                "action_id": "action-workflow-summary",
                "action_kind": "workflow_summarize",
                "inputs": {"target": "artifacts/workflows/demo_flow"},
                "allowed": True,
            },
        },
    )

    run_ticket(ticket_root / "tickets" / "workflow-summary-001.json")
    delivery = list_delivery_records(ticket_root)[0]
    assert delivery["workflow_summary"]["workflow_name"] == "demo_flow"
    assert delivery["workflow_summary"]["acceptance_summary"]["accepted"] is True

    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    delivery_history = _find_component(page, "qcchem-ai-delivery-history")

    assert delivery_history is not None
    rendered = str(delivery_history)
    assert "demo_flow" in rendered
    assert "completed" in rendered
    assert "accepted" in rendered
    assert "Records" in rendered
    assert "Review" in rendered
    assert "2 completed / 0 failed / 1 generated" in rendered
    assert "promote_workflow_outputs" in rendered
    assert "Review artifacts" in rendered
    assert "Workflow result" in rendered
    assert "Workflow report" in rendered
    assert "workflow_result.json" in rendered
    assert "workflow_report.md" in rendered
    assert "review linked outputs (review_linked_outputs)" in rendered


@pytest.mark.integration
def test_ai_workspace_delivery_renders_artifact_handoff_and_return_notes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    ticket_root = workspace_root(tmp_path)
    write_delivery_record(
        ticket_root,
        {
            "delivery_id": "delivery-returned-001",
            "task_id": "analysis-returned-001",
            "delivery_kind": "analysis_note",
            "summary": "Review H2 evidence handoff.",
            "linked_outputs": [
                "artifacts/ai_workspace/reviews/h2_claim/claim_review.json",
                "artifacts/ai_workspace/reviews/h2_claim/claim_review.md",
            ],
            "review_status": "returned",
            "reviewed_at": "2026-07-08T10:30:00Z",
            "reviewed_by": "lead-reviewer",
            "review_source": "cli",
            "return_notes": "Attach the exact baseline result path before closing.",
            "evidence_scope": "artifacts/h2_local",
            "limitation_notes": "Do not promote exploratory wording.",
            "evidence_summary": {
                "trust_tier": "exploratory",
                "primary_scientific_claim": "H2 claim needs baseline review.",
                "recommended_action": "review_evidence_boundary",
            },
        },
    )

    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    delivery_history = _find_component(page, "qcchem-ai-delivery-history")

    assert delivery_history is not None
    rendered = str(delivery_history)
    assert "Review artifacts" in rendered
    assert "Evidence scope" in rendered
    assert "artifacts/h2_local" in rendered
    assert "Linked output 1" in rendered
    assert "claim_review.json" in rendered
    assert "claim_review.md" in rendered
    assert "Review action" in rendered
    assert "address return notes (address_return_notes)" in rendered
    assert "Reviewed" in rendered
    assert "2026-07-08T10:30:00Z" in rendered
    assert "lead-reviewer via cli" in rendered
    assert "Return notes" in rendered
    assert "Attach the exact baseline result path before closing." in rendered


@pytest.mark.integration
def test_ai_workspace_delivery_history_filters_and_summarizes_handoffs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    ticket_root = workspace_root(tmp_path)
    write_delivery_record(
        ticket_root,
        {
            "delivery_id": "delivery-submitted-001",
            "task_id": "analysis-submitted-001",
            "delivery_kind": "analysis_note",
            "summary": "Submitted analysis handoff.",
            "linked_outputs": ["artifacts/ai_workspace/evidence/summary.json"],
            "review_status": "submitted",
            "evidence_summary": {"recommended_action": "review_evidence_boundary"},
        },
    )
    write_delivery_record(
        ticket_root,
        {
            "delivery_id": "delivery-returned-002",
            "task_id": "workflow-returned-002",
            "delivery_kind": "artifact_bundle",
            "summary": "Returned workflow handoff.",
            "linked_outputs": ["artifacts/workflows/demo_flow/workflow_result.json"],
            "review_status": "returned",
            "reviewed_at": "2026-07-08T10:45:00Z",
            "reviewed_by": "science-reviewer",
            "review_source": "cli",
            "return_notes": "Missing acceptance evidence.",
            "evidence_summary": {"recommended_action": "review_evidence_boundary"},
        },
    )

    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    deliveries = list_delivery_records(ticket_root)
    filtered = page_module.filter_delivery_records(
        deliveries,
        review_status="returned",
        delivery_kind="artifact_bundle",
    )
    summary = page_module.build_delivery_handoff_summary(deliveries, workspace_root_path=ticket_root)
    children = page_module.build_delivery_history_children(
        deliveries,
        workspace_root_path=ticket_root,
        review_status_filter="returned",
        delivery_kind_filter="artifact_bundle",
    )
    rendered = str(children)

    assert [delivery["delivery_id"] for delivery in filtered] == ["delivery-returned-002"]
    assert summary["delivery_count"] == 2
    assert summary["review_status_counts"] == {"returned": 1, "submitted": 1}
    assert summary["delivery_kind_counts"] == {"analysis_note": 1, "artifact_bundle": 1}
    assert summary["linked_output_path_count"] == 2
    assert summary["return_note_count"] == 1
    returned_handoff = next(item for item in summary["handoffs"] if item["delivery_id"] == "delivery-returned-002")
    assert returned_handoff["review_action"] == "address_return_notes"
    assert returned_handoff["reviewed_at"] == "2026-07-08T10:45:00Z"
    assert returned_handoff["reviewed_by"] == "science-reviewer"
    assert returned_handoff["review_source"] == "cli"
    assert "1 / 2" in rendered
    assert "Filter" in rendered
    assert "review=returned, kind=artifact_bundle" in rendered
    assert "Returned workflow handoff." in rendered
    assert "science-reviewer via cli" in rendered
    assert "Submitted analysis handoff." not in rendered


@pytest.mark.integration
def test_ticket_return_persists_return_notes_and_surfaces_in_lane(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    ticket_root = workspace_root(tmp_path)
    ticket_path = draft_ticket_from_form(
        task_type="analysis",
        title="Refine claim review",
        request_text="Review the H2 claim for overstatement.",
        linked_artifacts_text="artifacts/h2_local",
        plan_summary="Return this ticket until exact baseline evidence is attached.",
        expected_outputs_text="claim review",
        risk_notes_text="Attach exact baseline evidence before closing.",
        workspace_base=tmp_path,
    )
    current_record = json.loads(ticket_path.read_text(encoding="utf-8"))

    result = handle_ticket_editor_action(
        action="return",
        task_type="analysis",
        title="Refine claim review",
        request_text="Review the H2 claim for overstatement.",
        linked_artifacts_text="artifacts/h2_local",
        plan_summary="Return this ticket until exact baseline evidence is attached.",
        expected_outputs_text="claim review",
        risk_notes_text="Attach exact baseline evidence before closing.",
        current_ticket_path=str(ticket_path),
        current_ticket_record=current_record,
        workspace_base=tmp_path,
    )
    returned = list_ticket_records(ticket_root, lane=AI_WORKSPACE_TICKET_LANE_RETURNED)[0]

    assert result["current_ticket_record"]["status"] == AI_WORKSPACE_TICKET_STATUS_RETURNED
    assert returned["return_notes"] == "Attach exact baseline evidence before closing."

    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    returned_lane = _find_component(page, "qcchem-ai-task-returned")
    assert returned_lane is not None
    rendered = str(returned_lane)
    assert "Return handoff" in rendered
    assert "Attach exact baseline evidence before closing." in rendered


@pytest.mark.integration
def test_ai_workspace_returned_ticket_links_delivery_return_notes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    ticket_root = workspace_root(tmp_path)
    write_ticket_record(
        ticket_root,
        {
            "task_id": "analysis-returned-003",
            "task_type": "analysis",
            "title": "Returned evidence review",
            "request_text": "Revise the evidence boundary.",
            "status": AI_WORKSPACE_TICKET_STATUS_RETURNED,
        },
    )
    write_delivery_record(
        ticket_root,
        {
            "delivery_id": "delivery-returned-003",
            "task_id": "analysis-returned-003",
            "delivery_kind": "analysis_note",
            "summary": "Returned evidence handoff.",
            "linked_outputs": ["artifacts/ai_workspace/reviews/evidence_review.md"],
            "review_status": "returned",
            "return_notes": "Clarify the exploratory boundary before retrying.",
            "evidence_summary": {"recommended_action": "review_evidence_boundary"},
        },
    )

    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    returned_lane = _find_component(page, "qcchem-ai-task-returned")

    assert returned_lane is not None
    rendered = str(returned_lane)
    assert "delivery-returned-003 - Returned evidence handoff." in rendered
    assert "address return notes (address_return_notes)" in rendered
    assert "Clarify the exploratory boundary before retrying." in rendered


@pytest.mark.integration
def test_ai_workspace_delivery_persists_under_ticket_workspace_when_run_from_elsewhere(
    tmp_path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    ticket_root = workspace_root(workspace)
    write_ticket_record(
        ticket_root,
        {
            "task_id": "delivery-002",
            "task_type": "delivery",
            "title": "Submit artifact bundle",
            "request_text": "Submit the prepared artifact bundle",
            "plan_summary": "Record a delivery from a different current working directory.",
            "expected_outputs": ["delivery record"],
            "risk_notes": [],
            "linked_artifacts": ["artifacts/suite_a"],
            "status": AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
            "execution_target": "analysis_only_assistant",
        },
    )
    ticket_path = ticket_root / "tickets" / "delivery-002.json"

    monkeypatch.chdir(outside_dir)
    result = run_ticket(ticket_path)

    delivery_record_path = Path(result["delivery_record"])
    assert delivery_record_path.parent == workspace_root(workspace) / "deliveries"

    monkeypatch.chdir(workspace)
    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    submitted_lane = _find_component(page, "qcchem-ai-task-submitted")

    assert submitted_lane is not None
    assert "delivery-002" in str(submitted_lane)
    assert "Submit artifact bundle" in str(submitted_lane)


@pytest.mark.integration
def test_ticket_editor_action_requires_double_confirm_for_high_risk_execution(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    suite_dir = workspace / "artifacts" / "benchmark_suite_v1"
    suite_dir.mkdir(parents=True, exist_ok=True)
    (suite_dir / "hardware_calibration_summary.json").write_text(
        """
{
  "suite_name": "benchmark_suite_v1",
  "artifact_root": "",
  "summary": {
    "total_cases": 1,
    "runtime_evidence_status_counts": {"retrieved_result": 1}
  },
  "cases": [
    {
      "name": "case_a",
      "achieved_error": 0.012,
      "meets_chemical_accuracy": false
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    ticket_path = draft_ticket_from_form(
        task_type="execution",
        title="Run hardware benchmark",
        request_text="Run the benchmark through IBM runtime and collect the hardware result.",
        linked_artifacts_text="artifacts/benchmark_suite_v1",
        plan_summary="Benchmark the runtime-facing path and bundle the outputs.",
        expected_outputs_text="execution summary\nartifact bundle",
        risk_notes_text="Respect validated boundaries",
        workspace_base=workspace,
    )
    accepted_record = accept_ticket(ticket_path)

    guarded = handle_ticket_editor_action(
        action="run",
        task_type="execution",
        title="Run hardware benchmark",
        request_text="Run the benchmark through IBM runtime and collect the hardware result.",
        linked_artifacts_text="artifacts/benchmark_suite_v1",
        plan_summary="Benchmark the runtime-facing path and bundle the outputs.",
        expected_outputs_text="execution summary\nartifact bundle",
        risk_notes_text="Respect validated boundaries",
        current_ticket_path=str(ticket_path),
        current_ticket_record=accepted_record,
        workspace_base=workspace,
    )

    assert guarded["guard_state"]["visible"] is True
    assert guarded["did_change_workspace"] is False
    assert list_ticket_records(workspace_root(workspace), lane=AI_WORKSPACE_TICKET_LANE_INBOX)[0]["task_id"] == accepted_record["task_id"]

    guarded_again = handle_ticket_editor_action(
        action="run",
        task_type="execution",
        title="Run hardware benchmark",
        request_text="Run the benchmark through IBM runtime and collect the hardware result.",
        linked_artifacts_text="artifacts/benchmark_suite_v1",
        plan_summary="Benchmark the runtime-facing path and bundle the outputs.",
        expected_outputs_text="execution summary\nartifact bundle",
        risk_notes_text="Respect validated boundaries",
        current_ticket_path=str(ticket_path),
        current_ticket_record=accepted_record,
        guard_state=guarded["guard_state"],
        workspace_base=workspace,
    )

    assert guarded_again["guard_state"]["visible"] is True
    assert guarded_again["did_change_workspace"] is False

    confirmed = handle_ticket_editor_action(
        action="confirm_run",
        task_type="execution",
        title="Run hardware benchmark",
        request_text="Run the benchmark through IBM runtime and collect the hardware result.",
        linked_artifacts_text="artifacts/benchmark_suite_v1",
        plan_summary="Benchmark the runtime-facing path and bundle the outputs.",
        expected_outputs_text="execution summary\nartifact bundle",
        risk_notes_text="Respect validated boundaries",
        current_ticket_path=str(ticket_path),
        current_ticket_record=accepted_record,
        guard_state=guarded["guard_state"],
        workspace_base=workspace,
    )

    assert confirmed["current_ticket_record"]["status"] == AI_WORKSPACE_TICKET_STATUS_COMPLETED
    assert confirmed["guard_state"]["visible"] is False
    assert confirmed["did_change_workspace"] is True
