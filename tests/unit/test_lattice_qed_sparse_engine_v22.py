from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from qcchem.core import AtomSpec, LatticeQEDSpec, MoleculeSpec
from qcchem.qft.lattice_qed import build_lattice_qed_context
from qcchem.qft.observables import build_qft_observable_matrices


def _h2_molecule() -> MoleculeSpec:
    return MoleculeSpec(
        name="H2-lattice-qed-sparse-engine",
        geometry=[
            AtomSpec("H", (0.0, 0.0, 0.0)),
            AtomSpec("H", (0.0, 0.0, 0.74)),
        ],
    )


def _spec(*, shape: list[int] | None = None, spin_components: int = 2) -> LatticeQEDSpec:
    spec = LatticeQEDSpec(enabled=True)
    spec.dimensions = 1
    spec.grid.shape = shape or [2]
    spec.grid.spacing = [0.75 for _ in spec.grid.shape]
    spec.grid.softening = 0.35
    spec.matter.spin_components = spin_components
    spec.matter.target_electrons = "auto"
    spec.gauge.electric_cutoff = 1
    spec.gauge.coupling = 1.0
    spec.constraints.gauss_law_penalty = 10.0
    spec.constraints.particle_number_penalty = 10.0
    spec.constraints.padding_penalty = 50.0
    spec.constraints.enforce_physical_sector = True
    spec.constraints.target_charge_sector = "neutral"
    spec.constraints.gauss_law_tolerance = 1.0e-8
    spec.constraints.max_sector_enumeration_qubits = 12
    spec.engine.representation = "sparse_projected"
    spec.engine.materialize_pauli = "never"
    spec.engine.store_basis_indices = "full"
    spec.engine.max_projected_dimension = 4096
    return spec


def _dense_spec() -> LatticeQEDSpec:
    spec = _spec()
    spec.engine.representation = "dense_full"
    spec.engine.materialize_pauli = "always"
    return spec


def test_sparse_full_hamiltonian_matches_dense_sector_by_sector_for_2_site_h2() -> None:
    dense_context = build_lattice_qed_context(_h2_molecule(), _dense_spec(), mapping_kind="jordan_wigner")
    sparse_context = build_lattice_qed_context(
        _h2_molecule(),
        _spec(),
        mapping_kind="jordan_wigner",
    )

    bundle = sparse_context.sparse_bundle
    assert bundle is not None
    assert sp.issparse(bundle.full_hamiltonian)
    for sector_name, dense_matrix in dense_context.sector_matrices.items():
        sparse_matrix = bundle.sector_matrices[sector_name]
        assert sp.issparse(sparse_matrix)
        assert np.allclose(sparse_matrix.toarray(), dense_matrix)
    assert np.allclose(bundle.full_hamiltonian.toarray(), dense_context.hamiltonian_matrix)


def test_projected_hamiltonian_is_hermitian_and_matches_indexed_full_hamiltonian() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _spec(), mapping_kind="jordan_wigner")
    bundle = context.sparse_bundle

    assert bundle is not None
    assert bundle.projected_hamiltonian is not None
    indices = np.asarray(context.summary.physical_sector["basis_indices"], dtype=int)
    projected_from_full = bundle.full_hamiltonian[indices, :][:, indices]

    assert np.allclose(bundle.projected_hamiltonian.toarray(), projected_from_full.toarray())
    assert np.allclose(
        bundle.projected_hamiltonian.toarray(),
        bundle.projected_hamiltonian.conj().T.toarray(),
    )
    assert context.summary.physical_sector["basis_index_count"] == len(indices)
    assert context.summary.physical_sector["basis_hash"]
    assert context.summary.physical_sector["padding_state_rejection_count"] >= 0
    assert context.summary.engine["actual_representation"] == "sparse_projected"
    assert context.summary.engine["projected_dimension"] == len(indices)
    assert context.summary.engine["pauli_materialization"] == "skipped"


def test_projected_observables_are_hermitian_and_projected_dimension() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _spec(), mapping_kind="jordan_wigner")
    observables = build_qft_observable_matrices(context)
    projected_dimension = context.summary.engine["projected_dimension"]

    for name in ("particle_number", "total_electric_energy", "total_gauss_violation"):
        matrix = observables.aggregate[name]
        assert matrix.shape == (projected_dimension, projected_dimension)
        assert np.allclose(matrix.toarray(), matrix.conj().T.toarray())


def test_sparse_engine_scales_to_1d_4site_projected_h2() -> None:
    context = build_lattice_qed_context(
        _h2_molecule(),
        _spec(shape=[4], spin_components=1),
        mapping_kind="jordan_wigner",
    )

    assert context.sparse_bundle is not None
    assert context.summary.site_count == 4
    assert context.summary.total_qubits == 10
    assert context.summary.engine["actual_representation"] == "sparse_projected"
    assert 0 < context.summary.engine["projected_dimension"] <= 4096
    assert context.summary.physical_sector["basis_index_count"] == context.summary.engine["projected_dimension"]
