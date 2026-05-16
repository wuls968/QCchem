"""Pauli-Fierz cavity-QED field-model builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.mappers import BosonicLinearMapper
from qiskit_nature.second_q.operators import BosonicOp

from qcchem.core import CavityQEDModelSummary, CavityQEDSpec
from qcchem.mapping import MappedHamiltonian
from qcchem.solvers.spectrum import ExactSpectrum

HAMILTONIAN_FORMULA = (
    "H = H_e + sum_m omega_m a_m^dagger a_m + "
    "sum_m g_m (e_m dot mu)(a_m + a_m^dagger) + "
    "1/2 sum_m g_m^2 (e_m dot mu)^2"
)


@dataclass(slots=True)
class CavityQEDContext:
    """Pauli-Fierz qubit Hamiltonian and observable operators."""

    qubit_hamiltonian: SparsePauliOp
    summary: CavityQEDModelSummary
    photon_hamiltonian: SparsePauliOp
    photon_number_operators: list[SparsePauliOp]
    photon_leakage_operator: SparsePauliOp
    dipole_operators: list[SparsePauliOp]
    coupling_energy_operators: list[SparsePauliOp]
    dipole_self_energy_operators: list[SparsePauliOp]
    electronic_qubits: int
    photon_qubits: int
    photon_mode_qubits: list[int]


def _identity(num_qubits: int) -> SparsePauliOp:
    return SparsePauliOp.from_list([("I" * num_qubits, 1.0)])


def _zero(num_qubits: int) -> SparsePauliOp:
    return SparsePauliOp.from_list([("I" * num_qubits, 0.0)])


def _sum_ops(ops: list[SparsePauliOp], *, num_qubits: int) -> SparsePauliOp:
    total = _zero(num_qubits)
    for op in ops:
        total = total + op
    return total.simplify(atol=1.0e-12)


def _tensor_all(ops: list[SparsePauliOp]) -> SparsePauliOp:
    if not ops:
        raise ValueError("Cannot tensor an empty operator list.")
    total = ops[0]
    for op in ops[1:]:
        total = total.tensor(op)
    return total.simplify(atol=1.0e-12)


def _embed_mode_operator(
    mode_op: SparsePauliOp,
    *,
    mode_index: int,
    mode_qubits: list[int],
) -> SparsePauliOp:
    ops = [
        mode_op if index == mode_index else _identity(qubits)
        for index, qubits in enumerate(mode_qubits)
    ]
    return _tensor_all(ops)


def _embed_electronic(op: SparsePauliOp, photon_qubits: int) -> SparsePauliOp:
    return op.tensor(_identity(photon_qubits)).simplify(atol=1.0e-12)


def _embed_photon(op: SparsePauliOp, electronic_qubits: int) -> SparsePauliOp:
    return _identity(electronic_qubits).tensor(op).simplify(atol=1.0e-12)


def _normalize(vector: list[float]) -> np.ndarray:
    values = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(values))
    if norm <= 1.0e-12:
        raise ValueError("Cavity-QED mode polarization must be non-zero.")
    return values / norm


def _photon_mode_ops(max_occupation: int) -> tuple[SparsePauliOp, SparsePauliOp]:
    mapper = BosonicLinearMapper(max_occupation=max_occupation)
    number = mapper.map(BosonicOp({"+_0 -_0": 1.0}, num_modes=1)).simplify(atol=1.0e-12)
    displacement = mapper.map(BosonicOp({"+_0": 1.0, "-_0": 1.0}, num_modes=1)).simplify(atol=1.0e-12)
    return number, displacement


def _single_qubit_occupation_projector(qubit_index: int, num_qubits: int) -> SparsePauliOp:
    z_label = ["I"] * num_qubits
    z_label[num_qubits - qubit_index - 1] = "Z"
    return 0.5 * (
        SparsePauliOp.from_list([("I" * num_qubits, 1.0)])
        - SparsePauliOp.from_list([("".join(z_label), 1.0)])
    )


def _physical_subspace_penalty(num_qubits: int) -> SparsePauliOp:
    number_sum = _sum_ops(
        [_single_qubit_occupation_projector(index, num_qubits) for index in range(num_qubits)],
        num_qubits=num_qubits,
    )
    deviation = number_sum - _identity(num_qubits)
    return deviation.compose(deviation).simplify(atol=1.0e-12)


def _dipole_component_ops(chemistry, mapping: MappedHamiltonian) -> dict[str, SparsePauliOp]:
    dipole_property = getattr(chemistry.problem.properties, "electronic_dipole_moment", None)
    if dipole_property is None:
        raise ValueError("Pauli-Fierz cavity-QED requires an electronic dipole property from the chemistry context.")
    fermionic_ops = dipole_property.second_q_ops()
    nuclear = np.asarray(dipole_property.nuclear_dipole_moment, dtype=float)
    identity = _identity(mapping.summary.num_qubits)
    components: dict[str, SparsePauliOp] = {}
    for axis, op_name, nuclear_value in (
        ("x", "XDipole", nuclear[0]),
        ("y", "YDipole", nuclear[1]),
        ("z", "ZDipole", nuclear[2]),
    ):
        electronic = mapping.mapper.map(fermionic_ops[op_name])
        if getattr(dipole_property, "reverse_dipole_sign", True):
            components[axis] = (float(nuclear_value) * identity - electronic).simplify(atol=1.0e-12)
        else:
            components[axis] = (float(nuclear_value) * identity + electronic).simplify(atol=1.0e-12)
    return components


def _polarized_dipole(dipole_components: dict[str, SparsePauliOp], polarization: np.ndarray) -> SparsePauliOp:
    terms = [
        float(polarization[0]) * dipole_components["x"],
        float(polarization[1]) * dipole_components["y"],
        float(polarization[2]) * dipole_components["z"],
    ]
    return _sum_ops(terms, num_qubits=dipole_components["x"].num_qubits)


def _expectation(operator: SparsePauliOp, statevector: np.ndarray) -> float:
    matrix = operator.to_matrix(sparse=True)
    return float(np.real_if_close(np.vdot(statevector, matrix @ statevector)))


def _residual_norm(operator: SparsePauliOp, statevector: np.ndarray, energy: float) -> float:
    matrix = operator.to_matrix(sparse=True)
    return float(np.linalg.norm(matrix @ statevector - float(energy) * statevector))


def _decompose_photon_index(photon_index: int, mode_qubits: list[int]) -> list[int]:
    local_indices: list[int] = []
    remaining = int(photon_index)
    mode_dimensions = [2 ** int(qubits) for qubits in mode_qubits]
    for mode_index, dimension in enumerate(mode_dimensions):
        trailing = int(np.prod(mode_dimensions[mode_index + 1 :], dtype=int)) if mode_index + 1 < len(mode_dimensions) else 1
        local = remaining // trailing
        remaining %= trailing
        local_indices.append(int(local % dimension))
    return local_indices


def _photon_occupation_weights(
    statevector: np.ndarray,
    *,
    electronic_qubits: int,
    mode_qubits: list[int],
) -> list[dict[str, Any]]:
    if not mode_qubits:
        return []
    electronic_dimension = 2 ** int(electronic_qubits)
    photon_dimension = 2 ** int(sum(mode_qubits))
    reshaped = np.asarray(statevector, dtype=complex).reshape(electronic_dimension, photon_dimension)
    photon_probabilities = np.sum(np.abs(reshaped) ** 2, axis=0)
    weights: dict[tuple[int, int], float] = {
        (mode_index, occupation): 0.0
        for mode_index, qubits in enumerate(mode_qubits)
        for occupation in range(int(qubits))
    }
    leakage_weight = 0.0
    for photon_index, probability in enumerate(photon_probabilities):
        local_indices = _decompose_photon_index(photon_index, mode_qubits)
        for mode_index, local_index in enumerate(local_indices):
            if local_index > 0 and local_index & (local_index - 1) == 0:
                occupation = int(np.log2(local_index))
                weights[(mode_index, occupation)] += float(probability)
            else:
                leakage_weight += float(probability) / float(len(mode_qubits))
    payload = [
        {
            "component": "electronic_marginal_x_photon_occupation",
            "mode_index": int(mode_index),
            "occupation": int(occupation),
            "max_occupation": int(mode_qubits[mode_index] - 1),
            "weight": float(weight),
        }
        for (mode_index, occupation), weight in sorted(weights.items())
    ]
    if leakage_weight > 1.0e-12:
        payload.append(
            {
                "component": "photon_encoding_leakage_marginal",
                "mode_index": None,
                "occupation": None,
                "max_occupation": None,
                "weight": float(leakage_weight),
            }
        )
    return payload


def build_cavity_qed_context(
    spec,
    chemistry,
    mapping: MappedHamiltonian,
) -> CavityQEDContext:
    """Build a finite-cutoff molecular Pauli-Fierz qubit Hamiltonian."""
    cavity: CavityQEDSpec = spec.problem.cavity_qed
    if cavity.model.strip().lower() != "pauli_fierz_cavity_qed":
        raise ValueError(f"Unsupported cavity-QED model: {cavity.model}")
    if cavity.photon_encoding.strip().lower() != "linear":
        raise ValueError("Pauli-Fierz cavity-QED currently supports photon_encoding='linear'.")
    if spec.solver.ansatz.kind.strip().lower() in {"uccsd", "puccd", "puccsd", "succd"}:
        raise ValueError("Chemistry-only ansatzes are not valid for electron-photon cavity-QED runs.")

    electronic_qubits = int(mapping.summary.num_qubits)
    mode_qubits = [int(mode.max_occupation) + 1 for mode in cavity.modes]
    photon_qubits = int(sum(mode_qubits))
    photon_identity = _identity(photon_qubits)
    electronic_identity = _identity(electronic_qubits)

    photon_terms: list[SparsePauliOp] = []
    photon_number_ops: list[SparsePauliOp] = []
    displacement_ops: list[SparsePauliOp] = []
    leakage_terms: list[SparsePauliOp] = []
    for mode_index, mode in enumerate(cavity.modes):
        local_number, local_displacement = _photon_mode_ops(int(mode.max_occupation))
        number_op = _embed_mode_operator(
            local_number,
            mode_index=mode_index,
            mode_qubits=mode_qubits,
        )
        displacement_op = _embed_mode_operator(
            local_displacement,
            mode_index=mode_index,
            mode_qubits=mode_qubits,
        )
        leakage_op = _embed_mode_operator(
            _physical_subspace_penalty(mode_qubits[mode_index]),
            mode_index=mode_index,
            mode_qubits=mode_qubits,
        )
        photon_number_ops.append(number_op)
        displacement_ops.append(displacement_op)
        leakage_terms.append(leakage_op)
        photon_terms.append(float(mode.frequency) * number_op)
    photon_leakage = _sum_ops(leakage_terms, num_qubits=photon_qubits)
    if cavity.photon_physical_subspace_penalty > 0.0:
        photon_terms.append(float(cavity.photon_physical_subspace_penalty) * photon_leakage)
    photon_hamiltonian = _sum_ops(photon_terms, num_qubits=photon_qubits)

    dipole_components = _dipole_component_ops(chemistry, mapping)
    coupling_terms: list[SparsePauliOp] = []
    dse_terms: list[SparsePauliOp] = []
    full_dipoles: list[SparsePauliOp] = []
    full_numbers: list[SparsePauliOp] = []
    full_couplings: list[SparsePauliOp] = []
    full_dse: list[SparsePauliOp] = []
    for mode, displacement_op, number_op in zip(cavity.modes, displacement_ops, photon_number_ops):
        polarization = _normalize(mode.polarization)
        dipole = _polarized_dipole(dipole_components, polarization)
        coupling = float(mode.coupling_strength) * dipole.tensor(displacement_op)
        coupling_terms.append(coupling)
        full_dipoles.append(dipole.tensor(photon_identity).simplify(atol=1.0e-12))
        full_numbers.append(electronic_identity.tensor(number_op).simplify(atol=1.0e-12))
        full_couplings.append(coupling.simplify(atol=1.0e-12))
        if cavity.include_dipole_self_energy:
            dse = 0.5 * float(mode.coupling_strength) ** 2 * dipole.compose(dipole)
            expanded_dse = dse.tensor(photon_identity).simplify(atol=1.0e-12)
            dse_terms.append(expanded_dse)
            full_dse.append(expanded_dse)

    total_terms = [
        _embed_electronic(mapping.qubit_hamiltonian, photon_qubits),
        _embed_photon(photon_hamiltonian, electronic_qubits),
        *coupling_terms,
        *dse_terms,
    ]
    total = _sum_ops(total_terms, num_qubits=electronic_qubits + photon_qubits)

    modes_payload = [
        {
            "mode_index": index,
            "frequency": float(mode.frequency),
            "coupling_strength": float(mode.coupling_strength),
            "polarization": [float(value) for value in _normalize(mode.polarization)],
            "max_occupation": int(mode.max_occupation),
            "mode_qubits": mode_qubits[index],
        }
        for index, mode in enumerate(cavity.modes)
    ]
    summary = CavityQEDModelSummary(
        enabled=True,
        model=cavity.model,
        mode_count=len(cavity.modes),
        modes=modes_payload,
        photon_encoding=cavity.photon_encoding,
        include_dipole_self_energy=bool(cavity.include_dipole_self_energy),
        photon_physical_subspace_penalty=float(cavity.photon_physical_subspace_penalty),
        electronic_qubits=electronic_qubits,
        photon_qubits=photon_qubits,
        total_qubits=electronic_qubits + photon_qubits,
        hamiltonian_formula=HAMILTONIAN_FORMULA,
        term_counts_by_sector={
            "electronic": len(mapping.qubit_hamiltonian),
            "photon": len(photon_hamiltonian),
            "electron_photon_coupling": sum(len(term) for term in coupling_terms),
            "dipole_self_energy": sum(len(term) for term in dse_terms),
            "photon_physical_subspace_penalty": len(photon_leakage),
            "total": len(total),
        },
        observables={
            "dipole_self_energy_enabled": bool(cavity.include_dipole_self_energy),
            "photon_occupation": [],
            "dipole_expectation": [],
            "electron_photon_coupling_energy": [],
            "dipole_self_energy": [],
            "polaritonic_state_composition": [],
            "photon_physical_subspace_leakage": None,
            "vqe_vs_exact_error": None,
            "exact_residual_norm": None,
        },
        resource_estimate={
            "electronic_qubits": electronic_qubits,
            "photon_qubits": photon_qubits,
            "total_qubits": electronic_qubits + photon_qubits,
            "pauli_terms": len(total),
            "mode_qubits": mode_qubits,
        },
        error_budget={
            "photon_cutoff": {
                "max_occupation_by_mode": [int(mode.max_occupation) for mode in cavity.modes],
                "status": "finite_cutoff_configured",
            },
            "exact_residual_norm": None,
            "vqe_vs_exact_error": None,
            "photon_encoding_leakage": None,
        },
        notes=[
            "Exploratory Pauli-Fierz cavity-QED Hamiltonian with finite photon cutoff.",
            "Exact baselines are exact only for the configured electron-photon qubit Hamiltonian.",
        ],
    )

    return CavityQEDContext(
        qubit_hamiltonian=total,
        summary=summary,
        photon_hamiltonian=photon_hamiltonian,
        photon_number_operators=full_numbers,
        photon_leakage_operator=_embed_photon(photon_leakage, electronic_qubits),
        dipole_operators=full_dipoles,
        coupling_energy_operators=full_couplings,
        dipole_self_energy_operators=full_dse,
        electronic_qubits=electronic_qubits,
        photon_qubits=photon_qubits,
        photon_mode_qubits=mode_qubits,
    )


def summarize_cavity_qed_observables(
    context: CavityQEDContext,
    *,
    spectrum: ExactSpectrum | None,
    solver_energy: float | None,
    exact_energy: float | None,
) -> dict[str, Any]:
    """Summarize exact-spectrum cavity-QED observables for reports."""
    if spectrum is None or spectrum.eigenvectors.size == 0:
        return {
            "photon_occupation": [],
            "dipole_expectation": [],
            "electron_photon_coupling_energy": [],
            "dipole_self_energy": [],
            "polaritonic_state_composition": [],
            "photon_physical_subspace_leakage": None,
            "exact_residual_norm": None,
            "vqe_vs_exact_error": None,
        }
    state = np.asarray(spectrum.eigenvectors[:, 0], dtype=complex)
    photon_occupation = [
        {"mode_index": index, "expectation": _expectation(operator, state)}
        for index, operator in enumerate(context.photon_number_operators)
    ]
    dipole_expectation = [
        {"mode_index": index, "expectation": _expectation(operator, state)}
        for index, operator in enumerate(context.dipole_operators)
    ]
    coupling_energy = [
        {"mode_index": index, "expectation": _expectation(operator, state)}
        for index, operator in enumerate(context.coupling_energy_operators)
    ]
    dse_energy = [
        {"mode_index": index, "expectation": _expectation(operator, state)}
        for index, operator in enumerate(context.dipole_self_energy_operators)
    ]
    leakage = _expectation(context.photon_leakage_operator, state)
    residual = _residual_norm(context.qubit_hamiltonian, state, spectrum.eigenvalues[0])
    composition = _photon_occupation_weights(
        state,
        electronic_qubits=context.electronic_qubits,
        mode_qubits=context.photon_mode_qubits,
    )
    composition.extend(
        [
            {
                "component": "exact_ground_state_photon_marginal",
                "mode_index": item["mode_index"],
                "mean_photon_occupation": item["expectation"],
            }
            for item in photon_occupation
        ]
    )
    vqe_error = None
    if solver_energy is not None and exact_energy is not None:
        vqe_error = float(abs(float(solver_energy) - float(exact_energy)))
    return {
        "photon_occupation": photon_occupation,
        "dipole_expectation": dipole_expectation,
        "electron_photon_coupling_energy": coupling_energy,
        "dipole_self_energy": dse_energy,
        "polaritonic_state_composition": composition,
        "photon_physical_subspace_leakage": leakage,
        "exact_residual_norm": residual,
        "vqe_vs_exact_error": vqe_error,
    }
