"""Low-rank compression audits and execution helpers for electronic Hamiltonians."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.operators.symmetric_two_body import unfold

from qcchem.core import CompressionResultSummary, CompressionSpec, MappingSummary


@dataclass(slots=True)
class _FactorizationAudit:
    reconstructed_matrix: np.ndarray
    primary_rank: int
    secondary_rank: int | None
    reconstruction_error_frobenius: float
    verification_status: str
    notes: list[str]


@dataclass(slots=True)
class CompressionExecutionBundle:
    """Compressed Hamiltonian payload used by the execution workflow."""

    fermionic_hamiltonian: FermionicOp
    method: str
    threshold: float
    rank: int
    secondary_rank: int | None
    reconstruction_error: float | None
    notes: list[str]
    verification_status: str


def _extract_raw_integrals(problem) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, np.ndarray | None, np.ndarray | None] | None:
    ints = getattr(problem.hamiltonian, "electronic_integrals", None)
    if ints is None:
        return None
    h1_a = ints.alpha.get("+-")
    h2_aa = ints.alpha.get("++--")
    if h1_a is None or h2_aa is None:
        return None
    h1_b = ints.beta.get("+-") if ints.beta is not None else None
    h2_bb = ints.beta.get("++--") if ints.beta is not None else None
    h2_ba = ints.beta_alpha.get("++--") if ints.beta_alpha is not None else None
    return (
        np.asarray(h1_a, dtype=float),
        np.asarray(h2_aa, dtype=float),
        (np.asarray(h1_b, dtype=float) if h1_b is not None else None),
        (np.asarray(h2_bb, dtype=float) if h2_bb is not None else None),
        (np.asarray(h2_ba, dtype=float) if h2_ba is not None else None),
    )


def _pair_matrix(two_body_tensor: np.ndarray) -> np.ndarray:
    matrix = two_body_tensor.reshape((two_body_tensor.shape[0] * two_body_tensor.shape[1], -1))
    return 0.5 * (matrix + matrix.T)


def _matrix_to_tensor(matrix: np.ndarray, num_orbitals: int, threshold: float) -> np.ndarray:
    tensor = matrix.reshape((num_orbitals, num_orbitals, num_orbitals, num_orbitals))
    tensor[np.abs(tensor) < threshold] = 0.0
    return tensor


def _effective_max_rank(spec: CompressionSpec) -> int | None:
    """Return the execution rank cap after applying an adaptive rank schedule."""
    candidates: list[int] = []
    if spec.max_rank is not None:
        candidates.append(int(spec.max_rank))
    if spec.rank_schedule:
        candidates.extend(int(value) for value in spec.rank_schedule)
    return max(candidates) if candidates else None


def _modified_cholesky(matrix: np.ndarray, threshold: float, max_rank: int | None) -> _FactorizationAudit:
    diag = np.clip(np.diag(matrix).astype(float), a_min=0.0, a_max=None)
    vectors: list[np.ndarray] = []
    limit = max_rank if max_rank is not None else matrix.shape[0]
    while len(vectors) < limit:
        pivot = int(np.argmax(diag))
        delta = float(diag[pivot])
        if delta <= threshold:
            break
        if vectors:
            previous = np.vstack(vectors)
            correction = previous.T @ previous[:, pivot]
            new_vec = (matrix[:, pivot] - correction) / np.sqrt(delta)
        else:
            new_vec = matrix[:, pivot] / np.sqrt(delta)
        vectors.append(new_vec)
        diag = np.clip(diag - new_vec**2, a_min=0.0, a_max=None)
    factors = np.vstack(vectors) if vectors else np.zeros((0, matrix.shape[0]))
    reconstruction = factors.T @ factors
    error = float(np.linalg.norm(matrix - reconstruction))
    status = "validated" if error <= max(threshold * 10.0, 1.0e-8) else "exploratory"
    return _FactorizationAudit(
        reconstructed_matrix=reconstruction,
        primary_rank=int(factors.shape[0]),
        secondary_rank=None,
        reconstruction_error_frobenius=error,
        verification_status=status,
        notes=["Modified-Cholesky compression reconstructed the two-electron pair matrix for execution."],
    )


def _double_factorization(matrix: np.ndarray, threshold: float, max_rank: int | None) -> _FactorizationAudit:
    eigvals, eigvecs = np.linalg.eigh(matrix)
    keep = eigvals > threshold
    eigvals = eigvals[keep]
    eigvecs = eigvecs[:, keep]
    if max_rank is not None:
        eigvals = eigvals[-max_rank:]
        eigvecs = eigvecs[:, -max_rank:]
    if len(eigvals) == 0:
        return _FactorizationAudit(
            reconstructed_matrix=np.zeros_like(matrix),
            primary_rank=0,
            secondary_rank=0,
            reconstruction_error_frobenius=float(np.linalg.norm(matrix)),
            verification_status="exploratory",
            notes=["Double-factorization compression found no eigenmodes above threshold."],
        )
    reconstruction = eigvecs @ np.diag(eigvals) @ eigvecs.T
    factor_mats = [
        (np.sqrt(max(float(value), 0.0)) * eigvecs[:, index]).reshape(
            int(np.sqrt(matrix.shape[0])),
            int(np.sqrt(matrix.shape[0])),
        )
        for index, value in enumerate(eigvals)
    ]
    secondary_rank = 0
    for factor in factor_mats:
        sym_factor = 0.5 * (factor + factor.T)
        secondary_rank += int(np.count_nonzero(np.abs(np.linalg.eigvalsh(sym_factor)) > threshold))
    error = float(np.linalg.norm(matrix - reconstruction))
    return _FactorizationAudit(
        reconstructed_matrix=reconstruction,
        primary_rank=int(len(eigvals)),
        secondary_rank=secondary_rank,
        reconstruction_error_frobenius=error,
        verification_status="exploratory",
        notes=[
            "Double-factorization compression reconstructed the pair matrix from retained eigenmodes.",
            "Current QCchem path uses the reconstructed low-rank Hamiltonian in execution but still treats the method as exploratory.",
        ],
    )


def build_compressed_fermionic_hamiltonian(problem, spec: CompressionSpec) -> CompressionExecutionBundle | None:
    """Build a compressed fermionic Hamiltonian suitable for mapping and solving."""
    if not spec.enabled or not spec.execution_enabled:
        return None
    raw_integrals = _extract_raw_integrals(problem)
    if raw_integrals is None:
        return None
    h1_a, h2_aa, h1_b, h2_bb, h2_ba = raw_integrals
    if h2_aa.ndim != 4:
        h2_aa = np.asarray(unfold(h2_aa, validate=False), dtype=float)
    if h2_bb is not None and h2_bb.ndim != 4:
        h2_bb = np.asarray(unfold(h2_bb, validate=False), dtype=float)
    if h2_ba is not None and h2_ba.ndim != 4:
        h2_ba = np.asarray(unfold(h2_ba, validate=False), dtype=float)
    pair_matrix = _pair_matrix(h2_aa)
    effective_max_rank = _effective_max_rank(spec)
    method = spec.method.strip().lower()
    if method == "modified_cholesky":
        audit = _modified_cholesky(pair_matrix, spec.threshold, effective_max_rank)
    elif method == "double_factorization":
        audit = _double_factorization(pair_matrix, spec.threshold, effective_max_rank)
    else:
        raise ValueError(f"Unsupported compression method: {spec.method}")

    num_orbitals = h2_aa.shape[0]
    compressed_h2_aa = _matrix_to_tensor(audit.reconstructed_matrix.copy(), num_orbitals, spec.threshold)
    compressed_h2_bb = (
        _matrix_to_tensor(audit.reconstructed_matrix.copy(), num_orbitals, spec.threshold)
        if h2_bb is not None
        else None
    )
    compressed_h2_ba = (
        _matrix_to_tensor(audit.reconstructed_matrix.copy(), num_orbitals, spec.threshold)
        if h2_ba is not None
        else None
    )
    compressed_energy = ElectronicEnergy.from_raw_integrals(
        h1_a,
        compressed_h2_aa,
        h1_b,
        compressed_h2_bb,
        compressed_h2_ba,
        validate=False,
    )
    compressed_energy.constants = dict(problem.hamiltonian.constants)
    compressed_fermionic = compressed_energy.second_q_op()
    return CompressionExecutionBundle(
        fermionic_hamiltonian=compressed_fermionic,
        method=method,
        threshold=spec.threshold,
        rank=audit.primary_rank,
        secondary_rank=audit.secondary_rank,
        reconstruction_error=audit.reconstruction_error_frobenius,
        notes=audit.notes,
        verification_status=audit.verification_status,
    )


def build_compression_result(
    *,
    pre_mapping_summary: MappingSummary,
    spec: CompressionSpec,
    execution_bundle: CompressionExecutionBundle | None = None,
    post_mapping_summary: MappingSummary | None = None,
) -> CompressionResultSummary | None:
    """Build compression metadata for reporting and benchmarking."""
    if not spec.enabled:
        return None
    method = spec.method.strip().lower()
    rank = execution_bundle.rank if execution_bundle is not None else 0
    post_term_count = (
        post_mapping_summary.qubit_term_count
        if post_mapping_summary is not None
        else pre_mapping_summary.qubit_term_count
    )
    return CompressionResultSummary(
        enabled=True,
        method=method,
        threshold=spec.threshold,
        rank=rank,
        max_rank=_effective_max_rank(spec),
        apply_to_solver=spec.apply_to_solver,
        execution_enabled=spec.execution_enabled,
        original_num_qubits=pre_mapping_summary.num_qubits,
        original_fermionic_term_count=pre_mapping_summary.fermionic_term_count,
        original_qubit_term_count=pre_mapping_summary.qubit_term_count,
        compressed_term_count_estimate=post_term_count,
        pre_term_count=pre_mapping_summary.qubit_term_count,
        post_term_count=post_term_count,
        primary_rank=rank,
        secondary_rank=(execution_bundle.secondary_rank if execution_bundle is not None else None),
        reconstruction_error_frobenius=(execution_bundle.reconstruction_error if execution_bundle is not None else None),
        reconstruction_error=(execution_bundle.reconstruction_error if execution_bundle is not None else None),
        compressed_num_qubits=(post_mapping_summary.num_qubits if post_mapping_summary is not None else pre_mapping_summary.num_qubits),
        verification_status=(execution_bundle.verification_status if execution_bundle is not None else "exploratory"),
        notes=(execution_bundle.notes if execution_bundle is not None else ["Compression enabled but execution bundle was unavailable."]),
    )
