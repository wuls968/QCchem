from pathlib import Path

from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_run_result_contains_policy_and_reduction_plan() -> None:
    result = run_from_config(REPO_ROOT / "configs" / "lih_active_vqe.yaml")

    assert result.policy_engine is not None
    assert result.reduction_plan is not None
    assert result.chemical_accuracy is not None
    assert result.policy_engine.policy_name == "benchmark"


def test_report_mentions_validation_boundary_and_chemical_accuracy(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2.yaml",
        output_dir=tmp_path / "h2_core",
    )
    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")

    assert "Validation Boundary" in report_text
    assert "Chemical Accuracy" in report_text


def test_exploratory_report_declares_boundary(tmp_path: Path) -> None:
    config = tmp_path / "exploratory.yaml"
    config.write_text(
        """
        molecule:
          name: H2
          geometry:
            - {symbol: H, coords: [0.0, 0.0, 0.0]}
            - {symbol: H, coords: [0.0, 0.0, 0.74]}
        solver:
          kind: vqd
          experimental: true
          optimizer:
            kind: COBYLA
            maxiter: 20
          ansatz:
            kind: uccsd
            reps: 1
        policy:
          name: benchmark
          allow_exploratory: true
        exploratory:
          enabled: true
          modules: ["solvers.vqd"]
        run:
          overwrite: true
        """,
        encoding="utf-8",
    )
    result = run_from_config(config, output_dir=tmp_path / "exploratory_report")
    text = result.artifacts.report_markdown.read_text(encoding="utf-8")

    assert "Validation Boundary" in text
    assert "Module Origin" in text or "module_origin" in text
    assert "exploratory" in text
