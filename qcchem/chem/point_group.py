"""Point-group symmetry support built on PySCF metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qiskit_nature.exceptions import QiskitNatureError
from qiskit_nature.second_q.drivers import PySCFDriver

from qcchem.core import MoleculeSpec, PointGroupSpec


@dataclass(slots=True)
class PointGroupProblemResult:
    """Electronic problem plus point-group metadata from PySCF."""

    problem: object
    metadata: dict[str, Any]


@dataclass(slots=True)
class PointGroupFilterResult:
    """Resolved active-space filter from point-group orbital irreps."""

    active_orbitals_current: list[int]
    active_orbitals_original: list[int]
    num_electrons: int | tuple[int, int]
    num_spatial_orbitals: int
    metadata: dict[str, Any] = field(default_factory=dict)


class SymmetryAwarePySCFDriver(PySCFDriver):
    """PySCFDriver variant that lets PySCF build point-group symmetry metadata."""

    def __init__(self, *args, symmetry_subgroup: str | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._symmetry_subgroup = symmetry_subgroup

    def _build_molecule(self) -> None:
        from pyscf import gto
        from pyscf.lib import logger as pylogger
        from pyscf.lib import param

        atom = self._check_molecule_format(self.atom)
        if self._max_memory is None:
            self._max_memory = param.MAX_MEMORY
        try:
            self._mol = gto.Mole(
                atom=atom,
                unit=self._unit.value,
                basis=self._basis,
                max_memory=self._max_memory,
                verbose=pylogger.QUIET,
                output=None,
            )
            self._mol.symmetry = True
            if self._symmetry_subgroup is not None:
                self._mol.symmetry_subgroup = self._symmetry_subgroup
            self._mol.charge = self._charge
            self._mol.spin = self._spin
            self._mol.build(parse_arg=False)
        except Exception as exc:
            raise QiskitNatureError("Failed to build the symmetry-aware PySCF Molecule object.") from exc


def _as_float_list(value: Any) -> list[float]:
    if value is None:
        return []
    return [float(item) for item in np.asarray(value, dtype=float).reshape(-1).tolist()]


def _as_irrep_list(value: Any) -> list[str]:
    if value is None:
        return []
    return [str(item) for item in np.asarray(value).reshape(-1).tolist()]


def _label_orbital_irreps(driver: SymmetryAwarePySCFDriver) -> dict[str, Any]:
    from pyscf import symm

    mol = driver._mol
    calc = driver._calc
    metadata: dict[str, Any] = {
        "enabled": True,
        "status": "available",
        "group": getattr(mol, "groupname", None),
        "topgroup": getattr(mol, "topgroup", None),
        "irrep_names": [str(value) for value in getattr(mol, "irrep_name", [])],
        "irrep_ids": [int(value) for value in getattr(mol, "irrep_id", [])],
        "notes": [],
    }
    try:
        mo_coeff = calc.mo_coeff
        mo_occ = calc.mo_occ
        mo_energy = calc.mo_energy
        if isinstance(mo_coeff, (tuple, list)):
            spin_blocks = {}
            for label, coeff, occ, energy in zip(("alpha", "beta"), mo_coeff, mo_occ, mo_energy):
                irreps = symm.label_orb_symm(mol, mol.irrep_name, mol.symm_orb, coeff)
                spin_blocks[label] = {
                    "orbital_irreps": _as_irrep_list(irreps),
                    "orbital_occupations": _as_float_list(occ),
                    "orbital_energies": _as_float_list(energy),
                }
            metadata["spin_blocks"] = spin_blocks
            metadata["orbital_irreps"] = spin_blocks.get("alpha", {}).get("orbital_irreps", [])
            metadata["orbital_occupations"] = spin_blocks.get("alpha", {}).get("orbital_occupations", [])
            metadata["orbital_energies"] = spin_blocks.get("alpha", {}).get("orbital_energies", [])
        else:
            irreps = symm.label_orb_symm(mol, mol.irrep_name, mol.symm_orb, mo_coeff)
            metadata["orbital_irreps"] = _as_irrep_list(irreps)
            metadata["orbital_occupations"] = _as_float_list(mo_occ)
            metadata["orbital_energies"] = _as_float_list(mo_energy)
    except Exception as exc:
        metadata["status"] = "metadata_unavailable"
        metadata["notes"].append(f"PySCF orbital irrep labeling failed: {type(exc).__name__}: {exc}")
    return metadata


def run_point_group_pyscf(driver: SymmetryAwarePySCFDriver) -> PointGroupProblemResult:
    """Run a symmetry-aware PySCFDriver and return the Qiskit Nature problem plus metadata."""
    problem = driver.run()
    return PointGroupProblemResult(problem=problem, metadata=_label_orbital_irreps(driver))


def skipped_point_group_metadata(reason: str) -> dict[str, Any]:
    """Build a stable point-group metadata payload when symmetry is not used."""
    return {
        "enabled": False,
        "status": "skipped",
        "group": None,
        "topgroup": None,
        "orbital_irreps": [],
        "orbital_occupations": [],
        "orbital_energies": [],
        "selected_active_orbitals": [],
        "selected_active_orbitals_original": [],
        "notes": [reason],
    }


def resolve_point_group_filter(
    *,
    point_group: PointGroupSpec,
    metadata: dict[str, Any],
    available_original_orbitals: list[int],
    molecule: MoleculeSpec,
) -> PointGroupFilterResult | None:
    """Resolve explicit irrep-based active-space pruning after freeze-core removal."""
    if point_group.reduction_mode.strip().lower() != "irrep_filter":
        return None
    irreps = [str(value) for value in metadata.get("orbital_irreps", [])]
    if not irreps:
        raise ValueError("Point-group irrep_filter requires available PySCF orbital irreps.")
    active = {value.lower() for value in point_group.active_irreps}
    remove = {value.lower() for value in point_group.remove_irreps}
    if not active and not remove:
        raise ValueError("problem.point_group.irrep_filter requires active_irreps or remove_irreps.")

    selected_current: list[int] = []
    selected_original: list[int] = []
    for current_index, original_index in enumerate(available_original_orbitals):
        if original_index >= len(irreps):
            continue
        irrep = irreps[original_index]
        normalized = irrep.lower()
        keep = True
        if active:
            keep = normalized in active
        if normalized in remove:
            keep = False
        if keep:
            selected_current.append(current_index)
            selected_original.append(original_index)
    if not selected_current:
        raise ValueError("Point-group irrep_filter selected no active orbitals.")

    occupations = [float(value) for value in metadata.get("orbital_occupations", [])]
    if occupations:
        electron_count = int(round(sum(occupations[index] for index in selected_original if index < len(occupations))))
    else:
        electron_count = min(2 * len(selected_current), max(len(molecule.geometry) - molecule.charge, 1))
    if electron_count <= 0:
        raise ValueError("Point-group irrep_filter selected no active electrons.")

    selected_irreps = [irreps[index] for index in selected_original if index < len(irreps)]
    filter_metadata = {
        "reduction_mode": "irrep_filter",
        "active_irreps": list(point_group.active_irreps),
        "remove_irreps": list(point_group.remove_irreps),
        "selected_active_orbitals": list(selected_current),
        "selected_active_orbitals_original": list(selected_original),
        "selected_active_irreps": selected_irreps,
        "num_active_electrons": electron_count,
        "num_active_orbitals": len(selected_current),
    }
    return PointGroupFilterResult(
        active_orbitals_current=selected_current,
        active_orbitals_original=selected_original,
        num_electrons=electron_count,
        num_spatial_orbitals=len(selected_current),
        metadata=filter_metadata,
    )
