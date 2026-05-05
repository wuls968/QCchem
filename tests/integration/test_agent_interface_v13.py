from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.cli.main import main
from qcchem.io.agent_config import load_agent_task_spec
from qcchem.workflow.agent import run_agent_task_from_config, summarize_agent_target


def test_load_agent_task_spec_reads_runtime_collect_task(tmp_path: Path) -> None:
    task_path = tmp_path / "runtime_collect.yaml"
    task_path.write_text(
        "\n".join(
            [
                "agent_task:",
                "  version: 1",
                "  name: collect_h2",
                "  kind: runtime_collect",
                "  description: Collect one runtime artifact.",
                "  inputs:",
                "    artifact_root: artifacts/h2_runtime_hardware_probe_ca_layout",
                "  outputs:",
                "    summary_json: artifacts/agent/collect_h2.json",
            ]
        ),
        encoding="utf-8",
    )

    spec = load_agent_task_spec(task_path)

    assert spec.name == "collect_h2"
    assert spec.kind == "runtime_collect"
    assert spec.inputs["artifact_root"] == "artifacts/h2_runtime_hardware_probe_ca_layout"


def test_run_agent_task_executes_runtime_collect(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    task_path = tmp_path / "runtime_collect.yaml"
    task_path.write_text(
        "\n".join(
            [
                "agent_task:",
                "  version: 1",
                "  name: collect_h2",
                "  kind: runtime_collect",
                "  inputs:",
                "    artifact_root: artifacts/h2_runtime_hardware_probe_ca_layout",
            ]
        ),
        encoding="utf-8",
    )

    def _fake_collect_runtime_artifact(artifact_root: Path) -> dict[str, object]:
        assert artifact_root == (Path("/Users/a0000/QCchem") / "artifacts/h2_runtime_hardware_probe_ca_layout")
        return {
            "task_kind": "runtime_collect",
            "artifact_root": str(artifact_root),
            "job_id": "job-collect",
            "status": "DONE",
            "result_updated": True,
        }

    monkeypatch.setattr("qcchem.workflow.agent.collect_runtime_artifact", _fake_collect_runtime_artifact)

    summary = run_agent_task_from_config(task_path)

    assert summary["task_name"] == "collect_h2"
    assert summary["task_kind"] == "runtime_collect"
    assert summary["status"] == "DONE"
    assert summary["result_updated"] is True


def test_summarize_agent_target_builds_hardware_campaign_summary(tmp_path: Path) -> None:
    suite_dir = tmp_path / "hardware_suite"
    suite_dir.mkdir()
    (suite_dir / "hardware_calibration_summary.json").write_text(
        json.dumps(
            {
                "suite_name": "hardware_calibration_suite_v1",
                "artifact_root": str(suite_dir),
                "summary": {
                    "total_cases": 3,
                    "runtime_evidence_status_counts": {"retrieved_result": 3},
                    "hardware_verified_cases": ["case_a", "case_b", "case_c"],
                },
                "cases": [
                    {"name": "case_a", "achieved_error": 0.174, "meets_chemical_accuracy": False},
                    {"name": "case_b", "achieved_error": 0.0137, "meets_chemical_accuracy": False},
                    {"name": "case_c", "achieved_error": 0.267, "meets_chemical_accuracy": False},
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = summarize_agent_target(suite_dir)

    assert summary["best_case"]["name"] == "case_b"
    assert summary["best_case"]["achieved_error"] == pytest.approx(0.0137)
    assert Path(summary["summary_json"]).exists()
    assert Path(summary["report_markdown"]).exists()


def test_agent_validate_task_cli_reports_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    task_path = tmp_path / "runtime_collect.yaml"
    task_path.write_text(
        "\n".join(
            [
                "agent_task:",
                "  version: 1",
                "  name: collect_h2",
                "  kind: runtime_collect",
                "  inputs:",
                "    artifact_root: artifacts/h2_runtime_hardware_probe_ca_layout",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["agent", "validate-task", str(task_path)])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Agent task is valid" in stdout
    assert "runtime_collect" in stdout


def test_agent_run_task_cli_emits_json_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_path = tmp_path / "campaign_summary.yaml"
    task_path.write_text(
        "\n".join(
            [
                "agent_task:",
                "  version: 1",
                "  name: summarize_hardware_campaign",
                "  kind: hardware_campaign_summary",
                "  inputs:",
                "    target: artifacts/hardware_calibration_suite_v1",
            ]
        ),
        encoding="utf-8",
    )

    def _fake_summarize_agent_target(target: Path) -> dict[str, object]:
        assert target == Path("/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1")
        return {
            "suite_name": "hardware_calibration_suite_v1",
            "best_case": {"name": "h2_runtime_hardware_probe_puccd_layout"},
        }

    monkeypatch.setattr("qcchem.cli.main.summarize_agent_target", _fake_summarize_agent_target)

    exit_code = main(["agent", "summarize", "/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["suite_name"] == "hardware_calibration_suite_v1"
    assert payload["best_case"]["name"] == "h2_runtime_hardware_probe_puccd_layout"
