from __future__ import annotations

import numpy as np

from qcchem.core import AtomSpec, LatticeQEDSpec, MoleculeSpec
from qcchem.qft.grid import build_lattice_grid
from qcchem.qft.links import build_u1_link_operators


def _h2_molecule() -> MoleculeSpec:
    return MoleculeSpec(
        name="H2-grid",
        geometry=[
            AtomSpec("H", (0.0, 0.0, 0.0)),
            AtomSpec("H", (0.0, 0.0, 0.74)),
        ],
    )


def test_build_lattice_grid_indexes_open_links_in_one_and_two_dimensions() -> None:
    one_d = LatticeQEDSpec()
    one_d.dimensions = 1
    one_d.grid.shape = [2]
    one_d.grid.spacing = [0.75]
    grid_1d = build_lattice_grid(_h2_molecule(), one_d)

    assert grid_1d.site_count == 2
    assert [site.index for site in grid_1d.sites] == [(0,), (1,)]
    assert len(grid_1d.links) == 1
    assert grid_1d.links[0].start_site == 0
    assert grid_1d.links[0].end_site == 1
    assert grid_1d.nuclear_charge_by_site == [1.0, 1.0]

    two_d = LatticeQEDSpec()
    two_d.dimensions = 2
    two_d.grid.shape = [2, 2]
    two_d.grid.spacing = [0.5, 0.5]
    grid_2d = build_lattice_grid(_h2_molecule(), two_d)

    assert grid_2d.site_count == 4
    assert len(grid_2d.links) == 4
    assert len(grid_2d.plaquettes) == 1


def test_u1_link_operators_use_binary_padding_and_hermitian_electric_terms() -> None:
    link = build_u1_link_operators(electric_cutoff=1)

    assert link.levels == [-1, 0, 1]
    assert link.encoded_dimension == 4
    assert link.num_qubits == 2
    assert np.allclose(link.electric_matrix, link.electric_matrix.conj().T)
    assert np.allclose(link.electric_squared_matrix, link.electric_squared_matrix.conj().T)
    assert np.allclose(link.padding_projector_matrix, link.padding_projector_matrix.conj().T)
    assert link.raising_matrix[2, 1] == 1.0
    assert link.padding_projector_matrix[3, 3] == 1.0
    assert link.electric_squared_pauli.num_qubits == 2
