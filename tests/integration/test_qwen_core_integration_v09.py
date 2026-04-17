from pathlib import Path

from qcchem.workflow.runner import run_from_config


def test_run_result_contains_policy_and_reduction_plan() -> None:
    result = run_from_config(Path("/Users/a0000/QCchem/configs/lih_active_vqe.yaml"))

    assert result.policy_engine is not None
    assert result.reduction_plan is not None
    assert result.chemical_accuracy is not None
    assert result.policy_engine.policy_name == "benchmark"


def test_report_mentions_validation_boundary_and_chemical_accuracy(tmp_path: Path) -> None:
    result = run_from_config(
        Path("/Users/a0000/QCchem/configs/h2.yaml"),
        output_dir=tmp_path / "h2_core",
    )
    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")

    assert "Validation Boundary" in report_text
    assert "Chemical Accuracy" in report_text
