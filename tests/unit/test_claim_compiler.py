from __future__ import annotations

import json
from pathlib import Path

from qcchem.workflow.claim_compiler import compile_claim_review


def _write_hardware_artifact(root: Path) -> Path:
    root.mkdir(parents=True)
    path = root / "result.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.result.v0.8-alpha",
                "run_id": "h2_runtime",
                "verification_status": "hardware_verified",
                "hardware_verified": True,
                "runtime_submission": {"submitted": True, "succeeded": True, "job_id": "job-redacted"},
                "problem": {"molecule_name": "H2"},
                "energy": {"total_energy": -1.0},
                "benchmark": {"absolute_error": 0.02},
                "backend": {"kind": "runtime_estimator"},
                "mapping": {"kind": "jw"},
                "provenance": {"created_by": "test"},
                "evidence_summary": {
                    "result_identity": {"artifact_kind": "run"},
                    "primary_scientific_claim": "Runtime result was retrieved.",
                    "primary_baseline": {"baseline_strength": "weak"},
                    "primary_error_metric": {"metric_kind": "runtime_status", "value": "retrieved_result"},
                    "chemical_accuracy_status": "not_met",
                    "runtime_evidence_status": "retrieved_result",
                    "trust_tier": "hardware_verified",
                    "recommended_action": "review_runtime_gap",
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_claim_compiler_flags_hardware_publication_overclaim(tmp_path: Path) -> None:
    target = _write_hardware_artifact(tmp_path / "hardware")

    review = compile_claim_review(
        claim_text="hardware_verified proves publication-grade chemical accuracy",
        targets=[target],
    )

    assert review["schema_version"] == "qcchem.claim_compiler.v0.1-alpha"
    assert review["support_level"] == "overclaimed"
    assert review["status"] == "failed"
    assert review["overclaim_findings"]
    assert "runtime submission and retrieval" in review["safe_rewrite"]
    assert "chemical accuracy" in " ".join(review["required_next_evidence"])
