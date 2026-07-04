from __future__ import annotations

from pathlib import Path

from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_audit import run_release_audit


def test_release_audit_manifest_tracks_research_os_docs() -> None:
    spec = load_release_audit_spec(Path("configs/release/trust_first_audit.yaml"))
    docs = {str(doc.path): set(doc.terms) for doc in spec.required_docs}

    assert "docs/research_objectives.md" in docs
    assert "research objective" in docs["docs/research_objectives.md"]
    assert "docs/evidence_capsule.md" in docs
    assert "evidence capsule" in docs["docs/evidence_capsule.md"]
    assert "docs/claim_compiler.md" in docs
    assert "claim compiler" in docs["docs/claim_compiler.md"]
    assert "docs/promotion_gate.md" in docs
    assert "promotion gate" in docs["docs/promotion_gate.md"]
    assert "docs/custom_workflows.md" in docs
    assert "workflow_result.json" in docs["docs/custom_workflows.md"]

    commands = "\n".join(spec.acceptance_commands)
    assert "test_custom_workflow_config.py" in commands
    assert "test_custom_workflow_cli.py" in commands
    assert "SparseEfficiencyWarning" in commands


def test_release_audit_runs_research_os_optional_checks(tmp_path: Path) -> None:
    spec = load_release_audit_spec(Path("configs/release/trust_first_audit.yaml"))
    summary = run_release_audit(spec, repo_root=Path.cwd(), output_dir=tmp_path / "audit")
    check_ids = {check["id"] for check in summary["checks"]}

    assert "research_os:examples_exist" in check_ids
    assert "research_os:cli_commands_importable" in check_ids
    assert "research_os:promotion_gate_blocks_exploratory" in check_ids
    assert "custom_workflows:examples_exist" in check_ids
    assert "custom_workflows:builtin_example_validates" in check_ids
    assert "custom_workflows:builtin_plugins_registered" in check_ids
    assert "custom_workflows:index_contract" in check_ids


def test_release_audit_custom_workflow_check_skips_installed_plugins(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fail_if_loaded(group: str):
        raise AssertionError(f"installed workflow plugins should not be loaded for release audit: {group}")

    monkeypatch.setattr("qcchem.workflow.workflow_plugins._entry_points_for_group", fail_if_loaded)

    spec = load_release_audit_spec(Path("configs/release/trust_first_audit.yaml"))
    summary = run_release_audit(spec, repo_root=Path.cwd(), output_dir=tmp_path / "audit")
    builtin_check = next(
        check for check in summary["checks"] if check["id"] == "custom_workflows:builtin_example_validates"
    )

    assert builtin_check["status"] == "passed"
