"""Physical-sector basis helpers for finite-cutoff lattice-QED."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np

from qcchem.core import LatticeQEDSpec
from qcchem.qft.grid import LatticeGrid
from qcchem.qft.links import U1LinkOperators


@dataclass(slots=True)
class ProjectedBasis:
    """Basis states that satisfy the configured Gauss-law sector."""

    physical_indices: np.ndarray
    matter_indices: np.ndarray
    gauge_indices: np.ndarray
    occupations: np.ndarray
    gauge_digits: np.ndarray
    electric_levels: np.ndarray
    gauss_values: np.ndarray
    particle_numbers: np.ndarray
    index_by_full: dict[int, int]
    target_charge_values: list[float]

    @property
    def dimension(self) -> int:
        return int(self.physical_indices.size)

    def physical_sector_payload(
        self,
        *,
        max_qubits: int,
        tolerance: float,
        target_charge_sector: str,
    ) -> dict[str, Any]:
        indices = [int(value) for value in self.physical_indices.tolist()]
        return {
            "enumerated": True,
            "physical_sector_dimension": int(len(indices)),
            "basis_index_count": int(len(indices)),
            "basis_hash": _basis_hash(self.physical_indices),
            "basis_indices": indices,
            "basis_indices_preview": indices[:16],
            "padding_state_rejection_count": 0,
            "reference_basis_index": (indices[0] if indices else None),
            "tolerance": float(tolerance),
            "estimated_full_dimension": None,
            "skipped_reason": None,
            "target_charge_sector": target_charge_sector,
            "max_sector_enumeration_qubits": int(max_qubits),
            "builder": "sector_first",
        }


def _basis_hash(indices: np.ndarray) -> str:
    import hashlib

    array = np.asarray(indices, dtype=np.int64)
    return hashlib.sha256(array.tobytes()).hexdigest()


def matter_occupations(matter_index: int, matter_modes: int) -> tuple[int, ...]:
    """Return Jordan-Wigner occupations in mode order for a basis index."""
    return tuple(
        int((int(matter_index) >> (matter_modes - mode - 1)) & 1)
        for mode in range(matter_modes)
    )


def gauge_digits_from_index(
    gauge_index: int,
    *,
    link_count: int,
    encoded_dimension: int,
) -> tuple[int, ...]:
    digits: list[int] = []
    remaining = int(gauge_index)
    for link_position in range(link_count):
        divisor = encoded_dimension ** (link_count - link_position - 1)
        digit = remaining // divisor
        remaining %= divisor
        digits.append(int(digit))
    return tuple(digits)


def gauge_index_from_digits(digits: tuple[int, ...] | list[int], *, encoded_dimension: int) -> int:
    value = 0
    for digit in digits:
        value = value * int(encoded_dimension) + int(digit)
    return int(value)


def _target_charge_values(spec: LatticeQEDSpec, site_count: int) -> list[float]:
    raw = str(spec.constraints.target_charge_sector).strip().lower()
    if raw in {"neutral", "zero", "physical"}:
        return [0.0 for _ in range(site_count)]
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            "problem.qft.constraints.target_charge_sector must be 'neutral' or a numeric sector."
        ) from exc
    return [value for _ in range(site_count)]


def _link_adjacency(grid: LatticeGrid) -> tuple[dict[int, list[int]], dict[int, list[int]]]:
    incoming: dict[int, list[int]] = {site.linear_index: [] for site in grid.sites}
    outgoing: dict[int, list[int]] = {site.linear_index: [] for site in grid.sites}
    for link in grid.links:
        outgoing[link.start_site].append(link.linear_index)
        incoming[link.end_site].append(link.linear_index)
    return incoming, outgoing


def gauss_values_for_state(
    *,
    occupations: tuple[int, ...],
    electric_levels: tuple[float, ...],
    grid: LatticeGrid,
    spin_components: int,
) -> tuple[float, ...]:
    incoming, outgoing = _link_adjacency(grid)
    values: list[float] = []
    for site in grid.sites:
        divergence = 0.0
        for link_index in outgoing[site.linear_index]:
            divergence += float(electric_levels[link_index])
        for link_index in incoming[site.linear_index]:
            divergence -= float(electric_levels[link_index])
        local_density = sum(
            occupations[site.linear_index * spin_components + spin]
            for spin in range(spin_components)
        )
        values.append(
            float(divergence + local_density - float(grid.nuclear_charge_by_site[site.linear_index]))
        )
    return tuple(values)


def enumerate_projected_basis(
    grid: LatticeGrid,
    spec: LatticeQEDSpec,
    link_ops: U1LinkOperators,
    *,
    matter_modes: int,
    matter_dimension: int,
    gauge_dimension: int,
    total_qubits: int,
) -> ProjectedBasis:
    """Enumerate basis states in the target Gauss-law sector without padding states."""
    if total_qubits > int(spec.constraints.max_sector_enumeration_qubits):
        raise ValueError("total_qubits_exceeds_max_sector_enumeration_qubits")

    spin_components = int(spec.matter.spin_components)
    link_count = len(grid.links)
    target_charge_values = _target_charge_values(spec, grid.site_count)
    tolerance = float(spec.engine.projector_tolerance)

    physical_indices: list[int] = []
    matter_indices: list[int] = []
    gauge_indices: list[int] = []
    occupations_by_state: list[tuple[int, ...]] = []
    gauge_digits_by_state: list[tuple[int, ...]] = []
    electric_levels_by_state: list[tuple[float, ...]] = []
    gauss_by_state: list[tuple[float, ...]] = []
    particle_numbers: list[int] = []

    digit_ranges = [range(link_ops.physical_dimension) for _ in range(link_count)]
    for matter_index in range(matter_dimension):
        occupations = matter_occupations(matter_index, matter_modes)
        particle_number = int(sum(occupations))
        for digits in product(*digit_ranges):
            gauge_index = gauge_index_from_digits(digits, encoded_dimension=link_ops.encoded_dimension)
            if gauge_index >= gauge_dimension:
                continue
            levels = tuple(float(link_ops.levels[digit]) for digit in digits)
            gauss = gauss_values_for_state(
                occupations=occupations,
                electric_levels=levels,
                grid=grid,
                spin_components=spin_components,
            )
            residuals = [
                abs(float(value) - float(target))
                for value, target in zip(gauss, target_charge_values)
            ]
            if not all(value <= tolerance for value in residuals):
                continue
            full_index = int(matter_index * gauge_dimension + gauge_index)
            physical_indices.append(full_index)
            matter_indices.append(int(matter_index))
            gauge_indices.append(int(gauge_index))
            occupations_by_state.append(occupations)
            gauge_digits_by_state.append(tuple(int(value) for value in digits))
            electric_levels_by_state.append(levels)
            gauss_by_state.append(gauss)
            particle_numbers.append(particle_number)

    physical_array = np.asarray(physical_indices, dtype=np.int64)
    return ProjectedBasis(
        physical_indices=physical_array,
        matter_indices=np.asarray(matter_indices, dtype=np.int64),
        gauge_indices=np.asarray(gauge_indices, dtype=np.int64),
        occupations=np.asarray(occupations_by_state, dtype=np.int8),
        gauge_digits=np.asarray(gauge_digits_by_state, dtype=np.int16),
        electric_levels=np.asarray(electric_levels_by_state, dtype=float),
        gauss_values=np.asarray(gauss_by_state, dtype=float),
        particle_numbers=np.asarray(particle_numbers, dtype=np.int16),
        index_by_full={int(full): int(index) for index, full in enumerate(physical_array.tolist())},
        target_charge_values=target_charge_values,
    )
