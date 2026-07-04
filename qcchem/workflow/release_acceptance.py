"""Release-bound artifact acceptance sidecar writer."""

from __future__ import annotations

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
        raise FileExistsError(f"Release acceptance sidecar already exists: {output_path}")
    boundaries = release_boundaries or _release_boundaries_from_existing(output_path)
    summary = build_release_artifact_acceptance_summary(
        artifact_path,
        artifact_name=target["name"],
        release_audit_check_id=target["check_id"],
        repo_root=resolved_repo_root,
        release_boundaries=boundaries,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_result_json(summary, output_path)
    return summary, output_path


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
