"""Physical-sector-first sparse projected lattice-QED builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import scipy.sparse as sp

from qcchem.chem.external_charges import ResolvedExternalPointCharges, convert_point_charges_unit
from qcchem.core import LatticeQEDSpec, MoleculeSpec
from qcchem.qft.grid import ATOMIC_NUMBERS, LatticeGrid
from qcchem.qft.links import U1LinkOperators
from qcchem.qft.sector_basis import ProjectedBasis, enumerate_projected_basis, gauge_index_from_digits


SECTOR_NAMES = (
    "onsite",
    "external_point_charge",
    "hopping",
    "density_coulomb",
    "electric",
    "magnetic_plaquette",
    "gauss_law_penalty",
    "particle_number_penalty",
    "padding_penalty",
)


@dataclass(slots=True)
class ProjectedBuildResult:
    """Projected finite-cutoff operators and provenance."""

    sectors: dict[str, sp.csr_matrix]
    hamiltonian: sp.csr_matrix
    gauss_law_matrices: list[sp.csr_matrix]
    basis: ProjectedBasis
    matter_modes: int
    matter_dimension: int
    gauge_dimension: int
    metadata: dict[str, Any]


def _mode_index(site_index: int, spin_index: int, spin_components: int) -> int:
    return site_index * spin_components + spin_index


def _site_nuclear_potential(molecule: MoleculeSpec, position: np.ndarray, softening: float) -> float:
    potential = 0.0
    for atom in molecule.geometry:
        charge = float(ATOMIC_NUMBERS[atom.symbol])
        atom_position = np.asarray(atom.coords, dtype=float)
        distance = float(np.linalg.norm(position - atom_position))
        potential -= charge / np.sqrt(distance**2 + softening**2)
    return float(potential)


def _site_external_point_charge_potential(
    external_point_charges: ResolvedExternalPointCharges | None,
    position: np.ndarray,
    *,
    position_unit: str,
    softening: float,
) -> float:
    if external_point_charges is None or not external_point_charges.enabled:
        return 0.0
    potential = 0.0
    charges = convert_point_charges_unit(
        external_point_charges.charges,
        source_unit=external_point_charges.unit,
        target_unit=position_unit,
    )
    for charge in charges:
        charge_position = np.asarray(charge.coords, dtype=float)
        distance = float(np.linalg.norm(position - charge_position))
        potential -= float(charge.charge) / np.sqrt(distance**2 + softening**2)
    return float(potential)


def _diagonal(values: np.ndarray) -> sp.csr_matrix:
    return sp.diags(np.asarray(values, dtype=complex), offsets=0, format="csr")


def _empty_sector(dimension: int) -> sp.csr_matrix:
    return sp.csr_matrix((dimension, dimension), dtype=complex)


def _creation_action(matter_index: int, mode: int, matter_modes: int) -> tuple[int, int] | None:
    shift = matter_modes - mode - 1
    if (matter_index >> shift) & 1:
        return None
    parity = 0
    for prior in range(mode):
        parity += (matter_index >> (matter_modes - prior - 1)) & 1
    sign = -1 if parity % 2 else 1
    return int(matter_index | (1 << shift)), sign


def _annihilation_action(matter_index: int, mode: int, matter_modes: int) -> tuple[int, int] | None:
    shift = matter_modes - mode - 1
    if not ((matter_index >> shift) & 1):
        return None
    parity = 0
    for prior in range(mode):
        parity += (matter_index >> (matter_modes - prior - 1)) & 1
    sign = -1 if parity % 2 else 1
    return int(matter_index & ~(1 << shift)), sign


def _cdag_c_action(
    matter_index: int,
    *,
    create_mode: int,
    annihilate_mode: int,
    matter_modes: int,
) -> tuple[int, int] | None:
    annihilated = _annihilation_action(matter_index, annihilate_mode, matter_modes)
    if annihilated is None:
        return None
    intermediate, sign_a = annihilated
    created = _creation_action(intermediate, create_mode, matter_modes)
    if created is None:
        return None
    final, sign_c = created
    return final, int(sign_a * sign_c)


def _apply_link_shift(
    digits: np.ndarray,
    *,
    link_index: int,
    delta: int,
    physical_dimension: int,
) -> tuple[int, ...] | None:
    updated = [int(value) for value in digits.tolist()]
    next_digit = updated[link_index] + int(delta)
    if next_digit < 0 or next_digit >= int(physical_dimension):
        return None
    updated[link_index] = next_digit
    return tuple(updated)


def _projected_index(
    basis: ProjectedBasis,
    *,
    matter_index: int,
    gauge_digits: tuple[int, ...],
    gauge_dimension: int,
    encoded_dimension: int,
) -> int | None:
    gauge_index = gauge_index_from_digits(gauge_digits, encoded_dimension=encoded_dimension)
    full_index = int(matter_index * gauge_dimension + gauge_index)
    return basis.index_by_full.get(full_index)


def _hopping_sector(
    basis: ProjectedBasis,
    grid: LatticeGrid,
    spec: LatticeQEDSpec,
    link_ops: U1LinkOperators,
    *,
    matter_modes: int,
    gauge_dimension: int,
    link_filter: int | None = None,
    strength_scale: float = 1.0,
) -> sp.csr_matrix:
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    spin_components = int(spec.matter.spin_components)
    link_count = len(grid.links)
    for col, matter_index in enumerate(basis.matter_indices.tolist()):
        digits = basis.gauge_digits[col]
        for link in grid.links:
            if link_filter is not None and link.linear_index != int(link_filter):
                continue
            spacing = float(spec.grid.spacing[link.direction])
            hopping_strength = float(strength_scale) / (2.0 * spacing**2)
            for spin in range(spin_components):
                start_mode = _mode_index(link.start_site, spin, spin_components)
                end_mode = _mode_index(link.end_site, spin, spin_components)
                forward = _cdag_c_action(
                    int(matter_index),
                    create_mode=end_mode,
                    annihilate_mode=start_mode,
                    matter_modes=matter_modes,
                )
                shifted = _apply_link_shift(
                    digits,
                    link_index=link.linear_index,
                    delta=1,
                    physical_dimension=link_ops.physical_dimension,
                )
                if forward is not None and shifted is not None:
                    row = _projected_index(
                        basis,
                        matter_index=forward[0],
                        gauge_digits=shifted,
                        gauge_dimension=gauge_dimension,
                        encoded_dimension=link_ops.encoded_dimension,
                    )
                    if row is not None:
                        rows.append(row)
                        cols.append(col)
                        data.append(complex(-hopping_strength * forward[1]))
                backward = _cdag_c_action(
                    int(matter_index),
                    create_mode=start_mode,
                    annihilate_mode=end_mode,
                    matter_modes=matter_modes,
                )
                shifted = _apply_link_shift(
                    digits,
                    link_index=link.linear_index,
                    delta=-1,
                    physical_dimension=link_ops.physical_dimension,
                )
                if backward is not None and shifted is not None:
                    row = _projected_index(
                        basis,
                        matter_index=backward[0],
                        gauge_digits=shifted,
                        gauge_dimension=gauge_dimension,
                        encoded_dimension=link_ops.encoded_dimension,
                    )
                    if row is not None:
                        rows.append(row)
                        cols.append(col)
                        data.append(complex(-hopping_strength * backward[1]))
    return sp.coo_matrix((data, (rows, cols)), shape=(basis.dimension, basis.dimension)).tocsr()


def _plaquette_sector(
    basis: ProjectedBasis,
    grid: LatticeGrid,
    spec: LatticeQEDSpec,
    link_ops: U1LinkOperators,
    *,
    gauge_dimension: int,
) -> sp.csr_matrix:
    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    if not spec.gauge.include_magnetic_plaquettes or not grid.plaquettes:
        return _empty_sector(basis.dimension)
    coefficient = -0.5 / max(float(spec.gauge.coupling) ** 2, 1.0e-12)
    for col, matter_index in enumerate(basis.matter_indices.tolist()):
        for plaquette in grid.plaquettes:
            digits = [int(value) for value in basis.gauge_digits[col].tolist()]
            valid = True
            for link_index, orientation in zip(plaquette.link_indices, plaquette.orientations):
                next_digit = digits[link_index] + (1 if orientation > 0 else -1)
                if next_digit < 0 or next_digit >= link_ops.physical_dimension:
                    valid = False
                    break
                digits[link_index] = next_digit
            if not valid:
                continue
            row = _projected_index(
                basis,
                matter_index=int(matter_index),
                gauge_digits=tuple(digits),
                gauge_dimension=gauge_dimension,
                encoded_dimension=link_ops.encoded_dimension,
            )
            if row is None:
                continue
            rows.extend([row, col])
            cols.extend([col, row])
            data.extend([complex(coefficient), complex(coefficient)])
    return sp.coo_matrix((data, (rows, cols)), shape=(basis.dimension, basis.dimension)).tocsr()


def build_sector_first_projected(
    molecule: MoleculeSpec,
    spec: LatticeQEDSpec,
    grid: LatticeGrid,
    link_ops: U1LinkOperators,
    target_electrons: int,
    external_point_charges: ResolvedExternalPointCharges | None,
    *,
    total_qubits: int,
) -> ProjectedBuildResult:
    """Build projected sparse operators without materializing the full Hilbert-space matrix."""
    spin_components = int(spec.matter.spin_components)
    matter_modes = grid.site_count * spin_components
    matter_dimension = 2**matter_modes
    gauge_dimension = link_ops.encoded_dimension ** len(grid.links)
    basis = enumerate_projected_basis(
        grid,
        spec,
        link_ops,
        matter_modes=matter_modes,
        matter_dimension=matter_dimension,
        gauge_dimension=gauge_dimension,
        total_qubits=total_qubits,
    )
    if basis.dimension <= 0:
        raise ValueError("physical_sector_empty_or_not_enumerated")
    if basis.dimension > int(spec.engine.max_projected_dimension):
        raise ValueError("physical_sector_exceeds_max_projected_dimension")

    dimension = basis.dimension
    sectors = {name: _empty_sector(dimension) for name in SECTOR_NAMES}
    onsite = np.zeros(dimension, dtype=float)
    external = np.zeros(dimension, dtype=float)
    density_coulomb = np.zeros(dimension, dtype=float)
    electric = np.zeros(dimension, dtype=float)
    gauss_penalty = np.zeros(dimension, dtype=float)
    number_penalty = np.zeros(dimension, dtype=float)

    for site in grid.sites:
        potential = _site_nuclear_potential(
            molecule,
            np.asarray(site.real_space_coordinate, dtype=float),
            float(spec.grid.softening),
        )
        local_density = np.sum(
            basis.occupations[
                :,
                site.linear_index * spin_components : (site.linear_index + 1) * spin_components,
            ],
            axis=1,
        )
        onsite += potential * local_density
        external_potential = _site_external_point_charge_potential(
            external_point_charges,
            np.asarray(site.real_space_coordinate, dtype=float),
            position_unit=molecule.unit,
            softening=float(spec.grid.softening),
        )
        external += external_potential * local_density

    if spec.matter.include_soft_coulomb_density:
        site_densities = []
        for site in grid.sites:
            site_densities.append(
                np.sum(
                    basis.occupations[
                        :,
                        site.linear_index * spin_components : (site.linear_index + 1) * spin_components,
                    ],
                    axis=1,
                )
            )
        for left in grid.sites:
            left_position = np.asarray(left.real_space_coordinate, dtype=float)
            for right in grid.sites:
                if right.linear_index <= left.linear_index:
                    continue
                right_position = np.asarray(right.real_space_coordinate, dtype=float)
                distance = float(np.linalg.norm(left_position - right_position))
                strength = 1.0 / np.sqrt(distance**2 + float(spec.grid.softening) ** 2)
                density_coulomb += (
                    strength * site_densities[left.linear_index] * site_densities[right.linear_index]
                )

    for link in grid.links:
        electric += (
            0.5
            * (float(spec.gauge.coupling) ** 2)
            * (basis.electric_levels[:, link.linear_index] ** 2)
        )
    if spec.constraints.gauss_law_penalty > 0.0:
        gauss_penalty += float(spec.constraints.gauss_law_penalty) * np.sum(
            basis.gauss_values**2,
            axis=1,
        )
    if spec.constraints.particle_number_penalty > 0.0:
        number_penalty += float(spec.constraints.particle_number_penalty) * (
            basis.particle_numbers.astype(float) - float(target_electrons)
        ) ** 2

    sectors["onsite"] = _diagonal(onsite)
    sectors["external_point_charge"] = _diagonal(external)
    sectors["density_coulomb"] = _diagonal(density_coulomb)
    sectors["electric"] = _diagonal(electric)
    sectors["gauss_law_penalty"] = _diagonal(gauss_penalty)
    sectors["particle_number_penalty"] = _diagonal(number_penalty)
    sectors["hopping"] = _hopping_sector(
        basis,
        grid,
        spec,
        link_ops,
        matter_modes=matter_modes,
        gauge_dimension=gauge_dimension,
    )
    sectors["magnetic_plaquette"] = _plaquette_sector(
        basis,
        grid,
        spec,
        link_ops,
        gauge_dimension=gauge_dimension,
    )

    hamiltonian = sum(sectors.values(), _empty_sector(dimension)).tocsr()
    hamiltonian = (0.5 * (hamiltonian + hamiltonian.conj().T)).tocsr()
    gauss_law_matrices = [
        _diagonal(basis.gauss_values[:, site_index])
        for site_index in range(grid.site_count)
    ]
    full_dimension = int(matter_dimension * gauge_dimension)
    metadata = {
        "build_mode": "sector_first_projected",
        "operator_representation": "sparse_projected",
        "full_dimension": full_dimension,
        "projected": True,
        "projected_dimension": int(dimension),
        "full_to_projected_reduction": (float(full_dimension) / float(dimension) if dimension else None),
        "peak_matrix_dimension": int(dimension),
        "full_hamiltonian_nnz": None,
        "projected_hamiltonian_nnz": int(hamiltonian.nnz),
        "sector_nnz": {name: int(matrix.nnz) for name, matrix in sectors.items()},
        "projection_skipped_reason": None,
        "projected_builder_fallback_reason": None,
        "projected_basis": basis,
    }
    return ProjectedBuildResult(
        sectors=sectors,
        hamiltonian=hamiltonian,
        gauss_law_matrices=gauss_law_matrices,
        basis=basis,
        matter_modes=matter_modes,
        matter_dimension=matter_dimension,
        gauge_dimension=gauge_dimension,
        metadata=metadata,
    )


def build_projected_local_hopping_pulse(context: Any, spec: LatticeQEDSpec) -> sp.csr_matrix | None:
    """Build the projected local hopping pulse for sector-first contexts."""
    bundle = getattr(context, "sparse_bundle", None)
    metadata = getattr(bundle, "metadata", {}) if bundle is not None else {}
    basis = metadata.get("projected_basis")
    if not isinstance(basis, ProjectedBasis):
        return None
    link_index = int(spec.dynamics.initial_state.link_index)
    if link_index < 0 or link_index >= len(context.grid.links):
        raise ValueError("problem.qft.dynamics.initial_state.link_index is outside the grid link range.")
    matter_modes = int(context.summary.matter_mode_count)
    gauge_dimension = int(context.link_operator.encoded_dimension ** context.summary.link_count)
    pulse = _hopping_sector(
        basis,
        context.grid,
        spec,
        context.link_operator,
        matter_modes=matter_modes,
        gauge_dimension=gauge_dimension,
        link_filter=link_index,
        strength_scale=float(spec.dynamics.initial_state.pulse_strength),
    )
    return (0.5 * (pulse + pulse.conj().T)).tocsr()


def build_projected_observable_components(context: Any) -> dict[str, Any] | None:
    """Build observable matrices directly in the projected sector-first basis."""
    bundle = getattr(context, "sparse_bundle", None)
    metadata = getattr(bundle, "metadata", {}) if bundle is not None else {}
    basis = metadata.get("projected_basis")
    if not isinstance(basis, ProjectedBasis):
        return None
    dimension = basis.dimension
    spin_components = int(context.summary.matter_mode_count // context.summary.site_count)
    site_density = []
    for site in context.grid.sites:
        values = np.sum(
            basis.occupations[
                :,
                site.linear_index * spin_components : (site.linear_index + 1) * spin_components,
            ],
            axis=1,
        )
        site_density.append(_diagonal(values))
    link_electric_flux = [
        _diagonal(basis.electric_levels[:, link.linear_index])
        for link in context.grid.links
    ]
    link_electric_energy = [
        _diagonal(
            0.5
            * (float(context.summary.gauge_coupling) ** 2)
            * (basis.electric_levels[:, link.linear_index] ** 2)
        )
        for link in context.grid.links
    ]
    gauss_residual = [
        _diagonal(basis.gauss_values[:, site_index] - float(basis.target_charge_values[site_index]))
        for site_index in range(context.grid.site_count)
    ]
    plaquette_wilson = []
    zero = _empty_sector(dimension)
    for plaquette in context.grid.plaquettes:
        rows: list[int] = []
        cols: list[int] = []
        data: list[complex] = []
        for col, matter_index in enumerate(basis.matter_indices.tolist()):
            digits = [int(value) for value in basis.gauge_digits[col].tolist()]
            valid = True
            for link_index, orientation in zip(plaquette.link_indices, plaquette.orientations):
                next_digit = digits[link_index] + (1 if orientation > 0 else -1)
                if next_digit < 0 or next_digit >= context.link_operator.physical_dimension:
                    valid = False
                    break
                digits[link_index] = next_digit
            if not valid:
                continue
            row = _projected_index(
                basis,
                matter_index=int(matter_index),
                gauge_digits=tuple(digits),
                gauge_dimension=int(context.link_operator.encoded_dimension ** context.summary.link_count),
                encoded_dimension=context.link_operator.encoded_dimension,
            )
            if row is None:
                continue
            rows.extend([row, col])
            cols.extend([col, row])
            data.extend([0.5 + 0.0j, 0.5 + 0.0j])
        plaquette_wilson.append(
            sp.coo_matrix((data, (rows, cols)), shape=(dimension, dimension)).tocsr()
        )
    return {
        "site_density": site_density,
        "link_electric_flux": link_electric_flux,
        "link_electric_energy": link_electric_energy,
        "gauss_residual": gauss_residual,
        "plaquette_wilson": plaquette_wilson,
        "zero": zero,
    }
