"""Chemistry-side problem construction."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "ElectronicStructureContext",
    "ResolvedExternalPointCharges",
    "ResolvedEnvironmentInputs",
    "build_boundary_embedding_summary",
    "build_electronic_structure_context",
    "build_effective_hamiltonian_summary",
    "build_reduction_plan",
    "resolve_environment_inputs",
    "resolve_external_point_charges",
]

_EXPORTS = {
    "ElectronicStructureContext": ("qcchem.chem.problem_builder", "ElectronicStructureContext"),
    "ResolvedExternalPointCharges": ("qcchem.chem.external_charges", "ResolvedExternalPointCharges"),
    "ResolvedEnvironmentInputs": ("qcchem.chem.effective_hamiltonian", "ResolvedEnvironmentInputs"),
    "build_boundary_embedding_summary": (
        "qcchem.chem.effective_hamiltonian",
        "build_boundary_embedding_summary",
    ),
    "build_electronic_structure_context": (
        "qcchem.chem.problem_builder",
        "build_electronic_structure_context",
    ),
    "build_effective_hamiltonian_summary": (
        "qcchem.chem.effective_hamiltonian",
        "build_effective_hamiltonian_summary",
    ),
    "build_reduction_plan": ("qcchem.chem.reduction_planner", "build_reduction_plan"),
    "resolve_environment_inputs": ("qcchem.chem.effective_hamiltonian", "resolve_environment_inputs"),
    "resolve_external_point_charges": (
        "qcchem.chem.external_charges",
        "resolve_external_point_charges",
    ),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
