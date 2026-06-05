"""Workflow orchestration for QCchem."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "collect_runtime_artifact",
    "run_agent_task",
    "run_agent_task_from_config",
    "run_benchmark_suite_from_config",
    "run_from_config",
    "run_hardware_optimization_from_config",
    "run_release_audit_from_config",
    "run_scan_from_config",
    "run_spec",
    "run_study_from_config",
    "summarize_agent_target",
]

_EXPORTS = {
    "collect_runtime_artifact": ("qcchem.workflow.runtime_collect", "collect_runtime_artifact"),
    "run_agent_task": ("qcchem.workflow.agent", "run_agent_task"),
    "run_agent_task_from_config": ("qcchem.workflow.agent", "run_agent_task_from_config"),
    "run_benchmark_suite_from_config": (
        "qcchem.workflow.benchmark",
        "run_benchmark_suite_from_config",
    ),
    "run_from_config": ("qcchem.workflow.runner", "run_from_config"),
    "run_hardware_optimization_from_config": (
        "qcchem.workflow.hardware_optimization",
        "run_hardware_optimization_from_config",
    ),
    "run_release_audit_from_config": (
        "qcchem.workflow.release_audit",
        "run_release_audit_from_config",
    ),
    "run_scan_from_config": ("qcchem.workflow.scan", "run_scan_from_config"),
    "run_spec": ("qcchem.workflow.runner", "run_spec"),
    "run_study_from_config": ("qcchem.workflow.study", "run_study_from_config"),
    "summarize_agent_target": ("qcchem.workflow.agent", "summarize_agent_target"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
