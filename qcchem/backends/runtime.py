"""Runtime/session-ready metadata snapshots."""

from __future__ import annotations

from qcchem.core import (
    BackendCapabilitySummary,
    BackendSpec,
    CompressionResultSummary,
    MeasurementSummary,
    RuntimeOptionsSummary,
)


def build_runtime_options_summary(
    spec: BackendSpec,
    capability: BackendCapabilitySummary,
    *,
    measurement: MeasurementSummary | None = None,
    compression: CompressionResultSummary | None = None,
) -> RuntimeOptionsSummary | None:
    """Build a runtime/session/batch snapshot even when remote execution is not wired yet."""
    if not (spec.runtime.enabled or capability.runtime_ready or capability.session_ready or capability.batch_ready):
        return None
    low_rank_workload = bool(
        measurement is not None
        and measurement.low_rank_aware
        and compression is not None
        and compression.execution_enabled
    )
    session_recommendation = "optional"
    batch_recommendation = "optional"
    if measurement is not None and measurement.estimated_shot_cost >= 20_000:
        session_recommendation = "recommended"
    if measurement is not None and measurement.estimated_shot_cost >= 50_000:
        batch_recommendation = "recommended"
    return RuntimeOptionsSummary(
        enabled=bool(spec.runtime.enabled),
        service=spec.runtime.service,
        instance=spec.runtime.instance,
        runtime_ready=bool(capability.runtime_ready and spec.runtime.runtime_ready),
        session_ready=bool(capability.session_ready and spec.runtime.session_ready),
        batch_ready=bool(capability.batch_ready and spec.runtime.batch_ready),
        precision_target=spec.runtime.precision_target,
        max_budgeted_shots=spec.runtime.max_budgeted_shots,
        max_execution_seconds=spec.runtime.max_execution_seconds,
        calibration_strategy=spec.runtime.calibration_strategy,
        resilience_level=spec.runtime.resilience_level,
        grouping_policy=spec.runtime.grouping_policy,
        session_recommendation=session_recommendation,
        batch_recommendation=batch_recommendation,
        low_rank_workload=low_rank_workload,
        measurement_group_count=(measurement.group_count if measurement is not None else None),
        estimated_shot_cost=(measurement.estimated_shot_cost if measurement is not None else None),
        options=dict(spec.runtime.options),
        provenance={
            "adapter": "runtime_ready_placeholder",
            "remote_execution_configured": spec.kind.strip().lower().startswith("runtime"),
            "session_mode_requested": bool(spec.runtime.session_ready),
            "batch_mode_requested": bool(spec.runtime.batch_ready),
            "low_rank_policy_applied": low_rank_workload,
            "compression_method": (compression.method if compression is not None else None),
        },
    )
