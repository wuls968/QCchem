"""Helpers for chemically continuous variational initial guesses."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from qcchem.core import ContinuitySpec, InitialPointCandidate, RunResult, RunSpec


@dataclass(slots=True)
class ContinuityRecord:
    """One optimized VQE point that can seed a later run."""

    values: list[float]
    source: str
    source_run_id: str
    source_artifact_root: str
    source_parameter_count: int
    parameter_value: float | None = None


def supports_initial_point_continuity(spec: RunSpec) -> bool:
    """Return whether a run spec can accept a previous VQE optimum."""
    return str(spec.solver.kind).strip().lower() == "vqe"


def attach_initial_point_candidate(spec: RunSpec, candidate: InitialPointCandidate | None) -> None:
    """Attach a warm-start candidate to a run spec when the solver supports it."""
    if candidate is not None and supports_initial_point_continuity(spec):
        spec.solver.initial_point_candidate = candidate


def _invalid_candidate(
    records: list[ContinuityRecord],
    continuity: ContinuitySpec,
    *,
    target_parameter_value: float | None,
    fallback_reason: str,
) -> InitialPointCandidate | None:
    if not records:
        return None
    latest = records[-1]
    return InitialPointCandidate(
        values=[],
        source=latest.source,
        mode=continuity.mode,
        on_parameter_mismatch=continuity.on_parameter_mismatch,
        source_run_id=latest.source_run_id,
        source_artifact_root=latest.source_artifact_root,
        source_parameter_count=latest.source_parameter_count,
        history_sources=[item.source for item in records[-2:]],
        history_parameter_values=[
            float(item.parameter_value) for item in records[-2:] if item.parameter_value is not None
        ],
        target_parameter_value=target_parameter_value,
        fallback_reason=fallback_reason,
    )


def _previous_optimal_candidate(
    records: list[ContinuityRecord],
    continuity: ContinuitySpec,
    *,
    target_parameter_value: float | None,
) -> InitialPointCandidate | None:
    if not records:
        return None
    latest = records[-1]
    return InitialPointCandidate(
        values=[float(value) for value in latest.values],
        source=latest.source,
        mode="previous_optimal",
        on_parameter_mismatch=continuity.on_parameter_mismatch,
        source_run_id=latest.source_run_id,
        source_artifact_root=latest.source_artifact_root,
        source_parameter_count=latest.source_parameter_count,
        history_sources=[latest.source],
        history_parameter_values=(
            [] if latest.parameter_value is None else [float(latest.parameter_value)]
        ),
        target_parameter_value=target_parameter_value,
    )


def _linear_predictor_candidate(
    records: list[ContinuityRecord],
    continuity: ContinuitySpec,
    *,
    target_parameter_value: float | None,
) -> InitialPointCandidate | None:
    if len(records) < 2:
        return _previous_optimal_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
        )
    if target_parameter_value is None:
        return _invalid_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
            fallback_reason="linear_predictor requires a target scan parameter value",
        )
    previous = records[-1]
    before_previous = records[-2]
    if previous.parameter_value is None or before_previous.parameter_value is None:
        return _invalid_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
            fallback_reason="linear_predictor requires two prior scan parameter values",
        )
    delta = float(previous.parameter_value) - float(before_previous.parameter_value)
    if abs(delta) <= 1.0e-12:
        return _invalid_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
            fallback_reason="linear_predictor requires distinct previous scan parameter values",
        )
    if previous.source_parameter_count != before_previous.source_parameter_count or len(previous.values) != len(before_previous.values):
        return _invalid_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
            fallback_reason="linear_predictor history parameter counts do not match",
        )
    scale = (float(target_parameter_value) - float(previous.parameter_value)) / delta
    predicted = [
        float(prev + scale * (prev - older))
        for prev, older in zip(previous.values, before_previous.values)
    ]
    if not all(isfinite(value) for value in predicted):
        return _invalid_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
            fallback_reason="linear_predictor produced non-finite parameter values",
        )
    return InitialPointCandidate(
        values=predicted,
        source=previous.source,
        mode="linear_predictor",
        on_parameter_mismatch=continuity.on_parameter_mismatch,
        source_run_id=previous.source_run_id,
        source_artifact_root=previous.source_artifact_root,
        source_parameter_count=len(predicted),
        history_sources=[before_previous.source, previous.source],
        history_parameter_values=[
            float(before_previous.parameter_value),
            float(previous.parameter_value),
        ],
        target_parameter_value=float(target_parameter_value),
    )


def build_initial_point_candidate(
    records: list[ContinuityRecord],
    continuity: ContinuitySpec,
    *,
    target_parameter_value: float | None = None,
) -> InitialPointCandidate | None:
    """Build a warm-start candidate from previous VQE records."""
    if not continuity.enabled:
        return None
    mode = str(continuity.mode).strip().lower()
    if mode == "previous_optimal":
        return _previous_optimal_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
        )
    if mode == "linear_predictor":
        return _linear_predictor_candidate(
            records,
            continuity,
            target_parameter_value=target_parameter_value,
        )
    return _invalid_candidate(
        records,
        continuity,
        target_parameter_value=target_parameter_value,
        fallback_reason=f"unsupported continuity mode: {continuity.mode}",
    )


def build_continuity_record(
    result: RunResult,
    *,
    source_label: str,
    parameter_value: float | None = None,
) -> ContinuityRecord | None:
    """Extract a reusable VQE optimum from a completed run."""
    variational = result.variational_result
    if variational is None:
        return None
    if str(variational.solver_kind).strip().lower() != "vqe":
        return None
    if not variational.optimal_parameters:
        return None
    return ContinuityRecord(
        values=[float(value) for value in variational.optimal_parameters],
        source=source_label,
        source_run_id=result.run_id,
        source_artifact_root=str(result.artifacts.root),
        source_parameter_count=int(variational.parameter_count),
        parameter_value=parameter_value,
    )


def summarize_initial_point_continuity(result: RunResult) -> dict[str, object]:
    """Extract a compact warm-start summary from a run result."""
    variational = result.variational_result
    if variational is None:
        return {
            "initial_point_reused": None,
            "initial_point_source": None,
            "initial_point_strategy": None,
            "history_sources": [],
            "fallback_reason": None,
            "iterations": None,
            "evaluations": None,
            "parameter_count": None,
        }
    provenance = dict(variational.initial_point_provenance or {})
    return {
        "initial_point_reused": provenance.get("reused"),
        "initial_point_source": provenance.get("candidate_source"),
        "initial_point_strategy": provenance.get("effective_strategy"),
        "history_sources": list(provenance.get("history_sources") or []),
        "fallback_reason": provenance.get("fallback_reason"),
        "iterations": int(variational.iterations),
        "evaluations": int(variational.evaluations),
        "parameter_count": int(variational.parameter_count),
    }
