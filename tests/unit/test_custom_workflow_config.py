from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.io.workflow_config import load_workflow_spec, load_workflow_spec_from_text, workflow_template


def test_workflow_loader_adds_implicit_needs_from_step_references(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: implicit_needs
  output_root: out
  parameters:
    claim: local claim
  steps:
    - id: first
      kind: compare_artifacts
      inputs:
        artifacts: [artifact_a]
    - id: second
      kind: claim_check
      inputs:
        targets: ["${steps.first.outputs.summary_json}"]
        claim_text: "${parameters.claim}"
""",
        encoding="utf-8",
    )

    spec = load_workflow_spec(workflow)

    assert spec.name == "implicit_needs"
    assert spec.steps[1].needs == ["first"]
    assert spec.output_root == tmp_path / "out"


def test_workflow_loader_rejects_dependency_cycles(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: cycle
  steps:
    - id: a
      kind: compare_artifacts
      needs: [b]
    - id: b
      kind: compare_artifacts
      needs: [a]
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cycle"):
        load_workflow_spec(workflow)


def test_workflow_loader_rejects_unknown_parameters(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: bad_parameter
  steps:
    - id: a
      kind: compare_artifacts
      inputs:
        artifacts: ["${parameters.missing}"]
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown parameter"):
        load_workflow_spec(workflow)


def test_workflow_loader_rejects_self_output_reference(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: self_reference
  steps:
    - id: a
      kind: compare_artifacts
      inputs:
        artifacts: ["${steps.a.outputs.summary_json}"]
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cannot reference its own outputs"):
        load_workflow_spec(workflow)


def test_workflow_loader_rejects_unknown_acceptance_step(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: bad_acceptance
  steps:
    - id: a
      kind: compare_artifacts
      inputs:
        artifacts: [artifact_a]
  acceptance:
    required_steps: [missing]
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="required_steps references unknown step"):
        load_workflow_spec(workflow)


def test_workflow_loader_rejects_non_positive_wall_time_limit(tmp_path: Path) -> None:
    workflow = tmp_path / "workflow.yaml"
    workflow.write_text(
        """
workflow:
  version: "1"
  name: bad_limit
  limits:
    max_wall_time_seconds: 0
  steps:
    - id: a
      kind: compare_artifacts
      inputs:
        artifacts: [artifact_a]
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="max_wall_time_seconds"):
        load_workflow_spec(workflow)


def test_workflow_loader_validates_editor_buffer_with_source_path(tmp_path: Path) -> None:
    spec = load_workflow_spec_from_text(
        """
workflow:
  version: "1"
  name: editor_buffer
  output_root: out
  steps:
    - id: compare
      kind: compare_artifacts
      inputs:
        artifacts: [artifact_a]
""",
        source_path=tmp_path / "studio" / "workflow.yaml",
    )

    assert spec.name == "editor_buffer"
    assert spec.source_path == tmp_path / "studio" / "workflow.yaml"
    assert spec.output_root == tmp_path / "studio" / "out"


def test_workflow_template_paths_are_relative_to_target_file(tmp_path: Path) -> None:
    source_path = tmp_path / "examples" / "workflows" / "local_workflow.yaml"

    template = workflow_template(source_path=source_path, workspace_root=tmp_path)
    workflow = template["workflow"]

    assert workflow["output_root"] == "../../artifacts/workflows/h2_trust_first_workflow"
    assert workflow["steps"][0]["inputs"]["config"] == "../../configs/h2_exact.yaml"
