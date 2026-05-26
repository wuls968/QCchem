from __future__ import annotations

import pytest

from qcchem.pbc.ewald import (
    EwaldSettings,
    PeriodicPointCharge,
    periodic_qmmm_nuclear_point_charge_energy,
)


def test_periodic_qmmm_ewald_rejects_charged_cell() -> None:
    with pytest.raises(ValueError, match="neutral full QM/MM cell"):
        periodic_qmmm_nuclear_point_charge_energy(
            lattice_vectors=((10.0, 0.0, 0.0), (0.0, 10.0, 0.0), (0.0, 0.0, 10.0)),
            qm_nuclear_charges=[
                PeriodicPointCharge(label="H", coords=(0.0, 0.0, 0.0), charge=1.0)
            ],
            mm_point_charges=[
                PeriodicPointCharge(label="MM", coords=(2.0, 0.0, 0.0), charge=-0.25)
            ],
            settings=EwaldSettings(unit="bohr", total_cell_charge=0.75),
        )


def test_periodic_qmmm_ewald_returns_constant_and_fingerprint_payload() -> None:
    result = periodic_qmmm_nuclear_point_charge_energy(
        lattice_vectors=((12.0, 0.0, 0.0), (0.0, 12.0, 0.0), (0.0, 0.0, 12.0)),
        qm_nuclear_charges=[
            PeriodicPointCharge(label="H", coords=(0.0, 0.0, 0.0), charge=1.0)
        ],
        mm_point_charges=[
            PeriodicPointCharge(label="MM", coords=(1.5, 0.0, 0.0), charge=-1.0)
        ],
        settings=EwaldSettings(
            unit="bohr",
            alpha=0.35,
            real_space_cutoff=6.0,
            reciprocal_cutoff=4.0,
            total_cell_charge=0.0,
        ),
    )

    assert result.energy_hartree < 0.0
    assert result.fingerprint == result.payload["fingerprint"]
    assert result.payload["neutrality"]["passed"] is True
    assert result.payload["neutrality"]["total_charge"] == 0.0
    assert result.payload["components"]["self_hartree"] == 0.0
    assert result.payload["provenance"]["g_zero_policy"].startswith("rejected")


def test_periodic_qmmm_ewald_fingerprint_changes_with_physics() -> None:
    kwargs = {
        "lattice_vectors": ((12.0, 0.0, 0.0), (0.0, 12.0, 0.0), (0.0, 0.0, 12.0)),
        "qm_nuclear_charges": [
            PeriodicPointCharge(label="H", coords=(0.0, 0.0, 0.0), charge=1.0)
        ],
        "settings": EwaldSettings(
            unit="bohr",
            alpha=0.35,
            real_space_cutoff=6.0,
            reciprocal_cutoff=4.0,
            total_cell_charge=0.0,
        ),
    }
    first = periodic_qmmm_nuclear_point_charge_energy(
        **kwargs,
        mm_point_charges=[
            PeriodicPointCharge(label="MM", coords=(1.5, 0.0, 0.0), charge=-1.0)
        ],
    )
    second = periodic_qmmm_nuclear_point_charge_energy(
        **kwargs,
        mm_point_charges=[
            PeriodicPointCharge(label="MM", coords=(2.0, 0.0, 0.0), charge=-1.0)
        ],
    )

    assert first.fingerprint != second.fingerprint
    assert first.energy_hartree != pytest.approx(second.energy_hartree)
