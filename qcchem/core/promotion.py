"""Promotion gate constants for exploratory QCchem artifacts."""

from __future__ import annotations


PROMOTION_SCHEMA_VERSION = "qcchem.promotion_gate.v0.1-alpha"

QFT_REQUIRED_STUDIES = [
    "finite cutoff audit",
    "Gauss law / physical sector audit",
    "grid/cutoff convergence study",
    "comparison against molecular exact/reference where meaningful",
]

LR_ACE_REQUIRED_STUDIES = [
    "exact baseline",
    "multiple molecules",
    "active-space coverage",
    "compression-vs-uncompressed comparison",
    "ansatz limitation analysis",
    "failure cases",
]

TC_QSCI_REQUIRED_STUDIES = [
    "determinant selection audit",
    "symmetry sector audit",
    "physical Hamiltonian final diagonalization",
    "CAST provenance",
    "ablation against non-TC selection",
    "exact baseline where feasible",
]
