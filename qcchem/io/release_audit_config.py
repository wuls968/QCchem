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
class ReleaseAuditSpec:
    """Configuration for a local release-readiness audit."""

    profile: str
    release_version: str
    curated_artifacts: list[ReleaseAuditArtifactSpec] = field(default_factory=list)
    exploratory_assets: list[ReleaseAuditExploratoryAssetSpec] = field(default_factory=list)
    required_docs: list[ReleaseAuditDocSpec] = field(default_factory=list)
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


def _artifact_spec(raw: dict[str, Any], *, key: str) -> ReleaseAuditArtifactSpec:
    name = str(raw.get("name", "")).strip()
    path = str(raw.get("path", "")).strip()
    if not name:
        raise ValueError(f"release_audit.{key}.name is required.")
    if not path:
        raise ValueError(f"release_audit.{key}.path is required.")
    return ReleaseAuditArtifactSpec(
        name=name,
        path=Path(path),
        required=bool(raw.get("required", True)),
    )


def _exploratory_asset_spec(raw: dict[str, Any]) -> ReleaseAuditExploratoryAssetSpec:
    name = str(raw.get("name", "")).strip()
    kind = str(raw.get("kind", "")).strip()
    config = str(raw.get("config", "")).strip()
    if not name:
        raise ValueError("release_audit.exploratory_assets.name is required.")
    if kind not in SUPPORTED_EXPLORATORY_ASSET_KINDS:
        raise ValueError(
            "release_audit.exploratory_assets.kind must be one of "
            f"{sorted(SUPPORTED_EXPLORATORY_ASSET_KINDS)}, got '{kind}'."
        )
    if not config:
        raise ValueError("release_audit.exploratory_assets.config is required.")
    artifact_raw = raw.get("artifact")
    artifact = Path(str(artifact_raw)) if artifact_raw not in {None, ""} else None
    return ReleaseAuditExploratoryAssetSpec(
        name=name,
        kind=kind,
        config=Path(config),
        artifact=artifact,
        required=bool(raw.get("required", True)),
    )


def _doc_spec(raw: dict[str, Any]) -> ReleaseAuditDocSpec:
    path = str(raw.get("path", "")).strip()
    if not path:
        raise ValueError("release_audit.required_docs.path is required.")
    terms = raw.get("terms", [])
    if not isinstance(terms, list):
        raise ValueError("release_audit.required_docs.terms must be a list.")
    return ReleaseAuditDocSpec(
        path=Path(path),
        terms=[str(term) for term in terms],
        required=bool(raw.get("required", True)),
    )


def load_release_audit_spec(path: Path) -> ReleaseAuditSpec:
    """Load a release audit manifest from YAML."""
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Release audit configuration must deserialize to a mapping.")
    data = _require_mapping(raw, "release_audit")

    profile = str(data.get("profile", "trust_first")).strip()
    if profile not in SUPPORTED_RELEASE_AUDIT_PROFILES:
        raise ValueError(
            "release_audit.profile must be one of "
            f"{sorted(SUPPORTED_RELEASE_AUDIT_PROFILES)}, got '{profile}'."
        )
    release_version = str(data.get("release_version", "")).strip()
    if not release_version or "a" not in release_version:
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
    acceptance_commands = data.get("acceptance_commands", [])
    if not isinstance(acceptance_commands, list):
        raise ValueError("release_audit.acceptance_commands must be a list.")

    return ReleaseAuditSpec(
        profile=profile,
        release_version=release_version,
        curated_artifacts=curated_artifacts,
        exploratory_assets=exploratory_assets,
        required_docs=required_docs,
        acceptance_commands=[str(command) for command in acceptance_commands],
        source_path=resolved_path,
    )
