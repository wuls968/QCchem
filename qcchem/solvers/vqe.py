"""Variational ground-state solver using primitives V2."""

from __future__ import annotations

import warnings

import numpy as np
from qiskit.circuit.library import n_local
from qiskit_nature.second_q.circuit.library import HartreeFock, PUCCD, PUCCSD, SUCCD, UCCSD
from scipy.sparse import SparseEfficiencyWarning
from scipy.optimize import minimize

from qcchem.backends import BackendAdapter
from qcchem.core import ProblemSummary, SolverSpec
from qcchem.solvers.base import BaseSolver, SolverOutcome
from qcchem.solvers.exact import ExactDiagonalizationSolver


class VQESolver(BaseSolver):
    """A thin QCchem-owned VQE implementation."""

    def __init__(
        self,
        spec: SolverSpec,
        backend: BackendAdapter,
        seed: int,
        problem_summary: ProblemSummary | None = None,
        mapper: object | None = None,
    ) -> None:
        self.spec = spec
        self.backend = backend
        self.rng = np.random.default_rng(seed)
        self.problem_summary = problem_summary
        self.mapper = mapper

    def _build_ansatz(self, num_qubits: int):
        kind = self.spec.ansatz.kind.strip().lower()
        chemistry_ansatzes = {
            "uccsd": UCCSD,
            "puccd": PUCCD,
            "puccsd": PUCCSD,
            "succd": SUCCD,
        }
        if kind in chemistry_ansatzes:
            if self.problem_summary is None or self.mapper is None:
                raise ValueError(f"{self.spec.ansatz.kind} ansatz requires problem summary and qubit mapper context.")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SparseEfficiencyWarning)
                initial_state = HartreeFock(
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                )
                return chemistry_ansatzes[kind](
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                    reps=self.spec.ansatz.reps,
                    initial_state=initial_state,
                )
        return n_local(
            num_qubits,
            rotation_blocks=self.spec.ansatz.rotation_blocks,
            entanglement_blocks=self.spec.ansatz.entanglement_blocks,
            entanglement=self.spec.ansatz.entanglement,
            reps=self.spec.ansatz.reps,
            skip_final_rotation_layer=self.spec.ansatz.skip_final_rotation_layer,
        )

    def _initial_point(self, num_parameters: int) -> np.ndarray:
        if isinstance(self.spec.initial_point, list):
            return np.asarray(self.spec.initial_point, dtype=float)
        strategy = str(self.spec.initial_point).strip().lower()
        if strategy == "zeros":
            return np.zeros(num_parameters, dtype=float)
        if strategy == "random":
            return self.rng.uniform(-0.1, 0.1, size=num_parameters)
        raise ValueError(f"Unsupported initial point strategy: {self.spec.initial_point}")

    def solve(self, operator) -> SolverOutcome:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SparseEfficiencyWarning)
            ansatz = self._build_ansatz(operator.num_qubits)
            initial_point = self._initial_point(ansatz.num_parameters)
            evaluations = 0

            def objective(point: np.ndarray) -> float:
                nonlocal evaluations
                evaluations += 1
                return self.backend.estimate_expectation(ansatz, operator, point)

            result = minimize(
                objective,
                x0=initial_point,
                method=self.spec.optimizer.kind,
                tol=self.spec.optimizer.tol,
                options={"maxiter": self.spec.optimizer.maxiter},
            )
        return SolverOutcome(
            total_energy=float(result.fun),
            converged=bool(result.success),
            iterations=int(getattr(result, "nit", evaluations)),
            evaluations=evaluations,
            optimal_parameters=[float(value) for value in np.asarray(result.x)],
            metadata={
                "ansatz_circuit": ansatz,
                "ansatz_num_parameters": ansatz.num_parameters,
                "optimizer_message": str(result.message),
            },
        )


def build_solver(
    spec: SolverSpec,
    backend: BackendAdapter | None,
    seed: int,
    problem_summary: ProblemSummary | None = None,
    mapper: object | None = None,
) -> BaseSolver:
    """Build the solver declared by the config."""
    normalized = spec.kind.strip().lower()
    if normalized == "vqe":
        if backend is None:
            raise ValueError("VQE requires an execution backend.")
        return VQESolver(spec, backend, seed, problem_summary=problem_summary, mapper=mapper)
    if normalized in {"exact", "reference"}:
        return ExactDiagonalizationSolver()
    raise ValueError(f"Unsupported solver kind: {spec.kind}")
