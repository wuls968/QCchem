"""Safe policy-resolution helpers for QCchem core workflows."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from qcchem.core import PolicyEngineResult, RunSpec
from qcchem.io.serialization import to_primitive

POLICY_PRESETS: dict[str, dict[str, Any]] = {
    "benchmark": {
        "backend.shots": 4096,
        "backend.repetitions": 5,
        "benchmark.enabled": True,
        "benchmark.exact_baseline_qubit_limit": 12,
        "mitigation.symmetry_check.enabled": True,
    },
    "exploratory": {
        "backend.shots": 1024,
        "backend.repetitions": 1,
        "benchmark.enabled": False,
        "mitigation.symmetry_check.enabled": False,
    },
    "publication": {
        "backend.shots": 8192,
        "backend.repetitions": 5,
        "benchmark.enabled": True,
        "mitigation.symmetry_check.enabled": True,
        "run.exports.qcschema_json": True,
        "run.exports.hdf5": True,
    },
    "hardware_ready": {
        "backend.shots": 16384,
        "backend.repetitions": 7,
        "backend.runtime.enabled": True,
        "backend.runtime.runtime_ready": True,
        "backend.runtime.session_ready": True,
        "backend.runtime.batch_ready": True,
    },
}


def resolve_policy(spec: RunSpec) -> PolicyEngineResult:
    """Resolve a safe policy snapshot without overriding explicit user settings."""
    policy_name = spec.policy.name.strip().lower()
    preset = deepcopy(POLICY_PRESETS.get(policy_name, {}))
    resolved_policy = to_primitive(spec)
    overrides_applied: list[str] = []
    for key, value in preset.items():
        if _path_is_unset(spec, key):
            _set_nested_value(resolved_policy, key, value)
            overrides_applied.append(key)
    return PolicyEngineResult(
        policy_name=policy_name,
        resolved_policy=resolved_policy,
        overrides_applied=overrides_applied,
        presets_used=[policy_name] if policy_name in POLICY_PRESETS else [],
        provenance={
            "source": "qcchem.backends.policy_engine",
            "allow_exploratory": spec.policy.allow_exploratory,
        },
    )


def _path_is_unset(spec: RunSpec, key_path: str) -> bool:
    current: Any = spec
    for part in key_path.split("."):
        if not hasattr(current, part):
            return True
        current = getattr(current, part)
    if current is None or current is False or current == "":
        return True
    if isinstance(current, (list, dict)) and not current:
        return True
    return False


def _set_nested_value(target: dict[str, Any], key_path: str, value: Any) -> None:
    current = target
    parts = key_path.split(".")
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value
