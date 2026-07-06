from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_acceptance import (
    RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES,
    preview_release_artifact_acceptance_summary,
    release_acceptance_status_contract_failures,
    release_acceptance_status_report,
    write_release_artifact_acceptance_summary,
)
from qcchem.workflow.release_audit import run_release_audit


def _write_release_acceptance_fixture(root: Path) -> Path:
    (root / "pyproject.toml").write_text('[project]\nversion = "0.1.0a1"\n', encoding="utf-8")
    artifact = root / "artifacts" / "h2" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.result.v0.1-alpha",
                "run_id": "h2-local",
                "problem": {"molecule_name": "H2", "basis": "sto3g"},
                "energy": {"total_energy": -1.137, "energy_units": "Hartree"},
                "backend": {"kind": "statevector"},
                "benchmark": {
                    "absolute_error": 0.0,
                    "absolute_error_threshold": 0.0016,
                    "comparison_target": "exact diagonalization",
                    "exact_available": True,
                },
                "chemical_accuracy": {
                    "available": True,
                    "meets_chemical_accuracy": True,
                    "absolute_error_hartree": 0.0,
                },
                "verification_status": "validated",
            }
        ),
        encoding="utf-8",
    )
    config = root / "configs" / "release" / "trust_first_audit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts:
    - name: h2_anchor
      path: artifacts/h2/result.json
      required: true
  required_docs: []
  acceptance_commands: []
""".lstrip(),
        encoding="utf-8",
    )
    return config


def test_release_acceptance_writes_manifest_bound_sidecar(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)

    summary, output_path = write_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
    )

    assert output_path == tmp_path / "artifacts" / "h2" / "acceptance_summary.json"
    assert summary["schema_version"] == "qcchem.release_artifact_acceptance.v0.1-alpha"
    assert summary["artifact_name"] == "h2_anchor"
    assert summary["artifact_path"] == "artifacts/h2/result.json"
    assert summary["release_audit_check_id"] == "curated_artifact:h2_anchor:acceptance_summary"
    assert summary["trust_tier"] == "validated"
    assert summary["runtime_evidence_status"] == "none"
    assert summary["accepted"] is True
    assert summary["blocking_failures"] == []
    assert summary["warnings"] == []

    audit = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")
    acceptance_check = next(
        check
        for check in audit["checks"]
        if check["id"] == "curated_artifact:h2_anchor:acceptance_summary"
    )
    assert audit["status"] == "passed"
    assert acceptance_check["status"] == "passed"
    assert audit["evidence_matrix"][0]["acceptance_contract_failure_count"] == 0
    report = release_acceptance_status_report(spec, repo_root=tmp_path)
    assert report["status"] == "fresh"
    assert report["schema_features"] == list(RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES)
    assert "status_counts" in report["schema_features"]
    assert "repair_plan" in report["schema_features"]
    assert release_acceptance_status_contract_failures(report) == []
    assert report["fresh_count"] == 1
    assert report["requires_update_count"] == 0
    assert report["repair_plan_count"] == 0
    assert report["repair_plan"] == []
    assert report["items"][0]["status"] == "fresh"
    assert report["items"][0]["changed_fields"] == []


def test_release_acceptance_requires_overwrite_for_existing_sidecar(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    write_release_artifact_acceptance_summary(spec, artifact_name="h2_anchor", repo_root=tmp_path)

    with pytest.raises(FileExistsError, match="--dry-run"):
        write_release_artifact_acceptance_summary(spec, artifact_name="h2_anchor", repo_root=tmp_path)


def test_release_acceptance_preview_does_not_write_missing_sidecar(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    sidecar = tmp_path / "artifacts" / "h2" / "acceptance_summary.json"

    summary, output_path, status = preview_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
    )

    assert output_path == sidecar
    assert not sidecar.exists()
    assert summary["artifact_name"] == "h2_anchor"
    assert summary["artifact_path"] == "artifacts/h2/result.json"
    assert status["status"] == "missing"
    assert "artifact_sha256" in status["missing_fields"]


def test_release_acceptance_status_reports_missing_sidecar(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)

    report = release_acceptance_status_report(spec, repo_root=tmp_path)

    assert report["status"] == "needs_update"
    assert report["requires_update_count"] == 1
    assert report["status_counts"] == {"missing": 1}
    assert report["items"][0]["status"] == "missing"
    assert "artifact_sha256" in report["items"][0]["missing_fields"]
    assert report["repair_plan_count"] == 1
    repair = report["repair_plan"][0]
    assert repair["artifact_name"] == "h2_anchor"
    assert repair["status"] == "missing"
    assert repair["issue"] == "sidecar_missing"
    assert repair["preview_command"] is not None
    assert "--dry-run" in repair["preview_command"]
    assert repair["repair_command"] is not None
    assert "--overwrite" not in repair["repair_command"]


def test_release_acceptance_status_contract_reports_field_drift(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    report = release_acceptance_status_report(spec, repo_root=tmp_path)

    missing_count = dict(report)
    missing_count.pop("repair_plan_count")
    assert release_acceptance_status_contract_failures(missing_count) == [
        {
            "field": "repair_plan_count",
            "expected": "int",
            "actual_type": "missing",
        }
    ]

    mistyped_item = json.loads(json.dumps(report))
    mistyped_item["items"][0]["changed_fields"] = "artifact_sha256"
    assert release_acceptance_status_contract_failures(mistyped_item) == [
        {
            "field": "items[0].changed_fields",
            "expected": "list",
            "actual_type": "str",
        }
    ]

    missing_feature = json.loads(json.dumps(report))
    missing_feature["schema_features"] = ["status_counts"]
    assert release_acceptance_status_contract_failures(missing_feature) == [
        {
            "field": "schema_features",
            "expected": list(RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES),
            "actual": ["status_counts"],
        }
    ]


def test_release_acceptance_status_reports_unreadable_sidecar(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    sidecar = tmp_path / "artifacts" / "h2" / "acceptance_summary.json"
    sidecar.write_text("{not-json", encoding="utf-8")

    report = release_acceptance_status_report(spec, repo_root=tmp_path)

    assert report["status"] == "needs_update"
    assert report["items"][0]["status"] == "unreadable"
    assert "JSONDecodeError" in report["items"][0]["error"]


def test_release_acceptance_overwrite_preserves_existing_boundaries(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    sidecar = tmp_path / "artifacts" / "h2" / "acceptance_summary.json"
    write_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
        release_boundaries=["Manual boundary note."],
    )
    artifact = tmp_path / "artifacts" / "h2" / "result.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["energy"]["total_energy"] = -1.138
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    stale = json.loads(sidecar.read_text(encoding="utf-8"))["artifact_sha256"]

    summary, _ = write_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
        overwrite=True,
    )

    assert summary["artifact_sha256"] != stale
    assert summary["release_boundaries"] == ["Manual boundary note."]


def test_release_acceptance_preview_reports_stale_without_writing(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    sidecar = tmp_path / "artifacts" / "h2" / "acceptance_summary.json"
    write_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
        release_boundaries=["Manual boundary note."],
    )
    artifact = tmp_path / "artifacts" / "h2" / "result.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["energy"]["total_energy"] = -1.138
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    before = sidecar.read_text(encoding="utf-8")

    summary, output_path, status = preview_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
        release_boundaries=["Updated boundary note."],
    )

    assert output_path == sidecar
    assert sidecar.read_text(encoding="utf-8") == before
    assert summary["release_boundaries"] == ["Updated boundary note."]
    assert status["status"] == "stale"
    assert status["changed_fields"] == ["artifact_sha256", "release_boundaries"]
    assert status["contract_failures"][0]["field"] == "artifact_sha256"


def test_release_acceptance_preserves_existing_extra_fields(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    sidecar = tmp_path / "artifacts" / "h2" / "acceptance_summary.json"
    write_release_artifact_acceptance_summary(spec, artifact_name="h2_anchor", repo_root=tmp_path)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["case_count"] = 1
    payload["policy"] = {"strict_exit_code": True}
    sidecar.write_text(json.dumps(payload), encoding="utf-8")

    report = release_acceptance_status_report(spec, repo_root=tmp_path)

    assert report["status"] == "fresh"
    assert report["items"][0]["preserved_extra_fields"] == ["case_count", "policy"]
    summary, _ = write_release_artifact_acceptance_summary(
        spec,
        artifact_name="h2_anchor",
        repo_root=tmp_path,
        overwrite=True,
    )
    assert summary["case_count"] == 1
    assert summary["policy"] == {"strict_exit_code": True}


def test_release_acceptance_status_reports_stale_sidecar(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)
    write_release_artifact_acceptance_summary(spec, artifact_name="h2_anchor", repo_root=tmp_path)
    artifact = tmp_path / "artifacts" / "h2" / "result.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["energy"]["total_energy"] = -1.139
    artifact.write_text(json.dumps(payload), encoding="utf-8")

    report = release_acceptance_status_report(spec, repo_root=tmp_path)

    assert report["status"] == "needs_update"
    assert report["status_counts"] == {"stale": 1}
    assert report["items"][0]["status"] == "stale"
    assert "artifact_sha256" in report["items"][0]["changed_fields"]
    assert report["items"][0]["contract_failures"][0]["field"] == "artifact_sha256"
    assert report["repair_plan_count"] == 1
    repair = report["repair_plan"][0]
    assert repair["artifact_name"] == "h2_anchor"
    assert repair["status"] == "stale"
    assert repair["issue"] == "contract_failure:artifact_sha256"
    assert "--dry-run" in repair["preview_command"]
    assert "--overwrite" in repair["repair_command"]


def test_release_acceptance_rejects_unknown_manifest_name(tmp_path: Path) -> None:
    config = _write_release_acceptance_fixture(tmp_path)
    spec = load_release_audit_spec(config)

    with pytest.raises(ValueError, match="no artifact named 'missing'"):
        write_release_artifact_acceptance_summary(spec, artifact_name="missing", repo_root=tmp_path)
