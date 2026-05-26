"""Trusted active-space recommendation heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from qcchem.core import AutoActiveSpaceSpec


@dataclass(slots=True)
class OrbitalDiagnostics:
    """Orbital-level inputs used by the trusted active-space recommender."""

    orbital_energies: list[float]
    scf_occupations: list[float]
    natural_occupations: list[float] | None
    natural_occupation_source: str
    fallback_reasons: list[str]
    symmetry_labels: list[str] | None = None


@dataclass(slots=True)
class TrustedActiveSpaceRecommendationResult:
    """Resolved trusted active-space recommendation."""

    selected_current: list[int]
    selected_original: list[int]
    num_electrons: tuple[int, int]
    num_spatial_orbitals: int
    recommendation: dict[str, Any]


def _as_float_list(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (tuple, list)) and value and isinstance(value[0], np.ndarray):
        alpha = np.asarray(value[0], dtype=float).reshape(-1)
        beta = np.asarray(value[1], dtype=float).reshape(-1) if len(value) > 1 else np.zeros_like(alpha)
        return (alpha + beta).tolist()
    return np.asarray(value, dtype=float).reshape(-1).tolist()


def _mp2_natural_occupations(calc: Any) -> tuple[list[float] | None, str | None]:
    try:
        from pyscf import mp

        if isinstance(getattr(calc, "mo_coeff", None), (tuple, list)):
            return None, "MP2 natural occupations are only enabled for restricted references."
        mp2 = mp.MP2(calc).run(verbose=0)
        rdm1 = np.asarray(mp2.make_rdm1(), dtype=float)
        if rdm1.ndim != 2:
            return None, "MP2 one-particle density matrix was not a 2D array."
        occupations = np.diag(rdm1).reshape(-1).tolist()
        return [float(value) for value in occupations], None
    except Exception as exc:  # pragma: no cover - defensive PySCF boundary
        return None, f"MP2 natural occupations unavailable: {type(exc).__name__}: {exc}"


def build_orbital_diagnostics_from_pyscf_driver(
    pyscf_driver: Any | None,
    *,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
    available_original: list[int],
    natural_occupation_source: str,
) -> OrbitalDiagnostics:
    """Extract PySCF orbital diagnostics, with deterministic fallback data."""
    fallback_reasons: list[str] = []
    energies: list[float] = []
    occupations: list[float] = []
    natural_occupations: list[float] | None = None
    source = natural_occupation_source.strip().lower()

    calc = getattr(pyscf_driver, "_calc", None) if pyscf_driver is not None else None
    if calc is not None:
        energies = _as_float_list(getattr(calc, "mo_energy", None))
        occupations = _as_float_list(getattr(calc, "mo_occ", None))
        if source == "mp2":
            natural_occupations, reason = _mp2_natural_occupations(calc)
            if reason is not None:
                fallback_reasons.append(reason)
        elif source == "scf":
            natural_occupations = list(occupations)
        else:
            fallback_reasons.append("natural occupations disabled")
    else:
        fallback_reasons.append("PySCF driver diagnostics unavailable; using Aufbau fallback occupations.")

    if not occupations:
        alpha, beta = int(num_particles[0]), int(num_particles[1])
        occupations = []
        for index in range(num_spatial_orbitals):
            occ = (1.0 if index < alpha else 0.0) + (1.0 if index < beta else 0.0)
            occupations.append(occ)
    if not energies:
        energies = [float(index) for index in range(num_spatial_orbitals)]

    energies = _filter_by_available(energies, available_original, num_spatial_orbitals)
    occupations = _filter_by_available(occupations, available_original, num_spatial_orbitals)
    if natural_occupations is not None:
        natural_occupations = _filter_by_available(natural_occupations, available_original, num_spatial_orbitals)
        if len(natural_occupations) != num_spatial_orbitals:
            fallback_reasons.append("Natural occupation vector did not match available orbital count.")
            natural_occupations = None

    return OrbitalDiagnostics(
        orbital_energies=energies,
        scf_occupations=occupations,
        natural_occupations=natural_occupations,
        natural_occupation_source=source,
        fallback_reasons=fallback_reasons,
    )


def _filter_by_available(values: list[float], available_original: list[int], fallback_size: int) -> list[float]:
    filtered: list[float] = []
    for current_index, original_index in enumerate(available_original):
        if original_index < len(values):
            filtered.append(float(values[original_index]))
        elif current_index < len(values):
            filtered.append(float(values[current_index]))
    if len(filtered) < fallback_size:
        filtered.extend(float(index) for index in range(len(filtered), fallback_size))
    return filtered[:fallback_size]


def _frontier_window(num_spatial_orbitals: int, occupied_spatial_orbitals: int, desired_size: int) -> list[int]:
    desired = max(1, min(desired_size, num_spatial_orbitals))
    start = max(0, occupied_spatial_orbitals - desired // 2)
    end = start + desired
    if end > num_spatial_orbitals:
        end = num_spatial_orbitals
        start = max(0, end - desired)
    return list(range(start, end))


def _selected_electrons(current_orbitals: list[int], num_particles: tuple[int, int]) -> tuple[int, int]:
    inactive_doubly_occupied = current_orbitals[0] if current_orbitals else 0
    alpha = max(int(num_particles[0]) - inactive_doubly_occupied, 0)
    beta = max(int(num_particles[1]) - inactive_doubly_occupied, 0)
    return alpha, beta


def _seed_orbitals(
    diagnostics: OrbitalDiagnostics,
    *,
    occupied_spatial_orbitals: int,
    energy_window_hartree: float,
    occupation_tolerance: float,
) -> tuple[set[int], dict[int, float]]:
    n_orbitals = len(diagnostics.orbital_energies)
    homo = max(0, min(occupied_spatial_orbitals - 1, n_orbitals - 1))
    lumo = max(0, min(occupied_spatial_orbitals, n_orbitals - 1))
    seed = {homo, lumo}
    energies = diagnostics.orbital_energies
    if energies:
        homo_energy = energies[homo]
        lumo_energy = energies[lumo]
        for index, energy in enumerate(energies):
            reference = homo_energy if index <= homo else lumo_energy
            if abs(float(energy) - float(reference)) <= energy_window_hartree:
                seed.add(index)

    fractional_weights: dict[int, float] = {}
    if diagnostics.natural_occupations is not None:
        for index, occupation in enumerate(diagnostics.natural_occupations):
            distance_to_closed_shell = min(abs(float(occupation)), abs(2.0 - float(occupation)))
            if distance_to_closed_shell > occupation_tolerance:
                weight = min(1.0, distance_to_closed_shell / max(occupation_tolerance, 1.0e-12))
                fractional_weights[index] = weight
                seed.add(index)
    return seed, fractional_weights


def _candidate_windows(
    num_spatial_orbitals: int,
    occupied_spatial_orbitals: int,
    min_size: int,
    max_size: int,
    seed: set[int],
) -> list[list[int]]:
    windows: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    for size in range(min_size, max_size + 1):
        starts = {0, max(0, occupied_spatial_orbitals - size // 2), max(0, num_spatial_orbitals - size)}
        if seed:
            low = min(seed)
            high = max(seed)
            starts.add(max(0, min(low, num_spatial_orbitals - size)))
            starts.add(max(0, min(high - size + 1, num_spatial_orbitals - size)))
        for start in sorted(starts):
            end = start + size
            if end > num_spatial_orbitals:
                continue
            window = tuple(range(start, end))
            if window not in seen:
                seen.add(window)
                windows.append(list(window))
    return windows


def _score_candidate(
    window: list[int],
    *,
    seed: set[int],
    fractional_weights: dict[int, float],
    occupied_spatial_orbitals: int,
    min_size: int,
    max_size: int,
    max_qubits: int | None,
) -> tuple[float, dict[str, float]]:
    window_set = set(window)
    seed_coverage = len(window_set & seed) / max(len(seed), 1)
    fractional_total = sum(fractional_weights.values())
    fractional_score = (
        sum(weight for index, weight in fractional_weights.items() if index in window_set) / fractional_total
        if fractional_total > 0.0
        else seed_coverage
    )
    homo = max(0, occupied_spatial_orbitals - 1)
    lumo = occupied_spatial_orbitals
    frontier_score = float(homo in window_set and lumo in window_set)
    span = max(max_size - min_size, 1)
    compactness = 1.0 - ((len(window) - min_size) / span)
    if max_qubits is None:
        resource_score = 1.0
    else:
        resource_score = max(0.0, 1.0 - ((2 * len(window)) / max(max_qubits, 1)))
    score = (
        0.35 * seed_coverage
        + 0.25 * fractional_score
        + 0.25 * frontier_score
        + 0.10 * compactness
        + 0.05 * resource_score
    )
    terms = {
        "seed_coverage": seed_coverage,
        "fractional_occupation": fractional_score,
        "frontier_boundary": frontier_score,
        "compactness": compactness,
        "resource_margin": resource_score,
    }
    return score, terms


def _round_terms(values: dict[str, float]) -> dict[str, float]:
    return {key: round(float(value), 6) for key, value in values.items()}


def _candidate_payload(
    window: list[int],
    *,
    available_original: list[int],
    num_particles: tuple[int, int],
    score: float,
    terms: dict[str, float],
) -> dict[str, Any]:
    num_electrons = _selected_electrons(window, num_particles)
    return {
        "active_orbitals": list(window),
        "active_orbitals_original": [available_original[index] for index in window],
        "num_electrons": list(num_electrons),
        "num_spatial_orbitals": len(window),
        "num_qubits": 2 * len(window),
        "score": round(float(score), 6),
        "score_terms": _round_terms(terms),
    }


def recommend_trusted_active_space(
    diagnostics: OrbitalDiagnostics,
    auto: AutoActiveSpaceSpec,
    *,
    num_particles: tuple[int, int],
    available_original: list[int],
) -> TrustedActiveSpaceRecommendationResult:
    """Recommend a contiguous active space using auditable orbital scoring."""
    num_spatial_orbitals = len(available_original)
    if num_spatial_orbitals <= 0:
        raise ValueError("trusted active-space recommendation requires at least one available orbital.")

    max_size = auto.max_spatial_orbitals
    if max_size is None:
        max_size = max(auto.min_spatial_orbitals, auto.num_occupied + auto.num_virtual)
    max_size = min(max_size, num_spatial_orbitals)
    min_size = min(max(1, auto.min_spatial_orbitals), num_spatial_orbitals)
    if max_size < min_size:
        raise ValueError("trusted active-space max_spatial_orbitals cannot satisfy min_spatial_orbitals.")
    if auto.max_qubits is not None and 2 * min_size > auto.max_qubits:
        raise ValueError("trusted active-space max_qubits cannot satisfy min_spatial_orbitals.")

    occupied_spatial_orbitals = max(int(num_particles[0]), int(num_particles[1]))
    occupied_spatial_orbitals = max(1, min(occupied_spatial_orbitals, num_spatial_orbitals - 1))
    seed, fractional_weights = _seed_orbitals(
        diagnostics,
        occupied_spatial_orbitals=occupied_spatial_orbitals,
        energy_window_hartree=max(float(auto.energy_window_hartree), 0.0),
        occupation_tolerance=max(float(auto.occupation_tolerance), 0.0),
    )
    windows = _candidate_windows(
        num_spatial_orbitals,
        occupied_spatial_orbitals,
        min_size,
        max_size,
        seed,
    )
    if not windows:
        windows = [_frontier_window(num_spatial_orbitals, occupied_spatial_orbitals, min_size)]

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for window in windows:
        score, terms = _score_candidate(
            window,
            seed=seed,
            fractional_weights=fractional_weights,
            occupied_spatial_orbitals=occupied_spatial_orbitals,
            min_size=min_size,
            max_size=max(max_size, min_size),
            max_qubits=auto.max_qubits,
        )
        payload = _candidate_payload(
            window,
            available_original=available_original,
            num_particles=num_particles,
            score=score,
            terms=terms,
        )
        if auto.max_qubits is not None and payload["num_qubits"] > auto.max_qubits:
            rejected.append({**payload, "reason": "exceeds_max_qubits"})
            continue
        accepted.append(payload)

    if not accepted:
        raise ValueError("trusted active-space recommendation found no candidates within max_qubits.")

    accepted.sort(key=lambda item: (-float(item["score"]), int(item["num_qubits"]), item["active_orbitals"]))
    accepted = accepted[: max(1, int(auto.max_candidates))]
    selected = accepted[0]
    selected_current = [int(index) for index in selected["active_orbitals"]]
    selected_original = [int(index) for index in selected["active_orbitals_original"]]
    confidence = max(0.35, min(0.95, float(selected["score"])))
    diagnostics_payload = []
    for current_index, original_index in enumerate(available_original):
        natural = (
            diagnostics.natural_occupations[current_index]
            if diagnostics.natural_occupations is not None and current_index < len(diagnostics.natural_occupations)
            else None
        )
        diagnostics_payload.append(
            {
                "current_index": current_index,
                "original_index": original_index,
                "orbital_energy_hartree": (
                    diagnostics.orbital_energies[current_index]
                    if current_index < len(diagnostics.orbital_energies)
                    else None
                ),
                "scf_occupation": (
                    diagnostics.scf_occupations[current_index]
                    if current_index < len(diagnostics.scf_occupations)
                    else None
                ),
                "natural_occupation": natural,
                "seed_orbital": current_index in seed,
                "fractional_natural_weight": round(float(fractional_weights.get(current_index, 0.0)), 6),
            }
        )
    recommendation = {
        "strategy": "trusted_orbital_score",
        "confidence": round(confidence, 6),
        "selected": selected,
        "candidates": accepted,
        "rejected_candidates": rejected,
        "orbital_diagnostics": diagnostics_payload,
        "warnings": list(diagnostics.fallback_reasons),
        "provenance": {
            "source": "qcchem.chem.active_space_recommender",
            "natural_occupation_source": diagnostics.natural_occupation_source,
            "energy_window_hartree": float(auto.energy_window_hartree),
            "occupation_tolerance": float(auto.occupation_tolerance),
            "max_candidates": int(auto.max_candidates),
        },
    }
    return TrustedActiveSpaceRecommendationResult(
        selected_current=selected_current,
        selected_original=selected_original,
        num_electrons=tuple(int(value) for value in selected["num_electrons"]),
        num_spatial_orbitals=int(selected["num_spatial_orbitals"]),
        recommendation=recommendation,
    )
