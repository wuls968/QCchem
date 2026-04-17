"""Exploratory benchmark-suite definitions kept outside validated QCchem suites."""

from __future__ import annotations

EXPLORATORY_SUITES = {
    "spectroscopy_v1": {
        "scope": "exploratory",
        "description": "Exploratory spectroscopy cases retained outside the validated benchmark registry.",
        "default_status": "exploratory",
    },
    "strong_correlation_v1": {
        "scope": "exploratory",
        "description": "Exploratory strong-correlation stress cases retained outside the validated benchmark registry.",
        "default_status": "exploratory",
    },
    "resource_scaling_v1": {
        "scope": "exploratory",
        "description": "Exploratory scaling benchmarks that should not be mixed with validated chemistry baselines.",
        "default_status": "exploratory",
    },
}
