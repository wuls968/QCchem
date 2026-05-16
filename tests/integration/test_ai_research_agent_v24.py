from __future__ import annotations

import json
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from qcchem.cli.main import main
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json
from qcchem.workflow.ai_store import read_ticket_record, workspace_root, write_ticket_record
from qcchem.workflow.ai_workspace import run_ticket
from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_hardware_campaign(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "hardware_calibration_summary.json"
    path.write_text(
        json.dumps(
            {
                "suite_name": "h2_hardware_campaign",
                "summary": {
                    "total_cases": 1,
                    "runtime_evidence_status_counts": {"retrieved_result": 1},
                    "hardware_verified_cases": ["h2_runtime_probe"],
                },
                "cases": [
                    {
                        "name": "h2_runtime_probe",
                        "achieved_error": 0.012,
                        "meets_chemical_accuracy": False,
                        "runtime_evidence_status": "retrieved_result",
                        "hardware_verified": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _install_fake_runtime_module(monkeypatch: pytest.MonkeyPatch, *, evs: list[float]) -> None:
    fake_runtime_module = types.ModuleType("qiskit_ibm_runtime")

    class _FakeJob:
        usage_estimation = {"quantum_seconds": 12}

        def status(self):
            return "DONE"

        def result(self):
            return [
                SimpleNamespace(
                    data=SimpleNamespace(
                        evs=np.asarray(evs, dtype=float),
                        stds=np.asarray([1.0e-4], dtype=float),
                    ),
                    metadata={"shots": 1024},
                )
            ]

        def metrics(self):
            return {"usage": {"seconds": 12, "quantum_seconds": 12}}

    class _FakeService:
        def job(self, job_id: str):
            assert job_id == "job-collect"
            return _FakeJob()

    fake_runtime_module.QiskitRuntimeService = _FakeService
    monkeypatch.setitem(__import__("sys").modules, "qiskit_ibm_runtime", fake_runtime_module)


def test_ai_summarize_evidence_cli_writes_evidence_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = _write_hardware_campaign(tmp_path / "hardware")
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "evidence.json"

    exit_code = main(["ai", "summarize-evidence", "--artifact", str(artifact), "-o", str(output)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["best_runtime_evidence"]["artifact_kind"] == "hardware_campaign"
    assert output.exists()
    assert (tmp_path / "artifacts" / "ai_workspace" / "provenance" / "ai_provenance.jsonl").exists()


def test_ai_review_cli_writes_findings_for_overclaim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = _write_hardware_campaign(tmp_path / "hardware")
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "review"

    exit_code = main(
        [
            "ai",
            "review",
            "--target",
            str(artifact),
            "--claim",
            "This hardware_verified result is publication-grade chemical accuracy evidence.",
            "-o",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "failed"
    assert (output_dir / "review_findings.json").exists()
    assert (output_dir / "review_findings.md").exists()


def test_accepted_ai_ticket_runs_compare_artifacts_action(tmp_path: Path) -> None:
    artifact = _write_hardware_campaign(tmp_path / "workspace" / "artifacts" / "hardware")
    root = workspace_root(tmp_path / "workspace")
    ticket_path = write_ticket_record(
        root,
        {
            "task_id": "analysis-compare-001",
            "task_type": "analysis",
            "title": "Compare hardware evidence",
            "request_text": "Compare linked hardware evidence without overclaiming.",
            "linked_artifacts": [str(artifact)],
            "status": "accepted",
            "execution_target": "analysis_only_assistant",
            "action_plan": {
                "action_id": "action-compare",
                "action_kind": "compare_artifacts",
                "title": "Compare Artifacts",
                "rationale": "Compare evidence summaries.",
                "inputs": {"artifacts": [str(artifact)]},
                "allowed": True,
            },
            "risk_assessment": {"is_high_risk": False, "risk_tier": "standard", "reasons": []},
        },
    )

    result = run_ticket(ticket_path)

    assert result["status"] == "completed"
    assert result["delivery_kind"] == "analysis_note"
    assert Path(result["summary_json"]).exists()
    assert read_ticket_record(ticket_path)["status"] == "completed"


def test_ai_ticket_blocks_hardware_submit_action(tmp_path: Path) -> None:
    root = workspace_root(tmp_path)
    ticket_path = write_ticket_record(
        root,
        {
            "task_id": "execution-block-001",
            "task_type": "execution",
            "title": "Submit hardware job",
            "request_text": "Submit this to real hardware.",
            "linked_artifacts": [],
            "status": "accepted",
            "execution_target": "qcchem_agent_protocol",
            "action_plan": {
                "action_id": "action-submit",
                "action_kind": "hardware_optimize_submit",
                "title": "Submit Hardware",
                "rationale": "Should be blocked.",
                "inputs": {},
                "allowed": False,
                "blocked_reason": "Real hardware submit is blocked.",
            },
            "risk_assessment": {"is_high_risk": True, "risk_tier": "high", "reasons": ["hardware"]},
        },
    )

    with pytest.raises(PermissionError, match="blocked"):
        run_ticket(ticket_path)

    assert read_ticket_record(ticket_path)["status"] == "blocked"


def test_ai_ticket_runtime_collect_requires_confirmed_existing_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "workspace" / "artifacts" / "h2_collect",
    )
    payload = to_primitive(result)
    runtime_submission = {
        "attempted": True,
        "submitted": True,
        "succeeded": False,
        "service": "ibm_quantum_platform",
        "mode": "backend",
        "session_requested": True,
        "batch_requested": False,
        "options_snapshot": {"precision_target": 0.02},
        "job_id": "job-collect",
        "backend_name": "ibm_kingston",
        "provider": "QiskitRuntimeService",
        "returned_job_metadata": {},
        "usage_estimation": {},
        "job_metrics": {},
        "result_provenance": {"attempt_stage": "submitted"},
        "verification_status": "exploratory",
    }
    payload["runtime_submission"] = runtime_submission
    payload["hardware_verified"] = False
    payload["runtime_chemical_accuracy"] = None
    write_result_json(payload, result.artifacts.result_json)
    write_result_json(runtime_submission, result.artifacts.runtime_submission_json)

    exact_total = float(payload["exact_baseline"]["total_energy"])
    constant = float(payload["energy"]["constant_energy_correction"])
    nuclear = float(payload["energy"]["nuclear_repulsion_energy"])
    _install_fake_runtime_module(monkeypatch, evs=[exact_total - constant - nuclear])

    root = workspace_root(tmp_path / "workspace")
    ticket_path = write_ticket_record(
        root,
        {
            "task_id": "runtime-collect-001",
            "task_type": "execution",
            "title": "Collect runtime result",
            "request_text": "Collect the existing runtime job.",
            "linked_artifacts": [str(result.artifacts.root)],
            "status": "accepted",
            "execution_target": "qcchem_agent_protocol",
            "action_plan": {
                "action_id": "action-runtime-collect",
                "action_kind": "runtime_collect",
                "title": "Runtime Collect",
                "rationale": "Collect existing job only.",
                "inputs": {
                    "artifact_root": str(result.artifacts.root),
                    "confirm_runtime_collect": True,
                },
                "allowed": True,
            },
            "risk_assessment": {
                "is_high_risk": True,
                "risk_tier": "high",
                "confirmed_high_risk": True,
                "reasons": ["runtime_collect"],
            },
        },
    )

    executed = run_ticket(ticket_path)

    assert executed["status"] == "completed"
    updated = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert updated["hardware_verified"] is True
    assert updated["runtime_submission"]["succeeded"] is True
