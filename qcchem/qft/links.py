"""Finite compact-U(1) link operators for lattice-QED qubit encodings."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit.quantum_info import Operator, SparsePauliOp


@dataclass(slots=True)
class U1LinkOperators:
    """Binary-encoded finite electric-flux link operators."""

    electric_cutoff: int
    levels: list[int]
    physical_dimension: int
    encoded_dimension: int
    num_qubits: int
    electric_matrix: np.ndarray
    electric_squared_matrix: np.ndarray
    raising_matrix: np.ndarray
    lowering_matrix: np.ndarray
    padding_projector_matrix: np.ndarray
    electric_pauli: SparsePauliOp
    electric_squared_pauli: SparsePauliOp
    raising_pauli: SparsePauliOp
    lowering_pauli: SparsePauliOp
    padding_projector_pauli: SparsePauliOp


def _num_qubits_for_dimension(dimension: int) -> int:
    if dimension <= 1:
        return 1
    return int(np.ceil(np.log2(float(dimension))))


def matrix_to_sparse_pauli(matrix: np.ndarray, *, atol: float = 1.0e-12) -> SparsePauliOp:
    """Convert a dense qubit-space matrix into a simplified SparsePauliOp."""
    dimension = int(matrix.shape[0])
    num_qubits = _num_qubits_for_dimension(dimension)
    if dimension != 2**num_qubits:
        raise ValueError("matrix_to_sparse_pauli expects a binary-encoded qubit matrix.")
    if np.allclose(matrix, 0.0, atol=atol):
        return SparsePauliOp.from_list([("I" * num_qubits, 0.0)])
    return SparsePauliOp.from_operator(Operator(matrix), atol=atol).simplify(atol=atol)


def build_u1_link_operators(electric_cutoff: int) -> U1LinkOperators:
    """Build binary-encoded U(1) electric and shift operators for one link."""
    if electric_cutoff < 0:
        raise ValueError("electric_cutoff must be non-negative.")
    levels = list(range(-electric_cutoff, electric_cutoff + 1))
    physical_dimension = len(levels)
    num_qubits = _num_qubits_for_dimension(physical_dimension)
    encoded_dimension = 2**num_qubits

    electric = np.zeros((encoded_dimension, encoded_dimension), dtype=complex)
    raising = np.zeros_like(electric)
    padding = np.zeros_like(electric)
    for basis_index, level in enumerate(levels):
        electric[basis_index, basis_index] = float(level)
        if basis_index + 1 < physical_dimension:
            raising[basis_index + 1, basis_index] = 1.0
    for basis_index in range(physical_dimension, encoded_dimension):
        padding[basis_index, basis_index] = 1.0
    lowering = raising.conj().T
    electric_squared = electric @ electric

    return U1LinkOperators(
        electric_cutoff=electric_cutoff,
        levels=levels,
        physical_dimension=physical_dimension,
        encoded_dimension=encoded_dimension,
        num_qubits=num_qubits,
        electric_matrix=electric,
        electric_squared_matrix=electric_squared,
        raising_matrix=raising,
        lowering_matrix=lowering,
        padding_projector_matrix=padding,
        electric_pauli=matrix_to_sparse_pauli(electric),
        electric_squared_pauli=matrix_to_sparse_pauli(electric_squared),
        raising_pauli=matrix_to_sparse_pauli(raising),
        lowering_pauli=matrix_to_sparse_pauli(lowering),
        padding_projector_pauli=matrix_to_sparse_pauli(padding),
    )
