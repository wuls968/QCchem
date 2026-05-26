"""Observable summaries and matrices for exploratory lattice-QED artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import scipy.sparse as sp

from qcchem.qft.lattice_qed import LatticeQEDContext
from qcchem.qft.lattice_qed import (
    _embed_gauge,
    _embed_gauge_product_sparse,
    _embed_gauge_sparse,
    _embed_gauge_product,
    _embed_matter,
    _embed_matter_sparse,
    _fermion_number,
    _fermion_number_sparse,
    _mode_index,
)
from qcchem.qft.projected_builder import build_projected_observable_components


@dataclass(slots=True)
class QFTObservableMatrices:
    """Dense finite-cutoff observable matrices used by QFT dynamics."""

    site_density: list[np.ndarray] = field(default_factory=list)
    link_electric_flux: list[np.ndarray] = field(default_factory=list)
    link_electric_energy: list[np.ndarray] = field(default_factory=list)
    gauss_residual: list[np.ndarray] = field(default_factory=list)
    plaquette_wilson: list[np.ndarray] = field(default_factory=list)
    aggregate: dict[str, np.ndarray] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def _zero_sparse(context: LatticeQEDContext) -> sp.csr_matrix:
    if context.sparse_bundle is not None:
        dimension = int(context.sparse_bundle.full_hamiltonian.shape[0])
    else:
        dimension = int(context.hamiltonian_matrix.shape[0])
    return sp.csr_matrix((dimension, dimension), dtype=complex)


def _zero_dimension(dimension: int) -> sp.csr_matrix:
    return sp.csr_matrix((dimension, dimension), dtype=complex)


def _as_sparse(matrix: np.ndarray | sp.spmatrix) -> sp.csr_matrix:
    return matrix.tocsr() if sp.issparse(matrix) else sp.csr_matrix(matrix)


def _spin_components(context: LatticeQEDContext) -> int:
    if context.summary.site_count <= 0:
        return 0
    return int(context.summary.matter_mode_count // context.summary.site_count)


def _gauge_dimension(context: LatticeQEDContext) -> int:
    return int(context.link_operator.encoded_dimension ** context.summary.link_count)


def _target_charge(site_metadata: dict[str, Any]) -> float:
    return float(site_metadata.get("target_charge", 0.0))


def _project_matrices_if_needed(
    context: LatticeQEDContext,
    matrices: list[sp.csr_matrix],
) -> list[sp.csr_matrix]:
    bundle = context.sparse_bundle
    if bundle is None or bundle.projected_hamiltonian is None:
        return matrices
    indices = bundle.physical_indices
    return [matrix[indices, :][:, indices].tocsr() for matrix in matrices]


def build_qft_observable_matrices(context: LatticeQEDContext) -> QFTObservableMatrices:
    """Build the observable matrices used by QFT dynamics and reports."""
    projected_components = build_projected_observable_components(context)
    if projected_components is not None:
        site_density = projected_components["site_density"]
        link_electric_flux = projected_components["link_electric_flux"]
        link_electric_energy = projected_components["link_electric_energy"]
        gauss_residual = projected_components["gauss_residual"]
        plaquette_wilson = projected_components["plaquette_wilson"]
        zero = projected_components["zero"]
        particle_number = sum(site_density, zero)
        total_electric_energy = sum(link_electric_energy, zero)
        total_gauss_violation = sum((matrix @ matrix for matrix in gauss_residual), zero)
        total_wilson = sum(plaquette_wilson, zero)
        return QFTObservableMatrices(
            site_density=site_density,
            link_electric_flux=link_electric_flux,
            link_electric_energy=link_electric_energy,
            gauss_residual=gauss_residual,
            plaquette_wilson=plaquette_wilson,
            aggregate={
                "particle_number": particle_number,
                "total_electric_energy": total_electric_energy,
                "total_gauss_violation": total_gauss_violation,
                "total_wilson": total_wilson,
            },
            metadata={
                "site_density_count": len(site_density),
                "link_electric_flux_count": len(link_electric_flux),
                "link_electric_energy_count": len(link_electric_energy),
                "gauss_residual_count": len(gauss_residual),
                "plaquette_wilson_count": len(plaquette_wilson),
                "aggregate_observables": [
                    "particle_number",
                    "total_electric_energy",
                    "total_gauss_violation",
                    "total_wilson",
                ],
                "build_mode": "sector_first_projected",
            },
        )
    spin_components = _spin_components(context)
    matter_modes = int(context.summary.matter_mode_count)
    matter_dimension = 2**matter_modes
    gauge_dimension = _gauge_dimension(context)
    link_count = int(context.summary.link_count)
    encoded_dimension = int(context.link_operator.encoded_dimension)

    use_sparse = context.sparse_bundle is not None
    number_ops = [
        _fermion_number_sparse(mode, matter_modes) if use_sparse else _fermion_number(mode, matter_modes)
        for mode in range(matter_modes)
    ]
    site_density: list[sp.csr_matrix] = []
    for site in context.grid.sites:
        local_density = (
            sp.csr_matrix((matter_dimension, matter_dimension), dtype=complex)
            if use_sparse
            else np.zeros((matter_dimension, matter_dimension), dtype=complex)
        )
        for spin in range(spin_components):
            local_density += number_ops[_mode_index(site.linear_index, spin, spin_components)]
        if use_sparse:
            site_density.append(_embed_matter_sparse(local_density, gauge_dimension=gauge_dimension))
        else:
            site_density.append(_as_sparse(_embed_matter(local_density, gauge_dimension=gauge_dimension)))

    link_electric_flux: list[sp.csr_matrix] = []
    link_electric_energy: list[sp.csr_matrix] = []
    for link in context.grid.links:
        if use_sparse:
            link_electric_flux.append(
                _embed_gauge_sparse(
                    context.link_operator.electric_matrix,
                    link_index=link.linear_index,
                    matter_dimension=matter_dimension,
                    link_count=link_count,
                    encoded_dimension=encoded_dimension,
                )
            )
            link_electric_energy.append(
                0.5
                * (float(context.summary.gauge_coupling) ** 2)
                * _embed_gauge_sparse(
                    context.link_operator.electric_squared_matrix,
                    link_index=link.linear_index,
                    matter_dimension=matter_dimension,
                    link_count=link_count,
                    encoded_dimension=encoded_dimension,
                )
            )
        else:
            link_electric_flux.append(
                _as_sparse(
                    _embed_gauge(
                        context.link_operator.electric_matrix,
                        link_index=link.linear_index,
                        matter_dimension=matter_dimension,
                        link_count=link_count,
                        encoded_dimension=encoded_dimension,
                    )
                )
            )
            link_electric_energy.append(
                _as_sparse(
                    0.5
                    * (float(context.summary.gauge_coupling) ** 2)
                    * _embed_gauge(
                        context.link_operator.electric_squared_matrix,
                        link_index=link.linear_index,
                        matter_dimension=matter_dimension,
                        link_count=link_count,
                        encoded_dimension=encoded_dimension,
                    )
                )
            )

    gauss_residual: list[sp.csr_matrix] = []
    gauss_source = (
        context.sparse_bundle.gauss_law_matrices
        if context.sparse_bundle is not None
        else [_as_sparse(matrix) for matrix in context.gauss_law_matrices]
    )
    for metadata, matrix in zip(context.summary.gauss_law_generators, gauss_source):
        shifted = _as_sparse(matrix) - _target_charge(metadata) * sp.identity(
            matrix.shape[0],
            format="csr",
            dtype=complex,
        )
        gauss_residual.append(shifted)

    plaquette_wilson: list[sp.csr_matrix] = []
    for plaquette in context.grid.plaquettes:
        matrices: dict[int, np.ndarray] = {}
        for link_index, orientation in zip(plaquette.link_indices, plaquette.orientations):
            matrices[link_index] = (
                context.link_operator.raising_matrix
                if orientation > 0
                else context.link_operator.lowering_matrix
            )
        if use_sparse:
            loop = _embed_gauge_product_sparse(
                matrices,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=encoded_dimension,
            )
            plaquette_wilson.append((0.5 * (loop + loop.conj().T)).tocsr())
        else:
            loop = _embed_gauge_product(
                matrices,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=encoded_dimension,
            )
            plaquette_wilson.append(_as_sparse(0.5 * (loop + loop.conj().T)))

    site_density = _project_matrices_if_needed(context, site_density)
    link_electric_flux = _project_matrices_if_needed(context, link_electric_flux)
    link_electric_energy = _project_matrices_if_needed(context, link_electric_energy)
    gauss_residual = _project_matrices_if_needed(context, gauss_residual)
    plaquette_wilson = _project_matrices_if_needed(context, plaquette_wilson)

    output_dimension = (
        int(context.sparse_bundle.projected_hamiltonian.shape[0])
        if context.sparse_bundle is not None and context.sparse_bundle.projected_hamiltonian is not None
        else int(site_density[0].shape[0] if site_density else _zero_sparse(context).shape[0])
    )
    zero = _zero_dimension(output_dimension)
    particle_number = sum(site_density, zero)
    total_electric_energy = sum(link_electric_energy, zero)
    total_gauss_violation = sum((matrix @ matrix for matrix in gauss_residual), zero)
    total_wilson = sum(plaquette_wilson, zero)

    return QFTObservableMatrices(
        site_density=site_density,
        link_electric_flux=link_electric_flux,
        link_electric_energy=link_electric_energy,
        gauss_residual=gauss_residual,
        plaquette_wilson=plaquette_wilson,
        aggregate={
            "particle_number": particle_number,
            "total_electric_energy": total_electric_energy,
            "total_gauss_violation": total_gauss_violation,
            "total_wilson": total_wilson,
        },
        metadata={
            "site_density_count": len(site_density),
            "link_electric_flux_count": len(link_electric_flux),
            "link_electric_energy_count": len(link_electric_energy),
            "gauss_residual_count": len(gauss_residual),
            "plaquette_wilson_count": len(plaquette_wilson),
            "aggregate_observables": [
                "particle_number",
                "total_electric_energy",
                "total_gauss_violation",
                "total_wilson",
            ],
        },
    )


def expectation_value(matrix: np.ndarray, statevector: np.ndarray) -> float:
    """Return a real expectation value for an observable matrix."""
    return float(np.real_if_close(np.vdot(statevector, matrix @ statevector)))


def summarize_qft_observables(context: LatticeQEDContext) -> dict[str, Any]:
    """Return lightweight observable metadata for report-facing provenance."""
    observables = build_qft_observable_matrices(context)
    return {
        "target_electrons": context.target_electrons,
        "nuclear_charge_by_site": list(context.summary.nuclear_charge_by_site),
        "constraint_residuals": dict(context.summary.constraint_residuals),
        "term_counts_by_sector": dict(context.summary.term_counts_by_sector),
        "observable_metadata": dict(observables.metadata),
    }
