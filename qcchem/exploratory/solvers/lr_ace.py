"""LR-ACE: Low-Rank Adaptive Chemistry Eigensolver.

LR-ACE is an exploratory QCchem-native ansatz builder. It treats the mapped,
optionally low-rank-compressed Hamiltonian as the source of compact mixing
generators instead of starting from a full UCC excitation pool.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.circuit.library import HartreeFock
from scipy.optimize import minimize
from scipy.sparse import SparseEfficiencyWarning

from qcchem.backends import BackendAdapter
from qcchem.core import ProblemSummary
from qcchem.solvers.base import BaseSolver, SolverOutcome


@dataclass(slots=True)
class _LRACEGenerator:
    pauli: str
    source_pauli: str
    source_weight: float
    coefficient_real: float
    coefficient_imag: float


def _real_mixing_companion(pauli_label: str) -> str | None:
    """Turn an X/Y Hamiltonian factor into a real-amplitude mixing generator."""
    chars = list(pauli_label)
    for index, char in enumerate(chars):
        if char == "X":
            chars[index] = "Y"
            return "".join(chars)
        if char == "Y":
            chars[index] = "X"
            return "".join(chars)
    return None


def build_low_rank_generator_plan(
    operator: SparsePauliOp,
    *,
    max_generators: int,
    coefficient_threshold: float = 1.0e-12,
) -> dict[str, Any]:
    """Build a deterministic compact generator plan from dominant Hamiltonian factors."""
    source_terms: list[dict[str, Any]] = []
    candidates: list[_LRACEGenerator] = []
    seen: set[str] = set()
    for pauli, coeff in zip(operator.paulis, operator.coeffs):
        label = pauli.to_label()
        weight = float(abs(coeff))
        if weight <= coefficient_threshold or not any(char in label for char in "XY"):
            continue
        source_terms.append(
            {
                "pauli": label,
                "weight": weight,
                "coefficient_real": float(np.real(coeff)),
                "coefficient_imag": float(np.imag(coeff)),
            }
        )
    source_terms.sort(key=lambda item: (-float(item["weight"]), str(item["pauli"])))
    for item in source_terms:
        generator = _real_mixing_companion(str(item["pauli"]))
        if generator is None or generator in seen:
            continue
        seen.add(generator)
        candidates.append(
            _LRACEGenerator(
                pauli=generator,
                source_pauli=str(item["pauli"]),
                source_weight=float(item["weight"]),
                coefficient_real=float(item["coefficient_real"]),
                coefficient_imag=float(item["coefficient_imag"]),
            )
        )
        if len(candidates) >= max_generators:
            break
    return {
        "algorithm_name": "LR-ACE",
        "low_rank_aware": True,
        "selection_rule": "dominant_non_diagonal_hamiltonian_factors_with_real_mixing_companions",
        "source_terms": source_terms,
        "selected_generators": [
            {
                "pauli": item.pauli,
                "source_pauli": item.source_pauli,
                "source_weight": item.source_weight,
                "coefficient_real": item.coefficient_real,
                "coefficient_imag": item.coefficient_imag,
            }
            for item in candidates
        ],
        "selected_factor_count": len(candidates),
    }


class LRACESolver(BaseSolver):
    """Exploratory low-rank-factor-informed variational solver."""

    def __init__(
        self,
        *,
        spec,
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

    def _initial_state(self, num_qubits: int) -> QuantumCircuit:
        circuit = QuantumCircuit(num_qubits)
        if self.problem_summary is None or self.mapper is None:
            return circuit
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SparseEfficiencyWarning)
            try:
                hartree_fock = HartreeFock(
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                )
            except Exception:
                return circuit
        circuit.compose(hartree_fock, inplace=True)
        return circuit

    def _build_ansatz(self, operator: SparsePauliOp) -> tuple[QuantumCircuit, dict[str, Any]]:
        max_generators = max(int(getattr(self.spec.ansatz, "reps", 1)), 1)
        plan = build_low_rank_generator_plan(operator, max_generators=max_generators)
        circuit = self._initial_state(operator.num_qubits)
        parameters: list[Parameter] = []
        for index, generator in enumerate(plan["selected_generators"]):
            parameter = Parameter(f"theta_lr_ace_{index}")
            parameters.append(parameter)
            circuit.append(
                PauliEvolutionGate(
                    SparsePauliOp.from_list([(str(generator["pauli"]), 1.0)]),
                    time=parameter,
                ),
                range(operator.num_qubits),
            )
        plan["ansatz_parameter_count"] = len(parameters)
        return circuit, plan

    def _initial_point(self, num_parameters: int) -> np.ndarray:
        if isinstance(self.spec.initial_point, list):
            values = np.asarray(self.spec.initial_point, dtype=float)
            if len(values) != num_parameters:
                raise ValueError(
                    f"LR-ACE initial_point length {len(values)} does not match parameter count {num_parameters}."
                )
            return values
        strategy = str(self.spec.initial_point).strip().lower()
        if strategy == "zeros":
            return np.zeros(num_parameters, dtype=float)
        if strategy == "random":
            return self.rng.uniform(-0.05, 0.05, size=num_parameters)
        raise ValueError(f"Unsupported LR-ACE initial point strategy: {self.spec.initial_point}")

    def solve(self, operator: SparsePauliOp) -> SolverOutcome:
        ansatz, plan = self._build_ansatz(operator)
        initial_point = self._initial_point(ansatz.num_parameters)
        evaluations = 0

        def objective(point: np.ndarray) -> float:
            nonlocal evaluations
            evaluations += 1
            return self.backend.estimate_expectation(ansatz, operator, point)

        if ansatz.num_parameters:
            result = minimize(
                objective,
                x0=initial_point,
                method=self.spec.optimizer.kind,
                tol=self.spec.optimizer.tol,
                options={"maxiter": self.spec.optimizer.maxiter},
            )
            energy = float(result.fun)
            optimal = [float(value) for value in np.asarray(result.x)]
            converged = bool(result.success)
            message = str(result.message)
            iterations = int(getattr(result, "nit", evaluations))
        else:
            energy = float(objective(np.asarray([], dtype=float)))
            optimal = []
            converged = True
            message = "LR-ACE found no non-diagonal low-rank factors; evaluated reference state."
            iterations = 1

        plan["optimized_parameters"] = optimal
        return SolverOutcome(
            total_energy=energy,
            converged=converged,
            iterations=iterations,
            evaluations=evaluations,
            optimal_parameters=optimal,
            metadata={
                "ansatz_circuit": ansatz,
                "ansatz_num_parameters": ansatz.num_parameters,
                "optimizer_message": message,
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "lr_ace local exact-baseline gate",
                "scientific_risk_notes": [
                    "LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.",
                    "Dominant low-rank factor selection is heuristic and not yet publication-validated.",
                ],
                "lr_ace": plan,
            },
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None) -> BaseSolver:
    if backend is None:
        raise ValueError("LR-ACE requires an execution backend.")
    return LRACESolver(
        spec=spec,
        backend=backend,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
