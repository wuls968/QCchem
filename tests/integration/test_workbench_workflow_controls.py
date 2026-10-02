"""Real engine preflight and owned background dispatch through Workbench."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from flask import Flask

from qcchem.core import WorkflowStepResult
from qcchem.io.workflow_config import load_workflow_spec
from qcchem.reporting import write_result_json
from qcchem.workbench.app import create_app
from qcchem.workbench.components.workflow_controls import PREFIX
from qcchem.workbench.workflow_controls import WorkbenchWorkflowController, require_local_control_request, worker_main
from qcchem.workflow.custom_workflow import preview_workflow_resume_from_config
from qcchem.workflow.workflow_control import WorkflowCancelledError, WorkflowControl, WorkflowLock, file_manifest, read_checkpoint, workflow_status
from qcchem.workflow.workflow_plugins import WorkflowExecutionContext, workflow_plugin_registry


def _interrupted(tmp_path):
    artifacts = tmp_path / "evidence"
    root = artifacts / "nonstandard" / "workflow"
    linked = tmp_path / "input"
    linked.mkdir()
    (linked / "result.json").write_text(json.dumps({"verification_status": "validated"}))
    config = tmp_path / "workflow.yaml"
    config.write_text(yaml.safe_dump({"workflow": {"name": "Workbench recovery", "output_root": str(root), "steps": [
        {"id": "first", "kind": "compare_artifacts", "inputs": {"artifacts": [str(linked)]}},
        {"id": "second", "kind": "compare_artifacts", "needs": ["first"], "inputs": {"artifacts": [str(linked)]}},
    ]}}))
    spec = load_workflow_spec(config)
    plugins = workflow_plugin_registry()
    with WorkflowLock(root) as lock:
        root.mkdir(parents=True)
        control = WorkflowControl.create(root, spec, plugins)
        lock.activate(control.state)
        output = control.begin_step("first")
        output.mkdir(parents=True)
        control.record_iteration(0, 1)
        context = WorkflowExecutionContext(spec, root, output, tmp_path, {}, {})
        inputs = spec.steps[0].inputs
        control.capture_inputs(inputs, context, plugins["compare_artifacts"])
        result = WorkflowStepResult("first", "compare_artifacts", "completed", outputs=plugins["compare_artifacts"].run(inputs, context))
        control.commit_step(result, spec, plugins)
        output = control.begin_step("second")
        output.mkdir(parents=True)
        control.record_iteration(0, 2)
        control.capture_inputs(inputs, context, plugins["compare_artifacts"])
        (output / "partial.txt").write_text("Preserve this partial attempt")
    return artifacts, root, config, control


def _callback(app, prefix, values, states=(), changed=None, **kwargs):
    key = next(key for key in app.callback_map if key.startswith(prefix))
    outputs = app.callback_map[key]["output"]
    if not isinstance(outputs, list):
        outputs = [outputs]
    payload = {"output": key, "outputs": [{"id": item.component_id, "property": item.component_property} for item in outputs],
               "inputs": [{"id": id_, "property": prop, "value": value} for id_, prop, value in values],
               "state": [{"id": id_, "property": prop, "value": value} for id_, prop, value in states],
               "changedPropIds": [changed or f"{values[0][0]}.{values[0][1]}"]}
    response = app.server.test_client().post("/_dash-update-component", json=payload, **kwargs)
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()["response"]


def _act(app, value, session, retries, action, review=None, **kwargs):
    values = [(f"{PREFIX}-{name}", "n_clicks", int(name == action)) for name in ("cancel", "review", "confirm")]
    values += [(f"{PREFIX}-source", "value", value), (f"{PREFIX}-retry", "value", retries)]
    states = [(f"{PREFIX}-session", "data", {"value": value, "session_id": session}), (f"{PREFIX}-review-data", "data", review)]
    return _callback(app, f"..{PREFIX}-feedback", values, states, f"{PREFIX}-{action}.n_clicks", **kwargs)


def test_preview_is_read_only_and_requires_exact_retry_review(tmp_path):
    _, root, config, _ = _interrupted(tmp_path)
    before = file_manifest([tmp_path])
    with pytest.raises(ValueError, match="--retry-step: second"):
        preview_workflow_resume_from_config(config, output_dir=root)
    preview = preview_workflow_resume_from_config(config, output_dir=root, retry_steps=["second"])
    assert preview["reused_steps"] == ["first"]
    assert preview["pending_steps"] == [{"id": "second", "kind": "compare_artifacts"}]
    assert file_manifest([tmp_path]) == before


def test_background_resume_reuses_completed_outputs_and_preserves_partial_attempt(tmp_path):
    artifacts, root, _, _ = _interrupted(tmp_path)
    controller = WorkbenchWorkflowController(artifacts, tmp_path)
    row = controller.catalog()[0]
    first = file_manifest([root / "step_outputs" / "first"])
    preview = controller.review(row["value"], ["second"], row["status"]["session_id"])
    queued = controller.start(preview["token"])
    assert queued["status"] == "queued"
    assert Path(queued["request_path"]).is_relative_to(artifacts.parent)
    assert not Path(queued["request_path"]).is_relative_to(artifacts)
    with pytest.raises(ValueError, match="already used"):
        controller.start(preview["token"])
    controller._jobs[row["value"]]["process"].wait(timeout=30)
    receipt = controller.job_status(row["value"])
    assert receipt["status"] == "completed", receipt
    assert receipt["returncode"] == 0
    assert file_manifest([root / "step_outputs" / "first"]) == first
    assert (root / "step_outputs" / "second" / "partial.txt").read_text() == "Preserve this partial attempt"
    assert read_checkpoint(root)["session_count"] == 2
    assert workflow_status(root)["completed_steps"] == ["first", "second"]


@pytest.mark.parametrize("change", ["checkpoint", "configuration", "input"])
def test_changes_after_review_block_dispatch_without_execution(tmp_path, change):
    artifacts, root, config, control = _interrupted(tmp_path)
    controller = WorkbenchWorkflowController(artifacts, tmp_path)
    row = controller.catalog()[0]
    preview = controller.review(row["value"], ["second"], row["status"]["session_id"])
    if change == "checkpoint":
        control.state["error"] = "Changed after review"
        control.save()
    elif change == "configuration":
        config.write_text(config.read_text() + "\n# Changed after review\n")
    else:
        (tmp_path / "input" / "result.json").write_text("{}")
    with pytest.raises(ValueError, match="changed|inputs"):
        controller.start(preview["token"])
    assert not controller._jobs
    assert not controller.control_root.exists()


def test_stale_cancel_does_not_create_a_mailbox(tmp_path):
    artifacts, root, _, _ = _interrupted(tmp_path)
    controller = WorkbenchWorkflowController(artifacts, tmp_path)
    with pytest.raises(ValueError, match="session changed"):
        controller.cancel(controller.catalog()[0]["value"], "0" * 32)
    assert not (root / "workflow_control").exists()


def test_worker_rechecks_inputs_before_engine_mutation(tmp_path):
    _, root, config, _ = _interrupted(tmp_path)
    preview = preview_workflow_resume_from_config(config, output_dir=root, retry_steps=["second"])
    request = tmp_path / "request.json"
    write_result_json(preview, request)
    write_result_json({"status": "queued"}, request.with_name("receipt.json"))
    (tmp_path / "input" / "result.json").write_text("{}")
    before = file_manifest([root])
    assert worker_main(request) == 2
    receipt = json.loads(request.with_name("receipt.json").read_text())
    assert receipt["status"] == "failed" and "reviewed workflow inputs" in receipt["error"]
    assert file_manifest([root]) == before


def test_dispatch_failure_retains_a_failed_receipt(tmp_path, monkeypatch):
    artifacts, root, _, _ = _interrupted(tmp_path)
    controller = WorkbenchWorkflowController(artifacts, tmp_path)
    row = controller.catalog()[0]
    preview = controller.review(row["value"], ["second"], row["status"]["session_id"])
    before = file_manifest([root])

    def failed_launch(*args, **kwargs):
        raise OSError("Owned launch fixture failure")

    monkeypatch.setattr("qcchem.workbench.workflow_controls.subprocess.Popen", failed_launch)
    with pytest.raises(OSError, match="Owned launch"):
        controller.start(preview["token"])
    receipt = json.loads(next(controller.control_root.glob("*/receipt.json")).read_text())
    assert receipt["status"] == "failed" and "Could not launch" in receipt["error"]
    assert file_manifest([root]) == before


def test_pending_output_references_are_valid_during_review(tmp_path):
    _, root, config, control = _interrupted(tmp_path)
    payload = yaml.safe_load(config.read_text())
    step = {"id": "third", "kind": "report", "needs": ["second"],
            "inputs": {"artifact_root": "${steps.second.outputs.summary_json}"}}
    payload["workflow"]["steps"].append(step)
    config.write_text(yaml.safe_dump(payload))
    from qcchem.io.serialization import to_primitive
    from qcchem.workflow.workflow_control import workflow_fingerprint

    spec = load_workflow_spec(config)
    control.state["workflow"] = to_primitive(spec)
    control.state["workflow_sha256"] = workflow_fingerprint(spec)
    control.state["steps"] = to_primitive(spec.steps)
    # Add the newly selected builtin to this controlled initial checkpoint.
    from qcchem.workflow.workflow_control import implementation_identity

    control.state["implementation"] = implementation_identity(workflow_plugin_registry(), spec.steps)
    control.save()
    preview = preview_workflow_resume_from_config(config, output_dir=root, retry_steps=["second"])
    assert [step["id"] for step in preview["pending_steps"]] == ["second", "third"]


@pytest.mark.parametrize("base,remote,origin,allowed", [
    ("http://127.0.0.1:8050", "127.0.0.1", "http://127.0.0.1:8050", True),
    ("http://localhost:8050", "127.0.0.1", None, True),
    ("http://[::1]:8050", "::1", "http://[::1]:8050", True),
    ("http://127.0.0.1:8050", "192.0.2.3", None, False),
    ("http://outside.example:8050", "127.0.0.1", None, False),
    ("http://localhost:8050", "127.0.0.1", "http://outside.example", False),
    ("http://localhost:8050", "127.0.0.1", "null", False),
])
def test_mutating_request_boundary(base, remote, origin, allowed):
    with Flask(__name__).test_request_context(base_url=base, environ_base={"REMOTE_ADDR": remote},
                                             headers={"Origin": origin} if origin else {}):
        if allowed:
            require_local_control_request()
        else:
            with pytest.raises(ValueError):
                require_local_control_request()


def test_dash_cancel_review_and_confirm_use_configured_root(tmp_path, monkeypatch):
    artifacts, root, _, control = _interrupted(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QCCHEM_WORKBENCH_ARTIFACT_ROOT", str(artifacts))
    app = create_app()
    controller = app.workflow_controller
    row = controller.catalog()[0]
    value, session = row["value"], row["status"]["session_id"]
    with WorkflowLock(root) as lock:
        lock.activate(control.state)
        response = _act(app, value, session, [], "cancel")
        assert "Cancellation requested" in response[f"{PREFIX}-feedback"]["children"]
        with pytest.raises(WorkflowCancelledError):
            control.check_cancel()
    response = _act(app, value, session, [], "review")
    assert "--retry-step: second" in response[f"{PREFIX}-feedback"]["children"]
    response = _act(app, value, session, ["second"], "review")
    review = response[f"{PREFIX}-review-data"]["data"]
    assert "compare_artifacts" in str(response[f"{PREFIX}-review-plan"])
    assert response[f"{PREFIX}-confirm"]["hidden"] is False
    response = _act(app, value, session, ["second"], "confirm", review)
    assert "Recovery queued" in response[f"{PREFIX}-feedback"]["children"]
    controller._jobs[value]["process"].wait(timeout=30)
    assert controller.job_status(value)["status"] == "completed"


def test_remote_dash_request_cannot_dispatch(tmp_path, monkeypatch):
    artifacts, _, _, _ = _interrupted(tmp_path)
    monkeypatch.setenv("QCCHEM_WORKBENCH_ARTIFACT_ROOT", str(artifacts))
    app = create_app()
    row = app.workflow_controller.catalog()[0]
    response = _act(app, row["value"], row["status"]["session_id"], ["second"], "review",
                    environ_overrides={"REMOTE_ADDR": "192.0.2.1"})
    assert "local browser" in response[f"{PREFIX}-feedback"]["children"]
    assert not app.workflow_controller._reviews
