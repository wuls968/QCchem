from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_audit import run_release_audit


def _write_release_fixture(root: Path) -> None:
    (root / "pyproject.toml").write_text('[project]\nversion = "0.1.0a1"\n', encoding="utf-8")
    (root / "README.md").write_text(
        "QFT LR-ACE TC-QSCI finite-cutoff exploratory boundary release audit",
        encoding="utf-8",
    )
    docs = root / "docs"
    docs.mkdir()
    for name in ("verified_scope.md", "release_showcase.md"):
        (docs / name).write_text(
            "QFT LR-ACE TC-QSCI finite-cutoff exploratory boundary release audit",
            encoding="utf-8",
        )
    configs = root / "configs" / "exploratory"
    configs.mkdir(parents=True)
    (configs / "h2_4site_lattice_qed_sparse_exact.yaml").write_text(
        "problem:\n  qft:\n    enabled: true\nsolver:\n  kind: lattice_qed_sparse_exact\n",
        encoding="utf-8",
    )
    (configs / "h2_lr_ace.yaml").write_text("solver:\n  kind: lr_ace\n", encoding="utf-8")
    (configs / "h2_tc_qsci.yaml").write_text(
        "exploratory:\n  modules: [tc_qsci]\ntc_qsci:\n  enabled: true\n",
        encoding="utf-8",
    )


def _write_artifact(path: Path, *, algorithm: str = "core", trust_tier: str = "exploratory") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verification_status": trust_tier,
        "module_origin": "exploratory" if trust_tier == "exploratory" else "core",
        "hardware_verified": False,
        "scientific_risk_notes": ["finite-cutoff exploratory boundary"],
        "evidence_summary": {
            "trust_tier": trust_tier,
            "recommended_action": "collect_stronger_baseline",
            "primary_baseline": {
                "baseline_kind": "exact",
                "baseline_source": "exact_diagonalization",
                "baseline_scope": "single_run",
                "baseline_strength": "strong",
            },
            "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0},
        },
    }
    if algorithm == "qft":
        payload["qft_model"] = {"model": "lattice_qed_minimal_coupling", "engine": {"actual_representation": "sparse_projected"}}
    elif algorithm == "tc_qsci":
        payload["tc_qsci_result"] = {"algorithm_name": "TC-kicked QSCI"}
    elif algorithm == "lr_ace":
        payload["variational_result"] = {"ansatz": {"lr_ace": {"algorithm_name": "LR-ACE"}}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_config(root: Path, *, artifact: Path, algorithm: str = "qft") -> Path:
    config = root / "release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts:
    - name: core_anchor
      path: {artifact.relative_to(root)}
      required: true
  exploratory_assets:
    - name: {algorithm}_asset
      kind: {algorithm}
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      artifact: {artifact.relative_to(root)}
      required: true
  required_docs:
    - path: README.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/verified_scope.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/release_showcase.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
""",
        encoding="utf-8",
    )
    return config


def test_release_audit_config_parses_defaults_and_paths(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    config = _write_config(tmp_path, artifact=artifact)

    spec = load_release_audit_spec(config)

    assert spec.profile == "trust_first"
    assert spec.release_version == "0.1.0a1"
    assert spec.curated_artifacts[0].name == "core_anchor"
    assert spec.exploratory_assets[0].kind == "qft"
    assert spec.required_docs[0].terms[-1] == "release audit"
    assert spec.source_path == config


def test_release_audit_config_rejects_invalid_profile_and_version(tmp_path: Path) -> None:
    config = tmp_path / "bad_release_audit.yaml"
    config.write_text(
        """
release_audit:
  profile: anything_goes
  release_version: 1.0.0
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="release_audit.profile"):
        load_release_audit_spec(config)

    config.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 1.0.0
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="release_audit.release_version"):
        load_release_audit_spec(config)


def test_release_audit_fails_missing_evidence_fields(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "bad" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"verification_status": "exploratory", "evidence_summary": {"trust_tier": "exploratory"}}),
        encoding="utf-8",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    assert summary["status"] == "failed"
    failed_ids = {check["id"] for check in summary["checks"] if check["status"] == "failed"}
    assert "curated_artifact:core_anchor:evidence_summary" in failed_ids
    assert summary["required_fail_count"] > 0
    assert (tmp_path / "out" / "release_readiness.json").exists()
    assert (tmp_path / "out" / "release_readiness.md").exists()


@pytest.mark.parametrize("algorithm", ["qft", "lr_ace", "tc_qsci"])
def test_release_audit_rejects_exploratory_assets_marked_validated(tmp_path: Path, algorithm: str) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / algorithm / "result.json"
    _write_artifact(artifact, algorithm=algorithm, trust_tier="validated")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, algorithm=algorithm))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    failed_ids = {check["id"] for check in summary["checks"] if check["status"] == "failed"}
    assert f"exploratory_asset:{algorithm}_asset:boundary" in failed_ids


def test_release_audit_rejects_runtime_preview_marked_hardware_verified(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "runtime_preview" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["hardware_verified"] = True
    payload["runtime_submission"] = {"attempted": True, "submitted": False, "failure_category": "runtime_submission_disabled"}
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    failed_ids = {check["id"] for check in summary["checks"] if check["status"] == "failed"}
    assert "curated_artifact:core_anchor:runtime_boundary" in failed_ids


def test_release_audit_reports_missing_doc_terms(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    (tmp_path / "README.md").write_text("QFT only", encoding="utf-8")
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    readme_check = next(check for check in summary["checks"] if check["id"] == "doc:README.md:terms")
    assert readme_check["status"] == "failed"
    assert "TC-QSCI" in readme_check["details"]["missing_terms"]
