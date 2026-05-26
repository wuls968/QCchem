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


def test_release_audit_runs_research_os_optional_checks(tmp_path: Path) -> None:
    spec = load_release_audit_spec(Path("configs/release/trust_first_audit.yaml"))
    summary = run_release_audit(spec, repo_root=Path.cwd(), output_dir=tmp_path / "audit")
    check_ids = {check["id"] for check in summary["checks"]}

    assert "research_os:examples_exist" in check_ids
    assert "research_os:cli_commands_importable" in check_ids
    assert "research_os:promotion_gate_blocks_exploratory" in check_ids
