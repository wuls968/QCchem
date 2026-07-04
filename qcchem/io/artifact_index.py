"""Artifact indexing helpers for lightweight repository hygiene."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_GENERATED_ARTIFACT_DIR_NAMES = {"preview_local"}
_MAX_SKIPPED_GENERATED_RESULT_PATHS = 20


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_json_object_with_error(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return {}, "JSON payload is not an object."
    return payload, None


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
    if name == "workflow_result.json":
        return "workflow"
    return "run"


def _generated_artifact_skip_reason(result_path: Path, *, root: Path) -> str | None:
    try:
        relative_parts = result_path.relative_to(root).parts
    except ValueError:
        relative_parts = result_path.parts
    parent_parts = relative_parts[:-1]
    for name in _GENERATED_ARTIFACT_DIR_NAMES:
        if name in parent_parts:
            return name
    return None


def _empty_artifact_index(
    root: Path,
    *,
    root_exists: bool,
    root_is_dir: bool,
    index_error: str | None = None,
) -> dict[str, object]:
    return {
        "artifact_root": str(root),
        "artifact_root_exists": root_exists,
        "artifact_root_is_dir": root_is_dir,
        "index_error": index_error,
        "total_artifacts": 0,
        "skipped_generated_artifacts": 0,
        "skipped_generated_result_paths": [],
        "skipped_generated_result_paths_truncated": False,
        "artifacts": [],
    }


def build_artifact_index_entry(result_path: Path, *, root: Path | None = None) -> dict[str, object]:
    """Return a normalized artifact-index row for one result-like JSON file."""
    artifact_root = result_path.parent
    payload = _safe_read_json(result_path)
    evidence = payload.get("evidence_summary") if isinstance(payload.get("evidence_summary"), dict) else {}
    capsule_path = artifact_root / "evidence_capsule.json"
    capsule = _safe_read_json(capsule_path) if capsule_path.exists() else {}
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
        or payload.get("workflow_name")
        or artifact_root.name
    )
    embedded_acceptance_summary = (
        payload.get("acceptance_summary")
        if isinstance(payload.get("acceptance_summary"), dict)
        else {}
    )
    acceptance_summary_error: str | None = None
    sidecar_acceptance_path = artifact_root / "acceptance_summary.json"
    if sidecar_acceptance_path.exists():
        acceptance_summary, acceptance_summary_error = _read_json_object_with_error(sidecar_acceptance_path)
        acceptance_summary_readable = acceptance_summary_error is None
        acceptance_summary_source = "sidecar" if acceptance_summary_readable else None
    else:
        acceptance_summary = embedded_acceptance_summary
        acceptance_summary_source = "embedded" if embedded_acceptance_summary else None
        acceptance_summary_readable = bool(embedded_acceptance_summary)
    workflow_summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    mtime = result_path.stat().st_mtime if result_path.exists() else None
    entry = {
        "artifact_root": str(artifact_root if root is None else artifact_root),
        "artifact_kind": kind,
        "artifact_name": name,
        "result_json": str(result_path),
        "schema_version": payload.get("schema_version"),
        "verification_status": payload.get("verification_status") or payload.get("status") or evidence.get("trust_tier"),
        "trust_tier": evidence.get("trust_tier") or payload.get("verification_status") or payload.get("status"),
        "recommended_action": evidence.get("recommended_action") or acceptance_summary.get("recommended_action"),
        "capsule_status": capsule.get("capsule_status"),
        "evidence_summary_complete": (
            capsule.get("evidence_summary_status") == "complete"
            if capsule
            else all(
                evidence.get(key) is not None and evidence.get(key) != "" and evidence.get(key) != {}
                for key in (
                    "result_identity",
                    "primary_scientific_claim",
                    "primary_baseline",
                    "primary_error_metric",
                    "chemical_accuracy_status",
                    "runtime_evidence_status",
                    "trust_tier",
                    "recommended_action",
                )
            )
        ),
        "provenance_complete": (
            capsule.get("provenance_status") == "complete"
            if capsule
            else isinstance(payload.get("provenance"), dict) and bool(payload.get("provenance"))
        ),
        "capsule_json": str(capsule_path) if capsule_path.exists() else None,
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
        or (artifact_root / "campaign_report.md").exists()
        or (artifact_root / "workflow_report.md").exists(),
        "has_resolved_config": (artifact_root / "resolved_config.yaml").exists(),
        "has_runtime_submission": (artifact_root / "runtime_submission.json").exists(),
        "has_quantum_evidence": (artifact_root / "quantum_evidence.json").exists(),
        "has_pbc_metadata": isinstance(payload.get("periodic_boundary"), dict)
        or isinstance(payload.get("pbc"), dict),
        "has_pbc_qmmm_metadata": isinstance(payload.get("pbc_qmmm"), dict),
        "has_field_evidence": any(
            (artifact_root / name).exists()
            for name in (
                "field_model_registry.json",
                "field_hamiltonian.json",
                "field_observables.json",
                "field_dynamics.json",
                "field_constraints.json",
                "field_resources.json",
                "field_error_budget.json",
            )
        ),
        "field_sidecar_count": sum(
            1
            for name in (
                "field_model_registry.json",
                "field_hamiltonian.json",
                "field_observables.json",
                "field_dynamics.json",
                "field_constraints.json",
                "field_resources.json",
                "field_error_budget.json",
            )
            if (artifact_root / name).exists()
        ),
        "has_acceptance_summary": bool(embedded_acceptance_summary) or sidecar_acceptance_path.exists(),
        "acceptance_summary_path": str(sidecar_acceptance_path) if sidecar_acceptance_path.exists() else None,
        "acceptance_summary_source": acceptance_summary_source,
        "acceptance_summary_readable": acceptance_summary_readable,
        "acceptance_summary_error": acceptance_summary_error,
        "has_hardware_error_diagnostic": isinstance(payload.get("hardware_error_diagnostic"), dict),
        "workflow_status": payload.get("status") if kind == "workflow" else None,
        "workflow_accepted": acceptance_summary.get("accepted") if kind == "workflow" else None,
        "workflow_completed_steps": workflow_summary.get("completed_steps") if kind == "workflow" else None,
        "workflow_failed_steps": workflow_summary.get("failed_steps") if kind == "workflow" else None,
        "workflow_generated_steps": workflow_summary.get("generated_steps") if kind == "workflow" else None,
        "has_workflow_graph": (artifact_root / "workflow_graph.json").exists(),
        "has_workflow_provenance": (artifact_root / "provenance.jsonl").exists(),
        "has_workflow_registry": (artifact_root / "registry.json").exists(),
        "mtime": mtime,
    }
    return entry


def build_artifact_index(root: Path) -> dict[str, object]:
    """Return a compact index of artifact directories under ``root``."""
    resolved_root = Path(root).resolve()
    artifacts: list[dict[str, object]] = []
    if not resolved_root.exists():
        return _empty_artifact_index(resolved_root, root_exists=False, root_is_dir=False)
    if not resolved_root.is_dir():
        return _empty_artifact_index(
            resolved_root,
            root_exists=True,
            root_is_dir=False,
            index_error="Artifact root is not a directory.",
        )

    result_names = {
        "result.json",
        "benchmark_result.json",
        "study_result.json",
        "scan_result.json",
        "hardware_calibration_summary.json",
        "campaign_result.json",
        "workflow_result.json",
    }
    skipped_generated_paths: list[str] = []
    skipped_generated_count = 0
    for result_json in sorted(path for path in resolved_root.rglob("*.json") if path.name in result_names):
        if _generated_artifact_skip_reason(result_json, root=resolved_root) is not None:
            skipped_generated_count += 1
            if len(skipped_generated_paths) < _MAX_SKIPPED_GENERATED_RESULT_PATHS:
                skipped_generated_paths.append(str(result_json))
            continue
        artifacts.append(build_artifact_index_entry(result_json, root=resolved_root))

    return {
        "artifact_root": str(resolved_root),
        "artifact_root_exists": True,
        "artifact_root_is_dir": True,
        "index_error": None,
        "total_artifacts": len(artifacts),
        "skipped_generated_artifacts": skipped_generated_count,
        "skipped_generated_result_paths": skipped_generated_paths,
        "skipped_generated_result_paths_truncated": skipped_generated_count > len(skipped_generated_paths),
        "artifacts": artifacts,
    }
