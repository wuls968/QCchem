from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from qcchem.workflow.runner import run_from_config
from qcchem.io.config import load_run_spec

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_h2_lr_ace_flagship_core_run_is_validated_and_records_gate(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "lr_ace" / "h2_flagship.yaml",
        output_dir=tmp_path / "h2_lr_ace_flagship",
    )

    assert result.verification_status == "validated"
    assert result.module_origin == "core"
    assert result.capability_tier == "flagship"
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True
    assert result.variational_result is not None
    assert result.variational_result.solver_kind == "lr_ace"

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    lr_ace = payload["variational_result"]["ansatz"]["lr_ace"]
    assert lr_ace["method_role"] == "flagship"
    assert lr_ace["profile"] == "compact"
    assert lr_ace["validation_gate"]["verification_status"] == "validated"
    assert lr_ace["validation_gate"]["trust_label"] in {
        "local_exact_validated",
        "passed_exact_reference",
    }
    assert payload["evidence_summary"]["trust_judgment"]["lr_ace_trust_label"] == lr_ace["validation_gate"]["trust_label"]


@pytest.mark.integration
def test_lih_active_lr_ace_flagship_core_run_is_validated(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "lr_ace" / "lih_active_flagship.yaml",
        output_dir=tmp_path / "lih_active_lr_ace_flagship",
    )

    assert result.verification_status == "validated"
    assert result.module_origin == "core"
    assert result.capability_tier == "flagship"
    assert result.mapping.num_qubits == 2
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True


@pytest.mark.integration
def test_h2_lr_ace_reaches_local_chemical_accuracy_and_records_provenance(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_lr_ace.yaml",
        output_dir=tmp_path / "h2_lr_ace",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True
    assert result.mapping.num_qubits == 2
    assert result.variational_result is not None
    assert result.variational_result.parameter_count <= 2
    assert result.compression_result is not None
    assert result.compression_result.enabled is True

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    lr_ace = payload["variational_result"]["ansatz"]["lr_ace"]
    assert lr_ace["algorithm_name"] == "LR-ACE"
    assert lr_ace["low_rank_method"] == "modified_cholesky"
    assert lr_ace["selected_factor_count"] >= 1
    assert lr_ace["local_accuracy_gate"]["passed"] is True
    assert "LR-ACE" in result.artifacts.report_markdown.read_text(encoding="utf-8")


@pytest.mark.integration
def test_lih_active_lr_ace_runs_as_exploratory_low_qubit_artifact(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "lih_active_lr_ace.yaml",
        output_dir=tmp_path / "lih_active_lr_ace",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.mapping.num_qubits == 2
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True
    assert result.variational_result is not None
    assert result.variational_result.parameter_count <= 6
    assert result.compression_result is not None
    assert result.compression_result.rank >= 1


@pytest.mark.integration
def test_h2_lr_ace_runtime_config_is_submission_guarded_by_default() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "exploratory" / "h2_lr_ace_runtime.yaml")

    assert spec.solver.kind == "lr_ace"
    assert spec.solver.experimental is True
    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.options["submit_real_job"] is False
    assert spec.backend.runtime.options["requires_action_time_confirmation"] is True
    assert spec.backend.runtime.max_budgeted_shots == 4096


@pytest.mark.integration
@pytest.mark.slow
def test_h2_adaptive_lr_ace_slow_smoke_records_bounded_gate(tmp_path: Path) -> None:
    config = tmp_path / "h2_adaptive_lr_ace_smoke.yaml"
    config.write_text(
        dedent(
            """
            molecule:
              name: H2-LR-ACE-adaptive-smoke
              geometry:
                - symbol: H
                  coords: [0.0, 0.0, 0.0]
                - symbol: H
                  coords: [0.0, 0.0, 0.74]
              charge: 0
              multiplicity: 1
              basis: sto3g

            policy:
              name: benchmark
              allow_exploratory: true

            exploratory:
              enabled: true
              modules: [lr_ace]

            problem:
              compression:
                enabled: true
                method: modified_cholesky
                threshold: 1.0e-10
                max_rank: 4
                apply_to_solver: true
                execution_enabled: true
                term_budget_policy: precision_first
                allow_pauli_truncation: false
              measurement:
                strategy: low_rank_lr_ace_adaptive_local
                execution_mode: estimator
                grouping_policy: low_rank_factor_aware

            mapping:
              kind: parity_two_qubit_reduction

            backend:
              kind: statevector
              seed: 1729
              runtime:
                enabled: false

            solver:
              kind: lr_ace
              experimental: true
              optimizer:
                kind: COBYLA
                maxiter: 12
              ansatz:
                kind: lr_ace
                reps: 2
              initial_point: zeros
              lr_ace_adaptive:
                enabled: true
                generator_schedule: [1, 2]
                optimizer_maxiter_schedule: [8, 12]
                initial_point_strategies: [zeros]
                random_restarts: 1
                target_error_hartree: 1.6e-3
                max_wall_time_seconds: 5
                uncompressed_check_qubit_limit: 12
                candidate_pool_policy: residual_guided
                candidate_scan_limit: 4
                residual_batch_size: 2
                residual_scan_angles: [-0.05, 0.05]
                min_energy_improvement_hartree: 2.0e-4
                max_adaptive_expansions: 1

            benchmark:
              enabled: true
              exact_baseline_qubit_limit: 12
              absolute_error_threshold: 1.6e-3
              relative_error_threshold: 1.6e-3

            run:
              seed: 1729
              output_dir: artifacts/h2_adaptive_lr_ace_smoke
              overwrite: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    result = run_from_config(
        config,
        output_dir=tmp_path / "h2_adaptive_lr_ace_smoke",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.backend.runtime_enabled is False
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True
    assert result.variational_result is not None

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    adaptive = payload["variational_result"]["ansatz"]["lr_ace"]["adaptive"]
    assert adaptive["enabled"] is True
    assert adaptive["max_wall_time_seconds"] == 5.0
    assert adaptive["best_exact_error_hartree"] < adaptive["target_error_hartree"]
    assert adaptive["uncompressed_check_triggered"] is True
    assert adaptive["trust_label"] == "passed_exact_reference"
    assert len(adaptive["stages"]) >= 1


@pytest.mark.integration
@pytest.mark.stress
def test_h2o_active_adaptive_lr_ace_reaches_compressed_local_gate(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2o_active_lr_ace_adaptive.yaml",
        output_dir=tmp_path / "h2o_active_lr_ace_adaptive",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.backend.runtime_enabled is False
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True
    assert result.variational_result is not None

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    adaptive = payload["variational_result"]["ansatz"]["lr_ace"]["adaptive"]
    assert adaptive["enabled"] is True
    assert adaptive["best_exact_error_hartree"] < 1.6e-3
    assert adaptive["uncompressed_check_triggered"] is True
    assert adaptive["trust_label"] in {
        "passed_exact_reference",
        "passed_compressed_with_budget",
        "compression_limited",
    }


@pytest.mark.integration
@pytest.mark.stress
def test_h3plus_adaptive_lr_ace_runs_uncompressed_reference_gate(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h3plus_lr_ace_adaptive.yaml",
        output_dir=tmp_path / "h3plus_lr_ace_adaptive",
        exploratory_command=True,
    )

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    adaptive = payload["variational_result"]["ansatz"]["lr_ace"]["adaptive"]

    assert result.backend.runtime_enabled is False
    assert adaptive["best_exact_error_hartree"] < 1.6e-3
    assert adaptive["uncompressed_check_triggered"] is True
    assert adaptive["combined_error_vs_uncompressed_exact_hartree"] < 1.6e-3
    assert adaptive["trust_label"] == "passed_exact_reference"


def test_h4_chain_adaptive_config_is_local_and_submission_guarded() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "exploratory" / "h4_chain_lr_ace_adaptive.yaml")

    assert spec.solver.kind == "lr_ace"
    assert spec.solver.lr_ace_adaptive.enabled is True
    assert spec.solver.lr_ace_adaptive.candidate_pool_policy == "residual_guided"
    assert spec.solver.lr_ace_adaptive.candidate_scan_limit == 64
    assert spec.solver.lr_ace_adaptive.residual_batch_size == 8
    assert spec.solver.lr_ace_adaptive.max_adaptive_expansions == 3
    assert spec.backend.runtime.enabled is False
    assert spec.problem.compression.term_budget_policy == "precision_first"
    assert spec.problem.compression.allow_pauli_truncation is False


@pytest.mark.integration
@pytest.mark.stress
def test_h4_chain_adaptive_lr_ace_improves_or_flags_ansatz_limit(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h4_chain_lr_ace_adaptive.yaml",
        output_dir=tmp_path / "h4_chain_lr_ace_adaptive",
        exploratory_command=True,
    )

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    adaptive = payload["variational_result"]["ansatz"]["lr_ace"]["adaptive"]
    best_error = adaptive["best_exact_error_hartree"]

    assert result.backend.runtime_enabled is False
    assert adaptive["candidate_pool_policy"] == "residual_guided"
    assert best_error < 6.6e-3
    if best_error <= adaptive["target_error_hartree"]:
        assert adaptive["trust_label"] == "passed_exact_reference"
    else:
        assert adaptive["trust_label"] == "ansatz_limited"
        assert adaptive["expansions"]
