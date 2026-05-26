"""Field-model evidence sidecar construction for run artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import scipy.sparse as sp
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from qcchem.core import FieldArtifactPaths, FieldEvidenceSummary
from qcchem.field_models.registry import FIELD_MODEL_REGISTRY
from qcchem.io.serialization import to_primitive
from qcchem.qft.observables import build_qft_observable_matrices, expectation_value


SCHEMA = "qcchem.field_evidence.v1"


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(to_primitive(payload), indent=2, sort_keys=True).encode("utf-8")


def _write_sidecar(path: Path, payload: dict[str, Any]) -> str:
    encoded = _json_bytes(payload)
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def _real(value: Any) -> float:
    return float(np.real_if_close(value))


def _zero_op(num_qubits: int) -> SparsePauliOp:
    return SparsePauliOp.from_list([("I" * num_qubits, 0.0)])


def _identity_op(num_qubits: int) -> SparsePauliOp:
    return SparsePauliOp.from_list([("I" * num_qubits, 1.0)])


def _sum_sparse_paulis(operators: list[SparsePauliOp], *, num_qubits: int) -> SparsePauliOp:
    total = _zero_op(num_qubits)
    for operator in operators:
        total = total + operator
    return total.simplify(atol=1.0e-12)


def _expectation_matrix(matrix: Any, state: np.ndarray) -> float:
    operator = matrix.tocsr() if sp.issparse(matrix) else np.asarray(matrix, dtype=complex)
    return _real(np.vdot(state, operator @ state))


def _expectation_pauli(operator: SparsePauliOp, state: np.ndarray) -> float:
    matrix = operator.to_matrix(sparse=True)
    return _real(np.vdot(state, matrix @ state))


def _bind_circuit(circuit: QuantumCircuit, parameters: list[float]) -> QuantumCircuit:
    if not circuit.num_parameters:
        return circuit
    values = np.asarray(parameters, dtype=float)
    if len(values) != circuit.num_parameters:
        raise ValueError(
            f"Cannot bind field-evidence circuit: {len(values)} values for {circuit.num_parameters} parameters."
        )
    return circuit.assign_parameters(dict(zip(circuit.parameters, values, strict=True)), inplace=False)


def _state_from_solver_or_spectrum(
    *,
    solver_outcome: Any,
    spectrum: Any | None,
    dimension: int | None,
) -> tuple[np.ndarray | None, str | None, list[str]]:
    notes: list[str] = []
    metadata = getattr(solver_outcome, "metadata", {}) or {}
    circuit = metadata.get("ansatz_circuit")
    parameters = [float(value) for value in (getattr(solver_outcome, "optimal_parameters", []) or [])]
    if isinstance(circuit, QuantumCircuit):
        try:
            state = np.asarray(Statevector.from_instruction(_bind_circuit(circuit, parameters)).data, dtype=complex)
            if dimension is None or len(state) == int(dimension):
                return state, "variational_final_state", notes
            notes.append(
                f"variational_state_dimension_mismatch={len(state)} expected={dimension}"
            )
        except Exception as exc:  # pragma: no cover - defensive artifact path
            notes.append(f"variational_state_unavailable={type(exc).__name__}: {exc}")
    if spectrum is not None and getattr(spectrum, "eigenvectors", None) is not None:
        vectors = np.asarray(spectrum.eigenvectors, dtype=complex)
        if vectors.ndim == 2 and vectors.shape[1] >= 1:
            if dimension is None or vectors.shape[0] == int(dimension):
                return np.asarray(vectors[:, 0], dtype=complex), "exact_spectrum_ground_state", notes
            notes.append(
                f"exact_spectrum_dimension_mismatch={vectors.shape[0]} expected={dimension}"
            )
    notes.append("field_state_not_available")
    return None, None, notes


def _registry_payload(run_id: str, active_model_kind: str | None, field_model: Any | None) -> dict[str, Any]:
    adapters = []
    for adapter in FIELD_MODEL_REGISTRY.values():
        placeholder = adapter.capability_tier == "placeholder"
        adapters.append(
            {
                "model_kind": adapter.model_kind,
                "registry_name": adapter.registry_name,
                "capability_tier": adapter.capability_tier,
                "implementation_status": "placeholder" if placeholder else "implemented",
                "observables": list(adapter.observables),
                "risk_notes": list(adapter.risk_notes),
                "scientific_claim_allowed": not placeholder,
            }
        )
    return {
        "schema": SCHEMA,
        "artifact_kind": "field_model_registry",
        "run_id": run_id,
        "model_kind": active_model_kind,
        "registry_name": getattr(field_model, "registry_name", None) if field_model is not None else None,
        "active_model_kind": active_model_kind,
        "active_field_model": to_primitive(field_model),
        "supported_model_kinds": [item["model_kind"] for item in adapters],
        "adapters": adapters,
        "placeholder_policy": {
            "implementation_status": "placeholder",
            "scientific_claim_allowed": False,
            "required_risk_note": "Placeholder field-model entries must not be used as scientific evidence.",
        },
    }


def _lattice_sector_matrices(qft_context: Any, state_dimension: int | None) -> tuple[dict[str, Any], str]:
    bundle = getattr(qft_context, "sparse_bundle", None)
    if bundle is not None:
        projected = getattr(bundle, "projected_hamiltonian", None)
        if projected is not None and state_dimension == int(projected.shape[0]):
            return dict(getattr(bundle, "projected_sector_matrices", {}) or {}), "sparse_projected"
        return dict(getattr(bundle, "sector_matrices", {}) or {}), "sparse_full"
    return dict(getattr(qft_context, "sector_matrices", {}) or {}), "dense_full"


def _lattice_hamiltonian_payload(
    *,
    run_id: str,
    qft_context: Any,
    mapping: Any,
    solver_energy: float | None,
    solver_outcome: Any,
    spectrum: Any | None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    summary = qft_context.summary
    dimension = None
    if getattr(qft_context, "sparse_bundle", None) is not None:
        bundle = qft_context.sparse_bundle
        source = bundle.projected_hamiltonian if bundle.projected_hamiltonian is not None else bundle.full_hamiltonian
        dimension = int(source.shape[0])
    elif getattr(qft_context, "hamiltonian_matrix", None) is not None:
        matrix = np.asarray(qft_context.hamiltonian_matrix)
        if matrix.size:
            dimension = int(matrix.shape[0])
    state, state_source, notes = _state_from_solver_or_spectrum(
        solver_outcome=solver_outcome,
        spectrum=spectrum,
        dimension=dimension,
    )
    sectors, representation = _lattice_sector_matrices(qft_context, None if state is None else len(state))
    sector_payload: list[dict[str, Any]] = []
    sector_sum = 0.0
    for name, matrix in sectors.items():
        contribution = None
        if state is not None and int(matrix.shape[0]) == len(state):
            contribution = _expectation_matrix(matrix, state)
            sector_sum += contribution
        sector_payload.append(
            {
                "sector": str(name),
                "term_count": int((summary.term_counts_by_sector or {}).get(name, 0)),
                "matrix_dimension": int(matrix.shape[0]),
                "nnz": int(matrix.nnz if sp.issparse(matrix) else np.count_nonzero(np.abs(matrix) > 1.0e-12)),
                "energy_contribution": contribution,
            }
        )
    closure_available = state is not None and solver_energy is not None and bool(sector_payload)
    hamiltonian = {
        "schema": SCHEMA,
        "artifact_kind": "field_hamiltonian",
        "run_id": run_id,
        "model_kind": "lattice_qed",
        "model": summary.model,
        "operator_representation": representation,
        "pauli_term_count": int(getattr(mapping.summary, "qubit_term_count", 0)),
        "term_counts_by_sector": dict(summary.term_counts_by_sector or {}),
        "sectors": sector_payload,
        "sector_energy_sum": sector_sum if closure_available else None,
        "solver_hamiltonian_energy": solver_energy,
        "sector_energy_closure_error": (
            float(abs(sector_sum - float(solver_energy))) if closure_available else None
        ),
        "sector_energy_closure_available": closure_available,
        "state_source": state_source,
        "finite_cutoff_boundary": True,
    }
    compact = {
        "model_kind": "lattice_qed",
        "sector_count": len(sector_payload),
        "sector_energy_sum": hamiltonian["sector_energy_sum"],
        "sector_energy_closure_error": hamiltonian["sector_energy_closure_error"],
        "sector_energy_closure_available": closure_available,
        "pauli_term_count": hamiltonian["pauli_term_count"],
    }
    return hamiltonian, compact, notes


def _cavity_hamiltonian_payload(
    *,
    run_id: str,
    cavity_context: Any,
    mapping: Any,
    solver_energy: float | None,
    solver_outcome: Any,
    spectrum: Any | None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    summary = cavity_context.summary
    dimension = 2 ** int(summary.total_qubits)
    state, state_source, notes = _state_from_solver_or_spectrum(
        solver_outcome=solver_outcome,
        spectrum=spectrum,
        dimension=dimension,
    )
    electronic_qubits = int(cavity_context.electronic_qubits)
    photon_full = _identity_op(electronic_qubits).tensor(cavity_context.photon_hamiltonian).simplify(atol=1.0e-12)
    penalty_full = (
        float(summary.photon_physical_subspace_penalty) * cavity_context.photon_leakage_operator
    ).simplify(atol=1.0e-12)
    photon_without_penalty = (photon_full - penalty_full).simplify(atol=1.0e-12)
    coupling_full = _sum_sparse_paulis(
        list(cavity_context.coupling_energy_operators),
        num_qubits=int(summary.total_qubits),
    )
    dse_full = _sum_sparse_paulis(
        list(cavity_context.dipole_self_energy_operators),
        num_qubits=int(summary.total_qubits),
    )
    electronic_full = (
        cavity_context.qubit_hamiltonian - photon_without_penalty - penalty_full - coupling_full - dse_full
    ).simplify(atol=1.0e-12)
    sector_ops = [
        ("electronic", electronic_full),
        ("photon", photon_without_penalty),
        ("electron_photon_coupling", coupling_full),
        ("dipole_self_energy", dse_full),
        ("photon_physical_subspace_penalty", penalty_full),
    ]
    sector_payload: list[dict[str, Any]] = []
    sector_sum = 0.0
    for name, operator in sector_ops:
        contribution = None
        if state is not None:
            contribution = _expectation_pauli(operator, state)
            sector_sum += contribution
        sector_payload.append(
            {
                "sector": name,
                "pauli_term_count": int(len(operator)),
                "energy_contribution": contribution,
            }
        )
    closure_available = state is not None and solver_energy is not None
    hamiltonian = {
        "schema": SCHEMA,
        "artifact_kind": "field_hamiltonian",
        "run_id": run_id,
        "model_kind": "pauli_fierz_cavity_qed",
        "model": summary.model,
        "hamiltonian_formula": summary.hamiltonian_formula,
        "pauli_term_count": int(getattr(mapping.summary, "qubit_term_count", 0)),
        "term_counts_by_sector": dict(summary.term_counts_by_sector or {}),
        "sectors": sector_payload,
        "sector_energy_sum": sector_sum if closure_available else None,
        "solver_hamiltonian_energy": solver_energy,
        "sector_energy_closure_error": (
            float(abs(sector_sum - float(solver_energy))) if closure_available else None
        ),
        "sector_energy_closure_available": closure_available,
        "state_source": state_source,
        "finite_cutoff_boundary": True,
    }
    compact = {
        "model_kind": "pauli_fierz_cavity_qed",
        "sector_count": len(sector_payload),
        "sector_energy_sum": hamiltonian["sector_energy_sum"],
        "sector_energy_closure_error": hamiltonian["sector_energy_closure_error"],
        "sector_energy_closure_available": closure_available,
        "pauli_term_count": hamiltonian["pauli_term_count"],
    }
    return hamiltonian, compact, notes


def _error_series(left: Any, right: Any) -> list[float] | None:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right):
        return None
    return [float(abs(float(a) - float(b))) for a, b in zip(left, right, strict=True)]


def _observable_error_matrix(qft_dynamics: dict[str, Any] | None) -> dict[str, Any]:
    if not qft_dynamics:
        return {"available": False, "reason": "dynamics_not_available"}
    exact = qft_dynamics.get("exact") or {}
    trotter = qft_dynamics.get("trotter") or {}
    if not exact.get("available") or not trotter.get("available"):
        return {"available": False, "reason": "exact_or_trotter_unavailable"}
    exact_obs = exact.get("observables") or {}
    trotter_obs = trotter.get("observables") or {}
    matrix: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    times = exact.get("time_points") or []
    for name, exact_values in exact_obs.items():
        trotter_values = trotter_obs.get(name)
        if isinstance(exact_values, list) and exact_values and all(
            not isinstance(item, list) for item in exact_values
        ):
            errors = _error_series(exact_values, trotter_values)
            matrix[name] = {
                "per_time_abs_error": errors,
                "max_abs_error": max(errors) if errors else None,
            }
            if errors is not None:
                for index, error in enumerate(errors):
                    rows.append(
                        {
                            "time": float(times[index]) if index < len(times) else None,
                            "observable": name,
                            "exact": float(exact_values[index]),
                            "trotter": float(trotter_values[index]),
                            "abs_error": float(error),
                        }
                    )
    return {
        "available": True,
        "observable_count": len(matrix),
        "matrix": matrix,
        "rows": rows,
    }


def _lattice_observables_payload(
    *,
    run_id: str,
    qft_context: Any,
    solver_outcome: Any,
    spectrum: Any | None,
    qft_dynamics: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    observables = build_qft_observable_matrices(qft_context)
    state, state_source, notes = _state_from_solver_or_spectrum(
        solver_outcome=solver_outcome,
        spectrum=spectrum,
        dimension=int(observables.aggregate["particle_number"].shape[0]),
    )
    ground_state_expectations: dict[str, Any] = {}
    if state is not None:
        ground_state_expectations = {
            "particle_number": expectation_value(observables.aggregate["particle_number"], state),
            "total_electric_energy": expectation_value(observables.aggregate["total_electric_energy"], state),
            "total_gauss_violation": expectation_value(observables.aggregate["total_gauss_violation"], state),
            "total_wilson": expectation_value(observables.aggregate["total_wilson"], state),
        }
    dynamics_obs = (qft_dynamics or {}).get("exact", {}).get("observables", {}) if qft_dynamics else {}
    payload = {
        "schema": SCHEMA,
        "artifact_kind": "field_observables",
        "run_id": run_id,
        "model_kind": "lattice_qed",
        "metadata": dict(observables.metadata),
        "ground_state_expectations": ground_state_expectations,
        "ground_state_source": state_source,
        "dynamics_exact_observables": dynamics_obs,
        "wilson": {
            "plaquette_count": int(observables.metadata.get("plaquette_wilson_count", 0)),
            "exact_curve": dynamics_obs.get("total_wilson", []),
            "plaquette_wilson_curves": dynamics_obs.get("plaquette_wilson", []),
        },
        "electric": {
            "flux_curves": dynamics_obs.get("link_electric_flux", []),
            "energy_curves": dynamics_obs.get("link_electric_energy", []),
            "total_electric_energy": dynamics_obs.get("total_electric_energy", []),
        },
        "gauss": {
            "total_gauss_violation": dynamics_obs.get("total_gauss_violation", []),
            "gauss_residual_by_site": dynamics_obs.get("gauss_residual_by_site", []),
        },
        "observable_families": {
            "site_density": int(observables.metadata.get("site_density_count", 0)),
            "electric_flux": int(observables.metadata.get("link_electric_flux_count", 0)),
            "electric_energy": int(observables.metadata.get("link_electric_energy_count", 0)),
            "gauss_residual": int(observables.metadata.get("gauss_residual_count", 0)),
            "plaquette_wilson": int(observables.metadata.get("plaquette_wilson_count", 0)),
        },
    }
    compact = {
        "model_kind": "lattice_qed",
        "observable_families": payload["observable_families"],
        "ground_state_expectations_available": bool(ground_state_expectations),
        "has_wilson_observables": payload["observable_families"]["plaquette_wilson"] > 0,
    }
    return payload, compact, notes


def _cavity_observables_payload(run_id: str, cavity_context: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = cavity_context.summary
    observables = dict(summary.observables or {})
    payload = {
        "schema": SCHEMA,
        "artifact_kind": "field_observables",
        "run_id": run_id,
        "model_kind": "pauli_fierz_cavity_qed",
        "photon_occupation": observables.get("photon_occupation", []),
        "dipole_expectation": observables.get("dipole_expectation", []),
        "electron_photon_coupling_energy": observables.get("electron_photon_coupling_energy", []),
        "dipole_self_energy": observables.get("dipole_self_energy", []),
        "polaritonic_state_composition": observables.get("polaritonic_state_composition", []),
        "photon_physical_subspace_leakage": observables.get("photon_physical_subspace_leakage"),
        "exact_residual_norm": observables.get("exact_residual_norm"),
        "vqe_vs_exact_error": observables.get("vqe_vs_exact_error"),
        "cutoff_sensitivity_inputs": {
            "mode_count": int(summary.mode_count),
            "max_occupation_by_mode": [
                int(mode.get("max_occupation", 0)) for mode in list(summary.modes or [])
            ],
            "frequencies": [float(mode.get("frequency", 0.0)) for mode in list(summary.modes or [])],
            "coupling_strengths": [
                float(mode.get("coupling_strength", 0.0)) for mode in list(summary.modes or [])
            ],
        },
    }
    compact = {
        "model_kind": "pauli_fierz_cavity_qed",
        "photon_occupation_count": len(payload["photon_occupation"]),
        "polaritonic_component_count": len(payload["polaritonic_state_composition"]),
        "photon_physical_subspace_leakage": payload["photon_physical_subspace_leakage"],
        "cutoff_sensitivity_inputs": payload["cutoff_sensitivity_inputs"],
    }
    return payload, compact


def _dynamics_payload(run_id: str, model_kind: str, qft_dynamics: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if model_kind != "lattice_qed":
        payload = {
            "schema": SCHEMA,
            "artifact_kind": "field_dynamics",
            "run_id": run_id,
            "model_kind": model_kind,
            "available": False,
            "reason": "field_model_has_no_dynamics_artifact_in_v1",
        }
        return payload, {"available": False, "reason": payload["reason"]}
    dynamics = to_primitive(qft_dynamics) if qft_dynamics is not None else None
    error_matrix = _observable_error_matrix(dynamics)
    payload = {
        "schema": SCHEMA,
        "artifact_kind": "field_dynamics",
        "run_id": run_id,
        "model_kind": "lattice_qed",
        "available": dynamics is not None,
        "dynamics": dynamics,
        "exact_vs_trotter_error_matrix": error_matrix,
    }
    compact = {
        "available": dynamics is not None,
        "exact_available": ((dynamics or {}).get("exact") or {}).get("available") if dynamics else None,
        "trotter_available": ((dynamics or {}).get("trotter") or {}).get("available") if dynamics else None,
        "error_matrix_available": error_matrix.get("available"),
    }
    return payload, compact


def _constraints_payload(
    *,
    run_id: str,
    model_kind: str,
    qft_model: Any | None,
    cavity_model: Any | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if model_kind == "lattice_qed" and qft_model is not None:
        qft = to_primitive(qft_model)
        payload = {
            "schema": SCHEMA,
            "artifact_kind": "field_constraints",
            "run_id": run_id,
            "model_kind": model_kind,
            "gauss_law": {
                "constraints": qft.get("constraints", {}),
                "constraint_residuals": qft.get("constraint_residuals", {}),
                "gauss_law_generators": qft.get("gauss_law_generators", []),
                "hamiltonian_gauge_commutator_norms": qft.get("hamiltonian_gauge_commutator_norms", []),
                "constraint_expectations": qft.get("constraint_expectations", {}),
            },
            "physical_sector": qft.get("physical_sector", {}),
            "gauge_invariant_ansatz": qft.get("gauge_invariant_ansatz", {}),
            "finite_cutoff_boundary": True,
        }
        compact = {
            "model_kind": model_kind,
            "gauss_law_available": bool(payload["gauss_law"]["gauss_law_generators"]),
            "physical_sector": payload["physical_sector"],
        }
        return payload, compact
    if model_kind == "pauli_fierz_cavity_qed" and cavity_model is not None:
        cavity = to_primitive(cavity_model)
        observables = cavity.get("observables", {}) or {}
        payload = {
            "schema": SCHEMA,
            "artifact_kind": "field_constraints",
            "run_id": run_id,
            "model_kind": model_kind,
            "photon_physical_subspace": {
                "photon_encoding": cavity.get("photon_encoding"),
                "photon_physical_subspace_penalty": cavity.get("photon_physical_subspace_penalty"),
                "leakage": observables.get("photon_physical_subspace_leakage"),
            },
            "finite_photon_cutoff": {
                "max_occupation_by_mode": [
                    int(mode.get("max_occupation", 0)) for mode in list(cavity.get("modes", []) or [])
                ],
                "boundary": "configured_cutoff_only",
            },
        }
        compact = {
            "model_kind": model_kind,
            "photon_leakage": payload["photon_physical_subspace"]["leakage"],
            "finite_photon_cutoff": payload["finite_photon_cutoff"],
        }
        return payload, compact
    payload = {
        "schema": SCHEMA,
        "artifact_kind": "field_constraints",
        "run_id": run_id,
        "model_kind": model_kind,
        "available": False,
        "reason": "placeholder_or_missing_model_context",
    }
    return payload, {"available": False, "reason": payload["reason"]}


def _resources_payload(
    *,
    run_id: str,
    model_kind: str,
    field_model: Any | None,
    mapping: Any,
    qft_model: Any | None,
    cavity_model: Any | None,
    qft_dynamics: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    field = to_primitive(field_model) if field_model is not None else {}
    qft = to_primitive(qft_model) if qft_model is not None else {}
    cavity = to_primitive(cavity_model) if cavity_model is not None else {}
    dynamics = qft_dynamics or {}
    payload = {
        "schema": SCHEMA,
        "artifact_kind": "field_resources",
        "run_id": run_id,
        "model_kind": model_kind,
        "field_model_resource_estimate": field.get("resource_estimate", {}),
        "mapping_resources": {
            "num_qubits": getattr(mapping.summary, "num_qubits", None),
            "raw_num_qubits": getattr(mapping.summary, "raw_num_qubits", None),
            "qubit_term_count": getattr(mapping.summary, "qubit_term_count", None),
            "raw_qubit_term_count": getattr(mapping.summary, "raw_qubit_term_count", None),
        },
        "lattice_qed": {
            "matter_qubits": qft.get("matter_qubits"),
            "gauge_qubits": qft.get("gauge_qubits"),
            "total_qubits": qft.get("total_qubits"),
            "engine": qft.get("engine", {}),
        }
        if qft
        else None,
        "cavity_qed": {
            "electronic_qubits": cavity.get("electronic_qubits"),
            "photon_qubits": cavity.get("photon_qubits"),
            "total_qubits": cavity.get("total_qubits"),
            "mode_count": cavity.get("mode_count"),
        }
        if cavity
        else None,
        "dynamics_circuit_resources": ((dynamics.get("trotter") or {}).get("circuit_resources") or {}),
        "runtime_batch_preview": (dynamics.get("runtime_batch") or {}),
    }
    compact = {
        "model_kind": model_kind,
        "num_qubits": payload["mapping_resources"]["num_qubits"],
        "qubit_term_count": payload["mapping_resources"]["qubit_term_count"],
        "dynamics_max_depth": payload["dynamics_circuit_resources"].get("max_depth"),
        "dynamics_max_two_qubit_gate_count": payload["dynamics_circuit_resources"].get("max_two_qubit_gate_count"),
    }
    return payload, compact


def _error_budget_payload(
    *,
    run_id: str,
    model_kind: str,
    field_model: Any | None,
    benchmark: Any,
    qft_model: Any | None,
    qft_dynamics: dict[str, Any] | None,
    cavity_model: Any | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    field = to_primitive(field_model) if field_model is not None else {}
    qft = to_primitive(qft_model) if qft_model is not None else {}
    cavity = to_primitive(cavity_model) if cavity_model is not None else {}
    benchmark_payload = to_primitive(benchmark)
    dynamics = qft_dynamics or {}
    payload = {
        "schema": SCHEMA,
        "artifact_kind": "field_error_budget",
        "run_id": run_id,
        "model_kind": model_kind,
        "field_model_error_budget": field.get("error_budget", {}),
        "finite_cutoff": {
            "lattice_grid_shape": qft.get("grid_shape"),
            "lattice_grid_spacing": qft.get("grid_spacing"),
            "gauge_electric_cutoff": qft.get("gauge_electric_cutoff"),
            "photon_cutoff": (cavity.get("error_budget", {}) or {}).get("photon_cutoff") if cavity else None,
            "finite_cutoff_boundary": bool(qft or cavity),
        },
        "photon_cutoff": (cavity.get("error_budget", {}) or {}).get("photon_cutoff") if cavity else None,
        "trotter": {
            "error_summary": dynamics.get("trotter_error_summary"),
            "error_matrix": _observable_error_matrix(dynamics),
        },
        "ansatz": {
            "absolute_error_hartree": benchmark_payload.get("absolute_error"),
            "comparison_target": benchmark_payload.get("comparison_target"),
        },
        "photon_encoding": {
            "leakage": ((cavity.get("observables", {}) or {}).get("photon_physical_subspace_leakage") if cavity else None),
        },
        "placeholder_boundary": {
            "placeholder_models_registered": [
                key for key, adapter in FIELD_MODEL_REGISTRY.items() if adapter.capability_tier == "placeholder"
            ],
            "placeholder_claims_allowed": False,
        },
    }
    compact = {
        "model_kind": model_kind,
        "finite_cutoff_boundary": payload["finite_cutoff"]["finite_cutoff_boundary"],
        "ansatz_absolute_error_hartree": payload["ansatz"]["absolute_error_hartree"],
        "trotter_error_matrix_available": payload["trotter"]["error_matrix"].get("available"),
    }
    return payload, compact


def build_and_write_field_evidence(
    *,
    run_id: str,
    sidecar_paths: FieldArtifactPaths | None,
    mapping: Any,
    solver_outcome: Any,
    solver_energy: float | None,
    spectrum: Any | None,
    benchmark: Any,
    qft_context: Any | None,
    qft_dynamics: dict[str, Any] | None,
    cavity_context: Any | None,
    field_model: Any | None,
) -> FieldEvidenceSummary | None:
    """Build compact field evidence and write field-model sidecars."""
    active_model_kind = getattr(field_model, "model_kind", None) if field_model is not None else None
    if active_model_kind is None and qft_context is not None:
        active_model_kind = "lattice_qed"
    if active_model_kind is None and cavity_context is not None:
        active_model_kind = "pauli_fierz_cavity_qed"
    if active_model_kind is None:
        return None

    notes: list[str] = []
    registry_payload = _registry_payload(run_id, active_model_kind, field_model)
    if active_model_kind == "lattice_qed" and qft_context is not None:
        hamiltonian_payload, hamiltonian_summary, h_notes = _lattice_hamiltonian_payload(
            run_id=run_id,
            qft_context=qft_context,
            mapping=mapping,
            solver_energy=solver_energy,
            solver_outcome=solver_outcome,
            spectrum=spectrum,
        )
        observables_payload, observables_summary, o_notes = _lattice_observables_payload(
            run_id=run_id,
            qft_context=qft_context,
            solver_outcome=solver_outcome,
            spectrum=spectrum,
            qft_dynamics=qft_dynamics,
        )
        notes.extend(h_notes)
        notes.extend(o_notes)
    elif active_model_kind == "pauli_fierz_cavity_qed" and cavity_context is not None:
        hamiltonian_payload, hamiltonian_summary, h_notes = _cavity_hamiltonian_payload(
            run_id=run_id,
            cavity_context=cavity_context,
            mapping=mapping,
            solver_energy=solver_energy,
            solver_outcome=solver_outcome,
            spectrum=spectrum,
        )
        observables_payload, observables_summary = _cavity_observables_payload(run_id, cavity_context)
        notes.extend(h_notes)
    else:
        hamiltonian_payload = {
            "schema": SCHEMA,
            "artifact_kind": "field_hamiltonian",
            "run_id": run_id,
            "model_kind": active_model_kind,
            "implementation_status": "placeholder",
            "scientific_claim_allowed": False,
        }
        hamiltonian_summary = {"implementation_status": "placeholder"}
        observables_payload = {
            "schema": SCHEMA,
            "artifact_kind": "field_observables",
            "run_id": run_id,
            "model_kind": active_model_kind,
            "implementation_status": "placeholder",
            "scientific_claim_allowed": False,
        }
        observables_summary = {"implementation_status": "placeholder"}

    dynamics_payload, dynamics_summary = _dynamics_payload(run_id, active_model_kind, qft_dynamics)
    constraints_payload, constraints_summary = _constraints_payload(
        run_id=run_id,
        model_kind=active_model_kind,
        qft_model=getattr(qft_context, "summary", None) if qft_context is not None else None,
        cavity_model=getattr(cavity_context, "summary", None) if cavity_context is not None else None,
    )
    constraints_payload["sector_term_closure"] = hamiltonian_summary
    constraints_summary["sector_term_closure"] = hamiltonian_summary
    resources_payload, resources_summary = _resources_payload(
        run_id=run_id,
        model_kind=active_model_kind,
        field_model=field_model,
        mapping=mapping,
        qft_model=getattr(qft_context, "summary", None) if qft_context is not None else None,
        cavity_model=getattr(cavity_context, "summary", None) if cavity_context is not None else None,
        qft_dynamics=qft_dynamics,
    )
    error_payload, error_summary = _error_budget_payload(
        run_id=run_id,
        model_kind=active_model_kind,
        field_model=field_model,
        benchmark=benchmark,
        qft_model=getattr(qft_context, "summary", None) if qft_context is not None else None,
        qft_dynamics=qft_dynamics,
        cavity_model=getattr(cavity_context, "summary", None) if cavity_context is not None else None,
    )
    sidecars: dict[str, str] = {}
    hashes: dict[str, str] = {}
    if sidecar_paths is not None:
        payloads = {
            "registry": (sidecar_paths.registry_json, registry_payload),
            "hamiltonian": (sidecar_paths.hamiltonian_json, hamiltonian_payload),
            "observables": (sidecar_paths.observables_json, observables_payload),
            "dynamics": (sidecar_paths.dynamics_json, dynamics_payload),
            "constraints": (sidecar_paths.constraints_json, constraints_payload),
            "resources": (sidecar_paths.resources_json, resources_payload),
            "error_budget": (sidecar_paths.error_budget_json, error_payload),
        }
        for key, (path, payload) in payloads.items():
            hashes[key] = _write_sidecar(path, payload)
            sidecars[key] = str(path)

    return FieldEvidenceSummary(
        available=True,
        schema=SCHEMA,
        active_model_kind=active_model_kind,
        sidecars=sidecars,
        sidecar_sha256=hashes,
        hamiltonian=hamiltonian_summary,
        observables=observables_summary,
        dynamics=dynamics_summary,
        constraints=constraints_summary,
        resources=resources_summary,
        error_budget=error_summary,
        notes=sorted(set(notes)),
    )
