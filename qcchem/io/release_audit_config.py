"""Release-audit manifest loading for Trust-First release gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from qcchem.io.config import resolve_user_path

SUPPORTED_RELEASE_AUDIT_PROFILES = {"trust_first"}
SUPPORTED_EXPLORATORY_ASSET_KINDS = {"qft", "lr_ace", "tc_qsci"}


@dataclass(slots=True)
class ReleaseAuditArtifactSpec:
    """One artifact that the release audit should inspect."""

    name: str
    path: Path
    required: bool = True
    acceptance_required: bool = False


@dataclass(slots=True)
class ReleaseAuditExploratoryAssetSpec:
    """One opt-in exploratory research asset tracked by the release audit."""

    name: str
    kind: str
    config: Path
    artifact: Path | None = None
    required: bool = True


@dataclass(slots=True)
class ReleaseAuditDocSpec:
    """One release-facing document and the terms it must contain."""

    path: Path
    terms: list[str] = field(default_factory=list)
    required: bool = True


@dataclass(slots=True)
class ReleaseAuditWarningPolicy:
    """Policy for turning known release-audit warnings into a bounded gate."""

    max_count: int | None = None
    allowed_ids: list[str] | None = None


@dataclass(slots=True)
class ReleaseAuditSpec:
    """Configuration for a local release-readiness audit."""

    profile: str
    release_version: str
    curated_artifacts: list[ReleaseAuditArtifactSpec] = field(default_factory=list)
    exploratory_assets: list[ReleaseAuditExploratoryAssetSpec] = field(default_factory=list)
    required_docs: list[ReleaseAuditDocSpec] = field(default_factory=list)
    warning_policy: ReleaseAuditWarningPolicy | None = None
    acceptance_commands: list[str] = field(default_factory=list)
    source_path: Path | None = None


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"release_audit.{key} must be a mapping.")
    return value


def _list_of_mappings(value: Any, *, key: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"release_audit.{key} must be a list.")
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"release_audit.{key} entries must be mappings.")
    return value


def _bool_field(raw: dict[str, Any], key: str, *, default: bool, field_path: str) -> bool:
    if key not in raw:
        return default
    value = raw[key]
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field_path} must be a boolean.")


def _string_field(raw: dict[str, Any], key: str, *, field_path: str, default: str | None = None) -> str:
    if key not in raw:
        if default is None:
            raise ValueError(f"{field_path} must be a non-empty string.")
        return default
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_path} must be a non-empty string.")
    return value.strip()


def _repo_relative_path_value(value: str, *, field_path: str) -> Path:
    path = Path(value)
    if path.is_absolute() or value.startswith("~") or ".." in path.parts:
        raise ValueError(
            f"{field_path} must be a repository-relative path without absolute, "
            "home-directory, or parent-directory components."
        )
    return path


def _path_field(raw: dict[str, Any], key: str, *, field_path: str) -> Path:
    return _repo_relative_path_value(
        _string_field(raw, key, field_path=field_path),
        field_path=field_path,
    )


def _optional_path_field(raw: dict[str, Any], key: str, *, field_path: str) -> Path | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_path} must be a string when provided.")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_path} must be a non-empty string when provided.")
    return _repo_relative_path_value(stripped, field_path=field_path)


def _string_list_value(value: Any, *, field_path: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_path} must be a list.")
    strings: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_path}[{index}] must be a non-empty string.")
        strings.append(item.strip())
    return strings


def _string_list_field(raw: dict[str, Any], key: str, *, default: list[str], field_path: str) -> list[str]:
    if key not in raw:
        return list(default)
    return _string_list_value(raw[key], field_path=field_path)


def _optional_string_list_field(raw: dict[str, Any], key: str, *, field_path: str) -> list[str] | None:
    if raw.get(key) is None:
        return None
    return _string_list_value(raw[key], field_path=field_path)


def _ensure_unique_values(values: list[str], *, field_path: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        formatted = ", ".join(repr(item) for item in duplicates)
        raise ValueError(f"{field_path} entries must be unique; duplicates: {formatted}.")


def _artifact_spec(raw: dict[str, Any], *, key: str) -> ReleaseAuditArtifactSpec:
    name = _string_field(raw, "name", field_path=f"release_audit.{key}.name")
    path = _path_field(raw, "path", field_path=f"release_audit.{key}.path")
    return ReleaseAuditArtifactSpec(
        name=name,
        path=path,
        required=_bool_field(
            raw,
            "required",
            default=True,
            field_path=f"release_audit.{key}.required",
        ),
        acceptance_required=_bool_field(
            raw,
            "acceptance_required",
            default=False,
            field_path=f"release_audit.{key}.acceptance_required",
        ),
    )


def _exploratory_asset_spec(raw: dict[str, Any]) -> ReleaseAuditExploratoryAssetSpec:
    name = _string_field(raw, "name", field_path="release_audit.exploratory_assets.name")
    kind = _string_field(raw, "kind", field_path="release_audit.exploratory_assets.kind")
    config = _path_field(raw, "config", field_path="release_audit.exploratory_assets.config")
    if kind not in SUPPORTED_EXPLORATORY_ASSET_KINDS:
        raise ValueError(
            "release_audit.exploratory_assets.kind must be one of "
            f"{sorted(SUPPORTED_EXPLORATORY_ASSET_KINDS)}, got '{kind}'."
        )
    artifact = _optional_path_field(
        raw,
        "artifact",
        field_path="release_audit.exploratory_assets.artifact",
    )
    return ReleaseAuditExploratoryAssetSpec(
        name=name,
        kind=kind,
        config=config,
        artifact=artifact,
        required=_bool_field(
            raw,
            "required",
            default=True,
            field_path="release_audit.exploratory_assets.required",
        ),
    )


def _doc_spec(raw: dict[str, Any]) -> ReleaseAuditDocSpec:
    path = _path_field(raw, "path", field_path="release_audit.required_docs.path")
    return ReleaseAuditDocSpec(
        path=path,
        terms=_string_list_field(
            raw,
            "terms",
            default=[],
            field_path="release_audit.required_docs.terms",
        ),
        required=_bool_field(
            raw,
            "required",
            default=True,
            field_path="release_audit.required_docs.required",
        ),
    )


def _warning_policy(raw: Any) -> ReleaseAuditWarningPolicy | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("release_audit.warning_policy must be a mapping.")

    max_count_raw = raw.get("max_count")
    if max_count_raw is None:
        max_count = None
    elif isinstance(max_count_raw, bool) or not isinstance(max_count_raw, int) or max_count_raw < 0:
        raise ValueError("release_audit.warning_policy.max_count must be a non-negative integer.")
    else:
        max_count = max_count_raw

    allowed_ids = _optional_string_list_field(
        raw,
        "allowed_ids",
        field_path="release_audit.warning_policy.allowed_ids",
    )
    if allowed_ids is not None:
        _ensure_unique_values(
            allowed_ids,
            field_path="release_audit.warning_policy.allowed_ids",
        )

    return ReleaseAuditWarningPolicy(max_count=max_count, allowed_ids=allowed_ids)


def load_release_audit_spec(path: Path) -> ReleaseAuditSpec:
    """Load a release audit manifest from YAML."""
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Release audit configuration must deserialize to a mapping.")
    data = _require_mapping(raw, "release_audit")

    profile = _string_field(
        data,
        "profile",
        default="trust_first",
        field_path="release_audit.profile",
    )
    if profile not in SUPPORTED_RELEASE_AUDIT_PROFILES:
        raise ValueError(
            "release_audit.profile must be one of "
            f"{sorted(SUPPORTED_RELEASE_AUDIT_PROFILES)}, got '{profile}'."
        )
    release_version = _string_field(
        data,
        "release_version",
        field_path="release_audit.release_version",
    )
    if "a" not in release_version:
        raise ValueError("release_audit.release_version must be an alpha version such as 0.1.0a1.")

    curated_artifacts = [
        _artifact_spec(item, key="curated_artifacts")
        for item in _list_of_mappings(data.get("curated_artifacts"), key="curated_artifacts")
    ]
    exploratory_assets = [
        _exploratory_asset_spec(item)
        for item in _list_of_mappings(data.get("exploratory_assets"), key="exploratory_assets")
    ]
    required_docs = [
        _doc_spec(item)
        for item in _list_of_mappings(data.get("required_docs"), key="required_docs")
    ]
    _ensure_unique_values(
        [item.name for item in curated_artifacts],
        field_path="release_audit.curated_artifacts.name",
    )
    _ensure_unique_values(
        [item.name for item in exploratory_assets],
        field_path="release_audit.exploratory_assets.name",
    )
    _ensure_unique_values(
        [str(item.path) for item in required_docs],
        field_path="release_audit.required_docs.path",
    )
    acceptance_commands = _string_list_field(
        data,
        "acceptance_commands",
        default=[],
        field_path="release_audit.acceptance_commands",
    )
    _ensure_unique_values(
        acceptance_commands,
        field_path="release_audit.acceptance_commands",
    )

    return ReleaseAuditSpec(
        profile=profile,
        release_version=release_version,
        curated_artifacts=curated_artifacts,
        exploratory_assets=exploratory_assets,
        required_docs=required_docs,
        warning_policy=_warning_policy(data.get("warning_policy")),
        acceptance_commands=acceptance_commands,
        source_path=resolved_path,
    )
