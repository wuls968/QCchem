from __future__ import annotations

import pytest

from qcchem.core import HardwareOptimizationSpec
from qcchem.workflow.hardware_optimization import (
    HardwareOptimizationBudgetError,
    HardwareOptimizationCandidate,
    _next_submission,
    build_budget_ledger,
    rank_candidates,
)


def test_hardware_optimization_spec_defaults_are_budget_guarded() -> None:
    spec = HardwareOptimizationSpec(enabled=True)

    assert spec.profile == "h2_precision_push"
    assert spec.max_real_jobs == 3
    assert spec.max_total_budgeted_shots == 40960
    assert spec.stop_if_error_below == pytest.approx(1.6e-3)
    assert spec.requires_confirmation is True
    assert spec.candidate_strategies == [
        "jw_puccd_layout_baseline",
        "parity_puccd_layout",
        "parity_succd_layout",
        "parity_uccsd_layout",
    ]


def test_rank_candidates_prefers_accurate_reduced_low_depth_workload() -> None:
    candidates = [
        HardwareOptimizationCandidate(
            candidate_id="jw_puccd_layout_baseline",
            mapping_kind="jordan_wigner",
            ansatz_kind="puccd",
            local_accuracy_pass=True,
            qubits=4,
            terms=15,
            transpiled_two_qubit_gate_count=42,
            transpiled_depth=146,
            layout_score=0.01,
            local_error_hartree=1.0e-9,
        ),
        HardwareOptimizationCandidate(
            candidate_id="parity_puccd_layout",
            mapping_kind="parity_two_qubit_reduction",
            ansatz_kind="puccd",
            local_accuracy_pass=True,
            qubits=2,
            terms=5,
            transpiled_two_qubit_gate_count=8,
            transpiled_depth=34,
            layout_score=0.02,
            local_error_hartree=2.0e-9,
        ),
        HardwareOptimizationCandidate(
            candidate_id="parity_uccsd_layout",
            mapping_kind="parity_two_qubit_reduction",
            ansatz_kind="uccsd",
            local_accuracy_pass=False,
            qubits=2,
            terms=5,
            transpiled_two_qubit_gate_count=4,
            transpiled_depth=20,
            layout_score=0.0,
            local_error_hartree=0.3,
        ),
    ]

    ranked = rank_candidates(candidates)

    assert [item.candidate_id for item in ranked] == [
        "parity_puccd_layout",
        "jw_puccd_layout_baseline",
        "parity_uccsd_layout",
    ]
    assert ranked[0].eligible_for_runtime is True
    assert ranked[-1].eligible_for_runtime is False


def test_budget_ledger_refuses_more_jobs_than_budget_allows() -> None:
    spec = HardwareOptimizationSpec(
        enabled=True,
        max_real_jobs=1,
        max_total_budgeted_shots=8192,
    )
    ledger = build_budget_ledger(
        spec,
        submitted_attempts=[
            {
                "candidate_id": "parity_puccd_layout",
                "budgeted_shots": 8192,
                "submitted": True,
            }
        ],
    )

    assert ledger["real_jobs_submitted"] == 1
    assert ledger["total_budgeted_shots"] == 8192
    assert ledger["can_submit_more"] is False

    with pytest.raises(HardwareOptimizationBudgetError, match="max_real_jobs"):
        build_budget_ledger(
            spec,
            submitted_attempts=[
                {"candidate_id": "parity_puccd_layout", "budgeted_shots": 8192, "submitted": True},
                {"candidate_id": "parity_succd_layout", "budgeted_shots": 8192, "submitted": True},
            ],
            strict=True,
        )


def test_next_submission_prefers_mapping_diversity_after_systematic_bias() -> None:
    spec = HardwareOptimizationSpec(enabled=True)
    ranked = rank_candidates(
        [
            HardwareOptimizationCandidate(
                candidate_id="parity_puccd_layout",
                mapping_kind="parity_two_qubit_reduction",
                ansatz_kind="puccd",
                local_accuracy_pass=True,
                qubits=2,
                terms=5,
                transpiled_two_qubit_gate_count=4,
                transpiled_depth=22,
                layout_score=0.005,
                local_error_hartree=1.0e-9,
            ),
            HardwareOptimizationCandidate(
                candidate_id="parity_succd_layout",
                mapping_kind="parity_two_qubit_reduction",
                ansatz_kind="succd",
                local_accuracy_pass=True,
                qubits=2,
                terms=5,
                transpiled_two_qubit_gate_count=4,
                transpiled_depth=22,
                layout_score=0.006,
                local_error_hartree=1.0e-9,
            ),
            HardwareOptimizationCandidate(
                candidate_id="jw_puccd_layout_baseline",
                mapping_kind="jordan_wigner",
                ansatz_kind="puccd",
                local_accuracy_pass=True,
                qubits=4,
                terms=15,
                transpiled_two_qubit_gate_count=42,
                transpiled_depth=146,
                layout_score=0.01,
                local_error_hartree=1.0e-9,
            ),
        ]
    )

    candidate, shots, decision = _next_submission(
        ranked,
        [
            {
                "candidate_id": "parity_puccd_layout",
                "mapping_kind": "parity_two_qubit_reduction",
                "budgeted_shots": 8192,
                "submitted": True,
                "succeeded": True,
                "runtime_error_hartree": 0.018,
                "meets_chemical_accuracy": False,
            }
        ],
        spec,
    )

    assert candidate is not None
    assert candidate.candidate_id == "jw_puccd_layout_baseline"
    assert shots == 8192
    assert decision == "diverse_mapping_strategy_probe"
