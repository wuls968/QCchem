from __future__ import annotations

import json
from pathlib import Path

from qcchem.core.evidence_capsule import validate_evidence_capsule


def _write_run(root: Path, *, trust_tier: str = "validated", include_evidence: bool = True) -> None:
    root.mkdir(parents=True)
    (root / "report.md").write_text("# report\n", encoding="utf-8")
    (root / "resolved_config.yaml").write_text("run: {}\n", encoding="utf-8")
    (root / "run.log").write_text("ok\n", encoding="utf-8")
    payload = {
        "schema_version": "qcchem.result.v0.8-alpha",
        "run_id": root.name,
        "verification_status": trust_tier,
        "problem": {"molecule_name": "H2"},
        "energy": {"total_energy": -1.1},
        "benchmark": {"absolute_error": 0.0},
        "mapping": {"kind": "jw"},
        "backend": {"kind": "statevector"},
        "provenance": {"created_by": "test"},
        "artifacts": {"root": str(root)},
    }
    if include_evidence:
        payload["evidence_summary"] = {
            "result_identity": {"artifact_kind": "run"},
            "primary_scientific_claim": "H2 is locally validated.",
            "primary_baseline": {"baseline_strength": "strong"},
            "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0},
            "chemical_accuracy_status": "met",
            "runtime_evidence_status": "none",
            "trust_tier": trust_tier,
            "recommended_action": "promote_validated_result",
        }
    (root / "result.json").write_text(json.dumps(payload), encoding="utf-8")


def test_validate_evidence_capsule_complete_run(tmp_path: Path) -> None:
    _write_run(tmp_path / "h2")

    capsule = validate_evidence_capsule(tmp_path / "h2")

    assert capsule["schema_version"] == "qcchem.evidence_capsule.v0.1-alpha"
    assert capsule["capsule_status"] == "complete"
    assert capsule["artifact_kind"] == "run"
    assert capsule["evidence_summary_status"] == "complete"
    assert capsule["provenance_status"] == "complete"
    assert capsule["blocking_issues"] == []


def test_validate_evidence_capsule_flags_missing_summary(tmp_path: Path) -> None:
    _write_run(tmp_path / "bad", include_evidence=False)

    capsule = validate_evidence_capsule(tmp_path / "bad")

    assert capsule["capsule_status"] == "partial"
    assert capsule["evidence_summary_status"] == "missing"
    assert "evidence_summary" in " ".join(capsule["blocking_issues"])
