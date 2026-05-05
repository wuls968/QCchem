"""Base solver definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from qiskit.quantum_info import SparsePauliOp


@dataclass(slots=True)
class SolverOutcome:
    """Internal solver result."""

    total_energy: float
    converged: bool
    iterations: int
    evaluations: int
    optimal_parameters: list[float] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class BaseSolver(ABC):
    """Abstract base solver."""

    @abstractmethod
    def solve(self, operator: SparsePauliOp) -> SolverOutcome:
        """Solve the provided qubit Hamiltonian."""
