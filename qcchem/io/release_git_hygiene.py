"""Helpers for release git-hygiene checks."""

from __future__ import annotations

import json
from pathlib import Path

from qcchem.io.release_audit_config import ReleaseAuditSpec

RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION = "qcchem.release_artifact_acceptance.v0.1-alpha"


def release_generated_output_paths() -> tuple[str, ...]:
    """Return generated release-output paths that should stay ignored."""
    return (
        "artifacts/artifact_index.json",
        "artifacts/workbench_smoke.json",
        "artifacts/release_audit/release_readiness.json",
        "artifacts/workflows/research_os_review_workflow/workflow_result.json",
        "artifacts/lr_ace_flagship_suite_v1/preview_local/benchmark_result.json",
        ".playwright-cli/probe.yml",
    )


def manifest_acceptance_sidecar_paths(spec: ReleaseAuditSpec) -> set[Path]:
    """Return release-manifest sibling acceptance sidecar paths."""
    sidecars = {
        artifact.path.parent / "acceptance_summary.json"
        for artifact in spec.curated_artifacts
    }
    sidecars.update(
        asset.artifact.parent / "acceptance_summary.json"
        for asset in spec.exploratory_assets
        if asset.artifact is not None
    )
    return sidecars


def _json_schema_version(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    schema_version = payload.get("schema_version")
    return schema_version if isinstance(schema_version, str) else None


def orphan_release_acceptance_sidecars(
    repo_root: Path,
    manifest_sidecars: set[Path],
) -> list[Path]:
    """Return release-artifact acceptance sidecars not listed by the manifest."""
    repo_root = repo_root.resolve()
    manifest_relative = {Path(path) for path in manifest_sidecars}
    artifacts_root = repo_root / "artifacts"
    if not artifacts_root.exists():
        return []

    orphans: list[Path] = []
    for sidecar in artifacts_root.glob("**/acceptance_summary.json"):
        relative_sidecar = sidecar.relative_to(repo_root)
        if relative_sidecar in manifest_relative:
            continue
        if _json_schema_version(sidecar) == RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION:
            orphans.append(relative_sidecar)
    return sorted(orphans, key=str)
