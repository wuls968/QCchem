"""Real runtime submission attempts with graceful failure boundaries."""

from __future__ import annotations

from time import perf_counter
from typing import Any

import numpy as np
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qcchem.core import BackendSpec, RuntimeSubmissionSummary


def attempt_runtime_submission(
    *,
    spec: BackendSpec,
    circuit,
    operator,
    parameter_values: list[float] | np.ndarray,
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

    try:
        import qiskit_ibm_runtime
        from qiskit_ibm_runtime import QiskitRuntimeService
    except Exception as exc:
        summary.failure_category = "missing_dependency"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.result_provenance = {"attempt_stage": "import_runtime_package"}
        return summary

    try:
        service = QiskitRuntimeService()
    except Exception as exc:
        summary.failure_category = "account_not_found" if type(exc).__name__ == "AccountNotFoundError" else "service_initialization_failed"
        summary.failure_message = f"{type(exc).__name__}: {exc}"
        summary.submission_wall_time_seconds = float(perf_counter() - started)
        summary.result_provenance = {
            "attempt_stage": "initialize_service",
            "runtime_package_version": getattr(qiskit_ibm_runtime, "__version__", "unknown"),
        }
        return summary

    summary.provider = type(service).__name__
    backend_name = spec.runtime.options.get("backend_name")
    if backend_name is None:
        try:
            backends = service.backends(operational=True, simulator=False)
            if backends:
                first_backend = backends[0]
                backend_name = getattr(first_backend, "name", None)
                if callable(backend_name):
                    backend_name = backend_name()
            else:
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
    precision_target = spec.runtime.precision_target
    if precision_target is None:
        precision_target = float(spec.runtime.options.get("precision_target", 0.1))
    estimator_options = {
        "resilience_level": spec.runtime.resilience_level or 0,
    }
    try:
        pass_manager = generate_preset_pass_manager(
            backend=backend,
            optimization_level=optimization_level,
        )
        isa_circuit = pass_manager.run(circuit)
        isa_operator = operator.apply_layout(isa_circuit.layout)
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
        job = estimator.run(pubs, precision=precision_target)
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
            summary.result_provenance["attempt_stage"] = "result_retrieved"
        else:
            summary.result_provenance["attempt_stage"] = "submitted"
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
