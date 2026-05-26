"""Compatibility wrapper for legacy exploratory LR-ACE imports."""

from qcchem.solvers.lr_ace import (  # noqa: F401
    LRACESolver,
    build_low_rank_generator_plan,
    build_solver,
)

__all__ = ["LRACESolver", "build_low_rank_generator_plan", "build_solver"]
