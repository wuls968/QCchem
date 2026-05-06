"""Resource estimators for TC-kicked QSCI and coarse FT-QPE planning."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def lcu_lambda(operator) -> float:
    """Return the Pauli LCU one-norm."""
    return float(np.sum(np.abs(np.asarray(operator.coeffs, dtype=complex))))


def estimate_low_rank_resources(
    operator,
    *,
    selected_determinant_count: int,
    pauli_term_budget: int | None,
) -> dict[str, Any]:
    """Estimate low-rank/term-truncation resource posture for a Pauli Hamiltonian."""
    weights = np.abs(np.asarray(operator.coeffs, dtype=complex))
    term_count = int(len(weights))
    retained = term_count if pauli_term_budget is None else max(0, min(int(pauli_term_budget), term_count))
    discarded_l1 = 0.0
    if retained < term_count:
        ordered = np.sort(weights)[::-1]
        discarded_l1 = float(np.sum(ordered[retained:]))
    return {
        "resource_operator": "physical_active_space_hamiltonian",
        "qubit_count": int(operator.num_qubits),
        "pauli_term_count": term_count,
        "lcu_lambda": lcu_lambda(operator),
        "selected_determinant_count": int(selected_determinant_count),
        "retained_pauli_terms": int(retained),
        "discarded_pauli_terms": int(term_count - retained),
        "discarded_l1_norm": discarded_l1,
        "estimator_scope": "low_rank_resource_audit_only",
    }


def estimate_qpe_resources(
    operator,
    *,
    selected_determinant_count: int,
    target_precision: float,
    trotter_time: float,
    num_kicks: int,
) -> dict[str, Any]:
    """Estimate coarse logical resources for a fault-tolerant QPE-style workflow."""
    precision = max(float(target_precision), 1.0e-12)
    phase_bits = max(int(math.ceil(math.log2(1.0 / precision))), 1)
    queries = int(2**phase_bits - 1)
    term_count = int(len(operator))
    lambda_value = lcu_lambda(operator)
    trotter_steps_per_query = max(int(math.ceil(max(lambda_value * abs(float(trotter_time)), 1.0))), 1)
    pauli_rotations = int(queries * trotter_steps_per_query * max(term_count, 1))
    return {
        "resource_operator": "physical_active_space_hamiltonian",
        "target_precision": precision,
        "phase_bits": phase_bits,
        "controlled_time_evolution_queries": queries,
        "logical_qubit_estimate": int(operator.num_qubits + phase_bits + 2),
        "pauli_term_count": term_count,
        "lcu_lambda": lambda_value,
        "selected_determinant_count": int(selected_determinant_count),
        "first_order_trotter_steps_per_query": trotter_steps_per_query,
        "trotter_time": float(trotter_time),
        "num_tc_kicks": int(num_kicks),
        "pauli_rotation_estimate": pauli_rotations,
        "t_count_estimate": int(pauli_rotations * 50),
        "estimator_scope": "coarse_fault_tolerant_resource_estimate_only",
        "notes": [
            "This is not a compiled fault-tolerant QPE circuit.",
            "Costs are proxy estimates derived from Pauli term count, LCU lambda, and target phase precision.",
        ],
    }
