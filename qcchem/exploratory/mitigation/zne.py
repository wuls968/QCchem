"""Exploratory ZNE metadata and placeholder hooks."""

from __future__ import annotations

ZNE_EXPLORATORY_METADATA = {
    "module_origin": "exploratory",
    "capability_tier": "exploratory",
    "validation_scope": "zero-noise extrapolation skeleton",
    "scientific_risk_notes": [
        "Noise-scaling and extrapolation behavior remain exploratory in QCchem.",
    ],
}


def build_zne_placeholder() -> dict[str, object]:
    """Return persisted exploratory metadata for ZNE."""
    return dict(ZNE_EXPLORATORY_METADATA)
