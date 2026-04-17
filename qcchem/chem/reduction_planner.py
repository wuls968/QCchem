"""Safe reduction-planning helpers for QCchem core workflows."""

from __future__ import annotations

from qcchem.core import ReductionAuditSummary, ReductionPlanResult, RunSpec


def build_reduction_plan(
    spec: RunSpec,
    reduction_audit: ReductionAuditSummary | None,
) -> ReductionPlanResult:
    """Build a lightweight reduction-plan summary from the current QCchem spec."""
    active_space_spec = spec.problem.active_space
    strategy = "none"
    mode = "disabled"
    recommended_changes: dict[str, object] = {}
    notes: list[str] = []

    if spec.problem.freeze_core:
        recommended_changes["freeze_core"] = True
        notes.append("Freeze-core reduction is enabled.")
    if spec.problem.remove_orbitals:
        recommended_changes["remove_orbitals"] = list(spec.problem.remove_orbitals)
        notes.append("Manual virtual-orbital removal is configured.")
    if active_space_spec is not None:
        if active_space_spec.selection_mode.strip().lower() == "auto":
            mode = "auto"
            strategy = active_space_spec.auto.strategy
            recommended_changes["active_space"] = {
                "selection_mode": "auto",
                "num_occupied": active_space_spec.auto.num_occupied,
                "num_virtual": active_space_spec.auto.num_virtual,
            }
            notes.append("Automatic active-space recommendation is configured.")
        else:
            mode = "manual"
            strategy = "manual_active_space"
            recommended_changes["active_space"] = {
                "num_electrons": active_space_spec.num_electrons,
                "num_spatial_orbitals": active_space_spec.num_spatial_orbitals,
                "active_orbitals": active_space_spec.active_orbitals,
            }
            notes.append("Manual active-space reduction is configured.")

    if mode == "disabled" and reduction_audit is not None and reduction_audit.transformers_applied:
        mode = "audit_only"
        strategy = "executed_transformers"
        notes.append("Reduction audit captures executed transformers even without explicit planning metadata.")

    enabled = mode != "disabled" or reduction_audit is not None
    if not notes:
        notes.append("No reduction planning inputs were requested.")
    return ReductionPlanResult(
        enabled=enabled,
        mode=mode,
        strategy=strategy,
        recommended_changes=recommended_changes,
        reduction_audit=reduction_audit,
        provenance={
            "source": "qcchem.chem.reduction_planner",
            "policy_name": spec.policy.name,
        },
        notes=notes,
    )
