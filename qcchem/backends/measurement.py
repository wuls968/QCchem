"""Measurement-planning helpers, including low-rank-aware cost estimation."""

from __future__ import annotations

import math

from qcchem.core import CompressionResultSummary, MeasurementSpec, MeasurementSummary
from qcchem.mapping import MappedHamiltonian


def _group_count(mapping: MappedHamiltonian, *, low_rank_aware: bool) -> int:
    operator = mapping.qubit_hamiltonian
    try:
        groups = operator.group_commuting(qubit_wise=not low_rank_aware)
        return max(len(groups), 1)
    except Exception:
        return max(len(operator), 1)


def _precision_target(
    measurement_spec: MeasurementSpec,
    *,
    backend_precision: float | None,
    backend_shots: int | None,
) -> float:
    if measurement_spec.runtime_precision_target is not None:
        return float(measurement_spec.runtime_precision_target)
    if backend_precision is not None:
        return float(backend_precision)
    if backend_shots is not None and backend_shots > 0:
        return float(1.0 / math.sqrt(float(backend_shots)))
    return 1.0e-2


def plan_measurement(
    *,
    measurement_spec: MeasurementSpec,
    executed_mapping: MappedHamiltonian,
    uncompressed_mapping: MappedHamiltonian,
    compression_result: CompressionResultSummary | None,
    backend_precision: float | None,
    backend_shots: int | None,
) -> MeasurementSummary:
    """Build a persisted measurement plan for the chosen execution path."""
    low_rank_aware = bool(
        compression_result is not None
        and compression_result.execution_enabled
        and compression_result.rank > 0
    )
    precision_target = _precision_target(
        measurement_spec,
        backend_precision=backend_precision,
        backend_shots=backend_shots,
    )
    group_count = _group_count(executed_mapping, low_rank_aware=low_rank_aware)
    uncompressed_group_count = _group_count(uncompressed_mapping, low_rank_aware=False)
    shots_per_group = max(int(math.ceil(1.0 / max(precision_target**2, 1.0e-12))), 1)
    estimated_cost = float(group_count * shots_per_group)
    uncompressed_cost = float(uncompressed_group_count * shots_per_group)
    cost_ratio = None
    if uncompressed_cost > 0:
        cost_ratio = float(estimated_cost / uncompressed_cost)

    notes = [
        f"Measurement groups estimated with strategy '{measurement_spec.strategy}'.",
        f"Per-group shot estimate derived from precision target {precision_target:.6g}.",
    ]
    if low_rank_aware:
        notes.append("Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.")
    else:
        notes.append("Measurement planning reflects the uncompressed execution path.")

    return MeasurementSummary(
        strategy=measurement_spec.strategy,
        group_count=group_count,
        low_rank_aware=low_rank_aware,
        estimated_shot_cost=estimated_cost,
        runtime_precision_target=precision_target,
        execution_mode=measurement_spec.execution_mode,
        grouping_policy=measurement_spec.grouping_policy,
        term_count=len(executed_mapping.qubit_hamiltonian),
        uncompressed_group_count=uncompressed_group_count,
        uncompressed_estimated_shot_cost=uncompressed_cost,
        cost_reduction_ratio=cost_ratio,
        notes=notes,
    )
