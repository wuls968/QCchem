from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from qcchem.core import WorkflowPluginDescription
from qcchem.io.workflow_config import load_workflow_spec
from qcchem.workflow.custom_workflow import run_custom_workflow
from qcchem.workflow.workflow_plugins import WorkflowExecutionContext, WorkflowStepPlugin, installed_workflow_plugins


class EchoStep(WorkflowStepPlugin):
    def describe(self) -> WorkflowPluginDescription:
        return WorkflowPluginDescription(
            name="Echo",
            kind="echo",
            summary="Echo values for tests.",
            output_schema={"keys": ["value", "continue"]},
        )

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        target = int(inputs.get("target_iterations", 1))
        iteration = context.loop_iteration + 1
        return {
            "value": inputs.get("value", "ok"),
            "iteration": iteration,
            "continue": iteration < target,
        }


class PlannerStep(EchoStep):
    def describe(self) -> WorkflowPluginDescription:
        return WorkflowPluginDescription(name="Planner", kind="planner", summary="Generate a follow-up step.")

    def plan_next(self, result, context: WorkflowExecutionContext) -> list[dict[str, Any]]:
        return [
            {
                "id": "generated_echo",
                "kind": "echo",
                "inputs": {"value": "generated"},
            }
        ]


class FailingStep(EchoStep):
    def describe(self) -> WorkflowPluginDescription:
        return WorkflowPluginDescription(name="Failing", kind="failing", summary="Always fail.")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        raise RuntimeError("boom")


class BadPlannerStep(EchoStep):
    def describe(self) -> WorkflowPluginDescription:
        return WorkflowPluginDescription(name="Bad Planner", kind="bad_planner", summary="Generate an invalid step.")

    def plan_next(self, result, context: WorkflowExecutionContext) -> list[dict[str, Any]]:
        return [
            {
                "id": "bad_generated",
                "kind": "missing_plugin",
            }
        ]


def _patch_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = {
        "echo": EchoStep(),
        "planner": PlannerStep(),
        "failing": FailingStep(),
        "bad_planner": BadPlannerStep(),
    }
    monkeypatch.setattr("qcchem.workflow.custom_workflow.workflow_plugin_registry", lambda: registry)


def test_workflow_loop_uses_while_output_and_iteration_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_registry(monkeypatch)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: loop_demo
  output_root: out
  limits:
    max_steps: 8
    max_iterations: 5
  steps:
    - id: echo_loop
      kind: echo
      loop:
        while_output: continue
      inputs:
        target_iterations: 3
""",
        encoding="utf-8",
    )

    result = run_custom_workflow(load_workflow_spec(workflow))

    assert result.status == "completed"
    step = result.steps[0]
    assert step.iteration_count == 3
    assert step.outputs["iteration"] == 3
    assert len(step.outputs["iteration_outputs"]) == 3


def test_workflow_plugin_can_generate_validated_followup_steps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_registry(monkeypatch)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: generated_demo
  output_root: out
  steps:
    - id: planner
      kind: planner
""",
        encoding="utf-8",
    )

    result = run_custom_workflow(load_workflow_spec(workflow))

    assert result.status == "completed"
    assert [step.step_id for step in result.steps] == ["planner", "generated_echo"]
    assert result.steps[1].generated_by == "planner"
    assert result.steps[1].outputs["value"] == "generated"


def test_workflow_dynamic_steps_do_not_mutate_loaded_spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_registry(monkeypatch)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: generated_demo
  output_root: out
  steps:
    - id: planner
      kind: planner
""",
        encoding="utf-8",
    )
    spec = load_workflow_spec(workflow)

    first = run_custom_workflow(spec)
    second = run_custom_workflow(spec, output_dir=tmp_path / "out_second")

    assert [step.id for step in spec.steps] == ["planner"]
    assert [step.step_id for step in first.steps] == ["planner", "generated_echo"]
    assert [step.step_id for step in second.steps] == ["planner", "generated_echo"]
    assert first.status == "completed"
    assert second.status == "completed"


def test_workflow_rejects_existing_output_without_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_registry(monkeypatch)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: overwrite_guard
  output_root: out
  steps:
    - id: echo
      kind: echo
""",
        encoding="utf-8",
    )
    spec = load_workflow_spec(workflow)

    first = run_custom_workflow(spec)
    sentinel = Path(first.artifact_root) / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists and is not empty"):
        run_custom_workflow(spec)

    assert sentinel.read_text(encoding="utf-8") == "keep"
    second = run_custom_workflow(spec, overwrite=True)
    assert second.status == "completed"
    assert not sentinel.exists()


def test_workflow_rejects_invalid_dynamic_step_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_registry(monkeypatch)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: invalid_dynamic
  output_root: out
  steps:
    - id: planner
      kind: bad_planner
""",
        encoding="utf-8",
    )

    result = run_custom_workflow(load_workflow_spec(workflow))

    assert result.status == "failed"
    assert result.summary["generated_steps"] == 0
    assert "Dynamic step validation failed" in result.acceptance_summary["blocking_failures"][0]["error"]


def test_workflow_optional_failure_does_not_fail_acceptance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_registry(monkeypatch)
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: optional_failure
  output_root: out
  steps:
    - id: optional
      kind: failing
      required_for_success: false
      continue_on_error: true
    - id: required
      kind: echo
      required_for_success: true
      when: true
""",
        encoding="utf-8",
    )

    result = run_custom_workflow(load_workflow_spec(workflow))

    assert result.status == "completed"
    assert result.steps[0].status == "failed"
    assert result.steps[1].status == "completed"


def test_installed_workflow_plugins_load_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    class EntryPoint:
        name = "echo"
        dist = None

        def load(self):
            return EchoStep

    monkeypatch.setattr("qcchem.workflow.workflow_plugins._entry_points_for_group", lambda group: [EntryPoint()])

    plugins = installed_workflow_plugins()

    assert "echo" in plugins
    assert plugins["echo"].describe().kind == "echo"
