"""Measurement-planning helpers, including low-rank-aware cost estimation."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter

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


def _shadow_lr_payload(
    mapping: MappedHamiltonian,
    *,
    measurement_spec: MeasurementSpec,
    group_count: int,
    estimated_cost: float,
) -> dict[str, object]:
    operator = mapping.qubit_hamiltonian
    labels = list(operator.paulis.to_labels())
    coeffs = [abs(complex(coeff)) for coeff in operator.coeffs]
    total_weight = sum(coeffs) or 1.0
    basis_weights: Counter[str] = Counter()
    for label, weight in zip(labels, coeffs, strict=True):
        basis = "".join(char if char != "I" else "Z" for char in label)
        basis_weights[basis] += weight
    total_shots = int(measurement_spec.total_shots or max(math.ceil(estimated_cost), group_count))
    basis_limit = max(int(measurement_spec.max_circuits or group_count), 1)
    basis_limit = min(basis_limit, max(total_shots, 1), max(len(basis_weights), 1))
    ranked_bases = basis_weights.most_common(basis_limit)
    selected_weight = sum(float(weight) for _, weight in ranked_bases) or 1.0
    base_shots = [1 for _ in ranked_bases]
    remaining_shots = max(total_shots - len(ranked_bases), 0)
    raw_extras = [
        remaining_shots * float(weight) / selected_weight
        for _, weight in ranked_bases
    ]
    extra_shots = [int(math.floor(value)) for value in raw_extras]
    leftover = remaining_shots - sum(extra_shots)
    for index in sorted(
        range(len(raw_extras)),
        key=lambda item: raw_extras[item] - extra_shots[item],
        reverse=True,
    )[:leftover]:
        extra_shots[index] += 1
    shadow_bases: list[dict[str, object]] = []
    shot_allocation: list[dict[str, object]] = []
    for index, (basis, weight) in enumerate(ranked_bases):
        fraction = float(weight / total_weight)
        shots = base_shots[index] + extra_shots[index]
        shadow_bases.append(
            {
                "basis_id": index,
                "basis": basis,
                "weight": float(weight),
                "allocation_fraction": fraction,
                "allocated_shot_fraction": float(shots / max(total_shots, 1)),
            }
        )
        shot_allocation.append(
            {
                "basis_id": index,
                "shots": shots,
                "allocation_policy": "coefficient_l1_covariance_proxy",
            }
        )
    allocated = sum(int(item["shots"]) for item in shot_allocation)
    predicted_variance = float((total_weight**2) / max(allocated, 1))
    grouped_precision_variance_proxy = float((total_weight**2) / max(float(estimated_cost), 1.0))
    selected_basis_count = len(ranked_bases)
    total_basis_count = len(basis_weights)
    basis_l1_coverage_fraction = float(selected_weight / total_weight)
    unselected_basis_count = max(total_basis_count - selected_basis_count, 0)
    shot_fractions = [
        float(int(item["shots"]) / max(total_shots, 1))
        for item in shot_allocation
    ]
    max_allocated_shot_fraction = max(shot_fractions) if shot_fractions else 0.0
    if len(shot_fractions) > 1:
        allocation_entropy = float(
            -sum(fraction * math.log(fraction) for fraction in shot_fractions if fraction > 0.0)
            / math.log(len(shot_fractions))
        )
    else:
        allocation_entropy = 0.0
    variance_inflation = (
        float(predicted_variance / grouped_precision_variance_proxy)
        if grouped_precision_variance_proxy > 0.0
        else None
    )
    plan_digest_payload = {
        "planner": "shadow_lr",
        "shadow_bases": [
            {
                "basis": item["basis"],
                "weight": round(float(item["weight"]), 16),
                "allocation_fraction": round(float(item["allocation_fraction"]), 16),
            }
            for item in shadow_bases
        ],
        "shot_allocation": [
            {
                "basis_id": int(item["basis_id"]),
                "shots": int(item["shots"]),
                "allocation_policy": item["allocation_policy"],
            }
            for item in shot_allocation
        ],
        "budgeted_shots": int(total_shots),
        "max_circuits": measurement_spec.max_circuits,
        "objective": measurement_spec.objective,
    }
    plan_digest = hashlib.sha256(
        json.dumps(plan_digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "shadow_bases": shadow_bases,
        "shot_allocation": shot_allocation,
        "allocated_shots": allocated,
        "predicted_variance": predicted_variance,
        "measurement_cost_model": {
            "planner": "shadow_lr",
            "term_l1_norm": float(total_weight),
            "selected_basis_l1_norm": float(selected_weight),
            "basis_l1_coverage_fraction": basis_l1_coverage_fraction,
            "basis_count": total_basis_count,
            "selected_basis_count": selected_basis_count,
            "unselected_basis_count": unselected_basis_count,
            "budgeted_shots": total_shots,
            "allocated_shots": allocated,
            "max_allocated_shot_fraction": max_allocated_shot_fraction,
            "allocation_entropy": allocation_entropy,
            "grouped_precision_baseline_shots": float(estimated_cost),
            "predicted_variance": predicted_variance,
            "grouped_precision_variance_proxy": grouped_precision_variance_proxy,
            "variance_inflation_vs_grouped_precision_proxy": variance_inflation,
            "plan_digest": plan_digest,
            "max_circuits": measurement_spec.max_circuits,
            "strategies": list(measurement_spec.strategies),
            "objective": measurement_spec.objective,
        },
    }


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
    shadow_payload: dict[str, object] = {}
    planner = measurement_spec.planner.strip().lower()
    if planner == "shadow_lr":
        shadow_payload = _shadow_lr_payload(
            executed_mapping,
            measurement_spec=measurement_spec,
            group_count=group_count,
            estimated_cost=estimated_cost,
        )
        notes.append("Shadow-LR planner generated locally biased shadow bases and shot allocation.")
        allocated_shots = float(shadow_payload.get("allocated_shots", estimated_cost))
        if allocated_shots > 0:
            estimated_cost = allocated_shots
            if uncompressed_cost > 0:
                cost_ratio = float(estimated_cost / uncompressed_cost)
            notes.append(
                "Shadow-LR estimated shot cost uses allocated shadow shots; grouped precision cost is retained in measurement_cost_model."
            )

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
        planner=measurement_spec.planner,
        shadow_bases=list(shadow_payload.get("shadow_bases", [])),
        shot_allocation=list(shadow_payload.get("shot_allocation", [])),
        predicted_variance=shadow_payload.get("predicted_variance"),  # type: ignore[arg-type]
        realized_variance=None,
        measurement_cost_model=dict(shadow_payload.get("measurement_cost_model", {})),
        basis_reuse_across_properties=(planner == "shadow_lr"),
        notes=notes,
    )
