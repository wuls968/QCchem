"""Hardware error diagnostics for runtime-backed QCchem artifacts."""

from __future__ import annotations

from typing import Any

from qcchem.core.chemical_accuracy import CHEMICAL_ACCURACY_HARTREE


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _runtime_shots(runtime: dict[str, Any]) -> int | None:
    metadata = _safe_dict(_safe_dict(runtime.get("returned_job_metadata")).get("metadata"))
    for value in (
        metadata.get("shots"),
        _safe_dict(runtime.get("options_snapshot")).get("shots"),
        _safe_dict(runtime.get("options_snapshot")).get("default_shots"),
        _safe_dict(runtime.get("options_snapshot")).get("max_budgeted_shots"),
    ):
        if value is not None:
            return int(value)
    return None


def _runtime_expectation(runtime: dict[str, Any]) -> float | None:
    evs = _safe_dict(runtime.get("returned_job_metadata")).get("evs")
    if isinstance(evs, list) and evs:
        return _safe_float(evs[0])
    return None


def _runtime_statistical_error(payload: dict[str, Any], runtime: dict[str, Any]) -> float | None:
    runtime_accuracy = _safe_dict(payload.get("runtime_chemical_accuracy"))
    value = _safe_float(runtime_accuracy.get("statistical_error"))
    if value is not None:
        return value
    stds = _safe_dict(runtime.get("returned_job_metadata")).get("stds")
    if isinstance(stds, list) and stds:
        return _safe_float(stds[0])
    return _safe_float(_safe_dict(payload.get("benchmark")).get("statistical_error"))


def _derive_runtime_total_error(payload: dict[str, Any], runtime: dict[str, Any]) -> float | None:
    runtime_accuracy = _safe_dict(payload.get("runtime_chemical_accuracy"))
    value = _safe_float(runtime_accuracy.get("absolute_error_hartree"))
    if value is not None:
        return value
    expectation = _runtime_expectation(runtime)
    energy = _safe_dict(payload.get("energy"))
    exact = _safe_dict(payload.get("exact_baseline"))
    exact_total = _safe_float(exact.get("total_energy"))
    constant = _safe_float(energy.get("constant_energy_correction"))
    nuclear = _safe_float(energy.get("nuclear_repulsion_energy"))
    if expectation is None or exact_total is None or constant is None or nuclear is None:
        return None
    runtime_total = expectation + constant + nuclear
    return abs(runtime_total - exact_total)


def _mitigation_flags(payload: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    mitigation = _safe_dict(payload.get("mitigation"))
    options = _safe_dict(runtime.get("options_snapshot"))
    estimator_options = _safe_dict(options.get("estimator_options"))
    return {
        "applied_methods": list(mitigation.get("applied_methods") or []),
        "symmetry_check_enabled": bool(_safe_dict(mitigation.get("symmetry_check")).get("enabled")),
        "readout_mitigation_enabled": bool(_safe_dict(mitigation.get("readout_mitigation")).get("enabled")),
        "zne_enabled": bool(_safe_dict(mitigation.get("zne")).get("enabled")),
        "pec_enabled": bool(_safe_dict(mitigation.get("pec")).get("enabled")),
        "runtime_resilience_level": options.get("resilience_level"),
        "runtime_estimator_options": estimator_options,
        "dynamical_decoupling_enabled": bool(
            _safe_dict(estimator_options.get("dynamical_decoupling")).get("enable")
        ),
        "twirling_enabled": "twirling" in estimator_options,
        "measure_mitigation_enabled": bool(
            _safe_dict(_safe_dict(estimator_options.get("resilience")).get("measure_mitigation")).get("enable")
            if isinstance(_safe_dict(estimator_options.get("resilience")).get("measure_mitigation"), dict)
            else _safe_dict(estimator_options.get("resilience")).get("measure_mitigation", False)
        ),
    }


def _diagnostic_label(
    *,
    runtime: dict[str, Any],
    local_error: float | None,
    runtime_error: float | None,
    statistical_error: float | None,
    threshold: float,
    mitigation_flags: dict[str, Any],
) -> str:
    if not (runtime.get("submitted") and runtime.get("succeeded")):
        return "missing_runtime_result"
    if local_error is not None and local_error > threshold:
        return "local_baseline_not_validated"
    if runtime_error is None:
        return "inconclusive"
    if statistical_error is not None and runtime_error <= max(2.0 * statistical_error, threshold):
        return "statistical_limit"
    mitigation_used = any(
        bool(mitigation_flags.get(key))
        for key in (
            "readout_mitigation_enabled",
            "zne_enabled",
            "pec_enabled",
            "dynamical_decoupling_enabled",
            "twirling_enabled",
            "measure_mitigation_enabled",
        )
    )
    if mitigation_used and local_error is not None and runtime_error > local_error + threshold:
        return "mitigation_regressed"
    if local_error is not None and runtime_error > local_error + threshold:
        return "hardware_bias_or_layout"
    return "inconclusive"


def _next_measurement(label: str) -> str:
    return {
        "missing_runtime_result": "collect_runtime_result",
        "local_baseline_not_validated": "tighten_local_exact_or_reference_baseline",
        "statistical_limit": "increase_shots_or_repeat_count_before_changing_algorithm",
        "hardware_bias_or_layout": "compare_layout_mapping_and_backend_error_profile",
        "mitigation_regressed": "rerun_without_regressing_mitigation_combo_before_more_budget",
        "inconclusive": "add_one_controlled_runtime_comparator_with_same_local_baseline",
    }.get(label, "review_hardware_boundary")


def build_hardware_error_diagnostic(
    payload: dict[str, Any],
    *,
    runtime_submission_sidecar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a conservative diagnostic of runtime-derived chemistry error."""

    runtime = _safe_dict(runtime_submission_sidecar) or _safe_dict(payload.get("runtime_submission"))
    benchmark = _safe_dict(payload.get("benchmark"))
    chemical = _safe_dict(payload.get("chemical_accuracy"))
    runtime_error = _derive_runtime_total_error(payload, runtime)
    local_error = _safe_float(chemical.get("absolute_error_hartree"))
    if local_error is None:
        local_error = _safe_float(benchmark.get("absolute_error"))
    threshold = (
        _safe_float(chemical.get("threshold_hartree"))
        or _safe_float(benchmark.get("absolute_error_threshold"))
        or CHEMICAL_ACCURACY_HARTREE
    )
    statistical_error = _runtime_statistical_error(payload, runtime)
    mitigation_flags = _mitigation_flags(payload, runtime)
    label = _diagnostic_label(
        runtime=runtime,
        local_error=local_error,
        runtime_error=runtime_error,
        statistical_error=statistical_error,
        threshold=threshold,
        mitigation_flags=mitigation_flags,
    )
    simulator_runtime_gap = (
        None if local_error is None or runtime_error is None else abs(runtime_error - local_error)
    )
    return {
        "available": True,
        "diagnostic_label": label,
        "next_measurement": _next_measurement(label),
        "local_error_hartree": local_error,
        "runtime_error_hartree": runtime_error,
        "simulator_runtime_gap_hartree": simulator_runtime_gap,
        "statistical_error_hartree": statistical_error,
        "threshold_hartree": threshold,
        "shots": _runtime_shots(runtime),
        "layout_strategy": runtime.get("layout_strategy"),
        "selected_layout": runtime.get("selected_layout"),
        "transpiled_depth": runtime.get("transpiled_depth"),
        "transpiled_two_qubit_gate_count": runtime.get("transpiled_two_qubit_gate_count"),
        "backend_name": runtime.get("backend_name"),
        "job_id": runtime.get("job_id"),
        "runtime_submitted": bool(runtime.get("submitted")),
        "runtime_succeeded": bool(runtime.get("succeeded")),
        "mitigation_flags": mitigation_flags,
        "source": "result_json+runtime_submission_sidecar"
        if runtime_submission_sidecar is not None
        else "result_json",
    }
