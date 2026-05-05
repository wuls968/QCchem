"""Statevector-based primitives V2 backend."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from qcchem.backends.base import BackendAdapter, BackendEstimate
from qcchem.core import BackendSpec


class StatevectorBackend(BackendAdapter):
    """Backend adapter powered by :class:`StatevectorEstimator`."""

    backend_kind = "statevector"

    def __init__(self, spec: BackendSpec) -> None:
        self.spec = spec
        self.estimator = StatevectorEstimator()

    def evaluate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> BackendEstimate:
        result = self.estimator.run(
            [(circuit, operator, [np.asarray(parameter_values, dtype=float)])],
            precision=self.spec.precision,
        ).result()
        return BackendEstimate(
            value=float(np.real(result[0].data.evs[0])),
            reported_std=float(np.real(result[0].data.stds[0])) if hasattr(result[0].data, "stds") else 0.0,
            metadata={"precision": self.spec.precision},
            seed=self.spec.seed,
            shots=self.spec.shots,
        )
