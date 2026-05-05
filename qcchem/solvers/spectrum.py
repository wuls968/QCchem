"""Exact-spectrum helpers shared by QCchem workflows."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse.linalg import eigsh


@dataclass(slots=True)
class ExactSpectrum:
    """Exact eigenspectrum slice for a qubit operator."""

    eigenvalues: list[float]
    eigenvectors: np.ndarray


def compute_exact_spectrum(operator, num_states: int) -> ExactSpectrum:
    """Compute the lowest exact eigenpairs of a qubit operator."""
    matrix = operator.to_matrix(sparse=True)
    dim = matrix.shape[0]
    target_states = max(1, min(num_states, dim))
    if dim <= 8:
        dense = np.asarray(matrix.todense(), dtype=complex)
        eigenvalues, eigenvectors = np.linalg.eigh(dense)
        order = np.argsort(np.real(eigenvalues))
        eigenvalues = np.real(eigenvalues[order][:target_states])
        eigenvectors = np.asarray(eigenvectors[:, order[:target_states]], dtype=complex)
        return ExactSpectrum(
            eigenvalues=[float(value) for value in eigenvalues],
            eigenvectors=eigenvectors,
        )

    eigenvalues, eigenvectors = eigsh(matrix, k=target_states, which="SA")
    order = np.argsort(np.real(eigenvalues))
    sorted_values = np.real(eigenvalues[order])
    sorted_vectors = np.asarray(eigenvectors[:, order], dtype=complex)
    return ExactSpectrum(
        eigenvalues=[float(value) for value in sorted_values],
        eigenvectors=sorted_vectors,
    )
