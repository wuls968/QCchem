from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config
from qcchem.io.config import load_run_spec

REPO_ROOT = Path(__file__).resolve().parents[2]


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
@pytest.mark.slow
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
@pytest.mark.slow
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
