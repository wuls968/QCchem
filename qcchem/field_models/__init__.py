"""Field-model registry and builders for QCchem."""

from .cavity_qed import (
    CavityQEDContext,
    build_cavity_qed_context,
    summarize_cavity_qed_observables,
)
from .campaign import (
    apply_field_model_cross_case_decisions,
    build_field_model_campaign_summary,
    build_field_model_decision_summary,
    extract_field_model_case_metrics,
)
from .registry import FieldModelAdapter, build_field_model_summary, get_field_model_adapter

__all__ = [
    "CavityQEDContext",
    "FieldModelAdapter",
    "apply_field_model_cross_case_decisions",
    "build_cavity_qed_context",
    "build_field_model_campaign_summary",
    "build_field_model_decision_summary",
    "build_field_model_summary",
    "extract_field_model_case_metrics",
    "get_field_model_adapter",
    "summarize_cavity_qed_observables",
]
