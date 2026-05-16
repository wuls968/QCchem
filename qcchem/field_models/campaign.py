"""Field-model campaign metrics and guarded hardware gating."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

FIELD_MODEL_GATE_VERSION = "qcchem.field_model_campaign.v0.1-alpha"

GAUSS_OR_LEAKAGE_TOLERANCE = 1.0e-6
PHOTON_CUTOFF_DELTA_HARTREE_THRESHOLD = 1.0e-3
TROTTER_MAX_OBSERVABLE_ERROR_THRESHOLD = 1.0e-2
ANSATZ_VS_EXACT_HARTREE_THRESHOLD = 1.0e-3
MAX_HARDWARE_QUBITS = 8
MAX_HARDWARE_DEPTH = 200
MAX_HARDWARE_TWO_QUBIT_GATES = 80


def _primitive(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    return value


def _attr(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _max_numeric(values: list[Any]) -> float | None:
    numeric = [_as_float(value) for value in values]
    numeric = [value for value in numeric if value is not None]
    return max(numeric) if numeric else None


def _lattice_resource_estimate(qft_model: Any, mapping: Any) -> dict[str, Any]:
    if qft_model is None:
        return {}
    term_counts = dict(_attr(qft_model, "term_counts_by_sector", {}) or {})
    engine = dict(_attr(qft_model, "engine", {}) or {})
    return {
        "matter_qubits": _attr(qft_model, "matter_qubits"),
        "gauge_qubits": _attr(qft_model, "gauge_qubits"),
        "total_qubits": _attr(qft_model, "total_qubits"),
        "pauli_terms": _attr(mapping, "qubit_term_count"),
        "term_counts_by_sector": term_counts,
        "engine": engine,
        "projected_dimension": engine.get("projected_dimension"),
        "full_dimension": engine.get("full_dimension"),
    }


def _lattice_error_budget(qft_model: Any, qft_dynamics: dict[str, Any] | None) -> dict[str, Any]:
    if qft_model is None:
        return {}
    dynamics = qft_dynamics or {}
    return {
        "gauss_law": {
            "tolerance": _attr(qft_model, "constraints", {}).get("gauss_law_tolerance"),
            "reference_state_max_abs_gauss_law": (
                _attr(qft_model, "constraint_residuals", {}) or {}
            ).get("reference_state_max_abs_gauss_law"),
            "max_hamiltonian_gauge_commutator_norm": (
                _attr(qft_model, "constraint_residuals", {}) or {}
            ).get("max_hamiltonian_gauge_commutator_norm"),
        },
        "finite_cutoff": {
            "electric_cutoff": _attr(qft_model, "gauge_electric_cutoff"),
            "grid_shape": _attr(qft_model, "grid_shape"),
            "grid_spacing": _attr(qft_model, "grid_spacing"),
        },
        "trotter": dynamics.get("trotter_error_summary"),
    }


def _runtime_preview_from_dynamics(qft_dynamics: dict[str, Any] | None) -> dict[str, Any]:
    runtime_batch = (qft_dynamics or {}).get("runtime_batch") or {}
    pubs_preview = runtime_batch.get("pubs_preview") or []
    transpiled = runtime_batch.get("transpiled_pub_resources") or []
    return {
        "available": bool(runtime_batch.get("attempted")),
        "attempted": bool(runtime_batch.get("attempted")),
        "submitted": bool(runtime_batch.get("submitted")),
        "failure_category": runtime_batch.get("failure_category"),
        "pub_count": runtime_batch.get("pub_count"),
        "max_logical_depth": _max_numeric([item.get("circuit_depth") for item in pubs_preview if isinstance(item, dict)]),
        "max_transpiled_depth": _max_numeric(
            [item.get("transpiled_depth") for item in transpiled if isinstance(item, dict)]
        ),
        "max_transpiled_two_qubit_gate_count": _max_numeric(
            [
                item.get("transpiled_two_qubit_gate_count")
                for item in transpiled
                if isinstance(item, dict)
            ]
        ),
    }


def _trotter_metrics(qft_dynamics: dict[str, Any] | None) -> dict[str, Any]:
    dynamics = qft_dynamics or {}
    error_summary = dynamics.get("trotter_error_summary") or {}
    resources = ((dynamics.get("trotter") or {}).get("circuit_resources") or {})
    error_values = [
        value
        for key, value in error_summary.items()
        if key.startswith("max_") and key.endswith("_error")
    ]
    return {
        "trotter_error_summary": error_summary,
        "max_trotter_observable_error": _max_numeric(error_values),
        "trotter_step": resources.get("trotter_step") or (dynamics.get("evolution") or {}).get("trotter_step"),
        "trotter_max_depth": resources.get("max_depth"),
        "trotter_max_operation_count": resources.get("max_operation_count"),
        "trotter_max_two_qubit_gate_count": resources.get("max_two_qubit_gate_count"),
    }


def _cavity_observable_metrics(cavity_model: Any) -> dict[str, Any]:
    if cavity_model is None:
        return {}
    observables = dict(_attr(cavity_model, "observables", {}) or {})
    error_budget = dict(_attr(cavity_model, "error_budget", {}) or {})
    photon_occupation = observables.get("photon_occupation") or []
    occupation_values = [
        item.get("expectation")
        for item in photon_occupation
        if isinstance(item, dict)
    ]
    composition = observables.get("polaritonic_state_composition") or []
    boundary_weights: list[float] = []
    for item in composition:
        if not isinstance(item, dict):
            continue
        if item.get("occupation") == item.get("max_occupation"):
            value = _as_float(item.get("weight"))
            if value is not None:
                boundary_weights.append(value)
    return {
        "photon_occupation": photon_occupation,
        "max_photon_occupation": _max_numeric(occupation_values),
        "boundary_photon_occupation_weight": max(boundary_weights) if boundary_weights else None,
        "photon_physical_subspace_leakage": observables.get("photon_physical_subspace_leakage"),
        "dipole_expectation": observables.get("dipole_expectation") or [],
        "electron_photon_coupling_energy": observables.get("electron_photon_coupling_energy") or [],
        "dipole_self_energy": observables.get("dipole_self_energy") or [],
        "polaritonic_state_composition": composition,
        "exact_residual_norm": observables.get("exact_residual_norm"),
        "vqe_vs_exact_error": observables.get("vqe_vs_exact_error"),
        "photon_cutoff_delta_hartree": None,
        "error_budget": error_budget,
    }


def _runtime_preview_from_submission(runtime_submission: Any) -> dict[str, Any]:
    if runtime_submission is None:
        return {
            "available": False,
            "attempted": False,
            "submitted": False,
            "failure_category": None,
        }
    payload = _primitive(runtime_submission)
    if not isinstance(payload, dict):
        return {
            "available": False,
            "attempted": False,
            "submitted": False,
            "failure_category": None,
        }
    return {
        "available": bool(payload.get("attempted")),
        "attempted": bool(payload.get("attempted")),
        "submitted": bool(payload.get("submitted")),
        "failure_category": payload.get("failure_category"),
        "max_transpiled_depth": payload.get("transpiled_depth"),
        "max_transpiled_two_qubit_gate_count": payload.get("transpiled_two_qubit_gate_count"),
        "backend_name": payload.get("backend_name"),
        "job_id": payload.get("job_id"),
    }


def extract_field_model_case_metrics(result: Any) -> dict[str, Any]:
    """Extract model-agnostic field-model metrics from a run result."""
    field_model = _attr(result, "field_model")
    qft_model = _attr(result, "qft_model")
    cavity_model = _attr(result, "cavity_qed_model")
    qft_dynamics = _attr(result, "qft_dynamics")
    mapping = _attr(result, "mapping")
    model_kind = _attr(field_model, "model_kind")
    if model_kind is None and qft_model is not None:
        model_kind = "lattice_qed"
    if model_kind is None and cavity_model is not None:
        model_kind = "pauli_fierz_cavity_qed"
    if model_kind is None:
        return {
            "field_model_kind": None,
            "field_model_decision": {
                "available": False,
                "hardware_candidate": False,
                "hardware_skip_reason": "not_a_field_model_case",
            },
        }

    resource_estimate = dict(_attr(field_model, "resource_estimate", {}) or {})
    error_budget = dict(_attr(field_model, "error_budget", {}) or {})
    if model_kind == "lattice_qed":
        resource_estimate = resource_estimate or _lattice_resource_estimate(qft_model, mapping)
        error_budget = error_budget or _lattice_error_budget(qft_model, qft_dynamics)
    if model_kind == "pauli_fierz_cavity_qed" and cavity_model is not None:
        resource_estimate = resource_estimate or dict(_attr(cavity_model, "resource_estimate", {}) or {})
        error_budget = error_budget or dict(_attr(cavity_model, "error_budget", {}) or {})

    runtime_preview = _runtime_preview_from_submission(_attr(result, "runtime_submission"))
    dynamics_preview = _runtime_preview_from_dynamics(qft_dynamics if isinstance(qft_dynamics, dict) else None)
    if dynamics_preview["available"]:
        runtime_preview = {**runtime_preview, **dynamics_preview}

    metrics: dict[str, Any] = {
        "field_model_kind": model_kind,
        "field_model.model_kind": model_kind,
        "field_model_registry": _attr(field_model, "registry_name"),
        "field_model_capability_tier": _attr(field_model, "capability_tier"),
        "field_model_observables": list(_attr(field_model, "observables", []) or []),
        "field_model_resource_estimate": resource_estimate,
        "field_model_error_budget": error_budget,
        "field_model_risk_notes": list(_attr(field_model, "risk_notes", []) or []),
        "local_exact_baseline_available": bool(_attr(_attr(result, "exact_baseline"), "available", False)),
        "benchmark_absolute_error": _attr(_attr(result, "benchmark"), "absolute_error"),
        "qubits": resource_estimate.get("total_qubits") or _attr(mapping, "num_qubits"),
        "pauli_terms": resource_estimate.get("pauli_terms") or _attr(mapping, "qubit_term_count"),
        "runtime_preview": runtime_preview,
        "runtime_preview_available": bool(runtime_preview.get("available")),
        "runtime_preview_submitted": bool(runtime_preview.get("submitted")),
        "hardware_verified": bool(_attr(result, "hardware_verified", False)),
    }

    if model_kind == "lattice_qed" and qft_model is not None:
        trotter = _trotter_metrics(qft_dynamics if isinstance(qft_dynamics, dict) else None)
        engine = dict(_attr(qft_model, "engine", {}) or {})
        constraints = dict(_attr(qft_model, "constraint_residuals", {}) or {})
        metrics.update(
            {
                "gauss_law_residual": constraints.get("reference_state_max_abs_gauss_law"),
                "max_hamiltonian_gauge_commutator_norm": constraints.get(
                    "max_hamiltonian_gauge_commutator_norm"
                ),
                "projected_dimension": engine.get("projected_dimension"),
                "physical_sector_dimension": (
                    dict(_attr(qft_model, "physical_sector", {}) or {}).get("basis_index_count")
                ),
                "engine_representation": engine.get("actual_representation"),
                "pauli_materialization": engine.get("pauli_materialization"),
                **trotter,
            }
        )
    elif model_kind == "pauli_fierz_cavity_qed":
        metrics.update(_cavity_observable_metrics(cavity_model))
        metrics["photon_cutoff_max_occupation"] = max(
            [int(mode.get("max_occupation", 0)) for mode in (_attr(cavity_model, "modes", []) or [])],
            default=None,
        )

    metrics["field_model_decision"] = build_field_model_decision_summary(metrics)
    return metrics


def build_field_model_decision_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    """Classify one field-model case for local trust and guarded hardware readiness."""
    model_kind = metrics.get("field_model_kind")
    if not model_kind:
        return {
            "available": False,
            "hardware_candidate": False,
            "hardware_skip_reason": "not_a_field_model_case",
        }
    reasons: list[str] = []
    local_exact_ok = bool(metrics.get("local_exact_baseline_available"))
    if not local_exact_ok:
        reasons.append("missing_local_exact_baseline")

    gauss_residual = _as_float(metrics.get("gauss_law_residual"))
    photon_leakage = _as_float(metrics.get("photon_physical_subspace_leakage"))
    if model_kind == "lattice_qed":
        if gauss_residual is None:
            reasons.append("missing_gauss_law_residual")
        elif gauss_residual > GAUSS_OR_LEAKAGE_TOLERANCE:
            reasons.append("gauss_law_residual_above_gate")
    if model_kind == "pauli_fierz_cavity_qed":
        if photon_leakage is None:
            reasons.append("missing_photon_leakage_metric")
        elif photon_leakage > GAUSS_OR_LEAKAGE_TOLERANCE:
            reasons.append("photon_leakage_above_gate")

    cutoff_delta = _as_float(metrics.get("photon_cutoff_delta_hartree"))
    cutoff_sensitive = cutoff_delta is not None and cutoff_delta > PHOTON_CUTOFF_DELTA_HARTREE_THRESHOLD
    if cutoff_sensitive:
        reasons.append("photon_cutoff_delta_above_gate")

    trotter_error = _as_float(metrics.get("max_trotter_observable_error"))
    trotter_limited = trotter_error is not None and trotter_error > TROTTER_MAX_OBSERVABLE_ERROR_THRESHOLD
    if trotter_limited:
        reasons.append("trotter_error_above_gate")

    vqe_error = _as_float(metrics.get("vqe_vs_exact_error"))
    ansatz_limited = vqe_error is not None and vqe_error > ANSATZ_VS_EXACT_HARTREE_THRESHOLD
    if ansatz_limited:
        reasons.append("ansatz_error_above_gate")

    qubits = _as_int(metrics.get("qubits"))
    if qubits is None or qubits > MAX_HARDWARE_QUBITS:
        reasons.append("qubit_count_above_hardware_gate")

    runtime_preview = metrics.get("runtime_preview") or {}
    if not bool(metrics.get("runtime_preview_available")):
        reasons.append("missing_runtime_preview_metadata")
    if bool(metrics.get("runtime_preview_submitted")):
        reasons.append("runtime_preview_already_submitted")

    depth = _as_float(
        runtime_preview.get("max_transpiled_depth")
        or runtime_preview.get("max_logical_depth")
        or metrics.get("trotter_max_depth")
    )
    if depth is not None and depth > MAX_HARDWARE_DEPTH:
        reasons.append("depth_above_hardware_gate")

    two_qubit = _as_float(
        runtime_preview.get("max_transpiled_two_qubit_gate_count")
        or metrics.get("trotter_max_two_qubit_gate_count")
    )
    if two_qubit is not None and two_qubit > MAX_HARDWARE_TWO_QUBIT_GATES:
        reasons.append("two_qubit_gate_count_above_hardware_gate")

    hardware_candidate = not reasons
    return {
        "available": True,
        "gate_version": FIELD_MODEL_GATE_VERSION,
        "local_exact_ok": local_exact_ok,
        "cutoff_sensitive": cutoff_sensitive,
        "trotter_limited": trotter_limited,
        "ansatz_limited": ansatz_limited,
        "hardware_candidate": hardware_candidate,
        "hardware_skip_reason": None if hardware_candidate else reasons[0],
        "hardware_skip_reasons": reasons,
        "thresholds": {
            "gauss_or_leakage_tolerance": GAUSS_OR_LEAKAGE_TOLERANCE,
            "photon_cutoff_delta_hartree": PHOTON_CUTOFF_DELTA_HARTREE_THRESHOLD,
            "trotter_max_observable_error": TROTTER_MAX_OBSERVABLE_ERROR_THRESHOLD,
            "ansatz_vs_exact_hartree": ANSATZ_VS_EXACT_HARTREE_THRESHOLD,
            "max_hardware_qubits": MAX_HARDWARE_QUBITS,
            "max_hardware_depth": MAX_HARDWARE_DEPTH,
            "max_hardware_two_qubit_gates": MAX_HARDWARE_TWO_QUBIT_GATES,
        },
    }


def apply_field_model_cross_case_decisions(case_results: list[Any]) -> None:
    """Attach cutoff deltas and refresh decisions after all cases in a suite ran."""
    cavity_cases = [
        case
        for case in case_results
        if (case.metrics or {}).get("field_model_kind") == "pauli_fierz_cavity_qed"
        and case.total_energy is not None
        and (case.metrics or {}).get("photon_cutoff_max_occupation") is not None
    ]
    by_cutoff: dict[int, Any] = {}
    for case in cavity_cases:
        cutoff = int(case.metrics["photon_cutoff_max_occupation"])
        if cutoff not in by_cutoff:
            by_cutoff[cutoff] = case
    if 1 in by_cutoff and 2 in by_cutoff:
        delta = abs(float(by_cutoff[2].total_energy) - float(by_cutoff[1].total_energy))
        for case in (by_cutoff[1], by_cutoff[2]):
            case.metrics["photon_cutoff_delta_hartree"] = float(delta)
            case.metrics["field_model_decision"] = build_field_model_decision_summary(case.metrics)
            notes = list(case.notes)
            notes.append(
                "Photon cutoff delta compares finite-cutoff H2 Pauli-Fierz exact cases with max_occupation=1 and 2."
            )
            case.notes = notes


def build_field_model_campaign_summary(case_results: list[Any]) -> dict[str, Any]:
    """Summarize field-model benchmark cases by family and gate outcome."""
    field_cases = [case for case in case_results if (case.metrics or {}).get("field_model_kind")]
    by_model: dict[str, dict[str, Any]] = {}
    hardware_candidates: list[str] = []
    cutoff_sensitive_cases: list[str] = []
    trotter_limited_cases: list[str] = []
    ansatz_limited_cases: list[str] = []
    for case in field_cases:
        metrics = case.metrics or {}
        model_kind = str(metrics.get("field_model_kind"))
        bucket = by_model.setdefault(
            model_kind,
            {
                "case_count": 0,
                "cases": [],
                "hardware_candidates": [],
            },
        )
        decision = metrics.get("field_model_decision") or {}
        bucket["case_count"] += 1
        bucket["cases"].append(case.name)
        if decision.get("hardware_candidate"):
            bucket["hardware_candidates"].append(case.name)
            hardware_candidates.append(case.name)
        if decision.get("cutoff_sensitive"):
            cutoff_sensitive_cases.append(case.name)
        if decision.get("trotter_limited"):
            trotter_limited_cases.append(case.name)
        if decision.get("ansatz_limited"):
            ansatz_limited_cases.append(case.name)

    trotter_candidates = []
    for case in field_cases:
        metrics = case.metrics or {}
        step = _as_float(metrics.get("trotter_step"))
        error = _as_float(metrics.get("max_trotter_observable_error"))
        if step is not None and error is not None and error <= TROTTER_MAX_OBSERVABLE_ERROR_THRESHOLD:
            trotter_candidates.append(
                {
                    "case": case.name,
                    "trotter_step": step,
                    "max_trotter_observable_error": error,
                    "operation_count": metrics.get("trotter_max_operation_count"),
                }
            )
    recommended_trotter = None
    if trotter_candidates:
        recommended_trotter = max(
            trotter_candidates,
            key=lambda item: (float(item["trotter_step"]), -float(item.get("operation_count") or 0.0)),
        )

    return {
        "schema_version": FIELD_MODEL_GATE_VERSION,
        "case_count": len(field_cases),
        "by_model": by_model,
        "hardware_candidates": hardware_candidates,
        "cutoff_sensitive_cases": cutoff_sensitive_cases,
        "trotter_limited_cases": trotter_limited_cases,
        "ansatz_limited_cases": ansatz_limited_cases,
        "recommended_trotter_step": recommended_trotter,
        "hardware_gate_note": (
            "Real quantum hardware is not submitted by this local campaign; candidates only mean "
            "a preview passed local exact/cutoff/leakage/resource gates."
        ),
    }
