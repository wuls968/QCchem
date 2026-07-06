"""Read-only release status bundle validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.workflow.release_audit import RELEASE_AUDIT_SCHEMA_VERSION, RELEASE_HANDOFF_SCHEMA_VERSION

RELEASE_STATUS_SCHEMA_VERSION = "qcchem.release_status.v0.1-alpha"


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
