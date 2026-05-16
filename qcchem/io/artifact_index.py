"""Artifact indexing helpers for lightweight repository hygiene."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _artifact_kind(path: Path) -> str:
    name = path.name
    if name == "benchmark_result.json":
        return "benchmark_suite"
    if name == "study_result.json":
        return "study"
    if name == "scan_result.json":
        return "scan"
    if name == "hardware_calibration_summary.json":
        return "hardware_calibration"
    if name == "campaign_result.json":
        return "campaign"
    return "run"


def build_artifact_index_entry(result_path: Path, *, root: Path | None = None) -> dict[str, object]:
    """Return a normalized artifact-index row for one result-like JSON file."""
    artifact_root = result_path.parent
    payload = _safe_read_json(result_path)
    evidence = payload.get("evidence_summary") if isinstance(payload.get("evidence_summary"), dict) else {}
    runtime_submission = (
        _safe_read_json(artifact_root / "runtime_submission.json")
        if (artifact_root / "runtime_submission.json").exists()
        else payload.get("runtime_submission")
    )
    runtime_submission = runtime_submission if isinstance(runtime_submission, dict) else {}
    kind = _artifact_kind(result_path)
    name = (
        payload.get("run_id")
        or payload.get("suite_name")
        or payload.get("study_name")
        or payload.get("scan_name")
        or payload.get("campaign_name")
        or artifact_root.name
    )
    mtime = result_path.stat().st_mtime if result_path.exists() else None
    entry = {
        "artifact_root": str(artifact_root if root is None else artifact_root),
        "artifact_kind": kind,
        "artifact_name": name,
        "result_json": str(result_path),
        "schema_version": payload.get("schema_version"),
        "verification_status": payload.get("verification_status") or evidence.get("trust_tier"),
        "trust_tier": evidence.get("trust_tier") or payload.get("verification_status"),
        "recommended_action": evidence.get("recommended_action"),
        "runtime_evidence_status": evidence.get("runtime_evidence_status")
        or ("retrieved_result" if runtime_submission.get("submitted") and runtime_submission.get("succeeded") else None),
        "hardware_verified": bool(payload.get("hardware_verified") or runtime_submission.get("succeeded")),
        "runtime_submission_status": (
            "succeeded"
            if runtime_submission.get("submitted") and runtime_submission.get("succeeded")
            else runtime_submission.get("failure_category")
            or ("submitted" if runtime_submission.get("submitted") else "attempted" if runtime_submission.get("attempted") else None)
        ),
        "has_result_json": result_path.name == "result.json",
        "has_report_markdown": (artifact_root / "report.md").exists()
        or (artifact_root / "benchmark_report.md").exists()
        or (artifact_root / "study_report.md").exists()
        or (artifact_root / "scan_report.md").exists()
        or (artifact_root / "campaign_report.md").exists(),
        "has_resolved_config": (artifact_root / "resolved_config.yaml").exists(),
        "has_runtime_submission": (artifact_root / "runtime_submission.json").exists(),
        "has_acceptance_summary": (artifact_root / "acceptance_summary.json").exists(),
        "has_hardware_error_diagnostic": isinstance(payload.get("hardware_error_diagnostic"), dict),
        "mtime": mtime,
    }
    return entry


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

    result_names = {
        "result.json",
        "benchmark_result.json",
        "study_result.json",
        "scan_result.json",
        "hardware_calibration_summary.json",
        "campaign_result.json",
    }
    for result_json in sorted(path for path in resolved_root.rglob("*.json") if path.name in result_names):
        artifacts.append(build_artifact_index_entry(result_json, root=resolved_root))

    return {
        "artifact_root": str(resolved_root),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
    }
