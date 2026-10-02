"""Input and output helpers for QCchem.

Load configuration parsers on demand so checkpoint and control helpers remain
usable without the scientific execution stack.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "build_artifact_index",
    "build_artifact_index_entry",
    "load_campaign_spec",
    "load_benchmark_suite_spec",
    "load_release_audit_spec",
    "load_run_spec",
    "load_scan_spec",
    "load_study_spec",
]

_EXPORTS = {
    "build_artifact_index": ("qcchem.io.artifact_index", "build_artifact_index"),
    "build_artifact_index_entry": ("qcchem.io.artifact_index", "build_artifact_index_entry"),
    "load_campaign_spec": ("qcchem.io.campaign_config", "load_campaign_spec"),
    "load_benchmark_suite_spec": ("qcchem.io.benchmark_config", "load_benchmark_suite_spec"),
    "load_release_audit_spec": ("qcchem.io.release_audit_config", "load_release_audit_spec"),
    "load_run_spec": ("qcchem.io.config", "load_run_spec"),
    "load_scan_spec": ("qcchem.io.scan_config", "load_scan_spec"),
    "load_study_spec": ("qcchem.io.study_config", "load_study_spec"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
