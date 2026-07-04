from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from qcchem.cli.main import main
from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_audit import classify_exploratory_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def _release_artifact_payload(*, bad_artifact: bool = False) -> dict[str, object]:
    evidence = {
        "primary_scientific_claim": "QFT fixture remains release-readable within the exploratory boundary.",
        "trust_tier": "exploratory",
        "chemical_accuracy_status": "unavailable",
        "runtime_evidence_status": "none",
        "recommended_action": "collect_stronger_baseline",
        "primary_baseline": {"baseline_kind": "exact", "baseline_strength": "strong"},
        "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0},
    }
    if bad_artifact:
        evidence.pop("recommended_action")
    return {
        "verification_status": "exploratory",
        "module_origin": "exploratory",
        "scientific_risk_notes": ["finite-cutoff"],
        "evidence_summary": evidence,
        "qft_model": {"engine": {"actual_representation": "sparse_projected"}},
    }


def _write_release_acceptance(
    artifact: Path,
    *,
    artifact_path: str,
    release_audit_check_id: str,
) -> None:
    artifact_sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (artifact.parent / "acceptance_summary.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_artifact_acceptance.v0.1-alpha",
                "artifact_path": artifact_path,
                "artifact_sha256": artifact_sha256,
                "release_audit_check_id": release_audit_check_id,
                "trust_tier": "exploratory",
                "runtime_evidence_status": "none",
                "accepted": True,
                "blocking_failures": [],
                "warnings": [],
                "recommended_action": "accept_release_artifact_with_declared_boundary",
            }
        ),
        encoding="utf-8",
    )


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
    tests_dir = root / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_release_audit_v23.py").write_text("# fixture target\n", encoding="utf-8")

    curated_artifact = root / "artifacts" / "qft" / "result.json"
    curated_artifact.parent.mkdir(parents=True)
    curated_artifact.write_text(json.dumps(_release_artifact_payload(bad_artifact=bad_artifact)), encoding="utf-8")
    _write_release_acceptance(
        curated_artifact,
        artifact_path="artifacts/qft/result.json",
        release_audit_check_id="curated_artifact:qft_anchor:acceptance_summary",
    )

    exploratory_artifact = root / "artifacts" / "qft_sparse" / "result.json"
    exploratory_artifact.parent.mkdir(parents=True)
    exploratory_artifact.write_text(
        json.dumps(_release_artifact_payload(bad_artifact=bad_artifact)),
        encoding="utf-8",
    )
    _write_release_acceptance(
        exploratory_artifact,
        artifact_path="artifacts/qft_sparse/result.json",
        release_audit_check_id="exploratory_asset:qft_sparse:acceptance_summary",
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
      artifact: artifacts/qft_sparse/result.json
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
    return manifest


@pytest.mark.integration
def test_release_audit_cli_writes_pass_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    assert exit_code == 0
    summary = json.loads((output_dir / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "passed"
    assert summary["schema_version"] == "1.1"
    assert {
        "required_failed_checks",
        "evidence_matrix_core_fields",
        "evidence_matrix_review_warnings",
        "warning_policy",
        "acceptance_commands",
        "acceptance_command_remediation",
        "acceptance_summary_source",
        "acceptance_schema_version",
        "acceptance_artifact_sha256",
        "acceptance_release_audit_check_id",
        "acceptance_runtime_evidence_status",
        "acceptance_recommended_action",
        "acceptance_contract_failure_count",
        "audit_provenance",
    }.issubset(set(summary["schema_features"]))
    assert summary["audit_provenance"]["generated_at_utc"].endswith("Z")
    assert summary["audit_provenance"]["repo_root"] == str(tmp_path.resolve())
    assert summary["audit_provenance"]["manifest_path"] == "configs/release/trust_first_audit.yaml"
    assert summary["audit_provenance"]["output_dir"] == "release_audit"
    assert summary["acceptance_commands"] == ["python -m pytest tests/unit/test_release_audit_v23.py -q"]
    assert summary["required_fail_count"] == 0
    assert summary["required_failed_checks"] == []
    assert summary["warning_checks"] == []
    assert "Release audit completed: passed" in capsys.readouterr().out
    assert "release_readiness.md" in (output_dir / "release_readiness.md").read_text(encoding="utf-8")


@pytest.mark.integration
def test_release_audit_cli_resolves_relative_manifest_against_repo_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_minimal_release_tree(tmp_path)
    outside_cwd = tmp_path / "outside"
    outside_cwd.mkdir()
    output_dir = tmp_path / "external_release_audit"
    monkeypatch.chdir(outside_cwd)

    exit_code = main(
        [
            "release",
            "audit",
            "-c",
            "configs/release/trust_first_audit.yaml",
            "-o",
            str(output_dir),
            "--repo-root",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    summary = json.loads((output_dir / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "passed"
    assert summary["acceptance_commands"] == ["python -m pytest tests/unit/test_release_audit_v23.py -q"]


@pytest.mark.integration
def test_release_audit_cli_repo_root_controls_manifest_and_default_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_minimal_release_tree(tmp_path)
    outside_cwd = tmp_path / "outside"
    shadow_manifest = outside_cwd / "configs" / "release" / "trust_first_audit.yaml"
    shadow_manifest.parent.mkdir(parents=True)
    shadow_manifest.write_text("not: the release audit manifest\n", encoding="utf-8")
    monkeypatch.chdir(outside_cwd)

    exit_code = main(
        [
            "release",
            "audit",
            "-c",
            "configs/release/trust_first_audit.yaml",
            "--repo-root",
            str(tmp_path),
        ]
    )

    expected_output = tmp_path / "artifacts" / "release_audit"
    assert exit_code == 0
    assert (expected_output / "release_readiness.json").exists()
    assert not (outside_cwd / "artifacts" / "release_audit" / "release_readiness.json").exists()
    assert f"Report: {expected_output / 'release_readiness.md'}" in capsys.readouterr().out


@pytest.mark.integration
def test_release_audit_cli_infers_repo_root_from_absolute_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    outside_cwd = tmp_path / "outside"
    outside_cwd.mkdir()
    monkeypatch.chdir(outside_cwd)

    exit_code = main(["release", "audit", "-c", str(manifest)])

    expected_output = tmp_path / "artifacts" / "release_audit"
    assert exit_code == 0
    summary = json.loads((expected_output / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "passed"
    assert summary["audit_provenance"]["repo_root"] == str(tmp_path.resolve())
    assert summary["audit_provenance"]["manifest_path"] == "configs/release/trust_first_audit.yaml"
    assert summary["audit_provenance"]["output_dir"] == "artifacts/release_audit"
    assert not (outside_cwd / "artifacts" / "release_audit" / "release_readiness.json").exists()
    assert f"Report: {expected_output / 'release_readiness.md'}" in capsys.readouterr().out


@pytest.mark.integration
def test_release_audit_cli_rejects_missing_config_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["release", "audit", "-c", str(tmp_path / "missing_release_audit.yaml")])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "Release audit rejected:" in stdout
    assert "missing_release_audit.yaml" in stdout


@pytest.mark.integration
def test_release_audit_cli_rejects_malformed_yaml_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = tmp_path / "bad_release_audit.yaml"
    manifest.write_text("release_audit: [not-closed\n", encoding="utf-8")

    exit_code = main(["release", "audit", "-c", str(manifest)])

    assert exit_code == 2
    assert "Release audit rejected:" in capsys.readouterr().out


@pytest.mark.integration
def test_release_audit_cli_returns_two_for_failed_required_check(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path, bad_artifact=True)
    output_dir = tmp_path / "release_audit_failed"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    summary = json.loads((output_dir / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["required_fail_count"] > 0
    assert summary["failed_checks"]
    failed_ids = {check["id"] for check in summary["required_failed_checks"]}
    assert "curated_artifact:qft_anchor:evidence_summary" in failed_ids
    assert "Required failed checks:" in stdout
    assert "curated_artifact:qft_anchor:evidence_summary" in stdout
    report = (output_dir / "release_readiness.md").read_text(encoding="utf-8")
    assert "## Required Failed Checks" in report
    assert "curated_artifact:qft_anchor:evidence_summary" in report


@pytest.mark.integration
def test_release_audit_cli_prints_warning_triage_for_warning_policy_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    sidecar = tmp_path / "artifacts" / "qft" / "acceptance_summary.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["warnings"] = [{"reason": "manual_review_required"}]
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "  release_version: 0.1.0a1\n",
            "  release_version: 0.1.0a1\n"
            "  warning_policy:\n"
            "    max_count: 0\n"
            "    allowed_ids: []\n",
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "release_audit_warning_failed"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    summary = json.loads((output_dir / "release_readiness.json").read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["required_failed_checks"][0]["id"] == "release_warning_policy"
    assert summary["warning_checks"][0]["id"] == "curated_artifact:qft_anchor:acceptance_warnings"
    assert "Required failed checks:" in stdout
    assert "release_warning_policy" in stdout
    assert "Warning checks:" in stdout
    assert "curated_artifact:qft_anchor:acceptance_warnings" in stdout


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
    assert spec.warning_policy is not None
    assert spec.warning_policy.max_count == 0
    assert spec.warning_policy.allowed_ids == []
    assert {asset.kind for asset in spec.exploratory_assets} >= {"qft", "lr_ace", "tc_qsci"}
