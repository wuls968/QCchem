"""Recovery contracts: committed work, uncertain side effects, and preserved data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from qcchem.core import WorkflowPluginDescription
from qcchem.io.workflow_config import load_workflow_spec
from qcchem.workflow.custom_workflow import resume_custom_workflow, run_custom_workflow
from qcchem.workflow.workflow_control import (
    CHECKPOINT_FILE,
    WorkflowBusyError,
    WorkflowLock,
    read_checkpoint,
    request_workflow_cancel,
    workflow_status,
)
from qcchem.workflow.workflow_plugins import BuiltinWorkflowStep, WorkflowStepPlugin


class FileStep(WorkflowStepPlugin):
    def __init__(self):
        self.calls: list[str] = []
        self.fail = True
        self.version = "1"

    def describe(self):
        return WorkflowPluginDescription(name="File", kind="file", summary="Recovery fixture", version=self.version)

    def run(self, inputs, context):
        self.calls.append(inputs.get("label", "ok"))
        output = context.output_path("value.txt")
        output.write_text(str(inputs.get("value", "preserved")), encoding="utf-8")
        if inputs.get("fail") and self.fail:
            raise RuntimeError("transient failure with a partial output")
        return {"file": str(output), "value": inputs.get("value", "ok")}


class CancelStep(FileStep):
    def run(self, inputs, context):
        result = super().run(inputs, context)
        if self.fail:
            request_workflow_cancel(context.output_root, reason="test cancellation")
            if inputs.get("poll", True):
                context.check_control()
        return result


class InterruptStep(FileStep):
    def run(self, inputs, context):
        result = super().run(inputs, context)
        if self.fail:
            raise KeyboardInterrupt
        return result


class PlannerStep(FileStep):
    def plan_next(self, result, context):
        return [{"id": "generated", "kind": "file", "inputs": {"fail": True, "label": "generated"}}]


class MutableStep(FileStep):
    mutates_inputs = True

    def run(self, inputs, context):
        Path(inputs["source"]).write_text("updated by collection", encoding="utf-8")
        return super().run(inputs, context)


class ConfigStep(BuiltinWorkflowStep):
    kind = "config"
    summary = "Read configured source files without running chemistry"

    def run(self, inputs, context):
        context.output_path("value.txt").write_text("ok", encoding="utf-8")
        return {}


def _spec(tmp_path, steps, *, limits=None, acceptance=None):
    path = tmp_path / "workflow.yaml"
    path.write_text(yaml.safe_dump({"workflow": {
        "name": "recovery", "output_root": str(tmp_path / "out"), "steps": steps,
        "limits": limits or {}, "acceptance": acceptance or {},
    }}), encoding="utf-8")
    return load_workflow_spec(path)


def _registry(monkeypatch, plugin, **others):
    monkeypatch.setattr("qcchem.workflow.custom_workflow.workflow_plugin_registry", lambda: {"file": plugin, **others})


def test_resume_reuses_committed_work_and_preserves_partial_attempts(tmp_path, monkeypatch):
    plugin = FileStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [
        {"id": "first", "kind": "file", "inputs": {"label": "first"}},
        {"id": "second", "kind": "file", "needs": ["first"], "inputs": {"label": "second", "fail": True}},
    ])
    first = run_custom_workflow(spec)
    root = first.artifact_root
    partial = root / "step_outputs" / "second" / "value.txt"
    original = partial.read_bytes()
    checkpoint = (root / CHECKPOINT_FILE).read_bytes()
    with pytest.raises(ValueError, match="--retry-step: second"):
        resume_custom_workflow(spec)
    assert (root / CHECKPOINT_FILE).read_bytes() == checkpoint
    plugin.fail = False
    resumed = resume_custom_workflow(spec, retry_steps=["second"])
    assert resumed.status == "completed"
    assert plugin.calls == ["first", "second", "second"]
    assert resumed.summary["reused_steps"] == ["first"]
    assert resumed.summary["executed_step_count"] == 3
    assert partial.read_bytes() == original
    assert "resume-" in resumed.steps[1].outputs["file"]
    archived = list((root / "execution_history").glob(f"*/{CHECKPOINT_FILE}"))
    assert len(archived) == 1
    assert archived[0].read_bytes() == checkpoint
    completed_checkpoint = (root / CHECKPOINT_FILE).read_bytes()
    repeated = resume_custom_workflow(spec)
    assert repeated.summary["session_id"] == resumed.summary["session_id"]
    assert (root / CHECKPOINT_FILE).read_bytes() == completed_checkpoint
    assert len(plugin.calls) == 3


def test_retry_invalidates_dependency_skips_but_reuses_independent_steps(tmp_path, monkeypatch):
    plugin = FileStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [
        {"id": "upstream", "kind": "file", "continue_on_error": True, "inputs": {"fail": True, "label": "upstream"}},
        {"id": "dependent", "kind": "file", "needs": ["upstream"], "inputs": {"label": "dependent"}},
        {"id": "independent", "kind": "file", "inputs": {"label": "independent"}},
    ])
    first = run_custom_workflow(spec)
    assert [step.status for step in first.steps] == ["failed", "skipped", "completed"]
    assert (first.artifact_root / "step_outputs" / "dependent" / "step_result.json").exists()
    plugin.fail = False
    resumed = resume_custom_workflow(spec, retry_steps=["upstream"])
    assert resumed.status == "completed"
    assert plugin.calls == ["upstream", "independent", "upstream", "dependent"]


@pytest.mark.parametrize("change", ["modify", "missing", "extra"])
def test_resume_rejects_changed_completed_artifacts_before_mutating_state(tmp_path, monkeypatch, change):
    plugin = FileStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    result = run_custom_workflow(spec)
    output = result.artifact_root / "step_outputs" / "done" / "value.txt"
    if change == "modify":
        output.write_text("tampered", encoding="utf-8")
    elif change == "missing":
        output.rename(output.with_name("moved.txt"))
    else:
        output.with_name("extra.txt").write_text("extra", encoding="utf-8")
    checkpoint = (result.artifact_root / CHECKPOINT_FILE).read_bytes()
    with pytest.raises(ValueError, match="Cannot reuse step 'done' outputs"):
        resume_custom_workflow(spec)
    assert (result.artifact_root / CHECKPOINT_FILE).read_bytes() == checkpoint
    assert plugin.calls == ["ok"]
    assert not (result.artifact_root / "execution_history").exists()


def test_resume_rejects_modified_input_and_normalized_config(tmp_path, monkeypatch):
    plugin = FileStep()
    _registry(monkeypatch, plugin)
    source = tmp_path / "source.txt"
    source.write_text("original", encoding="utf-8")
    spec = _spec(tmp_path, [{"id": "done", "kind": "file", "inputs": {"source": str(source)}}])
    result = run_custom_workflow(spec)
    source.write_text("modified", encoding="utf-8")
    with pytest.raises(ValueError, match="inputs.*changed"):
        resume_custom_workflow(spec)
    spec.parameters["new_parameter"] = 1
    with pytest.raises(ValueError, match="configuration/source path differs"):
        resume_custom_workflow(spec)
    assert read_checkpoint(result.artifact_root)["session_count"] == 1


def test_builtin_config_hook_tracks_nested_data_files(tmp_path, monkeypatch):
    data = tmp_path / "charges.xyzq"
    data.write_text("H 0 0 2 0.1\n", encoding="utf-8")
    config = tmp_path / "run.yaml"
    config.write_text("problem:\n  external_point_charges:\n    source_file: charges.xyzq\n", encoding="utf-8")
    _registry(monkeypatch, FileStep(), config=ConfigStep())
    spec = _spec(tmp_path, [{"id": "data", "kind": "config", "inputs": {"config": str(config)}}])
    run_custom_workflow(spec)
    data.write_text("H 0 0 3 0.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="inputs.*changed"):
        resume_custom_workflow(spec)


def test_resume_rejects_plugin_and_dependency_version_changes(tmp_path, monkeypatch):
    plugin = FileStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    run_custom_workflow(spec)
    plugin.version = "2"
    with pytest.raises(ValueError, match="plugin identity, or environment changed"):
        resume_custom_workflow(spec)
    plugin.version = "1"
    from qcchem.workflow import workflow_control

    version = workflow_control.metadata.version
    monkeypatch.setattr(workflow_control.metadata, "version", lambda name: "999.0" if name == "numpy" else version(name))
    with pytest.raises(ValueError, match="environment changed"):
        resume_custom_workflow(spec)


@pytest.mark.parametrize("poll", [True, False])
def test_cancellation_never_retries_or_accepts_and_old_request_does_not_cancel_resume(tmp_path, monkeypatch, poll):
    plugin = CancelStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [
        {"id": "cancel", "kind": "file", "retry": 3, "required_for_success": False, "inputs": {"poll": poll}},
        {"id": "later", "kind": "file"},
    ], acceptance={"fail_on_required_failure": False})
    result = run_custom_workflow(spec)
    assert result.status == "cancelled"
    assert result.acceptance_summary["accepted"] is False
    assert len(plugin.calls) == 1
    status = workflow_status(result.artifact_root)
    assert status["status"] == "cancelled"
    assert status["worker_active"] is False
    assert request_workflow_cancel(result.artifact_root)["action"] == "already_stopped"
    with pytest.raises(ValueError, match="--retry-step: cancel"):
        resume_custom_workflow(spec)
    plugin.fail = False
    resumed = resume_custom_workflow(spec, retry_steps=["cancel"])
    assert resumed.status == "completed"
    assert resumed.summary["session_id"] != result.summary["session_id"]
    assert workflow_status(result.artifact_root)["cancel_requested"] is False
    assert len(list((result.artifact_root / "workflow_control").glob("cancel-*.json"))) == 1


def test_keyboard_interrupt_is_unaccepted_and_needs_explicit_retry(tmp_path, monkeypatch):
    plugin = InterruptStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [{"id": "interrupt", "kind": "file"}])
    result = run_custom_workflow(spec)
    assert result.status == "interrupted"
    assert result.acceptance_summary["accepted"] is False
    with pytest.raises(ValueError, match="--retry-step: interrupt"):
        resume_custom_workflow(spec)
    plugin.fail = False
    assert resume_custom_workflow(spec, retry_steps=["interrupt"]).status == "completed"


def test_dynamic_graph_commits_with_planner_and_is_not_generated_twice(tmp_path, monkeypatch):
    plugin = FileStep()
    planner = PlannerStep()
    _registry(monkeypatch, plugin, planner=planner)
    spec = _spec(tmp_path, [{"id": "planner", "kind": "planner"}])
    first = run_custom_workflow(spec)
    assert first.status == "failed"
    plugin.fail = False
    resumed = resume_custom_workflow(spec, retry_steps=["generated"])
    assert resumed.status == "completed"
    assert len(planner.calls) == 1
    assert [step.id for step in spec.steps] == ["planner"]
    assert [step.step_id for step in resumed.steps] == ["planner", "generated"]


def test_failed_planner_regenerates_only_unfinished_generated_subgraph(tmp_path, monkeypatch):
    plugin = FileStep()
    planner = PlannerStep()
    _registry(monkeypatch, plugin, planner=planner)
    spec = _spec(tmp_path, [{"id": "planner", "kind": "planner", "inputs": {"fail": True}}])
    assert run_custom_workflow(spec).status == "failed"
    planner.fail = False
    plugin.fail = False
    resumed = resume_custom_workflow(spec, retry_steps=["planner"])
    assert resumed.status == "completed"
    assert len([step for step in resumed.steps if step.step_id == "generated"]) == 1
    assert resume_custom_workflow(spec).status == "completed"


def test_mutable_input_collection_reuses_post_operation_state(tmp_path, monkeypatch):
    source = tmp_path / "sidecar.json"
    source.write_text("original", encoding="utf-8")
    plugin = MutableStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [{"id": "collect", "kind": "file", "inputs": {"source": str(source)}}])
    result = run_custom_workflow(spec)
    assert resume_custom_workflow(spec).status == "completed"
    manifest = read_checkpoint(result.artifact_root)["manifests"]["collect"]
    assert manifest["inputs_before"] != manifest["inputs"]
    assert len(plugin.calls) == 1


@pytest.mark.parametrize("budget", ["steps", "iterations"])
def test_global_limits_cannot_be_bypassed_by_optional_permissive_acceptance(tmp_path, monkeypatch, budget):
    class LoopStep(FileStep):
        def run(self, inputs, context):
            super().run(inputs, context)
            return {"continue": True}

    _registry(monkeypatch, LoopStep())
    limits = {"max_steps": 1, "max_iterations": 3} if budget == "steps" else {"max_steps": 5, "max_iterations": 1}
    spec = _spec(tmp_path, [{"id": "loop", "kind": "file", "required_for_success": False, "loop": True}],
                 limits=limits, acceptance={"fail_on_required_failure": False})
    result = run_custom_workflow(spec)
    assert result.status == "failed"
    assert result.acceptance_summary["accepted"] is False
    assert f"max_{budget}" in result.steps[0].error


def test_checkpoint_corruption_and_illegal_retry_are_readonly_rejections(tmp_path, monkeypatch):
    plugin = FileStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    result = run_custom_workflow(spec)
    for step_id in ("done", "unknown"):
        with pytest.raises(ValueError, match="--retry-step only accepts"):
            resume_custom_workflow(spec, retry_steps=[step_id])
    path = result.artifact_root / CHECKPOINT_FILE
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["results"]["done"]["status"] = "failed"
    path.write_text(json.dumps(payload), encoding="utf-8")
    corrupted = path.read_bytes()
    with pytest.raises(ValueError, match="integrity check failed"):
        resume_custom_workflow(spec)
    assert path.read_bytes() == corrupted


def test_execution_lock_prevents_resume_and_overwrite_without_touching_bundle(tmp_path, monkeypatch):
    _registry(monkeypatch, FileStep())
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    result = run_custom_workflow(spec)
    checkpoint = (result.artifact_root / CHECKPOINT_FILE).read_bytes()
    with WorkflowLock(result.artifact_root):
        for action in (
            lambda: resume_custom_workflow(spec),
            lambda: run_custom_workflow(spec, overwrite=True),
        ):
            with pytest.raises(WorkflowBusyError, match="already running"):
                action()
    assert (result.artifact_root / CHECKPOINT_FILE).read_bytes() == checkpoint
    assert not list(tmp_path.glob("out.backup-*"))


def test_output_written_before_checkpoint_commit_is_still_uncertain(tmp_path, monkeypatch):
    from qcchem.workflow import workflow_control

    plugin = FileStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [
        {"id": "first", "kind": "file", "inputs": {"label": "first"}},
        {"id": "second", "kind": "file", "needs": ["first"], "inputs": {"label": "second"}},
    ])
    writer = workflow_control.write_result_json
    fail_commit = {"enabled": True}

    def fail_after_result(payload, path):
        if fail_commit["enabled"] and path.name == CHECKPOINT_FILE and "second" in payload.get("results", {}):
            raise OSError("simulated interruption before checkpoint replacement")
        writer(payload, path)

    monkeypatch.setattr(workflow_control, "write_result_json", fail_after_result)
    with pytest.raises(OSError, match="simulated interruption"):
        run_custom_workflow(spec)
    root = spec.output_root
    assert (root / "step_outputs" / "second" / "step_result.json").exists()
    assert workflow_status(root)["current_step"]["step_id"] == "second"
    with pytest.raises(ValueError, match="--retry-step: second"):
        resume_custom_workflow(spec)
    fail_commit["enabled"] = False
    assert resume_custom_workflow(spec, retry_steps=["second"]).status == "completed"
    assert plugin.calls == ["first", "second", "second"]


def test_cancelled_loop_retry_retains_execution_budget_and_partial_iterations(tmp_path, monkeypatch):
    class LoopCancelStep(FileStep):
        def run(self, inputs, context):
            super().run(inputs, context)
            if context.loop_iteration == 1 and self.fail:
                request_workflow_cancel(context.output_root)
                context.check_control()
            return {"continue": context.loop_iteration < 2}

    plugin = LoopCancelStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [{"id": "loop", "kind": "file", "loop": True}], limits={"max_steps": 4})
    first = run_custom_workflow(spec)
    assert first.status == "cancelled"
    assert first.summary["executed_step_count"] == 2
    original = first.artifact_root / "step_outputs" / "loop" / "iteration_001" / "value.txt"
    before = original.read_bytes()
    plugin.fail = False
    retried = resume_custom_workflow(spec, retry_steps=["loop"])
    assert retried.status == "failed"
    assert retried.acceptance_summary["accepted"] is False
    assert "max_steps=4" in retried.steps[0].error
    assert retried.summary["executed_step_count"] == 4
    assert original.read_bytes() == before
    assert len(plugin.calls) == 4


def test_retry_cannot_accept_reused_outputs_changed_by_another_step(tmp_path, monkeypatch):
    class SharedOutputStep(FileStep):
        def run(self, inputs, context):
            outputs = super().run(inputs, context)
            if inputs.get("fail") and not self.fail:
                Path(context.step_results["first"].outputs["file"]).write_text("changed by retry", encoding="utf-8")
            return outputs

    plugin = SharedOutputStep()
    _registry(monkeypatch, plugin)
    spec = _spec(tmp_path, [
        {"id": "first", "kind": "file"},
        {"id": "retry", "kind": "file", "inputs": {"fail": True}},
    ])
    assert run_custom_workflow(spec).status == "failed"
    plugin.fail = False
    result = resume_custom_workflow(spec, retry_steps=["retry"])
    assert result.status == "failed"
    assert result.acceptance_summary["accepted"] is False
    assert "reused step 'first' outputs" in result.acceptance_summary["blocking_failures"][-1]["error"]


def test_credentials_are_rejected_before_config_or_plugin_output_is_checkpointed(tmp_path, monkeypatch):
    _registry(monkeypatch, FileStep())
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    spec.parameters["api_key"] = "fixture-only-placeholder"
    with pytest.raises(ValueError, match="cannot persist credential field 'api_key'"):
        run_custom_workflow(spec)
    assert not spec.output_root.exists()
    spec.parameters = {}

    class CredentialOutputStep(FileStep):
        def run(self, inputs, context):
            return {"access_token": "fixture-only-placeholder"}

    _registry(monkeypatch, CredentialOutputStep())
    result = run_custom_workflow(spec)
    assert result.status == "failed"
    assert "fixture-only-placeholder" not in (result.artifact_root / CHECKPOINT_FILE).read_text(encoding="utf-8")


def test_installed_plugin_distribution_version_is_bound_even_if_describe_omits_it(tmp_path, monkeypatch):
    from types import SimpleNamespace

    plugin = FileStep()
    _registry(monkeypatch, plugin)
    distribution = SimpleNamespace(metadata={"Name": "workflow-fixture"}, version="1")
    entry_point = SimpleNamespace(name="file", value=f"{FileStep.__module__}:FileStep", dist=distribution)
    monkeypatch.setattr("qcchem.workflow.workflow_plugins._entry_points_for_group", lambda _: [entry_point])
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    run_custom_workflow(spec)
    distribution.version = "2"
    with pytest.raises(ValueError, match="plugin identity, or environment changed"):
        resume_custom_workflow(spec)


def test_recovery_preparation_is_not_mistaken_for_a_running_old_session(tmp_path, monkeypatch):
    _registry(monkeypatch, FileStep())
    spec = _spec(tmp_path, [{"id": "done", "kind": "file"}])
    result = run_custom_workflow(spec)
    checkpoint = (result.artifact_root / CHECKPOINT_FILE).read_bytes()
    with WorkflowLock(result.artifact_root):
        status = workflow_status(result.artifact_root)
        assert status["status"] == "preparing"
        assert status["worker_active"] is True
        with pytest.raises(ValueError, match="no execution session is active yet"):
            request_workflow_cancel(result.artifact_root)
    assert (result.artifact_root / CHECKPOINT_FILE).read_bytes() == checkpoint
    assert workflow_status(result.artifact_root)["status"] == "completed"


def test_duck_typed_plugin_without_optional_planning_or_input_hooks_can_recover(tmp_path, monkeypatch):
    class MinimalPlugin:
        def describe(self):
            return WorkflowPluginDescription(name="Minimal", kind="minimal", summary="No optional hooks")

        def validate(self, inputs, context):
            return []

        def run(self, inputs, context):
            return {"done": True}

    _registry(monkeypatch, FileStep(), minimal=MinimalPlugin())
    spec = _spec(tmp_path, [{"id": "minimal", "kind": "minimal"}])
    assert run_custom_workflow(spec).status == "completed"
    assert resume_custom_workflow(spec).status == "completed"
