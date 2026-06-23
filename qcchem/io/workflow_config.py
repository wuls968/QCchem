"""YAML loading and validation for custom QCchem workflows."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from qcchem.core import (
    WorkflowAcceptanceSpec,
    WorkflowLimitsSpec,
    WorkflowRetrySpec,
    WorkflowSpec,
    WorkflowStepSpec,
)
from qcchem.io.config import resolve_user_path

REFERENCE_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"workflow.{key} must be a mapping.")
    return value


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"workflow.{key} must be a list.")
    return value


def _parse_retry(raw: Any) -> WorkflowRetrySpec:
    if raw is None or raw is False:
        return WorkflowRetrySpec()
    if raw is True:
        return WorkflowRetrySpec(max_retries=1)
    if isinstance(raw, int):
        return WorkflowRetrySpec(max_retries=max(raw, 0))
    if not isinstance(raw, dict):
        raise ValueError("workflow.steps[].retry must be a mapping, integer, or boolean.")
    if "max_retries" in raw:
        return WorkflowRetrySpec(max_retries=max(int(raw["max_retries"]), 0))
    if "max_attempts" in raw:
        return WorkflowRetrySpec(max_retries=max(int(raw["max_attempts"]) - 1, 0))
    return WorkflowRetrySpec()


def _parse_step(raw: Any) -> WorkflowStepSpec:
    if not isinstance(raw, dict):
        raise ValueError("workflow.steps entries must be mappings.")
    step_id = str(raw.get("id", "")).strip()
    kind = str(raw.get("kind", "")).strip()
    if not step_id:
        raise ValueError("workflow.steps[].id is required.")
    if not kind:
        raise ValueError(f"workflow.steps[{step_id}].kind is required.")
    needs_raw = raw.get("needs", [])
    if isinstance(needs_raw, str):
        needs = [needs_raw]
    elif isinstance(needs_raw, list):
        needs = [str(item) for item in needs_raw]
    else:
        raise ValueError(f"workflow.steps[{step_id}].needs must be a string or list.")
    loop = raw.get("loop", {})
    if loop is None or loop is False:
        loop = {}
    if loop is True:
        loop = {"while_output": "continue"}
    if not isinstance(loop, dict):
        raise ValueError(f"workflow.steps[{step_id}].loop must be a mapping or boolean.")
    return WorkflowStepSpec(
        id=step_id,
        kind=kind,
        plugin=str(raw["plugin"]).strip() if raw.get("plugin") is not None else None,
        inputs=dict(raw.get("inputs", {}) or {}),
        needs=needs,
        when=raw.get("when", True),
        loop=dict(loop),
        retry=_parse_retry(raw.get("retry")),
        continue_on_error=bool(raw.get("continue_on_error", False)),
        required_for_success=bool(raw.get("required_for_success", True)),
        generated_by=str(raw["generated_by"]) if raw.get("generated_by") is not None else None,
    )


def _references_in_value(value: Any) -> list[str]:
    if isinstance(value, str):
        return [match.group(1).strip() for match in REFERENCE_PATTERN.finditer(value)]
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_references_in_value(item))
        return refs
    if isinstance(value, dict):
        refs = []
        for item in value.values():
            refs.extend(_references_in_value(item))
        return refs
    return []


def referenced_step_ids(value: Any) -> set[str]:
    """Return step ids referenced by explicit ``${steps.<id>.outputs.<key>}`` syntax."""
    refs: set[str] = set()
    for ref in _references_in_value(value):
        parts = ref.split(".")
        if len(parts) >= 4 and parts[0] == "steps" and parts[2] == "outputs":
            refs.add(parts[1])
    return refs


def _add_implicit_needs(step: WorkflowStepSpec) -> None:
    refs = referenced_step_ids(step.inputs) | referenced_step_ids(step.when)
    refs.update(referenced_step_ids(step.loop))
    for ref in sorted(refs):
        if ref != step.id and ref not in step.needs:
            step.needs.append(ref)


def _validate_reference_shapes(spec: WorkflowSpec) -> None:
    step_ids = {step.id for step in spec.steps}
    parameter_keys = set(spec.parameters)
    for step in spec.steps:
        for ref in _references_in_value({"inputs": step.inputs, "when": step.when, "loop": step.loop}):
            parts = ref.split(".")
            if parts[0] == "steps":
                if len(parts) < 4 or parts[2] != "outputs":
                    raise ValueError(f"Unsupported workflow reference '${{{ref}}}'. Use steps.<id>.outputs.<key>.")
                if parts[1] not in step_ids:
                    raise ValueError(f"Workflow step '{step.id}' references unknown step '{parts[1]}'.")
                if parts[1] == step.id:
                    raise ValueError(f"Workflow step '{step.id}' cannot reference its own outputs.")
                continue
            if parts[0] == "parameters":
                if len(parts) < 2 or parts[1] not in parameter_keys:
                    raise ValueError(f"Workflow step '{step.id}' references unknown parameter '${{{ref}}}'.")
                continue
            if ref not in {"workflow.output_root", "workflow.name"}:
                raise ValueError(f"Unsupported workflow reference '${{{ref}}}'.")


def _validate_acyclic_steps(spec: WorkflowSpec) -> None:
    ids = [step.id for step in spec.steps]
    if len(ids) != len(set(ids)):
        raise ValueError("workflow.steps ids must be unique.")
    step_ids = set(ids)
    needs_by_id = {step.id: list(step.needs) for step in spec.steps}
    for step in spec.steps:
        for need in step.needs:
            if need not in step_ids:
                raise ValueError(f"Workflow step '{step.id}' needs unknown step '{need}'.")
            if need == step.id:
                raise ValueError(f"Workflow step '{step.id}' cannot need itself.")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> None:
        if step_id in visited:
            return
        if step_id in visiting:
            raise ValueError(f"Workflow dependency cycle detected at '{step_id}'.")
        visiting.add(step_id)
        for need in needs_by_id[step_id]:
            visit(need)
        visiting.remove(step_id)
        visited.add(step_id)

    for step_id in ids:
        visit(step_id)


def _validate_acceptance_steps(spec: WorkflowSpec) -> None:
    step_ids = {step.id for step in spec.steps}
    unknown = sorted(step_id for step_id in spec.acceptance.required_steps if step_id not in step_ids)
    if unknown:
        raise ValueError(
            "workflow.acceptance.required_steps references unknown step(s): "
            + ", ".join(unknown)
        )


def validate_workflow_spec(spec: WorkflowSpec) -> WorkflowSpec:
    """Validate a loaded workflow spec and return it for chaining."""
    if not spec.steps:
        raise ValueError("workflow.steps must contain at least one step.")
    if spec.limits.max_steps < 1:
        raise ValueError("workflow.limits.max_steps must be >= 1.")
    if spec.limits.max_iterations < 1:
        raise ValueError("workflow.limits.max_iterations must be >= 1.")
    if spec.limits.max_wall_time_seconds is not None and spec.limits.max_wall_time_seconds <= 0:
        raise ValueError("workflow.limits.max_wall_time_seconds must be positive when provided.")
    for step in spec.steps:
        _add_implicit_needs(step)
    _validate_reference_shapes(spec)
    _validate_acyclic_steps(spec)
    _validate_acceptance_steps(spec)
    return spec


def _workflow_spec_from_mapping(raw: Any, *, source_path: Path) -> WorkflowSpec:
    if not isinstance(raw, dict):
        raise ValueError("Workflow configuration must deserialize to a mapping.")
    data = _require_mapping(raw, "workflow")
    limits_raw = data.get("limits", {})
    if limits_raw is None or limits_raw is False:
        limits_raw = {}
    if not isinstance(limits_raw, dict):
        raise ValueError("workflow.limits must be a mapping.")
    acceptance_raw = data.get("acceptance", {})
    if acceptance_raw is None or acceptance_raw is False:
        acceptance_raw = {}
    if not isinstance(acceptance_raw, dict):
        raise ValueError("workflow.acceptance must be a mapping.")
    base_dir = source_path.parent
    output_root = data.get("output_root") or Path("artifacts") / "workflows" / str(data.get("name", "workflow"))
    spec = WorkflowSpec(
        version=str(data.get("version", "1")),
        name=str(data.get("name", "")).strip(),
        description=str(data.get("description", "")),
        output_root=(Path(str(output_root)).expanduser() if Path(str(output_root)).is_absolute() else (base_dir / str(output_root)).resolve()),
        limits=WorkflowLimitsSpec(
            max_steps=int(limits_raw.get("max_steps", 64)),
            max_iterations=int(limits_raw.get("max_iterations", 16)),
            max_wall_time_seconds=(
                float(limits_raw["max_wall_time_seconds"])
                if limits_raw.get("max_wall_time_seconds") is not None
                else None
            ),
        ),
        parameters=dict(data.get("parameters", {}) or {}),
        steps=[_parse_step(item) for item in _require_list(data, "steps")],
        acceptance=WorkflowAcceptanceSpec(
            required_steps=[str(item) for item in acceptance_raw.get("required_steps", [])],
            fail_on_required_failure=bool(acceptance_raw.get("fail_on_required_failure", True)),
        ),
        source_path=source_path,
    )
    if not spec.name:
        raise ValueError("workflow.name is required.")
    return validate_workflow_spec(spec)


def load_workflow_spec(path: Path) -> WorkflowSpec:
    """Load one custom workflow YAML config."""
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    return _workflow_spec_from_mapping(raw, source_path=resolved_path)


def load_workflow_spec_from_text(text: str, *, source_path: Path | None = None) -> WorkflowSpec:
    """Load one custom workflow YAML config from an editor buffer."""
    resolved_source = source_path or (Path.cwd() / "workflow.yaml")
    raw = yaml.safe_load(text)
    return _workflow_spec_from_mapping(raw, source_path=resolved_source)


def _workspace_relative_path(target: Path, *, source_dir: Path) -> str:
    """Return a portable path from a workflow file directory to a workspace target."""
    return Path(os.path.relpath(target, start=source_dir)).as_posix()


def workflow_template(*, source_path: Path | None = None, workspace_root: Path | None = None) -> dict[str, Any]:
    """Return a small starter workflow template."""
    config_path = "configs/h2_exact.yaml"
    output_root = "artifacts/workflows/h2_trust_first_workflow"
    if source_path is not None:
        resolved_source = source_path if source_path.is_absolute() else (Path.cwd() / source_path).resolve()
        root = (workspace_root or Path.cwd()).resolve()
        source_dir = resolved_source.parent.resolve()
        config_path = _workspace_relative_path(root / "configs" / "h2_exact.yaml", source_dir=source_dir)
        output_root = _workspace_relative_path(
            root / "artifacts" / "workflows" / "h2_trust_first_workflow",
            source_dir=source_dir,
        )
    return {
        "workflow": {
            "version": "1",
            "name": "h2_trust_first_workflow",
            "description": "Run H2, validate its evidence capsule, and render a workflow report.",
            "output_root": output_root,
            "limits": {"max_steps": 16, "max_iterations": 4},
            "parameters": {
                "claim": "The H2 local artifact is validated against an exact baseline.",
            },
            "steps": [
                {
                    "id": "run_h2",
                    "kind": "run_config",
                    "inputs": {
                        "config": config_path,
                    },
                },
                {
                    "id": "capsule_h2",
                    "kind": "capsule_validate",
                    "needs": ["run_h2"],
                    "inputs": {
                        "artifact_root": "${steps.run_h2.outputs.artifact_root}",
                    },
                },
                {
                    "id": "claim_h2",
                    "kind": "claim_check",
                    "needs": ["capsule_h2"],
                    "inputs": {
                        "targets": ["${steps.run_h2.outputs.artifact_root}"],
                        "claim_text": "${parameters.claim}",
                    },
                },
            ],
            "acceptance": {
                "required_steps": ["run_h2", "capsule_h2", "claim_h2"],
                "fail_on_required_failure": True,
            },
        }
    }
