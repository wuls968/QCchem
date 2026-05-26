from __future__ import annotations

from pathlib import Path

from qcchem.io.objective_config import load_research_objective, write_objective_template


def test_write_and_load_research_objective_template(tmp_path: Path) -> None:
    path = tmp_path / "objective.yaml"

    written = write_objective_template(
        name="h2_local_validation",
        claim="H2 local workflow stays inside chemical accuracy against exact baseline.",
        output_path=path,
    )
    spec = load_research_objective(written)

    assert written == path
    assert spec.name == "h2_local_validation"
    assert spec.claim.startswith("H2 local workflow")
    assert "evidence_summary_complete" in spec.required_evidence
    assert spec.outputs["artifact_root"].endswith("h2_local_validation")
