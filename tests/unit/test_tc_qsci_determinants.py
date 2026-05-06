from __future__ import annotations

import numpy as np
import pytest
from qiskit.quantum_info import SparsePauliOp

from qcchem.exploratory.tc_qsci.determinants import (
    build_initial_state,
    build_selected_subspace_matrix,
    determinant_sector,
    determinants_in_sector,
    filter_determinants_by_sector,
    hartree_fock_determinant,
)


def test_determinants_in_jw_spin_sector_track_particle_number_and_sz() -> None:
    sector = determinants_in_sector(num_spatial_orbitals=2, num_particles=(1, 1))

    assert [item.index for item in sector] == [5, 6, 9, 10]
    assert sector[0].bitstring == "0101"
    assert sector[0].alpha_electrons == 1
    assert sector[0].beta_electrons == 1
    assert sector[0].spin_projection == pytest.approx(0.0)

    filtered = filter_determinants_by_sector(
        [0, hartree_fock_determinant(2, (1, 1)), 15],
        num_spatial_orbitals=2,
        num_particles=(1, 1),
    )
    assert filtered == [5]
    assert determinant_sector(5, num_spatial_orbitals=2).total_electrons == 2


def test_initial_state_builders_cover_hf_cisd_and_sparse_multiconfig() -> None:
    hf = build_initial_state(
        kind="hf",
        num_qubits=4,
        num_spatial_orbitals=2,
        num_particles=(1, 1),
    )
    assert hf.determinants == [5]
    assert hf.vector[5] == pytest.approx(1.0)

    cisd = build_initial_state(
        kind="cisd",
        num_qubits=4,
        num_spatial_orbitals=2,
        num_particles=(1, 1),
    )
    assert set(cisd.determinants) == {5, 6, 9, 10}
    assert np.linalg.norm(cisd.vector) == pytest.approx(1.0)

    sparse = build_initial_state(
        kind="sparse_multiconfig",
        num_qubits=4,
        num_spatial_orbitals=2,
        num_particles=(1, 1),
        entries=[
            {"bitstring": "0101", "coefficient": 1.0},
            {"bitstring": "1010", "coefficient": -1.0},
        ],
    )
    assert sparse.determinants == [5, 10]
    assert sparse.vector[5] == pytest.approx(1 / np.sqrt(2))
    assert sparse.vector[10] == pytest.approx(-1 / np.sqrt(2))


def test_selected_subspace_matrix_matches_full_matrix_when_all_determinants_are_kept() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", -0.2),
            ("ZI", 0.7),
            ("IZ", -0.4),
            ("XX", 0.15),
        ]
    )
    determinants = [0, 1, 2, 3]

    selected = build_selected_subspace_matrix(operator, determinants)
    full = np.asarray(operator.to_matrix(), dtype=complex)

    assert selected.shape == (4, 4)
    assert np.allclose(selected, full)
    assert np.linalg.eigvalsh(selected)[0] == pytest.approx(np.linalg.eigvalsh(full)[0])
