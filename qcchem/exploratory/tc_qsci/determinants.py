"""Determinant-space helpers for JW spin-orbital bitstrings."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np


@dataclass(slots=True)
class DeterminantInfo:
    """Symmetry metadata for one computational-basis determinant."""

    index: int
    bitstring: str
    occupied_spin_orbitals: list[int]
    alpha_electrons: int
    beta_electrons: int
    total_electrons: int
    spin_projection: float
    point_group_label: str | None = None


@dataclass(slots=True)
class InitialState:
    """Sparse determinant initial state embedded in a full state vector."""

    kind: str
    vector: np.ndarray
    determinants: list[int]
    coefficients: dict[int, complex]


def index_to_bitstring(index: int, num_qubits: int) -> str:
    """Return a Qiskit-style computational bitstring label."""
    return format(int(index), f"0{int(num_qubits)}b")


def bitstring_to_index(bitstring: str, num_qubits: int) -> int:
    """Parse a computational bitstring label into an integer basis index."""
    cleaned = bitstring.strip().replace("_", "")
    if len(cleaned) != num_qubits or any(char not in {"0", "1"} for char in cleaned):
        raise ValueError(f"Invalid determinant bitstring for {num_qubits} qubits: {bitstring}")
    return int(cleaned, 2)


def occupied_spin_orbitals(index: int, num_qubits: int) -> list[int]:
    """Return occupied spin-orbital indices using JW qubit index order."""
    return [orbital for orbital in range(num_qubits) if (int(index) >> orbital) & 1]


def determinant_sector(
    index: int,
    *,
    num_spatial_orbitals: int,
    point_group_labels: list[str] | None = None,
) -> DeterminantInfo:
    """Describe electron-number and S_z sector metadata for one determinant."""
    num_qubits = 2 * int(num_spatial_orbitals)
    occupied = occupied_spin_orbitals(index, num_qubits)
    alpha = sum(1 for orbital in occupied if orbital < num_spatial_orbitals)
    beta = sum(1 for orbital in occupied if orbital >= num_spatial_orbitals)
    label = None
    if point_group_labels:
        labels = [
            point_group_labels[orbital]
            for orbital in occupied
            if orbital < len(point_group_labels)
        ]
        label = " ".join(labels) if labels else None
    return DeterminantInfo(
        index=int(index),
        bitstring=index_to_bitstring(index, num_qubits),
        occupied_spin_orbitals=occupied,
        alpha_electrons=int(alpha),
        beta_electrons=int(beta),
        total_electrons=int(alpha + beta),
        spin_projection=float((alpha - beta) / 2.0),
        point_group_label=label,
    )


def hartree_fock_determinant(num_spatial_orbitals: int, num_particles: tuple[int, int]) -> int:
    """Build the closed/open-shell HF determinant in Qiskit Nature spin-orbital ordering."""
    alpha, beta = (int(num_particles[0]), int(num_particles[1]))
    if alpha > num_spatial_orbitals or beta > num_spatial_orbitals:
        raise ValueError("HF determinant requires particle counts no larger than spatial orbital count.")
    index = 0
    for orbital in range(alpha):
        index |= 1 << orbital
    for orbital in range(beta):
        index |= 1 << (num_spatial_orbitals + orbital)
    return index


def determinants_in_sector(
    *,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
    point_group_labels: list[str] | None = None,
) -> list[DeterminantInfo]:
    """Enumerate JW determinants with fixed alpha/beta electron counts."""
    alpha, beta = (int(num_particles[0]), int(num_particles[1]))
    determinants: list[DeterminantInfo] = []
    for alpha_occ in combinations(range(num_spatial_orbitals), alpha):
        alpha_bits = sum(1 << orbital for orbital in alpha_occ)
        for beta_occ in combinations(range(num_spatial_orbitals), beta):
            beta_bits = sum(1 << (num_spatial_orbitals + orbital) for orbital in beta_occ)
            determinants.append(
                determinant_sector(
                    alpha_bits | beta_bits,
                    num_spatial_orbitals=num_spatial_orbitals,
                    point_group_labels=point_group_labels,
                )
            )
    determinants.sort(key=lambda item: item.index)
    return determinants


def filter_determinants_by_sector(
    determinants: list[int],
    *,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
) -> list[int]:
    """Filter determinant indices to the configured alpha/beta sector."""
    alpha, beta = (int(num_particles[0]), int(num_particles[1]))
    filtered: list[int] = []
    for determinant in determinants:
        sector = determinant_sector(determinant, num_spatial_orbitals=num_spatial_orbitals)
        if sector.alpha_electrons == alpha and sector.beta_electrons == beta:
            filtered.append(int(determinant))
    return filtered


def _excitation_rank(reference: int, determinant: int) -> int:
    changed_orbitals = int((int(reference) ^ int(determinant)).bit_count())
    return changed_orbitals // 2


def _coefficient_from_entry(entry: dict[str, Any]) -> complex:
    coeff = entry.get("coefficient", 1.0)
    if isinstance(coeff, dict):
        return complex(float(coeff.get("real", 0.0)), float(coeff.get("imag", 0.0)))
    if isinstance(coeff, (list, tuple)) and len(coeff) == 2:
        return complex(float(coeff[0]), float(coeff[1]))
    return complex(coeff)


def build_initial_state(
    *,
    kind: str,
    num_qubits: int,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
    entries: list[dict[str, Any]] | None = None,
    operator=None,
    max_determinants: int | None = None,
) -> InitialState:
    """Build an HF/CISD/FCI-truncated/sparse multiconfiguration initial vector."""
    normalized = kind.strip().lower()
    hf_index = hartree_fock_determinant(num_spatial_orbitals, num_particles)
    sector_determinants = [item.index for item in determinants_in_sector(
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
    )]
    coefficients: dict[int, complex] = {}

    if normalized == "hf":
        coefficients[hf_index] = 1.0 + 0.0j
    elif normalized == "cisd":
        for determinant in sector_determinants:
            if _excitation_rank(hf_index, determinant) <= 2:
                coefficients[determinant] = 1.0 + 0.0j
    elif normalized == "fci_truncated":
        if operator is None:
            determinants = sector_determinants
            if max_determinants is not None:
                determinants = determinants[: max(int(max_determinants), 1)]
            for determinant in determinants:
                coefficients[determinant] = 1.0 + 0.0j
        else:
            matrix = build_selected_subspace_matrix(operator, sector_determinants)
            _, eigenvectors = np.linalg.eigh(matrix)
            ground = np.asarray(eigenvectors[:, 0], dtype=complex)
            ranked = sorted(
                zip(sector_determinants, ground, strict=True),
                key=lambda item: (-abs(item[1]), item[0]),
            )
            if max_determinants is not None:
                ranked = ranked[: max(int(max_determinants), 1)]
            coefficients = {int(det): complex(coeff) for det, coeff in ranked if abs(coeff) > 0.0}
    elif normalized == "sparse_multiconfig":
        if not entries:
            raise ValueError("sparse_multiconfig initial state requires determinant entries.")
        for entry in entries:
            if "index" in entry:
                determinant = int(entry["index"])
            elif "bitstring" in entry:
                determinant = bitstring_to_index(str(entry["bitstring"]), num_qubits)
            else:
                raise ValueError("Each sparse_multiconfig entry requires index or bitstring.")
            coefficients[determinant] = coefficients.get(determinant, 0.0j) + _coefficient_from_entry(entry)
    else:
        raise ValueError(f"Unsupported TC-QSCI initial state kind: {kind}")

    if not coefficients:
        raise ValueError(f"Initial state '{kind}' produced no determinants.")
    norm = float(np.sqrt(sum(abs(value) ** 2 for value in coefficients.values())))
    if norm <= 0.0:
        raise ValueError(f"Initial state '{kind}' has zero norm.")
    vector = np.zeros(2**int(num_qubits), dtype=complex)
    normalized_coeffs: dict[int, complex] = {}
    for determinant, coeff in sorted(coefficients.items()):
        normalized_coeff = complex(coeff) / norm
        vector[int(determinant)] = normalized_coeff
        normalized_coeffs[int(determinant)] = normalized_coeff
    return InitialState(
        kind=normalized,
        vector=vector,
        determinants=sorted(normalized_coeffs),
        coefficients=normalized_coeffs,
    )


def build_selected_subspace_matrix(operator, determinants: list[int]) -> np.ndarray:
    """Project a qubit operator matrix into a selected determinant subspace."""
    if not determinants:
        raise ValueError("Selected determinant subspace cannot be empty.")
    sparse_matrix = operator.to_matrix(sparse=True).tocsr()
    selected = sparse_matrix[np.ix_([int(item) for item in determinants], [int(item) for item in determinants])]
    return np.asarray(selected.todense(), dtype=complex)
