"""Real-time dynamics for exploratory finite-cutoff lattice-QED models."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import scipy.sparse as sp
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import HamiltonianGate
from qiskit.quantum_info import SparsePauliOp
from scipy.sparse.linalg import expm_multiply

from qcchem.backends.runtime_batch import attempt_runtime_batch_submission
from qcchem.core import BackendSpec, LatticeQEDSpec
from qcchem.qft.lattice_qed import LatticeQEDContext
from qcchem.qft.lattice_qed import (
    _embed_matter_link,
    _embed_matter_link_sparse,
    _fermion_annihilation,
    _fermion_annihilation_sparse,
    _fermion_creation,
    _fermion_creation_sparse,
    _mode_index,
)
from qcchem.qft.links import matrix_to_sparse_pauli
from qcchem.qft.observables import (
    QFTObservableMatrices,
    build_qft_observable_matrices,
    expectation_value,
)

_SECTOR_ORDER = [
    "onsite",
    "hopping",
    "density_coulomb",
    "electric",
    "magnetic_plaquette",
    "gauss_law_penalty",
    "particle_number_penalty",
    "padding_penalty",
]


def _time_points(spec: LatticeQEDSpec) -> list[float]:
    grid = spec.dynamics.time_grid
    return [
        float(value)
        for value in np.linspace(float(grid.start), float(grid.stop), int(grid.num_points))
    ]


def _basis_state(dimension: int, basis_index: int | None) -> np.ndarray:
    if basis_index is None:
        basis_index = 0
    state = np.zeros(dimension, dtype=complex)
    state[int(basis_index)] = 1.0 + 0.0j
    return state


def _reference_basis_index(context: LatticeQEDContext) -> int | None:
    return context.summary.physical_sector.get("reference_basis_index")


def _sector_sequence(context: LatticeQEDContext) -> list[tuple[str, np.ndarray]]:
    sequence: list[tuple[str, np.ndarray]] = []
    if context.sparse_bundle is not None:
        sectors = (
            context.sparse_bundle.projected_sector_matrices
            if context.sparse_bundle.projected_hamiltonian is not None
            else context.sparse_bundle.sector_matrices
        )
        for name in _SECTOR_ORDER:
            matrix = sectors.get(name)
            if matrix is not None and matrix.nnz:
                sequence.append((name, matrix))
        return sequence
    for name in _SECTOR_ORDER:
        matrix = context.sector_matrices.get(name)
        if matrix is not None and not np.allclose(matrix, 0.0, atol=1.0e-12):
            sequence.append((name, matrix))
    return sequence


def _dynamics_dimension(context: LatticeQEDContext) -> int:
    if context.sparse_bundle is not None and context.sparse_bundle.projected_hamiltonian is not None:
        return int(context.sparse_bundle.projected_hamiltonian.shape[0])
    if context.sparse_bundle is not None:
        return int(context.sparse_bundle.full_hamiltonian.shape[0])
    return int(context.hamiltonian_matrix.shape[0])


def _reference_state_index(context: LatticeQEDContext) -> int | None:
    reference = _reference_basis_index(context)
    if reference is None:
        return None
    if context.sparse_bundle is None or context.sparse_bundle.projected_hamiltonian is None:
        return int(reference)
    matches = np.where(context.sparse_bundle.physical_indices == int(reference))[0]
    return int(matches[0]) if len(matches) else None


def _local_hopping_pulse_matrix(context: LatticeQEDContext, spec: LatticeQEDSpec) -> np.ndarray:
    initial = spec.dynamics.initial_state
    if initial.kind.strip().lower() != "local_hopping_pulse":
        raise ValueError("problem.qft.dynamics.initial_state.kind currently supports local_hopping_pulse.")
    if initial.base.strip().lower() != "physical_reference":
        raise ValueError("problem.qft.dynamics.initial_state.base currently supports physical_reference.")
    link_index = int(initial.link_index)
    if link_index < 0 or link_index >= len(context.grid.links):
        raise ValueError("problem.qft.dynamics.initial_state.link_index is outside the grid link range.")

    link = context.grid.links[link_index]
    spin_components = int(context.summary.matter_mode_count // context.summary.site_count)
    matter_modes = int(context.summary.matter_mode_count)
    if context.sparse_bundle is not None:
        creation_ops = [_fermion_creation_sparse(mode, matter_modes) for mode in range(matter_modes)]
        annihilation_ops = [_fermion_annihilation_sparse(mode, matter_modes) for mode in range(matter_modes)]
        dimension = int(context.sparse_bundle.full_hamiltonian.shape[0])
        pulse = sp.csr_matrix((dimension, dimension), dtype=complex)
        spacing = float(context.grid.spacing[link.direction])
        hopping_strength = float(initial.pulse_strength) / (2.0 * spacing**2)
        for spin in range(spin_components):
            start_mode = _mode_index(link.start_site, spin, spin_components)
            end_mode = _mode_index(link.end_site, spin, spin_components)
            forward = creation_ops[end_mode] @ annihilation_ops[start_mode]
            backward = creation_ops[start_mode] @ annihilation_ops[end_mode]
            pulse += -hopping_strength * _embed_matter_link_sparse(
                forward,
                context.link_operator.raising_matrix,
                link_index=link.linear_index,
                link_count=len(context.grid.links),
                encoded_dimension=context.link_operator.encoded_dimension,
            )
            pulse += -hopping_strength * _embed_matter_link_sparse(
                backward,
                context.link_operator.lowering_matrix,
                link_index=link.linear_index,
                link_count=len(context.grid.links),
                encoded_dimension=context.link_operator.encoded_dimension,
            )
        pulse = (0.5 * (pulse + pulse.conj().T)).tocsr()
        if context.sparse_bundle.projected_hamiltonian is not None:
            indices = context.sparse_bundle.physical_indices
            pulse = pulse[indices, :][:, indices].tocsr()
        return pulse
    creation_ops = [_fermion_creation(mode, matter_modes) for mode in range(matter_modes)]
    annihilation_ops = [_fermion_annihilation(mode, matter_modes) for mode in range(matter_modes)]
    pulse = np.zeros_like(context.hamiltonian_matrix, dtype=complex)
    spacing = float(context.grid.spacing[link.direction])
    hopping_strength = float(initial.pulse_strength) / (2.0 * spacing**2)
    for spin in range(spin_components):
        start_mode = _mode_index(link.start_site, spin, spin_components)
        end_mode = _mode_index(link.end_site, spin, spin_components)
        forward = creation_ops[end_mode] @ annihilation_ops[start_mode]
        backward = creation_ops[start_mode] @ annihilation_ops[end_mode]
        pulse += -hopping_strength * _embed_matter_link(
            forward,
            context.link_operator.raising_matrix,
            link_index=link.linear_index,
            link_count=len(context.grid.links),
            encoded_dimension=context.link_operator.encoded_dimension,
        )
        pulse += -hopping_strength * _embed_matter_link(
            backward,
            context.link_operator.lowering_matrix,
            link_index=link.linear_index,
            link_count=len(context.grid.links),
            encoded_dimension=context.link_operator.encoded_dimension,
        )
    return 0.5 * (pulse + pulse.conj().T)


def _prepare_quench_state(context: LatticeQEDContext, spec: LatticeQEDSpec) -> tuple[np.ndarray, dict[str, Any], np.ndarray]:
    reference_index = _reference_state_index(context)
    reference = _basis_state(_dynamics_dimension(context), reference_index)
    pulse = _local_hopping_pulse_matrix(context, spec)
    pulse_time = float(spec.dynamics.initial_state.pulse_time)
    state = expm_multiply((-1.0j * pulse_time) * sp.csr_matrix(pulse), reference)
    norm = float(np.linalg.norm(state))
    if norm > 0.0:
        state = state / norm
    return (
        np.asarray(state, dtype=complex),
        {
            "kind": spec.dynamics.initial_state.kind,
            "base": spec.dynamics.initial_state.base,
            "reference_basis_index": _reference_basis_index(context),
            "evolution_reference_index": reference_index,
            "link_index": int(spec.dynamics.initial_state.link_index),
            "pulse_time": pulse_time,
            "pulse_strength": float(spec.dynamics.initial_state.pulse_strength),
            "post_pulse_state_norm": float(np.linalg.norm(state)),
        },
        pulse,
    )


def _empty_observable_curves(observables: QFTObservableMatrices) -> dict[str, Any]:
    return {
        "particle_number": [],
        "total_electric_energy": [],
        "total_gauss_violation": [],
        "loschmidt_echo": [],
        "total_wilson": [],
        "matter_density_by_site": [[] for _ in observables.site_density],
        "link_electric_flux": [[] for _ in observables.link_electric_flux],
        "link_electric_energy": [[] for _ in observables.link_electric_energy],
        "gauss_residual_by_site": [[] for _ in observables.gauss_residual],
        "plaquette_wilson": [[] for _ in observables.plaquette_wilson],
    }


def _append_observables(
    curves: dict[str, Any],
    observables: QFTObservableMatrices,
    state: np.ndarray,
    reference_state: np.ndarray,
) -> None:
    curves["particle_number"].append(expectation_value(observables.aggregate["particle_number"], state))
    curves["total_electric_energy"].append(expectation_value(observables.aggregate["total_electric_energy"], state))
    curves["total_gauss_violation"].append(expectation_value(observables.aggregate["total_gauss_violation"], state))
    curves["total_wilson"].append(expectation_value(observables.aggregate["total_wilson"], state))
    curves["loschmidt_echo"].append(float(abs(np.vdot(reference_state, state)) ** 2))
    for target, matrix in zip(curves["matter_density_by_site"], observables.site_density):
        target.append(expectation_value(matrix, state))
    for target, matrix in zip(curves["link_electric_flux"], observables.link_electric_flux):
        target.append(expectation_value(matrix, state))
    for target, matrix in zip(curves["link_electric_energy"], observables.link_electric_energy):
        target.append(expectation_value(matrix, state))
    for target, matrix in zip(curves["gauss_residual_by_site"], observables.gauss_residual):
        target.append(expectation_value(matrix, state))
    for target, matrix in zip(curves["plaquette_wilson"], observables.plaquette_wilson):
        target.append(expectation_value(matrix, state))


def _exact_dynamics(
    context: LatticeQEDContext,
    spec: LatticeQEDSpec,
    initial_state: np.ndarray,
    observables: QFTObservableMatrices,
    times: list[float],
) -> dict[str, Any]:
    if not spec.dynamics.evolution.exact_enabled:
        return {"available": False, "skipped_reason": "exact_disabled", "time_points": [], "observables": {}}
    if context.summary.total_qubits > int(spec.dynamics.evolution.exact_qubit_limit):
        return {
            "available": False,
            "skipped_reason": "total_qubits_exceeds_exact_qubit_limit",
            "time_points": [],
            "observables": {},
        }
    if context.sparse_bundle is not None:
        if context.sparse_bundle.projected_hamiltonian is not None:
            hamiltonian = context.sparse_bundle.projected_hamiltonian
            evolution_space = "physical_sector"
            physical_sector_dimension = int(hamiltonian.shape[0])
            states = expm_multiply(
                -1.0j * hamiltonian,
                initial_state,
                start=float(times[0]),
                stop=float(times[-1]),
                num=len(times),
                endpoint=True,
            )
        else:
            hamiltonian = context.sparse_bundle.full_hamiltonian
            evolution_space = "full_hilbert_space"
            physical_sector_dimension = None
            states = expm_multiply(
                -1.0j * hamiltonian,
                initial_state,
                start=float(times[0]),
                stop=float(times[-1]),
                num=len(times),
                endpoint=True,
            )
        curves = _empty_observable_curves(observables)
        state_norms: list[float] = []
        for state in states:
            vector = np.asarray(state, dtype=complex)
            state_norms.append(float(np.linalg.norm(vector)))
            _append_observables(curves, observables, vector, initial_state)
        return {
            "available": True,
            "skipped_reason": None,
            "time_points": list(times),
            "state_norms": state_norms,
            "observables": curves,
            "evolution_space": evolution_space,
            "physical_sector_dimension": physical_sector_dimension,
            "projected_dimension": physical_sector_dimension,
            "operator_representation": context.summary.engine.get("actual_representation"),
        }

    physical_indices = context.summary.physical_sector.get("basis_indices")
    use_physical_sector = (
        bool(spec.constraints.enforce_physical_sector)
        and isinstance(physical_indices, list)
        and len(physical_indices) > 0
        and len(physical_indices) < context.hamiltonian_matrix.shape[0]
    )
    embedded_states = None
    evolution_space = "full_hilbert_space"
    physical_sector_dimension = None
    if use_physical_sector:
        indices = np.asarray([int(value) for value in physical_indices], dtype=int)
        reduced_initial = np.asarray(initial_state[indices], dtype=complex)
        reduced_norm = float(np.linalg.norm(reduced_initial))
        if reduced_norm <= 1.0e-12:
            return {
                "available": False,
                "skipped_reason": "initial_state_has_no_physical_sector_support",
                "time_points": [],
                "observables": {},
            }
        reduced_initial = reduced_initial / reduced_norm
        hamiltonian = sp.csr_matrix(context.hamiltonian_matrix[np.ix_(indices, indices)])
        reduced_states = expm_multiply(
            -1.0j * hamiltonian,
            reduced_initial,
            start=float(times[0]),
            stop=float(times[-1]),
            num=len(times),
            endpoint=True,
        )
        embedded_states = []
        for reduced_state in reduced_states:
            full_state = np.zeros_like(initial_state, dtype=complex)
            full_state[indices] = np.asarray(reduced_state, dtype=complex)
            embedded_states.append(full_state)
        states = embedded_states
        evolution_space = "physical_sector"
        physical_sector_dimension = int(len(indices))
    else:
        hamiltonian = sp.csr_matrix(context.hamiltonian_matrix)
        states = expm_multiply(
            -1.0j * hamiltonian,
            initial_state,
            start=float(times[0]),
            stop=float(times[-1]),
            num=len(times),
            endpoint=True,
        )
    curves = _empty_observable_curves(observables)
    state_norms: list[float] = []
    for state in states:
        vector = np.asarray(state, dtype=complex)
        state_norms.append(float(np.linalg.norm(vector)))
        _append_observables(curves, observables, vector, initial_state)
    return {
        "available": True,
        "skipped_reason": None,
        "time_points": list(times),
        "state_norms": state_norms,
        "observables": curves,
        "evolution_space": evolution_space,
        "physical_sector_dimension": physical_sector_dimension,
        "projected_dimension": physical_sector_dimension,
        "operator_representation": context.summary.engine.get("actual_representation", "dense_full"),
    }


def _trotter_state(
    context: LatticeQEDContext,
    initial_state: np.ndarray,
    *,
    time: float,
    step: float,
) -> np.ndarray:
    if abs(time) <= 1.0e-15:
        return np.asarray(initial_state, dtype=complex)
    sequence = [(name, sp.csr_matrix(matrix)) for name, matrix in _sector_sequence(context)]
    step_count = max(int(np.ceil(abs(float(time)) / float(step))), 1)
    dt = float(time) / float(step_count)
    state = np.asarray(initial_state, dtype=complex)
    for _ in range(step_count):
        for _, matrix in sequence:
            state = expm_multiply((-1.0j * dt) * matrix, state)
    norm = float(np.linalg.norm(state))
    return state / norm if norm > 0.0 else state


def _trotter_dynamics(
    context: LatticeQEDContext,
    spec: LatticeQEDSpec,
    initial_state: np.ndarray,
    observables: QFTObservableMatrices,
    times: list[float],
) -> dict[str, Any]:
    if not spec.dynamics.evolution.trotter_enabled:
        return {"available": False, "skipped_reason": "trotter_disabled", "time_points": [], "observables": {}}
    curves = _empty_observable_curves(observables)
    state_norms: list[float] = []
    step = float(spec.dynamics.evolution.trotter_step)
    for time in times:
        state = _trotter_state(context, initial_state, time=float(time), step=step)
        state_norms.append(float(np.linalg.norm(state)))
        _append_observables(curves, observables, state, initial_state)
    resources = _trotter_circuit_resources(context, spec, times)
    return {
        "available": True,
        "skipped_reason": None,
        "time_points": list(times),
        "state_norms": state_norms,
        "observables": curves,
        "circuit_resources": resources,
    }


def _max_abs_error(left: list[float], right: list[float]) -> float | None:
    if not left or not right or len(left) != len(right):
        return None
    return float(max(abs(float(a) - float(b)) for a, b in zip(left, right)))


def _trotter_error_summary(exact: dict[str, Any], trotter: dict[str, Any]) -> dict[str, Any]:
    if not exact.get("available") or not trotter.get("available"):
        return {"available": False, "skipped_reason": "exact_or_trotter_unavailable"}
    exact_obs = exact.get("observables") or {}
    trotter_obs = trotter.get("observables") or {}
    return {
        "available": True,
        "max_loschmidt_abs_error": _max_abs_error(
            exact_obs.get("loschmidt_echo", []),
            trotter_obs.get("loschmidt_echo", []),
        ),
        "max_particle_number_abs_error": _max_abs_error(
            exact_obs.get("particle_number", []),
            trotter_obs.get("particle_number", []),
        ),
        "max_total_gauss_violation_abs_error": _max_abs_error(
            exact_obs.get("total_gauss_violation", []),
            trotter_obs.get("total_gauss_violation", []),
        ),
    }


def _append_initial_state(circuit: QuantumCircuit, reference_index: int | None) -> None:
    if reference_index is None:
        return
    for qubit in range(circuit.num_qubits):
        if (int(reference_index) >> qubit) & 1:
            circuit.x(qubit)


def _append_evolution_gate(
    circuit: QuantumCircuit,
    matrix: np.ndarray,
    *,
    time: float,
    name: str,
    unitary_gates: bool,
) -> None:
    if unitary_gates:
        circuit.append(HamiltonianGate(matrix, time=float(time)), range(circuit.num_qubits))
    else:
        circuit.append(Gate(name=name[:32], num_qubits=circuit.num_qubits, params=[]), range(circuit.num_qubits))


def build_trotter_circuit(
    context: LatticeQEDContext,
    spec: LatticeQEDSpec,
    *,
    time: float,
    unitary_gates: bool = False,
) -> QuantumCircuit:
    """Build a logical first-order Trotter circuit for one dynamics time point."""
    circuit = QuantumCircuit(context.summary.total_qubits)
    _append_initial_state(circuit, _reference_basis_index(context))
    pulse = _local_hopping_pulse_matrix(context, spec)
    _append_evolution_gate(
        circuit,
        pulse,
        time=float(spec.dynamics.initial_state.pulse_time),
        name="qft_pulse",
        unitary_gates=unitary_gates,
    )
    if abs(time) <= 1.0e-15:
        return circuit
    step = float(spec.dynamics.evolution.trotter_step)
    step_count = max(int(np.ceil(abs(float(time)) / step)), 1)
    dt = float(time) / float(step_count)
    for _ in range(step_count):
        for sector_name, matrix in _sector_sequence(context):
            _append_evolution_gate(
                circuit,
                matrix,
                time=dt,
                name=f"qft_{sector_name}",
                unitary_gates=unitary_gates,
            )
    return circuit


def _trotter_circuit_resources(
    context: LatticeQEDContext,
    spec: LatticeQEDSpec,
    times: list[float],
) -> dict[str, Any]:
    per_time_point: list[dict[str, Any]] = []
    for time in times:
        circuit = build_trotter_circuit(context, spec, time=float(time), unitary_gates=False)
        counts = circuit.count_ops()
        per_time_point.append(
            {
                "time": float(time),
                "depth": int(circuit.depth()) if circuit.depth() is not None else 0,
                "operation_count": int(sum(counts.values())),
                "two_qubit_gate_count": int(sum(int(counts.get(name, 0)) for name in ("cx", "cz", "ecr"))),
            }
        )
    return {
        "time_point_count": len(per_time_point),
        "max_depth": max((item["depth"] for item in per_time_point), default=0),
        "max_operation_count": max((item["operation_count"] for item in per_time_point), default=0),
        "max_two_qubit_gate_count": max((item["two_qubit_gate_count"] for item in per_time_point), default=0),
        "per_time_point": per_time_point,
        "trotter_step": float(spec.dynamics.evolution.trotter_step),
        "trotter_order": int(spec.dynamics.evolution.trotter_order),
    }


def _projector_sparse_pauli(state: np.ndarray) -> SparsePauliOp:
    projector = np.outer(state, state.conj())
    return matrix_to_sparse_pauli(projector, atol=1.0e-10).simplify(atol=1.0e-10)


def _runtime_operators(
    observables: QFTObservableMatrices,
    initial_state: np.ndarray,
) -> dict[str, SparsePauliOp]:
    operators = {
        "particle_number": matrix_to_sparse_pauli(
            observables.aggregate["particle_number"].toarray(),
            atol=1.0e-10,
        ),
        "total_electric_energy": matrix_to_sparse_pauli(
            observables.aggregate["total_electric_energy"].toarray(),
            atol=1.0e-10,
        ),
        "total_gauss_violation": matrix_to_sparse_pauli(
            observables.aggregate["total_gauss_violation"].toarray(),
            atol=1.0e-10,
        ),
        "loschmidt_echo": _projector_sparse_pauli(initial_state),
    }
    if observables.metadata.get("plaquette_wilson_count", 0) > 0:
        operators["total_wilson"] = matrix_to_sparse_pauli(
            observables.aggregate["total_wilson"].toarray(),
            atol=1.0e-10,
        )
    return {name: op.simplify(atol=1.0e-10) for name, op in operators.items()}


def _runtime_batch(
    context: LatticeQEDContext,
    spec: LatticeQEDSpec,
    backend_spec: BackendSpec | None,
    observables: QFTObservableMatrices,
    initial_state: np.ndarray,
    times: list[float],
) -> dict[str, Any] | None:
    if not spec.dynamics.runtime.enabled:
        return None
    if backend_spec is None:
        return {
            "attempted": False,
            "submitted": False,
            "succeeded": False,
            "failure_category": "backend_spec_unavailable",
            "pub_count": 0,
            "observable_policy": spec.dynamics.runtime.runtime_observables,
        }
    submit_real_job = bool(backend_spec.runtime.options.get("submit_real_job", False))
    operators = _runtime_operators(observables, initial_state)
    pubs: list[dict[str, Any]] = []
    for time in times:
        circuit = build_trotter_circuit(
            context,
            spec,
            time=float(time),
            unitary_gates=submit_real_job,
        )
        for observable_name, operator in operators.items():
            pubs.append(
                {
                    "time": float(time),
                    "observable": observable_name,
                    "circuit": circuit,
                    "operator": operator,
                    "parameter_values": [],
                }
            )
    return attempt_runtime_batch_submission(
        spec=backend_spec,
        pubs=pubs,
        observable_policy=spec.dynamics.runtime.runtime_observables,
    )


def build_lattice_qed_dynamics(
    context: LatticeQEDContext,
    spec: LatticeQEDSpec,
    *,
    backend_spec: BackendSpec | None = None,
) -> dict[str, Any] | None:
    """Build exact, Trotter, and guarded-runtime QFT dynamics metadata."""
    if not spec.dynamics.enabled:
        return None
    if spec.dynamics.method.strip().lower() != "real_time_quench":
        raise ValueError("problem.qft.dynamics.method currently supports real_time_quench.")
    times = _time_points(spec)
    observables = build_qft_observable_matrices(context)
    initial_state, quench_metadata, _ = _prepare_quench_state(context, spec)
    exact = _exact_dynamics(context, spec, initial_state, observables, times)
    trotter = _trotter_dynamics(context, spec, initial_state, observables, times)
    runtime_batch = _runtime_batch(
        context,
        spec,
        backend_spec,
        observables,
        initial_state,
        times,
    )
    return {
        "enabled": True,
        "method": spec.dynamics.method,
        "quench": quench_metadata,
        "time_grid": asdict(spec.dynamics.time_grid),
        "evolution": asdict(spec.dynamics.evolution),
        "observables": dict(observables.metadata),
        "exact": exact,
        "trotter": trotter,
        "trotter_error_summary": _trotter_error_summary(exact, trotter),
        "runtime_batch": runtime_batch,
        "notes": [
            "Exploratory finite-cutoff lattice-QED real-time dynamics.",
            "Exact curves and Trotter curves are for the same finite Hamiltonian.",
            "Runtime batch submissions are guarded by backend.runtime.options.submit_real_job.",
        ],
    }
