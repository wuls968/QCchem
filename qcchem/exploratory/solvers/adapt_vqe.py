"""Exploratory ADAPT-VQE skeleton."""

from __future__ import annotations

from dataclasses import replace

from qcchem.solvers import build_solver as build_core_solver
from qcchem.solvers.base import BaseSolver, SolverOutcome


class ExploratoryADAPTVQESolver(BaseSolver):
    """Exploratory ADAPT-VQE skeleton delegating to QCchem VQE."""

    def __init__(self, delegate: BaseSolver) -> None:
        self._delegate = delegate

    def solve(self, operator) -> SolverOutcome:
        outcome = self._delegate.solve(operator)
        metadata = dict(outcome.metadata)
        metadata.update(
            {
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "adapt_vqe skeleton",
                "scientific_risk_notes": [
                    "Current ADAPT-VQE path delegates to QCchem VQE and remains exploratory.",
                ],
                "delegated_execution": "vqe",
            }
        )
        return SolverOutcome(
            total_energy=outcome.total_energy,
            converged=outcome.converged,
            iterations=outcome.iterations,
            evaluations=outcome.evaluations,
            optimal_parameters=outcome.optimal_parameters,
            metadata=metadata,
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None) -> BaseSolver:
    delegate_spec = replace(spec, kind="vqe", experimental=False)
    delegate = build_core_solver(
        delegate_spec,
        backend=backend,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
    return ExploratoryADAPTVQESolver(delegate)
