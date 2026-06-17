"""Execution-policy presets for QCchem."""

from __future__ import annotations

from copy import deepcopy

from qcchem.core import (
    BenchmarkSpec,
    ExecutionPolicySummary,
    MitigationSpec,
    PolicySpec,
    BackendSpec,
)


_POLICY_DEFAULTS: dict[str, dict[str, object]] = {
    "benchmark": {
        "default_shots": 4096,
        "default_repetitions": 5,
        "exact_baseline_required": True,
        "confidence_rule": "require exact baseline when available; use repeated sampling for shot backends",
        "mitigation_posture": "symmetry-check preferred",
        "runtime_ready_expected": False,
        "session_ready_expected": False,
        "batch_ready_expected": False,
        "noise_ready_expected": False,
        "symmetry_check_enabled": True,
        "readout_enabled": False,
    },
    "exploratory": {
        "default_shots": 1024,
        "default_repetitions": 1,
        "exact_baseline_required": False,
        "confidence_rule": "baseline optional; prioritize fast iteration",
        "mitigation_posture": "minimal mitigation",
        "runtime_ready_expected": False,
        "session_ready_expected": False,
        "batch_ready_expected": False,
        "noise_ready_expected": False,
        "symmetry_check_enabled": False,
        "readout_enabled": False,
    },
    "publication": {
        "default_shots": 8192,
        "default_repetitions": 5,
        "exact_baseline_required": True,
        "confidence_rule": "exact baseline and uncertainty reporting required",
        "mitigation_posture": "symmetry-check required, readout placeholder allowed",
        "runtime_ready_expected": True,
        "session_ready_expected": False,
        "batch_ready_expected": False,
        "noise_ready_expected": False,
        "symmetry_check_enabled": True,
        "readout_enabled": False,
    },
    "hardware_ready": {
        "default_shots": 16384,
        "default_repetitions": 7,
        "exact_baseline_required": True,
        "confidence_rule": "exact baseline preferred and repeated sampling mandatory",
        "mitigation_posture": "symmetry-check and readout-mitigation placeholders enabled",
        "runtime_ready_expected": True,
        "session_ready_expected": True,
        "batch_ready_expected": True,
        "noise_ready_expected": True,
        "symmetry_check_enabled": True,
        "readout_enabled": True,
    },
}


def _defaults_for(name: str) -> dict[str, object]:
    normalized = name.strip().lower()
    if normalized not in _POLICY_DEFAULTS:
        raise ValueError(f"Unsupported execution policy: {name}")
    return deepcopy(_POLICY_DEFAULTS[normalized])


def apply_policy_defaults(
    policy_name: str,
    backend_raw: dict[str, object],
    benchmark_raw: dict[str, object],
    mitigation_raw: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Merge policy defaults into raw config mappings without overriding explicit user values."""
    defaults = _defaults_for(policy_name)
    merged_backend = dict(backend_raw)
    merged_benchmark = dict(benchmark_raw)
    merged_mitigation = dict(mitigation_raw)

    if merged_backend.get("kind", "statevector") in {
        "shot_estimator",
        "aer_shot_estimator",
        "cudaq_sample",
    }:
        merged_backend.setdefault("shots", defaults["default_shots"])
        merged_backend.setdefault("repetitions", defaults["default_repetitions"])

    runtime = dict(merged_backend.get("runtime", {}))
    runtime.setdefault("enabled", bool(defaults["runtime_ready_expected"]))
    runtime.setdefault("runtime_ready", bool(defaults["runtime_ready_expected"]))
    runtime.setdefault("session_ready", bool(defaults["session_ready_expected"]))
    runtime.setdefault("batch_ready", bool(defaults["batch_ready_expected"]))
    runtime.setdefault("service", "local")
    runtime.setdefault("precision_target", None)
    runtime.setdefault("resilience_level", 0)
    runtime.setdefault("grouping_policy", "default")
    runtime.setdefault("options", {})
    merged_backend["runtime"] = runtime

    noise = dict(merged_backend.get("noise", {}))
    noise.setdefault("enabled", False)
    noise.setdefault("profile", "none")
    noise.setdefault("depolarizing_probability_1q", 0.0)
    noise.setdefault("depolarizing_probability_2q", 0.0)
    noise.setdefault("readout_error_probability", 0.0)
    noise.setdefault("basis_gates", [])
    merged_backend["noise"] = noise

    merged_benchmark.setdefault("enabled", True)
    if bool(defaults["exact_baseline_required"]):
        merged_benchmark.setdefault("exact_baseline_qubit_limit", 12)

    symmetry = dict(merged_mitigation.get("symmetry_check", {}))
    symmetry.setdefault("enabled", defaults["symmetry_check_enabled"])
    symmetry.setdefault("strategy", "parity_placeholder")
    merged_mitigation["symmetry_check"] = symmetry

    readout = dict(merged_mitigation.get("readout", {}))
    readout.setdefault("enabled", defaults["readout_enabled"])
    readout.setdefault("method", "placeholder")
    merged_mitigation["readout"] = readout

    merged_mitigation.setdefault("zne", {"enabled": False, "method": "placeholder"})
    merged_mitigation.setdefault("pec", {"enabled": False, "method": "placeholder"})
    return merged_backend, merged_benchmark, merged_mitigation


def resolve_execution_policy(
    policy_spec: PolicySpec,
    backend_spec: BackendSpec,
    benchmark_spec: BenchmarkSpec,
    mitigation_spec: MitigationSpec,
) -> ExecutionPolicySummary:
    """Resolve a QCchem execution policy to a persisted summary."""
    defaults = _defaults_for(policy_spec.name)
    default_shots = (
        defaults["default_shots"]
        if backend_spec.kind in {"shot_estimator", "aer_shot_estimator", "cudaq_sample"}
        else None
    )
    return ExecutionPolicySummary(
        name=policy_spec.name,
        default_shots=default_shots,
        default_repetitions=max(backend_spec.repetitions, int(defaults["default_repetitions"])),
        exact_baseline_required=bool(defaults["exact_baseline_required"]) and benchmark_spec.enabled,
        confidence_rule=str(defaults["confidence_rule"]),
        mitigation_posture=str(defaults["mitigation_posture"]),
        runtime_ready_expected=bool(defaults["runtime_ready_expected"]),
        session_ready_expected=bool(defaults["session_ready_expected"]),
        batch_ready_expected=bool(defaults["batch_ready_expected"]),
        noise_ready_expected=bool(defaults["noise_ready_expected"]),
    )
