from __future__ import annotations

import json
from pathlib import Path

from qcchem.workflow.objective import plan_research_objective, status_research_objective


def _write_objective(path: Path, config: Path, artifact: Path) -> None:
    path.write_text(
        f"""
research_objective:
  name: h2_local_validation
  title: H2 local validation
  claim: H2 local workflow stays inside chemical accuracy against exact baseline.
  system_scope:
    molecule: H2
    basis: sto3g
    hardware_scope: preview_only
  required_evidence:
    - exact_active_space_baseline
    - evidence_summary_complete
  candidate_configs:
    - {config}
  linked_artifacts:
    - {artifact}
  outputs:
    artifact_root: artifacts/objectives/h2_local_validation
""".strip(),
        encoding="utf-8",
    )


def _write_artifact(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "report.md").write_text("# report\n", encoding="utf-8")
    (root / "run.log").write_text("ok\n", encoding="utf-8")
    (root / "resolved_config.yaml").write_text("run: {}\n", encoding="utf-8")
    result = root / "result.json"
    result.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.result.v0.8-alpha",
                "run_id": "h2",
                "verification_status": "validated",
                "problem": {"molecule_name": "H2", "basis": "sto3g"},
                "energy": {"total_energy": -1.1},
                "benchmark": {"absolute_error": 0.0001},
                "mapping": {"kind": "jordan_wigner"},
                "backend": {"kind": "statevector"},
                "provenance": {"created_by": "test"},
                "artifacts": {"root": str(root)},
                "evidence_summary": {
                    "result_identity": {"artifact_kind": "run"},
                    "primary_scientific_claim": "H2 local workflow stays inside chemical accuracy.",
                    "primary_baseline": {"baseline_strength": "strong"},
                    "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0001},
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


def test_objective_plan_and_status_write_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "configs" / "h2.yaml"
    config.parent.mkdir()
    config.write_text("run: {}\n", encoding="utf-8")
    artifact = _write_artifact(tmp_path / "artifacts" / "h2")
    objective = tmp_path / "objective.yaml"
    _write_objective(objective, config, artifact)

    plan = plan_research_objective(objective, tmp_path / "plan")
    status = status_research_objective(objective, tmp_path / "status")

    assert plan["status"] == "planned"
    assert plan["missing_evidence"] == []
    assert (tmp_path / "plan" / "objective_plan.json").exists()
    assert (tmp_path / "plan" / "objective_plan.md").exists()
    artifact_root_status = status_research_objective(tmp_path / "plan", tmp_path / "status_from_root")
    assert artifact_root_status["objective_name"] == "h2_local_validation"
    assert (tmp_path / "status_from_root" / "objective_status.json").exists()
    assert status["status"] == "ready_for_review"
    assert status["claim_review"]["support_level"] == "supported"
    assert (tmp_path / "status" / "objective_status.json").exists()
    assert (tmp_path / "status" / "objective_status.md").exists()
