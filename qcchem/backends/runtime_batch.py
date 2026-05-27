"""Guarded runtime batch submission for exploratory QFT dynamics."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Callable

import numpy as np
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qcchem.backends.runtime_submission import (
    _deep_merge_options,
    _runtime_service_kwargs,
    _select_runtime_backend_name,
)
from qcchem.core import BackendSpec


def _pub_preview(pub: dict[str, Any], index: int) -> dict[str, Any]:
    circuit = pub.get("circuit")
    operator = pub.get("operator")
    return {
        "pub_index": int(index),
        "time": pub.get("time"),
        "observable": pub.get("observable"),
        "circuit_qubits": int(getattr(circuit, "num_qubits", 0)),
        "circuit_depth": int(circuit.depth()) if circuit is not None and circuit.depth() is not None else None,
        "operator_qubits": int(getattr(operator, "num_qubits", 0)),
        "parameter_count": int(len(pub.get("parameter_values", []) or [])),
        "reference_value": pub.get("reference_value"),
    }


def attempt_runtime_batch_submission(
    *,
    spec: BackendSpec,
    pubs: list[dict[str, Any]],
    observable_policy: str = "aggregate_gauge",
    runtime_limits: dict[str, Any] | None = None,
    submission_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Attempt a guarded IBM Runtime Estimator batch for many QFT dynamics pubs."""
    mode = "job"
    if spec.runtime.batch_ready:
        mode = "batch"
    elif spec.runtime.session_ready:
        mode = "session"
    started = perf_counter()
    summary: dict[str, Any] = {
        "attempted": bool(spec.runtime.enabled),
        "submitted": False,
        "succeeded": False,
        "service": spec.runtime.service,
        "mode": mode,
        "observable_policy": observable_policy,
        "pub_count": int(len(pubs)),
        "pubs_preview": [_pub_preview(pub, index) for index, pub in enumerate(pubs)],
        "transpiled_pub_resources": [],
        "returned_job_metadata": {},
        "failure_category": None,
        "failure_message": None,
        "verification_status": "exploratory",
        "options_snapshot": {
            "precision_target": spec.runtime.precision_target,
            "max_budgeted_shots": spec.runtime.max_budgeted_shots,
            "max_execution_seconds": spec.runtime.max_execution_seconds,
            "budget_strategy": spec.runtime.calibration_strategy,
            "resilience_level": spec.runtime.resilience_level,
            "grouping_policy": spec.runtime.grouping_policy,
            **dict(spec.runtime.options),
        },
        "result_provenance": {
            "attempt_stage": "initialized",
            "pub_count": int(len(pubs)),
            "observable_policy": observable_policy,
        },
    }
    limits = runtime_limits or {}
    if limits:
        summary["runtime_limits"] = dict(limits)
    if not spec.runtime.enabled:
        summary["failure_category"] = "runtime_disabled"
        summary["failure_message"] = "Backend runtime is disabled; no batch submission was attempted."
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary
    max_pub_count = limits.get("max_pub_count")
    if max_pub_count is not None and len(pubs) > int(max_pub_count):
        summary["failure_category"] = "runtime_budget_exceeded"
        summary["failure_message"] = (
            f"Runtime batch pub_count={len(pubs)} exceeds max_pub_count={int(max_pub_count)}."
        )
        summary["result_provenance"]["attempt_stage"] = "budget_gate"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary
    default_shots_limit = spec.runtime.options.get("default_shots")
    if default_shots_limit is None and spec.runtime.max_budgeted_shots is not None:
        default_shots_limit = spec.runtime.max_budgeted_shots
    max_total_pub_shots = limits.get("max_total_pub_shots")
    if max_total_pub_shots is not None and default_shots_limit is not None:
        total_pub_shots = int(len(pubs)) * int(default_shots_limit)
        if total_pub_shots > int(max_total_pub_shots):
            summary["failure_category"] = "runtime_budget_exceeded"
            summary["failure_message"] = (
                f"Runtime batch pub_shots={total_pub_shots} exceeds "
                f"max_total_pub_shots={int(max_total_pub_shots)}."
            )
            summary["result_provenance"]["attempt_stage"] = "budget_gate"
            summary["result_provenance"]["estimated_total_pub_shots"] = total_pub_shots
            summary["submission_wall_time_seconds"] = float(perf_counter() - started)
            return summary
    max_logical_depth = limits.get("max_logical_depth")
    if max_logical_depth is not None:
        depths = [
            item.get("circuit_depth")
            for item in summary["pubs_preview"]
            if isinstance(item, dict) and item.get("circuit_depth") is not None
        ]
        max_depth = max(depths, default=0)
        if int(max_depth) > int(max_logical_depth):
            summary["failure_category"] = "runtime_budget_exceeded"
            summary["failure_message"] = (
                f"Runtime batch max_logical_depth={int(max_depth)} exceeds "
                f"max_logical_depth={int(max_logical_depth)}."
            )
            summary["result_provenance"]["attempt_stage"] = "budget_gate"
            summary["submission_wall_time_seconds"] = float(perf_counter() - started)
            return summary
    if not bool(spec.runtime.options.get("submit_real_job", False)):
        summary["failure_category"] = "runtime_submission_disabled"
        summary["failure_message"] = (
            "Runtime batch is configured for preview only; no remote IBM job was requested."
        )
        summary["result_provenance"]["attempt_stage"] = "submission_disabled_before_service_init"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary
    confirmation = spec.runtime.options.get("runtime_budget_confirmation")
    if confirmation != "I understand IBM Runtime budget":
        summary["failure_category"] = "runtime_budget_confirmation_missing"
        summary["failure_message"] = (
            "Real Runtime batch submission requires --confirm-runtime-budget "
            "'I understand IBM Runtime budget'."
        )
        summary["result_provenance"]["attempt_stage"] = "confirmation_gate"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary

    try:
        import qiskit_ibm_runtime
        from qiskit_ibm_runtime import QiskitRuntimeService
    except Exception as exc:
        summary["failure_category"] = "missing_dependency"
        summary["failure_message"] = f"{type(exc).__name__}: {exc}"
        summary["result_provenance"]["attempt_stage"] = "import_runtime_package"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary

    try:
        service_kwargs = _runtime_service_kwargs(spec)
        service = QiskitRuntimeService(**service_kwargs)
    except Exception as exc:
        summary["failure_category"] = (
            "account_not_found" if type(exc).__name__ == "AccountNotFoundError" else "service_initialization_failed"
        )
        summary["failure_message"] = f"{type(exc).__name__}: {exc}"
        summary["result_provenance"]["attempt_stage"] = "initialize_service"
        summary["result_provenance"]["runtime_package_version"] = getattr(
            qiskit_ibm_runtime, "__version__", "unknown"
        )
        summary["result_provenance"]["service_kwargs"] = {
            key: ("***" if key == "token" else value)
            for key, value in service_kwargs.items()
        }
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary

    backend_name = spec.runtime.options.get("backend_name")
    layout_strategy = spec.runtime.options.get("layout_strategy")
    backend_selection_metadata: dict[str, Any] = {
        "backend_selection_strategy": "pinned_backend" if backend_name is not None else (layout_strategy or "first_available"),
    }
    if backend_name is None:
        try:
            first_circuit = pubs[0].get("circuit") if pubs else None
            backend_name, backend_selection_metadata = _select_runtime_backend_name(
                service,
                num_qubits=int(getattr(first_circuit, "num_qubits", 0)),
                layout_strategy=(str(layout_strategy) if layout_strategy is not None else None),
            )
        except Exception as exc:
            summary["failure_category"] = "backend_discovery_failed"
            summary["failure_message"] = f"{type(exc).__name__}: {exc}"
            summary["result_provenance"]["attempt_stage"] = "discover_backend"
            summary["submission_wall_time_seconds"] = float(perf_counter() - started)
            return summary
    if backend_name is None:
        summary["failure_category"] = "no_runtime_backend_available"
        summary["failure_message"] = "Runtime service returned no operational non-simulator backends."
        summary["result_provenance"]["attempt_stage"] = "discover_backend"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary
    summary["backend_name"] = str(backend_name)
    summary["result_provenance"].update(backend_selection_metadata)

    try:
        from qiskit_ibm_runtime import Batch, EstimatorV2, Session
        backend = service.backend(str(backend_name))
    except Exception as exc:
        summary["failure_category"] = "runtime_submission_dependency_error"
        summary["failure_message"] = f"{type(exc).__name__}: {exc}"
        summary["result_provenance"]["attempt_stage"] = "load_submission_dependencies"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary

    optimization_level = int(spec.runtime.options.get("optimization_level", 1))
    precision_target = spec.runtime.precision_target
    if precision_target is None and spec.runtime.options.get("precision_target") is not None:
        precision_target = float(spec.runtime.options["precision_target"])
    default_shots = spec.runtime.options.get("default_shots")
    if default_shots is None and spec.runtime.max_budgeted_shots is not None:
        default_shots = spec.runtime.max_budgeted_shots
    estimator_options: dict[str, Any] = {
        "resilience_level": spec.runtime.resilience_level or 0,
    }
    if default_shots is not None:
        estimator_options["default_shots"] = int(default_shots)
    elif precision_target is not None:
        estimator_options["default_precision"] = float(precision_target)
    if spec.seed is not None:
        estimator_options["seed_estimator"] = int(spec.seed)
    custom_estimator_options = spec.runtime.options.get("estimator_options")
    if isinstance(custom_estimator_options, dict):
        estimator_options = _deep_merge_options(estimator_options, custom_estimator_options)

    try:
        pass_manager = generate_preset_pass_manager(
            backend=backend,
            optimization_level=optimization_level,
            seed_transpiler=spec.seed,
        )
        isa_pubs = []
        resources = []
        for index, pub in enumerate(pubs):
            circuit = pub["circuit"]
            operator = pub["operator"]
            parameter_values = np.asarray(pub.get("parameter_values", []), dtype=float)
            isa_circuit = pass_manager.run(circuit)
            isa_operator = operator.apply_layout(isa_circuit.layout)
            counts = isa_circuit.count_ops()
            resources.append(
                {
                    "pub_index": int(index),
                    "time": pub.get("time"),
                    "observable": pub.get("observable"),
                    "transpiled_depth": int(isa_circuit.depth()) if isa_circuit.depth() is not None else None,
                    "transpiled_two_qubit_gate_count": int(
                        sum(int(counts.get(name, 0)) for name in ("cz", "ecr", "cx"))
                    ),
                }
            )
            if getattr(isa_circuit, "num_parameters", 0):
                isa_pubs.append((isa_circuit, isa_operator, [parameter_values]))
            else:
                isa_pubs.append((isa_circuit, isa_operator))
        summary["transpiled_pub_resources"] = resources
        summary["result_provenance"]["attempt_stage"] = "prepared_isa_batch"
    except Exception as exc:
        summary["failure_category"] = "isa_preparation_failed"
        summary["failure_message"] = f"{type(exc).__name__}: {exc}"
        summary["result_provenance"]["attempt_stage"] = "prepare_isa_batch"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary

    context = None
    actual_mode = "backend"
    try:
        if bool(spec.runtime.options.get("use_batch", False)) and spec.runtime.batch_ready:
            context = Batch(backend=backend)
            actual_mode = "batch"
        elif bool(spec.runtime.options.get("use_session", False)) and spec.runtime.session_ready:
            context = Session(backend=backend)
            actual_mode = "session"
        estimator = EstimatorV2(mode=(context if context is not None else backend), options=estimator_options)
        run_kwargs: dict[str, Any] = {}
        if default_shots is None and precision_target is not None:
            run_kwargs["precision"] = float(precision_target)
        job = estimator.run(isa_pubs, **run_kwargs)
        summary["submitted"] = True
        summary["mode"] = actual_mode
        summary["job_id"] = job.job_id()
        if context is not None:
            session_id = getattr(context, "session_id", None)
            summary["session_id"] = session_id() if callable(session_id) else session_id
        if actual_mode == "batch":
            summary["batch_id"] = summary.get("session_id")
        summary["result_provenance"]["attempt_stage"] = "submitted"
        if submission_callback is not None:
            submission_callback(dict(summary))
        if bool(spec.runtime.options.get("wait_for_result", False)):
            runtime_result = job.result()
            summary["succeeded"] = True
            pub_results = []
            for pub, item in zip(pubs, runtime_result):
                evs = np.asarray(item.data.evs).tolist()
                stds = np.asarray(item.data.stds).tolist()
                reference_value = pub.get("reference_value")
                residual = None
                try:
                    residual = float(np.asarray(item.data.evs).reshape(-1)[0]) - float(reference_value)
                except Exception:
                    residual = None
                pub_results.append(
                    {
                        "time": pub.get("time"),
                        "observable": pub.get("observable"),
                        "evs": evs,
                        "stds": stds,
                        "reference_value": reference_value,
                        "runtime_minus_exact_residual": residual,
                        "metadata": dict(item.metadata),
                    }
                )
            summary["returned_job_metadata"] = {
                "evs": [np.asarray(item.data.evs).tolist() for item in runtime_result],
                "stds": [np.asarray(item.data.stds).tolist() for item in runtime_result],
                "metadata": [dict(item.metadata) for item in runtime_result],
                "pub_results": pub_results,
            }
            summary["result_provenance"]["attempt_stage"] = "result_retrieved"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary
    except Exception as exc:
        summary["failure_category"] = "job_submission_failed" if not summary["submitted"] else "job_result_failed"
        summary["failure_message"] = f"{type(exc).__name__}: {exc}"
        summary["result_provenance"]["attempt_stage"] = "submit_or_wait"
        summary["submission_wall_time_seconds"] = float(perf_counter() - started)
        return summary
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
