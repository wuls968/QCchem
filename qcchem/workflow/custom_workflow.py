"""Custom workflow execution engine for QCchem."""

from __future__ import annotations

import json
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
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.workflow_plugins import (
    WorkflowExecutionContext,
    WorkflowStepPlugin,
    describe_workflow_plugins,
    workflow_plugin_registry,
)

SCHEMA_VERSION = "qcchem.workflow_run.v0.1-alpha"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plugin_key(step: WorkflowStepSpec) -> str:
    return step.plugin or step.kind


def _append_provenance(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(to_primitive(event), sort_keys=True) + "\n")


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
        raise ValueError(f"Unsupported workflow step plugin/kind '{key}' for step '{step.id}'.")
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
) -> WorkflowStepResult:
    step_output_dir = output_root / "step_outputs" / step.id
    if loop_iteration:
        step_output_dir = step_output_dir / f"iteration_{loop_iteration:03d}"
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
    )
    resolved_inputs = _resolve_value(step.inputs, spec=spec, results=results, output_root=output_root)
    attempts = _normalize_retry_attempts(step)
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            warnings = plugin.validate(dict(resolved_inputs), context)
            outputs = plugin.run(dict(resolved_inputs), context)
            if warnings:
                outputs = {**outputs, "validation_warnings": warnings}
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
        if executed_budget["executed"] >= spec.limits.max_steps:
            raise RuntimeError(f"Workflow exceeded max_steps={spec.limits.max_steps}.")
        executed_budget["executed"] += 1
        result = _run_once(
            step=step,
            spec=spec,
            plugin=plugin,
            output_root=output_root,
            results=results,
            loop_iteration=iteration,
            provenance_path=provenance_path,
        )
        iteration_results.append(result)
        results[step.id] = result
        planned = plugin.plan_next(result, _step_context(
            spec=spec,
            output_root=output_root,
            step_output_dir=output_root / "step_outputs" / step.id,
            results=results,
            loop_iteration=iteration,
        ))
        if planned:
            generated_steps.extend(_normalize_generated_steps(planned, generated_by=step.id))
        should_continue = False
        if result.status == "completed" and while_output:
            should_continue = bool(result.outputs.get(str(while_output)))
        iteration += 1
        if not should_continue:
            break
        if iteration >= max_iterations:
            raise RuntimeError(f"Workflow step '{step.id}' exceeded max_iterations={max_iterations}.")

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


def run_custom_workflow(spec: WorkflowSpec, *, output_dir: Path | None = None) -> WorkflowRunResult:
    """Run one validated custom workflow spec and write its artifact bundle."""
    spec = deepcopy(spec)
    registry = workflow_plugin_registry()
    validate_workflow_plugins(spec, registry)
    root = (output_dir or spec.output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    provenance_path = root / "provenance.jsonl"
    if provenance_path.exists():
        provenance_path.unlink()
    _append_provenance(
        provenance_path,
        {
            "timestamp": _now(),
            "event_type": "workflow_started",
            "workflow_name": spec.name,
            "source_path": str(spec.source_path),
        },
    )
    start = time.monotonic()
    results: dict[str, WorkflowStepResult] = {}
    pending = list(spec.steps)
    executed_budget = {"executed": 0}
    aborted = False
    abort_error = ""
    while pending:
        if spec.limits.max_wall_time_seconds is not None and time.monotonic() - start > spec.limits.max_wall_time_seconds:
            aborted = True
            abort_error = f"Workflow exceeded max_wall_time_seconds={spec.limits.max_wall_time_seconds}."
            break
        progressed = False
        for step in list(pending):
            if not all(need in results for need in step.needs):
                continue
            pending.remove(step)
            progressed = True
            if any(results[need].status in {"failed", "skipped"} for need in step.needs):
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
                results[step.id] = result
                continue
            try:
                result, generated = _execute_step(
                    step=step,
                    spec=spec,
                    registry=registry,
                    output_root=root,
                    results=results,
                    provenance_path=provenance_path,
                    executed_budget=executed_budget,
                )
            except Exception as exc:
                result = WorkflowStepResult(
                    step_id=step.id,
                    kind=step.kind,
                    plugin=_plugin_key(step),
                    status="failed",
                    outputs={},
                    error=f"{type(exc).__name__}: {exc}",
                    started_at=_now(),
                    completed_at=_now(),
                    generated_by=step.generated_by,
                    required_for_success=step.required_for_success,
                )
                generated = []
            results[step.id] = result
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
                    aborted = True
                    abort_error = f"Dynamic step validation failed for '{step.id}': {type(exc).__name__}: {exc}"
                    _append_provenance(
                        provenance_path,
                        {
                            "timestamp": _now(),
                            "event_type": "dynamic_step_validation_failed",
                            "step_id": step.id,
                            "error": abort_error,
                        },
                    )
                    break
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
            if result.status == "failed" and step.required_for_success and not step.continue_on_error:
                aborted = True
                abort_error = result.error
                break
        if aborted:
            break
        if not progressed:
            aborted = True
            abort_error = "Workflow could not make dependency progress."
            break

    acceptance = _build_acceptance(spec, results)
    completed = [item for item in results.values() if item.status == "completed"]
    failed = [item for item in results.values() if item.status == "failed"]
    skipped = [item for item in results.values() if item.status == "skipped"]
    status = "failed" if aborted or not acceptance["accepted"] else "completed"
    if aborted and abort_error:
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
        },
        acceptance_summary=acceptance,
        graph=graph,
        outputs={
            "workflow_result_json": str(root / "workflow_result.json"),
            "workflow_report_markdown": str(root / "workflow_report.md"),
            "workflow_graph_json": str(root / "workflow_graph.json"),
            "provenance_jsonl": str(provenance_path),
            "registry_json": str(root / "registry.json"),
        },
    )
    write_result_json(graph, root / "workflow_graph.json")
    write_result_json(result, root / "workflow_result.json")
    (root / "workflow_report.md").write_text(render_workflow_report(result), encoding="utf-8")
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
        root / "registry.json",
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
    return result


def run_custom_workflow_from_config(path: Path, *, output_dir: Path | None = None) -> WorkflowRunResult:
    """Load and run a custom workflow config."""
    return run_custom_workflow(load_workflow_spec(path), output_dir=output_dir)


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
