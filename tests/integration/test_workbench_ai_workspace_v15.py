from __future__ import annotations

import importlib
from collections.abc import Iterable
from pathlib import Path

import pytest

from qcchem.core.ai_workspace import (
    AI_WORKSPACE_TICKET_LANE_COMPLETED,
    AI_WORKSPACE_TICKET_LANE_INBOX,
    AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
    AI_WORKSPACE_TICKET_STATUS_COMPLETED,
    AI_WORKSPACE_TICKET_STATUS_NEEDS_CONFIRMATION,
)
from qcchem.workflow.ai_store import list_ticket_records, workspace_root, write_ticket_record
from qcchem.workflow.ai_workspace import (
    accept_ticket,
    draft_ticket_from_form,
    handle_ticket_editor_action,
    run_ticket,
)
from qcchem.workbench.app import create_app


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
    assert "qcchem-ai-current-ticket-preview" in rendered


@pytest.mark.integration
def test_workbench_shell_contains_ticket_editor_controls() -> None:
    app = create_app()
    layout = _resolve_layout(app.layout)
    rendered = str(layout)

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
    assert "qcchem-ai-provider-drawer.hidden" in app.callback_map


@pytest.mark.integration
def test_workbench_shell_registers_ticket_editor_callbacks() -> None:
    app = create_app()
    callback_outputs = "\n".join(app.callback_map.keys())

    assert "qcchem-ai-current-ticket-preview.children" in app.callback_map
    assert "qcchem-ai-current-ticket-record.data" in callback_outputs
    assert "qcchem-ai-current-ticket-path.data" in callback_outputs
    assert "qcchem-ai-task-inbox.children" in app.callback_map


@pytest.mark.integration
def test_ai_workspace_page_exposes_placeholder_task_lanes() -> None:
    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")
    page = _resolve_layout(page_module.layout)
    rendered = str(page)

    assert "AI Workspace" in rendered
    assert "qcchem-ai-task-inbox" in rendered
    assert "qcchem-ai-task-running" in rendered
    assert "qcchem-ai-task-submitted" in rendered
    assert "qcchem-ai-task-completed" in rendered
    assert "qcchem-ai-task-returned" in rendered


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
    assert list_ticket_records(root, lane=AI_WORKSPACE_TICKET_LANE_INBOX)[0]["task_id"] == "ticket-inbox-001"


@pytest.mark.integration
def test_ai_workspace_page_render_does_not_create_workspace_directories(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    page_module = importlib.import_module("qcchem.workbench.pages.ai_workspace")

    assert not (tmp_path / "artifacts" / "ai_workspace").exists()

    _resolve_layout(page_module.layout)

    assert not (tmp_path / "artifacts" / "ai_workspace").exists()


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
