"""Statevector-based primitives V2 backend."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from qcchem.backends.base import BackendAdapter, BackendEstimate
from qcchem.circuit_utils import statevector_ready_circuit
from qcchem.core import BackendSpec


class StatevectorBackend(BackendAdapter):
    """Backend adapter powered by :class:`StatevectorEstimator`."""

    backend_kind = "statevector"

    def __init__(self, spec: BackendSpec) -> None:
        self.spec = spec

    def evaluate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> BackendEstimate:
        bound_circuit = statevector_ready_circuit(circuit, parameter_values)
        state = Statevector.from_instruction(bound_circuit)
        expectation = state.expectation_value(operator)
        return BackendEstimate(
            value=float(np.real(expectation)),
            reported_std=0.0,
            metadata={"precision": self.spec.precision},
            seed=self.spec.seed,
            shots=self.spec.shots,
        )
