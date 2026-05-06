"""Sparse physical-sector exact solver for finite lattice-QED Hamiltonians."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.sparse.linalg import eigsh

from qcchem.qft.lattice_qed import LatticeQEDContext
from qcchem.solvers.base import BaseSolver, SolverOutcome


class LatticeQEDSparseExactSolver(BaseSolver):
    """Exact diagonalization over the configured sparse lattice-QED engine."""

    def __init__(
        self,
        *,
        spec,
        backend=None,
        seed: int | None = None,
        qft_context: LatticeQEDContext | None = None,
        problem_summary: object | None = None,
        mapper: object | None = None,
    ) -> None:
        if qft_context is None or qft_context.sparse_bundle is None:
            raise ValueError("lattice_qed_sparse_exact requires a sparse lattice-QED context.")
        self.spec = spec
        self.qft_context = qft_context
        self.problem_summary = problem_summary
        self.mapper = mapper

    def _matrix(self):
        bundle = self.qft_context.sparse_bundle
        if bundle is None:
            raise ValueError("lattice_qed_sparse_exact requires sparse operators.")
        if bundle.projected_hamiltonian is not None:
            return bundle.projected_hamiltonian, "physical_sector"
        return bundle.full_hamiltonian, "full_hilbert_space"

    def solve(self, operator) -> SolverOutcome:
        matrix, evolution_space = self._matrix()
        dimension = int(matrix.shape[0])
        if dimension <= 8:
            dense = matrix.toarray()
            values, vectors = np.linalg.eigh(dense)
            order = np.argsort(np.real(values))
            ground_energy = float(np.real(values[order[0]]))
            residual = float(np.linalg.norm(dense @ vectors[:, order[0]] - ground_energy * vectors[:, order[0]]))
        else:
            values, vectors = eigsh(matrix, k=1, which="SA")
            ground_energy = float(np.real(values[0]))
            residual = float(np.linalg.norm(matrix @ vectors[:, 0] - ground_energy * vectors[:, 0]))
        metadata: dict[str, Any] = {
            "ansatz_num_parameters": 0,
            "optimizer_message": "sparse physical-sector exact diagonalization",
            "module_origin": "exploratory",
            "capability_tier": "exploratory",
            "validation_scope": "lattice_qed_sparse_projected_exact",
            "scientific_risk_notes": [
                "Sparse exact energy is exact only for the configured finite lattice/cutoff Hamiltonian.",
                "Physical-sector projection is a finite-cutoff Gauss-law audit, not continuum chemistry accuracy.",
            ],
            "qft_sparse_exact": {
                "operator_representation": self.qft_context.summary.engine.get("actual_representation"),
                "evolution_space": evolution_space,
                "dimension": dimension,
                "projected_dimension": self.qft_context.summary.engine.get("projected_dimension"),
                "eigen_residual_norm": residual,
                "basis_hash": self.qft_context.summary.physical_sector.get("basis_hash"),
            },
        }
        return SolverOutcome(
            total_energy=ground_energy,
            converged=True,
            iterations=1,
            evaluations=1,
            metadata=metadata,
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None, qft_context=None) -> BaseSolver:
    return LatticeQEDSparseExactSolver(
        spec=spec,
        backend=backend,
        seed=seed,
        qft_context=qft_context,
        problem_summary=problem_summary,
        mapper=mapper,
    )
