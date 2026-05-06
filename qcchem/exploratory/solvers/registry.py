"""Registry for exploratory solver skeletons."""

from __future__ import annotations

import inspect
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
    "lr_ace": {
        "loader": "qcchem.exploratory.solvers.lr_ace:build_solver",
        "class_name": "LRACESolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "LR-ACE is a QCchem-native low-rank-factor-informed solver prototype.",
            "Current LR-ACE evidence is local benchmark evidence, not a publication-validated algorithm.",
        ],
    },
    "lattice_qed_givqe": {
        "loader": "qcchem.exploratory.solvers.lattice_qed_givqe:build_solver",
        "class_name": "LatticeQEDGIVQESolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Gauge-invariant VQE is validated only against finite-cutoff lattice-QED audit checks.",
            "Continuum chemistry accuracy is outside the current lattice_qed_givqe validation scope.",
        ],
    },
    "lattice_qed_sparse_exact": {
        "loader": "qcchem.exploratory.solvers.lattice_qed_sparse_exact:build_solver",
        "class_name": "LatticeQEDSparseExactSolver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Sparse exact diagonalization is exact only for the configured finite lattice-QED Hamiltonian.",
            "Projected physical-sector results are finite-cutoff Gauss-law audits, not continuum chemistry claims.",
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


def build_exploratory_solver(
    kind: str,
    spec,
    backend,
    seed,
    problem_summary=None,
    mapper=None,
    qft_context=None,
):
    """Build the requested exploratory solver skeleton."""
    normalized = kind.strip().lower()
    metadata = EXPLORATORY_SOLVERS[normalized]
    module_path, attr_name = metadata["loader"].split(":")
    module = import_module(module_path)
    builder = getattr(module, attr_name)
    kwargs = {
        "spec": spec,
        "backend": backend,
        "seed": seed,
        "problem_summary": problem_summary,
        "mapper": mapper,
    }
    parameters = inspect.signature(builder).parameters
    accepts_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    if accepts_kwargs or "qft_context" in parameters:
        kwargs["qft_context"] = qft_context
    return builder(**kwargs)
