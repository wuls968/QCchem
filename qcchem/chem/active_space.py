"""Active-space selection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qcchem.core import ActiveSpaceSpec
from qcchem.chem.active_space_recommender import (
    build_orbital_diagnostics_from_pyscf_driver,
    recommend_trusted_active_space,
)


@dataclass(slots=True)
class ResolvedActiveSpace:
    """Resolved active-space configuration after QCchem heuristics."""

    num_electrons: int | tuple[int, int]
    num_spatial_orbitals: int
    active_orbitals_current: list[int]
    active_orbitals_original: list[int]
    selection_mode: str
    selection_reason: str
    recommendation_metadata: dict[str, Any] | None = None


def infer_frozen_core_orbitals(
    original_num_spatial_orbitals: int,
    post_freeze_num_spatial_orbitals: int,
    remove_orbitals: list[int],
) -> list[int]:
    """Infer frozen core orbitals from orbital count changes."""
    frozen_count = max(
        original_num_spatial_orbitals - post_freeze_num_spatial_orbitals - len(remove_orbitals),
        0,
    )
    return list(range(frozen_count))


def available_original_orbitals(
    original_num_spatial_orbitals: int,
    frozen_core_orbitals: list[int],
    remove_orbitals: list[int],
) -> list[int]:
    """Return the original-space orbital indices still available after reductions."""
    removed = set(frozen_core_orbitals) | set(remove_orbitals)
    return [index for index in range(original_num_spatial_orbitals) if index not in removed]


def _frontier_window(
    num_spatial_orbitals: int,
    occupied_spatial_orbitals: int,
    desired_size: int,
) -> list[int]:
    desired = max(1, min(desired_size, num_spatial_orbitals))
    start = max(0, occupied_spatial_orbitals - desired // 2)
    end = start + desired
    if end > num_spatial_orbitals:
        end = num_spatial_orbitals
        start = max(0, end - desired)
    return list(range(start, end))


def resolve_active_space(
    spec: ActiveSpaceSpec | None,
    *,
    num_particles: tuple[int, int],
    num_spatial_orbitals: int,
    available_original: list[int],
    pyscf_driver: Any | None = None,
) -> ResolvedActiveSpace | None:
    """Resolve manual or automatic active-space selection."""
    if spec is None:
        return None

    selection_mode = spec.selection_mode.strip().lower()
    if selection_mode == "auto":
        strategy = spec.auto.strategy.strip().lower()
        if strategy == "trusted_orbital_score":
            diagnostics = build_orbital_diagnostics_from_pyscf_driver(
                pyscf_driver,
                num_spatial_orbitals=num_spatial_orbitals,
                num_particles=num_particles,
                available_original=available_original,
                natural_occupation_source=spec.auto.natural_occupation_source,
            )
            recommendation = recommend_trusted_active_space(
                diagnostics,
                spec.auto,
                num_particles=num_particles,
                available_original=available_original,
            )
            return ResolvedActiveSpace(
                num_electrons=recommendation.num_electrons,
                num_spatial_orbitals=recommendation.num_spatial_orbitals,
                active_orbitals_current=recommendation.selected_current,
                active_orbitals_original=recommendation.selected_original,
                selection_mode="auto",
                selection_reason=(
                    "Trusted orbital score selected an auditable active-space window "
                    f"with confidence {recommendation.recommendation['confidence']}."
                ),
                recommendation_metadata=recommendation.recommendation,
            )
        if strategy != "frontier_orbitals":
            raise ValueError(f"Unsupported active-space auto strategy: {spec.auto.strategy}")
        if spec.num_spatial_orbitals is None:
            desired_size = max(spec.auto.num_occupied + spec.auto.num_virtual, 2)
        else:
            desired_size = spec.num_spatial_orbitals
        occupied = max(int(num_particles[0]), int(num_particles[1]))
        current_orbitals = _frontier_window(num_spatial_orbitals, occupied, desired_size)
        original_orbitals = [available_original[index] for index in current_orbitals]
        inactive_doubly_occupied = current_orbitals[0] if current_orbitals else 0
        alpha = max(int(num_particles[0]) - inactive_doubly_occupied, 0)
        beta = max(int(num_particles[1]) - inactive_doubly_occupied, 0)
        return ResolvedActiveSpace(
            num_electrons=(alpha, beta),
            num_spatial_orbitals=len(current_orbitals),
            active_orbitals_current=current_orbitals,
            active_orbitals_original=original_orbitals,
            selection_mode="auto",
            selection_reason=(
                "Frontier-orbitals heuristic selected a contiguous active window "
                f"around the occupied/virtual boundary with {len(current_orbitals)} orbitals."
            ),
        )

    if spec.active_orbitals is not None:
        current_orbitals = []
        original_orbitals = [int(value) for value in spec.active_orbitals]  # interpreted in original MO space
        for orbital in original_orbitals:
            if orbital not in available_original:
                raise ValueError(
                    f"Requested active orbital {orbital} is not available after freeze-core/remove-orbital reductions."
                )
            current_orbitals.append(available_original.index(orbital))
    else:
        if spec.num_spatial_orbitals is None or spec.num_electrons is None:
            raise ValueError("Manual active-space selection requires num_electrons and num_spatial_orbitals.")
        current_orbitals = []
        original_orbitals = []

    if spec.num_electrons is None or spec.num_spatial_orbitals is None:
        raise ValueError("Manual active-space selection requires num_electrons and num_spatial_orbitals.")

    return ResolvedActiveSpace(
        num_electrons=spec.num_electrons,
        num_spatial_orbitals=int(spec.num_spatial_orbitals),
        active_orbitals_current=current_orbitals,
        active_orbitals_original=original_orbitals,
        selection_mode="manual",
        selection_reason=(
            "Manual active-space selection from user-provided orbital list and electron counts."
            if original_orbitals
            else "Manual active-space selection from user-provided electron/orbital counts; Qiskit Nature chooses the orbital window."
        ),
    )
