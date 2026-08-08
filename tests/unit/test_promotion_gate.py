from __future__ import annotations

import json
from pathlib import Path

from qcchem.workflow.promotion import review_exploratory_promotion


def _write_lr_ace(root: Path) -> Path:
    root.mkdir(parents=True)
    path = root / "result.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.result.v0.8-alpha",
                "run_id": "h2_lr_ace",
                "verification_status": "exploratory",
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "problem": {"molecule_name": "H2"},
                "energy": {"total_energy": -1.0},
                "benchmark": {"absolute_error": 0.001},
                "variational_result": {"ansatz": {"lr_ace": {"rank": 2}}},
                "evidence_summary": {
                    "trust_tier": "exploratory",
                    "recommended_action": "collect_stronger_baseline",
                    "chemical_accuracy_status": "met",
                    "runtime_evidence_status": "none",
                    "primary_baseline": {"baseline_strength": "strong"},
                    "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.001},
                    "primary_scientific_claim": "LR-ACE local exploratory evidence.",
                    "result_identity": {"artifact_kind": "run"},
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_promotion_gate_blocks_exploratory_direct_validated_promotion(tmp_path: Path) -> None:
    artifact = _write_lr_ace(tmp_path / "h2_lr_ace")

    review = review_exploratory_promotion(
        artifact=artifact,
        target="validated_algorithm_candidate",
    )

    assert review["schema_version"] == "qcchem.promotion_gate.v0.1-alpha"
    assert review["status"] == "blocked"
    assert review["module_origin"] == "lr_ace"
    assert "multiple molecules" in " ".join(review["required_studies"]).lower()
    assert "publication-grade general method" not in review["safe_claim"].lower()
