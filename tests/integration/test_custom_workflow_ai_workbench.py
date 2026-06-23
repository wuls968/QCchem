from __future__ import annotations

import json
from pathlib import Path

from qcchem.workflow.ai_store import workspace_root, write_ticket_record
from qcchem.workflow.ai_workspace import run_ticket


def _write_artifact(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "result.json").write_text(
        json.dumps(
            {
                "verification_status": "validated",
                "evidence_summary": {
                    "primary_scientific_claim": "Workflow AI test artifact is validated.",
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
    return root


def _write_workflow(workspace: Path) -> Path:
    artifact = _write_artifact(workspace / "artifacts" / "h2")
    workflow = workspace / "workflow.yaml"
    workflow.write_text(
        f"""
workflow:
  version: "1"
  name: ai_workflow
  output_root: {workspace / "artifacts" / "workflows" / "ai_workflow"}
  steps:
    - id: compare
      kind: compare_artifacts
      inputs:
        artifacts:
          - {artifact}
""",
        encoding="utf-8",
    )
    return workflow


def test_ai_ticket_validates_runs_and_summarizes_workflow(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workflow = _write_workflow(workspace)
    root = workspace_root(workspace)

    validate_ticket = write_ticket_record(
        root,
        {
            "task_id": "workflow-validate-001",
            "task_type": "analysis",
            "title": "Validate workflow",
            "request_text": "Validate workflow",
            "status": "accepted",
            "linked_artifacts": [str(workflow)],
            "action_plan": {
                "action_id": "action-validate",
                "action_kind": "workflow_validate",
                "inputs": {"config": str(workflow)},
                "allowed": True,
            },
        },
    )
    validated = run_ticket(validate_ticket)
    assert validated["workflow_validation"]["status"] == "valid"

    run_ticket_path = write_ticket_record(
        root,
        {
            "task_id": "workflow-run-001",
            "task_type": "execution",
            "title": "Run workflow",
            "request_text": "Run workflow",
            "status": "accepted",
            "linked_artifacts": [str(workflow)],
            "action_plan": {
                "action_id": "action-run",
                "action_kind": "workflow_run",
                "inputs": {"config": str(workflow)},
                "allowed": True,
            },
            "risk_assessment": {"is_high_risk": True, "risk_tier": "high", "reasons": ["workflow_run"]},
        },
    )
    executed = run_ticket(run_ticket_path)
    assert executed["workflow_status"] == "completed"
    result_json = Path(executed["workflow_result_json"])
    assert result_json.exists()

    summarize_ticket = write_ticket_record(
        root,
        {
            "task_id": "workflow-summary-001",
            "task_type": "analysis",
            "title": "Summarize workflow",
            "request_text": "Summarize workflow",
            "status": "accepted",
            "linked_artifacts": [str(result_json)],
            "action_plan": {
                "action_id": "action-summary",
                "action_kind": "workflow_summarize",
                "inputs": {"result_json": str(result_json)},
                "allowed": True,
            },
        },
    )
    summarized = run_ticket(summarize_ticket)
    assert summarized["workflow_summary"]["status"] == "completed"
    assert Path(summarized["workflow_report_markdown"]).exists()


def test_workflow_studio_page_is_registered() -> None:
    from qcchem.workbench.app import create_app

    app = create_app()
    paths = {page.get("path") for page in app.page_registry.values()}
    assert "/workflow-studio" in paths


def test_workflow_studio_layout_exposes_yaml_validation_and_export_controls() -> None:
    from qcchem.workbench.pages.workflow_studio import layout

    root = layout()
    found_ids: set[str] = set()

    def visit(component) -> None:
        component_id = getattr(component, "id", None)
        if isinstance(component_id, str):
            found_ids.add(component_id)
        children = getattr(component, "children", None)
        if isinstance(children, list):
            for child in children:
                visit(child)
        elif children is not None:
            visit(children)

    visit(root)

    assert "qcchem-workflow-studio-yaml" in found_ids
    assert "qcchem-workflow-studio-validation" in found_ids
    assert "qcchem-workflow-studio-export" in found_ids


def test_workflow_studio_loads_acceptance_graph_and_provenance(tmp_path: Path) -> None:
    from qcchem.workbench.pages.workflow_studio import _result_card, _workflow_results

    artifact_root = tmp_path / "artifacts" / "workflows" / "demo"
    artifact_root.mkdir(parents=True)
    (artifact_root / "workflow_result.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.workflow_run.v0.1-alpha",
                "workflow_name": "demo",
                "status": "failed",
                "artifact_root": str(artifact_root),
                "summary": {"completed_steps": 1, "failed_steps": 1, "generated_steps": 0},
                "steps": [
                    {"step_id": "first", "status": "completed"},
                    {"step_id": "second", "status": "failed"},
                ],
                "acceptance_summary": {
                    "accepted": False,
                    "recommended_action": "resolve_workflow_failures",
                    "blocking_failures": [
                        {"step_id": "second", "reason": "required_step_failed", "error": "boom"}
                    ],
                },
                "outputs": {"workflow_report_markdown": str(artifact_root / "workflow_report.md")},
            }
        ),
        encoding="utf-8",
    )
    (artifact_root / "workflow_graph.json").write_text(
        json.dumps({"nodes": [{"id": "first"}, {"id": "second"}], "edges": [{"source": "first", "target": "second"}]}),
        encoding="utf-8",
    )
    (artifact_root / "workflow_report.md").write_text("# Demo\n", encoding="utf-8")
    (artifact_root / "provenance.jsonl").write_text("{}\n{}\n", encoding="utf-8")
    (artifact_root / "registry.json").write_text("{}", encoding="utf-8")

    results = _workflow_results(tmp_path)
    assert len(results) == 1
    result = results[0]
    assert result["accepted"] is False
    assert result["recommended_action"] == "resolve_workflow_failures"
    assert result["blocking_failure_count"] == 1
    assert result["first_blocking_failure"] == "second: required_step_failed - boom"
    assert result["step_status_counts"] == {"completed": 1, "failed": 1}
    assert result["graph_node_count"] == 2
    assert result["graph_edge_count"] == 1
    assert result["provenance_event_count"] == 2

    card = _result_card(result)
    rendered_text: list[str] = []

    def visit(component) -> None:
        if isinstance(component, str):
            rendered_text.append(component)
            return
        children = getattr(component, "children", None)
        if isinstance(children, list):
            for child in children:
                visit(child)
        elif children is not None:
            visit(children)

    visit(card)
    text = "\n".join(rendered_text)
    assert "not accepted" in text
    assert "2 nodes / 1 edges" in text
    assert "2 events" in text
    assert "second: required_step_failed - boom" in text
    assert "sidecars: complete" in text
