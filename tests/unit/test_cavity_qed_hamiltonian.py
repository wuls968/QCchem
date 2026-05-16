from __future__ import annotations

import numpy as np

from qcchem.chem import build_electronic_structure_context
from qcchem.core import AtomSpec, CavityQEDModeSpec, CavityQEDSpec, MoleculeSpec, RunSpec
from qcchem.field_models.cavity_qed import build_cavity_qed_context, summarize_cavity_qed_observables
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.solvers.spectrum import compute_exact_spectrum


def _run_spec(*, coupling: float = 0.05, include_dse: bool = True, max_occupation: int = 1) -> RunSpec:
    spec = RunSpec(
        molecule=MoleculeSpec(
            name="H2-cavity-unit",
            geometry=[
                AtomSpec("H", (0.0, 0.0, 0.0)),
                AtomSpec("H", (0.0, 0.0, 0.74)),
            ],
        )
    )
    spec.problem.cavity_qed = CavityQEDSpec(
        enabled=True,
        include_dipole_self_energy=include_dse,
        photon_physical_subspace_penalty=25.0,
        modes=[
            CavityQEDModeSpec(
                frequency=0.4,
                coupling_strength=coupling,
                polarization=[0.0, 0.0, 1.0],
                max_occupation=max_occupation,
            )
        ],
    )
    return spec


def _electronic_mapping(spec: RunSpec):
    chemistry = build_electronic_structure_context(spec)
    mapping = map_fermionic_hamiltonian(
        chemistry.fermionic_hamiltonian,
        spec.mapping.kind,
        num_particles=chemistry.summary.num_particles,
    )
    return chemistry, mapping


def test_pauli_fierz_hamiltonian_is_hermitian() -> None:
    spec = _run_spec()
    chemistry, mapping = _electronic_mapping(spec)

    context = build_cavity_qed_context(spec, chemistry, mapping)
    matrix = context.qubit_hamiltonian.to_matrix()

    assert np.allclose(matrix, matrix.conj().T)
    assert context.summary.mode_count == 1
    assert context.summary.electronic_qubits == mapping.summary.num_qubits
    assert context.summary.photon_qubits == 2
    assert context.summary.total_qubits == mapping.summary.num_qubits + 2


def test_zero_coupling_recovers_electronic_plus_photon_baseline() -> None:
    spec = _run_spec(coupling=0.0, include_dse=True)
    chemistry, mapping = _electronic_mapping(spec)
    context = build_cavity_qed_context(spec, chemistry, mapping)

    total_matrix = context.qubit_hamiltonian.to_matrix()
    electronic = mapping.qubit_hamiltonian.to_matrix()
    photon = context.photon_hamiltonian.to_matrix()
    expected = np.kron(electronic, np.eye(photon.shape[0])) + np.kron(
        np.eye(electronic.shape[0]),
        photon,
    )

    assert np.allclose(total_matrix, expected)


def test_dse_contribution_is_nonnegative_when_enabled() -> None:
    spec = _run_spec(coupling=0.06, include_dse=True)
    chemistry, mapping = _electronic_mapping(spec)
    context = build_cavity_qed_context(spec, chemistry, mapping)

    assert context.summary.observables["dipole_self_energy_enabled"] is True
    assert context.summary.term_counts_by_sector["dipole_self_energy"] > 0
    assert context.dipole_self_energy_operators
    dse_matrix = context.dipole_self_energy_operators[0].to_matrix()
    eigenvalues = np.linalg.eigvalsh(dse_matrix)
    assert float(np.min(eigenvalues)) >= -1.0e-9


def test_photon_observables_are_populated_from_exact_spectrum() -> None:
    spec = _run_spec(coupling=0.04)
    chemistry, mapping = _electronic_mapping(spec)
    context = build_cavity_qed_context(spec, chemistry, mapping)
    spectrum = compute_exact_spectrum(context.qubit_hamiltonian, num_states=2)

    observables = summarize_cavity_qed_observables(
        context,
        spectrum=spectrum,
        solver_energy=spectrum.eigenvalues[0],
        exact_energy=spectrum.eigenvalues[0],
    )

    assert observables["photon_occupation"][0]["expectation"] >= 0.0
    assert observables["photon_physical_subspace_leakage"] >= 0.0
    assert observables["polaritonic_state_composition"]
    assert observables["exact_residual_norm"] <= 1.0e-8
