from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.cli.main import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_run_artifact(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    result = root / "result.json"
    result.write_text(
        json.dumps(
            {
                "run_id": "fake_h2",
                "verification_status": "validated",
                "evidence_summary": {
                    "primary_scientific_claim": "Fake H2 fixture is validated for workflow tests.",
                    "primary_baseline": {"baseline_kind": "exact", "baseline_strength": "strong"},
                    "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0},
                    "chemical_accuracy_status": "met",
                    "runtime_evidence_status": "none",
                    "trust_tier": "validated",
                    "recommended_action": "promote_validated_result",
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "report.md").write_text("# Fake H2\n", encoding="utf-8")
    (root / "resolved_config.yaml").write_text("molecule:\n  name: fake_h2\n", encoding="utf-8")
    (root / "run.log").write_text("ok\n", encoding="utf-8")
    return root


def test_workflow_cli_validate_run_report_plugins_and_template(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    artifact = _write_run_artifact(tmp_path / "artifacts" / "h2")
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        f"""
workflow:
  version: "1"
  name: cli_workflow
  output_root: {tmp_path / "workflow_out"}
  steps:
    - id: compare
      kind: compare_artifacts
      inputs:
        artifacts:
          - {artifact}
""",
        encoding="utf-8",
    )

    assert main(["workflow", "validate", "-c", str(workflow)]) == 0
    validation = json.loads(capsys.readouterr().out)
    assert validation["status"] == "valid"

    assert main(["workflow", "run", "-c", str(workflow)]) == 0
    stdout = capsys.readouterr().out
    assert "Workflow completed: cli_workflow" in stdout
    result_json = tmp_path / "workflow_out" / "workflow_result.json"
    assert result_json.exists()
    assert (tmp_path / "workflow_out" / "workflow_graph.json").exists()
    assert (tmp_path / "workflow_out" / "provenance.jsonl").exists()
    assert (tmp_path / "workflow_out" / "registry.json").exists()

    sentinel = tmp_path / "workflow_out" / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    assert main(["workflow", "run", "-c", str(workflow)]) == 2
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert "Workflow run rejected:" in capsys.readouterr().out

    assert main(["workflow", "run", "-c", str(workflow), "--overwrite"]) == 0
    assert not sentinel.exists()
    assert result_json.exists()
    capsys.readouterr()

    report = tmp_path / "workflow_report_copy.md"
    assert main(["workflow", "report", str(result_json), "-o", str(report)]) == 0
    assert report.exists()
    capsys.readouterr()

    assert main(["workflow", "plugins"]) == 0
    plugins = json.loads(capsys.readouterr().out)
    assert "run_config" in {plugin["kind"] for plugin in plugins["plugins"]}

    template = tmp_path / "template.yaml"
    assert main(["workflow", "template", "-o", str(template)]) == 0
    assert template.exists()


def test_workflow_cli_rejects_unknown_step_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workflow = tmp_path / "bad_workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: bad_workflow
  steps:
    - id: missing
      kind: missing_plugin
""",
        encoding="utf-8",
    )

    assert main(["workflow", "validate", "-c", str(workflow)]) == 2

    stdout = capsys.readouterr().out
    assert "Workflow validation rejected:" in stdout
    assert "Unsupported workflow step plugin/kind 'missing_plugin'" in stdout
    assert "Available plugins:" in stdout
    assert "claim_check" in stdout
    assert "Run 'qcchem workflow plugins' to inspect installed plugin metadata." in stdout


@pytest.mark.integration
def test_workflow_cli_runs_h2_capsule_and_claim(tmp_path: Path) -> None:
    workflow = tmp_path / "h2_workflow.yaml"
    workflow.write_text(
        f"""
workflow:
  version: "1"
  name: h2_real_workflow
  output_root: {tmp_path / "h2_workflow"}
  limits:
    max_steps: 8
  parameters:
    claim: The H2 local run is validated against an exact baseline within the configured trust boundary.
  steps:
    - id: run_h2
      kind: run_config
      inputs:
        config: {REPO_ROOT / "configs" / "h2_exact.yaml"}
    - id: capsule_h2
      kind: capsule_validate
      inputs:
        artifact_root: ${{steps.run_h2.outputs.artifact_root}}
    - id: claim_h2
      kind: claim_check
      inputs:
        targets:
          - ${{steps.run_h2.outputs.artifact_root}}
        claim_text: ${{parameters.claim}}
""",
        encoding="utf-8",
    )

    assert main(["workflow", "run", "-c", str(workflow)]) == 0
    payload = json.loads((tmp_path / "h2_workflow" / "workflow_result.json").read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert {step["step_id"] for step in payload["steps"]} == {"run_h2", "capsule_h2", "claim_h2"}
