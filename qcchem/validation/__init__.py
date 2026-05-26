"""Validation harnesses for QCchem trust loops.

Validation modules are loaded lazily because several harnesses exercise runner
surfaces that also import CLI/reporting helpers during startup.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "PBCQMMMValidationCase",
    "default_pbc_qmmm_validation_cases",
    "run_pbc_qmmm_validation",
    "QMMMValidationCase",
    "default_qmmm_validation_cases",
    "run_qmmm_embedding_validation",
]


def __getattr__(name: str) -> Any:
    if name in {
        "QMMMValidationCase",
        "default_qmmm_validation_cases",
        "run_qmmm_embedding_validation",
    }:
        from . import qmmm_embedding

        return getattr(qmmm_embedding, name)
    if name in {
        "PBCQMMMValidationCase",
        "default_pbc_qmmm_validation_cases",
        "run_pbc_qmmm_validation",
    }:
        from . import pbc_qmmm

        return getattr(pbc_qmmm, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
