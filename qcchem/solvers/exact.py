"""Reference exact diagonalization solver."""

from __future__ import annotations

from qcchem.solvers.base import BaseSolver, SolverOutcome
from qcchem.solvers.spectrum import compute_exact_spectrum


class ExactDiagonalizationSolver(BaseSolver):
    """Compute the exact ground-state energy by diagonalization."""

    def solve(self, operator) -> SolverOutcome:
        spectrum = compute_exact_spectrum(operator, num_states=1)
        energy = float(spectrum.eigenvalues[0])
        return SolverOutcome(
            total_energy=energy,
            converged=True,
            iterations=1,
            evaluations=1,
            metadata={"kind": "exact", "ansatz_num_parameters": 0, "optimizer_message": "exact diagonalization"},
        )
