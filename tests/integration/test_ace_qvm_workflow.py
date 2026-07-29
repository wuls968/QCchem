from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from qcchem.cli.main import main
from qcchem.workflow.runner import run_from_config


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_standard_run_rejects_ace_qvm_without_exploratory_opt_in(tmp_path: Path) -> None:
    config = tmp_path / "h2_ace_qvm_no_opt_in.yaml"
    config.write_text(
        dedent(
            """
            molecule:
              name: H2-ace-qvm-no-opt-in
              geometry:
                - {symbol: H, coords: [0.0, 0.0, 0.0]}
                - {symbol: H, coords: [0.0, 0.0, 0.74]}

            mapping:
              kind: parity_two_qubit_reduction

            backend:
              kind: ace_qvm

            solver:
              kind: vqe
              optimizer:
                kind: COBYLA
                maxiter: 1

            run:
              output_dir: artifacts/h2_ace_qvm_no_opt_in
              overwrite: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    exit_code = main(["run", "-c", str(config), "-o", str(tmp_path / "out")])

    assert exit_code == 2


@pytest.mark.integration
def test_standard_run_accepts_ace_qvm_with_policy_opt_in(tmp_path: Path) -> None:
    exit_code = main(
        [
            "run",
            "-c",
            str(REPO_ROOT / "configs" / "exploratory" / "h2_ace_qvm_lr_ace.yaml"),
            "-o",
            str(tmp_path / "h2_ace_qvm_policy_opt_in"),
        ]
    )

    assert exit_code == 0
    payload = json.loads((tmp_path / "h2_ace_qvm_policy_opt_in" / "result.json").read_text(encoding="utf-8"))
    assert payload["verification_status"] == "exploratory"
    assert payload["backend"]["kind"] == "ace_qvm"
    assert payload["hardware_verified"] is False


@pytest.mark.integration
def test_h2_ace_qvm_lr_ace_writes_exploratory_evidence(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "exploratory" / "h2_ace_qvm_lr_ace.yaml",
        output_dir=tmp_path / "h2_ace_qvm_lr_ace",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.module_origin == "exploratory"
    assert result.capability_tier == "exploratory"
    assert result.hardware_verified is False
    assert result.variational_result is not None
    assert result.backend.metadata["ace_qvm"]["algorithm_name"] == "ACE-QVM"

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    ace_qvm = payload["backend"]["metadata"]["ace_qvm"]
    assert ace_qvm["ledger"]["capacity_status"] == "within_budget"
    assert ace_qvm["memory_report"]["within_memory_budget"] is True
    assert ace_qvm["memory_report"]["max_observed_memory_bytes"] == ace_qvm["ledger"]["max_observed_memory_bytes"]
    assert payload["evidence_summary"]["trust_tier"] == "exploratory"
    assert payload["evidence_summary"]["trust_judgment"]["ace_qvm"]["algorithm_name"] == "ACE-QVM"

    quantum_evidence = json.loads(result.artifacts.quantum_evidence_json.read_text(encoding="utf-8"))
    assert quantum_evidence["ace_qvm"]["algorithm_name"] == "ACE-QVM"
    assert quantum_evidence["resources"]["ace_qvm"]["ledger"]["capacity_status"] == "within_budget"
    assert quantum_evidence["resources"]["ace_qvm"]["memory_report"]["within_memory_budget"] is True
    assert quantum_evidence["error_budget"]["ace_qvm"]["available"] is True
    assert quantum_evidence["error_budget"]["ace_qvm"]["within_memory_budget"] is True
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "ACE-QVM Compression Ledger" in report
    assert "memory_report" in report
