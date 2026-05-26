"""Evidence Capsule validation for artifact roots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVIDENCE_CAPSULE_SCHEMA_VERSION = "qcchem.evidence_capsule.v0.1-alpha"
EVIDENCE_SUMMARY_REQUIRED_FIELDS = (
    "result_identity",
    "primary_scientific_claim",
    "primary_baseline",
    "primary_error_metric",
    "chemical_accuracy_status",
    "runtime_evidence_status",
    "trust_tier",
    "recommended_action",
)
RUN_REQUIRED_PAYLOAD_FIELDS = (
    "schema_version",
    "evidence_summary",
    "problem",
    "energy",
    "benchmark",
    "mapping",
    "backend",
    "provenance",
    "artifacts",
)
OPTIONAL_SIDECARS = (
    "exact_result.json",
    "quantum_evidence.json",
    "runtime_submission.json",
    "calibration.json",
    "qcschema.json",
    "result.h5",
)


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _detect_result_path(root: Path) -> tuple[str, Path | None, str | None]:
    candidates = [
        ("run", "result.json"),
        ("benchmark_suite", "benchmark_result.json"),
        ("study", "study_result.json"),
        ("scan", "scan_result.json"),
        ("campaign", "campaign_result.json"),
        ("hardware_campaign", "hardware_calibration_summary.json"),
    ]
    for kind, filename in candidates:
        path = root / filename
        if path.exists():
            return kind, path, filename
    return "unknown", None, None


def _required_files_for(kind: str) -> tuple[str, ...]:
    if kind == "run":
        return ("result.json", "report.md", "resolved_config.yaml", "run.log")
    if kind == "benchmark_suite":
        return ("benchmark_result.json", "benchmark_report.md")
    if kind == "study":
        return ("study_result.json", "study_report.md")
    if kind == "scan":
        return ("scan_result.json", "scan_report.md")
    if kind == "campaign":
        return ("campaign_result.json", "campaign_report.md")
    if kind == "hardware_campaign":
        return ("hardware_calibration_summary.json", "hardware_calibration_report.md")
    return ()


def _evidence_status(payload: dict[str, Any]) -> tuple[str, list[str]]:
    evidence = payload.get("evidence_summary")
    if not isinstance(evidence, dict):
        return "missing", list(EVIDENCE_SUMMARY_REQUIRED_FIELDS)
    missing = [
        key
        for key in EVIDENCE_SUMMARY_REQUIRED_FIELDS
        if evidence.get(key) is None or evidence.get(key) == "" or evidence.get(key) == () or evidence.get(key) == {}
    ]
    return ("complete" if not missing else "incomplete"), missing


def _provenance_status(payload: dict[str, Any]) -> str:
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        return "missing"
    return "complete" if provenance else "incomplete"


def _payload_missing_fields(kind: str, payload: dict[str, Any]) -> list[str]:
    if kind != "run":
        return []
    return [key for key in RUN_REQUIRED_PAYLOAD_FIELDS if key not in payload]


def _boundary_warnings(payload: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    trust_tier = str(evidence.get("trust_tier") or payload.get("verification_status") or "")
    runtime_status = str(evidence.get("runtime_evidence_status") or "")
    chemical_status = str(evidence.get("chemical_accuracy_status") or "")
    if payload.get("hardware_verified") or trust_tier == "hardware_verified":
        warnings.append("hardware_verified records runtime retrieval evidence; it is not publication-grade chemistry validation.")
        if chemical_status != "met":
            warnings.append("Hardware-derived chemical accuracy is not met or not available.")
        if runtime_status != "retrieved_result":
            warnings.append("Hardware-facing artifact does not report retrieved_result runtime evidence.")
    if trust_tier in {"exploratory", "unstable"} or str(payload.get("module_origin")) == "exploratory":
        warnings.append("Exploratory or unstable evidence cannot be treated as validated without a promotion gate.")
    return sorted(set(warnings))


def validate_evidence_capsule(artifact_root: Path) -> dict[str, Any]:
    """Validate an artifact root as an evidence capsule."""
    root = artifact_root.expanduser().resolve()
    kind, result_path, _filename = _detect_result_path(root)
    payload = _safe_read_json(result_path) if result_path is not None else {}
    evidence = payload.get("evidence_summary") if isinstance(payload.get("evidence_summary"), dict) else {}
    required_files = {name: {"path": str(root / name), "present": (root / name).exists()} for name in _required_files_for(kind)}
    optional_files = {name: {"path": str(root / name), "present": (root / name).exists()} for name in OPTIONAL_SIDECARS}
    missing_required = [name for name, info in required_files.items() if not info["present"]]
    missing_recommended = [name for name, info in optional_files.items() if not info["present"]]
    evidence_status, missing_evidence = _evidence_status(payload)
    provenance_status = _provenance_status(payload)
    missing_payload = _payload_missing_fields(kind, payload)
    blocking: list[str] = []
    if result_path is None:
        blocking.append("No supported QCchem result JSON was found in the artifact root.")
    if missing_required:
        blocking.append(f"Missing required files: {', '.join(missing_required)}.")
    if missing_payload:
        blocking.append(f"Missing result payload fields: {', '.join(missing_payload)}.")
    if evidence_status != "complete":
        blocking.append(f"evidence_summary is {evidence_status}: missing {', '.join(missing_evidence)}.")
    if provenance_status == "missing":
        blocking.append("provenance is missing.")

    if result_path is None or missing_required:
        capsule_status = "invalid"
    elif blocking:
        capsule_status = "partial"
    else:
        capsule_status = "complete"

    return {
        "schema_version": EVIDENCE_CAPSULE_SCHEMA_VERSION,
        "artifact_root": str(root),
        "artifact_kind": kind,
        "result_json": None if result_path is None else str(result_path),
        "capsule_status": capsule_status,
        "trust_tier": evidence.get("trust_tier") or payload.get("verification_status") or "unknown",
        "recommended_action": evidence.get("recommended_action") or "review_evidence_boundary",
        "evidence_summary": evidence,
        "required_files": required_files,
        "optional_files": optional_files,
        "missing_required_files": missing_required,
        "missing_recommended_files": missing_recommended,
        "evidence_summary_status": evidence_status,
        "evidence_summary_missing_fields": missing_evidence,
        "provenance_status": provenance_status,
        "payload_missing_fields": missing_payload,
        "boundary_warnings": _boundary_warnings(payload, evidence),
        "blocking_issues": blocking,
    }


def render_evidence_capsule_markdown(payload: dict[str, Any]) -> str:
    """Render an evidence capsule report."""
    lines = [
        "# QCchem Evidence Capsule",
        "",
        f"- artifact_root: `{payload.get('artifact_root')}`",
        f"- artifact_kind: `{payload.get('artifact_kind')}`",
        f"- capsule_status: `{payload.get('capsule_status')}`",
        f"- trust_tier: `{payload.get('trust_tier')}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        "",
        "## Required Files",
        "",
    ]
    for name, info in (payload.get("required_files") or {}).items():
        lines.append(f"- `{name}`: `{bool(info.get('present'))}`")
    lines.extend(["", "## Evidence Summary", ""])
    lines.append(f"- status: `{payload.get('evidence_summary_status')}`")
    missing = payload.get("evidence_summary_missing_fields") or []
    lines.append(f"- missing_fields: `{missing}`")
    lines.extend(["", "## Boundary Warnings", ""])
    lines.extend([f"- {item}" for item in payload.get("boundary_warnings") or []] or ["- None"])
    lines.extend(["", "## Blocking Issues", ""])
    lines.extend([f"- {item}" for item in payload.get("blocking_issues") or []] or ["- None"])
    return "\n".join(lines) + "\n"
