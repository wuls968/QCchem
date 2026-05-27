"""Real runtime submission attempts with graceful failure boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import numpy as np
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qcchem.backends.layout import recommend_initial_layout
from qcchem.core import BackendSpec, RuntimeSubmissionSummary


def _deep_merge_options(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_options(merged[key], value)
        else:
            merged[key] = value
    return merged


def _runtime_backend_name(backend: Any) -> str | None:
    name = getattr(backend, "name", None)
    if callable(name):
        name = name()
    return str(name) if name is not None else None


def _backend_pending_jobs(backend: Any) -> int:
    try:
        status = backend.status()
    except Exception:
        return 0
    pending = getattr(status, "pending_jobs", 0)
    try:
        return int(pending)
    except Exception:
        return 0


def _runtime_service_kwargs(spec: BackendSpec) -> dict[str, Any]:
    """Map QCchem runtime service labels onto current qiskit-ibm-runtime kwargs."""
    options = spec.runtime.options
    raw_channel = options.get("channel") or spec.runtime.service
    raw_channel_key = str(raw_channel).strip().lower()
    if (
        raw_channel_key == "ibm_quantum_platform"
        and options.get("token") is None
        and options.get("account_name") is None
    ):
        legacy_kwargs = _legacy_platform_account_kwargs()
        if legacy_kwargs:
            return legacy_kwargs
    channel_aliases = {
        "ibm_quantum_platform": "ibm_quantum",
        "ibm_quantum": "ibm_quantum",
        "ibm_cloud": "ibm_cloud",
        "local": "local",
    }
    channel = channel_aliases.get(raw_channel_key)
    kwargs: dict[str, Any] = {}
    if channel is not None:
        kwargs["channel"] = channel
    option_map = {
        "token": "token",
        "url": "url",
        "account_name": "name",
        "instance": "instance",
    }
    for option_key, service_key in option_map.items():
        value = options.get(option_key)
        if value is not None:
            kwargs[service_key] = value
    return kwargs


def _legacy_platform_account_kwargs() -> dict[str, Any]:
    """Load old ibm_quantum_platform account records for qiskit-ibm-runtime 0.36."""
    path = Path.home() / ".qiskit" / "qiskit-ibm.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    candidates = [
        account
        for account in payload.values()
        if isinstance(account, dict)
        and str(account.get("channel", "")).strip().lower() == "ibm_quantum_platform"
    ]
    if not candidates:
        return {}
    candidates.sort(key=lambda account: not bool(account.get("is_default_account", False)))
    account = candidates[0]
    token = account.get("token")
    if not token:
        return {}
    url = str(account.get("url") or "")
    channel = "ibm_cloud" if "cloud.ibm.com" in url else "ibm_quantum"
    kwargs: dict[str, Any] = {"channel": channel, "token": token}
    for key in ("url", "instance", "private_endpoint"):
        value = account.get(key)
        if value is not None:
            kwargs[key] = value
    return kwargs


def _select_runtime_backend_name(
    service: Any,
    *,
    num_qubits: int,
    layout_strategy: str | None,
) -> tuple[str | None, dict[str, Any]]:
    """Select the best available backend for a small chemistry workload."""
    backends = service.backends(operational=True, simulator=False)
    candidates: list[tuple[float, int, str, dict[str, Any]]] = []
    for backend in backends:
        backend_name = _runtime_backend_name(backend)
        if backend_name is None:
            continue
        score = 1.0e9
        layout_payload: dict[str, Any] = {}
        if layout_strategy:
            try:
                layout_plan = recommend_initial_layout(
                    backend,
                    int(num_qubits),
                    strategy=str(layout_strategy),
                )
            except Exception:
                layout_plan = None
            if layout_plan is not None:
                score = float(layout_plan.score)
                layout_payload = {
                    "selected_layout": list(layout_plan.selected_layout),
                    "layout_score": float(layout_plan.score),
                    "readout_score": float(layout_plan.readout_score),
                    "entangling_score": float(layout_plan.entangling_score),
                }
        pending_jobs = _backend_pending_jobs(backend)
        candidates.append(
            (
                score,
                pending_jobs,
                backend_name,
                {
                    "backend_name": backend_name,
                    "layout_score": score,
                    "pending_jobs": pending_jobs,
                    **layout_payload,
                },
            )
        )
    if not candidates:
        return None, {"backend_selection_strategy": layout_strategy or "first_available", "candidates": []}
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    selected = candidates[0]
    return selected[2], {
        "backend_selection_strategy": layout_strategy or "first_available",
        "selected_backend": selected[2],
        "candidates": [item[3] for item in candidates],
    }


def attempt_runtime_submission(
    *,
    spec: BackendSpec,
    circuit,
    operator,
    parameter_values: list[float] | np.ndarray,
    submission_callback: Callable[[RuntimeSubmissionSummary], None] | None = None,
) -> RuntimeSubmissionSummary | None:
    """Attempt a real IBM Runtime submission when the runtime path is requested."""
    if not spec.runtime.enabled:
        return None

    mode = "job"
    if spec.runtime.batch_ready:
        mode = "batch"
    elif spec.runtime.session_ready:
        mode = "session"

    summary = RuntimeSubmissionSummary(
        attempted=True,
        submitted=False,
        succeeded=False,
        service=spec.runtime.service,
        mode=mode,
        session_requested=bool(spec.runtime.session_ready),
        batch_requested=bool(spec.runtime.batch_ready),
        options_snapshot={
            "precision_target": spec.runtime.precision_target,
            "max_budgeted_shots": spec.runtime.max_budgeted_shots,
            "max_execution_seconds": spec.runtime.max_execution_seconds,
            "budget_strategy": spec.runtime.calibration_strategy,
            "resilience_level": spec.runtime.resilience_level,
            "grouping_policy": spec.runtime.grouping_policy,
            **dict(spec.runtime.options),
        },
        verification_status="exploratory",
    )
    started = perf_counter()

    if not bool(spec.runtime.options.get("submit_real_job", False)):
        summary.failure_category = "runtime_submission_disabled"
        summary.failure_message = (
            "Runtime submission is configured for preview only; no remote IBM job was requested."
        )
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance = {
            "attempt_stage": "submission_disabled_before_service_init",
            "real_submission_requested": False,
        }
        return summary
    confirmation = spec.runtime.options.get("runtime_budget_confirmation")
    if confirmation != "I understand IBM Runtime budget":
        summary.failure_category = "runtime_budget_confirmation_missing"
        summary.failure_message = (
            "Real Runtime submission requires --confirm-runtime-budget "
            "'I understand IBM Runtime budget'."
        )
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance = {
            "attempt_stage": "confirmation_gate",
            "real_submission_requested": True,
        }
        return summary

    try:
        import qiskit_ibm_runtime
        from qiskit_ibm_runtime import QiskitRuntimeService
    except Exception as exc:
        summary.failure_category = "missing_dependency"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.result_provenance = {"attempt_stage": "import_runtime_package"}
        return summary

    try:
        service_kwargs = _runtime_service_kwargs(spec)
        service = QiskitRuntimeService(**service_kwargs)
    except Exception as exc:
        summary.failure_category = "account_not_found" if type(exc).__name__ == "AccountNotFoundError" else "service_initialization_failed"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance = {
            "attempt_stage": "initialize_service",
            "runtime_package_version": getattr(qiskit_ibm_runtime, "__version__", "unknown"),
            "service_kwargs": {key: ("***" if key == "token" else value) for key, value in service_kwargs.items()},
        }
        return summary

    summary.provider = type(service).__name__
    backend_name = spec.runtime.options.get("backend_name")
    layout_strategy = spec.runtime.options.get("layout_strategy")
    backend_selection_metadata: dict[str, Any] = {
        "backend_selection_strategy": "pinned_backend" if backend_name is not None else (layout_strategy or "first_available"),
    }
    if backend_name is None:
        try:
            backend_name, backend_selection_metadata = _select_runtime_backend_name(
                service,
                num_qubits=int(getattr(circuit, "num_qubits", 0)),
                layout_strategy=(str(layout_strategy) if layout_strategy is not None else None),
            )
            if backend_name is None:
                summary.failure_category = "no_runtime_backend_available"
                summary.failure_message = "Runtime service returned no operational non-simulator backends."
                summary.submission_wall_time_seconds = float(perf_counter() - started)
                summary.result_provenance = {"attempt_stage": "discover_backend"}
                return summary
        except Exception as exc:
            summary.failure_category = "backend_discovery_failed"
            summary.failure_message = f"{type(exc).__name__}: {exc}"
            summary.submission_wall_time_seconds = float(perf_counter() - started)
            summary.result_provenance = {"attempt_stage": "discover_backend"}
            return summary

    summary.backend_name = str(backend_name) if backend_name is not None else None
    summary.result_provenance = {
        "attempt_stage": "ready_to_submit",
        "runtime_package_version": getattr(__import__("qiskit_ibm_runtime"), "__version__", "unknown"),
        "backend_name": summary.backend_name,
        "parameter_count": int(len(parameter_values)),
        "operator_qubits": int(getattr(operator, "num_qubits", 0)),
        "circuit_qubits": int(getattr(circuit, "num_qubits", 0)),
        **backend_selection_metadata,
    }

    try:
        from qiskit_ibm_runtime import Batch, EstimatorV2, Session
    except Exception as exc:
        summary.failure_category = "runtime_submission_dependency_error"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance["attempt_stage"] = "import_submission_primitives"
        return summary

    try:
        backend = service.backend(summary.backend_name)
    except Exception as exc:
        summary.failure_category = "backend_lookup_failed"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance["attempt_stage"] = "load_backend"
        return summary

    optimization_level = int(spec.runtime.options.get("optimization_level", 1))
    layout_method = spec.runtime.options.get("layout_method")
    routing_method = spec.runtime.options.get("routing_method")
    approximation_degree = float(spec.runtime.options.get("approximation_degree", 1.0))
    seed_transpiler = spec.runtime.options.get("seed_transpiler", spec.seed)
    seed_transpiler = int(seed_transpiler) if seed_transpiler is not None else None
    explicit_initial_layout = spec.runtime.options.get("initial_layout")
    selected_layout: list[int] | None = None
    if isinstance(explicit_initial_layout, (list, tuple)):
        selected_layout = [int(item) for item in explicit_initial_layout]
    elif layout_strategy:
        layout_plan = recommend_initial_layout(
            backend,
            int(getattr(circuit, "num_qubits", 0)),
            strategy=str(layout_strategy),
        )
        if layout_plan is not None:
            summary.layout_strategy = layout_plan.strategy
            summary.selected_layout = list(layout_plan.selected_layout)
            summary.layout_score = float(layout_plan.score)
            selected_layout = list(layout_plan.selected_layout)
    summary.transpilation_options = {
        "optimization_level": optimization_level,
        "layout_method": (str(layout_method) if layout_method is not None else None),
        "routing_method": (str(routing_method) if routing_method is not None else None),
        "approximation_degree": approximation_degree,
        "seed_transpiler": seed_transpiler,
    }
    if layout_strategy and summary.layout_strategy is None:
        summary.layout_strategy = str(layout_strategy)
    if selected_layout is not None:
        summary.selected_layout = list(selected_layout)
        summary.transpilation_options["initial_layout"] = list(selected_layout)
    summary.result_provenance["layout_strategy"] = summary.layout_strategy
    precision_target = spec.runtime.precision_target
    if precision_target is None:
        precision_option = spec.runtime.options.get("precision_target")
        precision_target = float(precision_option) if precision_option is not None else None
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
        prepared_circuit = circuit
        if getattr(circuit, "num_parameters", 0):
            parameters = list(circuit.parameters)
            values = np.asarray(parameter_values, dtype=float).reshape(-1)
            if len(parameters) != len(values):
                raise ValueError(
                    "Runtime submission parameter count does not match the ansatz circuit."
                )
            prepared_circuit = circuit.assign_parameters(
                {parameter: float(value) for parameter, value in zip(parameters, values)},
                inplace=False,
            )
        pass_manager = generate_preset_pass_manager(
            backend=backend,
            optimization_level=optimization_level,
            initial_layout=selected_layout,
            layout_method=(str(layout_method) if layout_method is not None else None),
            routing_method=(str(routing_method) if routing_method is not None else None),
            approximation_degree=approximation_degree,
            seed_transpiler=seed_transpiler,
        )
        isa_circuit = pass_manager.run(prepared_circuit)
        isa_operator = operator.apply_layout(isa_circuit.layout)
        counts = isa_circuit.count_ops()
        summary.transpiled_depth = int(isa_circuit.depth()) if isa_circuit.depth() is not None else None
        summary.transpiled_two_qubit_gate_count = int(
            sum(int(counts.get(name, 0)) for name in ("cz", "ecr", "cx"))
        )
        pubs = []
        if getattr(isa_circuit, "num_parameters", 0):
            pubs.append((isa_circuit, isa_operator, [np.asarray(parameter_values, dtype=float)]))
        else:
            pubs.append((isa_circuit, isa_operator))
    except Exception as exc:
        summary.failure_category = "isa_preparation_failed"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance["attempt_stage"] = "prepare_isa_payload"
        return summary

    actual_mode = "backend"
    context = None
    try:
        if bool(spec.runtime.options.get("use_batch", False)) and spec.runtime.batch_ready:
            context = Batch(backend=backend)
            actual_mode = "batch"
        elif bool(spec.runtime.options.get("use_session", False)) and spec.runtime.session_ready:
            context = Session(backend=backend)
            actual_mode = "session"

        if context is not None:
            estimator = EstimatorV2(mode=context, options=estimator_options)
        else:
            estimator = EstimatorV2(mode=backend, options=estimator_options)
        run_kwargs: dict[str, Any] = {}
        if default_shots is None and precision_target is not None:
            run_kwargs["precision"] = float(precision_target)
        job = estimator.run(pubs, **run_kwargs)
        summary.submitted = True
        summary.job_id = job.job_id()
        summary.mode = actual_mode
        summary.backend_name = getattr(backend, "name", summary.backend_name)
        if callable(summary.backend_name):
            summary.backend_name = summary.backend_name()
        if context is not None:
            summary.session_id = getattr(context, "session_id", None)
            if callable(summary.session_id):
                summary.session_id = summary.session_id()
        if actual_mode == "batch":
            summary.batch_id = summary.session_id
        summary.result_provenance["attempt_stage"] = "submitted"
        if submission_callback is not None:
            try:
                submission_callback(summary)
            except Exception as exc:
                summary.result_provenance["submission_callback_error"] = f"{type(exc).__name__}: {exc}"
        wait_for_result = bool(spec.runtime.options.get("wait_for_result", False))
        if wait_for_result:
            runtime_result = job.result()
            pub_result = runtime_result[0]
            summary.succeeded = True
            summary.returned_job_metadata = {
                "evs": np.asarray(pub_result.data.evs).tolist(),
                "stds": np.asarray(pub_result.data.stds).tolist(),
                "metadata": dict(pub_result.metadata),
            }
            try:
                usage_estimation = job.usage_estimation
                if usage_estimation is not None:
                    summary.usage_estimation = dict(usage_estimation)
            except Exception:
                pass
            try:
                metrics = job.metrics()
                if metrics is not None:
                    summary.job_metrics = dict(metrics)
            except Exception:
                pass
            summary.result_provenance["attempt_stage"] = "result_retrieved"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        return summary
    except Exception as exc:
        summary.failure_category = "job_submission_failed" if not summary.submitted else "job_result_failed"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance["attempt_stage"] = "submit_or_wait"
        return summary
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
