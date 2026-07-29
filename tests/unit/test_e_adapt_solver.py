from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

import numpy as np

from qcchem.backends import StatevectorBackend
from qcchem.core import BackendSpec, EADAPTSpec, OptimizerSpec, SolverSpec
from qcchem.exploratory.solvers.adapt_vqe import ExploratoryADAPTVQESolver
from qcchem.solvers.base import BaseSolver, SolverOutcome


class _IdentityDelegate(BaseSolver):
    def solve(self, operator: SparsePauliOp) -> SolverOutcome:
        circuit = QuantumCircuit(operator.num_qubits)
        return SolverOutcome(
            total_energy=0.0,
            converged=True,
            iterations=0,
            evaluations=1,
            optimal_parameters=[],
            metadata={
                "ansatz_circuit": circuit,
                "ansatz_num_parameters": 0,
                "evaluation_trajectory": [{"parameters": [], "energy": 0.0}],
                "optimizer_message": "identity delegate",
            },
        )


def test_e_adapt_solver_uses_selected_pauli_in_real_adaptive_ansatz() -> None:
    operator = SparsePauliOp.from_list([("Y", 1.0), ("X", 0.1)])
    spec = SolverSpec(
        kind="e_adapt_vqe",
        optimizer=OptimizerSpec(kind="COBYLA", maxiter=80),
        experimental=True,
        e_adapt=EADAPTSpec(
            gradient_threshold=1.0e-3,
            max_operators=1,
            finite_difference_step=1.0e-2,
        ),
    )
    backend = StatevectorBackend(BackendSpec(kind="statevector"))

    result = ExploratoryADAPTVQESolver(_IdentityDelegate(), spec, backend).solve(operator)

    payload = result.metadata["e_adapt_result"]
    selected = payload["selected_operators"]
    adaptive = payload["adaptive_optimization"]

    assert result.total_energy < -0.5
    assert selected[0]["pauli"] == "X"
    assert selected[0]["gradient_evaluation_status"] == "finite_difference"
    assert adaptive["energy_replaces_delegate"] is True
    assert adaptive["adaptive_improvement_status"] == "replaces_delegate"
    assert adaptive["optimization_signal_present"] is True
    assert adaptive["adaptive_energy"] == result.total_energy
    assert adaptive["delegate_improvement_to_replacement_threshold_ratio"] > 1.0
    assert adaptive["cumulative_selected_energy_lowering_hartree"] > 0.0
    assert adaptive["max_selected_energy_lowering_hartree"] > 0.0
    assert adaptive["final_cumulative_two_qubit_increment"] == 0
    assert adaptive["adaptive_evaluations_per_selected_operator"] > 0.0
    assert adaptive["ansatz_parameter_count"] == 1
    assert result.metadata["ansatz_circuit"].num_parameters == 1
    assert result.metadata["ansatz_num_parameters"] == 1
    assert len(result.optimal_parameters) == 1


def test_e_adapt_rejects_operator_when_adaptive_optimization_does_not_improve() -> None:
    operator = SparsePauliOp.from_list([("Y", 1.0), ("X", 0.1)])
    spec = SolverSpec(
        kind="e_adapt_vqe",
        optimizer=OptimizerSpec(kind="COBYLA", maxiter=5),
        experimental=True,
        e_adapt=EADAPTSpec(
            gradient_threshold=1.0e-3,
            max_operators=1,
            finite_difference_step=1.0e-2,
        ),
    )
    backend = StatevectorBackend(BackendSpec(kind="statevector"))
    solver = ExploratoryADAPTVQESolver(_IdentityDelegate(), spec, backend)

    def _no_improvement_optimizer(
        operator_arg,
        base_ansatz,
        selected,
        initial_base_values,
        initial_adaptive_values,
    ):
        return (
            0.0,
            np.asarray([0.0], dtype=float),
            QuantumCircuit(base_ansatz.num_qubits),
            0,
            1,
            [{"evaluation_index": 1, "parameters": [0.0], "energy": 0.0}],
            "forced no improvement",
        )

    solver._optimize_adaptive_ansatz = _no_improvement_optimizer  # type: ignore[method-assign]

    result = solver.solve(operator)

    payload = result.metadata["e_adapt_result"]
    adaptive = payload["adaptive_optimization"]
    rejected = payload["rejected_operators"]

    assert result.total_energy == 0.0
    assert payload["selected_operators"] == []
    assert adaptive["status"] == "no_operator_selected"
    assert adaptive["adaptive_improvement_status"] == "not_evaluated"
    assert adaptive["optimization_signal_present"] is False
    assert adaptive["cumulative_selected_energy_lowering_hartree"] == 0.0
    assert adaptive["adaptive_evaluations_per_selected_operator"] is None
    assert adaptive["no_improvement_rejection_count"] == 1
    assert adaptive["operator_acceptance_policy"] == (
        "optimized_energy_must_improve_current_energy"
    )
    no_improvement = [
        entry
        for entry in rejected
        if entry.get("reason") == "adaptive_optimization_no_improvement"
    ]
    assert len(no_improvement) == 1
    assert no_improvement[0]["selection_status"] == "rejected_after_optimization"
    assert no_improvement[0]["energy_lowering_hartree"] == 0.0
