from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from qiskit.quantum_info import SparsePauliOp

from qcchem.backends import StatevectorBackend
from qcchem.core import BackendSpec, CompressionSpec
from qcchem.io.config import load_run_spec
from qcchem.exploratory.solvers.lr_ace import build_low_rank_generator_plan
from qcchem.exploratory.solvers.lr_ace import build_solver as build_lr_ace_solver
from qcchem.workflow.runner import _classify_lr_ace_adaptive_trust, _compression_post_term_limit


def test_lr_ace_turns_dominant_x_factor_into_real_mixing_generator() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", -1.0),
            ("IZ", 0.4),
            ("ZI", -0.4),
            ("ZZ", -0.01),
            ("XX", 0.18),
        ]
    )

    plan = build_low_rank_generator_plan(operator, max_generators=2)

    assert plan["source_terms"][0]["pauli"] == "XX"
    assert plan["selected_generators"][0]["pauli"] == "YX"
    assert plan["selected_generators"][0]["source_pauli"] == "XX"
    assert plan["selected_factor_count"] == 1
    assert {item["pauli"] for item in plan["candidate_generators"]} == {"YX", "XY"}
    assert plan["low_rank_aware"] is True


def test_lr_ace_adaptive_generator_plan_records_scores_and_batches() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("IIII", -1.0),
            ("XXII", 0.20),
            ("IXYI", 0.12),
            ("IIZX", 0.08),
            ("YYYY", 0.04),
        ]
    )

    plan = build_low_rank_generator_plan(operator, max_generators=3)

    assert plan["selection_rule"] == "adaptive_score_weight_locality_reference_mixing"
    assert [item["batch_index"] for item in plan["selected_generators"]] == [0, 1, 2]
    assert all("adaptive_score" in item for item in plan["selected_generators"])
    assert plan["selected_generators"][0]["adaptive_score"] > plan["selected_generators"][2]["adaptive_score"]


def test_lr_ace_generator_plan_enumerates_deduplicated_candidate_pool() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", -1.0),
            ("XX", 0.20),
            ("YY", 0.19),
        ]
    )

    plan = build_low_rank_generator_plan(operator, max_generators=1)
    candidate_paulis = [item["pauli"] for item in plan["candidate_generators"]]

    assert len(candidate_paulis) > len(plan["selected_generators"])
    assert len(candidate_paulis) == len(set(candidate_paulis))
    assert set(candidate_paulis) == {"XY", "YX"}


def test_precision_first_compression_disables_legacy_rank_times_six_truncation() -> None:
    bundle = SimpleNamespace(method="modified_cholesky", rank=3, secondary_rank=None)
    spec = CompressionSpec(enabled=True, execution_enabled=True)

    assert _compression_post_term_limit(bundle, 100, spec) is None


def test_explicit_runtime_term_budget_restores_low_rank_truncation() -> None:
    bundle = SimpleNamespace(method="modified_cholesky", rank=3, secondary_rank=None)
    spec = CompressionSpec(enabled=True, execution_enabled=True, runtime_term_budget=12)

    assert _compression_post_term_limit(bundle, 100, spec) == 12


def test_lr_ace_adaptive_config_is_loaded_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "adaptive_lr_ace.yaml"
    config_path.write_text(
        """
molecule:
  name: adaptive-H2
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.74]

policy:
  allow_exploratory: true

problem:
  compression:
    enabled: true
    execution_enabled: true
    rank_schedule: [4, 8]
    compression_error_budget_hartree: 7.0e-4
    allow_pauli_truncation: true

mapping:
  kind: parity_two_qubit_reduction

backend:
  kind: statevector

solver:
  kind: lr_ace
  experimental: true
  lr_ace_adaptive:
    enabled: true
    generator_schedule: [2, 4]
    optimizer_maxiter_schedule: [25, 50]
    initial_point_strategies: [zeros, random]
    random_restarts: 2
    target_error_hartree: 1.0e-4
    max_wall_time_seconds: 30
    uncompressed_check_qubit_limit: 10
    candidate_pool_policy: residual_guided
    candidate_scan_limit: 5
    residual_batch_size: 2
    residual_scan_angles: [-0.2, 0.2]
    min_energy_improvement_hartree: 3.0e-4
    max_adaptive_expansions: 2

run:
  output_dir: artifacts/adaptive-H2
""",
        encoding="utf-8",
    )

    spec = load_run_spec(config_path)

    assert spec.solver.lr_ace_adaptive.enabled is True
    assert spec.solver.lr_ace_adaptive.generator_schedule == [2, 4]
    assert spec.solver.lr_ace_adaptive.random_restarts == 2
    assert spec.solver.lr_ace_adaptive.candidate_pool_policy == "residual_guided"
    assert spec.solver.lr_ace_adaptive.candidate_scan_limit == 5
    assert spec.solver.lr_ace_adaptive.residual_batch_size == 2
    assert spec.solver.lr_ace_adaptive.residual_scan_angles == pytest.approx([-0.2, 0.2])
    assert spec.solver.lr_ace_adaptive.min_energy_improvement_hartree == pytest.approx(3.0e-4)
    assert spec.solver.lr_ace_adaptive.max_adaptive_expansions == 2
    assert spec.problem.compression.rank_schedule == [4, 8]
    assert spec.problem.compression.compression_error_budget_hartree == pytest.approx(7.0e-4)
    assert spec.problem.compression.allow_pauli_truncation is True


def test_lr_ace_adaptive_solver_runs_schedule_and_records_provenance() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", -1.0),
            ("IZ", 0.3),
            ("ZI", -0.2),
            ("XX", 0.18),
            ("YY", -0.11),
        ]
    )
    spec = SimpleNamespace(
        ansatz=SimpleNamespace(kind="lr_ace", reps=1),
        optimizer=SimpleNamespace(kind="COBYLA", maxiter=3, tol=None),
        initial_point="zeros",
        lr_ace_adaptive=SimpleNamespace(
            enabled=True,
            generator_schedule=[1, 2],
            optimizer_maxiter_schedule=[3, 5],
            initial_point_strategies=["zeros"],
            random_restarts=0,
            target_error_hartree=0.0,
            max_wall_time_seconds=60.0,
            uncompressed_check_qubit_limit=4,
            candidate_pool_policy="residual_guided",
            candidate_scan_limit=8,
            residual_batch_size=1,
            residual_scan_angles=[-0.2, 0.2],
            min_energy_improvement_hartree=0.0,
            max_adaptive_expansions=1,
        ),
    )
    solver = build_lr_ace_solver(
        spec,
        StatevectorBackend(BackendSpec(kind="statevector", seed=123)),
        seed=123,
    )

    outcome = solver.solve(operator)
    adaptive = outcome.metadata["lr_ace"]["adaptive"]

    assert adaptive["enabled"] is True
    assert [stage["generator_count"] for stage in adaptive["stages"]] == [1, 2]
    assert [stage["optimizer_maxiter"] for stage in adaptive["stages"]] == [3, 5]
    assert adaptive["best_stage_index"] in {0, 1}
    assert adaptive["trust_label"] in {"passed_compressed_with_budget", "ansatz_limited"}


def test_lr_ace_residual_guided_adaptive_expansion_records_selected_generators() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", -1.0),
            ("IZ", 0.3),
            ("ZI", -0.2),
            ("XX", 0.18),
            ("YY", -0.17),
        ]
    )
    spec = SimpleNamespace(
        ansatz=SimpleNamespace(kind="lr_ace", reps=1),
        optimizer=SimpleNamespace(kind="COBYLA", maxiter=2, tol=None),
        initial_point="zeros",
        lr_ace_adaptive=SimpleNamespace(
            enabled=True,
            generator_schedule=[1],
            optimizer_maxiter_schedule=[2],
            initial_point_strategies=["zeros"],
            random_restarts=0,
            target_error_hartree=0.0,
            max_wall_time_seconds=60.0,
            uncompressed_check_qubit_limit=4,
            candidate_pool_policy="residual_guided",
            candidate_scan_limit=8,
            residual_batch_size=1,
            residual_scan_angles=[-3.14, -0.2, 0.2],
            min_energy_improvement_hartree=0.0,
            max_adaptive_expansions=1,
        ),
    )
    solver = build_lr_ace_solver(
        spec,
        StatevectorBackend(BackendSpec(kind="statevector", seed=321)),
        seed=321,
    )

    outcome = solver.solve(operator)
    adaptive = outcome.metadata["lr_ace"]["adaptive"]

    assert adaptive["expansions"]
    assert adaptive["expansions"][0]["candidate_pool_size"] >= 1
    assert adaptive["expansions"][0]["scanned_count"] >= 1
    assert adaptive["expansions"][0]["selected_count"] >= 1
    assert adaptive["expansions"][0]["selected_generators"]
    assert adaptive["expansions"][0]["best_estimated_drop_hartree"] is not None


def test_lr_ace_residual_scan_prefers_measured_drop_over_coefficient_score() -> None:
    class PreferenceBackend:
        backend_kind = "preference"

        def estimate_expectation(self, circuit, operator, parameter_values) -> float:
            label = circuit.data[-1].operation.operator.paulis[0].to_label()
            return {"XY": -0.01, "IY": -0.30}.get(label, 0.0)

    operator = SparsePauliOp.from_list(
        [
            ("II", -1.0),
            ("XX", 0.20),
            ("IX", 0.05),
        ]
    )
    spec = SimpleNamespace(
        ansatz=SimpleNamespace(kind="lr_ace", reps=1),
        optimizer=SimpleNamespace(kind="COBYLA", maxiter=2, tol=None),
        initial_point="zeros",
        lr_ace_adaptive=SimpleNamespace(enabled=True),
    )
    solver = build_lr_ace_solver(spec, PreferenceBackend(), seed=11)

    selected, expansion, evaluations = solver._scan_residual_candidates(
        operator,
        selected_paulis=["YX"],
        best_parameters=[0.0],
        base_energy=0.0,
        candidate_scan_limit=4,
        residual_batch_size=1,
        residual_scan_angles=[0.1],
        min_energy_improvement_hartree=0.0,
        expansion_index=0,
    )

    assert selected == ["IY"]
    assert expansion["selected_generators"][0]["pauli"] == "IY"
    assert expansion["best_estimated_drop_hartree"] == pytest.approx(0.30)
    assert evaluations == 2


def test_lr_ace_adaptive_trust_marks_compression_limited_when_uncompressed_ansatz_passes() -> None:
    label = _classify_lr_ace_adaptive_trust(
        target_error_hartree=1.6e-3,
        local_exact_error_hartree=1.0e-5,
        compression_enabled=True,
        compressed_solver_energy=-1.00,
        uncompressed_solver_energy=-1.004,
        uncompressed_exact_solver_energy=-1.00401,
    )

    assert label == "compression_limited"


def test_lr_ace_adaptive_trust_marks_ansatz_limited_when_uncompressed_ansatz_fails() -> None:
    label = _classify_lr_ace_adaptive_trust(
        target_error_hartree=1.6e-3,
        local_exact_error_hartree=1.0e-5,
        compression_enabled=True,
        compressed_solver_energy=-1.00,
        uncompressed_solver_energy=-0.990,
        uncompressed_exact_solver_energy=-1.004,
    )

    assert label == "ansatz_limited"
