"""Exploratory finite-cutoff lattice-QED Hamiltonian builder."""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
import hashlib
from typing import Any

import numpy as np
import scipy.sparse as sp
from qiskit.quantum_info import SparsePauliOp

from qcchem.core import LatticeQEDSpec, MoleculeSpec, QFTModelSummary
from qcchem.qft.grid import ATOMIC_NUMBERS, LatticeGrid, build_lattice_grid
from qcchem.qft.links import U1LinkOperators, build_u1_link_operators, matrix_to_sparse_pauli


@dataclass(slots=True)
class LatticeQEDContext:
    """A finite lattice-QED qubit Hamiltonian and its audit metadata."""

    qubit_hamiltonian: SparsePauliOp
    summary: QFTModelSummary
    grid: LatticeGrid
    link_operator: U1LinkOperators
    nuclear_repulsion_energy: float
    target_electrons: int
    hamiltonian_matrix: np.ndarray
    sector_matrices: dict[str, np.ndarray]
    gauss_law_matrices: list[np.ndarray]
    ansatz_generator_ops: list[SparsePauliOp]
    sparse_bundle: "SparseLatticeQEDBundle | None" = None


@dataclass(slots=True)
class SparseLatticeQEDBundle:
    """Sparse full and projected finite-cutoff lattice-QED operators."""

    full_hamiltonian: sp.csr_matrix
    sector_matrices: dict[str, sp.csr_matrix]
    gauss_law_matrices: list[sp.csr_matrix]
    projected_hamiltonian: sp.csr_matrix | None
    projected_sector_matrices: dict[str, sp.csr_matrix]
    projected_gauss_law_matrices: list[sp.csr_matrix]
    physical_indices: np.ndarray
    metadata: dict[str, Any]


def _kron_all(items: list[np.ndarray]) -> np.ndarray:
    return reduce(np.kron, items)


def _identity(dimension: int) -> np.ndarray:
    return np.eye(dimension, dtype=complex)


def _fermion_annihilation(mode_index: int, mode_count: int) -> np.ndarray:
    identity = np.eye(2, dtype=complex)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    sigma_minus = np.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=complex)
    factors = []
    for index in range(mode_count):
        if index < mode_index:
            factors.append(z)
        elif index == mode_index:
            factors.append(sigma_minus)
        else:
            factors.append(identity)
    return _kron_all(factors)


def _fermion_creation(mode_index: int, mode_count: int) -> np.ndarray:
    return _fermion_annihilation(mode_index, mode_count).conj().T


def _fermion_number(mode_index: int, mode_count: int) -> np.ndarray:
    annihilation = _fermion_annihilation(mode_index, mode_count)
    return annihilation.conj().T @ annihilation


def _mode_index(site_index: int, spin_index: int, spin_components: int) -> int:
    return site_index * spin_components + spin_index


def _target_electrons(molecule: MoleculeSpec, spec: LatticeQEDSpec, matter_modes: int) -> int:
    configured = spec.matter.target_electrons
    if configured == "auto":
        total_charge = sum(ATOMIC_NUMBERS[atom.symbol] for atom in molecule.geometry)
        target = int(total_charge - molecule.charge)
    else:
        target = int(configured)
    if target > matter_modes:
        raise ValueError(
            "lattice-QED target electron count exceeds available matter modes; "
            "increase grid.shape or matter.spin_components."
        )
    return target


def _nuclear_repulsion(molecule: MoleculeSpec, softening: float) -> float:
    total = 0.0
    for left_index, left in enumerate(molecule.geometry):
        left_charge = float(ATOMIC_NUMBERS[left.symbol])
        left_position = np.asarray(left.coords, dtype=float)
        for right in molecule.geometry[left_index + 1 :]:
            right_charge = float(ATOMIC_NUMBERS[right.symbol])
            right_position = np.asarray(right.coords, dtype=float)
            distance = float(np.linalg.norm(left_position - right_position))
            total += left_charge * right_charge / np.sqrt(distance**2 + softening**2)
    return float(total)


def _site_nuclear_potential(molecule: MoleculeSpec, position: np.ndarray, softening: float) -> float:
    potential = 0.0
    for atom in molecule.geometry:
        charge = float(ATOMIC_NUMBERS[atom.symbol])
        atom_position = np.asarray(atom.coords, dtype=float)
        distance = float(np.linalg.norm(position - atom_position))
        potential -= charge / np.sqrt(distance**2 + softening**2)
    return float(potential)


def _embed_matter(matter_operator: np.ndarray, *, gauge_dimension: int) -> np.ndarray:
    return np.kron(matter_operator, _identity(gauge_dimension))


def _gauge_block(
    link_count: int,
    encoded_dimension: int,
    matrices_by_link: dict[int, np.ndarray],
) -> np.ndarray:
    blocks = [
        matrices_by_link.get(link_index, _identity(encoded_dimension))
        for link_index in range(link_count)
    ]
    return _kron_all(blocks) if blocks else np.asarray([[1.0]], dtype=complex)


def _embed_gauge(
    matrix: np.ndarray,
    *,
    link_index: int,
    matter_dimension: int,
    link_count: int,
    encoded_dimension: int,
) -> np.ndarray:
    gauge = _gauge_block(link_count, encoded_dimension, {link_index: matrix})
    return np.kron(_identity(matter_dimension), gauge)


def _embed_matter_link(
    matter_operator: np.ndarray,
    link_matrix: np.ndarray,
    *,
    link_index: int,
    link_count: int,
    encoded_dimension: int,
) -> np.ndarray:
    gauge = _gauge_block(link_count, encoded_dimension, {link_index: link_matrix})
    return np.kron(matter_operator, gauge)


def _embed_gauge_product(
    matrices_by_link: dict[int, np.ndarray],
    *,
    matter_dimension: int,
    link_count: int,
    encoded_dimension: int,
) -> np.ndarray:
    gauge = _gauge_block(link_count, encoded_dimension, matrices_by_link)
    return np.kron(_identity(matter_dimension), gauge)


def _sparse_identity(dimension: int) -> sp.csr_matrix:
    return sp.identity(dimension, format="csr", dtype=complex)


def _kron_all_sparse(items: list[sp.spmatrix]) -> sp.csr_matrix:
    if not items:
        return sp.csr_matrix([[1.0 + 0.0j]])
    result = items[0].tocsr()
    for item in items[1:]:
        result = sp.kron(result, item, format="csr")
    return result


def _fermion_annihilation_sparse(mode_index: int, mode_count: int) -> sp.csr_matrix:
    identity = sp.identity(2, format="csr", dtype=complex)
    z = sp.csr_matrix(np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=complex))
    sigma_minus = sp.csr_matrix(np.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=complex))
    factors: list[sp.spmatrix] = []
    for index in range(mode_count):
        if index < mode_index:
            factors.append(z)
        elif index == mode_index:
            factors.append(sigma_minus)
        else:
            factors.append(identity)
    return _kron_all_sparse(factors)


def _fermion_creation_sparse(mode_index: int, mode_count: int) -> sp.csr_matrix:
    return _fermion_annihilation_sparse(mode_index, mode_count).conj().T.tocsr()


def _fermion_number_sparse(mode_index: int, mode_count: int) -> sp.csr_matrix:
    annihilation = _fermion_annihilation_sparse(mode_index, mode_count)
    return (annihilation.conj().T @ annihilation).tocsr()


def _gauge_block_sparse(
    link_count: int,
    encoded_dimension: int,
    matrices_by_link: dict[int, np.ndarray | sp.spmatrix],
) -> sp.csr_matrix:
    blocks = [
        sp.csr_matrix(matrices_by_link.get(link_index, _sparse_identity(encoded_dimension)))
        for link_index in range(link_count)
    ]
    return _kron_all_sparse(blocks)


def _embed_matter_sparse(matter_operator: sp.spmatrix, *, gauge_dimension: int) -> sp.csr_matrix:
    return sp.kron(matter_operator, _sparse_identity(gauge_dimension), format="csr")


def _embed_gauge_sparse(
    matrix: np.ndarray | sp.spmatrix,
    *,
    link_index: int,
    matter_dimension: int,
    link_count: int,
    encoded_dimension: int,
) -> sp.csr_matrix:
    gauge = _gauge_block_sparse(link_count, encoded_dimension, {link_index: matrix})
    return sp.kron(_sparse_identity(matter_dimension), gauge, format="csr")


def _embed_matter_link_sparse(
    matter_operator: sp.spmatrix,
    link_matrix: np.ndarray | sp.spmatrix,
    *,
    link_index: int,
    link_count: int,
    encoded_dimension: int,
) -> sp.csr_matrix:
    gauge = _gauge_block_sparse(link_count, encoded_dimension, {link_index: link_matrix})
    return sp.kron(matter_operator, gauge, format="csr")


def _embed_gauge_product_sparse(
    matrices_by_link: dict[int, np.ndarray | sp.spmatrix],
    *,
    matter_dimension: int,
    link_count: int,
    encoded_dimension: int,
) -> sp.csr_matrix:
    gauge = _gauge_block_sparse(link_count, encoded_dimension, matrices_by_link)
    return sp.kron(_sparse_identity(matter_dimension), gauge, format="csr")


def _sector_pauli_count(matrix: np.ndarray, *, atol: float = 1.0e-10, materialize_pauli: bool = True) -> int:
    if sp.issparse(matrix):
        if matrix.nnz == 0:
            return 0
        if not materialize_pauli:
            return -1
        matrix = matrix.toarray()
    if np.allclose(matrix, 0.0, atol=atol):
        return 0
    if not materialize_pauli:
        return -1
    return len(matrix_to_sparse_pauli(matrix, atol=atol))


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


def _commutator_frobenius(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.linalg.norm(left @ right - right @ left))


def _matrix_diagonal(matrix: np.ndarray | sp.spmatrix) -> np.ndarray:
    if sp.issparse(matrix):
        return np.real_if_close(matrix.diagonal()).astype(float)
    return np.real_if_close(np.diag(matrix)).astype(float)


def _basis_hash(indices: list[int] | np.ndarray) -> str:
    array = np.asarray(indices, dtype=np.int64)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _pauli_metadata(
    matrix: np.ndarray,
    *,
    atol: float = 1.0e-10,
    materialize_pauli: bool = True,
) -> dict[str, Any]:
    pauli_term_count = None
    frobenius_norm = float(sp.linalg.norm(matrix)) if sp.issparse(matrix) else float(np.linalg.norm(matrix))
    hermitian = (
        bool(sp.linalg.norm(matrix - matrix.conj().T) <= atol)
        if sp.issparse(matrix)
        else bool(np.allclose(matrix, matrix.conj().T, atol=atol))
    )
    if materialize_pauli:
        pauli_term_count = int(
            len(matrix_to_sparse_pauli(matrix.toarray() if sp.issparse(matrix) else matrix, atol=atol))
        )
    return {
        "pauli_term_count": pauli_term_count,
        "pauli_materialized": bool(materialize_pauli),
        "frobenius_norm": frobenius_norm,
        "hermitian": hermitian,
    }


def _gauge_basis_is_physical(
    gauge_index: int,
    *,
    link_count: int,
    encoded_dimension: int,
    physical_dimension: int,
) -> bool:
    if link_count == 0:
        return True
    remaining = int(gauge_index)
    for link_position in range(link_count):
        divisor = encoded_dimension ** (link_count - link_position - 1)
        local_index = remaining // divisor
        remaining %= divisor
        if local_index >= physical_dimension:
            return False
    return True


def _enumerate_physical_sector(
    *,
    gauss_law_matrices: list[np.ndarray],
    target_charge_values: list[float],
    matter_dimension: int,
    gauge_dimension: int,
    link_count: int,
    link_ops: U1LinkOperators,
    total_qubits: int,
    max_qubits: int,
    tolerance: float,
    target_charge_sector: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "enumerated": False,
        "physical_sector_dimension": None,
        "target_charge_sector": target_charge_sector,
        "max_sector_enumeration_qubits": int(max_qubits),
        "basis_indices_preview": [],
        "reference_basis_index": None,
    }
    if total_qubits > max_qubits:
        payload.update(
            {
                "skipped_reason": "total_qubits_exceeds_max_sector_enumeration_qubits",
                "estimated_full_dimension": int(2**total_qubits),
            }
        )
        return payload

    diagonals = [_matrix_diagonal(matrix) for matrix in gauss_law_matrices]
    physical_indices: list[int] = []
    padding_rejections = 0
    for matter_index in range(matter_dimension):
        for gauge_index in range(gauge_dimension):
            if not _gauge_basis_is_physical(
                gauge_index,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
                physical_dimension=link_ops.physical_dimension,
            ):
                padding_rejections += 1
                continue
            basis_index = matter_index * gauge_dimension + gauge_index
            residuals = [
                abs(float(diagonal[basis_index]) - float(target))
                for diagonal, target in zip(diagonals, target_charge_values)
            ]
            if all(value <= tolerance for value in residuals):
                physical_indices.append(int(basis_index))

    payload.update(
        {
            "enumerated": True,
            "physical_sector_dimension": int(len(physical_indices)),
            "basis_index_count": int(len(physical_indices)),
            "basis_hash": _basis_hash(physical_indices),
            "basis_indices": physical_indices,
            "basis_indices_preview": physical_indices[:16],
            "padding_state_rejection_count": int(padding_rejections),
            "reference_basis_index": (physical_indices[0] if physical_indices else None),
            "tolerance": float(tolerance),
            "estimated_full_dimension": int(matter_dimension * gauge_dimension),
            "skipped_reason": None,
        }
    )
    return payload


def _build_gauss_law_summary(
    gauss_law_matrices: list[np.ndarray],
    *,
    hamiltonian_matrix: np.ndarray,
    target_charge_values: list[float],
    atol: float,
    materialize_pauli: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    generator_metadata: list[dict[str, Any]] = []
    commutator_metadata: list[dict[str, Any]] = []
    for site_index, matrix in enumerate(gauss_law_matrices):
        metadata = _pauli_metadata(matrix, atol=atol, materialize_pauli=materialize_pauli)
        diagonal = _matrix_diagonal(matrix)
        metadata.update(
            {
                "site_index": int(site_index),
                "target_charge": float(target_charge_values[site_index]),
                "diagonal_min": float(np.min(diagonal)) if len(diagonal) else 0.0,
                "diagonal_max": float(np.max(diagonal)) if len(diagonal) else 0.0,
            }
        )
        generator_metadata.append(metadata)
        if materialize_pauli:
            norm = _commutator_frobenius(hamiltonian_matrix, matrix)
            commutator_metadata.append(
                {
                    "site_index": int(site_index),
                    "frobenius_norm": norm,
                    "within_tolerance": bool(norm <= atol),
                    "skipped_reason": None,
                }
            )
        else:
            commutator_metadata.append(
                {
                    "site_index": int(site_index),
                    "frobenius_norm": None,
                    "within_tolerance": None,
                    "skipped_reason": "full_commutator_skipped_for_dynamics_resource_guard",
                }
            )
    return generator_metadata, commutator_metadata


def _reference_gauss_expectations(
    physical_sector: dict[str, Any],
    gauss_law_matrices: list[np.ndarray],
    target_charge_values: list[float],
) -> dict[str, Any]:
    reference = physical_sector.get("reference_basis_index")
    payload: dict[str, Any] = {
        "reference_basis_index": reference,
        "reference_state_gauss_law_residuals": [],
        "reference_state_max_abs_gauss_law": None,
    }
    if reference is None:
        payload["available"] = False
        return payload
    residuals = [
        float(np.real_if_close(matrix[int(reference), int(reference)]) - float(target))
        for matrix, target in zip(gauss_law_matrices, target_charge_values)
    ]
    payload.update(
        {
            "available": True,
            "reference_state_gauss_law_residuals": residuals,
            "reference_state_max_abs_gauss_law": (
                float(max(abs(value) for value in residuals)) if residuals else 0.0
            ),
        }
    )
    return payload


def _generator_sector_names(policy: str) -> list[str]:
    normalized = policy.strip().lower()
    if normalized == "gauge_invariant_hopping":
        return ["hopping"]
    if normalized == "electric_magnetic":
        return ["hopping", "electric", "magnetic_plaquette"]
    if normalized == "conservative":
        return ["hopping"]
    raise ValueError(
        "problem.qft.ansatz.generator_policy must be one of "
        "'gauge_invariant_hopping', 'electric_magnetic', or 'conservative'."
    )


def _build_gauge_invariant_ansatz_plan(
    sectors: dict[str, np.ndarray],
    gauss_law_matrices: list[np.ndarray],
    spec: LatticeQEDSpec,
    *,
    atol: float,
    materialize_pauli: bool,
) -> tuple[dict[str, Any], list[SparsePauliOp]]:
    selected: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    operators: list[SparsePauliOp] = []
    for sector_name in _generator_sector_names(spec.ansatz.generator_policy):
        matrix = sectors.get(sector_name)
        empty_matrix = matrix is None or (
            matrix.nnz == 0 if sp.issparse(matrix) else np.allclose(matrix, 0.0, atol=atol)
        )
        if empty_matrix:
            checks.append(
                {
                    "sector": sector_name,
                    "selected": False,
                    "reason": "empty_sector",
                    "commutes_with_all_gauss_law_generators": True,
                    "max_commutator_norm": 0.0,
                }
            )
            continue
        hermitian = (0.5 * (matrix + matrix.conj().T)).tocsr() if sp.issparse(matrix) else 0.5 * (matrix + matrix.conj().T)
        if materialize_pauli:
            norms = [_commutator_frobenius(hermitian, gauss) for gauss in gauss_law_matrices]
        else:
            norms = []
        max_norm = float(max(norms)) if norms else 0.0
        commutes = bool(max_norm <= atol) if materialize_pauli else False
        item = {
            "sector": sector_name,
            "selected": commutes,
            "commutes_with_all_gauss_law_generators": commutes,
            "max_commutator_norm": (max_norm if materialize_pauli else None),
            "commutator_norms": [float(value) for value in norms],
            "pauli_term_count": _sector_pauli_count(
                hermitian,
                atol=atol,
                materialize_pauli=materialize_pauli,
            ),
            "pauli_materialized": bool(materialize_pauli),
            "skipped_reason": (
                None if materialize_pauli else "ansatz_commutator_skipped_for_dynamics_resource_guard"
            ),
        }
        checks.append(item)
        if commutes:
            selected.append(dict(item))
            if materialize_pauli:
                operators.append(matrix_to_sparse_pauli(hermitian, atol=atol).simplify(atol=atol))

    return (
        {
            "kind": "gauss_law_preserving",
            "generator_policy": spec.ansatz.generator_policy,
            "selected_generator_count": len(selected),
            "selected_generators": selected,
            "commutator_checks": checks,
        },
        operators,
    )


def _build_sector_matrices(
    molecule: MoleculeSpec,
    spec: LatticeQEDSpec,
    grid: LatticeGrid,
    link_ops: U1LinkOperators,
    target_electrons: int,
) -> tuple[dict[str, np.ndarray], list[np.ndarray], int, int, int]:
    spin_components = int(spec.matter.spin_components)
    if spin_components < 1:
        raise ValueError("problem.qft.matter.spin_components must be at least 1.")
    matter_modes = grid.site_count * spin_components
    matter_dimension = 2**matter_modes
    link_count = len(grid.links)
    gauge_dimension = link_ops.encoded_dimension**link_count
    total_dimension = matter_dimension * gauge_dimension

    matter_identity = _identity(matter_dimension)
    total_identity = _identity(total_dimension)
    number_ops = [_fermion_number(mode, matter_modes) for mode in range(matter_modes)]
    creation_ops = [_fermion_creation(mode, matter_modes) for mode in range(matter_modes)]
    annihilation_ops = [_fermion_annihilation(mode, matter_modes) for mode in range(matter_modes)]

    sectors = {
        "onsite": np.zeros((total_dimension, total_dimension), dtype=complex),
        "hopping": np.zeros((total_dimension, total_dimension), dtype=complex),
        "density_coulomb": np.zeros((total_dimension, total_dimension), dtype=complex),
        "electric": np.zeros((total_dimension, total_dimension), dtype=complex),
        "magnetic_plaquette": np.zeros((total_dimension, total_dimension), dtype=complex),
        "gauss_law_penalty": np.zeros((total_dimension, total_dimension), dtype=complex),
        "particle_number_penalty": np.zeros((total_dimension, total_dimension), dtype=complex),
        "padding_penalty": np.zeros((total_dimension, total_dimension), dtype=complex),
    }

    for site in grid.sites:
        potential = _site_nuclear_potential(
            molecule,
            np.asarray(site.real_space_coordinate, dtype=float),
            spec.grid.softening,
        )
        for spin in range(spin_components):
            mode = _mode_index(site.linear_index, spin, spin_components)
            sectors["onsite"] += potential * _embed_matter(number_ops[mode], gauge_dimension=gauge_dimension)

    if spec.matter.include_soft_coulomb_density:
        for left in grid.sites:
            left_position = np.asarray(left.real_space_coordinate, dtype=float)
            for right in grid.sites:
                if right.linear_index <= left.linear_index:
                    continue
                right_position = np.asarray(right.real_space_coordinate, dtype=float)
                distance = float(np.linalg.norm(left_position - right_position))
                strength = 1.0 / np.sqrt(distance**2 + spec.grid.softening**2)
                left_density = sum(
                    number_ops[_mode_index(left.linear_index, spin, spin_components)]
                    for spin in range(spin_components)
                )
                right_density = sum(
                    number_ops[_mode_index(right.linear_index, spin, spin_components)]
                    for spin in range(spin_components)
                )
                sectors["density_coulomb"] += strength * _embed_matter(
                    left_density @ right_density,
                    gauge_dimension=gauge_dimension,
                )

    for link in grid.links:
        spacing = float(spec.grid.spacing[link.direction])
        hopping_strength = 1.0 / (2.0 * spacing**2)
        for spin in range(spin_components):
            start_mode = _mode_index(link.start_site, spin, spin_components)
            end_mode = _mode_index(link.end_site, spin, spin_components)
            forward = creation_ops[end_mode] @ annihilation_ops[start_mode]
            backward = creation_ops[start_mode] @ annihilation_ops[end_mode]
            sectors["hopping"] += -hopping_strength * _embed_matter_link(
                forward,
                link_ops.raising_matrix,
                link_index=link.linear_index,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
            sectors["hopping"] += -hopping_strength * _embed_matter_link(
                backward,
                link_ops.lowering_matrix,
                link_index=link.linear_index,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )

        sectors["electric"] += 0.5 * (spec.gauge.coupling**2) * _embed_gauge(
            link_ops.electric_squared_matrix,
            link_index=link.linear_index,
            matter_dimension=matter_dimension,
            link_count=link_count,
            encoded_dimension=link_ops.encoded_dimension,
        )

        if spec.constraints.padding_penalty > 0.0:
            sectors["padding_penalty"] += spec.constraints.padding_penalty * _embed_gauge(
                link_ops.padding_projector_matrix,
                link_index=link.linear_index,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )

    if spec.gauge.include_magnetic_plaquettes and grid.plaquettes:
        coefficient = -0.5 / max(spec.gauge.coupling**2, 1.0e-12)
        for plaquette in grid.plaquettes:
            matrices: dict[int, np.ndarray] = {}
            for link_index, orientation in zip(plaquette.link_indices, plaquette.orientations):
                matrices[link_index] = (
                    link_ops.raising_matrix if orientation > 0 else link_ops.lowering_matrix
                )
            plaquette_op = _embed_gauge_product(
                matrices,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
            sectors["magnetic_plaquette"] += coefficient * (plaquette_op + plaquette_op.conj().T)

    incoming: dict[int, list[int]] = {site.linear_index: [] for site in grid.sites}
    outgoing: dict[int, list[int]] = {site.linear_index: [] for site in grid.sites}
    for link in grid.links:
        outgoing[link.start_site].append(link.linear_index)
        incoming[link.end_site].append(link.linear_index)
    gauss_law_matrices: list[np.ndarray] = []
    for site in grid.sites:
        divergence = np.zeros((total_dimension, total_dimension), dtype=complex)
        for link_index in outgoing[site.linear_index]:
            divergence += _embed_gauge(
                link_ops.electric_matrix,
                link_index=link_index,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
        for link_index in incoming[site.linear_index]:
            divergence -= _embed_gauge(
                link_ops.electric_matrix,
                link_index=link_index,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
        local_density = np.zeros((matter_dimension, matter_dimension), dtype=complex)
        for spin in range(spin_components):
            local_density += number_ops[_mode_index(site.linear_index, spin, spin_components)]
        charge = _embed_matter(local_density, gauge_dimension=gauge_dimension)
        charge -= float(grid.nuclear_charge_by_site[site.linear_index]) * total_identity
        gauss = divergence + charge
        gauss_law_matrices.append(gauss)
        if spec.constraints.gauss_law_penalty > 0.0:
            sectors["gauss_law_penalty"] += spec.constraints.gauss_law_penalty * (gauss @ gauss)

    if spec.constraints.particle_number_penalty > 0.0:
        total_number = sum(number_ops)
        shifted = total_number - float(target_electrons) * matter_identity
        sectors["particle_number_penalty"] += spec.constraints.particle_number_penalty * _embed_matter(
            shifted @ shifted,
            gauge_dimension=gauge_dimension,
        )

    return sectors, gauss_law_matrices, matter_modes, matter_dimension, gauge_dimension


def _zero_sparse_sectors(total_dimension: int) -> dict[str, sp.csr_matrix]:
    return {
        "onsite": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "hopping": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "density_coulomb": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "electric": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "magnetic_plaquette": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "gauss_law_penalty": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "particle_number_penalty": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
        "padding_penalty": sp.csr_matrix((total_dimension, total_dimension), dtype=complex),
    }


def _build_sparse_sector_matrices(
    molecule: MoleculeSpec,
    spec: LatticeQEDSpec,
    grid: LatticeGrid,
    link_ops: U1LinkOperators,
    target_electrons: int,
) -> tuple[dict[str, sp.csr_matrix], list[sp.csr_matrix], int, int, int]:
    spin_components = int(spec.matter.spin_components)
    if spin_components < 1:
        raise ValueError("problem.qft.matter.spin_components must be at least 1.")
    matter_modes = grid.site_count * spin_components
    matter_dimension = 2**matter_modes
    link_count = len(grid.links)
    gauge_dimension = link_ops.encoded_dimension**link_count
    total_dimension = matter_dimension * gauge_dimension

    matter_identity = _sparse_identity(matter_dimension)
    total_identity = _sparse_identity(total_dimension)
    number_ops = [_fermion_number_sparse(mode, matter_modes) for mode in range(matter_modes)]
    creation_ops = [_fermion_creation_sparse(mode, matter_modes) for mode in range(matter_modes)]
    annihilation_ops = [_fermion_annihilation_sparse(mode, matter_modes) for mode in range(matter_modes)]
    sectors = _zero_sparse_sectors(total_dimension)

    for site in grid.sites:
        potential = _site_nuclear_potential(
            molecule,
            np.asarray(site.real_space_coordinate, dtype=float),
            spec.grid.softening,
        )
        for spin_index in range(spin_components):
            mode = _mode_index(site.linear_index, spin_index, spin_components)
            sectors["onsite"] += potential * _embed_matter_sparse(
                number_ops[mode],
                gauge_dimension=gauge_dimension,
            )

    if spec.matter.include_soft_coulomb_density:
        for left in grid.sites:
            left_position = np.asarray(left.real_space_coordinate, dtype=float)
            for right in grid.sites:
                if right.linear_index <= left.linear_index:
                    continue
                right_position = np.asarray(right.real_space_coordinate, dtype=float)
                distance = float(np.linalg.norm(left_position - right_position))
                strength = 1.0 / np.sqrt(distance**2 + spec.grid.softening**2)
                left_density = sum(
                    (
                        number_ops[_mode_index(left.linear_index, spin_index, spin_components)]
                        for spin_index in range(spin_components)
                    ),
                    sp.csr_matrix((matter_dimension, matter_dimension), dtype=complex),
                )
                right_density = sum(
                    (
                        number_ops[_mode_index(right.linear_index, spin_index, spin_components)]
                        for spin_index in range(spin_components)
                    ),
                    sp.csr_matrix((matter_dimension, matter_dimension), dtype=complex),
                )
                sectors["density_coulomb"] += strength * _embed_matter_sparse(
                    left_density @ right_density,
                    gauge_dimension=gauge_dimension,
                )

    raising = sp.csr_matrix(link_ops.raising_matrix)
    lowering = sp.csr_matrix(link_ops.lowering_matrix)
    electric = sp.csr_matrix(link_ops.electric_matrix)
    electric_squared = sp.csr_matrix(link_ops.electric_squared_matrix)
    padding = sp.csr_matrix(link_ops.padding_projector_matrix)
    for link in grid.links:
        spacing = float(spec.grid.spacing[link.direction])
        hopping_strength = 1.0 / (2.0 * spacing**2)
        for spin_index in range(spin_components):
            start_mode = _mode_index(link.start_site, spin_index, spin_components)
            end_mode = _mode_index(link.end_site, spin_index, spin_components)
            forward = creation_ops[end_mode] @ annihilation_ops[start_mode]
            backward = creation_ops[start_mode] @ annihilation_ops[end_mode]
            sectors["hopping"] += -hopping_strength * _embed_matter_link_sparse(
                forward,
                raising,
                link_index=link.linear_index,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
            sectors["hopping"] += -hopping_strength * _embed_matter_link_sparse(
                backward,
                lowering,
                link_index=link.linear_index,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )

        sectors["electric"] += 0.5 * (spec.gauge.coupling**2) * _embed_gauge_sparse(
            electric_squared,
            link_index=link.linear_index,
            matter_dimension=matter_dimension,
            link_count=link_count,
            encoded_dimension=link_ops.encoded_dimension,
        )

        if spec.constraints.padding_penalty > 0.0:
            sectors["padding_penalty"] += spec.constraints.padding_penalty * _embed_gauge_sparse(
                padding,
                link_index=link.linear_index,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )

    if spec.gauge.include_magnetic_plaquettes and grid.plaquettes:
        coefficient = -0.5 / max(spec.gauge.coupling**2, 1.0e-12)
        for plaquette in grid.plaquettes:
            matrices: dict[int, sp.csr_matrix] = {}
            for link_index, orientation in zip(plaquette.link_indices, plaquette.orientations):
                matrices[link_index] = raising if orientation > 0 else lowering
            plaquette_op = _embed_gauge_product_sparse(
                matrices,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
            sectors["magnetic_plaquette"] += coefficient * (plaquette_op + plaquette_op.conj().T)

    incoming: dict[int, list[int]] = {site.linear_index: [] for site in grid.sites}
    outgoing: dict[int, list[int]] = {site.linear_index: [] for site in grid.sites}
    for link in grid.links:
        outgoing[link.start_site].append(link.linear_index)
        incoming[link.end_site].append(link.linear_index)
    gauss_law_matrices: list[sp.csr_matrix] = []
    for site in grid.sites:
        divergence = sp.csr_matrix((total_dimension, total_dimension), dtype=complex)
        for link_index in outgoing[site.linear_index]:
            divergence += _embed_gauge_sparse(
                electric,
                link_index=link_index,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
        for link_index in incoming[site.linear_index]:
            divergence -= _embed_gauge_sparse(
                electric,
                link_index=link_index,
                matter_dimension=matter_dimension,
                link_count=link_count,
                encoded_dimension=link_ops.encoded_dimension,
            )
        local_density = sum(
            (
                number_ops[_mode_index(site.linear_index, spin_index, spin_components)]
                for spin_index in range(spin_components)
            ),
            sp.csr_matrix((matter_dimension, matter_dimension), dtype=complex),
        )
        charge = _embed_matter_sparse(local_density, gauge_dimension=gauge_dimension)
        charge -= float(grid.nuclear_charge_by_site[site.linear_index]) * total_identity
        gauss = (divergence + charge).tocsr()
        gauss_law_matrices.append(gauss)
        if spec.constraints.gauss_law_penalty > 0.0:
            sectors["gauss_law_penalty"] += spec.constraints.gauss_law_penalty * (gauss @ gauss)

    if spec.constraints.particle_number_penalty > 0.0:
        total_number = sum(
            number_ops,
            sp.csr_matrix((matter_dimension, matter_dimension), dtype=complex),
        )
        shifted = total_number - float(target_electrons) * matter_identity
        sectors["particle_number_penalty"] += spec.constraints.particle_number_penalty * _embed_matter_sparse(
            shifted @ shifted,
            gauge_dimension=gauge_dimension,
        )

    return {key: value.tocsr() for key, value in sectors.items()}, gauss_law_matrices, matter_modes, matter_dimension, gauge_dimension


def _resolve_engine_representation(spec: LatticeQEDSpec, total_qubits: int) -> str:
    requested = spec.engine.representation.strip().lower()
    if requested != "auto":
        return requested
    if (
        spec.engine.auto_project_physical_sector
        and total_qubits > int(spec.engine.max_full_qubits_for_dense)
    ):
        return "sparse_projected"
    return "dense_full"


def _resolve_materialize_pauli(
    spec: LatticeQEDSpec,
    *,
    actual_representation: str,
    materialize_pauli: bool,
    total_qubits: int,
) -> bool:
    requested = spec.engine.materialize_pauli.strip().lower()
    if requested == "always":
        return bool(materialize_pauli)
    if requested == "never":
        return False
    return bool(
        materialize_pauli
        and actual_representation == "dense_full"
        and total_qubits <= int(spec.engine.max_full_qubits_for_dense)
    )


def _sparse_sector_counts(sectors: dict[str, sp.csr_matrix]) -> dict[str, int]:
    return {name: int(matrix.nnz) for name, matrix in sectors.items()}


def _project_sparse_bundle(
    sectors: dict[str, sp.csr_matrix],
    gauss_law_matrices: list[sp.csr_matrix],
    physical_sector: dict[str, Any],
    *,
    max_projected_dimension: int,
) -> tuple[sp.csr_matrix | None, dict[str, sp.csr_matrix], list[sp.csr_matrix], np.ndarray, dict[str, Any]]:
    indices = np.asarray(physical_sector.get("basis_indices", []), dtype=int)
    metadata: dict[str, Any] = {
        "projected": False,
        "projected_dimension": 0,
        "projection_skipped_reason": None,
    }
    if indices.size == 0:
        metadata["projection_skipped_reason"] = "physical_sector_empty_or_not_enumerated"
        return None, {}, [], indices, metadata
    if indices.size > max_projected_dimension:
        metadata["projection_skipped_reason"] = "physical_sector_exceeds_max_projected_dimension"
        metadata["projected_dimension"] = int(indices.size)
        return None, {}, [], indices, metadata
    projected_sectors = {
        name: matrix[indices, :][:, indices].tocsr()
        for name, matrix in sectors.items()
    }
    projected_hamiltonian = sum(
        projected_sectors.values(),
        sp.csr_matrix((indices.size, indices.size), dtype=complex),
    ).tocsr()
    projected_gauss = [matrix[indices, :][:, indices].tocsr() for matrix in gauss_law_matrices]
    metadata.update(
        {
            "projected": True,
            "projected_dimension": int(indices.size),
        }
    )
    return projected_hamiltonian, projected_sectors, projected_gauss, indices, metadata


def _build_sparse_bundle(
    sectors: dict[str, sp.csr_matrix],
    gauss_law_matrices: list[sp.csr_matrix],
    physical_sector: dict[str, Any],
    spec: LatticeQEDSpec,
    *,
    full_dimension: int,
    actual_representation: str,
) -> SparseLatticeQEDBundle:
    full_hamiltonian = sum(
        sectors.values(),
        sp.csr_matrix((full_dimension, full_dimension), dtype=complex),
    ).tocsr()
    full_hamiltonian = (0.5 * (full_hamiltonian + full_hamiltonian.conj().T)).tocsr()
    projected_hamiltonian = None
    projected_sectors: dict[str, sp.csr_matrix] = {}
    projected_gauss: list[sp.csr_matrix] = []
    physical_indices = np.asarray(physical_sector.get("basis_indices", []), dtype=int)
    projection_metadata: dict[str, Any] = {
        "projected": False,
        "projected_dimension": None,
        "projection_skipped_reason": "projection_not_requested",
    }
    if actual_representation == "sparse_projected":
        (
            projected_hamiltonian,
            projected_sectors,
            projected_gauss,
            physical_indices,
            projection_metadata,
        ) = _project_sparse_bundle(
            sectors,
            gauss_law_matrices,
            physical_sector,
            max_projected_dimension=int(spec.engine.max_projected_dimension),
        )
    return SparseLatticeQEDBundle(
        full_hamiltonian=full_hamiltonian,
        sector_matrices=sectors,
        gauss_law_matrices=gauss_law_matrices,
        projected_hamiltonian=projected_hamiltonian,
        projected_sector_matrices=projected_sectors,
        projected_gauss_law_matrices=projected_gauss,
        physical_indices=physical_indices,
        metadata={
            "operator_representation": actual_representation,
            "full_dimension": int(full_dimension),
            "full_nnz": int(full_hamiltonian.nnz),
            "sector_nnz": _sparse_sector_counts(sectors),
            **projection_metadata,
        },
    )


def _sparse_reference_gauss_expectations(
    physical_sector: dict[str, Any],
    gauss_law_matrices: list[sp.csr_matrix],
    target_charge_values: list[float],
) -> dict[str, Any]:
    reference = physical_sector.get("reference_basis_index")
    payload: dict[str, Any] = {
        "reference_basis_index": reference,
        "reference_state_gauss_law_residuals": [],
        "reference_state_max_abs_gauss_law": None,
    }
    if reference is None:
        payload["available"] = False
        return payload
    residuals = [
        float(np.real_if_close(matrix.diagonal()[int(reference)]) - float(target))
        for matrix, target in zip(gauss_law_matrices, target_charge_values)
    ]
    payload.update(
        {
            "available": True,
            "reference_state_gauss_law_residuals": residuals,
            "reference_state_max_abs_gauss_law": (
                float(max(abs(value) for value in residuals)) if residuals else 0.0
            ),
        }
    )
    return payload


def _build_sparse_lattice_qed_context(
    molecule: MoleculeSpec,
    spec: LatticeQEDSpec,
    grid: LatticeGrid,
    link_ops: U1LinkOperators,
    target: int,
    *,
    actual_representation: str,
    materialize_resolved: bool,
    total_qubits: int,
) -> LatticeQEDContext:
    sectors, gauss_law_matrices, matter_modes, matter_dimension, gauge_dimension = _build_sparse_sector_matrices(
        molecule,
        spec,
        grid,
        link_ops,
        target,
    )
    full_dimension = matter_dimension * gauge_dimension
    tolerance = float(spec.engine.projector_tolerance)
    target_charge_values = _target_charge_values(spec, grid.site_count)
    physical_sector = _enumerate_physical_sector(
        gauss_law_matrices=gauss_law_matrices,
        target_charge_values=target_charge_values,
        matter_dimension=matter_dimension,
        gauge_dimension=gauge_dimension,
        link_count=len(grid.links),
        link_ops=link_ops,
        total_qubits=total_qubits,
        max_qubits=int(spec.constraints.max_sector_enumeration_qubits),
        tolerance=tolerance,
        target_charge_sector=str(spec.constraints.target_charge_sector),
    )
    sparse_bundle = _build_sparse_bundle(
        sectors,
        gauss_law_matrices,
        physical_sector,
        spec,
        full_dimension=full_dimension,
        actual_representation=actual_representation,
    )
    gauss_metadata, commutator_metadata = _build_gauss_law_summary(
        gauss_law_matrices,
        hamiltonian_matrix=np.zeros((0, 0), dtype=complex),
        target_charge_values=target_charge_values,
        atol=tolerance,
        materialize_pauli=False,
    )
    ansatz_metadata, ansatz_generator_ops = _build_gauge_invariant_ansatz_plan(
        sectors,
        gauss_law_matrices,
        spec,
        atol=tolerance,
        materialize_pauli=False,
    )
    constraint_expectations = {
        "available": False,
        "gauss_law_tolerance": tolerance,
        "target_charge_sector": str(spec.constraints.target_charge_sector),
        **_sparse_reference_gauss_expectations(
            physical_sector,
            gauss_law_matrices,
            target_charge_values,
        ),
    }
    constraints = {
        "gauss_law_penalty": float(spec.constraints.gauss_law_penalty),
        "particle_number_penalty": float(spec.constraints.particle_number_penalty),
        "padding_penalty": float(spec.constraints.padding_penalty),
        "enforce_physical_sector": bool(spec.constraints.enforce_physical_sector),
        "target_charge_sector": str(spec.constraints.target_charge_sector),
        "gauss_law_tolerance": float(spec.constraints.gauss_law_tolerance),
        "max_sector_enumeration_qubits": int(spec.constraints.max_sector_enumeration_qubits),
    }
    constraint_residuals = {
        "gauss_law_penalty": float(spec.constraints.gauss_law_penalty),
        "particle_number_penalty": float(spec.constraints.particle_number_penalty),
        "padding_penalty": float(spec.constraints.padding_penalty),
        "max_hamiltonian_gauge_commutator_norm": None,
        "reference_state_max_abs_gauss_law": float(
            constraint_expectations.get("reference_state_max_abs_gauss_law") or 0.0
        ),
    }
    pauli_materialization = "materialized" if materialize_resolved else "skipped"
    gauge_qubits = len(grid.links) * link_ops.num_qubits
    nuclear_repulsion = _nuclear_repulsion(molecule, spec.grid.softening)
    qubit_hamiltonian = SparsePauliOp.from_list([("I" * total_qubits, 0.0)])
    if materialize_resolved:
        source = sparse_bundle.full_hamiltonian
        qubit_hamiltonian = matrix_to_sparse_pauli(source.toarray(), atol=1.0e-10).simplify(atol=1.0e-10)
    engine_metadata = {
        "requested_representation": spec.engine.representation,
        "actual_representation": actual_representation,
        "operator_representation": actual_representation,
        "auto_project_physical_sector": bool(spec.engine.auto_project_physical_sector),
        "projected_dimension": sparse_bundle.metadata.get("projected_dimension"),
        "full_dimension": int(full_dimension),
        "max_projected_dimension": int(spec.engine.max_projected_dimension),
        "max_full_qubits_for_dense": int(spec.engine.max_full_qubits_for_dense),
        "materialize_pauli": spec.engine.materialize_pauli,
        "pauli_materialization": pauli_materialization,
        "dense_full_matrix_materialized": False,
        "store_basis_indices": spec.engine.store_basis_indices,
        "projector_tolerance": tolerance,
        "full_hamiltonian_nnz": int(sparse_bundle.full_hamiltonian.nnz),
        "sector_nnz": dict(sparse_bundle.metadata.get("sector_nnz", {})),
        "projection_skipped_reason": sparse_bundle.metadata.get("projection_skipped_reason"),
    }
    return LatticeQEDContext(
        qubit_hamiltonian=qubit_hamiltonian,
        summary=QFTModelSummary(
            enabled=True,
            model=spec.model,
            dimensions=spec.dimensions,
            grid_shape=list(spec.grid.shape),
            grid_spacing=[float(value) for value in spec.grid.spacing],
            grid_origin=spec.grid.origin,
            grid_axes=spec.grid.axes,
            boundary=spec.grid.boundary,
            softening=float(spec.grid.softening),
            site_count=grid.site_count,
            link_count=len(grid.links),
            plaquette_count=len(grid.plaquettes),
            matter_mode_count=matter_modes,
            matter_qubits=matter_modes,
            gauge_qubits=gauge_qubits,
            total_qubits=total_qubits,
            gauge_group=spec.gauge.group,
            gauge_electric_cutoff=int(spec.gauge.electric_cutoff),
            gauge_coupling=float(spec.gauge.coupling),
            target_electrons=target,
            term_counts_by_sector=_sparse_sector_counts(sectors),
            constraints=constraints,
            constraint_residuals=constraint_residuals,
            nuclear_charge_by_site=[float(value) for value in grid.nuclear_charge_by_site],
            gauss_law_generators=gauss_metadata,
            hamiltonian_gauge_commutator_norms=commutator_metadata,
            physical_sector=physical_sector,
            gauge_invariant_ansatz=ansatz_metadata,
            constraint_expectations=constraint_expectations,
            engine=engine_metadata,
            notes=[
                "Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.",
                "Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.",
                "Runtime circuits still act on the full qubit register unless explicitly transformed.",
            ],
        ),
        grid=grid,
        link_operator=link_ops,
        nuclear_repulsion_energy=nuclear_repulsion,
        target_electrons=target,
        hamiltonian_matrix=np.zeros((0, 0), dtype=complex),
        sector_matrices={},
        gauss_law_matrices=[],
        ansatz_generator_ops=ansatz_generator_ops,
        sparse_bundle=sparse_bundle,
    )


def build_lattice_qed_context(
    molecule: MoleculeSpec,
    spec: LatticeQEDSpec,
    *,
    mapping_kind: str,
    materialize_pauli: bool = True,
) -> LatticeQEDContext:
    """Build a finite real-space compact-U(1) lattice-QED qubit Hamiltonian."""
    if spec.model.strip().lower() != "lattice_qed_minimal_coupling":
        raise ValueError(f"Unsupported lattice-QED model: {spec.model}")
    if spec.gauge.group.strip().lower() != "u1":
        raise ValueError(f"Unsupported lattice-QED gauge group: {spec.gauge.group}")
    if mapping_kind.strip().lower() != "jordan_wigner":
        raise ValueError("lattice-QED matter fields currently require mapping.kind='jordan_wigner'.")

    grid = build_lattice_grid(molecule, spec)
    spin_components = int(spec.matter.spin_components)
    matter_modes = grid.site_count * spin_components
    target = _target_electrons(molecule, spec, matter_modes)
    link_ops = build_u1_link_operators(spec.gauge.electric_cutoff)
    total_qubits = matter_modes + len(grid.links) * link_ops.num_qubits
    actual_representation = _resolve_engine_representation(spec, total_qubits)
    materialize_resolved = _resolve_materialize_pauli(
        spec,
        actual_representation=actual_representation,
        materialize_pauli=materialize_pauli,
        total_qubits=total_qubits,
    )
    if actual_representation in {"sparse_projected", "sparse_full"}:
        return _build_sparse_lattice_qed_context(
            molecule,
            spec,
            grid,
            link_ops,
            target,
            actual_representation=actual_representation,
            materialize_resolved=materialize_resolved,
            total_qubits=total_qubits,
        )
    sectors, gauss_law_matrices, matter_modes, matter_dimension, gauge_dimension = _build_sector_matrices(
        molecule,
        spec,
        grid,
        link_ops,
        target,
    )
    hamiltonian_matrix = sum(sectors.values())
    hamiltonian_matrix = 0.5 * (hamiltonian_matrix + hamiltonian_matrix.conj().T)
    if materialize_resolved:
        qubit_hamiltonian = matrix_to_sparse_pauli(hamiltonian_matrix, atol=1.0e-10).simplify(atol=1.0e-10)
    else:
        qubit_hamiltonian = SparsePauliOp.from_list([("I" * total_qubits, 0.0)])
    term_counts = {
        sector: _sector_pauli_count(
            matrix,
            atol=1.0e-10,
            materialize_pauli=materialize_resolved,
        )
        for sector, matrix in sectors.items()
    }
    gauge_qubits = len(grid.links) * link_ops.num_qubits
    nuclear_repulsion = _nuclear_repulsion(molecule, spec.grid.softening)
    tolerance = float(spec.constraints.gauss_law_tolerance)
    target_charge_values = _target_charge_values(spec, grid.site_count)
    gauss_metadata, commutator_metadata = _build_gauss_law_summary(
        gauss_law_matrices,
        hamiltonian_matrix=hamiltonian_matrix,
        target_charge_values=target_charge_values,
        atol=tolerance,
        materialize_pauli=materialize_resolved,
    )
    physical_sector = _enumerate_physical_sector(
        gauss_law_matrices=gauss_law_matrices,
        target_charge_values=target_charge_values,
        matter_dimension=matter_dimension,
        gauge_dimension=gauge_dimension,
        link_count=len(grid.links),
        link_ops=link_ops,
        total_qubits=total_qubits,
        max_qubits=int(spec.constraints.max_sector_enumeration_qubits),
        tolerance=tolerance,
        target_charge_sector=str(spec.constraints.target_charge_sector),
    )
    ansatz_metadata, ansatz_generator_ops = _build_gauge_invariant_ansatz_plan(
        sectors,
        gauss_law_matrices,
        spec,
        atol=tolerance,
        materialize_pauli=materialize_resolved,
    )
    constraint_expectations = {
        "available": False,
        "gauss_law_tolerance": tolerance,
        "target_charge_sector": str(spec.constraints.target_charge_sector),
        **_reference_gauss_expectations(
            physical_sector,
            gauss_law_matrices,
            target_charge_values,
        ),
    }
    constraints = {
        "gauss_law_penalty": float(spec.constraints.gauss_law_penalty),
        "particle_number_penalty": float(spec.constraints.particle_number_penalty),
        "padding_penalty": float(spec.constraints.padding_penalty),
        "enforce_physical_sector": bool(spec.constraints.enforce_physical_sector),
        "target_charge_sector": str(spec.constraints.target_charge_sector),
        "gauss_law_tolerance": tolerance,
        "max_sector_enumeration_qubits": int(spec.constraints.max_sector_enumeration_qubits),
    }
    numeric_commutator_norms = [
        float(item["frobenius_norm"])
        for item in commutator_metadata
        if item.get("frobenius_norm") is not None
    ]
    constraint_residuals = {
        "gauss_law_penalty": float(spec.constraints.gauss_law_penalty),
        "particle_number_penalty": float(spec.constraints.particle_number_penalty),
        "padding_penalty": float(spec.constraints.padding_penalty),
        "max_hamiltonian_gauge_commutator_norm": (
            float(max(numeric_commutator_norms)) if numeric_commutator_norms else None
        ),
        "reference_state_max_abs_gauss_law": float(
            constraint_expectations.get("reference_state_max_abs_gauss_law") or 0.0
        ),
    }
    engine_metadata = {
        "requested_representation": spec.engine.representation,
        "actual_representation": actual_representation,
        "operator_representation": actual_representation,
        "auto_project_physical_sector": bool(spec.engine.auto_project_physical_sector),
        "projected_dimension": None,
        "full_dimension": int(matter_dimension * gauge_dimension),
        "max_projected_dimension": int(spec.engine.max_projected_dimension),
        "max_full_qubits_for_dense": int(spec.engine.max_full_qubits_for_dense),
        "materialize_pauli": spec.engine.materialize_pauli,
        "pauli_materialization": "materialized" if materialize_resolved else "skipped",
        "dense_full_matrix_materialized": True,
        "store_basis_indices": spec.engine.store_basis_indices,
        "projector_tolerance": float(spec.engine.projector_tolerance),
        "full_hamiltonian_nnz": int(np.count_nonzero(np.abs(hamiltonian_matrix) > 1.0e-12)),
        "sector_nnz": {
            sector: int(np.count_nonzero(np.abs(matrix) > 1.0e-12))
            for sector, matrix in sectors.items()
        },
        "projection_skipped_reason": "dense_full_representation",
    }

    return LatticeQEDContext(
        qubit_hamiltonian=qubit_hamiltonian,
        summary=QFTModelSummary(
            enabled=True,
            model=spec.model,
            dimensions=spec.dimensions,
            grid_shape=list(spec.grid.shape),
            grid_spacing=[float(value) for value in spec.grid.spacing],
            grid_origin=spec.grid.origin,
            grid_axes=spec.grid.axes,
            boundary=spec.grid.boundary,
            softening=float(spec.grid.softening),
            site_count=grid.site_count,
            link_count=len(grid.links),
            plaquette_count=len(grid.plaquettes),
            matter_mode_count=matter_modes,
            matter_qubits=matter_modes,
            gauge_qubits=gauge_qubits,
            total_qubits=total_qubits,
            gauge_group=spec.gauge.group,
            gauge_electric_cutoff=int(spec.gauge.electric_cutoff),
            gauge_coupling=float(spec.gauge.coupling),
            target_electrons=target,
            term_counts_by_sector=term_counts,
            constraints=constraints,
            constraint_residuals=constraint_residuals,
            nuclear_charge_by_site=[float(value) for value in grid.nuclear_charge_by_site],
            gauss_law_generators=gauss_metadata,
            hamiltonian_gauge_commutator_norms=commutator_metadata,
            physical_sector=physical_sector,
            gauge_invariant_ansatz=ansatz_metadata,
            constraint_expectations=constraint_expectations,
            engine=engine_metadata,
            notes=[
                "Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.",
                "Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.",
                f"Gauge links use binary padding with encoded dimension {link_ops.encoded_dimension}.",
                (
                    "Pauli decomposition was materialized for this finite Hamiltonian."
                    if materialize_resolved
                    else "Pauli decomposition was skipped for dynamics-only audit; dense finite Hamiltonian is retained locally."
                ),
            ],
        ),
        grid=grid,
        link_operator=link_ops,
        nuclear_repulsion_energy=nuclear_repulsion,
        target_electrons=target,
        hamiltonian_matrix=hamiltonian_matrix,
        sector_matrices=sectors,
        gauss_law_matrices=gauss_law_matrices,
        ansatz_generator_ops=ansatz_generator_ops,
        sparse_bundle=None,
    )
