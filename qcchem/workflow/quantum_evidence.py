"""Quantum evidence sidecar construction for run artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector

from qcchem.core import QuantumEvidenceSummary
from qcchem.io.serialization import to_primitive


SCHEMA = "qcchem.quantum_evidence.v1"
MAX_DOMINANT_CONFIGURATIONS = 16
MAX_COUNTS_GROUPS = 64
MAX_COUNTS_QUBITS = 16
DEFAULT_COUNTS_SHOTS = 4096


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _coerce_real(value: complex | float | int) -> float:
    return float(np.real(value))


def _qft_payload(qft_model: Any | None) -> dict[str, Any]:
    payload = to_primitive(qft_model) if qft_model is not None else {}
    return payload if isinstance(payload, dict) else {}


def _pauli_materialization_skipped(qft_payload: dict[str, Any]) -> bool:
    engine = qft_payload.get("engine") if isinstance(qft_payload.get("engine"), dict) else {}
    return str(engine.get("pauli_materialization") or "").strip().lower() == "skipped"


def _qft_projected_metadata(qft_payload: dict[str, Any]) -> dict[str, Any]:
    engine = qft_payload.get("engine") if isinstance(qft_payload.get("engine"), dict) else {}
    physical = (
        qft_payload.get("physical_sector")
        if isinstance(qft_payload.get("physical_sector"), dict)
        else {}
    )
    validation = (
        qft_payload.get("sparse_exact_validation")
        if isinstance(qft_payload.get("sparse_exact_validation"), dict)
        else {}
    )
    return {
        "projected_matrix_dimension": validation.get("projected_matrix_dimension")
        or engine.get("projected_dimension"),
        "projected_hamiltonian_nnz": validation.get("projected_hamiltonian_nnz")
        or engine.get("projected_hamiltonian_nnz"),
        "physical_sector_dimension": validation.get("physical_sector_dimension")
        or physical.get("physical_sector_dimension")
        or physical.get("basis_index_count"),
        "basis_hash": validation.get("basis_hash") or physical.get("basis_hash"),
        "projected_matrix_sha256": validation.get("projected_matrix_sha256"),
        "qft_engine_build_mode": engine.get("build_mode"),
        "qft_engine_actual_representation": engine.get("actual_representation"),
    }


def _measurement_plan_payload(measurement: Any | None, *, pauli_skipped: bool) -> dict[str, Any] | None:
    plan = to_primitive(measurement)
    if not isinstance(plan, dict):
        return None
    if not pauli_skipped:
        return plan
    sparse_group_count = plan.get("group_count")
    sparse_estimated_cost = plan.get("estimated_shot_cost")
    notes = list(plan.get("notes", []) or [])
    notes.extend(
        [
            "Pauli terms are unavailable because sparse projected lattice-QED skipped materialization.",
            "Sparse exploratory estimates are recorded separately from Pauli hardware measurement costs.",
        ]
    )
    plan.update(
        {
            "pauli_terms_available": False,
            "term_count": None,
            "group_count": None,
            "estimated_shot_cost": None,
            "uncompressed_group_count": None,
            "uncompressed_estimated_shot_cost": None,
            "cost_reduction_ratio": None,
            "sparse_exploratory_group_count": sparse_group_count,
            "sparse_exploratory_estimated_shot_cost": sparse_estimated_cost,
            "notes": notes,
        }
    )
    return plan


def _bind_circuit(circuit: QuantumCircuit, parameters: list[float]) -> QuantumCircuit:
    if not circuit.num_parameters:
        return circuit
    values = np.asarray(parameters, dtype=float)
    if len(values) != circuit.num_parameters:
        raise ValueError(
            f"Cannot bind evidence circuit: {len(values)} values for {circuit.num_parameters} parameters."
        )
    return circuit.assign_parameters(dict(zip(circuit.parameters, values, strict=True)), inplace=False)


def _final_state(
    *,
    solver_outcome: Any,
    spectrum: Any | None,
    num_qubits: int,
) -> tuple[Statevector | None, QuantumCircuit | None, list[str]]:
    notes: list[str] = []
    metadata = getattr(solver_outcome, "metadata", {}) or {}
    circuit = metadata.get("ansatz_circuit")
    parameters = getattr(solver_outcome, "optimal_parameters", []) or []
    if isinstance(circuit, QuantumCircuit):
        try:
            bound = _bind_circuit(circuit, [float(value) for value in parameters])
            return Statevector.from_instruction(bound), bound, notes
        except Exception as exc:  # pragma: no cover - defensive artifact path
            notes.append(f"final_state_from_ansatz_failed={type(exc).__name__}: {exc}")
    if spectrum is not None and getattr(spectrum, "eigenvectors", None) is not None:
        vectors = np.asarray(spectrum.eigenvectors)
        if vectors.ndim == 2 and vectors.shape[1] >= 1 and vectors.shape[0] == 2**num_qubits:
            return Statevector(vectors[:, 0]), None, notes
    notes.append("final_state_not_available")
    return None, None, notes


def _group_operator(operator: SparsePauliOp) -> list[SparsePauliOp]:
    try:
        return list(operator.group_commuting(qubit_wise=True))
    except Exception:
        return [operator]


def _measurement_basis(labels: list[str]) -> tuple[str, list[str]]:
    if not labels:
        return "", []
    basis = ["I"] * len(labels[0])
    conflicts: list[str] = []
    for label in labels:
        for index, char in enumerate(label):
            if char == "I":
                continue
            if basis[index] == "I" or basis[index] == char:
                basis[index] = char
            else:
                conflicts.append(f"q{index}:{basis[index]}/{char}")
    return "".join(char if char != "I" else "Z" for char in basis), conflicts


def _rotate_for_basis(state: Statevector, basis: str) -> Statevector:
    circuit = QuantumCircuit(len(basis))
    for index, char in enumerate(reversed(basis)):
        if char == "X":
            circuit.h(index)
        elif char == "Y":
            circuit.sdg(index)
            circuit.h(index)
    return state.evolve(circuit)


def _measurement_circuit(bound_circuit: QuantumCircuit, basis: str) -> QuantumCircuit:
    circuit = bound_circuit.copy()
    for index, char in enumerate(reversed(basis)):
        if char == "X":
            circuit.h(index)
        elif char == "Y":
            circuit.sdg(index)
            circuit.h(index)
    circuit.measure_all()
    return circuit


def _sample_counts_from_backend(
    *,
    backend: Any | None,
    bound_circuit: QuantumCircuit | None,
    groups: list[dict[str, Any]],
    shots: int,
    seed: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    simulator = getattr(backend, "_backend", None)
    if simulator is None or bound_circuit is None or not hasattr(simulator, "run"):
        return None
    if len(groups) > MAX_COUNTS_GROUPS or bound_circuit.num_qubits > MAX_COUNTS_QUBITS:
        return None
    circuits = []
    group_ids: list[int] = []
    unavailable: list[dict[str, Any]] = []
    for group in groups:
        basis = str(group.get("basis") or "")
        if group.get("basis_conflicts"):
            unavailable.append(
                {
                    "group_id": group["group_id"],
                    "available": False,
                    "basis": basis,
                    "reason": "basis_conflicts",
                    "basis_conflicts": group.get("basis_conflicts"),
                }
            )
            continue
        circuits.append(_measurement_circuit(bound_circuit, basis))
        group_ids.append(int(group["group_id"]))
    try:
        transpiled = transpile(circuits, backend=simulator, optimization_level=0)
        job = simulator.run(transpiled, shots=max(int(shots), 1), seed_simulator=seed)
        result = job.result()
    except Exception as exc:  # pragma: no cover - defensive fallback path
        return (
            [],
            {
                "available": False,
                "reason": "backend_counts_failed",
                "failure": f"{type(exc).__name__}: {exc}",
            },
        )
    group_counts = list(unavailable)
    for index, group_id in enumerate(group_ids):
        counts = {str(key): int(value) for key, value in result.get_counts(index).items()}
        group_counts.append(
            {
                "group_id": group_id,
                "available": True,
                "basis": groups[group_id].get("basis"),
                "shots": int(shots),
                "counts": counts,
                "top_counts": sorted(
                    counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:MAX_DOMINANT_CONFIGURATIONS],
            }
        )
    group_counts.sort(key=lambda item: int(item["group_id"]))
    digest_payload = {"groups": group_counts, "shots": int(shots)}
    return group_counts, {
        "available": True,
        "source": "backend_measurement_circuits",
        "group_count": len(group_counts),
        "shots_per_group": int(shots),
        "counts_sha256": _json_sha256(digest_payload),
    }


def _sample_counts_from_state(
    *,
    state: Statevector | None,
    groups: list[dict[str, Any]],
    shots: int,
    seed: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if state is None:
        return [], {"available": False, "reason": "final_state_not_available"}
    num_qubits = int(state.num_qubits)
    if num_qubits > MAX_COUNTS_QUBITS:
        return [], {
            "available": False,
            "reason": "qubit_count_above_counts_limit",
            "num_qubits": num_qubits,
            "limit": MAX_COUNTS_QUBITS,
        }
    if len(groups) > MAX_COUNTS_GROUPS:
        return [], {
            "available": False,
            "reason": "measurement_group_count_above_counts_limit",
            "group_count": len(groups),
            "limit": MAX_COUNTS_GROUPS,
        }
    rng = np.random.default_rng(seed)
    group_counts: list[dict[str, Any]] = []
    for group in groups:
        basis = str(group.get("basis") or "")
        if group.get("basis_conflicts"):
            group_counts.append(
                {
                    "group_id": group["group_id"],
                    "available": False,
                    "basis": basis,
                    "reason": "basis_conflicts",
                    "basis_conflicts": group.get("basis_conflicts"),
                }
            )
            continue
        rotated = _rotate_for_basis(state, basis)
        probabilities = rotated.probabilities()
        labels = [format(index, f"0{num_qubits}b") for index in range(len(probabilities))]
        sampled = rng.multinomial(max(int(shots), 1), probabilities)
        counts = {
            label: int(count)
            for label, count in zip(labels, sampled, strict=True)
            if int(count) > 0
        }
        group_counts.append(
            {
                "group_id": group["group_id"],
                "available": True,
                "basis": basis,
                "shots": int(shots),
                "counts": counts,
                "top_counts": sorted(
                    counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:MAX_DOMINANT_CONFIGURATIONS],
            }
        )
    digest_payload = {"groups": group_counts, "shots": int(shots)}
    return group_counts, {
        "available": True,
        "source": "statevector_sampler_from_final_state",
        "group_count": len(group_counts),
        "shots_per_group": int(shots),
        "counts_sha256": _json_sha256(digest_payload),
    }


def _pauli_evidence(
    *,
    operator: SparsePauliOp,
    state: Statevector | None,
    pauli_terms_available: bool = True,
    unavailable_reason: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not pauli_terms_available:
        return [], [], {
            "pauli_terms_available": False,
            "pauli_unavailable_reason": unavailable_reason or "pauli_terms_not_available",
            "pauli_term_count": None,
            "measurement_group_count": None,
            "expectations_available": False,
            "energy_contribution_sum": None,
            "coefficient_l1_norm": None,
        }
    groups = _group_operator(operator)
    labels_to_group: dict[str, int] = {}
    group_payloads: list[dict[str, Any]] = []
    for group_id, group in enumerate(groups):
        labels = list(group.paulis.to_labels())
        basis, conflicts = _measurement_basis(labels)
        for label in labels:
            labels_to_group.setdefault(label, group_id)
        group_payloads.append(
            {
                "group_id": group_id,
                "term_count": len(group),
                "basis": basis,
                "basis_conflicts": conflicts,
                "pauli_labels": labels,
            }
        )

    term_payloads: list[dict[str, Any]] = []
    contribution_sum = 0.0
    expectation_available = state is not None
    for index, (pauli, coeff) in enumerate(zip(operator.paulis, operator.coeffs, strict=True)):
        label = pauli.to_label()
        expectation = None
        contribution = None
        if state is not None:
            expectation = _coerce_real(state.expectation_value(SparsePauliOp.from_list([(label, 1.0)])))
            contribution = _coerce_real(coeff) * expectation
            contribution_sum += contribution
        term_payloads.append(
            {
                "index": index,
                "pauli": label,
                "coefficient_real": _coerce_real(coeff),
                "coefficient_imag": float(np.imag(coeff)),
                "measurement_group_id": labels_to_group.get(label),
                "expectation_value": expectation,
                "energy_contribution": contribution,
            }
        )
    summary = {
        "pauli_terms_available": True,
        "pauli_term_count": len(operator),
        "measurement_group_count": len(group_payloads),
        "expectations_available": expectation_available,
        "energy_contribution_sum": contribution_sum if expectation_available else None,
        "coefficient_l1_norm": float(np.sum(np.abs(operator.coeffs))),
    }
    return term_payloads, group_payloads, summary


def _state_summary(
    *,
    state: Statevector | None,
    operator: SparsePauliOp,
    spectrum: Any | None,
) -> dict[str, Any]:
    if state is None:
        return {"available": False, "reason": "final_state_not_available"}
    probabilities = state.probabilities_dict()
    dominant = [
        {"bitstring": bitstring, "probability": float(probability)}
        for bitstring, probability in sorted(
            probabilities.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:MAX_DOMINANT_CONFIGURATIONS]
    ]
    variance = None
    expectation = None
    if operator.num_qubits <= 12:
        matrix = operator.to_matrix(sparse=True)
        vector = np.asarray(state.data, dtype=complex)
        h_vector = matrix @ vector
        expectation = _coerce_real(np.vdot(vector, h_vector))
        variance = max(_coerce_real(np.vdot(h_vector, h_vector)) - expectation**2, 0.0)
    ground_overlap = None
    if spectrum is not None and getattr(spectrum, "eigenvectors", None) is not None:
        vectors = np.asarray(spectrum.eigenvectors)
        if vectors.ndim == 2 and vectors.shape[1] >= 1 and vectors.shape[0] == len(state.data):
            ground_overlap = float(abs(np.vdot(vectors[:, 0], state.data)) ** 2)
    return {
        "available": True,
        "dominant_configurations": dominant,
        "ground_state_overlap": ground_overlap,
        "hamiltonian_expectation": expectation,
        "hamiltonian_variance": variance,
        "variance_method": "sparse_matrix_norm" if variance is not None else "not_available",
    }


def _resource_summary(bound_circuit: QuantumCircuit | None, runtime_submission: Any | None, mapping: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "num_qubits": int(mapping.summary.num_qubits),
        "raw_num_qubits": getattr(mapping.summary, "raw_num_qubits", None),
        "qubit_term_count": int(mapping.summary.qubit_term_count),
        "raw_qubit_term_count": getattr(mapping.summary, "raw_qubit_term_count", None),
    }
    if bound_circuit is not None:
        counts = bound_circuit.count_ops()
        payload.update(
            {
                "circuit_depth": int(bound_circuit.depth()),
                "circuit_size": int(bound_circuit.size()),
                "two_qubit_gate_count": int(
                    sum(int(counts.get(name, 0)) for name in ("cx", "cz", "ecr", "rxx", "ryy", "rzz", "swap"))
                ),
                "operation_counts": {str(key): int(value) for key, value in counts.items()},
            }
        )
    else:
        payload.update(
            {
                "circuit_depth": None,
                "two_qubit_gate_count": None,
                "operation_counts": {},
            }
        )
    runtime = to_primitive(runtime_submission) if runtime_submission is not None else {}
    if runtime:
        payload["runtime_transpiled_depth"] = runtime.get("transpiled_depth")
        payload["runtime_transpiled_two_qubit_gate_count"] = runtime.get("transpiled_two_qubit_gate_count")
        payload["runtime_selected_layout"] = runtime.get("selected_layout", [])
    return payload


def _symmetry_summary(problem: Any, mapping: Any, qft_model: Any | None) -> dict[str, Any]:
    qft = to_primitive(qft_model) if qft_model is not None else None
    return {
        "particle_number": {
            "target_num_particles": list(getattr(problem, "num_particles", []) or []),
            "status": "declared_from_problem_summary",
            "expectation_value": None,
            "deviation": None,
            "notes": [
                "Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1."
            ],
        },
        "spin": {
            "status": "not_available",
            "notes": ["Spin-conservation expectation requires a mapped spin operator and is not computed in v1."],
        },
        "z2": {
            "status": getattr(mapping.summary, "symmetry_reduction_status", None),
            "z2_symmetry_count": getattr(mapping.summary, "z2_symmetry_count", 0),
            "z2_tapering_values": getattr(mapping.summary, "z2_tapering_values", None),
            "validation": getattr(mapping.summary, "symmetry_reduction_validation", {}),
            "notes": getattr(mapping.summary, "symmetry_reduction_notes", []),
        },
        "qft_constraints": (qft or {}).get("constraint_expectations") if qft else None,
    }


def _error_budget(
    *,
    benchmark: Any,
    sampled_result: Any | None,
    compression_result: Any | None,
    runtime_submission: Any | None,
    qft_model: Any | None,
    cavity_qed_model: Any | None,
    environment_embedding: Any | None,
    existing_error_budget: dict[str, Any] | None,
) -> dict[str, Any]:
    benchmark_payload = to_primitive(benchmark)
    sampled = to_primitive(sampled_result) if sampled_result is not None else None
    compression = to_primitive(compression_result) if compression_result is not None else None
    runtime = to_primitive(runtime_submission) if runtime_submission is not None else None
    qft = to_primitive(qft_model) if qft_model is not None else None
    cavity = to_primitive(cavity_qed_model) if cavity_qed_model is not None else None
    embedding = to_primitive(environment_embedding) if environment_embedding is not None else None
    runtime_stds = None
    if runtime:
        returned = runtime.get("returned_job_metadata") or {}
        stds = returned.get("stds")
        if isinstance(stds, list) and stds:
            runtime_stds = stds[0]
    return {
        "ansatz_error": {
            "available": benchmark_payload.get("comparison_target") in {"variational_result", "sampled_result"},
            "absolute_error_hartree": benchmark_payload.get("absolute_error"),
            "baseline": "exact_baseline" if benchmark_payload.get("exact_available") else None,
        },
        "shot_noise": {
            "available": sampled is not None or runtime_stds is not None,
            "sampled_standard_error": (sampled or {}).get("standard_error") if sampled else None,
            "runtime_reported_std": runtime_stds,
            "benchmark_statistical_error": benchmark_payload.get("statistical_error"),
        },
        "compression_error": {
            "available": compression is not None,
            "reconstruction_error": (compression or {}).get("reconstruction_error") if compression else None,
            "compressed_vs_uncompressed": benchmark_payload.get("compressed_vs_uncompressed"),
        },
        "hardware_noise": {
            "available": runtime is not None,
            "verification_status": (runtime or {}).get("verification_status") if runtime else None,
            "mitigation_metadata": ((runtime or {}).get("returned_job_metadata") or {}).get("metadata") if runtime else None,
        },
        "field_model": {
            "qft_error_budget": (qft or {}).get("error_budget") if qft else None,
            "cavity_error_budget": (cavity or {}).get("error_budget") if cavity else None,
            "finite_cutoff_boundary": bool(qft or cavity),
        },
        "qmmm_embedding": {
            "available": embedding is not None,
            "mm_environment_quantized": False if embedding is not None else None,
            "one_body_environment": (embedding or {}).get("one_body_environment") if embedding else None,
            "cache_validation": (embedding or {}).get("cache_validation") if embedding else None,
            "boundary": (embedding or {}).get("boundary") if embedding else None,
        },
        "existing_error_budget": existing_error_budget or {},
    }


def build_and_write_quantum_evidence(
    *,
    run_id: str,
    sidecar_path: Path | None,
    mapping: Any,
    solver_outcome: Any,
    spectrum: Any | None,
    problem: Any,
    backend: Any | None,
    measurement: Any | None,
    backend_summary: Any,
    benchmark: Any,
    sampled_result: Any | None,
    runtime_submission: Any | None,
    compression_result: Any | None,
    qft_model: Any | None,
    qft_dynamics: dict[str, Any] | None,
    cavity_qed_model: Any | None,
    field_model: Any | None,
    environment_embedding: Any | None,
    external_point_charges: Any | None,
    existing_error_budget: dict[str, Any] | None = None,
) -> QuantumEvidenceSummary:
    """Build the compact summary and write the full quantum evidence sidecar."""
    qft_payload = _qft_payload(qft_model)
    pauli_skipped = _pauli_materialization_skipped(qft_payload)
    state, bound_circuit, state_notes = _final_state(
        solver_outcome=solver_outcome,
        spectrum=spectrum,
        num_qubits=int(mapping.summary.num_qubits),
    )
    pauli_terms, measurement_groups, hamiltonian_summary = _pauli_evidence(
        operator=mapping.qubit_hamiltonian,
        state=state,
        pauli_terms_available=not pauli_skipped,
        unavailable_reason=(
            "qft_sparse_projected_pauli_materialization_skipped"
            if pauli_skipped
            else None
        ),
    )
    projected_metadata = _qft_projected_metadata(qft_payload)
    hamiltonian_summary.update({key: value for key, value in projected_metadata.items() if value is not None})
    shots = int(getattr(backend_summary, "shots", None) or DEFAULT_COUNTS_SHOTS)
    seed = getattr(backend_summary, "seed", None)
    if pauli_skipped:
        group_counts = []
        sampling_summary = {
            "available": False,
            "reason": "pauli_materialization_skipped_for_sparse_projected_lattice_qed",
            "source": "not_applicable",
        }
    else:
        backend_counts = _sample_counts_from_backend(
            backend=backend,
            bound_circuit=bound_circuit,
            groups=measurement_groups,
            shots=shots,
            seed=seed,
        )
        if backend_counts is None:
            group_counts, sampling_summary = _sample_counts_from_state(
                state=state,
                groups=measurement_groups,
                shots=shots,
                seed=seed,
            )
        else:
            group_counts, sampling_summary = backend_counts
    state_summary = _state_summary(state=state, operator=mapping.qubit_hamiltonian, spectrum=spectrum)
    resources = _resource_summary(bound_circuit, runtime_submission, mapping)
    resources.update({key: value for key, value in projected_metadata.items() if value is not None})
    sparse_estimate = bool(pauli_skipped and qft_payload)
    groups_sha256 = None if pauli_skipped else _json_sha256({"groups": measurement_groups})
    raw_estimated_cost = getattr(measurement, "estimated_shot_cost", None) if measurement is not None else None
    measurement_summary = {
        "plan": _measurement_plan_payload(measurement, pauli_skipped=pauli_skipped),
        "qubit_wise_group_count": None if pauli_skipped else len(measurement_groups),
        "counts_shots_per_group": shots,
        "estimated_measurement_cost": None if pauli_skipped else raw_estimated_cost,
        "sparse_exploratory_estimated_measurement_cost": raw_estimated_cost if sparse_estimate else None,
        "groups_sha256": groups_sha256,
        "measurement_group_count_scope": (
            "sparse_exploratory_estimate" if sparse_estimate else "pauli_grouping"
        ),
        "estimated_measurement_cost_scope": (
            "sparse_exploratory_estimate" if sparse_estimate else "pauli_grouping"
        ),
        "estimated_measurement_cost_is_hardware_cost": False if sparse_estimate else None,
        "sparse_estimated_group_count": (
            getattr(measurement, "group_count", None) if sparse_estimate and measurement is not None else None
        ),
        "notes": (
            [
                "Pauli terms are not materialized for this sparse projected lattice-QED Hamiltonian.",
                "Measurement groups and shot cost are exploratory sparse estimates, not real hardware measurement cost.",
            ]
            if sparse_estimate
            else []
        ),
    }
    symmetry_checks = _symmetry_summary(problem, mapping, qft_model)
    error_budget = _error_budget(
        benchmark=benchmark,
        sampled_result=sampled_result,
        compression_result=compression_result,
        runtime_submission=runtime_submission,
        qft_model=qft_model,
        cavity_qed_model=cavity_qed_model,
        environment_embedding=environment_embedding,
        existing_error_budget=existing_error_budget,
    )
    sparse_exact_validation = (
        qft_payload.get("sparse_exact_validation")
        if isinstance(qft_payload.get("sparse_exact_validation"), dict)
        else {}
    )
    lattice_qed_observables = (
        qft_payload.get("observables")
        if isinstance(qft_payload.get("observables"), dict)
        else {}
    )
    field_payload = {
        "field_model": to_primitive(field_model),
        "qft_model": qft_payload,
        "qft_dynamics": to_primitive(qft_dynamics),
        "cavity_qed_model": to_primitive(cavity_qed_model),
        "environment_embedding": to_primitive(environment_embedding),
        "external_point_charges": to_primitive(external_point_charges),
    }
    sidecar = {
        "schema": SCHEMA,
        "run_id": run_id,
        "hamiltonian": {
            **hamiltonian_summary,
            "pauli_terms": pauli_terms,
        },
        "measurement": {
            **measurement_summary,
            "groups": measurement_groups,
        },
        "sampling": {
            **sampling_summary,
            "group_counts": group_counts,
        },
        "optimization": {
            "trajectory": list((getattr(solver_outcome, "metadata", {}) or {}).get("evaluation_trajectory", [])),
            "evaluation_count": int(getattr(solver_outcome, "evaluations", 0)),
            "converged": bool(getattr(solver_outcome, "converged", False)),
        },
        "state": state_summary,
        "symmetry_checks": symmetry_checks,
        "resources": resources,
        "error_budget": error_budget,
        "sparse_exact_validation": sparse_exact_validation,
        "lattice_qed_observables": lattice_qed_observables,
        "field_and_embedding": field_payload,
        "notes": state_notes,
    }
    if sidecar_path is not None:
        sidecar_path.write_text(json.dumps(to_primitive(sidecar), indent=2, sort_keys=True), encoding="utf-8")
        sidecar_sha = hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
        sidecar_ref = str(sidecar_path)
    else:
        sidecar_sha = None
        sidecar_ref = None
    return QuantumEvidenceSummary(
        available=True,
        schema=SCHEMA,
        sidecar_path=sidecar_ref,
        sidecar_sha256=sidecar_sha,
        hamiltonian={key: value for key, value in hamiltonian_summary.items() if key != "pauli_terms"},
        measurement=measurement_summary,
        sampling=sampling_summary,
        state=state_summary,
        symmetry_checks=symmetry_checks,
        resources=resources,
        error_budget=error_budget,
        sparse_exact_validation=sparse_exact_validation,
        lattice_qed_observables=lattice_qed_observables,
        notes=state_notes,
    )
