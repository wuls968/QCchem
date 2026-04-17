"""Empirical calibration helpers for low-rank execution workflows."""

from __future__ import annotations

from qcchem.core import (
    BenchmarkSummary,
    CalibrationSummary,
    MeasurementSummary,
    SampledResultSummary,
)


def build_calibration_summary(
    *,
    measurement: MeasurementSummary | None,
    sampled_result: SampledResultSummary | None,
    benchmark: BenchmarkSummary | None,
    measured_wall_time_seconds: float,
    measured_shot_usage: float | None = None,
    precision_target: float | None = None,
    achieved_error: float | None = None,
    estimated_measurement_cost: float | None = None,
) -> CalibrationSummary | None:
    """Build a calibration summary comparing planned and observed execution cost."""

    derived_shot_usage = None
    if measured_shot_usage is not None:
        derived_shot_usage = float(measured_shot_usage)
    elif measurement is not None and sampled_result is not None and sampled_result.shots is not None:
        derived_shot_usage = float(
            sampled_result.shots
            * max(sampled_result.num_repeats, 1)
            * max(measurement.group_count, 1)
        )

    derived_precision = measurement.runtime_precision_target if measurement is not None else None
    derived_error = benchmark.absolute_error if benchmark is not None else None
    derived_cost = measurement.estimated_shot_cost if measurement is not None else None

    estimated_ratio = None
    if derived_shot_usage is not None and derived_shot_usage > 0:
        if estimated_measurement_cost is not None:
            estimated_ratio = float(estimated_measurement_cost / derived_shot_usage)
        elif derived_cost is not None:
            estimated_ratio = float(derived_cost / derived_shot_usage)

    notes = [
        "Measured wall time is taken from the executed solver path, not full workflow overhead.",
        "Measured shot usage is derived from backend shots, repeat count, and measurement group count.",
    ]
    if benchmark is not None and benchmark.within_uncertainty is False:
        notes.append("Achieved error remains outside the reported statistical uncertainty band.")

    return CalibrationSummary(
        available=True,
        measured_wall_time_seconds=float(measured_wall_time_seconds),
        measured_shot_usage=derived_shot_usage,
        precision_target=precision_target if precision_target is not None else derived_precision,
        achieved_error=achieved_error if achieved_error is not None else derived_error,
        estimated_measurement_cost=(
            estimated_measurement_cost if estimated_measurement_cost is not None else derived_cost
        ),
        estimated_vs_measured_cost=estimated_ratio,
        reference_target=benchmark.comparison_target if benchmark is not None else "exact_baseline",
        notes=notes,
    )
