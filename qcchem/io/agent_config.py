"""Agent task config loading for AI-friendly QCchem orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from qcchem.io.config import resolve_user_path

SUPPORTED_AGENT_TASK_KINDS = {
    "run_config",
    "runtime_collect",
    "benchmark_suite",
    "study",
    "scan",
    "hardware_optimize_preview",
    "report",
    "compare_artifacts",
    "review_claims",
    "hardware_campaign_summary",
}


@dataclass(slots=True)
class AgentTaskSpec:
    """One AI-facing QCchem task definition."""

    version: str
    name: str
    kind: str
    description: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"Expected '{key}' to be a mapping, got {type(value).__name__}.")
    return value


def load_agent_task_spec(path: Path) -> AgentTaskSpec:
    """Load an agent-facing QCchem task definition from YAML or JSON."""
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Agent task configuration must deserialize to a mapping.")
    task_raw = _require_mapping(raw, "agent_task")

    kind = str(task_raw.get("kind", "")).strip()
    if kind not in SUPPORTED_AGENT_TASK_KINDS:
        raise ValueError(
            "agent_task.kind must be one of "
            f"{sorted(SUPPORTED_AGENT_TASK_KINDS)}, got '{kind}'."
        )

    inputs = _require_mapping(task_raw, "inputs")
    outputs = _require_mapping(task_raw, "outputs")
    policy = _require_mapping(task_raw, "policy")
    name = str(task_raw.get("name", "")).strip()
    if not name:
        raise ValueError("agent_task.name is required.")

    if kind == "runtime_collect" and "artifact_root" not in inputs:
        raise ValueError("runtime_collect tasks require inputs.artifact_root.")
    if kind in {"run_config", "benchmark_suite", "study", "scan", "hardware_optimize_preview"} and "config" not in inputs:
        raise ValueError(f"{kind} tasks require inputs.config.")
    if kind == "report" and "result_json" not in inputs:
        raise ValueError("report tasks require inputs.result_json.")
    if kind == "compare_artifacts" and "artifacts" not in inputs:
        raise ValueError("compare_artifacts tasks require inputs.artifacts.")
    if kind == "review_claims" and "targets" not in inputs:
        raise ValueError("review_claims tasks require inputs.targets.")
    if kind == "hardware_campaign_summary" and "target" not in inputs:
        raise ValueError("hardware_campaign_summary tasks require inputs.target.")

    return AgentTaskSpec(
        version=str(task_raw.get("version", "1")),
        name=name,
        kind=kind,
        description=str(task_raw.get("description", "")),
        inputs=inputs,
        outputs=outputs,
        policy=policy,
        source_path=resolved_path,
    )
