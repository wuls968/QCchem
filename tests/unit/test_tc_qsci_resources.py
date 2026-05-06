from __future__ import annotations

import numpy as np
import pytest
from qiskit.quantum_info import SparsePauliOp

from qcchem.exploratory.tc_qsci.cast import hermitian_project_operator
from qcchem.exploratory.tc_qsci.resources import (
    estimate_low_rank_resources,
    estimate_qpe_resources,
)


def test_hermitian_projection_records_anti_hermitian_norm() -> None:
    operator = SparsePauliOp.from_list([("X", 1.0j), ("Z", 0.5)])

    projected, audit = hermitian_project_operator(operator)

    assert audit["hermitian_projection_applied"] is True
    assert audit["anti_hermitian_norm"] > 0.0
    assert np.allclose(projected.to_matrix(), projected.to_matrix().conj().T)
    assert np.linalg.norm(projected.to_matrix() - SparsePauliOp.from_list([("Z", 0.5)]).to_matrix()) < 1e-12


def test_resource_estimators_report_lcu_lambda_and_qpe_costs() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", 1.0),
            ("ZI", -0.5),
            ("XX", 0.25),
        ]
    )

    low_rank = estimate_low_rank_resources(
        operator,
        selected_determinant_count=3,
        pauli_term_budget=2,
    )
    qpe = estimate_qpe_resources(
        operator,
        selected_determinant_count=3,
        target_precision=1.0e-3,
        trotter_time=0.2,
        num_kicks=2,
    )

    assert low_rank["qubit_count"] == 2
    assert low_rank["pauli_term_count"] == 3
    assert low_rank["lcu_lambda"] == pytest.approx(1.75)
    assert low_rank["selected_determinant_count"] == 3
    assert low_rank["retained_pauli_terms"] == 2
    assert qpe["phase_bits"] == 10
    assert qpe["controlled_time_evolution_queries"] == 1023
    assert qpe["logical_qubit_estimate"] == 14
    assert qpe["estimator_scope"] == "coarse_fault_tolerant_resource_estimate_only"
