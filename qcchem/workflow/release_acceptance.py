"""Release-bound artifact acceptance sidecar writer."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

from qcchem.io.config import workspace_root_for_path
from qcchem.io.release_audit_config import ReleaseAuditSpec, load_release_audit_spec
from qcchem.reporting import write_result_json
from qcchem.workflow.release_audit import (
    RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION,
    _acceptance_contract_failures,
    _file_sha256,
    _payload_with_release_evidence,
    _read_json,
    _runtime_evidence_status,
    _resolve,
)

DEFAULT_RELEASE_ACCEPTANCE_SCOPE = "alpha_release_boundary"
DEFAULT_RELEASE_ACCEPTANCE_ACTION = "accept_release_artifact_with_declared_boundary"
DEFAULT_RELEASE_BOUNDARIES = [
    "Accepted as release-readable evidence with the declared trust tier.",
    "This sidecar does not promote the artifact beyond its evidence_summary boundary.",
]
RELEASE_ACCEPTANCE_STATUS_SCHEMA_VERSION = "qcchem.release_artifact_acceptance_status.v0.1-alpha"
RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES = [
    "status_counts",
    "repair_plan",
    "repair_plan_count",
    "item_changed_fields",
    "item_missing_fields",
    "item_contract_failures",
    "repair_commands",
]


def _acceptance_status_expected_type_name(expected_type: type | tuple[type, ...]) -> str:
    if isinstance(expected_type, tuple):
        return "|".join(_acceptance_status_expected_type_name(item) for item in expected_type)
    if expected_type is str:
        return "str"
    if expected_type is int:
        return "int"
    if expected_type is list:
        return "list"
    if expected_type is dict:
        return "dict"
    if expected_type is type(None):
        return "NoneType"
    return expected_type.__name__


def _acceptance_status_actual_type(value: object, *, missing: bool) -> str:
    if missing:
        return "missing"
    if isinstance(value, bool):
        return "bool"
    if value is None:
        return "NoneType"
    return type(value).__name__


def _acceptance_status_type_matches(value: object, expected_type: type | tuple[type, ...]) -> bool:
    expected_types = expected_type if isinstance(expected_type, tuple) else (expected_type,)
    if int in expected_types and isinstance(value, bool):
        return False
    return isinstance(value, expected_types)


def _acceptance_status_require_fields(
    payload: dict[str, Any],
    required_fields: tuple[tuple[str, type | tuple[type, ...]], ...],
    *,
    prefix: str = "",
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for field, expected_type in required_fields:
        exists = field in payload
        value = payload.get(field)
        if not exists or not _acceptance_status_type_matches(value, expected_type):
            failures.append(
                {
                    "field": f"{prefix}.{field}" if prefix else field,
                    "expected": _acceptance_status_expected_type_name(expected_type),
                    "actual_type": _acceptance_status_actual_type(value, missing=not exists),
                }
            )
    return failures


def release_acceptance_status_contract_failures(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return schema-contract failures for a release acceptance status report."""

    failures: list[dict[str, Any]] = []
    schema_version = report.get("schema_version")
    if schema_version != RELEASE_ACCEPTANCE_STATUS_SCHEMA_VERSION:
        failures.append(
            {
                "field": "schema_version",
                "expected": RELEASE_ACCEPTANCE_STATUS_SCHEMA_VERSION,
                "actual": schema_version,
            }
        )

    failures.extend(
        _acceptance_status_require_fields(
            report,
            (
                ("schema_version", str),
                ("schema_features", list),
                ("status", str),
                ("repo_root", str),
                ("total_sidecars", int),
                ("fresh_count", int),
                ("requires_update_count", int),
                ("status_counts", dict),
                ("repair_plan", list),
                ("repair_plan_count", int),
                ("items", list),
            ),
        )
    )
    schema_features = report.get("schema_features")
    if isinstance(schema_features, list) and schema_features != list(
        RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES
    ):
        failures.append(
            {
                "field": "schema_features",
                "expected": list(RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES),
                "actual": schema_features,
            }
        )

    items = report.get("items")
    if isinstance(items, list):
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                failures.append(
                    {
                        "field": f"items[{index}]",
                        "expected": "dict",
                        "actual_type": _acceptance_status_actual_type(item, missing=False),
                    }
                )
                continue
            failures.extend(
                _acceptance_status_require_fields(
                    item,
                    (
                        ("artifact_name", str),
                        ("artifact_kind", str),
                        ("artifact_path", str),
                        ("sidecar_path", str),
                        ("release_audit_check_id", str),
                        ("status", str),
                        ("changed_fields", list),
                        ("missing_fields", list),
                        ("extra_fields", list),
                        ("preserved_extra_fields", list),
                        ("contract_failures", list),
                    ),
                    prefix=f"items[{index}]",
                )
            )

    repair_plan = report.get("repair_plan")
    if isinstance(repair_plan, list):
        for index, item in enumerate(repair_plan):
            if not isinstance(item, dict):
                failures.append(
                    {
                        "field": f"repair_plan[{index}]",
                        "expected": "dict",
                        "actual_type": _acceptance_status_actual_type(item, missing=False),
                    }
                )
                continue
            failures.extend(
                _acceptance_status_require_fields(
                    item,
                    (
                        ("artifact_name", str),
                        ("artifact_kind", str),
                        ("status", str),
                        ("issue", str),
                        ("artifact_path", str),
                        ("sidecar_path", str),
                        ("changed_fields", list),
                        ("missing_fields", list),
                        ("contract_failures", list),
                        ("recommended_action", str),
                        ("preview_command", (str, type(None))),
                        ("repair_command", (str, type(None))),
                    ),
                    prefix=f"repair_plan[{index}]",
                )
            )

    return failures


def _repo_relative_artifact_path(artifact_path: Path, *, repo_root: Path) -> str:
    try:
        return artifact_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"Release acceptance artifact must be inside repo root: {artifact_path}") from exc


def _release_boundaries_from_existing(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    try:
        payload = _read_json(path)
    except Exception:
        return None
    boundaries = payload.get("release_boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        return None
    cleaned = [
        str(item).strip()
        for item in boundaries
        if isinstance(item, str) and item.strip()
    ]
    return cleaned or None


def _summary_with_existing_extra_fields(summary: dict[str, Any], path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return summary, []
    try:
        existing = _read_json(path)
    except Exception:
        return summary, []
    extras = {
        key: value
        for key, value in existing.items()
        if key not in summary
    }
    return {**extras, **summary}, sorted(extras)


def _release_acceptance_targets(spec: ReleaseAuditSpec) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for artifact in spec.curated_artifacts:
        targets.append(
            {
                "name": artifact.name,
                "path": artifact.path,
                "kind": "curated_artifact",
                "check_id": f"curated_artifact:{artifact.name}:acceptance_summary",
            }
        )
    for asset in spec.exploratory_assets:
        targets.append(
            {
                "name": asset.name,
                "path": asset.artifact,
                "kind": "exploratory_asset",
                "check_id": f"exploratory_asset:{asset.name}:acceptance_summary",
            }
        )
    return targets


def resolve_release_acceptance_target(spec: ReleaseAuditSpec, artifact_name: str) -> dict[str, Any]:
    """Resolve one release manifest artifact or artifact-backed exploratory asset."""

    targets = _release_acceptance_targets(spec)
    matches = [target for target in targets if target["name"] == artifact_name]
    if not matches:
        available = ", ".join(target["name"] for target in targets) or "none"
        raise ValueError(
            f"Release manifest has no artifact named '{artifact_name}'. "
            f"Available: {available}."
        )
    artifact_targets = [target for target in matches if target["path"] is not None]
    if not artifact_targets:
        raise ValueError(f"Release manifest entry '{artifact_name}' does not declare an artifact path.")
    if len(artifact_targets) > 1:
        kinds = ", ".join(str(target["kind"]) for target in artifact_targets)
        raise ValueError(
            f"Release manifest artifact name '{artifact_name}' is ambiguous across: {kinds}."
        )
    return artifact_targets[0]


def build_release_artifact_acceptance_summary(
    artifact_path: Path,
    *,
    artifact_name: str,
    release_audit_check_id: str,
    repo_root: Path,
    release_boundaries: list[str] | None = None,
    acceptance_scope: str = DEFAULT_RELEASE_ACCEPTANCE_SCOPE,
    recommended_action: str = DEFAULT_RELEASE_ACCEPTANCE_ACTION,
) -> dict[str, Any]:
    """Build a release-bound acceptance sidecar payload for one artifact."""

    resolved_repo_root = repo_root.resolve()
    resolved_artifact_path = _resolve(resolved_repo_root, artifact_path).resolve()
    if not resolved_artifact_path.is_file():
        raise ValueError(
            "Release acceptance artifact does not exist or is not a file: "
            f"{resolved_artifact_path}"
        )
    artifact_payload = _payload_with_release_evidence(_read_json(resolved_artifact_path))
    evidence = artifact_payload.get("evidence_summary")
    if not isinstance(evidence, dict):
        raise ValueError(
            "Release acceptance artifact has no release-readable evidence_summary: "
            f"{artifact_path}"
        )
    trust_tier = evidence.get("trust_tier")
    if not isinstance(trust_tier, str) or not trust_tier.strip():
        raise ValueError(
            "Release acceptance artifact has no non-empty evidence_summary.trust_tier: "
            f"{artifact_path}"
        )
    runtime_status = _runtime_evidence_status(artifact_payload)
    if runtime_status is None:
        runtime_status = "none"
    boundaries = [
        str(item).strip()
        for item in (release_boundaries or DEFAULT_RELEASE_BOUNDARIES)
        if isinstance(item, str) and str(item).strip()
    ]
    if not boundaries:
        raise ValueError("Release acceptance sidecar requires at least one release boundary note.")

    summary = {
        "schema_version": RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION,
        "artifact_name": artifact_name,
        "artifact_path": _repo_relative_artifact_path(resolved_artifact_path, repo_root=resolved_repo_root),
        "accepted": True,
        "acceptance_scope": acceptance_scope,
        "trust_tier": trust_tier,
        "runtime_evidence_status": runtime_status,
        "release_audit_check_id": release_audit_check_id,
        "blocking_failures": [],
        "warnings": [],
        "release_boundaries": boundaries,
        "recommended_action": recommended_action,
        "artifact_sha256": _file_sha256(resolved_artifact_path),
    }
    failures = _acceptance_contract_failures(
        summary,
        expected_check_id=release_audit_check_id,
        artifact_path=resolved_artifact_path,
        artifact_payload=artifact_payload,
        repo_root=resolved_repo_root,
        release_binding_required=True,
    )
    if failures:
        raise ValueError(f"Generated release acceptance sidecar failed its own contract: {failures}")
    return summary


def write_release_artifact_acceptance_summary(
    spec: ReleaseAuditSpec,
    *,
    artifact_name: str,
    repo_root: Path | None = None,
    overwrite: bool = False,
    release_boundaries: list[str] | None = None,
) -> tuple[dict[str, Any], Path]:
    """Write a manifest-bound release acceptance sidecar beside one artifact."""

    default_repo_root = (
        workspace_root_for_path(spec.source_path)
        if spec.source_path is not None
        else Path.cwd()
    )
    resolved_repo_root = (repo_root or default_repo_root).resolve()
    target = resolve_release_acceptance_target(spec, artifact_name)
    artifact_path = _resolve(resolved_repo_root, target["path"])
    output_path = artifact_path.parent / "acceptance_summary.json"
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            "Release acceptance sidecar already exists: "
            f"{output_path}. Use --overwrite to replace it or --dry-run to preview the update."
        )
    boundaries = release_boundaries or _release_boundaries_from_existing(output_path)
    summary = build_release_artifact_acceptance_summary(
        artifact_path,
        artifact_name=target["name"],
        release_audit_check_id=target["check_id"],
        repo_root=resolved_repo_root,
        release_boundaries=boundaries,
    )
    summary, _preserved_extra_fields = _summary_with_existing_extra_fields(summary, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_result_json(summary, output_path)
    return summary, output_path


def preview_release_artifact_acceptance_summary(
    spec: ReleaseAuditSpec,
    *,
    artifact_name: str,
    repo_root: Path | None = None,
    release_boundaries: list[str] | None = None,
) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    """Build the manifest-bound acceptance sidecar payload without writing it."""

    default_repo_root = (
        workspace_root_for_path(spec.source_path)
        if spec.source_path is not None
        else Path.cwd()
    )
    resolved_repo_root = (repo_root or default_repo_root).resolve()
    target = resolve_release_acceptance_target(spec, artifact_name)
    artifact_path = _resolve(resolved_repo_root, target["path"])
    output_path = artifact_path.parent / "acceptance_summary.json"
    boundaries = release_boundaries or _release_boundaries_from_existing(output_path)
    summary = build_release_artifact_acceptance_summary(
        artifact_path,
        artifact_name=target["name"],
        release_audit_check_id=target["check_id"],
        repo_root=resolved_repo_root,
        release_boundaries=boundaries,
    )
    summary, preserved_extra_fields = _summary_with_existing_extra_fields(summary, output_path)
    artifact_payload = _payload_with_release_evidence(_read_json(artifact_path))
    status = _acceptance_sidecar_status_from_expected(
        target,
        artifact_path=artifact_path,
        sidecar_path=output_path,
        expected=summary,
        artifact_payload=artifact_payload,
        repo_root=resolved_repo_root,
        preserved_extra_fields=preserved_extra_fields,
    )
    return (
        summary,
        output_path,
        {
            **status,
            "would_preserve_extra_fields": preserved_extra_fields,
        },
    )


def _acceptance_sidecar_status(
    target: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    artifact_path = _resolve(repo_root, target["path"])
    sidecar_path = artifact_path.parent / "acceptance_summary.json"
    base = {
        "artifact_name": target["name"],
        "artifact_kind": target["kind"],
        "artifact_path": _repo_relative_artifact_path(artifact_path, repo_root=repo_root)
        if artifact_path.exists()
        else target["path"].as_posix(),
        "sidecar_path": _repo_relative_artifact_path(sidecar_path, repo_root=repo_root)
        if sidecar_path.exists()
        else (target["path"].parent / "acceptance_summary.json").as_posix(),
        "release_audit_check_id": target["check_id"],
    }
    try:
        expected = build_release_artifact_acceptance_summary(
            artifact_path,
            artifact_name=target["name"],
            release_audit_check_id=target["check_id"],
            repo_root=repo_root,
            release_boundaries=_release_boundaries_from_existing(sidecar_path),
        )
        artifact_payload = _payload_with_release_evidence(_read_json(artifact_path))
    except Exception as exc:
        return {
            **base,
            "status": "blocked",
            "error": f"{type(exc).__name__}: {exc}",
            "changed_fields": [],
            "missing_fields": [],
            "extra_fields": [],
            "preserved_extra_fields": [],
            "contract_failures": [],
        }

    expected, preserved_extra_fields = _summary_with_existing_extra_fields(expected, sidecar_path)
    return _acceptance_sidecar_status_from_expected(
        target,
        artifact_path=artifact_path,
        sidecar_path=sidecar_path,
        expected=expected,
        artifact_payload=artifact_payload,
        repo_root=repo_root,
        preserved_extra_fields=preserved_extra_fields,
    )


def _acceptance_sidecar_status_from_expected(
    target: dict[str, Any],
    *,
    artifact_path: Path,
    sidecar_path: Path,
    expected: dict[str, Any],
    artifact_payload: dict[str, Any],
    repo_root: Path,
    preserved_extra_fields: list[str],
) -> dict[str, Any]:
    base = {
        "artifact_name": target["name"],
        "artifact_kind": target["kind"],
        "artifact_path": _repo_relative_artifact_path(artifact_path, repo_root=repo_root)
        if artifact_path.exists()
        else target["path"].as_posix(),
        "sidecar_path": _repo_relative_artifact_path(sidecar_path, repo_root=repo_root)
        if sidecar_path.exists()
        else (target["path"].parent / "acceptance_summary.json").as_posix(),
        "release_audit_check_id": target["check_id"],
    }

    if not sidecar_path.exists():
        return {
            **base,
            "status": "missing",
            "expected_artifact_sha256": expected.get("artifact_sha256"),
            "sidecar_artifact_sha256": None,
            "changed_fields": [],
            "missing_fields": sorted(expected),
            "extra_fields": [],
            "preserved_extra_fields": preserved_extra_fields,
            "contract_failures": [],
        }

    try:
        existing = _read_json(sidecar_path)
    except Exception as exc:
        return {
            **base,
            "status": "unreadable",
            "error": f"{type(exc).__name__}: {exc}",
            "expected_artifact_sha256": expected.get("artifact_sha256"),
            "sidecar_artifact_sha256": None,
            "changed_fields": [],
            "missing_fields": [],
            "extra_fields": [],
            "preserved_extra_fields": [],
            "contract_failures": [],
        }

    changed_fields = sorted(
        key
        for key, value in expected.items()
        if existing.get(key) != value
    )
    missing_fields = sorted(key for key in expected if key not in existing)
    extra_fields = sorted(key for key in existing if key not in expected)
    contract_failures = _acceptance_contract_failures(
        existing,
        expected_check_id=target["check_id"],
        artifact_path=artifact_path,
        artifact_payload=artifact_payload,
        repo_root=repo_root,
        release_binding_required=True,
    )
    status = "fresh" if not changed_fields and not extra_fields and not contract_failures else "stale"
    return {
        **base,
        "status": status,
        "expected_artifact_sha256": expected.get("artifact_sha256"),
        "sidecar_artifact_sha256": existing.get("artifact_sha256"),
        "changed_fields": changed_fields,
        "missing_fields": missing_fields,
        "extra_fields": extra_fields,
        "preserved_extra_fields": preserved_extra_fields,
        "contract_failures": contract_failures,
    }


def _release_acceptance_manifest_command_path(config_path: Path | None, *, repo_root: Path) -> str | None:
    if config_path is None:
        return None
    resolved_config_path = config_path.expanduser().resolve()
    try:
        return resolved_config_path.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(resolved_config_path)


def _release_acceptance_cli_command(
    *,
    config_path: Path | None,
    repo_root: Path,
    artifact_name: str,
    dry_run: bool = False,
    overwrite: bool = False,
) -> str | None:
    manifest_path = _release_acceptance_manifest_command_path(config_path, repo_root=repo_root)
    if manifest_path is None:
        return None
    parts = [
        "qcchem",
        "release",
        "accept-artifact",
        "-c",
        manifest_path,
        "--name",
        artifact_name,
        "--repo-root",
        str(repo_root),
    ]
    if dry_run:
        parts.append("--dry-run")
    if overwrite:
        parts.append("--overwrite")
    return " ".join(shlex.quote(str(part)) for part in parts)


def _release_acceptance_repair_issue(item: dict[str, Any]) -> str:
    status = item.get("status")
    if status == "missing":
        return "sidecar_missing"
    error = item.get("error")
    if error:
        return str(error)
    contract_failures = item.get("contract_failures")
    if isinstance(contract_failures, list) and contract_failures:
        first = next((failure for failure in contract_failures if isinstance(failure, dict)), None)
        if first is None:
            return f"contract_failure:{contract_failures[0]}"
        field = first.get("field")
        reason = first.get("reason")
        if field and reason:
            return f"contract_failure:{field}:{reason}"
        if field:
            return f"contract_failure:{field}"
        if reason:
            return f"contract_failure:{reason}"
        return "contract_failure"
    missing_fields = item.get("missing_fields")
    if isinstance(missing_fields, list) and missing_fields:
        return "missing_fields:" + ",".join(str(field) for field in missing_fields[:5])
    return str(status or "unknown")


def _release_acceptance_repair_plan(
    items: list[dict[str, Any]],
    *,
    config_path: Path | None,
    repo_root: Path,
) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for item in items:
        if item.get("status") == "fresh":
            continue
        artifact_name = str(item.get("artifact_name") or "")
        status = str(item.get("status") or "unknown")
        entry = {
            "artifact_name": artifact_name,
            "artifact_kind": item.get("artifact_kind"),
            "status": status,
            "issue": _release_acceptance_repair_issue(item),
            "artifact_path": item.get("artifact_path"),
            "sidecar_path": item.get("sidecar_path"),
            "changed_fields": list(item.get("changed_fields") or []),
            "missing_fields": list(item.get("missing_fields") or []),
            "contract_failures": list(item.get("contract_failures") or []),
        }
        if status == "blocked":
            entry.update(
                {
                    "recommended_action": "repair_blocking_artifact_or_manifest_before_acceptance",
                    "preview_command": None,
                    "repair_command": None,
                }
            )
        else:
            repair_requires_overwrite = status in {"stale", "unreadable"}
            entry.update(
                {
                    "recommended_action": "preview_release_sidecar_update_then_refresh",
                    "preview_command": _release_acceptance_cli_command(
                        config_path=config_path,
                        repo_root=repo_root,
                        artifact_name=artifact_name,
                        dry_run=True,
                    ),
                    "repair_command": _release_acceptance_cli_command(
                        config_path=config_path,
                        repo_root=repo_root,
                        artifact_name=artifact_name,
                        overwrite=repair_requires_overwrite,
                    ),
                }
            )
        plan.append(entry)
    return plan


def release_acceptance_status_report(
    spec: ReleaseAuditSpec,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Report whether manifest-bound release acceptance sidecars are fresh."""

    default_repo_root = (
        workspace_root_for_path(spec.source_path)
        if spec.source_path is not None
        else Path.cwd()
    )
    resolved_repo_root = (repo_root or default_repo_root).resolve()
    items = [
        _acceptance_sidecar_status(target, repo_root=resolved_repo_root)
        for target in _release_acceptance_targets(spec)
        if target["path"] is not None
    ]
    status_counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    stale_statuses = {"missing", "stale", "unreadable", "blocked"}
    requires_update = sum(status_counts.get(status, 0) for status in stale_statuses)
    repair_plan = _release_acceptance_repair_plan(
        items,
        config_path=spec.source_path,
        repo_root=resolved_repo_root,
    )
    report = {
        "schema_version": RELEASE_ACCEPTANCE_STATUS_SCHEMA_VERSION,
        "schema_features": list(RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES),
        "status": "fresh" if requires_update == 0 else "needs_update",
        "repo_root": str(resolved_repo_root),
        "total_sidecars": len(items),
        "fresh_count": status_counts.get("fresh", 0),
        "requires_update_count": requires_update,
        "status_counts": dict(sorted(status_counts.items())),
        "repair_plan": repair_plan,
        "repair_plan_count": len(repair_plan),
        "items": items,
    }
    contract_failures = release_acceptance_status_contract_failures(report)
    if contract_failures:
        raise ValueError(f"Release acceptance status report contract mismatch: {contract_failures}")
    return report


def release_acceptance_status_report_from_config(
    config_path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Load a release manifest and report release sidecar freshness."""

    resolved_config_path = config_path.expanduser()
    if not resolved_config_path.is_absolute() and repo_root is not None:
        resolved_config_path = repo_root.expanduser() / resolved_config_path
    spec = load_release_audit_spec(resolved_config_path)
    return release_acceptance_status_report(spec, repo_root=repo_root)


def write_release_artifact_acceptance_summary_from_config(
    config_path: Path,
    *,
    artifact_name: str,
    repo_root: Path | None = None,
    overwrite: bool = False,
    release_boundaries: list[str] | None = None,
) -> tuple[dict[str, Any], Path]:
    """Load a release manifest and write one artifact acceptance sidecar."""

    resolved_config_path = config_path.expanduser()
    if not resolved_config_path.is_absolute() and repo_root is not None:
        resolved_config_path = repo_root.expanduser() / resolved_config_path
    spec = load_release_audit_spec(resolved_config_path)
    return write_release_artifact_acceptance_summary(
        spec,
        artifact_name=artifact_name,
        repo_root=repo_root,
        overwrite=overwrite,
        release_boundaries=release_boundaries,
    )


def preview_release_artifact_acceptance_summary_from_config(
    config_path: Path,
    *,
    artifact_name: str,
    repo_root: Path | None = None,
    release_boundaries: list[str] | None = None,
) -> tuple[dict[str, Any], Path, dict[str, Any]]:
    """Load a release manifest and preview one artifact acceptance sidecar."""

    resolved_config_path = config_path.expanduser()
    if not resolved_config_path.is_absolute() and repo_root is not None:
        resolved_config_path = repo_root.expanduser() / resolved_config_path
    spec = load_release_audit_spec(resolved_config_path)
    return preview_release_artifact_acceptance_summary(
        spec,
        artifact_name=artifact_name,
        repo_root=repo_root,
        release_boundaries=release_boundaries,
    )
