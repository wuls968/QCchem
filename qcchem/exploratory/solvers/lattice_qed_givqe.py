"""Gauge-invariant VQE path for finite lattice-QED Hamiltonians."""

from __future__ import annotations

from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import HamiltonianGate
from qiskit.quantum_info import SparsePauliOp, Statevector
from scipy.optimize import minimize

from qcchem.backends import BackendAdapter
from qcchem.qft.lattice_qed import LatticeQEDContext
from qcchem.solvers.base import BaseSolver, SolverOutcome


class LatticeQEDGIVQESolver(BaseSolver):
    """Exploratory Gauss-law-preserving variational solver for lattice QED."""

    def __init__(
        self,
        *,
        spec,
        backend: BackendAdapter,
        seed: int,
        qft_context: LatticeQEDContext | None = None,
        problem_summary: object | None = None,
        mapper: object | None = None,
    ) -> None:
        if qft_context is None:
            raise ValueError("lattice_qed_givqe requires a lattice-QED context.")
        self.spec = spec
        self.backend = backend
        self.rng = np.random.default_rng(seed)
        self.qft_context = qft_context
        self.problem_summary = problem_summary
        self.mapper = mapper

    def _initial_state(self, num_qubits: int) -> QuantumCircuit:
        circuit = QuantumCircuit(num_qubits)
        reference = self.qft_context.summary.physical_sector.get("reference_basis_index")
        if reference is None:
            return circuit
        for qubit in range(num_qubits):
            if (int(reference) >> qubit) & 1:
                circuit.x(qubit)
        return circuit

    def _build_ansatz(self, operator: SparsePauliOp) -> tuple[QuantumCircuit, dict[str, Any]]:
        circuit = self._initial_state(operator.num_qubits)
        generator_ops = list(self.qft_context.ansatz_generator_ops)
        selected_metadata = list(
            self.qft_context.summary.gauge_invariant_ansatz.get("selected_generators", [])
        )
        reps = max(int(getattr(self.spec.ansatz, "reps", 1)), 1)
        sequence: list[dict[str, Any]] = []
        for rep in range(reps):
            for generator_index, generator in enumerate(generator_ops):
                parameter = Parameter(f"theta_givqe_{rep}_{generator_index}")
                source = (
                    dict(selected_metadata[generator_index])
                    if generator_index < len(selected_metadata)
                    else {}
                )
                sector = str(source.get("sector", ""))
                matrix = self.qft_context.sector_matrices.get(sector)
                if matrix is None:
                    matrix = generator.to_matrix()
                matrix = 0.5 * (np.asarray(matrix, dtype=complex) + np.asarray(matrix, dtype=complex).conj().T)
                circuit.append(HamiltonianGate(matrix, time=parameter), range(operator.num_qubits))
                sequence.append(
                    {
                        "rep": int(rep),
                        "generator_index": int(generator_index),
                        "sector": sector,
                        "pauli_term_count": int(len(generator)),
                        "evolution_gate": "HamiltonianGate",
                        "parameter": str(parameter),
                    }
                )

        plan = dict(self.qft_context.summary.gauge_invariant_ansatz)
        plan.update(
            {
                "algorithm_name": "lattice_qed_givqe",
                "ansatz_kind": "gauss_law_preserving",
                "reps": reps,
                "generator_sequence": sequence,
                "ansatz_parameter_count": circuit.num_parameters,
                "physical_sector_reference": dict(self.qft_context.summary.physical_sector),
            }
        )
        return circuit, plan

    def _initial_point(self, num_parameters: int) -> np.ndarray:
        if isinstance(self.spec.initial_point, list):
            values = np.asarray(self.spec.initial_point, dtype=float)
            if len(values) != num_parameters:
                raise ValueError(
                    "lattice_qed_givqe initial_point length "
                    f"{len(values)} does not match parameter count {num_parameters}."
                )
            return values
        strategy = str(self.spec.initial_point).strip().lower()
        if strategy == "zeros":
            return np.zeros(num_parameters, dtype=float)
        if strategy == "random":
            return self.rng.uniform(-0.05, 0.05, size=num_parameters)
        raise ValueError(f"Unsupported lattice_qed_givqe initial point strategy: {self.spec.initial_point}")

    def _constraint_expectations(
        self,
        circuit: QuantumCircuit,
        parameter_values: list[float],
    ) -> dict[str, Any]:
        values = np.asarray(parameter_values, dtype=float)
        assignment = {parameter: value for parameter, value in zip(circuit.parameters, values)}
        bound = circuit.assign_parameters(assignment, inplace=False)
        state = np.asarray(Statevector.from_instruction(bound).data, dtype=complex)
        residuals: list[float] = []
        squared_residuals: list[float] = []
        for metadata, matrix in zip(
            self.qft_context.summary.gauss_law_generators,
            self.qft_context.gauss_law_matrices,
        ):
            target = float(metadata.get("target_charge", 0.0))
            shifted = matrix - target * np.eye(matrix.shape[0], dtype=complex)
            residual = np.vdot(state, shifted @ state)
            squared = np.vdot(state, shifted @ shifted @ state)
            residuals.append(float(np.real_if_close(residual)))
            squared_residuals.append(float(np.real_if_close(squared)))
        max_abs = float(max(abs(value) for value in residuals)) if residuals else 0.0
        violation = float(max(squared_residuals)) if squared_residuals else 0.0
        return {
            "available": True,
            "gauss_law_tolerance": float(
                self.qft_context.summary.constraints.get("gauss_law_tolerance", 1.0e-8)
            ),
            "gauss_law_residual_expectations": residuals,
            "gauss_law_squared_residual_expectations": squared_residuals,
            "max_abs_gauss_law_residual_expectation": max_abs,
            "gauss_law_violation_expectation": violation,
            "reference_basis_index": self.qft_context.summary.physical_sector.get(
                "reference_basis_index"
            ),
        }

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
            message = "No gauge-invariant generators selected; evaluated physical reference state."
            iterations = 1

        plan["optimized_parameters"] = optimal
        plan["constraint_expectations"] = self._constraint_expectations(ansatz, optimal)
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
                "validation_scope": "lattice_qed_gauge_invariant_vqe",
                "scientific_risk_notes": [
                    "lattice_qed_givqe preserves the audited finite-cutoff Gauss-law sector only within the configured truncation.",
                    "Gauge-invariant VQE evidence is local to this finite lattice Hamiltonian, not continuum chemistry.",
                ],
                "qft_givqe": plan,
            },
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None, qft_context=None) -> BaseSolver:
    if backend is None:
        raise ValueError("lattice_qed_givqe requires an execution backend.")
    return LatticeQEDGIVQESolver(
        spec=spec,
        backend=backend,
        seed=seed,
        qft_context=qft_context,
        problem_summary=problem_summary,
        mapper=mapper,
    )
