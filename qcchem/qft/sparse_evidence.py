"""Sparse exact evidence helpers for finite-cutoff lattice-QED artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

from qcchem.core import LatticeQEDSpec, MoleculeSpec
from qcchem.qft.lattice_qed import _site_nuclear_potential
from qcchem.qft.observables import build_qft_observable_matrices
from qcchem.qft.projected_builder import _hopping_sector
from qcchem.qft.sector_basis import ProjectedBasis

OBSERVABLE_KEYS = (
    "site_density",
    "link_electric_flux",
    "electric_energy_by_link",
    "onsite_energy_by_site",
    "hopping_energy_by_link",
    "gauss_law_residual_by_site",
    "dominant_physical_sector_configurations",
)


def unavailable_lattice_qed_observables(reason: str) -> dict[str, Any]:
    """Return an explicit unavailable payload for every report-facing observable."""
    return {key: {"available": False, "reason": reason} for key in OBSERVABLE_KEYS}


def _matrix_sha256(matrix: sp.spmatrix) -> str:
    csr = matrix.tocsr()
    header = {
        "shape": [int(csr.shape[0]), int(csr.shape[1])],
        "nnz": int(csr.nnz),
        "format": "csr",
        "data_dtype": "complex128",
        "index_dtype": "int64",
    }
    digest = hashlib.sha256(json.dumps(header, sort_keys=True).encode("utf-8"))
    digest.update(np.asarray(csr.data, dtype=np.complex128).tobytes())
    digest.update(np.asarray(csr.indices, dtype=np.int64).tobytes())
    digest.update(np.asarray(csr.indptr, dtype=np.int64).tobytes())
    return digest.hexdigest()


def _lowest_eigensystem(matrix: sp.spmatrix, max_eigenvalues: int) -> tuple[np.ndarray, np.ndarray]:
    dimension = int(matrix.shape[0])
    if dimension <= 0:
        raise ValueError("empty_sparse_exact_matrix")
    if dimension <= 256:
        values, vectors = np.linalg.eigh(matrix.toarray())
        order = np.argsort(np.real(values))
        return np.real(values[order]), vectors[:, order]
    k = max(1, min(int(max_eigenvalues), dimension - 1))
    values, vectors = eigsh(matrix, k=k, which="SA")
    order = np.argsort(np.real(values))
    return np.real(values[order]), vectors[:, order]


def _expectation(matrix: sp.spmatrix, state: np.ndarray) -> float:
    return float(np.real(np.vdot(state, matrix @ state)))


def build_sparse_exact_validation(
    context: Any,
    *,
    solver_energy: float | None,
    max_eigenvalues: int = 8,
) -> tuple[dict[str, Any], np.ndarray | None]:
    """Build numerical residual and matrix metadata for the sparse exact path."""
    bundle = getattr(context, "sparse_bundle", None)
    if bundle is None:
        return {"available": False, "reason": "sparse_bundle_not_available"}, None
    projected = bundle.projected_hamiltonian is not None
    matrix = bundle.projected_hamiltonian if projected else bundle.full_hamiltonian
    if matrix is None:
        return {"available": False, "reason": "sparse_hamiltonian_not_available"}, None
    matrix = matrix.tocsr()
    values, vectors = _lowest_eigensystem(matrix, max_eigenvalues)
    ground_energy = float(values[0])
    ground_state = np.asarray(vectors[:, 0], dtype=complex)
    residual_vector = matrix @ ground_state - ground_energy * ground_state
    residual_norm = float(np.linalg.norm(residual_vector))
    hpsi_norm = float(np.linalg.norm(matrix @ ground_state))
    relative_residual = float(residual_norm / max(hpsi_norm, abs(ground_energy), 1.0e-12))
    gap = float(values[1] - values[0]) if len(values) > 1 else None
    engine = dict(getattr(context.summary, "engine", {}) or {})
    physical_sector = dict(getattr(context.summary, "physical_sector", {}) or {})
    validation = {
        "available": True,
        "scope": "finite_cutoff_lattice_qed_sparse_exact",
        "operator_space": "physical_sector" if projected else "full_hilbert_space",
        "projected": bool(projected),
        "projected_matrix_dimension": (
            int(matrix.shape[0]) if projected else engine.get("projected_dimension")
        ),
        "projected_hamiltonian_nnz": (
            int(matrix.nnz) if projected else engine.get("projected_hamiltonian_nnz")
        ),
        "physical_sector_dimension": physical_sector.get("physical_sector_dimension")
        or physical_sector.get("basis_index_count"),
        "basis_hash": physical_sector.get("basis_hash"),
        "eigen_residual_norm": residual_norm,
        "relative_eigen_residual": relative_residual,
        "ground_state_gap": gap,
        "lowest_eigenvalues": [float(value) for value in values[: int(max_eigenvalues)]],
        "projected_matrix_sha256": _matrix_sha256(matrix) if projected else None,
        "solver_ground_energy": solver_energy,
        "diagonalized_ground_energy": ground_energy,
        "solver_vs_diagonalized_abs_error": (
            None if solver_energy is None else float(abs(float(solver_energy) - ground_energy))
        ),
    }
    return validation, ground_state


def _dominant_physical_configurations(
    basis: ProjectedBasis | None,
    state: np.ndarray | None,
    *,
    limit: int,
) -> dict[str, Any]:
    if basis is None:
        return {"available": False, "reason": "projected_basis_not_available"}
    if state is None:
        return {"available": False, "reason": "ground_state_vector_not_available"}
    probabilities = np.abs(state) ** 2
    order = np.argsort(probabilities)[::-1][:limit]
    configurations: list[dict[str, Any]] = []
    for rank, basis_position in enumerate(order, start=1):
        amplitude = complex(state[int(basis_position)])
        configurations.append(
            {
                "rank": rank,
                "basis_position": int(basis_position),
                "basis_index": int(basis.physical_indices[basis_position]),
                "probability": float(probabilities[basis_position]),
                "amplitude_real": float(np.real(amplitude)),
                "amplitude_imag": float(np.imag(amplitude)),
                "matter_index": int(basis.matter_indices[basis_position]),
                "gauge_index": int(basis.gauge_indices[basis_position]),
                "occupations": [int(value) for value in basis.occupations[basis_position].tolist()],
                "gauge_digits": [int(value) for value in basis.gauge_digits[basis_position].tolist()],
                "electric_levels": [float(value) for value in basis.electric_levels[basis_position].tolist()],
                "gauss_values": [float(value) for value in basis.gauss_values[basis_position].tolist()],
                "particle_number": int(basis.particle_numbers[basis_position]),
            }
        )
    return {
        "available": True,
        "basis": "projected_physical_sector",
        "basis_hash": hashlib.sha256(np.asarray(basis.physical_indices, dtype=np.int64).tobytes()).hexdigest(),
        "configurations": configurations,
    }


def _onsite_energy_by_site(
    context: Any,
    molecule: MoleculeSpec | None,
    qft_spec: LatticeQEDSpec | None,
    site_density: list[sp.csr_matrix],
    state: np.ndarray,
) -> dict[str, Any]:
    if molecule is None or qft_spec is None:
        return {"available": False, "reason": "molecule_or_qft_spec_not_available"}
    values: list[float] = []
    potentials: list[float] = []
    for site, density_matrix in zip(context.grid.sites, site_density, strict=True):
        potential = _site_nuclear_potential(
            molecule,
            np.asarray(site.real_space_coordinate, dtype=float),
            float(qft_spec.grid.softening),
        )
        potentials.append(float(potential))
        values.append(_expectation(potential * density_matrix, state))
    return {
        "available": True,
        "scope": "nuclear_scalar_onsite_sector",
        "values": values,
        "site_potentials": potentials,
        "includes_external_point_charge_sector": False,
    }


def _hopping_energy_by_link(
    context: Any,
    qft_spec: LatticeQEDSpec | None,
    basis: ProjectedBasis | None,
    state: np.ndarray,
) -> dict[str, Any]:
    if qft_spec is None:
        return {"available": False, "reason": "qft_spec_not_available"}
    if basis is None:
        return {"available": False, "reason": "projected_basis_not_available"}
    matter_modes = int(context.summary.matter_mode_count)
    gauge_dimension = int(context.link_operator.encoded_dimension ** context.summary.link_count)
    values = []
    for link in context.grid.links:
        matrix = _hopping_sector(
            basis,
            context.grid,
            qft_spec,
            context.link_operator,
            matter_modes=matter_modes,
            gauge_dimension=gauge_dimension,
            link_filter=link.linear_index,
        )
        values.append(_expectation(0.5 * (matrix + matrix.conj().T), state))
    return {"available": True, "scope": "projected_hopping_sector_by_link", "values": values}


def build_lattice_qed_sparse_observables(
    context: Any,
    *,
    molecule: MoleculeSpec | None,
    qft_spec: LatticeQEDSpec | None,
    ground_state: np.ndarray | None,
    max_dominant_configurations: int = 8,
) -> dict[str, Any]:
    """Build report-facing lattice-QED observables with explicit unavailable reasons."""
    if ground_state is None:
        return unavailable_lattice_qed_observables("ground_state_vector_not_available")
    try:
        matrices = build_qft_observable_matrices(context)
    except Exception as exc:  # pragma: no cover - defensive artifact path
        return unavailable_lattice_qed_observables(f"observable_matrix_build_failed: {type(exc).__name__}: {exc}")
    bundle = getattr(context, "sparse_bundle", None)
    basis = None
    if bundle is not None:
        candidate = (getattr(bundle, "metadata", {}) or {}).get("projected_basis")
        if isinstance(candidate, ProjectedBasis):
            basis = candidate
    observables: dict[str, Any] = {
        "site_density": {
            "available": True,
            "values": [_expectation(matrix, ground_state) for matrix in matrices.site_density],
            "units": "electron_count",
        },
        "link_electric_flux": {
            "available": True,
            "values": [_expectation(matrix, ground_state) for matrix in matrices.link_electric_flux],
            "units": "electric_flux_quantum",
        },
        "electric_energy_by_link": {
            "available": True,
            "values": [_expectation(matrix, ground_state) for matrix in matrices.link_electric_energy],
            "units": "Hartree",
        },
        "onsite_energy_by_site": _onsite_energy_by_site(
            context,
            molecule,
            qft_spec,
            matrices.site_density,
            ground_state,
        ),
        "hopping_energy_by_link": _hopping_energy_by_link(context, qft_spec, basis, ground_state),
        "gauss_law_residual_by_site": {
            "available": True,
            "values": [_expectation(matrix, ground_state) for matrix in matrices.gauss_residual],
            "units": "charge",
        },
        "dominant_physical_sector_configurations": _dominant_physical_configurations(
            basis,
            ground_state,
            limit=int(max_dominant_configurations),
        ),
    }
    return observables


def summarize_lattice_qed_sparse_exact_evidence(
    context: Any,
    *,
    molecule: MoleculeSpec | None,
    qft_spec: LatticeQEDSpec | None,
    solver_energy: float | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return sparse exact validation and lattice-QED observable payloads."""
    validation, ground_state = build_sparse_exact_validation(
        context,
        solver_energy=solver_energy,
    )
    if not validation.get("available"):
        return validation, unavailable_lattice_qed_observables(str(validation.get("reason") or "validation_unavailable"))
    observables = build_lattice_qed_sparse_observables(
        context,
        molecule=molecule,
        qft_spec=qft_spec,
        ground_state=ground_state,
    )
    return validation, observables
