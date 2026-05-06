from __future__ import annotations

import numpy as np

from qcchem.core import AtomSpec, LatticeQEDSpec, MoleculeSpec
from qcchem.qft.lattice_qed import build_lattice_qed_context


def _h2_molecule() -> MoleculeSpec:
    return MoleculeSpec(
        name="H2-lattice-qed-gauge-audit",
        geometry=[
            AtomSpec("H", (0.0, 0.0, 0.0)),
            AtomSpec("H", (0.0, 0.0, 0.74)),
        ],
    )


def _spec() -> LatticeQEDSpec:
    spec = LatticeQEDSpec(enabled=True)
    spec.dimensions = 1
    spec.grid.shape = [2]
    spec.grid.spacing = [0.75]
    spec.grid.softening = 0.35
    spec.matter.spin_components = 2
    spec.matter.target_electrons = "auto"
    spec.gauge.electric_cutoff = 1
    spec.gauge.coupling = 1.0
    spec.constraints.gauss_law_penalty = 10.0
    spec.constraints.particle_number_penalty = 10.0
    spec.constraints.padding_penalty = 50.0
    spec.constraints.enforce_physical_sector = True
    spec.constraints.target_charge_sector = "neutral"
    spec.constraints.gauss_law_tolerance = 1.0e-8
    spec.constraints.max_sector_enumeration_qubits = 8
    spec.ansatz.generator_policy = "gauge_invariant_hopping"
    return spec


def test_gauss_law_generators_are_hermitian_and_commute_with_hamiltonian() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _spec(), mapping_kind="jordan_wigner")

    assert len(context.gauss_law_matrices) == context.summary.site_count
    assert len(context.summary.gauss_law_generators) == context.summary.site_count
    for matrix, metadata in zip(context.gauss_law_matrices, context.summary.gauss_law_generators):
        assert np.allclose(matrix, matrix.conj().T)
        assert metadata["hermitian"] is True
        assert metadata["pauli_term_count"] > 0

    commutators = context.summary.hamiltonian_gauge_commutator_norms
    assert len(commutators) == context.summary.site_count
    assert all(item["frobenius_norm"] <= 1.0e-8 for item in commutators)


def test_physical_sector_enumeration_and_gauge_invariant_generator_plan_are_nonempty() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _spec(), mapping_kind="jordan_wigner")

    sector = context.summary.physical_sector
    assert sector["enumerated"] is True
    assert sector["physical_sector_dimension"] > 0
    assert sector["reference_basis_index"] in sector["basis_indices_preview"]
    assert sector["target_charge_sector"] == "neutral"

    ansatz = context.summary.gauge_invariant_ansatz
    assert ansatz["generator_policy"] == "gauge_invariant_hopping"
    assert ansatz["selected_generator_count"] > 0
    assert all(item["commutes_with_all_gauss_law_generators"] for item in ansatz["commutator_checks"])

    expectations = context.summary.constraint_expectations
    assert expectations["gauss_law_tolerance"] == 1.0e-8
    assert expectations["reference_state_max_abs_gauss_law"] <= 1.0e-8
