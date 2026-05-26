"""Periodic QM/MM Ewald constants for fixed point charges."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np


BOHR_PER_ANGSTROM = 1.8897259886


@dataclass(frozen=True, slots=True)
class PeriodicPointCharge:
    """One fixed point charge in a periodic cell."""

    label: str | None
    coords: tuple[float, float, float]
    charge: float


@dataclass(frozen=True, slots=True)
class EwaldSettings:
    """Numerical controls for the cross Ewald sum."""

    alpha: float | None = None
    real_space_cutoff: float | None = None
    reciprocal_cutoff: float | None = None
    neutrality_tolerance: float = 1.0e-10
    unit: str = "bohr"
    total_cell_charge: float | None = None


@dataclass(frozen=True, slots=True)
class PeriodicQMMMEwaldResult:
    """Periodic QM/MM nuclear-point-charge constant and audit payload."""

    energy_hartree: float
    fingerprint: str
    payload: dict[str, Any]


def _unit_scale(unit: str) -> float:
    normalized = unit.strip().lower()
    if normalized in {"bohr", "au", "a.u."}:
        return 1.0
    if normalized in {"angstrom", "ang"}:
        return BOHR_PER_ANGSTROM
    raise ValueError(f"Unsupported Ewald coordinate unit: {unit}")


def _as_vector(value: Sequence[float], *, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (3,):
        raise ValueError(f"{name} must be a 3-vector.")
    return array


def _as_lattice(lattice_vectors: Sequence[Sequence[float]], *, scale: float) -> np.ndarray:
    lattice = np.asarray(lattice_vectors, dtype=float)
    if lattice.shape != (3, 3):
        raise ValueError("lattice_vectors must be a 3x3 matrix.")
    lattice = lattice * scale
    volume = float(abs(np.linalg.det(lattice)))
    if volume <= 0.0:
        raise ValueError("lattice_vectors must define a nonzero cell volume.")
    return lattice


def _charges_to_payload(charges: Iterable[PeriodicPointCharge]) -> list[dict[str, Any]]:
    return [
        {
            "label": charge.label,
            "coords_bohr": [float(value) for value in charge.coords],
            "charge": float(charge.charge),
        }
        for charge in charges
    ]


def _scaled_charges(
    charges: Iterable[PeriodicPointCharge],
    *,
    scale: float,
) -> list[PeriodicPointCharge]:
    return [
        PeriodicPointCharge(
            label=charge.label,
            coords=tuple(float(value) * scale for value in charge.coords),
            charge=float(charge.charge),
        )
        for charge in charges
    ]


def _integer_translations(lattice: np.ndarray, cutoff: float) -> list[np.ndarray]:
    lengths = np.linalg.norm(lattice, axis=1)
    limits = [int(math.ceil(cutoff / max(length, 1.0e-15))) + 1 for length in lengths]
    translations: list[np.ndarray] = []
    for i in range(-limits[0], limits[0] + 1):
        for j in range(-limits[1], limits[1] + 1):
            for k in range(-limits[2], limits[2] + 1):
                vector = i * lattice[0] + j * lattice[1] + k * lattice[2]
                if np.linalg.norm(vector) <= cutoff + max(lengths):
                    translations.append(vector)
    return translations


def _reciprocal_vectors(lattice: np.ndarray, cutoff: float) -> list[np.ndarray]:
    reciprocal = 2.0 * math.pi * np.linalg.inv(lattice).T
    lengths = np.linalg.norm(reciprocal, axis=1)
    limits = [int(math.ceil(cutoff / max(length, 1.0e-15))) for length in lengths]
    vectors: list[np.ndarray] = []
    for h in range(-limits[0], limits[0] + 1):
        for k in range(-limits[1], limits[1] + 1):
            for l in range(-limits[2], limits[2] + 1):
                if h == 0 and k == 0 and l == 0:
                    continue
                vector = h * reciprocal[0] + k * reciprocal[1] + l * reciprocal[2]
                if np.linalg.norm(vector) <= cutoff + 1.0e-14:
                    vectors.append(vector)
    return vectors


def _default_settings(
    lattice: np.ndarray,
    settings: EwaldSettings,
) -> tuple[float, float, float]:
    lengths = np.linalg.norm(lattice, axis=1)
    shortest = float(np.min(lengths))
    alpha = float(settings.alpha if settings.alpha is not None else 5.0 / shortest)
    if alpha <= 0.0:
        raise ValueError("Ewald alpha must be positive.")
    real_cutoff = float(
        settings.real_space_cutoff
        if settings.real_space_cutoff is not None
        else shortest / 2.0
    )
    reciprocal_cutoff = float(
        settings.reciprocal_cutoff
        if settings.reciprocal_cutoff is not None
        else 8.0 * alpha
    )
    if real_cutoff <= 0.0 or reciprocal_cutoff <= 0.0:
        raise ValueError("Ewald cutoffs must be positive.")
    return alpha, real_cutoff, reciprocal_cutoff


def periodic_qmmm_nuclear_point_charge_energy(
    *,
    lattice_vectors: Sequence[Sequence[float]],
    qm_nuclear_charges: Sequence[PeriodicPointCharge],
    mm_point_charges: Sequence[PeriodicPointCharge],
    settings: EwaldSettings | None = None,
) -> PeriodicQMMMEwaldResult:
    """Compute the periodic cross Ewald energy between QM nuclei and MM charges.

    The result is the constant term added to the electronic problem when MM point
    charges are represented as fixed classical sources. A strict neutrality gate
    is used because the G=0 contribution is not well-defined for a charged cell.
    """

    controls = settings or EwaldSettings()
    scale = _unit_scale(controls.unit)
    lattice = _as_lattice(lattice_vectors, scale=scale)
    qm = _scaled_charges(qm_nuclear_charges, scale=scale)
    mm = _scaled_charges(mm_point_charges, scale=scale)
    if not qm:
        raise ValueError("At least one QM nuclear charge is required.")
    if not mm:
        raise ValueError("At least one MM point charge is required.")
    source_charge = sum(charge.charge for charge in qm) + sum(
        charge.charge for charge in mm
    )
    if controls.total_cell_charge is None:
        raise ValueError(
            "Periodic QM/MM Ewald requires total_cell_charge including QM electrons "
            "and MM point charges for the neutrality gate."
        )
    total_charge = float(controls.total_cell_charge)
    neutral = abs(total_charge) <= controls.neutrality_tolerance
    if not neutral:
        raise ValueError(
            "Periodic QM/MM Ewald requires a neutral full QM/MM cell including QM electrons: "
            f"total_cell_charge={total_charge:.12g}, tolerance={controls.neutrality_tolerance:.3g}."
        )

    alpha, real_cutoff, reciprocal_cutoff = _default_settings(lattice, controls)
    translations = _integer_translations(lattice, real_cutoff)
    reciprocal_vectors = _reciprocal_vectors(lattice, reciprocal_cutoff)
    volume = float(abs(np.linalg.det(lattice)))

    real_energy = 0.0
    for qnuc in qm:
        r_qm = _as_vector(qnuc.coords, name="qm charge coordinates")
        for mm_charge in mm:
            r_mm = _as_vector(mm_charge.coords, name="mm charge coordinates")
            prefactor = qnuc.charge * mm_charge.charge
            for translation in translations:
                delta = r_qm - r_mm + translation
                distance = float(np.linalg.norm(delta))
                if distance <= 1.0e-14 or distance > real_cutoff:
                    continue
                real_energy += prefactor * math.erfc(alpha * distance) / distance

    reciprocal_energy = 0.0
    for vector in reciprocal_vectors:
        g2 = float(np.dot(vector, vector))
        factor = (4.0 * math.pi / volume) * math.exp(-g2 / (4.0 * alpha * alpha)) / g2
        rho_qm = sum(
            charge.charge
            * np.exp(
                1j
                * float(
                    np.dot(
                        vector,
                        _as_vector(charge.coords, name="qm charge coordinates"),
                    )
                )
            )
            for charge in qm
        )
        rho_mm = sum(
            charge.charge
            * np.exp(
                -1j
                * float(
                    np.dot(
                        vector,
                        _as_vector(charge.coords, name="mm charge coordinates"),
                    )
                )
            )
            for charge in mm
        )
        reciprocal_energy += factor * float(np.real(rho_qm * rho_mm))

    payload = {
        "schema": "qcchem.pbc.qmmm_ewald.v1",
        "lattice_vectors_bohr": lattice.tolist(),
        "qm_nuclear_charges": _charges_to_payload(qm),
        "mm_point_charges": _charges_to_payload(mm),
        "settings": {
            "alpha": alpha,
            "real_space_cutoff": real_cutoff,
            "reciprocal_cutoff": reciprocal_cutoff,
            "neutrality_tolerance": float(controls.neutrality_tolerance),
        },
        "neutrality": {
            "total_charge": float(total_charge),
            "source_charge_without_qm_electrons": float(source_charge),
            "passed": neutral,
        },
        "components": {
            "real_space_hartree": float(real_energy),
            "reciprocal_space_hartree": float(reciprocal_energy),
            "self_hartree": 0.0,
        },
        "energy_hartree": float(real_energy + reciprocal_energy),
        "provenance": {
            "adapter": "qcchem.pbc.ewald.periodic_qmmm_nuclear_point_charge_energy",
            "semantics": "cross Ewald energy between QM nuclear charges and fixed MM point charges",
            "g_zero_policy": "rejected unless the full QM/MM cell, including QM electrons, is neutral",
        },
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return PeriodicQMMMEwaldResult(
        energy_hartree=float(payload["energy_hartree"]),
        fingerprint=fingerprint,
        payload={**payload, "fingerprint": fingerprint},
    )
