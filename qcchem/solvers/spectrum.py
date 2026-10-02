"""Resource-bounded exact spectra with physical molecular sectors."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh

from qcchem.solvers.sector import MolecularSector


@dataclass(slots=True)
class ExactSpectrum:
    """Eigenpairs in the original mapped qubit space."""

    eigenvalues: list[float]
    eigenvectors: np.ndarray
    sector: dict[str, object] = field(default_factory=dict)


def _guard_dense(dim: int, memory_limit_mb: int) -> None:
    # Matrix, eigenspace, projections, and LAPACK work arrays coexist.
    estimated = 6 * dim * dim * np.dtype(np.complex128).itemsize
    if estimated > memory_limit_mb * 1024**2:
        raise ValueError(
            f"Exact dense diagonalization needs approximately {estimated / 1024**2:.1f} MiB; "
            f"limit={memory_limit_mb} MiB. Reduce the active space or requested spectrum."
        )


def _constraint_matrix(operator, qubits: int):
    matrix = operator.to_matrix(sparse=True).tocsr()
    extra = qubits - operator.num_qubits
    if extra < 0:
        raise ValueError("Molecular constraints have more qubits than the Hamiltonian.")
    if extra:
        # The cavity builder tensors electrons on the left of photon registers.
        matrix = sparse.kron(matrix, sparse.eye(2**extra, format="csr"), format="csr")
    return matrix


def compute_exact_spectrum(
    operator, num_states: int, *, sector: MolecularSector | None = None,
    max_qubits: int = 16, memory_limit_mb: int = 512,
) -> ExactSpectrum:
    """Compute bounded eigenpairs in a specified electron/spin sector.

    Eigenvectors retain the original qubit dimension for property evaluation.
    Reduced mappings additionally retain their selected Z2 sector.
    """
    if isinstance(num_states, bool) or not isinstance(num_states, int) or num_states < 1:
        raise ValueError("num_states must be a positive integer.")
    if max_qubits < 0 or memory_limit_mb < 1:
        raise ValueError("Exact resource limits require non-negative qubits and positive memory.")
    if operator.num_qubits > max_qubits:
        raise ValueError(
            f"Exact diagonalization requires {operator.num_qubits} qubits; limit={max_qubits}. "
            "Reduce the active space or use a variational solver."
        )
    dim = 2**operator.num_qubits
    # Bound sparse Pauli construction before allocating potentially huge CSR arrays.
    if dim * len(operator) * 32 > memory_limit_mb * 1024**2:
        raise ValueError("Exact sparse matrix construction exceeds the configured memory limit.")
    matrix = operator.to_matrix(sparse=True).tocsr()
    indices = np.arange(dim)
    spin_basis = None
    metadata: dict[str, object] = {"kind": "full_hilbert_space"}
    if sector is not None:
        metadata = sector.metadata()
        for number_op, target in zip(sector.number_operators, sector.num_particles):
            number = _constraint_matrix(number_op, operator.num_qubits)
            diagonal = number.diagonal()
            off_diagonal = number - sparse.diags(diagonal, format="csr")
            if off_diagonal.nnz and np.max(np.abs(off_diagonal.data)) > 1e-9:
                raise ValueError("Particle projection requires diagonal mapped number operators.")
            indices = indices[np.isclose(diagonal[indices], target, atol=1e-8, rtol=0)]
        if not len(indices):
            raise ValueError("The requested particle sector is empty in this mapping.")
        spin = _constraint_matrix(sector.spin_squared, operator.num_qubits)[indices][:, indices]
        target_spin = float(metadata["spin_squared"])
        diagonal = spin.diagonal()
        off_diagonal = spin - sparse.diags(diagonal, format="csr")
        if not off_diagonal.nnz or np.max(np.abs(off_diagonal.data)) < 1e-9:
            indices = indices[np.isclose(diagonal, target_spin, atol=1e-8, rtol=0)]
        else:
            _guard_dense(len(indices), memory_limit_mb)
            spin_values, spin_vectors = np.linalg.eigh(spin.toarray())
            spin_basis = spin_vectors[:, np.isclose(spin_values, target_spin, atol=1e-8, rtol=0)]
        if not len(indices) or (spin_basis is not None and not spin_basis.shape[1]):
            raise ValueError("The requested total-spin sector is empty in this mapping.")
        matrix = matrix[indices][:, indices]
        if spin_basis is not None:
            matrix = sparse.csr_matrix(spin_basis.conj().T @ (matrix @ spin_basis))
    sector_dim = matrix.shape[0]
    metadata["dimension"] = sector_dim
    target_states = min(num_states, sector_dim)
    # Complex Hermitian eigsh dispatches to eigs, which requires k < N - 1.
    if sector_dim <= 8 or target_states >= sector_dim - 1:
        _guard_dense(sector_dim, memory_limit_mb)
        eigenvalues, eigenvectors = np.linalg.eigh(matrix.toarray())
        eigenvalues, eigenvectors = eigenvalues[:target_states], eigenvectors[:, :target_states]
    else:
        if dim * max(2 * target_states + 1, 20) * 16 > memory_limit_mb * 1024**2:
            raise ValueError("Exact eigensolver work vectors exceed the configured memory limit.")
        eigenvalues, eigenvectors = eigsh(matrix, k=target_states, which="SA")
    order = np.argsort(np.real(eigenvalues))
    vectors = eigenvectors[:, order]
    if sector is not None:
        if spin_basis is not None:
            vectors = spin_basis @ vectors
        if dim * target_states * 16 > memory_limit_mb * 1024**2:
            raise ValueError("Exact output eigenvectors exceed the configured memory limit.")
        lifted = np.zeros((dim, target_states), dtype=complex)
        lifted[indices] = vectors
        vectors = lifted
    return ExactSpectrum(
        eigenvalues=[float(value) for value in np.real(eigenvalues[order])],
        eigenvectors=np.asfortranarray(vectors, dtype=complex), sector=metadata,
    )
