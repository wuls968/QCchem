"""Static external point-charge helpers for electrostatic embedding."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from qiskit_nature.exceptions import QiskitNatureError
from qiskit_nature.second_q.drivers import MethodType, PySCFDriver

from qcchem.core import (
    ExternalPointChargeSpec,
    ExternalPointChargeSummary,
    MoleculeSpec,
    PointChargeDampingSpec,
    PointChargeSpec,
)

LOGGER = logging.getLogger(__name__)
BOHR_PER_ANGSTROM = 1.8897261254535
ATOMIC_NUMBERS = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 5,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Ne": 10,
}


@dataclass(slots=True)
class ResolvedExternalPointCharges:
    """Validated external point charges and derived electrostatic constants."""

    enabled: bool
    charges: list[PointChargeSpec]
    unit: str
    sources: list[str]
    min_distance_to_qm_atoms: float | None
    min_distance_threshold: float
    qm_nuclear_interaction_energy: float
    radii: list[float] | None = None
    radii_unit: str | None = None
    damping_model: dict[str, object] | None = None
    max_abs_center_potential_au: float | None = None
    compatibility_mode: str = "external_point_charges"

    def to_summary(self, *, adapter_strategy: str) -> ExternalPointChargeSummary | None:
        """Build a persisted audit summary."""
        if not self.enabled:
            return None
        return ExternalPointChargeSummary(
            enabled=True,
            charge_count=len(self.charges),
            total_charge=float(sum(charge.charge for charge in self.charges)),
            unit=self.unit,
            sources=list(self.sources),
            min_distance_to_qm_atoms=self.min_distance_to_qm_atoms,
            min_distance_threshold=self.min_distance_threshold,
            qm_nuclear_interaction_energy=self.qm_nuclear_interaction_energy,
            includes_mm_self_energy=False,
            adapter_strategy=adapter_strategy,
            charges_preview=[
                {
                    "label": charge.label,
                    "coords": list(charge.coords),
                    "charge": charge.charge,
                }
                for charge in self.charges[:8]
            ],
            provenance={
                "charge_model": (
                    "fixed_gaussian_damped_point_charges"
                    if self.radii is not None
                    else "fixed_static_point_charges"
                ),
                "coordinate_unit": self.unit,
                "damping_model": self.damping_model or {"kind": "none"},
                "radii_preview": list(self.radii[:8]) if self.radii is not None else [],
                "radii_unit": self.radii_unit,
                "compatibility_mode": self.compatibility_mode,
                "max_abs_center_potential_au": self.max_abs_center_potential_au,
            },
            risk_notes=[
                "External point charges are fixed classical electrostatic sources.",
                "MM-MM, van der Waals, polarization, and environment relaxation terms are not included.",
                *(
                    [
                        "Gaussian damping is applied to reduce bare point-charge overpolarization near the QM region."
                    ]
                    if self.radii is not None
                    else [
                        "Bare point charges may overpolarize nearby QM density; prefer problem.environment_embedding point-charge damping for production studies."
                    ]
                ),
                *(
                    [
                        "Estimated charge-center potential exceeds the configured overpolarization warning threshold."
                    ]
                    if (
                        self.max_abs_center_potential_au is not None
                        and self.damping_model is not None
                        and self.max_abs_center_potential_au
                        > float(self.damping_model.get("overpolarization_warning_potential_au", float("inf")))
                    )
                    else []
                ),
            ],
        )


def normalize_unit(unit: str) -> str:
    """Normalize supported distance-unit aliases."""
    normalized = unit.strip().lower()
    if normalized in {"angstrom", "ang", "a"}:
        return "angstrom"
    if normalized in {"bohr", "au"}:
        return "bohr"
    raise ValueError(f"Unsupported external point-charge unit: {unit}")


def _to_bohr(coords: Iterable[float], unit: str) -> np.ndarray:
    array = np.asarray(list(coords), dtype=float)
    if normalize_unit(unit) == "angstrom":
        return array * BOHR_PER_ANGSTROM
    return array


def _from_bohr(coords: np.ndarray, unit: str) -> tuple[float, float, float]:
    if normalize_unit(unit) == "angstrom":
        coords = coords / BOHR_PER_ANGSTROM
    return (float(coords[0]), float(coords[1]), float(coords[2]))


def _scalar_length_to_unit(value: float, *, source_unit: str, target_unit: str) -> float:
    source = normalize_unit(source_unit)
    target = normalize_unit(target_unit)
    if source == target:
        return float(value)
    if source == "angstrom" and target == "bohr":
        return float(value) * BOHR_PER_ANGSTROM
    if source == "bohr" and target == "angstrom":
        return float(value) / BOHR_PER_ANGSTROM
    return float(value)


def _resolve_damping_radii(
    charges: list[PointChargeSpec],
    *,
    charge_unit: str,
    damping: PointChargeDampingSpec | None,
) -> tuple[list[float] | None, str | None, dict[str, object] | None, float | None]:
    if damping is None or damping.kind.strip().lower() == "none":
        return None, None, {"kind": "none"}, None
    kind = damping.kind.strip().lower()
    if kind != "gaussian":
        raise ValueError(f"Unsupported point-charge damping kind: {damping.kind}")
    if damping.default_radius is None or damping.default_radius <= 0.0:
        raise ValueError("Gaussian point-charge damping requires a positive default_radius.")
    if damping.min_radius <= 0.0:
        raise ValueError("Gaussian point-charge damping min_radius must be positive.")
    if damping.default_radius < damping.min_radius:
        raise ValueError("Gaussian point-charge damping default_radius must be >= min_radius.")
    radius_unit = normalize_unit(damping.radius_unit)
    charge_unit = normalize_unit(charge_unit)
    radius_in_charge_unit = _scalar_length_to_unit(
        float(damping.default_radius),
        source_unit=radius_unit,
        target_unit=charge_unit,
    )
    radius_bohr = _scalar_length_to_unit(
        float(damping.default_radius),
        source_unit=radius_unit,
        target_unit="bohr",
    )
    radii = [radius_in_charge_unit for _charge in charges]
    max_abs_center_potential = (
        max((2.0 / np.sqrt(np.pi)) * abs(float(charge.charge)) / radius_bohr for charge in charges)
        if charges
        else 0.0
    )
    return (
        radii,
        charge_unit,
        {
            "kind": "gaussian",
            "default_radius": float(damping.default_radius),
            "radius_unit": radius_unit,
            "min_radius": float(damping.min_radius),
            "resolved_radius_in_charge_unit": radius_in_charge_unit,
            "overpolarization_warning_potential_au": float(
                damping.overpolarization_warning_potential_au
            ),
        },
        float(max_abs_center_potential),
    )


def convert_point_charges_unit(
    charges: list[PointChargeSpec],
    *,
    source_unit: str,
    target_unit: str,
) -> list[PointChargeSpec]:
    """Convert point-charge coordinates between supported units."""
    source = normalize_unit(source_unit)
    target = normalize_unit(target_unit)
    if source == target:
        return [
            PointChargeSpec(label=charge.label, coords=charge.coords, charge=charge.charge)
            for charge in charges
        ]
    return [
        PointChargeSpec(
            label=charge.label,
            coords=_from_bohr(_to_bohr(charge.coords, source), target),
            charge=charge.charge,
        )
        for charge in charges
    ]


def read_xyzq(path: Path) -> list[PointChargeSpec]:
    """Read fixed point charges from a simple XYZQ text file."""
    charges: list[PointChargeSpec] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) < 4:
            raise ValueError(f"{path}:{line_number}: expected x y z q or label x y z q.")
        label = None
        numeric_fields = fields
        if len(fields) >= 5:
            label = fields[0]
            numeric_fields = fields[1:5]
        else:
            numeric_fields = fields[:4]
        try:
            x, y, z, q = (float(value) for value in numeric_fields)
        except ValueError as exc:
            lowered = {field.strip().lower() for field in fields}
            if {"x", "y", "z"} <= lowered and ("q" in lowered or "charge" in lowered):
                continue
            raise ValueError(f"{path}:{line_number}: invalid XYZQ numeric values.") from exc
        charges.append(PointChargeSpec(label=label, coords=(x, y, z), charge=q))
    return charges


def _qm_atom_bohr_positions(molecule: MoleculeSpec) -> list[tuple[float, np.ndarray]]:
    unit = normalize_unit(molecule.unit)
    atoms: list[tuple[float, np.ndarray]] = []
    for atom in molecule.geometry:
        try:
            atomic_number = float(ATOMIC_NUMBERS[atom.symbol])
        except KeyError as exc:
            raise ValueError(f"Unsupported atom symbol for point-charge embedding: {atom.symbol}") from exc
        atoms.append((atomic_number, _to_bohr(atom.coords, unit)))
    return atoms


def qm_nuclear_point_charge_interaction_energy(
    molecule: MoleculeSpec,
    charges: list[PointChargeSpec],
    *,
    charge_unit: str,
) -> float:
    """Compute QM nuclei and external point-charge Coulomb energy in Hartree."""
    if not charges:
        return 0.0
    atoms = _qm_atom_bohr_positions(molecule)
    total = 0.0
    for atomic_number, atom_position in atoms:
        for charge in charges:
            charge_position = _to_bohr(charge.coords, charge_unit)
            distance = float(np.linalg.norm(atom_position - charge_position))
            if distance <= 0.0:
                raise ValueError("External point charge overlaps a QM atom.")
            total += atomic_number * float(charge.charge) / distance
    return float(total)


def pyscf_qmmm_nuclear_interaction_energy(
    molecule: MoleculeSpec,
    charges: list[PointChargeSpec],
    *,
    charge_unit: str,
    radii: list[float] | None = None,
) -> float:
    """Compute the PySCF qmmm nuclear-energy delta for point charges."""
    if not charges:
        return 0.0
    from pyscf import gto, qmmm, scf

    mol = gto.M(
        atom=molecule.geometry_string(),
        unit=("Angstrom" if normalize_unit(molecule.unit) == "angstrom" else "Bohr"),
        basis=molecule.basis,
        charge=molecule.charge,
        spin=molecule.spin,
        verbose=0,
    )
    embedded = qmmm.mm_charge(
        scf.RHF(mol),
        [charge.coords for charge in charges],
        [charge.charge for charge in charges],
        radii=radii,
        unit=("Angstrom" if normalize_unit(charge_unit) == "angstrom" else "Bohr"),
    )
    return float(embedded.energy_nuc() - gto.mole.energy_nuc(mol))


def resolve_external_point_charges(
    molecule: MoleculeSpec,
    spec: ExternalPointChargeSpec,
    *,
    damping: PointChargeDampingSpec | None = None,
    compatibility_mode: str = "external_point_charges",
) -> ResolvedExternalPointCharges:
    """Load, merge, and validate configured fixed external point charges."""
    unit = normalize_unit(spec.unit or molecule.unit)
    if not spec.enabled:
        return ResolvedExternalPointCharges(
            enabled=False,
            charges=[],
            unit=unit,
            sources=[],
            min_distance_to_qm_atoms=None,
            min_distance_threshold=float(spec.min_distance_to_qm_atoms),
            qm_nuclear_interaction_energy=0.0,
            radii=None,
            radii_unit=None,
            damping_model={"kind": "none"},
            max_abs_center_potential_au=None,
            compatibility_mode=compatibility_mode,
        )

    charges = [
        PointChargeSpec(label=charge.label, coords=charge.coords, charge=float(charge.charge))
        for charge in spec.charges
    ]
    sources: list[str] = []
    if charges:
        sources.append("inline")
    if spec.source_file is not None:
        if not spec.source_file.exists():
            raise FileNotFoundError(f"External point-charge source_file not found: {spec.source_file}")
        file_charges = read_xyzq(spec.source_file)
        charges.extend(file_charges)
        sources.append(str(spec.source_file))
    if not charges:
        raise ValueError("problem.external_point_charges.enabled=true requires charges or source_file.")

    qm_atoms = _qm_atom_bohr_positions(molecule)
    threshold_bohr = float(spec.min_distance_to_qm_atoms)
    if unit == "angstrom":
        threshold_bohr *= BOHR_PER_ANGSTROM
    min_distance_bohr: float | None = None
    for charge in charges:
        charge_position = _to_bohr(charge.coords, unit)
        for _atomic_number, atom_position in qm_atoms:
            distance = float(np.linalg.norm(atom_position - charge_position))
            min_distance_bohr = distance if min_distance_bohr is None else min(min_distance_bohr, distance)
    if min_distance_bohr is not None and min_distance_bohr <= threshold_bohr:
        raise ValueError(
            "External point charge is too close to a QM atom: "
            f"min_distance={min_distance_bohr:.6e} bohr, threshold={threshold_bohr:.6e} bohr."
        )

    min_distance = None
    if min_distance_bohr is not None:
        min_distance = min_distance_bohr / BOHR_PER_ANGSTROM if unit == "angstrom" else min_distance_bohr

    radii, radii_unit, damping_model, max_abs_center_potential = _resolve_damping_radii(
        charges,
        charge_unit=unit,
        damping=damping,
    )
    return ResolvedExternalPointCharges(
        enabled=True,
        charges=charges,
        unit=unit,
        sources=sources,
        min_distance_to_qm_atoms=min_distance,
        min_distance_threshold=float(spec.min_distance_to_qm_atoms),
        qm_nuclear_interaction_energy=pyscf_qmmm_nuclear_interaction_energy(
            molecule,
            charges,
            charge_unit=unit,
            radii=radii,
        ),
        radii=radii,
        radii_unit=radii_unit,
        damping_model=damping_model,
        max_abs_center_potential_au=max_abs_center_potential,
        compatibility_mode=compatibility_mode,
    )


class StaticPointChargePySCFDriver(PySCFDriver):
    """PySCFDriver variant that decorates SCF with fixed external point charges."""

    def __init__(
        self,
        *args,
        point_charges: ResolvedExternalPointCharges,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._external_point_charges = point_charges
        self.external_point_charge_potential_matrix_ao: np.ndarray | None = None
        self.external_point_charge_nuclear_interaction_energy: float = 0.0

    def run_pyscf(self) -> None:
        """Run PySCF with qmmm.mm_charge applied before SCF convergence."""
        self._build_molecule()

        from pyscf import dft, qmmm, scf
        from pyscf.lib import chkfile as lib_chkfile

        method_name = None
        method_cls = None
        try:
            method_name = self.method.value.upper()
            method_cls = getattr(scf, method_name)
        except AttributeError as exc:
            raise QiskitNatureError(f"Failed to load {method_name} HF object.") from exc

        self._calc = method_cls(self._mol)
        if method_name in ("RKS", "ROKS", "UKS"):
            self._calc._numint.libxc = getattr(dft, self.xcf_library)
            self._calc.xc = self.xc_functional

        if self._external_point_charges.enabled:
            base_hcore = np.asarray(self._calc.get_hcore(), dtype=float)
            base_nuclear_energy = float(self._calc.energy_nuc())
            self._calc = qmmm.mm_charge(
                self._calc,
                [charge.coords for charge in self._external_point_charges.charges],
                [charge.charge for charge in self._external_point_charges.charges],
                radii=self._external_point_charges.radii,
                unit=self._external_point_charges.unit,
            )
            embedded_hcore = np.asarray(self._calc.get_hcore(), dtype=float)
            self.external_point_charge_potential_matrix_ao = embedded_hcore - base_hcore
            self.external_point_charge_nuclear_interaction_energy = float(
                self._calc.energy_nuc() - base_nuclear_energy
            )

        if self._chkfile is not None and os.path.exists(self._chkfile):
            self._calc.__dict__.update(lib_chkfile.load(self._chkfile, "scf"))
            LOGGER.info("PySCF loaded from chkfile e(hf): %s", self._calc.e_tot)
        else:
            self._calc.conv_tol = self._conv_tol
            self._calc.max_cycle = self._max_cycle
            self._calc.init_guess = self._init_guess
            self._calc.kernel()
            LOGGER.info(
                "PySCF kernel() converged: %s, e(hf): %s",
                self._calc.converged,
                self._calc.e_tot,
            )


def build_pyscf_driver(
    *,
    atom: str,
    unit,
    charge: int,
    spin: int,
    basis: str,
    method: MethodType,
    point_charges: ResolvedExternalPointCharges,
) -> PySCFDriver:
    """Build the appropriate PySCF driver for a molecule and embedding spec."""
    driver_cls = StaticPointChargePySCFDriver if point_charges.enabled else PySCFDriver
    kwargs = {
        "atom": atom,
        "unit": unit,
        "charge": charge,
        "spin": spin,
        "basis": basis,
        "method": method,
    }
    if point_charges.enabled:
        kwargs["point_charges"] = point_charges
    return driver_cls(**kwargs)
