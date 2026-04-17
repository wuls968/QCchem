"""Exploratory CDR metadata and placeholder hooks."""

from __future__ import annotations

CDR_EXPLORATORY_METADATA = {
    "module_origin": "exploratory",
    "capability_tier": "exploratory",
    "validation_scope": "clifford-data-regression skeleton",
    "scientific_risk_notes": [
        "Training-circuit generation and regression behavior remain exploratory in QCchem.",
    ],
}


def build_cdr_placeholder() -> dict[str, object]:
    """Return persisted exploratory metadata for CDR."""
    return dict(CDR_EXPLORATORY_METADATA)
