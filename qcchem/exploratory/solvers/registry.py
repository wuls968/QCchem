"""Registry for exploratory solver skeletons."""

from __future__ import annotations

from importlib import import_module
from typing import Any


EXPLORATORY_SOLVERS: dict[str, dict[str, Any]] = {
    "adapt_vqe": {
        "loader": "qcchem.exploratory.solvers.adapt_vqe:build_solver",
        "class_name": "ExploratoryADAPTVQESolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Adaptive excitation-pool behavior is not part of the validated QCchem path.",
        ],
    },
    "vqd": {
        "loader": "qcchem.exploratory.solvers.vqd:build_solver",
        "class_name": "ExploratoryVQDSolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Excited-state targeting remains exploratory and currently delegates to a ground-state variational path.",
        ],
    },
    "qse": {
        "loader": "qcchem.exploratory.solvers.qse:build_solver",
        "class_name": "ExploratoryQSESolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Subspace construction and matrix elements remain exploratory and are not validated chemistry benchmarks.",
        ],
    },
    "iqpe": {
        "loader": "qcchem.exploratory.solvers.iqpe:build_solver",
        "class_name": "ExploratoryIQPESolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Phase-estimation behavior remains exploratory in QCchem.",
        ],
    },
    "folded_spectrum": {
        "loader": "qcchem.exploratory.solvers.folded_spectrum:build_solver",
        "class_name": "ExploratoryFoldedSpectrumSolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Interior-state targeting remains exploratory in QCchem.",
        ],
    },
}


def get_exploratory_solver(kind: str):
    """Return the exploratory solver class and registry metadata."""
    normalized = kind.strip().lower()
    metadata = EXPLORATORY_SOLVERS[normalized]
    module_path, _ = metadata["loader"].split(":")
    module = import_module(module_path)
    return getattr(module, metadata["class_name"]), dict(metadata)


def build_exploratory_solver(kind: str, spec, backend, seed, problem_summary=None, mapper=None):
    """Build the requested exploratory solver skeleton."""
    normalized = kind.strip().lower()
    metadata = EXPLORATORY_SOLVERS[normalized]
    module_path, attr_name = metadata["loader"].split(":")
    module = import_module(module_path)
    builder = getattr(module, attr_name)
    return builder(
        spec=spec,
        backend=backend,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
