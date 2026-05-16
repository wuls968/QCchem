from __future__ import annotations

from pathlib import Path

import pytest
from pyscf import gto, qmmm, scf
from qiskit_nature.second_q.drivers import MethodType
from qiskit_nature.units import DistanceUnit

from qcchem.chem.external_charges import (
    build_pyscf_driver,
    qm_nuclear_point_charge_interaction_energy,
    pyscf_qmmm_nuclear_interaction_energy,
    read_xyzq,
    resolve_external_point_charges,
)
from qcchem.core import (
    AtomSpec,
    ExternalPointChargeSpec,
    MoleculeSpec,
    PointChargeDampingSpec,
    PointChargeSpec,
)


def _h2_molecule() -> MoleculeSpec:
    return MoleculeSpec(
        name="H2-external",
        geometry=[
            AtomSpec("H", (0.0, 0.0, 0.0)),
            AtomSpec("H", (0.0, 0.0, 0.735)),
        ],
        unit="angstrom",
    )


def test_read_xyzq_supports_header_comments_and_optional_labels(tmp_path: Path) -> None:
    path = tmp_path / "environment.xyzq"
    path.write_text(
        """
# label x y z q
label x y z q
mm1 0.0 0.0 2.0 -0.5
0.0 0.0 -2.0 0.25
        """.strip(),
        encoding="utf-8",
    )

    charges = read_xyzq(path)

    assert [charge.label for charge in charges] == ["mm1", None]
    assert charges[0].coords == (0.0, 0.0, 2.0)
    assert charges[0].charge == -0.5
    assert charges[1].charge == 0.25


def test_resolve_external_point_charges_rejects_overlapping_qm_atom() -> None:
    spec = ExternalPointChargeSpec(
        enabled=True,
        unit="angstrom",
        charges=[PointChargeSpec(label="bad", coords=(0.0, 0.0, 0.0), charge=-0.5)],
        min_distance_to_qm_atoms=1.0e-5,
    )

    with pytest.raises(ValueError, match="too close"):
        resolve_external_point_charges(_h2_molecule(), spec)


def test_qm_nuclear_point_charge_energy_matches_pyscf_qmmm_energy_nuc_delta() -> None:
    molecule = _h2_molecule()
    charges = [PointChargeSpec(label="mm", coords=(0.0, 0.0, 2.0), charge=-0.5)]

    helper_energy = qm_nuclear_point_charge_interaction_energy(
        molecule,
        charges,
        charge_unit="angstrom",
    )

    mol = gto.M(
        atom=molecule.geometry_string(),
        unit="Angstrom",
        basis=molecule.basis,
        charge=molecule.charge,
        spin=molecule.spin,
        verbose=0,
    )
    embedded = qmmm.mm_charge(
        scf.RHF(mol),
        [charges[0].coords],
        [charges[0].charge],
        unit="Angstrom",
    )

    assert helper_energy == pytest.approx(embedded.energy_nuc() - gto.mole.energy_nuc(mol))


def test_gaussian_damped_point_charges_expose_radii_energy_and_hcore_delta() -> None:
    molecule = _h2_molecule()
    spec = ExternalPointChargeSpec(
        enabled=True,
        unit="angstrom",
        charges=[PointChargeSpec(label="mm", coords=(0.0, 0.0, 2.0), charge=-0.5)],
    )

    resolved = resolve_external_point_charges(
        molecule,
        spec,
        damping=PointChargeDampingSpec(
            kind="gaussian",
            default_radius=0.4,
            radius_unit="angstrom",
            min_radius=0.15,
            overpolarization_warning_potential_au=2.0,
        ),
        compatibility_mode="environment_embedding.point_charges",
    )

    assert resolved.radii == pytest.approx([0.4])
    assert resolved.damping_model["kind"] == "gaussian"
    assert resolved.qm_nuclear_interaction_energy == pytest.approx(
        pyscf_qmmm_nuclear_interaction_energy(
            molecule,
            resolved.charges,
            charge_unit=resolved.unit,
            radii=resolved.radii,
        )
    )

    driver = build_pyscf_driver(
        atom=molecule.geometry_string(),
        unit=DistanceUnit.ANGSTROM,
        charge=molecule.charge,
        spin=molecule.spin,
        basis=molecule.basis,
        method=MethodType.RHF,
        point_charges=resolved,
    )
    driver.run()

    matrix = driver.external_point_charge_potential_matrix_ao
    assert matrix is not None
    assert matrix.shape[0] == matrix.shape[1]
    assert matrix.shape[0] > 0
    assert matrix == pytest.approx(matrix.T)
    assert float(abs(matrix).max()) > 0.0
