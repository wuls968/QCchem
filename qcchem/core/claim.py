"""Claim compiler helpers for Trust-First boundary language."""

from __future__ import annotations

import re


CLAIM_SCHEMA_VERSION = "qcchem.claim_compiler.v0.1-alpha"

OVERCLAIM_TERMS = (
    "validated",
    "publication-grade",
    "publication grade",
    "chemical accuracy",
    "chemically accurate",
    "hardware verified proves chemistry",
    "hardware_verified proves",
)


def claim_uses_overclaim_language(claim: str) -> bool:
    """Return whether a claim uses terms that require strict evidence."""
    lowered = claim.lower()
    return any(term in lowered for term in OVERCLAIM_TERMS) or bool(
        re.search(r"\bvalidat(?:ed|es|ion)\b", lowered)
    )


def conservative_safe_rewrite(claim: str, *, support_level: str) -> str:
    """Return a safer Trust-First rewrite for a claim."""
    lowered = claim.lower()
    if "hardware" in lowered or "runtime" in lowered or "hardware_verified" in lowered:
        return (
            "The artifact verifies runtime submission and retrieval, but the hardware-derived chemistry estimate "
            "remains exploratory until runtime chemical accuracy is met against the stated baseline."
        )
    if support_level == "supported":
        return claim
    if "lr-ace" in lowered or "lr_ace" in lowered or "qft" in lowered or "tc-qsci" in lowered or "tc_qsci" in lowered:
        return (
            "The artifact is reproducible exploratory algorithm evidence. Treat broader validated chemistry or "
            "publication-grade method claims as pending until the promotion gate records stronger baselines, "
            "ablation, and coverage."
        )
    return (
        "The current artifact set provides bounded evidence for the stated workflow, but the claim should remain "
        "conditional until the missing baseline, chemical accuracy, and trust-tier gaps are closed."
    )
