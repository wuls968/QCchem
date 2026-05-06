from __future__ import annotations

import numpy as np

from qcchem.core import AtomSpec, LatticeQEDSpec, MoleculeSpec
from qcchem.qft.lattice_qed import build_lattice_qed_context


def _h2_molecule() -> MoleculeSpec:
    return MoleculeSpec(
        name="H2-lattice-qed",
        geometry=[
            AtomSpec("H", (0.0, 0.0, 0.0)),
            AtomSpec("H", (0.0, 0.0, 0.74)),
        ],
    )


def _spec(*, gauss_penalty: float = 10.0, particle_penalty: float = 10.0) -> LatticeQEDSpec:
    spec = LatticeQEDSpec(enabled=True)
    spec.dimensions = 1
    spec.grid.shape = [2]
    spec.grid.spacing = [0.75]
    spec.grid.softening = 0.35
    spec.matter.spin_components = 2
    spec.matter.target_electrons = "auto"
    spec.gauge.electric_cutoff = 1
    spec.gauge.coupling = 1.0
    spec.constraints.gauss_law_penalty = gauss_penalty
    spec.constraints.particle_number_penalty = particle_penalty
    spec.constraints.padding_penalty = 50.0
    return spec


def test_lattice_qed_hamiltonian_is_hermitian_and_records_sector_counts() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _spec(), mapping_kind="jordan_wigner")

    matrix = np.asarray(context.qubit_hamiltonian.to_matrix(), dtype=complex)
    assert np.allclose(matrix, matrix.conj().T)
    assert context.summary.total_qubits == 6
    assert context.summary.matter_mode_count == 4
    assert context.summary.link_count == 1
    assert context.summary.term_counts_by_sector["hopping"] > 0
    assert context.summary.term_counts_by_sector["gauss_law_penalty"] > 0
    assert context.summary.constraint_residuals["gauss_law_penalty"] == 10.0


def test_lattice_qed_penalties_change_the_finite_cutoff_operator() -> None:
    constrained = build_lattice_qed_context(_h2_molecule(), _spec(), mapping_kind="jordan_wigner")
    unconstrained = build_lattice_qed_context(
        _h2_molecule(),
        _spec(gauss_penalty=0.0, particle_penalty=0.0),
        mapping_kind="jordan_wigner",
    )

    constrained_matrix = np.asarray(constrained.qubit_hamiltonian.to_matrix(), dtype=complex)
    unconstrained_matrix = np.asarray(unconstrained.qubit_hamiltonian.to_matrix(), dtype=complex)
    assert not np.allclose(constrained_matrix, unconstrained_matrix)
    assert len(constrained.qubit_hamiltonian) > len(unconstrained.qubit_hamiltonian)
