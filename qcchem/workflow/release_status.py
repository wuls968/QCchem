"""Read-only release status bundle validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from qcchem.workflow.release_audit import (
    RELEASE_AUDIT_SCHEMA_VERSION,
    RELEASE_DIAGNOSTICS_MANIFEST_SCHEMA_VERSION,
    RELEASE_HANDOFF_SCHEMA_VERSION,
)

RELEASE_STATUS_SCHEMA_VERSION = "qcchem.release_status.v0.1-alpha"
RELEASE_ARTIFACT_VERIFICATION_SCHEMA_VERSION = "qcchem.release_artifact_verification.v0.1-alpha"
RELEASE_HISTORY_SUMMARY_SCHEMA_VERSION = "qcchem.release_history_summary.v0.1-alpha"
RELEASE_EVIDENCE_COLLECTION_SCHEMA_VERSION = "qcchem.release_evidence_collection.v0.1-alpha"
RELEASE_HISTORY_HANDOFF_MARKDOWN_HEADING = "# QCchem Release History Handoff"


def compact_release_audit_check(check: object) -> dict[str, object] | None:
    if not isinstance(check, dict):
        return None
    compact: dict[str, object] = {
        "id": check.get("id"),
        "summary": check.get("summary"),
    }
    detail_hint = _release_audit_detail_hint(check.get("details"))
    if detail_hint:
        compact["detail_hint"] = detail_hint
    return compact


def compact_release_sidecar_repair(item: object) -> dict[str, object] | None:
    if not isinstance(item, dict):
        return None
    return {
        "artifact_name": item.get("artifact_name"),
        "status": item.get("status"),
        "issue": item.get("issue"),
        "sidecar_path": item.get("sidecar_path"),
        "preview_command": item.get("preview_command"),
        "repair_command": item.get("repair_command"),
    }


def first_compact_release_check(value: object) -> dict[str, object] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        compact = compact_release_audit_check(item)
        if compact is not None:
            return compact
    return None


def first_compact_sidecar_repair(value: object) -> dict[str, object] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        compact = compact_release_sidecar_repair(item)
        if compact is not None:
            return compact
    return None


def read_release_status_json(path: Path, *, label: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return payload


def release_status_schema_mismatches(
    *,
    readiness: dict[str, object],
    handoff: dict[str, object],
) -> list[dict[str, object]]:
    expected = {
        "release_readiness.json": RELEASE_AUDIT_SCHEMA_VERSION,
        "release_handoff.json": RELEASE_HANDOFF_SCHEMA_VERSION,
    }
    actual = {
        "release_readiness.json": readiness.get("schema_version"),
        "release_handoff.json": handoff.get("schema_version"),
    }
    mismatches: list[dict[str, object]] = []
    for file_name, expected_version in expected.items():
        actual_version = actual[file_name]
        if actual_version != expected_version:
            mismatches.append(
                {
                    "file": file_name,
                    "field": "schema_version",
                    "expected": expected_version,
                    "actual": actual_version,
                }
            )
    return mismatches


def release_status_lookup(payload: dict[str, object], field_path: tuple[str, ...]) -> tuple[bool, object]:
    current: object = payload
    for field in field_path:
        if not isinstance(current, dict) or field not in current:
            return False, None
        current = current[field]
    return True, current


def release_status_expected_type_name(expected_type: type) -> str:
    if expected_type is str:
        return "str"
    if expected_type is int:
        return "int"
    if expected_type is list:
        return "list"
    if expected_type is dict:
        return "dict"
    return expected_type.__name__


def release_status_actual_type(value: object, *, missing: bool) -> str:
    if missing:
        return "missing"
    if isinstance(value, bool):
        return "bool"
    if value is None:
        return "NoneType"
    return type(value).__name__


def release_status_type_matches(value: object, expected_type: type) -> bool:
    if expected_type is int:
        return type(value) is int
    return isinstance(value, expected_type)


def release_status_contract_mismatches(
    *,
    readiness: dict[str, object],
    handoff: dict[str, object],
) -> list[dict[str, object]]:
    required_fields = (
        ("release_readiness.json", readiness, ("status",), str),
        ("release_readiness.json", readiness, ("recommended_action",), str),
        ("release_readiness.json", readiness, ("required_pass_count",), int),
        ("release_readiness.json", readiness, ("required_fail_count",), int),
        ("release_readiness.json", readiness, ("warning_count",), int),
        ("release_readiness.json", readiness, ("required_failed_checks",), list),
        ("release_readiness.json", readiness, ("warning_checks",), list),
        ("release_readiness.json", readiness, ("release_acceptance_sidecars",), dict),
        ("release_readiness.json", readiness, ("release_acceptance_sidecars", "status"), str),
        ("release_readiness.json", readiness, ("release_acceptance_sidecars", "repair_plan"), list),
        ("release_readiness.json", readiness, ("release_acceptance_sidecars", "repair_plan_count"), int),
        ("release_handoff.json", handoff, ("status",), str),
        ("release_handoff.json", handoff, ("recommended_action",), str),
        ("release_handoff.json", handoff, ("release_readiness",), dict),
        ("release_handoff.json", handoff, ("release_readiness", "json"), str),
        ("release_handoff.json", handoff, ("release_readiness", "markdown"), str),
        ("release_handoff.json", handoff, ("release_audit",), dict),
        ("release_handoff.json", handoff, ("release_audit", "required_fail_count"), int),
        ("release_handoff.json", handoff, ("release_audit", "warning_count"), int),
        ("release_handoff.json", handoff, ("ci",), dict),
        ("release_handoff.json", handoff, ("diagnostic_artifacts",), dict),
        ("release_handoff.json", handoff, ("diagnostic_artifacts", "names"), list),
        ("release_handoff.json", handoff, ("diagnostic_artifacts", "upload_paths"), list),
        ("release_handoff.json", handoff, ("diagnostic_artifacts", "manifest"), dict),
        ("release_handoff.json", handoff, ("diagnostic_artifacts", "manifest", "path"), str),
        ("release_handoff.json", handoff, ("diagnostic_artifacts", "manifest", "schema_version"), str),
    )
    mismatches: list[dict[str, object]] = []
    for file_name, payload, field_path, expected_type in required_fields:
        exists, value = release_status_lookup(payload, field_path)
        missing = not exists
        if missing or not release_status_type_matches(value, expected_type):
            mismatches.append(
                {
                    "file": file_name,
                    "field": ".".join(field_path),
                    "expected": release_status_expected_type_name(expected_type),
                    "actual_type": release_status_actual_type(value, missing=missing),
                }
            )
    if mismatches:
        return mismatches
    mismatches.extend(release_status_consistency_mismatches(readiness=readiness, handoff=handoff))
    return mismatches


def release_status_consistency_mismatches(
    *,
    readiness: dict[str, object],
    handoff: dict[str, object],
) -> list[dict[str, object]]:
    checks = (
        (
            "release_handoff.json",
            handoff,
            ("status",),
            readiness,
            ("status",),
            "must_match_release_readiness.status",
        ),
        (
            "release_handoff.json",
            handoff,
            ("recommended_action",),
            readiness,
            ("recommended_action",),
            "must_match_release_readiness.recommended_action",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "profile"),
            readiness,
            ("profile",),
            "must_match_release_readiness.profile",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "release_version"),
            readiness,
            ("release_version",),
            "must_match_release_readiness.release_version",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "manifest_path"),
            readiness,
            ("audit_provenance", "manifest_path"),
            "must_match_release_readiness.audit_provenance.manifest_path",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "output_dir"),
            readiness,
            ("audit_provenance", "output_dir"),
            "must_match_release_readiness.audit_provenance.output_dir",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "required_fail_count"),
            readiness,
            ("required_fail_count",),
            "must_match_release_readiness.required_fail_count",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "warning_count"),
            readiness,
            ("warning_count",),
            "must_match_release_readiness.warning_count",
        ),
        (
            "release_handoff.json",
            handoff,
            ("release_audit", "release_acceptance_sidecars_status"),
            readiness,
            ("release_acceptance_sidecars", "status"),
            "must_match_release_readiness.release_acceptance_sidecars.status",
        ),
    )
    mismatches: list[dict[str, object]] = []
    for file_name, actual_payload, actual_path, expected_payload, expected_path, reason in checks:
        actual_exists, actual = release_status_lookup(actual_payload, actual_path)
        expected_exists, expected = release_status_lookup(expected_payload, expected_path)
        if not actual_exists or not expected_exists:
            continue
        if actual != expected:
            mismatches.append(
                _release_status_value_mismatch(
                    file_name=file_name,
                    field_path=actual_path,
                    expected=expected,
                    actual=actual,
                    reason=reason,
                )
            )

    readiness_required_fail_count = readiness.get("required_fail_count")
    required_failed_checks = readiness.get("required_failed_checks")
    if isinstance(readiness_required_fail_count, int) and isinstance(required_failed_checks, list):
        if readiness_required_fail_count != len(required_failed_checks):
            mismatches.append(
                _release_status_value_mismatch(
                    file_name="release_readiness.json",
                    field_path=("required_fail_count",),
                    expected=len(required_failed_checks),
                    actual=readiness_required_fail_count,
                    reason="must_equal_required_failed_checks_length",
                )
            )
    warning_count = readiness.get("warning_count")
    warning_checks = readiness.get("warning_checks")
    if isinstance(warning_count, int) and isinstance(warning_checks, list):
        if warning_count != len(warning_checks):
            mismatches.append(
                _release_status_value_mismatch(
                    file_name="release_readiness.json",
                    field_path=("warning_count",),
                    expected=len(warning_checks),
                    actual=warning_count,
                    reason="must_equal_warning_checks_length",
                )
            )

    readiness_status = readiness.get("status")
    if isinstance(readiness_required_fail_count, int) and isinstance(readiness_status, str):
        expected_status = "passed" if readiness_required_fail_count == 0 else "failed"
        if readiness_status != expected_status:
            mismatches.append(
                _release_status_value_mismatch(
                    file_name="release_readiness.json",
                    field_path=("status",),
                    expected=expected_status,
                    actual=readiness_status,
                    reason="must_match_required_fail_count",
                )
            )
    sidecars = readiness.get("release_acceptance_sidecars")
    if isinstance(sidecars, dict):
        repair_plan = sidecars.get("repair_plan")
        repair_plan_count = sidecars.get("repair_plan_count")
        if isinstance(repair_plan, list) and isinstance(repair_plan_count, int):
            if repair_plan_count != len(repair_plan):
                mismatches.append(
                    _release_status_value_mismatch(
                        file_name="release_readiness.json",
                        field_path=("release_acceptance_sidecars", "repair_plan_count"),
                        expected=len(repair_plan),
                        actual=repair_plan_count,
                        reason="must_equal_release_acceptance_sidecars.repair_plan_length",
                    )
                )
    manifest = handoff.get("diagnostic_artifacts")
    manifest = manifest.get("manifest") if isinstance(manifest, dict) else None
    if isinstance(manifest, dict):
        manifest_schema_version = manifest.get("schema_version")
        if manifest_schema_version != RELEASE_DIAGNOSTICS_MANIFEST_SCHEMA_VERSION:
            mismatches.append(
                _release_status_value_mismatch(
                    file_name="release_handoff.json",
                    field_path=("diagnostic_artifacts", "manifest", "schema_version"),
                    expected=RELEASE_DIAGNOSTICS_MANIFEST_SCHEMA_VERSION,
                    actual=manifest_schema_version,
                    reason="must_match_release_diagnostics_manifest_schema_version",
                )
            )
    return mismatches


def validate_release_status_bundle(
    *,
    readiness: dict[str, object],
    handoff: dict[str, object],
) -> list[dict[str, object]]:
    """Return schema, contract, and consistency failures for a release bundle."""

    schema_mismatches = release_status_schema_mismatches(readiness=readiness, handoff=handoff)
    if schema_mismatches:
        return schema_mismatches
    return release_status_contract_mismatches(readiness=readiness, handoff=handoff)


def build_release_status_summary(audit_dir: Path) -> dict[str, object]:
    """Summarize existing release audit handoff outputs without rerunning the audit."""

    readiness_json = audit_dir / "release_readiness.json"
    readiness_md = audit_dir / "release_readiness.md"
    handoff_json = audit_dir / "release_handoff.json"
    handoff_md = audit_dir / "release_handoff.md"
    missing = [path.name for path in (readiness_json, handoff_json) if not path.exists()]
    base: dict[str, object] = {
        "schema_version": RELEASE_STATUS_SCHEMA_VERSION,
        "audit_dir": str(audit_dir),
        "release_readiness": {
            "json": str(readiness_json),
            "markdown": str(readiness_md),
        },
        "release_handoff": {
            "json": str(handoff_json),
            "markdown": str(handoff_md),
        },
    }
    if missing:
        base.update(
            {
                "status": "missing_outputs",
                "recommended_action": "run_release_audit",
                "missing_files": missing,
            }
        )
        return base

    try:
        readiness = read_release_status_json(readiness_json, label="release_readiness.json")
        handoff = read_release_status_json(handoff_json, label="release_handoff.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        base.update(
            {
                "status": "unreadable_outputs",
                "recommended_action": "rerun_release_audit",
                "error": str(exc),
            }
        )
        return base

    schema_mismatches = release_status_schema_mismatches(readiness=readiness, handoff=handoff)
    if schema_mismatches:
        base.update(
            {
                "status": "schema_mismatch",
                "recommended_action": "rerun_release_audit",
                "schema_mismatches": schema_mismatches,
            }
        )
        return base

    contract_mismatches = release_status_contract_mismatches(readiness=readiness, handoff=handoff)
    if contract_mismatches:
        base.update(
            {
                "status": "contract_mismatch",
                "recommended_action": "rerun_release_audit",
                "contract_mismatches": contract_mismatches,
            }
        )
        return base

    sidecars = readiness.get("release_acceptance_sidecars")
    sidecar_status = sidecars.get("status") if isinstance(sidecars, dict) else None
    repair_plan = sidecars.get("repair_plan") if isinstance(sidecars, dict) else None
    diagnostic_artifacts = handoff.get("diagnostic_artifacts")
    ci = handoff.get("ci")
    base.update(
        {
            "status": readiness.get("status"),
            "recommended_action": readiness.get("recommended_action"),
            "required_pass_count": readiness.get("required_pass_count"),
            "required_fail_count": readiness.get("required_fail_count"),
            "warning_count": readiness.get("warning_count"),
            "release_acceptance_sidecars_status": sidecar_status,
            "release_acceptance_sidecars_repair_plan_count": (
                sidecars.get("repair_plan_count") if isinstance(sidecars, dict) else None
            ),
            "ci": ci if isinstance(ci, dict) else {},
            "diagnostic_artifacts": diagnostic_artifacts if isinstance(diagnostic_artifacts, dict) else {},
            "first_required_failure": first_compact_release_check(readiness.get("required_failed_checks")),
            "first_warning": first_compact_release_check(readiness.get("warning_checks")),
            "first_sidecar_repair": first_compact_sidecar_repair(repair_plan),
        }
    )
    return base


def verify_release_diagnostics_artifacts(artifact_dir: Path) -> dict[str, object]:
    """Verify a downloaded CI release diagnostics artifact directory."""

    artifact_dir = Path(artifact_dir)
    failures: list[dict[str, object]] = []
    report: dict[str, object] = {
        "schema_version": RELEASE_ARTIFACT_VERIFICATION_SCHEMA_VERSION,
        "artifact_dir": str(artifact_dir),
        "release_statuses": [],
        "diagnostics_manifests": [],
        "acceptance_statuses": [],
        "release_history_handoffs": [],
        "failures": failures,
    }
    if not artifact_dir.exists():
        failures.append({"reason": "artifact_dir_missing", "path": str(artifact_dir)})
        _finalize_release_artifact_verification_report(report)
        return report
    if not artifact_dir.is_dir():
        failures.append({"reason": "artifact_dir_not_directory", "path": str(artifact_dir)})
        _finalize_release_artifact_verification_report(report)
        return report

    release_status_paths = sorted(artifact_dir.rglob("release_status.json"))
    diagnostics_manifest_paths = sorted(artifact_dir.rglob("release_diagnostics_manifest.json"))
    acceptance_status_paths = sorted(artifact_dir.rglob("qcchem-release-acceptance-status.json"))
    release_history_summary_paths = sorted(artifact_dir.rglob("release_history_summary.json"))

    release_statuses = report["release_statuses"]
    assert isinstance(release_statuses, list)
    for status_path in release_status_paths:
        release_statuses.append(_verify_downloaded_release_status(status_path, failures))
    if not release_status_paths:
        failures.append({"reason": "missing_release_status_files", "path": str(artifact_dir)})

    diagnostics_manifests = report["diagnostics_manifests"]
    assert isinstance(diagnostics_manifests, list)
    for manifest_path in diagnostics_manifest_paths:
        diagnostics_manifests.append(_verify_diagnostics_manifest(manifest_path, failures))
    if not diagnostics_manifest_paths:
        failures.append({"reason": "missing_diagnostics_manifests", "path": str(artifact_dir)})

    acceptance_statuses = report["acceptance_statuses"]
    assert isinstance(acceptance_statuses, list)
    for status_path in acceptance_status_paths:
        acceptance_statuses.append(_verify_acceptance_status(status_path, failures))
    if not acceptance_status_paths:
        failures.append({"reason": "missing_acceptance_status_files", "path": str(artifact_dir)})

    release_history_handoffs = report["release_history_handoffs"]
    assert isinstance(release_history_handoffs, list)
    for summary_path in release_history_summary_paths:
        release_history_handoffs.append(_verify_release_history_handoff(summary_path, failures))
    if not release_history_summary_paths:
        failures.append({"reason": "missing_release_history_summary_files", "path": str(artifact_dir)})

    _finalize_release_artifact_verification_report(report)
    return report


def _verify_downloaded_release_status(
    status_path: Path,
    failures: list[dict[str, object]],
) -> dict[str, object]:
    audit_dir = status_path.parent
    summary = build_release_status_summary(audit_dir)
    entry = {
        "path": str(status_path),
        "audit_dir": str(audit_dir),
        "status": summary.get("status"),
        "required_pass_count": summary.get("required_pass_count"),
        "required_fail_count": summary.get("required_fail_count"),
        "warning_count": summary.get("warning_count"),
        "release_acceptance_sidecars_status": summary.get("release_acceptance_sidecars_status"),
    }
    if summary.get("status") != "passed":
        failures.append(
            {
                "reason": "release_status_not_passed",
                "path": str(status_path),
                "status": summary.get("status"),
                "recommended_action": summary.get("recommended_action"),
            }
        )
    schema_mismatches = summary.get("schema_mismatches")
    if isinstance(schema_mismatches, list) and schema_mismatches:
        failures.append(
            {
                "reason": "release_status_schema_mismatch",
                "path": str(status_path),
                "schema_mismatches": schema_mismatches,
            }
        )
    contract_mismatches = summary.get("contract_mismatches")
    if isinstance(contract_mismatches, list) and contract_mismatches:
        failures.append(
            {
                "reason": "release_status_contract_mismatch",
                "path": str(status_path),
                "contract_mismatches": contract_mismatches,
            }
        )
    return entry


def _verify_diagnostics_manifest(
    manifest_path: Path,
    failures: list[dict[str, object]],
) -> dict[str, object]:
    try:
        manifest = read_release_status_json(manifest_path, label="release_diagnostics_manifest.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            {
                "reason": "diagnostics_manifest_unreadable",
                "path": str(manifest_path),
                "error": str(exc),
            }
        )
        return {"path": str(manifest_path), "status": "unreadable"}

    entry = {
        "path": str(manifest_path),
        "schema_version": manifest.get("schema_version"),
        "file_count": manifest.get("file_count"),
        "present_count": manifest.get("present_count"),
        "digest_count": manifest.get("digest_count"),
        "omitted_count": manifest.get("omitted_count"),
    }
    if manifest.get("schema_version") != RELEASE_DIAGNOSTICS_MANIFEST_SCHEMA_VERSION:
        failures.append(
            {
                "reason": "diagnostics_manifest_schema_mismatch",
                "path": str(manifest_path),
                "expected": RELEASE_DIAGNOSTICS_MANIFEST_SCHEMA_VERSION,
                "actual": manifest.get("schema_version"),
            }
        )

    missing_paths = manifest.get("missing_paths")
    if isinstance(missing_paths, list) and missing_paths:
        failures.append(
            {
                "reason": "diagnostics_manifest_missing_paths",
                "path": str(manifest_path),
                "missing_paths": missing_paths,
            }
        )
    non_file_paths = manifest.get("non_file_paths")
    if isinstance(non_file_paths, list) and non_file_paths:
        failures.append(
            {
                "reason": "diagnostics_manifest_non_file_paths",
                "path": str(manifest_path),
                "non_file_paths": non_file_paths,
            }
        )

    files = manifest.get("files")
    if not isinstance(files, list):
        failures.append(
            {
                "reason": "diagnostics_manifest_files_not_list",
                "path": str(manifest_path),
                "actual_type": release_status_actual_type(files, missing="files" not in manifest),
            }
        )
        return entry

    _check_diagnostics_manifest_count(
        failures,
        manifest_path=manifest_path,
        field="file_count",
        expected=len(files),
        actual=manifest.get("file_count"),
    )
    _check_diagnostics_manifest_count(
        failures,
        manifest_path=manifest_path,
        field="present_count",
        expected=sum(1 for record in files if isinstance(record, dict) and record.get("status") == "present"),
        actual=manifest.get("present_count"),
    )
    _check_diagnostics_manifest_count(
        failures,
        manifest_path=manifest_path,
        field="digest_count",
        expected=sum(1 for record in files if isinstance(record, dict) and record.get("sha256")),
        actual=manifest.get("digest_count"),
    )
    omitted_paths = manifest.get("omitted_paths")
    if isinstance(omitted_paths, list):
        _check_diagnostics_manifest_count(
            failures,
            manifest_path=manifest_path,
            field="omitted_count",
            expected=len(omitted_paths),
            actual=manifest.get("omitted_count"),
        )

    artifact_root = _downloaded_artifact_root(
        local_path=manifest_path,
        remote_path=manifest.get("manifest_path"),
    )
    if artifact_root is None:
        failures.append(
            {
                "reason": "diagnostics_manifest_path_unmappable",
                "path": str(manifest_path),
                "manifest_path": manifest.get("manifest_path"),
            }
        )
        return entry

    for index, record in enumerate(files):
        if not isinstance(record, dict):
            failures.append(
                {
                    "reason": "diagnostics_manifest_record_not_object",
                    "path": str(manifest_path),
                    "index": index,
                    "actual_type": release_status_actual_type(record, missing=False),
                }
            )
            continue
        _verify_diagnostics_manifest_record(
            record,
            artifact_root=artifact_root,
            manifest_path=manifest_path,
            index=index,
            failures=failures,
        )
    return entry


def _verify_acceptance_status(
    status_path: Path,
    failures: list[dict[str, object]],
) -> dict[str, object]:
    try:
        status = read_release_status_json(status_path, label="qcchem-release-acceptance-status.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            {
                "reason": "acceptance_status_unreadable",
                "path": str(status_path),
                "error": str(exc),
            }
        )
        return {"path": str(status_path), "status": "unreadable"}

    from qcchem.workflow.release_acceptance import release_acceptance_status_contract_failures

    entry = {
        "path": str(status_path),
        "status": status.get("status"),
        "total_sidecars": status.get("total_sidecars"),
        "fresh_count": status.get("fresh_count"),
        "requires_update_count": status.get("requires_update_count"),
        "repair_plan_count": status.get("repair_plan_count"),
    }
    contract_failures = release_acceptance_status_contract_failures(status)
    if contract_failures:
        failures.append(
            {
                "reason": "acceptance_status_contract_failure",
                "path": str(status_path),
                "contract_failures": contract_failures,
            }
        )
    if status.get("status") != "fresh":
        failures.append(
            {
                "reason": "acceptance_status_not_fresh",
                "path": str(status_path),
                "status": status.get("status"),
            }
        )
    if status.get("repair_plan_count") != 0:
        failures.append(
            {
                "reason": "acceptance_status_repair_plan_not_empty",
                "path": str(status_path),
                "repair_plan_count": status.get("repair_plan_count"),
            }
        )
    return entry


def _verify_release_history_handoff(
    summary_path: Path,
    failures: list[dict[str, object]],
) -> dict[str, object]:
    markdown_path = summary_path.with_suffix(".md")
    current_evidence_path = summary_path.parent / "release_history" / "current" / "release_evidence_summary.json"
    entry: dict[str, object] = {
        "path": str(summary_path),
        "markdown_path": str(markdown_path),
        "current_release_evidence_summary_path": str(current_evidence_path),
    }
    try:
        summary = read_release_status_json(summary_path, label="release_history_summary.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            {
                "reason": "release_history_summary_unreadable",
                "path": str(summary_path),
                "error": str(exc),
            }
        )
        entry["status"] = "unreadable"
        _verify_release_history_markdown(markdown_path, summary_path=summary_path, failures=failures)
        _verify_release_history_current_evidence(current_evidence_path, summary_path=summary_path, failures=failures)
        return entry

    entry.update(
        {
            "schema_version": summary.get("schema_version"),
            "status": summary.get("status"),
            "recommended_action": summary.get("recommended_action"),
            "run_count": summary.get("run_count"),
            "passed_run_count": summary.get("passed_run_count"),
            "failed_run_count": summary.get("failed_run_count"),
            "incomplete_run_count": summary.get("incomplete_run_count"),
        }
    )
    if summary.get("schema_version") != RELEASE_HISTORY_SUMMARY_SCHEMA_VERSION:
        failures.append(
            {
                "reason": "release_history_summary_schema_mismatch",
                "path": str(summary_path),
                "expected": RELEASE_HISTORY_SUMMARY_SCHEMA_VERSION,
                "actual": summary.get("schema_version"),
            }
        )
    if summary.get("status") != "passed":
        failures.append(
            {
                "reason": "release_history_summary_not_passed",
                "path": str(summary_path),
                "status": summary.get("status"),
                "recommended_action": summary.get("recommended_action"),
            }
        )
    run_count = summary.get("run_count")
    if not isinstance(run_count, int) or run_count < 1:
        failures.append(
            {
                "reason": "release_history_summary_run_count_invalid",
                "path": str(summary_path),
                "actual": run_count,
            }
        )

    _verify_release_history_markdown(markdown_path, summary_path=summary_path, failures=failures)
    current_evidence = _verify_release_history_current_evidence(
        current_evidence_path,
        summary_path=summary_path,
        failures=failures,
    )
    if current_evidence:
        entry["current_release_evidence_status"] = current_evidence.get("status")
        entry["current_release_evidence_schema_version"] = current_evidence.get("schema_version")
    return entry


def _verify_release_history_markdown(
    markdown_path: Path,
    *,
    summary_path: Path,
    failures: list[dict[str, object]],
) -> None:
    if not markdown_path.exists():
        failures.append(
            {
                "reason": "release_history_markdown_missing",
                "path": str(summary_path),
                "markdown_path": str(markdown_path),
            }
        )
        return
    if not markdown_path.is_file():
        failures.append(
            {
                "reason": "release_history_markdown_not_file",
                "path": str(summary_path),
                "markdown_path": str(markdown_path),
            }
        )
        return
    try:
        markdown = markdown_path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(
            {
                "reason": "release_history_markdown_unreadable",
                "path": str(summary_path),
                "markdown_path": str(markdown_path),
                "error": str(exc),
            }
        )
        return
    if RELEASE_HISTORY_HANDOFF_MARKDOWN_HEADING not in markdown:
        failures.append(
            {
                "reason": "release_history_markdown_heading_missing",
                "path": str(summary_path),
                "markdown_path": str(markdown_path),
                "expected": RELEASE_HISTORY_HANDOFF_MARKDOWN_HEADING,
            }
        )
    if summary_path.name not in markdown:
        failures.append(
            {
                "reason": "release_history_markdown_summary_reference_missing",
                "path": str(summary_path),
                "markdown_path": str(markdown_path),
                "expected": summary_path.name,
            }
        )


def _verify_release_history_current_evidence(
    evidence_path: Path,
    *,
    summary_path: Path,
    failures: list[dict[str, object]],
) -> dict[str, object] | None:
    if not evidence_path.exists():
        failures.append(
            {
                "reason": "release_history_current_evidence_missing",
                "path": str(summary_path),
                "current_release_evidence_summary_path": str(evidence_path),
            }
        )
        return None
    if not evidence_path.is_file():
        failures.append(
            {
                "reason": "release_history_current_evidence_not_file",
                "path": str(summary_path),
                "current_release_evidence_summary_path": str(evidence_path),
            }
        )
        return None
    try:
        evidence = read_release_status_json(evidence_path, label="release_evidence_summary.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        failures.append(
            {
                "reason": "release_history_current_evidence_unreadable",
                "path": str(summary_path),
                "current_release_evidence_summary_path": str(evidence_path),
                "error": str(exc),
            }
        )
        return None
    if evidence.get("schema_version") != RELEASE_EVIDENCE_COLLECTION_SCHEMA_VERSION:
        failures.append(
            {
                "reason": "release_history_current_evidence_schema_mismatch",
                "path": str(summary_path),
                "current_release_evidence_summary_path": str(evidence_path),
                "expected": RELEASE_EVIDENCE_COLLECTION_SCHEMA_VERSION,
                "actual": evidence.get("schema_version"),
            }
        )
    if evidence.get("status") != "passed":
        failures.append(
            {
                "reason": "release_history_current_evidence_not_passed",
                "path": str(summary_path),
                "current_release_evidence_summary_path": str(evidence_path),
                "status": evidence.get("status"),
                "recommended_action": evidence.get("recommended_action"),
            }
        )
    return evidence


def _verify_diagnostics_manifest_record(
    record: dict[str, object],
    *,
    artifact_root: Path,
    manifest_path: Path,
    index: int,
    failures: list[dict[str, object]],
) -> None:
    if record.get("status") != "present":
        return
    local_path = _downloaded_file_path(artifact_root, record.get("resolved_path") or record.get("path"))
    if local_path is None:
        failures.append(
            {
                "reason": "diagnostics_manifest_record_path_unmappable",
                "path": str(manifest_path),
                "index": index,
                "record_path": record.get("path"),
                "resolved_path": record.get("resolved_path"),
            }
        )
        return
    if not local_path.exists():
        failures.append(
            {
                "reason": "diagnostics_manifest_local_file_missing",
                "path": str(manifest_path),
                "index": index,
                "local_path": str(local_path),
                "record_path": record.get("path"),
            }
        )
        return
    if not local_path.is_file():
        failures.append(
            {
                "reason": "diagnostics_manifest_local_path_not_file",
                "path": str(manifest_path),
                "index": index,
                "local_path": str(local_path),
                "record_path": record.get("path"),
            }
        )
        return
    expected_size = record.get("size_bytes")
    actual_size = local_path.stat().st_size
    if expected_size != actual_size:
        failures.append(
            {
                "reason": "diagnostics_manifest_size_mismatch",
                "path": str(manifest_path),
                "index": index,
                "local_path": str(local_path),
                "record_path": record.get("path"),
                "expected": expected_size,
                "actual": actual_size,
            }
        )
    expected_sha256 = record.get("sha256")
    actual_sha256 = _file_sha256(local_path)
    if expected_sha256 != actual_sha256:
        failures.append(
            {
                "reason": "diagnostics_manifest_sha256_mismatch",
                "path": str(manifest_path),
                "index": index,
                "local_path": str(local_path),
                "record_path": record.get("path"),
                "expected": expected_sha256,
                "actual": actual_sha256,
            }
        )


def _check_diagnostics_manifest_count(
    failures: list[dict[str, object]],
    *,
    manifest_path: Path,
    field: str,
    expected: int,
    actual: object,
) -> None:
    if actual != expected:
        failures.append(
            {
                "reason": "diagnostics_manifest_count_mismatch",
                "path": str(manifest_path),
                "field": field,
                "expected": expected,
                "actual": actual,
            }
        )


def _downloaded_artifact_root(*, local_path: Path, remote_path: object) -> Path | None:
    suffix = _portable_path_suffix_parts(remote_path)
    if not suffix:
        return None
    local_parts = local_path.resolve().parts
    if len(local_parts) < len(suffix):
        return None
    if tuple(local_parts[-len(suffix) :]) != suffix:
        return None
    root_parts = local_parts[: -len(suffix)]
    if not root_parts:
        return Path(".")
    return Path(*root_parts)


def _downloaded_file_path(artifact_root: Path, remote_path: object) -> Path | None:
    suffix = _portable_path_suffix_parts(remote_path)
    if not suffix:
        return None
    return artifact_root.joinpath(*suffix)


def _portable_path_suffix_parts(path_value: object) -> tuple[str, ...] | None:
    if not isinstance(path_value, str) or not path_value:
        return None
    path = Path(path_value)
    parts = path.parts
    if path.anchor and parts and parts[0] == path.anchor:
        parts = parts[1:]
    return tuple(part for part in parts if part not in {"", "."})


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finalize_release_artifact_verification_report(report: dict[str, object]) -> None:
    failures = report.get("failures")
    failure_count = len(failures) if isinstance(failures, list) else 0
    release_statuses = report.get("release_statuses")
    diagnostics_manifests = report.get("diagnostics_manifests")
    acceptance_statuses = report.get("acceptance_statuses")
    release_history_handoffs = report.get("release_history_handoffs")
    report["status"] = "passed" if failure_count == 0 else "failed"
    report["summary"] = {
        "release_status_count": len(release_statuses) if isinstance(release_statuses, list) else 0,
        "diagnostics_manifest_count": len(diagnostics_manifests) if isinstance(diagnostics_manifests, list) else 0,
        "acceptance_status_count": len(acceptance_statuses) if isinstance(acceptance_statuses, list) else 0,
        "release_history_handoff_count": (
            len(release_history_handoffs) if isinstance(release_history_handoffs, list) else 0
        ),
        "failure_count": failure_count,
    }


def _release_status_value_mismatch(
    *,
    file_name: str,
    field_path: tuple[str, ...],
    expected: object,
    actual: object,
    reason: str,
) -> dict[str, object]:
    return {
        "file": file_name,
        "field": ".".join(field_path),
        "reason": reason,
        "expected": expected,
        "actual": actual,
    }


def _release_audit_detail_hint(details: object) -> str | None:
    if not isinstance(details, dict):
        return None
    artifact = details.get("artifact")
    if isinstance(artifact, str) and artifact:
        return f"artifact={artifact}"
    path = details.get("path")
    if isinstance(path, str) and path:
        return f"path={path}"
    manifest_path = details.get("manifest_path")
    if isinstance(manifest_path, str) and manifest_path:
        return f"manifest={manifest_path}"
    failures = details.get("failures")
    if isinstance(failures, list) and failures:
        return f"failure={_compact_detail_value(failures[0])}"
    contract_failures = details.get("contract_failures")
    if isinstance(contract_failures, list) and contract_failures:
        first = next((failure for failure in contract_failures if isinstance(failure, dict)), None)
        if first is None:
            return f"contract_failure={_compact_detail_value(contract_failures[0])}"
        field = first.get("field")
        reason = first.get("reason")
        if field and reason:
            return f"contract_failure={field}:{reason}"
        if field:
            return f"contract_failure={field}"
        if reason:
            return f"contract_failure={reason}"
        return "contract_failure"
    unexpected = details.get("unexpected_ids")
    if isinstance(unexpected, list) and unexpected:
        return "unexpected_warning=" + ",".join(str(item) for item in unexpected[:3])
    return None


def _compact_detail_value(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("id", "field", "reason", "path", "artifact"):
            item = value.get(key)
            if item:
                return str(item)
        return json.dumps(value, sort_keys=True)
    return str(value)
