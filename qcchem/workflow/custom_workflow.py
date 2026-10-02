"""Custom workflow execution engine for QCchem."""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from qcchem.core import WorkflowRunResult, WorkflowSpec, WorkflowStepResult, WorkflowStepSpec
from qcchem.io.serialization import to_primitive
from qcchem.io.workflow_config import load_workflow_spec, validate_workflow_spec, workflow_template
from qcchem.reporting import write_result_json
from qcchem.workflow.common import prepare_clean_output_root, contained_output_path
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.workflow_control import (
    WorkflowCancelledError,
    WorkflowControl,
    WorkflowLock,
    detected_paths,
    file_manifest,
    implementation_identity,
    read_checkpoint,
    validate_checkpoint_data,
    verify_manifest,
    workflow_fingerprint,
    workflow_root,
)
from qcchem.workflow.workflow_plugins import (
    WorkflowExecutionContext,
    WorkflowStepPlugin,
    describe_workflow_plugins,
    workflow_plugin_registry,
)

SCHEMA_VERSION = "qcchem.workflow_run.v0.1-alpha"


class WorkflowLimitError(RuntimeError):
    """A workflow budget was exhausted, independent of step acceptance policy."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_deadline(deadline: float | None) -> None:
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("Workflow exceeded max_wall_time_seconds; cooperative deadline reached.")


def _check_control(deadline: float | None, control: WorkflowControl | None) -> None:
    _check_deadline(deadline)
    if control is not None:
        control.check_cancel()


def _interruption_status(exc: BaseException) -> str:
    if isinstance(exc, WorkflowCancelledError):
        return "cancelled"
    return "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"


def _plugin_key(step: WorkflowStepSpec) -> str:
    return step.plugin or step.kind


def _append_provenance(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(to_primitive(event), sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _nested_get(value: Any, parts: list[str]) -> Any:
    current = value
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise KeyError(".".join(parts))
    return current


def _resolve_reference(expr: str, *, spec: WorkflowSpec, results: dict[str, WorkflowStepResult], output_root: Path) -> Any:
    parts = expr.split(".")
    if parts[:1] == ["workflow"]:
        if parts[1:] == ["output_root"]:
            return str(output_root)
        if parts[1:] == ["name"]:
            return spec.name
    if parts[:1] == ["parameters"]:
        return _nested_get(spec.parameters, parts[1:])
    if len(parts) >= 4 and parts[0] == "steps" and parts[2] == "outputs":
        step_id = parts[1]
        if step_id not in results:
            raise KeyError(expr)
        return _nested_get(results[step_id].outputs, parts[3:])
    raise KeyError(expr)


def _resolve_value(value: Any, *, spec: WorkflowSpec, results: dict[str, WorkflowStepResult], output_root: Path) -> Any:
    from qcchem.io.workflow_config import REFERENCE_PATTERN

    if isinstance(value, str):
        matches = list(REFERENCE_PATTERN.finditer(value))
        if not matches:
            return value
        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            return _resolve_reference(matches[0].group(1).strip(), spec=spec, results=results, output_root=output_root)
        resolved = value
        for match in matches:
            replacement = _resolve_reference(match.group(1).strip(), spec=spec, results=results, output_root=output_root)
            resolved = resolved.replace(match.group(0), str(replacement))
        return resolved
    if isinstance(value, list):
        return [_resolve_value(item, spec=spec, results=results, output_root=output_root) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_value(item, spec=spec, results=results, output_root=output_root) for key, item in value.items()}
    return value


def _truthy_condition(value: Any, *, spec: WorkflowSpec, results: dict[str, WorkflowStepResult], output_root: Path) -> bool:
    try:
        resolved = _resolve_value(value, spec=spec, results=results, output_root=output_root)
    except KeyError:
        return False
    if isinstance(resolved, str):
        return resolved.strip().lower() not in {"", "0", "false", "no", "none", "null"}
    return bool(resolved)


def _normalize_retry_attempts(step: WorkflowStepSpec) -> int:
    return max(int(step.retry.max_retries), 0) + 1


def _build_graph(spec: WorkflowSpec, results: dict[str, WorkflowStepResult]) -> dict[str, Any]:
    nodes = []
    edges = []
    for step in spec.steps:
        result = results.get(step.id)
        nodes.append(
            {
                "id": step.id,
                "kind": step.kind,
                "plugin": step.plugin,
                "status": None if result is None else result.status,
                "generated_by": step.generated_by,
                "required_for_success": step.required_for_success,
                "loop": bool(step.loop),
            }
        )
        for need in step.needs:
            edges.append({"source": need, "target": step.id})
    return {"nodes": nodes, "edges": edges}


def _render_workflow_report(payload: dict[str, Any]) -> str:
    lines = [
        f"# Workflow Report: {payload.get('workflow_name')}",
        "",
        f"- status: `{payload.get('status')}`",
        f"- artifact_root: `{payload.get('artifact_root')}`",
        f"- source_path: `{payload.get('source_path')}`",
        f"- total_steps: `{(payload.get('summary') or {}).get('total_steps')}`",
        f"- completed_steps: `{(payload.get('summary') or {}).get('completed_steps')}`",
        f"- failed_steps: `{(payload.get('summary') or {}).get('failed_steps')}`",
        f"- skipped_steps: `{(payload.get('summary') or {}).get('skipped_steps')}`",
        f"- generated_steps: `{(payload.get('summary') or {}).get('generated_steps')}`",
        "",
        "## Acceptance",
        "",
    ]
    acceptance = payload.get("acceptance_summary") or {}
    lines.extend(
        [
            f"- accepted: `{acceptance.get('accepted')}`",
            f"- recommended_action: `{acceptance.get('recommended_action')}`",
            f"- blocking_failures: `{acceptance.get('blocking_failures', [])}`",
            "",
            "## Steps",
            "",
        ]
    )
    for step in payload.get("steps") or []:
        lines.append(
            "- `{step_id}` kind=`{kind}` status=`{status}` attempts=`{attempts}` iterations=`{iterations}`".format(
                step_id=step.get("step_id"),
                kind=step.get("kind"),
                status=step.get("status"),
                attempts=step.get("attempts"),
                iterations=step.get("iteration_count"),
            )
        )
        if step.get("error"):
            lines.append(f"  error=`{step.get('error')}`")
        output_keys = sorted((step.get("outputs") or {}).keys())
        if output_keys:
            lines.append(f"  outputs=`{output_keys}`")
    lines.append("")
    return "\n".join(lines)


def render_workflow_report(result: WorkflowRunResult | dict[str, Any]) -> str:
    """Render a workflow result as Markdown."""
    return _render_workflow_report(to_primitive(result))


def _validate_step_plugin(step: WorkflowStepSpec, registry: dict[str, WorkflowStepPlugin]) -> WorkflowStepPlugin:
    key = _plugin_key(step)
    if key not in registry:
        available = ", ".join(sorted(registry)) or "none"
        raise ValueError(
            f"Unsupported workflow step plugin/kind '{key}' for step '{step.id}'. "
            f"Available plugins: {available}. "
            "Run 'qcchem workflow plugins' to inspect installed plugin metadata."
        )
    return registry[key]


def validate_workflow_plugins(spec: WorkflowSpec, registry: dict[str, WorkflowStepPlugin] | None = None) -> list[dict[str, Any]]:
    """Validate that all step plugins exist and return plugin metadata."""
    selected_registry = registry if registry is not None else workflow_plugin_registry()
    validate_workflow_spec(spec)
    descriptions: list[dict[str, Any]] = []
    for step in spec.steps:
        plugin = _validate_step_plugin(step, selected_registry)
        descriptions.append(to_primitive(plugin.describe()))
    return descriptions


def validate_workflow_from_config(path: Path, *, include_installed: bool = True) -> dict[str, Any]:
    """Load and validate a workflow config for CLI use."""
    spec = load_workflow_spec(path)
    plugins = validate_workflow_plugins(spec, workflow_plugin_registry(include_installed=include_installed))
    return {
        "schema_version": "qcchem.workflow_validation.v0.1-alpha",
        "workflow_name": spec.name,
        "source_path": str(spec.source_path),
        "steps": [step.id for step in spec.steps],
        "plugin_count": len(plugins),
        "plugins": plugins,
        "status": "valid",
    }


def _step_context(
    *,
    spec: WorkflowSpec,
    output_root: Path,
    step_output_dir: Path,
    results: dict[str, WorkflowStepResult],
    loop_iteration: int,
    deadline: float | None = None,
    control: WorkflowControl | None = None,
) -> WorkflowExecutionContext:
    base_dir = spec.source_path.parent if spec.source_path is not None else Path.cwd()
    return WorkflowExecutionContext(
        workflow=spec,
        output_root=output_root,
        step_output_dir=step_output_dir,
        base_dir=base_dir,
        parameters=spec.parameters,
        step_results=results,
        loop_iteration=loop_iteration,
        metadata={
            "deadline_monotonic": deadline,
            "control_check": lambda: _check_control(deadline, control),
            "computation_recovery": control.state.get("computation_recovery", {}) if control is not None else {},
        },
    )


def _run_once(
    *,
    step: WorkflowStepSpec,
    spec: WorkflowSpec,
    plugin: WorkflowStepPlugin,
    output_root: Path,
    results: dict[str, WorkflowStepResult],
    loop_iteration: int,
    provenance_path: Path,
    deadline: float | None = None,
    control: WorkflowControl | None = None,
    step_output_root: Path | None = None,
) -> WorkflowStepResult:
    _check_control(deadline, control)
    step_output_dir = step_output_root or contained_output_path(output_root, Path("step_outputs") / step.id)
    if loop_iteration:
        step_output_dir = contained_output_path(step_output_dir, f"iteration_{loop_iteration:03d}")
    step_output_dir.mkdir(parents=True, exist_ok=True)
    started_at = _now()
    _append_provenance(
        provenance_path,
        {
            "timestamp": started_at,
            "event_type": "step_started",
            "step_id": step.id,
            "kind": step.kind,
            "loop_iteration": loop_iteration,
        },
    )
    context = _step_context(
        spec=spec,
        output_root=output_root,
        step_output_dir=step_output_dir,
        results=results,
        loop_iteration=loop_iteration,
        deadline=deadline,
        control=control,
    )
    recovery = context.metadata["computation_recovery"].get(step.id)
    if recovery and loop_iteration == 0 and recovery.get("iteration", 0) == 0 and not step.loop:
        context.metadata["computation_resume_dir"] = recovery["output_dir"]
    resolved_inputs = _resolve_value(step.inputs, spec=spec, results=results, output_root=output_root)
    if control is not None:
        control.capture_inputs(resolved_inputs, context, plugin)
    attempts = _normalize_retry_attempts(step)
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            _check_control(deadline, control)
            if control is not None:
                control.record_attempt(attempt)
            warnings = plugin.validate(dict(resolved_inputs), context)
            _check_control(deadline, control)
            outputs = plugin.run(dict(resolved_inputs), context)
            _check_control(deadline, control)
            if warnings:
                outputs = {**outputs, "validation_warnings": warnings}
            validate_checkpoint_data(outputs)
            completed_at = _now()
            result = WorkflowStepResult(
                step_id=step.id,
                kind=step.kind,
                plugin=_plugin_key(step),
                status="completed",
                attempts=attempt,
                outputs=to_primitive(outputs),
                started_at=started_at,
                completed_at=completed_at,
                generated_by=step.generated_by,
                required_for_success=step.required_for_success,
            )
            _append_provenance(
                provenance_path,
                {
                    "timestamp": completed_at,
                    "event_type": "step_completed",
                    "step_id": step.id,
                    "attempt": attempt,
                    "loop_iteration": loop_iteration,
                    "outputs": sorted(result.outputs.keys()),
                },
            )
            return result
        except (TimeoutError, WorkflowCancelledError):
            raise
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            _append_provenance(
                provenance_path,
                {
                    "timestamp": _now(),
                    "event_type": "step_attempt_failed",
                    "step_id": step.id,
                    "attempt": attempt,
                    "loop_iteration": loop_iteration,
                    "error": last_error,
                },
            )
    return WorkflowStepResult(
        step_id=step.id,
        kind=step.kind,
        plugin=_plugin_key(step),
        status="failed",
        attempts=attempts,
        outputs={},
        error=last_error,
        started_at=started_at,
        completed_at=_now(),
        generated_by=step.generated_by,
        required_for_success=step.required_for_success,
    )


def _normalize_generated_steps(items: list[dict[str, Any]], *, generated_by: str) -> list[WorkflowStepSpec]:
    validate_checkpoint_data(items)
    normalized: list[WorkflowStepSpec] = []
    from qcchem.io.workflow_config import _parse_step  # reuse the public YAML grammar internally

    for item in items:
        payload = dict(item)
        payload.setdefault("needs", [generated_by])
        payload.setdefault("generated_by", generated_by)
        normalized.append(_parse_step(payload))
    return normalized


def _execute_step(
    *,
    step: WorkflowStepSpec,
    spec: WorkflowSpec,
    registry: dict[str, WorkflowStepPlugin],
    output_root: Path,
    results: dict[str, WorkflowStepResult],
    provenance_path: Path,
    executed_budget: dict[str, int],
    deadline: float | None = None,
    control: WorkflowControl | None = None,
    step_output_root: Path | None = None,
) -> tuple[WorkflowStepResult, list[WorkflowStepSpec]]:
    plugin = _validate_step_plugin(step, registry)
    if not _truthy_condition(step.when, spec=spec, results=results, output_root=output_root):
        return (
            WorkflowStepResult(
                step_id=step.id,
                kind=step.kind,
                plugin=_plugin_key(step),
                status="skipped",
                outputs={"skip_reason": "when_condition_false"},
                started_at=_now(),
                completed_at=_now(),
                generated_by=step.generated_by,
                required_for_success=step.required_for_success,
            ),
            [],
        )

    max_iterations = int(step.loop.get("max_iterations") or spec.limits.max_iterations)
    max_iterations = min(max_iterations, spec.limits.max_iterations)
    while_output = step.loop.get("while_output")
    iteration_results: list[WorkflowStepResult] = []
    generated_steps: list[WorkflowStepSpec] = []
    iteration = 0
    while True:
        _check_control(deadline, control)
        if executed_budget["executed"] >= spec.limits.max_steps:
            raise WorkflowLimitError(f"Workflow exceeded max_steps={spec.limits.max_steps}.")
        executed_budget["executed"] += 1
        if control is not None:
            control.record_iteration(iteration, executed_budget["executed"])
        result = _run_once(
            step=step,
            spec=spec,
            plugin=plugin,
            output_root=output_root,
            results=results,
            loop_iteration=iteration,
            provenance_path=provenance_path,
            deadline=deadline,
            control=control,
            step_output_root=step_output_root,
        )
        iteration_results.append(result)
        results[step.id] = result
        _check_control(deadline, control)
        planner = getattr(plugin, "plan_next", None)
        planned = planner(result, _step_context(
            spec=spec,
            output_root=output_root,
            step_output_dir=step_output_root or output_root / "step_outputs" / step.id,
            results=results,
            loop_iteration=iteration,
            deadline=deadline,
            control=control,
        )) if callable(planner) else []
        _check_control(deadline, control)
        if planned:
            generated_steps.extend(_normalize_generated_steps(planned, generated_by=step.id))
        should_continue = False
        if result.status == "completed" and while_output:
            should_continue = bool(result.outputs.get(str(while_output)))
        iteration += 1
        if not should_continue:
            break
        if iteration >= max_iterations:
            raise WorkflowLimitError(f"Workflow step '{step.id}' exceeded max_iterations={max_iterations}.")

    final = iteration_results[-1]
    final.iteration_count = len(iteration_results)
    if len(iteration_results) > 1:
        final.outputs = {
            **final.outputs,
            "iteration_outputs": [item.outputs for item in iteration_results],
        }
    return final, generated_steps


def _build_acceptance(spec: WorkflowSpec, results: dict[str, WorkflowStepResult]) -> dict[str, Any]:
    required = set(spec.acceptance.required_steps)
    for step in spec.steps:
        if step.required_for_success:
            required.add(step.id)
    blocking: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for step_id in sorted(required):
        result = results.get(step_id)
        if result is None:
            blocking.append({"step_id": step_id, "reason": "missing_required_step"})
            continue
        if result.status == "failed":
            blocking.append({"step_id": step_id, "reason": "required_step_failed", "error": result.error})
        elif result.status == "skipped":
            blocking.append({"step_id": step_id, "reason": "required_step_skipped"})
    for step_id, result in results.items():
        if result.status == "failed" and step_id not in required:
            warnings.append({"step_id": step_id, "reason": "optional_step_failed", "error": result.error})
    accepted = not blocking if spec.acceptance.fail_on_required_failure else True
    return {
        "schema_version": "qcchem.workflow_acceptance.v0.1-alpha",
        "accepted": accepted,
        "required_steps": sorted(required),
        "blocking_failures": blocking,
        "warnings": warnings,
        "recommended_action": "review_workflow_outputs" if accepted and warnings else "promote_workflow_outputs" if accepted else "resolve_workflow_failures",
    }


def _run_checkpointed_workflow(
    spec: WorkflowSpec,
    *,
    root: Path,
    registry: dict[str, WorkflowStepPlugin],
    control: WorkflowControl,
    initial_results: dict[str, WorkflowStepResult] | None = None,
) -> WorkflowRunResult:
    """Execute only uncommitted steps while the caller holds the output lock."""
    provenance_path = contained_output_path(root, "provenance.jsonl")
    _append_provenance(
        provenance_path,
        {
            "timestamp": _now(),
            "event_type": "workflow_resumed" if initial_results is not None else "workflow_started",
            "workflow_name": spec.name,
            "source_path": str(spec.source_path),
            "run_id": control.state["run_id"],
            "session_id": control.state["session_id"],
            "reused_steps": list(initial_results or {}),
        },
    )
    start = time.monotonic()
    results = dict(initial_results or {})
    pending = [step for step in spec.steps if step.id not in results]
    executed_budget = {"executed": control.state["executed_step_count"]}
    deadline = None if spec.limits.max_wall_time_seconds is None else start + spec.limits.max_wall_time_seconds
    abort_status: str | None = None
    abort_error = ""
    while pending:
        progressed = False
        for step in list(pending):
            try:
                _check_control(deadline, control)
            except (TimeoutError, WorkflowCancelledError, KeyboardInterrupt) as exc:
                abort_status = _interruption_status(exc)
                abort_error = str(exc) or "Workflow interrupted by user."
                break
            if not all(need in results for need in step.needs):
                continue
            pending.remove(step)
            progressed = True
            step_output_root = control.begin_step(step.id)
            generated: list[WorkflowStepSpec] = []
            if any(results[need].status != "completed" for need in step.needs):
                result = WorkflowStepResult(
                    step_id=step.id,
                    kind=step.kind,
                    plugin=_plugin_key(step),
                    status="skipped",
                    outputs={"skip_reason": "dependency_not_completed"},
                    started_at=_now(),
                    completed_at=_now(),
                    generated_by=step.generated_by,
                    required_for_success=step.required_for_success,
                )
            else:
                try:
                    result, generated = _execute_step(
                        step=step,
                        spec=spec,
                        registry=registry,
                        output_root=root,
                        results=results,
                        provenance_path=provenance_path,
                        executed_budget=executed_budget,
                        deadline=deadline,
                        control=control,
                        step_output_root=step_output_root,
                    )
                except (Exception, KeyboardInterrupt) as exc:
                    if isinstance(exc, (TimeoutError, WorkflowLimitError, WorkflowCancelledError, KeyboardInterrupt)):
                        abort_status = _interruption_status(exc)
                        abort_error = str(exc) or "Workflow interrupted by user."
                    result = WorkflowStepResult(
                        step_id=step.id,
                        kind=step.kind,
                        plugin=_plugin_key(step),
                        status=abort_status or "failed",
                        attempts=(control.state["active_step"] or {}).get("attempt", 0),
                        iteration_count=(control.state["active_step"] or {}).get("iteration", 0) + 1,
                        outputs={},
                        error=f"{type(exc).__name__}: {exc}" if str(exc) else "Workflow interrupted by user.",
                        started_at=_now(),
                        completed_at=_now(),
                        generated_by=step.generated_by,
                        required_for_success=step.required_for_success,
                    )
                    generated = []
            if generated:
                existing_ids = {item.id for item in spec.steps}
                try:
                    for generated_step in generated:
                        if generated_step.id in existing_ids:
                            raise ValueError(f"Generated workflow step id already exists: {generated_step.id}")
                        _validate_step_plugin(generated_step, registry)
                    validate_workflow_spec(
                        WorkflowSpec(
                            version=spec.version,
                            name=spec.name,
                            description=spec.description,
                            output_root=spec.output_root,
                            limits=spec.limits,
                            parameters=spec.parameters,
                            steps=[*spec.steps, *generated],
                            acceptance=spec.acceptance,
                            source_path=spec.source_path,
                        )
                    )
                except Exception as exc:
                    abort_status = "failed"
                    abort_error = f"Dynamic step validation failed for '{step.id}': {type(exc).__name__}: {exc}"
                    result.status = "failed"
                    result.error = abort_error
                    _append_provenance(
                        provenance_path,
                        {
                            "timestamp": _now(),
                            "event_type": "dynamic_step_validation_failed",
                            "step_id": step.id,
                            "error": abort_error,
                        },
                    )
                else:
                    for generated_step in generated:
                        spec.steps.append(generated_step)
                        pending.append(generated_step)
                        existing_ids.add(generated_step.id)
                    _append_provenance(
                        provenance_path,
                        {
                            "timestamp": _now(),
                            "event_type": "steps_generated",
                            "step_id": step.id,
                            "generated_steps": [item.id for item in generated],
                        },
                    )
            results[step.id] = result
            control.commit_step(result, spec, registry)
            if abort_status:
                break
            if result.status == "failed" and step.required_for_success and not step.continue_on_error:
                abort_status = "failed"
                abort_error = result.error
                break
        if abort_status:
            break
        if not progressed:
            abort_status = "failed"
            abort_error = "Workflow could not make dependency progress."
            break

    try:
        _check_control(deadline, control)
        # An explicitly retried plugin may share an external output destination
        # with a reused step. Do not accept stale cached results after that write.
        if abort_status is None:
            for step_id in initial_results or {}:
                manifests = control.state["manifests"][step_id]
                verify_manifest(manifests["inputs"], label=f"reused step '{step_id}' inputs")
                verify_manifest(manifests["outputs"], label=f"reused step '{step_id}' outputs")
                _check_control(deadline, control)
    except (TimeoutError, WorkflowCancelledError, KeyboardInterrupt) as exc:
        if abort_status is None:
            abort_status = _interruption_status(exc)
            abort_error = str(exc) or "Workflow interrupted by user."
    except ValueError as exc:
        abort_status, abort_error = "failed", str(exc)
    acceptance = _build_acceptance(spec, results)
    if abort_status:
        acceptance["accepted"] = False
        acceptance["recommended_action"] = "resume_workflow_after_review" if abort_status in {"cancelled", "interrupted"} else "resolve_workflow_failures"
    completed = [item for item in results.values() if item.status == "completed"]
    failed = [item for item in results.values() if item.status == "failed"]
    skipped = [item for item in results.values() if item.status == "skipped"]
    status = abort_status or ("completed" if acceptance["accepted"] else "failed")
    if abort_status and abort_error:
        acceptance.setdefault("blocking_failures", []).append({"reason": "workflow_aborted", "error": abort_error})
    graph = _build_graph(spec, results)
    result = WorkflowRunResult(
        schema_version=SCHEMA_VERSION,
        workflow_name=spec.name,
        status=status,
        artifact_root=root,
        source_path=spec.source_path,
        steps=list(results.values()),
        summary={
            "total_steps": len(spec.steps),
            "completed_steps": len(completed),
            "failed_steps": len(failed),
            "skipped_steps": len(skipped),
            "generated_steps": len([step for step in spec.steps if step.generated_by]),
            "executed_step_count": executed_budget["executed"],
            "run_id": control.state["run_id"],
            "session_id": control.state["session_id"],
            "session_count": control.state["session_count"],
            "reused_steps": list(initial_results or {}),
        },
        acceptance_summary=acceptance,
        graph=graph,
        outputs={
            "workflow_result_json": str(root / "workflow_result.json"),
            "workflow_report_markdown": str(root / "workflow_report.md"),
            "workflow_graph_json": str(root / "workflow_graph.json"),
            "provenance_jsonl": str(provenance_path),
            "registry_json": str(root / "registry.json"),
            "workflow_checkpoint_json": str(root / "workflow_checkpoint.json"),
        },
    )
    write_result_json(graph, contained_output_path(root, "workflow_graph.json"))
    write_result_json(result, contained_output_path(root, "workflow_result.json"))
    contained_output_path(root, "workflow_report.md").write_text(render_workflow_report(result), encoding="utf-8")
    write_registry(
        [
            make_registry_entry(
                name=step.step_id,
                kind=f"workflow:{step.kind}",
                status=step.status,
                artifact_root=root / "step_outputs" / step.step_id,
                source=step.plugin or step.kind,
                tags=["workflow-step"],
            )
            for step in result.steps
        ]
        + [
            make_registry_entry(
                name=spec.name,
                kind="workflow",
                status=status,
                artifact_root=root,
                source=str(spec.source_path or "workflow"),
                tags=["workflow"],
            )
        ],
        contained_output_path(root, "registry.json"),
    )
    _append_provenance(
        provenance_path,
        {
            "timestamp": _now(),
            "event_type": "workflow_completed",
            "workflow_name": spec.name,
            "status": status,
            "accepted": acceptance["accepted"],
        },
    )
    control.finish(result, error=abort_error)
    return result


def _execute_owned_workflow(
    spec: WorkflowSpec, *, root: Path, registry: dict[str, WorkflowStepPlugin],
    control: WorkflowControl, initial_results: dict[str, WorkflowStepResult] | None = None,
) -> WorkflowRunResult:
    try:
        return _run_checkpointed_workflow(
            spec, root=root, registry=registry, control=control, initial_results=initial_results,
        )
    except BaseException as exc:
        # Unexpected I/O errors, SystemExit, and interrupts outside plugin calls
        # leave the last active step uncertain. Never claim a completed workflow.
        control.state["status"] = "interrupted"
        control.state["error"] = f"{type(exc).__name__}: {exc}"
        control.state.pop("run_result", None)
        control.state.pop("final_outputs", None)
        try:
            control.save()
        except (OSError, ValueError):
            pass  # The prior atomic checkpoint remains the recovery authority.
        raise


def run_custom_workflow(
    spec: WorkflowSpec,
    *,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> WorkflowRunResult:
    """Run a validated workflow with a durable checkpoint and execution lock."""
    spec = deepcopy(spec)
    registry = workflow_plugin_registry()
    validate_workflow_plugins(spec, registry)
    root = workflow_root(output_dir or spec.output_root)
    spec.output_root = root
    workflow_fingerprint(spec)  # Reject non-JSON/non-finite data before mutation.
    with WorkflowLock(root) as lock:
        root = prepare_clean_output_root(root, workflow_name="Workflow", overwrite=overwrite)
        control = WorkflowControl.create(root, spec, registry)
        lock.activate(control.state)
        return _execute_owned_workflow(spec, root=root, registry=registry, control=control)


def _restore_run_result(payload: dict[str, Any]) -> WorkflowRunResult:
    restored = dict(payload)
    restored["artifact_root"] = Path(restored["artifact_root"])
    restored["source_path"] = Path(restored["source_path"]) if restored.get("source_path") else None
    restored["steps"] = [WorkflowStepResult(**item) for item in restored["steps"]]
    return WorkflowRunResult(**restored)


def _resume_results(
    spec: WorkflowSpec, state: dict[str, Any], retry_steps: list[str],
) -> dict[str, WorkflowStepResult]:
    """Select reusable results without changing any artifact or checkpoint."""
    try:
        results = {key: WorkflowStepResult(**item) for key, item in state["results"].items()}
    except (TypeError, KeyError) as exc:
        raise ValueError("Workflow checkpoint has invalid step result fields.") from exc
    retry = set(retry_steps)
    active = state.get("active_step")
    uncertain = {active["step_id"]} if active else set()
    retryable = uncertain | {key for key, result in results.items() if result.status in {"failed", "cancelled", "interrupted"}}
    if retry - retryable:
        raise ValueError(f"--retry-step only accepts failed, cancelled, or interrupted steps: {', '.join(sorted(retry - retryable))}")
    required_retry = uncertain | {
        key for key, result in results.items()
        if result.status in {"cancelled", "interrupted"} or (result.status == "failed" and state["status"] != "completed")
    }
    if required_retry - retry:
        raise ValueError(
            "Review partial artifacts and explicitly allow rerunning each uncertain/failed step with "
            f"--retry-step: {', '.join(sorted(required_retry - retry))}. External side effects may already have occurred."
        )
    invalidated = set(retry)
    while True:
        descendants = {step.id for step in spec.steps if set(step.needs) & invalidated}
        if descendants <= invalidated:
            break
        invalidated.update(descendants)
    completed = {key for key in invalidated if key in results and results[key].status == "completed"}
    if completed:
        raise ValueError(f"Retry would discard completed dependent results: {', '.join(sorted(completed))}. Use a new output root.")
    # A failed planner can have committed generated steps. Regenerate its
    # unfinished subgraph rather than appending duplicate step IDs on retry.
    generated = set()
    while True:
        more = {step.id for step in spec.steps if step.generated_by in retry | generated}
        if more <= generated:
            break
        generated.update(more)
    if any(key in results and results[key].status == "completed" for key in generated):
        raise ValueError("Retry would replace completed generated steps; use a new output root.")
    spec.steps = [step for step in spec.steps if step.id not in generated]
    validate_workflow_spec(spec)
    return {key: result for key, result in results.items() if key not in invalidated | generated}


def _prepare_workflow_resume(spec: WorkflowSpec, root: Path, registry: dict, retry_steps: list[str]):
    """Shared read-only preflight; execution calls it while owning the lock."""
    from qcchem.io.workflow_config import _parse_step

    state = read_checkpoint(root)
    if workflow_fingerprint(spec) != state["workflow_sha256"]:
        raise ValueError("Workflow configuration/source path differs from the checkpoint; use the original config or a new output root.")
    spec.steps = [_parse_step(item) for item in state["steps"]]
    validate_workflow_plugins(spec, registry)
    if implementation_identity(registry, spec.steps) != state["implementation"]:
        raise ValueError("Workflow implementation, plugin identity, or environment changed; recovery requires the original software or a new run.")
    results = _resume_results(spec, state, retry_steps)
    for step_id in results:
        manifests = state["manifests"].get(step_id)
        if not manifests:
            raise ValueError(f"Workflow checkpoint lacks manifests for step '{step_id}'.")
        verify_manifest(manifests.get("inputs", {}), label=f"step '{step_id}' inputs")
        verify_manifest(manifests.get("outputs", {}), label=f"step '{step_id}' outputs")
    if state.get("final_outputs"):
        verify_manifest(state["final_outputs"], label="workflow result sidecars")
    return state, results


def preview_workflow_resume_from_config(
    path: Path, *, output_dir: Path | None = None, retry_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Validate and describe recovery without creating locks or changing files."""
    from qcchem.workflow.workflow_control import workflow_status

    spec = load_workflow_spec(path)
    root = workflow_root(output_dir or spec.output_root)
    spec.output_root = root
    status = workflow_status(root)
    if status["worker_active"]:
        raise ValueError("Workflow is active; wait for it to stop before reviewing recovery.")
    registry = workflow_plugin_registry()
    state, results = _prepare_workflow_resume(spec, root, registry, retry_steps or [])
    pending = [step for step in spec.steps if step.id not in results]
    if not pending:
        raise ValueError("No unfinished workflow steps require recovery.")
    # Snapshot known pending/retry inputs so confirmation also detects changes
    # that would otherwise be permitted by an explicitly retried whole step.
    paths = [spec.source_path]
    input_manifests = [item.get("inputs", {}) for item in state["manifests"].values()]
    input_manifests.append((state.get("active_step") or {}).get("inputs", {}))
    for manifest in input_manifests:
        paths.extend(Path(item) for item in manifest.get("roots", []))
    for step in pending:
        inputs = {key: item for key, item in step.inputs.items() if key not in {"output_dir", "output_root", "report_markdown"}}
        try:
            inputs = _resolve_value(inputs, spec=spec, results=results, output_root=root)
        except (ValueError, KeyError):
            pass  # Future output references do not exist until their producer runs.
        paths.extend(detected_paths(inputs, base_dir=spec.source_path.parent, root=root))
    from qcchem.workflow.workflow_plugins import _config_input_paths

    for config in list(paths):
        if config.suffix.lower() in {".yaml", ".yml"} and config.is_file():
            paths.extend(_config_input_paths(config))
    return {
        "artifact_root": str(root), "source_path": str(spec.source_path),
        "run_id": state["run_id"], "session_id": state["session_id"],
        "checkpoint_sha256": state["checkpoint_sha256"],
        "retry_steps": list(retry_steps or []), "reused_steps": list(results),
        "pending_steps": [{"id": step.id, "kind": step.kind} for step in pending],
        "review_inputs": file_manifest(paths),
    }


def resume_custom_workflow(
    spec: WorkflowSpec,
    *,
    output_dir: Path | None = None,
    retry_steps: list[str] | None = None,
    expected_checkpoint_sha256: str | None = None,
) -> WorkflowRunResult:
    """Resume a matching checkpoint; uncertain steps need explicit retry IDs."""
    spec = deepcopy(spec)
    registry = workflow_plugin_registry()
    validate_workflow_plugins(spec, registry)
    root = workflow_root(output_dir or spec.output_root)
    spec.output_root = root
    if not root.is_dir():
        raise ValueError(f"Workflow output root does not exist: {root}")
    with WorkflowLock(root) as lock:
        state, results = _prepare_workflow_resume(spec, root, registry, retry_steps or [])
        if expected_checkpoint_sha256 is not None and state["checkpoint_sha256"] != expected_checkpoint_sha256:
            raise ValueError("Workflow checkpoint changed after review; refresh and review recovery again.")
        if len(results) == len(spec.steps) and state.get("run_result") and state["status"] == state["run_result"]["status"]:
            return _restore_run_result(state["run_result"])
        control = WorkflowControl(root, state)
        control.start_resume(results=results, steps=spec.steps)
        lock.activate(control.state)
        return _execute_owned_workflow(spec, root=root, registry=registry, control=control, initial_results=results)


def resume_custom_workflow_from_config(
    path: Path,
    *,
    output_dir: Path | None = None,
    retry_steps: list[str] | None = None,
    expected_checkpoint_sha256: str | None = None,
) -> WorkflowRunResult:
    """Load the original configuration and resume its durable workflow."""
    return resume_custom_workflow(load_workflow_spec(path), output_dir=output_dir, retry_steps=retry_steps,
                                  expected_checkpoint_sha256=expected_checkpoint_sha256)


def run_custom_workflow_from_config(
    path: Path,
    *,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> WorkflowRunResult:
    """Load and run a custom workflow config."""
    return run_custom_workflow(load_workflow_spec(path), output_dir=output_dir, overwrite=overwrite)


def report_custom_workflow_result(result_json: Path, *, output_path: Path | None = None) -> dict[str, Any]:
    """Regenerate a workflow report from ``workflow_result.json``."""
    payload = json.loads(result_json.read_text(encoding="utf-8"))
    output = output_path or result_json.with_name("workflow_report.md")
    output.write_text(_render_workflow_report(payload), encoding="utf-8")
    return {"workflow_result_json": str(result_json), "workflow_report_markdown": str(output)}


def write_workflow_template(output_path: Path) -> Path:
    """Write a starter workflow YAML template."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(workflow_template(source_path=output_path, workspace_root=Path.cwd()), sort_keys=False),
        encoding="utf-8",
    )
    return output_path


def workflow_plugins_summary(*, include_installed: bool = True) -> dict[str, Any]:
    """Return discovered workflow plugins for CLI, AI, and Workbench."""
    plugins = describe_workflow_plugins(include_installed=include_installed)
    return {
        "schema_version": "qcchem.workflow_plugins.v0.1-alpha",
        "entry_point_group": "qcchem.workflow_steps",
        "plugin_count": len(plugins),
        "plugins": plugins,
    }
