from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from qcchem.cli.main import main
from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_audit import classify_exploratory_config
from qcchem.workflow.release_status import build_release_status_summary

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
                "artifact_name": release_audit_check_id.split(":")[1],
                "artifact_path": artifact_path,
                "artifact_sha256": artifact_sha256,
                "release_audit_check_id": release_audit_check_id,
                "acceptance_scope": "alpha_release_boundary",
                "trust_tier": "exploratory",
                "runtime_evidence_status": "none",
                "accepted": True,
                "blocking_failures": [],
                "warnings": [],
                "release_boundaries": [
                    "Accepted as release-readable evidence with the declared trust tier.",
                    "This sidecar does not promote the artifact beyond its evidence_summary boundary.",
                ],
                "recommended_action": "accept_release_artifact_with_declared_boundary",
            }
        ),
        encoding="utf-8",
    )


def _write_workbench_smoke(path: Path, *, status: str = "passed") -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.workbench_smoke.v0.1-alpha",
                "status": status,
                "route_count": 0,
                "failed_routes": 0 if status == "passed" else 1,
                "page_count": 0,
                "failed_pages": 0 if status == "passed" else 1,
                "failed_checks": [] if status == "passed" else ["route:/overview"],
                "release_verification": {"status": "passed"},
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


def _write_downloaded_release_diagnostics_artifact(
    tmp_path: Path,
) -> tuple[Path, dict[str, Path]]:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    status_json = output_dir / "release_status.json"
    acceptance_status_json = tmp_path / "qcchem-release-acceptance-status.json"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    assert main(["release", "status", "--audit-dir", str(output_dir), "-o", str(status_json)]) == 0
    assert (
        main(
            [
                "release",
                "acceptance-status",
                "-c",
                str(manifest),
                "--repo-root",
                str(tmp_path),
                "--strict",
                "-o",
                str(acceptance_status_json),
            ]
        )
        == 0
    )
    workbench_smoke_json = tmp_path / "workbench_smoke.json"
    _write_workbench_smoke(workbench_smoke_json)
    ci_evidence_dir = tmp_path / "ci_release_evidence"
    assert (
        main(
            [
                "release",
                "evidence-handoff",
                "--audit-dir",
                str(output_dir),
                "--workbench-smoke",
                str(workbench_smoke_json),
                "--acceptance-status",
                str(acceptance_status_json),
                "--output-dir",
                str(ci_evidence_dir),
            ]
        )
        == 0
    )

    artifact_dir = tmp_path / "downloaded" / "qcchem-release-diagnostics-3.11"
    workspace_root = "/home/runner/work/QCchem/QCchem"
    manifest_remote_path = f"{workspace_root}/artifacts/release_audit/release_diagnostics_manifest.json"
    copied_paths: dict[str, Path] = {}
    records: list[dict[str, object]] = []
    sources = [
        ("workbench_smoke_json", workbench_smoke_json, "artifacts/workbench_smoke.json"),
        (
            "release_evidence_summary_json",
            ci_evidence_dir / "release_evidence_summary.json",
            "artifacts/release_evidence/release_evidence_summary.json",
        ),
        (
            "release_evidence_handoff_md",
            ci_evidence_dir / "release_evidence_handoff.md",
            "artifacts/release_evidence/release_evidence_handoff.md",
        ),
        ("release_readiness_json", output_dir / "release_readiness.json", "artifacts/release_audit/release_readiness.json"),
        ("release_readiness_md", output_dir / "release_readiness.md", "artifacts/release_audit/release_readiness.md"),
        ("release_handoff_json", output_dir / "release_handoff.json", "artifacts/release_audit/release_handoff.json"),
        ("release_handoff_md", output_dir / "release_handoff.md", "artifacts/release_audit/release_handoff.md"),
        ("release_status_json", status_json, "artifacts/release_audit/release_status.json"),
        ("acceptance_status_json", acceptance_status_json, "/tmp/qcchem-release-acceptance-status.json"),
    ]
    for name, source, upload_path in sources:
        remote_path = upload_path if upload_path.startswith("/") else f"{workspace_root}/{upload_path}"
        local_path = artifact_dir / remote_path.lstrip("/")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, local_path)
        copied_paths[name] = local_path
        records.append(_diagnostics_manifest_file_record(upload_path, remote_path, local_path))

    manifest_path = artifact_dir / manifest_remote_path.lstrip("/")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    upload_paths = [str(record["path"]) for record in records]
    upload_paths.append("artifacts/release_audit/release_diagnostics_manifest.json")
    manifest_payload = {
        "schema_version": "qcchem.release_diagnostics_manifest.v0.1-alpha",
        "generated_at_utc": "2026-07-06T00:00:00Z",
        "base_dir": workspace_root,
        "ci": {"github_actions": True},
        "diagnostic_artifact": {
            "name": "qcchem-release-diagnostics-3.11",
            "name_prefix": "qcchem-release-diagnostics-",
        },
        "manifest_path": manifest_remote_path,
        "upload_paths": upload_paths,
        "files": records,
        "file_count": len(records),
        "present_count": len(records),
        "digest_count": len(records),
        "missing_paths": [],
        "missing_count": 0,
        "non_file_paths": [],
        "non_file_count": 0,
        "omitted_paths": [
            {
                "path": "artifacts/release_audit/release_diagnostics_manifest.json",
                "resolved_path": manifest_remote_path,
                "reason": "self_manifest_digest_omitted",
            }
        ],
        "omitted_count": 1,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True), encoding="utf-8")
    copied_paths["diagnostics_manifest_json"] = manifest_path
    return artifact_dir.parent, copied_paths


def _diagnostics_manifest_file_record(
    upload_path: str,
    remote_path: str,
    local_path: Path,
) -> dict[str, object]:
    payload = local_path.read_bytes()
    return {
        "path": upload_path,
        "resolved_path": remote_path,
        "status": "present",
        "exists": True,
        "is_file": True,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


@pytest.mark.integration
def test_release_audit_cli_writes_pass_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    stdout = capsys.readouterr().out
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
        "ci_acceptance_command_alignment",
        "acceptance_summary_source",
        "ci_release_diagnostic_artifacts",
        "ci_release_diagnostics_manifest",
        "acceptance_schema_version",
        "acceptance_artifact_sha256",
        "acceptance_release_audit_check_id",
        "acceptance_runtime_evidence_status",
        "acceptance_recommended_action",
        "acceptance_contract_failure_count",
        "release_acceptance_sidecar_status",
        "release_acceptance_repair_plan",
        "audit_provenance",
    }.issubset(set(summary["schema_features"]))
    assert summary["audit_provenance"]["generated_at_utc"].endswith("Z")
    assert summary["audit_provenance"]["repo_root"] == str(tmp_path.resolve())
    assert summary["audit_provenance"]["manifest_path"] == "configs/release/trust_first_audit.yaml"
    assert summary["audit_provenance"]["output_dir"] == "release_audit"
    assert summary["release_acceptance_sidecars"]["status"] == "fresh"
    assert summary["release_acceptance_sidecars"]["repair_plan_count"] == 0
    assert summary["acceptance_commands"] == ["python -m pytest tests/unit/test_release_audit_v23.py -q"]
    assert summary["required_fail_count"] == 0
    assert summary["required_failed_checks"] == []
    assert summary["warning_checks"] == []
    assert "Release audit completed: passed" in stdout
    assert f"Report: {output_dir / 'release_readiness.md'}" in stdout
    assert f"Handoff: {output_dir / 'release_handoff.md'}" in stdout
    assert "release_readiness.md" in (output_dir / "release_readiness.md").read_text(encoding="utf-8")
    handoff = json.loads((output_dir / "release_handoff.json").read_text(encoding="utf-8"))
    assert handoff["schema_version"] == "qcchem.release_handoff.v0.2-alpha"
    assert handoff["release_readiness"]["markdown"] == "release_readiness.md"
    assert handoff["diagnostic_artifacts"]["manifest"] == {
        "path": "artifacts/release_audit/release_diagnostics_manifest.json",
        "schema_version": "qcchem.release_diagnostics_manifest.v0.1-alpha",
    }
    assert "release_handoff.md" in (output_dir / "release_handoff.md").read_text(encoding="utf-8")


@pytest.mark.integration
def test_release_audit_cli_prints_ci_diagnostic_artifact_hint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_API_URL", "https://api.github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "wuls968/QCchem")
    monkeypatch.setenv("GITHUB_RUN_ID", "28725875043")
    monkeypatch.setenv("QCCHEM_RELEASE_DIAGNOSTIC_ARTIFACT_NAME", "qcchem-release-diagnostics-3.11")

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "Diagnostic artifact: qcchem-release-diagnostics-3.11" in stdout
    assert "Artifact listing: https://api.github.com/repos/wuls968/QCchem/actions/runs/28725875043/artifacts" in stdout
    assert "Diagnostics manifest: artifacts/release_audit/release_diagnostics_manifest.json" in stdout


@pytest.mark.integration
def test_release_status_cli_summarizes_existing_audit_outputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    status_json = tmp_path / "release_status.json"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()

    exit_code = main(["release", "status", "--audit-dir", str(output_dir), "-o", str(status_json)])

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "Release status: passed" in stdout
    assert f"Report: {output_dir / 'release_readiness.md'}" in stdout
    assert f"Handoff: {output_dir / 'release_handoff.md'}" in stdout
    assert "Diagnostics manifest: artifacts/release_audit/release_diagnostics_manifest.json" in stdout
    assert f"Status JSON: {status_json}" in stdout
    status = json.loads(status_json.read_text(encoding="utf-8"))
    assert status["schema_version"] == "qcchem.release_status.v0.1-alpha"
    assert status["status"] == "passed"
    assert status["required_fail_count"] == 0
    assert status["release_acceptance_sidecars_status"] == "fresh"
    assert status["first_required_failure"] is None
    assert status["first_sidecar_repair"] is None
    assert status["release_handoff"]["markdown"] == str(output_dir / "release_handoff.md")


@pytest.mark.integration
def test_release_evidence_handoff_cli_writes_local_ci_handoff(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    acceptance_status_json = tmp_path / "qcchem-release-acceptance-status.json"
    workbench_smoke_json = tmp_path / "workbench_smoke.json"
    evidence_root = tmp_path / "release_evidence"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    assert main(["release", "status", "--audit-dir", str(output_dir), "-o", str(output_dir / "release_status.json")]) == 0
    assert (
        main(
            [
                "release",
                "acceptance-status",
                "-c",
                str(manifest),
                "--repo-root",
                str(tmp_path),
                "--strict",
                "-o",
                str(acceptance_status_json),
            ]
        )
        == 0
    )
    _write_workbench_smoke(workbench_smoke_json)
    capsys.readouterr()

    exit_code = main(
        [
            "release",
            "evidence-handoff",
            "--audit-dir",
            str(output_dir),
            "--workbench-smoke",
            str(workbench_smoke_json),
            "--acceptance-status",
            str(acceptance_status_json),
            "--output-dir",
            str(evidence_root),
            "--strict",
        ]
    )

    stdout = capsys.readouterr().out
    summary_path = evidence_root / "release_evidence_summary.json"
    handoff_path = evidence_root / "release_evidence_handoff.md"
    assert exit_code == 0
    assert "Release evidence handoff: passed" in stdout
    assert f"Release evidence JSON: {summary_path}" in stdout
    assert f"Release evidence handoff Markdown: {handoff_path}" in stdout
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    handoff = handoff_path.read_text(encoding="utf-8")
    assert summary["schema_version"] == "qcchem.release_evidence_collection.v0.1-alpha"
    assert summary["collection_mode"] == "ci_diagnostics_handoff"
    assert summary["status"] == "passed"
    assert summary["first_failure"] is None
    assert summary["release_status"]["status"] == "passed"
    assert summary["acceptance_status"]["status"] == "fresh"
    assert summary["release_artifact_verification"]["status"] == "not_run"
    assert summary["release_matrix_delta"]["status"] == "not_applicable"
    assert summary["release_matrix_delta"]["reason"] == "downloaded_artifact_verification_not_run"
    assert summary["workbench_smoke"]["status"] == "passed"
    assert summary["failures"] == []
    assert "# QCchem Release Evidence Handoff" in handoff
    assert "`None`" not in handoff
    assert "- docs_path: `not_applicable`" in handoff
    assert "- collection_mode: `ci_diagnostics_handoff`" in handoff
    assert "- release_artifact_verification_json: `not_applicable`" in handoff
    assert "- release_matrix_summary_json: `not_applicable`" in handoff
    assert "## CI Diagnostics Handoff" in handoff
    assert "- release_status: `passed`" in handoff
    assert "- acceptance_status: `fresh`" in handoff
    assert "- release_status_count: `not_applicable`" in handoff
    assert "## Matrix Artifact Delta" in handoff
    assert "- status: `not_applicable`" in handoff
    assert "`downloaded_artifact_verification` verifies downloaded CI diagnostics" in handoff


@pytest.mark.integration
def test_release_evidence_handoff_cli_strict_fails_when_workbench_smoke_is_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    acceptance_status_json = tmp_path / "qcchem-release-acceptance-status.json"
    evidence_root = tmp_path / "release_evidence"
    missing_smoke_json = tmp_path / "missing_workbench_smoke.json"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    assert (
        main(
            [
                "release",
                "acceptance-status",
                "-c",
                str(manifest),
                "--repo-root",
                str(tmp_path),
                "--strict",
                "-o",
                str(acceptance_status_json),
            ]
        )
        == 0
    )
    capsys.readouterr()

    exit_code = main(
        [
            "release",
            "evidence-handoff",
            "--audit-dir",
            str(output_dir),
            "--workbench-smoke",
            str(missing_smoke_json),
            "--acceptance-status",
            str(acceptance_status_json),
            "--output-dir",
            str(evidence_root),
            "--strict",
        ]
    )

    stdout = capsys.readouterr().out
    summary = json.loads((evidence_root / "release_evidence_summary.json").read_text(encoding="utf-8"))
    handoff = (evidence_root / "release_evidence_handoff.md").read_text(encoding="utf-8")
    assert exit_code == 2
    assert "Release evidence handoff: failed" in stdout
    assert f"First failure: workbench_smoke_missing path={missing_smoke_json}" in stdout
    assert summary["collection_mode"] == "ci_diagnostics_handoff"
    assert summary["status"] == "failed"
    assert summary["first_failure"] == {"path": str(missing_smoke_json), "reason": "workbench_smoke_missing"}
    assert "- status: `failed`" in handoff
    assert "workbench_smoke_missing" in handoff


@pytest.mark.integration
def test_release_verify_artifacts_cli_accepts_downloaded_diagnostics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, _ = _write_downloaded_release_diagnostics_artifact(tmp_path)
    capsys.readouterr()
    verification_json = tmp_path / "release_artifact_verification.json"

    exit_code = main(["release", "verify-artifacts", "--artifact-dir", str(artifact_dir), "-o", str(verification_json)])

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "Release artifact verification: passed" in stdout
    assert "Release status bundles: 1" in stdout
    assert "Diagnostics manifests: 1" in stdout
    assert "Acceptance status files: 1" in stdout
    assert f"Verification JSON: {verification_json}" in stdout
    report = json.loads(verification_json.read_text(encoding="utf-8"))
    assert report["schema_version"] == "qcchem.release_artifact_verification.v0.1-alpha"
    assert report["status"] == "passed"
    assert report["summary"] == {
        "acceptance_status_count": 1,
        "diagnostics_manifest_count": 1,
        "failure_count": 0,
        "release_status_count": 1,
    }
    assert report["failures"] == []


@pytest.mark.integration
def test_release_collect_evidence_cli_writes_verifier_and_workbench_handoff(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, _ = _write_downloaded_release_diagnostics_artifact(tmp_path)
    evidence_root = tmp_path / "release_evidence"
    capsys.readouterr()

    exit_code = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(artifact_dir),
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--output-dir",
            str(evidence_root),
        ]
    )

    stdout = capsys.readouterr().out
    verification_path = evidence_root / "release_artifact_verification.json"
    matrix_summary_path = evidence_root / "release_matrix_summary.json"
    smoke_path = evidence_root / "workbench_smoke.json"
    summary_path = evidence_root / "release_evidence_summary.json"
    handoff_path = evidence_root / "release_evidence_handoff.md"
    assert exit_code == 0
    assert "Release artifact verification: passed" in stdout
    assert f"Verification JSON: {verification_path}" in stdout
    assert f"Release matrix summary: {matrix_summary_path}" in stdout
    assert "Matrix artifact comparison: not_compared" in stdout
    assert f"Workbench smoke summary written to {smoke_path}" in stdout
    assert "Release evidence summary: passed" in stdout
    assert f"Release evidence JSON: {summary_path}" in stdout
    assert f"Release evidence handoff: {handoff_path}" in stdout

    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    matrix_summary = json.loads(matrix_summary_path.read_text(encoding="utf-8"))
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    handoff = handoff_path.read_text(encoding="utf-8")
    assert verification["status"] == "passed"
    assert smoke["status"] == "passed"
    assert smoke["release_verification"]["status"] == "passed"
    assert Path(smoke["release_verification"]["source_path"]).resolve() == verification_path.resolve()
    assert summary["schema_version"] == "qcchem.release_evidence_collection.v0.1-alpha"
    assert summary["collection_mode"] == "downloaded_artifact_verification"
    assert summary["status"] == "passed"
    assert summary["recommended_action"] == "review_release_evidence"
    assert summary["first_failure"] is None
    assert summary["outputs"] == {
        "release_evidence_summary": str(summary_path),
        "release_evidence_handoff": str(handoff_path),
        "release_artifact_verification": str(verification_path),
        "release_matrix_summary": str(matrix_summary_path),
        "workbench_smoke": str(smoke_path),
    }
    assert summary["release_artifact_verification"]["summary"] == {
        "acceptance_status_count": 1,
        "diagnostics_manifest_count": 1,
        "failure_count": 0,
        "release_status_count": 1,
    }
    assert summary["release_artifact_verification"]["first_failure"] is None
    matrix_artifacts = summary["release_artifact_verification"]["matrix_artifacts"]
    assert len(matrix_artifacts) == 1
    matrix_artifact = matrix_artifacts[0]
    assert matrix_artifact["artifact_name"] == "qcchem-release-diagnostics-3.11"
    assert matrix_artifact["status"] == "passed"
    assert matrix_artifact["release_status_count"] == 1
    assert matrix_artifact["source_tree_release_status"] == "passed"
    assert matrix_artifact["wheel_release_status"] is None
    assert matrix_artifact["diagnostics_manifest_count"] == 1
    assert matrix_artifact["diagnostics_digest_count"] == matrix_artifact["diagnostics_file_count"]
    assert matrix_artifact["acceptance_status"] == "fresh"
    assert matrix_artifact["failure_count"] == 0
    assert matrix_artifact["first_failure"] is None
    assert matrix_summary["schema_version"] == "qcchem.release_matrix_summary.v0.1-alpha"
    assert matrix_summary["source_verification"] == str(verification_path)
    assert matrix_summary["artifact_count"] == 1
    assert matrix_summary["failed_artifact_count"] == 0
    assert matrix_summary["artifacts"] == matrix_artifacts
    assert summary["release_matrix_summary"] == matrix_summary
    assert summary["release_matrix_delta"] == {
        "status": "not_compared",
        "reason": "baseline_not_provided",
        "baseline_path": None,
        "current_artifact_count": 1,
        "baseline_artifact_count": None,
        "added": [],
        "removed": [],
        "changed": [],
        "unchanged_count": 0,
        "first_change": None,
        "first_failure": None,
    }
    assert summary["workbench_smoke"]["release_verification"]["status"] == "passed"
    assert "# QCchem Release Evidence Handoff" in handoff
    assert "`None`" not in handoff
    assert "- status: `passed`" in handoff
    assert "- recommended_action: `review_release_evidence`" in handoff
    assert "- first_failure: `none`" in handoff
    assert "- collection_mode: `downloaded_artifact_verification`" in handoff
    assert "- release_status: `not_applicable`" in handoff
    assert "- required_checks: `not_applicable`" in handoff
    assert "- acceptance_status: `not_applicable`" in handoff
    assert "- release_status_count: `1`" in handoff
    assert "## Matrix Artifact Verification" in handoff
    assert "`qcchem-release-diagnostics-3.11`: status=`passed`" in handoff
    assert "wheel=`not_applicable`" in handoff
    assert "acceptance=`fresh`" in handoff
    assert "## Matrix Artifact Delta" in handoff
    assert "- status: `not_compared`" in handoff
    assert "- reason: `baseline_not_provided`" in handoff
    assert "- baseline_path: `not_provided`" in handoff
    assert "- linked_release_verification_status: `passed`" in handoff
    assert "It does not replace the real browser console checklist" in handoff


@pytest.mark.integration
def test_release_collect_evidence_handoff_compares_matrix_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, _ = _write_downloaded_release_diagnostics_artifact(tmp_path)
    seed_root = tmp_path / "seed_release_evidence"
    assert (
        main(
            [
                "release",
                "collect-evidence",
                "--artifact-dir",
                str(artifact_dir),
                "--docs",
                str(REPO_ROOT / "docs" / "workbench.md"),
                "--output-dir",
                str(seed_root),
            ]
        )
        == 0
    )
    baseline_payload = json.loads((seed_root / "release_matrix_summary.json").read_text(encoding="utf-8"))
    baseline_payload["artifacts"][0]["diagnostics_digest_count"] = 0
    baseline_path = tmp_path / "previous_release_matrix_summary.json"
    baseline_path.write_text(json.dumps(baseline_payload, indent=2, sort_keys=True), encoding="utf-8")
    evidence_root = tmp_path / "release_evidence"
    capsys.readouterr()

    exit_code = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(artifact_dir),
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--output-dir",
            str(evidence_root),
            "--baseline-summary",
            str(baseline_path),
        ]
    )

    stdout = capsys.readouterr().out
    summary = json.loads((evidence_root / "release_evidence_summary.json").read_text(encoding="utf-8"))
    handoff = (evidence_root / "release_evidence_handoff.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Matrix artifact comparison: changed" in stdout
    assert summary["status"] == "passed"
    delta = summary["release_matrix_delta"]
    assert delta["status"] == "changed"
    assert delta["baseline_path"] == str(baseline_path)
    assert delta["current_artifact_count"] == 1
    assert delta["baseline_artifact_count"] == 1
    assert delta["added"] == []
    assert delta["removed"] == []
    assert delta["unchanged_count"] == 0
    assert len(delta["changed"]) == 1
    changed = delta["changed"][0]
    assert changed["artifact_name"] == "qcchem-release-diagnostics-3.11"
    assert "diagnostics_digest_count" in changed["changed_fields"]
    assert changed["before"]["diagnostics_digest_count"] == 0
    assert changed["after"]["diagnostics_digest_count"] == changed["after"]["diagnostics_file_count"]
    assert delta["first_change"] == {
        "change_type": "changed",
        "artifact_name": "qcchem-release-diagnostics-3.11",
        "changed_fields": changed["changed_fields"],
    }
    assert "`None`" not in handoff
    assert "## Matrix Artifact Delta" in handoff
    assert "- baseline_selection: `explicit`" in handoff
    assert "- status: `changed`" in handoff
    assert f"- baseline_path: `{baseline_path}`" in handoff
    assert "- changed `qcchem-release-diagnostics-3.11`: fields=`diagnostics_digest_count`" in handoff


@pytest.mark.integration
def test_release_collect_evidence_auto_selects_latest_matrix_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, _ = _write_downloaded_release_diagnostics_artifact(tmp_path)
    seed_root = tmp_path / "seed_release_evidence"
    assert (
        main(
            [
                "release",
                "collect-evidence",
                "--artifact-dir",
                str(artifact_dir),
                "--docs",
                str(REPO_ROOT / "docs" / "workbench.md"),
                "--output-dir",
                str(seed_root),
            ]
        )
        == 0
    )
    seed_payload = json.loads((seed_root / "release_matrix_summary.json").read_text(encoding="utf-8"))
    older_root = tmp_path / "release_history" / "2026-07-05"
    newer_root = tmp_path / "release_history" / "2026-07-06"
    older_root.mkdir(parents=True)
    newer_root.mkdir(parents=True)
    older_path = older_root / "release_matrix_summary.json"
    newer_path = newer_root / "release_matrix_summary.json"
    older_payload = dict(seed_payload)
    older_payload["source_verification"] = str(older_root / "release_artifact_verification.json")
    newer_payload = json.loads(json.dumps(seed_payload))
    newer_payload["source_verification"] = str(newer_root / "release_artifact_verification.json")
    newer_payload["artifacts"][0]["diagnostics_digest_count"] = 0
    older_path.write_text(json.dumps(older_payload, indent=2, sort_keys=True), encoding="utf-8")
    newer_path.write_text(json.dumps(newer_payload, indent=2, sort_keys=True), encoding="utf-8")
    os.utime(older_path, (1_700_000_000, 1_700_000_000))
    os.utime(newer_path, (1_800_000_000, 1_800_000_000))
    evidence_root = tmp_path / "current_release_evidence"
    capsys.readouterr()

    exit_code = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(artifact_dir),
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--output-dir",
            str(evidence_root),
            "--baseline-search-root",
            str(tmp_path / "release_history"),
        ]
    )

    stdout = capsys.readouterr().out
    summary = json.loads((evidence_root / "release_evidence_summary.json").read_text(encoding="utf-8"))
    handoff = (evidence_root / "release_evidence_handoff.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert f"Matrix baseline selection: auto ({newer_path})" in stdout
    assert "Matrix artifact comparison: changed" in stdout
    selection = summary["release_matrix_baseline_selection"]
    assert selection == {
        "mode": "auto",
        "path": str(newer_path),
        "search_root": str(tmp_path / "release_history"),
        "candidate_count": 2,
        "reason": None,
    }
    delta = summary["release_matrix_delta"]
    assert delta["status"] == "changed"
    assert delta["baseline_path"] == str(newer_path)
    assert delta["current_artifact_count"] == 1
    assert delta["baseline_artifact_count"] == 1
    assert delta["added"] == []
    assert delta["removed"] == []
    assert delta["unchanged_count"] == 0
    assert delta["changed"][0]["artifact_name"] == "qcchem-release-diagnostics-3.11"
    assert delta["changed"][0]["before"]["diagnostics_digest_count"] == 0
    assert "- baseline_selection: `auto`" in handoff
    assert f"- baseline_search_root: `{tmp_path / 'release_history'}`" in handoff
    assert "- baseline_candidate_count: `2`" in handoff
    assert f"- baseline_path: `{newer_path}`" in handoff


@pytest.mark.integration
def test_release_collect_evidence_history_root_retains_runs_and_reuses_previous_baseline(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, _ = _write_downloaded_release_diagnostics_artifact(tmp_path)
    history_root = tmp_path / "release_history"
    capsys.readouterr()

    first_exit = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(artifact_dir),
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--history-root",
            str(history_root),
            "--history-label",
            "run-001",
        ]
    )
    second_exit = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(artifact_dir),
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--history-root",
            str(history_root),
            "--history-label",
            "run-002",
        ]
    )

    stdout = capsys.readouterr().out
    first_root = history_root / "run-001"
    second_root = history_root / "run-002"
    summary = json.loads((second_root / "release_evidence_summary.json").read_text(encoding="utf-8"))
    handoff = (second_root / "release_evidence_handoff.md").read_text(encoding="utf-8")
    assert first_exit == 0
    assert second_exit == 0
    assert f"Release evidence JSON: {first_root / 'release_evidence_summary.json'}" in stdout
    assert f"Release evidence JSON: {second_root / 'release_evidence_summary.json'}" in stdout
    assert summary["status"] == "passed"
    assert summary["evidence_root"] == str(second_root)
    assert summary["release_history"] == {
        "mode": "retained_history",
        "root": str(history_root),
        "label": "run-002",
        "path": str(second_root),
        "baseline_search_root": str(history_root),
    }
    selection = summary["release_matrix_baseline_selection"]
    assert selection["mode"] == "auto"
    assert selection["path"] == str(first_root / "release_matrix_summary.json")
    assert selection["search_root"] == str(history_root)
    assert selection["candidate_count"] == 1
    delta = summary["release_matrix_delta"]
    assert delta["status"] == "passed"
    assert delta["baseline_path"] == str(first_root / "release_matrix_summary.json")
    assert "- history_mode: `retained_history`" in handoff
    assert f"- history_root: `{history_root}`" in handoff
    assert "- history_label: `run-002`" in handoff
    assert "- baseline_selection: `auto`" in handoff


@pytest.mark.integration
def test_release_collect_evidence_history_root_rejects_unsafe_output_choices(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    history_root = tmp_path / "release_history"
    occupied_root = history_root / "run-001"
    occupied_root.mkdir(parents=True)
    (occupied_root / "release_matrix_summary.json").write_text("{}", encoding="utf-8")
    capsys.readouterr()

    existing_exit = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(tmp_path / "downloaded"),
            "--history-root",
            str(history_root),
            "--history-label",
            "run-001",
        ]
    )
    combined_exit = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(tmp_path / "downloaded"),
            "--output-dir",
            str(tmp_path / "release_evidence"),
            "--history-root",
            str(history_root),
            "--history-label",
            "run-002",
        ]
    )
    bad_label_exit = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(tmp_path / "downloaded"),
            "--history-root",
            str(history_root),
            "--history-label",
            "../bad",
        ]
    )

    stdout = capsys.readouterr().out
    assert existing_exit == 2
    assert combined_exit == 2
    assert bad_label_exit == 2
    assert "release history output directory is not empty" in stdout
    assert "--history-root cannot be combined with --output-dir" in stdout
    assert "release history label must be one relative directory name" in stdout


@pytest.mark.integration
def test_release_collect_evidence_handoff_surfaces_tampered_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, copied_paths = _write_downloaded_release_diagnostics_artifact(tmp_path)
    copied_paths["release_handoff_md"].write_text("tampered handoff\n", encoding="utf-8")
    evidence_root = tmp_path / "release_evidence"
    capsys.readouterr()

    exit_code = main(
        [
            "release",
            "collect-evidence",
            "--artifact-dir",
            str(artifact_dir),
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--output-dir",
            str(evidence_root),
        ]
    )

    stdout = capsys.readouterr().out
    summary_path = evidence_root / "release_evidence_summary.json"
    handoff_path = evidence_root / "release_evidence_handoff.md"
    assert exit_code == 2
    assert "Release artifact verification: failed" in stdout
    assert "First failure: diagnostics_manifest_size_mismatch" in stdout
    assert "Release evidence summary: failed" in stdout
    assert f"Release evidence handoff: {handoff_path}" in stdout

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    handoff = handoff_path.read_text(encoding="utf-8")
    assert summary["status"] == "failed"
    assert summary["recommended_action"] == "inspect_release_evidence_failures"
    assert summary["first_failure"]["reason"] == "diagnostics_manifest_size_mismatch"
    assert "release_handoff.md" in str(summary["first_failure"]["local_path"])
    assert summary["release_artifact_verification"]["status"] == "failed"
    matrix_artifact = summary["release_artifact_verification"]["matrix_artifacts"][0]
    assert matrix_artifact["artifact_name"] == "qcchem-release-diagnostics-3.11"
    assert matrix_artifact["status"] == "failed"
    assert matrix_artifact["failure_count"] >= 1
    assert matrix_artifact["first_failure"]["reason"] == "diagnostics_manifest_size_mismatch"
    assert summary["workbench_smoke"]["status"] == "passed"
    assert "- status: `failed`" in handoff
    assert "- recommended_action: `inspect_release_evidence_failures`" in handoff
    assert "diagnostics_manifest_size_mismatch" in handoff
    assert "release_handoff.md" in handoff
    assert "`qcchem-release-diagnostics-3.11`: status=`failed`" in handoff
    assert "- linked_release_verification_status: `failed`" in handoff


@pytest.mark.integration
def test_release_verify_artifacts_cli_rejects_manifest_digest_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir, copied_paths = _write_downloaded_release_diagnostics_artifact(tmp_path)
    copied_paths["release_handoff_md"].write_text("tampered handoff\n", encoding="utf-8")
    capsys.readouterr()
    verification_json = tmp_path / "release_artifact_verification.json"

    exit_code = main(["release", "verify-artifacts", "--artifact-dir", str(artifact_dir), "-o", str(verification_json)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release artifact verification: failed" in stdout
    assert "First failure: diagnostics_manifest_size_mismatch" in stdout
    report = json.loads(verification_json.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert {
        "diagnostics_manifest_size_mismatch",
        "diagnostics_manifest_sha256_mismatch",
    }.issubset({failure["reason"] for failure in report["failures"]})


@pytest.mark.integration
@pytest.mark.parametrize(
    ("file_name", "stale_schema_version", "expected_schema_version"),
    [
        ("release_readiness.json", "0.0-stale", "1.1"),
        ("release_handoff.json", "qcchem.release_handoff.v0.0-stale", "qcchem.release_handoff.v0.2-alpha"),
    ],
)
def test_release_status_cli_rejects_schema_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    file_name: str,
    stale_schema_version: str,
    expected_schema_version: str,
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    status_json = tmp_path / "release_status.json"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()

    contract_json = output_dir / file_name
    contract_payload = json.loads(contract_json.read_text(encoding="utf-8"))
    contract_payload["schema_version"] = stale_schema_version
    contract_json.write_text(json.dumps(contract_payload), encoding="utf-8")

    exit_code = main(["release", "status", "--audit-dir", str(output_dir), "-o", str(status_json)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release status unavailable: schema mismatch" in stdout
    assert f"{file_name} schema_version expected={expected_schema_version} actual={stale_schema_version}" in stdout
    status = json.loads(status_json.read_text(encoding="utf-8"))
    assert status["status"] == "schema_mismatch"
    assert status["recommended_action"] == "rerun_release_audit"
    assert status["schema_mismatches"] == [
        {
            "file": file_name,
            "field": "schema_version",
            "expected": expected_schema_version,
            "actual": stale_schema_version,
        }
    ]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("file_name", "field_path", "replacement", "expected_contract"),
    [
        (
            "release_readiness.json",
            ("required_fail_count",),
            None,
            {
                "file": "release_readiness.json",
                "field": "required_fail_count",
                "expected": "int",
                "actual_type": "missing",
            },
        ),
        (
            "release_handoff.json",
            ("diagnostic_artifacts", "names"),
            "qcchem-release-diagnostics-3.11",
            {
                "file": "release_handoff.json",
                "field": "diagnostic_artifacts.names",
                "expected": "list",
                "actual_type": "str",
            },
        ),
        (
            "release_readiness.json",
            ("release_acceptance_sidecars", "status"),
            12,
            {
                "file": "release_readiness.json",
                "field": "release_acceptance_sidecars.status",
                "expected": "str",
                "actual_type": "int",
            },
        ),
        (
            "release_readiness.json",
            ("release_acceptance_sidecars", "repair_plan_count"),
            4,
            {
                "file": "release_readiness.json",
                "field": "release_acceptance_sidecars.repair_plan_count",
                "reason": "must_equal_release_acceptance_sidecars.repair_plan_length",
                "expected": 0,
                "actual": 4,
            },
        ),
        (
            "release_handoff.json",
            ("diagnostic_artifacts", "manifest", "schema_version"),
            "qcchem.release_diagnostics_manifest.v0.0-stale",
            {
                "file": "release_handoff.json",
                "field": "diagnostic_artifacts.manifest.schema_version",
                "reason": "must_match_release_diagnostics_manifest_schema_version",
                "expected": "qcchem.release_diagnostics_manifest.v0.1-alpha",
                "actual": "qcchem.release_diagnostics_manifest.v0.0-stale",
            },
        ),
    ],
)
def test_release_status_cli_rejects_contract_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    file_name: str,
    field_path: tuple[str, ...],
    replacement: object,
    expected_contract: dict[str, object],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    status_json = tmp_path / "release_status.json"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()

    contract_json = output_dir / file_name
    contract_payload = json.loads(contract_json.read_text(encoding="utf-8"))
    target = contract_payload
    for part in field_path[:-1]:
        target = target[part]
    if replacement is None:
        target.pop(field_path[-1])
    else:
        target[field_path[-1]] = replacement
    contract_json.write_text(json.dumps(contract_payload), encoding="utf-8")

    exit_code = main(["release", "status", "--audit-dir", str(output_dir), "-o", str(status_json)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release status unavailable: contract mismatch" in stdout
    assert f"{expected_contract['file']} {expected_contract['field']} expected={expected_contract['expected']}" in stdout
    status = json.loads(status_json.read_text(encoding="utf-8"))
    assert status["status"] == "contract_mismatch"
    assert status["recommended_action"] == "rerun_release_audit"
    assert status["contract_mismatches"] == [expected_contract]


@pytest.mark.integration
@pytest.mark.parametrize(
    ("field_path", "replacement", "expected_contract"),
    [
        (
            ("status",),
            "failed",
            {
                "file": "release_handoff.json",
                "field": "status",
                "reason": "must_match_release_readiness.status",
                "expected": "passed",
                "actual": "failed",
            },
        ),
        (
            ("release_audit", "required_fail_count"),
            7,
            {
                "file": "release_handoff.json",
                "field": "release_audit.required_fail_count",
                "reason": "must_match_release_readiness.required_fail_count",
                "expected": 0,
                "actual": 7,
            },
        ),
    ],
)
def test_release_status_cli_rejects_handoff_consistency_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    field_path: tuple[str, ...],
    replacement: object,
    expected_contract: dict[str, object],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    status_json = tmp_path / "release_status.json"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()

    handoff_json = output_dir / "release_handoff.json"
    handoff = json.loads(handoff_json.read_text(encoding="utf-8"))
    target = handoff
    for part in field_path[:-1]:
        target = target[part]
    target[field_path[-1]] = replacement
    handoff_json.write_text(json.dumps(handoff), encoding="utf-8")

    exit_code = main(["release", "status", "--audit-dir", str(output_dir), "-o", str(status_json)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release status unavailable: contract mismatch" in stdout
    assert expected_contract["reason"] in stdout
    status = json.loads(status_json.read_text(encoding="utf-8"))
    assert status["status"] == "contract_mismatch"
    assert status["recommended_action"] == "rerun_release_audit"
    assert status["contract_mismatches"] == [expected_contract]


@pytest.mark.integration
def test_release_status_shared_validator_reports_handoff_consistency_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    output_dir = tmp_path / "release_audit"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 0
    capsys.readouterr()

    handoff_json = output_dir / "release_handoff.json"
    handoff = json.loads(handoff_json.read_text(encoding="utf-8"))
    handoff["release_audit"]["warning_count"] = 3
    handoff_json.write_text(json.dumps(handoff), encoding="utf-8")

    status = build_release_status_summary(output_dir)

    assert status["status"] == "contract_mismatch"
    assert status["recommended_action"] == "rerun_release_audit"
    assert status["contract_mismatches"] == [
        {
            "file": "release_handoff.json",
            "field": "release_audit.warning_count",
            "reason": "must_match_release_readiness.warning_count",
            "expected": 0,
            "actual": 3,
        }
    ]


@pytest.mark.integration
def test_release_status_cli_reports_missing_outputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    audit_dir = tmp_path / "missing_release_audit"

    exit_code = main(["release", "status", "--audit-dir", str(audit_dir)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release status unavailable: missing outputs" in stdout
    assert "release_readiness.json" in stdout
    assert "release_handoff.json" in stdout


@pytest.mark.integration
def test_release_status_cli_strict_fails_for_failed_audit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path, bad_artifact=True)
    output_dir = tmp_path / "release_audit_failed"
    assert main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)]) == 2
    capsys.readouterr()

    exit_code = main(["release", "status", "--audit-dir", str(output_dir), "--strict"])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release status: failed" in stdout
    assert "First required failure: curated_artifact:qft_anchor:evidence_summary" in stdout
    assert "Required checks:" in stdout


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
def test_release_audit_cli_prints_sidecar_repair_triage(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_minimal_release_tree(tmp_path)
    sidecar = tmp_path / "artifacts" / "qft" / "acceptance_summary.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["artifact_sha256"] = "0" * 64
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = tmp_path / "release_audit_stale_sidecar"

    exit_code = main(["release", "audit", "-c", str(manifest), "-o", str(output_dir), "--repo-root", str(tmp_path)])

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release audit completed: failed" in stdout
    assert "Release sidecar repair:" in stdout
    assert "- qft_anchor status=stale issue=contract_failure:artifact_sha256" in stdout
    assert "preview: qcchem release accept-artifact" in stdout
    assert "repair: qcchem release accept-artifact" in stdout
    assert "--overwrite" in stdout


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
