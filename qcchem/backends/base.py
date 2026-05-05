"""Abstract backend adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


@dataclass(slots=True)
class BackendEstimate:
    """One expectation-value estimate returned by a backend."""

    value: float
    reported_std: float
    metadata: dict[str, object] = field(default_factory=dict)
    seed: int | None = None
    shots: int | None = None


class BackendAdapter(ABC):
    """Abstract execution backend used by QCchem solvers."""

    backend_kind: str = "unknown"

    @abstractmethod
    def evaluate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> BackendEstimate:
        """Estimate the expectation value of an operator once."""

    def estimate_expectation(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> float:
        """Return only the estimated expectation value."""
        return self.evaluate(circuit, operator, parameter_values).value

    def sample_repeated(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> list[BackendEstimate]:
        """Run repeated evaluations when the backend supports stochastic sampling."""
        return [self.evaluate(circuit, operator, parameter_values)]
