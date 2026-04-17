"""Artifact indexing helpers for lightweight repository hygiene."""

from __future__ import annotations

from pathlib import Path


def build_artifact_index(root: Path) -> dict[str, object]:
    """Return a compact index of artifact directories under ``root``."""
    resolved_root = Path(root).resolve()
    artifacts: list[dict[str, object]] = []
    if not resolved_root.exists():
        return {
            "artifact_root": str(resolved_root),
            "total_artifacts": 0,
            "artifacts": artifacts,
        }

    for result_json in sorted(resolved_root.rglob("result.json")):
        artifact_root = result_json.parent
        artifacts.append(
            {
                "artifact_root": str(artifact_root),
                "result_json": str(result_json),
                "has_result_json": True,
                "has_report_markdown": (artifact_root / "report.md").exists(),
                "has_resolved_config": (artifact_root / "resolved_config.yaml").exists(),
                "has_runtime_submission": (artifact_root / "runtime_submission.json").exists(),
            }
        )

    return {
        "artifact_root": str(resolved_root),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
    }
