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
