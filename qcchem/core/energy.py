"""Shared energy bookkeeping for local and retrieved runtime estimates."""

from __future__ import annotations

from math import fsum, isfinite

ENERGY_CONSTANT_KEYS = (
    "constant_energy_correction", "nuclear_repulsion_energy",
    "external_point_charge_nuclear_interaction_energy", "boundary_embedding_constant_energy",
)


def total_energy_from_solver(solver_energy: float, constants: dict) -> float:
    values = [float(solver_energy), *(float(constants.get(key) or 0.0) for key in ENERGY_CONSTANT_KEYS)]
    if not all(isfinite(value) for value in values):
        raise ValueError("Energy estimates and constants must be finite.")
    return fsum(values)
