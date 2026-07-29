"""TC-kicked QSCI exploratory workflow utilities."""

from __future__ import annotations


def run_tc_qsci(*args, **kwargs):
    """Lazy public entrypoint for the TC-QSCI workflow."""
    from .workflow import run_tc_qsci as _run_tc_qsci

    return _run_tc_qsci(*args, **kwargs)

__all__ = ["run_tc_qsci"]
