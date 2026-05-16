"""Registry for QCchem field-model families."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qcchem.core import CavityQEDModelSummary, FieldModelSummary, QFTModelSummary


@dataclass(frozen=True, slots=True)
class FieldModelAdapter:
    """Static registry metadata for a field-model family."""

    model_kind: str
    registry_name: str
    capability_tier: str
    observables: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)


FIELD_MODEL_REGISTRY: dict[str, FieldModelAdapter] = {
    "lattice_qed": FieldModelAdapter(
        model_kind="lattice_qed",
        registry_name="finite_cutoff_lattice_qed",
        capability_tier="exploratory",
        observables=[
            "gauss_law",
            "physical_sector",
            "electric_flux",
            "electric_energy",
            "wilson_loop",
            "real_time_dynamics",
            "trotter_resource_estimate",
            "qpe_resource_estimate",
        ],
        risk_notes=[
            "Finite-cutoff lattice-QED evidence is gauge-audited but not a continuum-limit chemistry claim.",
        ],
    ),
    "pauli_fierz_cavity_qed": FieldModelAdapter(
        model_kind="pauli_fierz_cavity_qed",
        registry_name="molecular_pauli_fierz_cavity_qed",
        capability_tier="exploratory",
        observables=[
            "photon_occupation",
            "dipole_expectation",
            "electron_photon_coupling_energy",
            "dipole_self_energy",
            "polaritonic_state_composition",
            "photon_cutoff_convergence",
        ],
        risk_notes=[
            "Pauli-Fierz cavity-QED evidence is exact or variational only for the configured photon cutoff.",
            "External cavity-QED benchmark validation is outside this first QCchem milestone.",
        ],
    ),
}


def get_field_model_adapter(kind: str) -> FieldModelAdapter:
    """Return static metadata for a supported field-model family."""
    normalized = kind.strip().lower()
    if normalized not in FIELD_MODEL_REGISTRY:
        raise ValueError(f"Unsupported field model: {kind}")
    return FIELD_MODEL_REGISTRY[normalized]


def build_field_model_summary(
    *,
    kind: str,
    model_summary: QFTModelSummary | CavityQEDModelSummary | None,
    resource_estimate: dict[str, Any] | None = None,
    error_budget: dict[str, Any] | None = None,
    risk_notes: list[str] | None = None,
) -> FieldModelSummary:
    """Build the registry-level summary persisted on run artifacts."""
    adapter = get_field_model_adapter(kind)
    inferred_resource = resource_estimate
    inferred_error = error_budget
    if model_summary is not None:
        inferred_resource = inferred_resource or dict(getattr(model_summary, "resource_estimate", {}) or {})
        inferred_error = inferred_error or dict(getattr(model_summary, "error_budget", {}) or {})
    return FieldModelSummary(
        model_kind=adapter.model_kind,
        registry_name=adapter.registry_name,
        capability_tier=adapter.capability_tier,
        observables=list(adapter.observables),
        resource_estimate=inferred_resource or {},
        error_budget=inferred_error or {},
        risk_notes=[*adapter.risk_notes, *(risk_notes or [])],
    )
