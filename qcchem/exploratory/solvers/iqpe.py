"""Exploratory IQPE skeleton."""

from __future__ import annotations

from dataclasses import replace

from qcchem.solvers import build_solver as build_core_solver
from qcchem.solvers.base import BaseSolver, SolverOutcome


class ExploratoryIQPESolver(BaseSolver):
    """Exploratory IQPE skeleton delegating to exact diagonalization."""

    def __init__(self, delegate: BaseSolver) -> None:
        self._delegate = delegate

    def solve(self, operator) -> SolverOutcome:
        outcome = self._delegate.solve(operator)
        metadata = dict(outcome.metadata)
        metadata.update(
            {
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "iqpe skeleton",
                "scientific_risk_notes": [
                    "Current IQPE path delegates to exact diagonalization and does not validate phase-estimation behavior.",
                ],
                "delegated_execution": "exact",
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
    delegate_spec = replace(spec, kind="exact", experimental=False)
    delegate = build_core_solver(
        delegate_spec,
        backend=None,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
    return ExploratoryIQPESolver(delegate)
