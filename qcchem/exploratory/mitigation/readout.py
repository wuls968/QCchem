"""Exploratory readout-mitigation metadata and placeholder hooks."""

from __future__ import annotations

READOUT_EXPLORATORY_METADATA = {
    "module_origin": "exploratory",
    "capability_tier": "exploratory",
    "validation_scope": "general observable readout correction",
    "scientific_risk_notes": [
        "Current implementation is not validated for arbitrary non-diagonal observables.",
    ],
}


def build_readout_mitigation_placeholder() -> dict[str, object]:
    """Return persisted exploratory metadata for readout mitigation."""
    return dict(READOUT_EXPLORATORY_METADATA)
