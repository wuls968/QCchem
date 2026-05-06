from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from qcchem.cli.main import main
from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_audit import classify_exploratory_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_minimal_release_tree(root: Path, *, bad_artifact: bool = False) -> Path:
    (root / "pyproject.toml").write_text('[project]\nversion = "0.1.0a1"\n', encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    for path in [root / "README.md", docs / "verified_scope.md", docs / "release_showcase.md"]:
        path.write_text(
            "QFT LR-ACE TC-QSCI finite-cutoff exploratory boundary release audit",
            encoding="utf-8",
        )
    config_dir = root / "configs" / "exploratory"
    config_dir.mkdir(parents=True)
    (config_dir / "h2_4site_lattice_qed_sparse_exact.yaml").write_text("problem:\n  qft:\n    enabled: true\n", encoding="utf-8")

    artifact = root / "artifacts" / "qft" / "result.json"
    artifact.parent.mkdir(parents=True)
    evidence = {
        "trust_tier": "exploratory",
        "recommended_action": "collect_stronger_baseline",
        "primary_baseline": {"baseline_kind": "exact", "baseline_strength": "strong"},
        "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0},
    }
    if bad_artifact:
        evidence.pop("recommended_action")
    artifact.write_text(
        json.dumps(
            {
                "verification_status": "exploratory",
                "module_origin": "exploratory",
                "scientific_risk_notes": ["finite-cutoff"],
                "evidence_summary": evidence,
                "qft_model": {"engine": {"actual_representation": "sparse_projected"}},
            }
        ),
        encoding="utf-8",
    )

    manifest = root / "configs" / "release" / "trust_first_audit.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts:
    - name: qft_anchor
      path: artifacts/qft/result.json
      required: true
  exploratory_assets:
    - name: qft_sparse
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      artifact: artifacts/qft/result.json
      required: true
  required_docs:
    - path: README.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/verified_scope.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/release_showcase.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
""",
        encoding="utf-8",
    )
    return manifest


@pytest.mark.integration
def test_release_audit_cli_writes_pass_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    assert exit_code == 0
    summary = json.loads((output_dir / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "passed"
    assert summary["required_fail_count"] == 0
    assert "Release audit completed: passed" in capsys.readouterr().out
    assert "release_readiness.md" in (output_dir / "release_readiness.md").read_text(encoding="utf-8")


@pytest.mark.integration
def test_release_audit_cli_returns_two_for_failed_required_check(tmp_path: Path) -> None:
    manifest = _write_minimal_release_tree(tmp_path, bad_artifact=True)
    output_dir = tmp_path / "release_audit_failed"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    assert exit_code == 2
    summary = json.loads((output_dir / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["required_fail_count"] > 0


@pytest.mark.integration
def test_real_exploratory_configs_are_classified_for_release_manifest() -> None:
    expected = {
        "configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml": "qft",
        "configs/exploratory/h2_lr_ace.yaml": "lr_ace",
        "configs/exploratory/h2_tc_qsci.yaml": "tc_qsci",
    }

    for relative_path, kind in expected.items():
        assert classify_exploratory_config(REPO_ROOT / relative_path) == kind


def test_exploratory_cli_prints_evidence_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    result = SimpleNamespace(
        problem=SimpleNamespace(molecule_name="H2-QFT"),
        verification_status="exploratory",
        module_origin="exploratory",
        capability_tier="exploratory",
        evidence_summary=SimpleNamespace(
            trust_tier="exploratory",
            recommended_action="collect_stronger_baseline",
        ),
        qft_model=SimpleNamespace(engine={"actual_representation": "sparse_projected", "projected_dimension": 12}),
        tc_qsci_result={"verification_status": "exploratory", "subspace_dimension": 4},
        artifacts=SimpleNamespace(root=tmp_path),
    )

    def _fake_run_from_config(*args, **kwargs):
        assert kwargs["exploratory_command"] is True
        return result

    monkeypatch.setattr("qcchem.cli.main.run_from_config", _fake_run_from_config)

    exit_code = main(["exploratory", "run", "-c", str(tmp_path / "config.yaml")])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Trust tier: exploratory" in stdout
    assert "Recommended action: collect_stronger_baseline" in stdout
    assert "QFT engine: representation=sparse_projected, projected_dimension=12" in stdout
    assert "TC-QSCI: subspace_dimension=4" in stdout


def test_default_release_audit_manifest_loads() -> None:
    spec = load_release_audit_spec(REPO_ROOT / "configs" / "release" / "trust_first_audit.yaml")

    assert spec.profile == "trust_first"
    assert spec.release_version == "0.1.0a1"
    assert {asset.kind for asset in spec.exploratory_assets} >= {"qft", "lr_ace", "tc_qsci"}
