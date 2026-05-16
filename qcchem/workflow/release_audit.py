"""Trust-First release-readiness audit workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from qcchem.core.evidence import summarize_artifact_payload
from qcchem.io.release_audit_config import (
    ReleaseAuditExploratoryAssetSpec,
    ReleaseAuditSpec,
    load_release_audit_spec,
)

RELEASE_AUDIT_SCHEMA_VERSION = "1"


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _read_project_version(pyproject: Path) -> str | None:
    if not pyproject.exists():
        return None
    match = re.search(r'^\s*version\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def _check(
    checks: list[dict[str, Any]],
    *,
    check_id: str,
    label: str,
    passed: bool,
    required: bool = True,
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "id": check_id,
            "label": label,
            "status": "passed" if passed else "failed",
            "required": required,
            "summary": summary,
            "details": details or {},
        }
    )


def _skipped(
    checks: list[dict[str, Any]],
    *,
    check_id: str,
    label: str,
    required: bool = False,
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "id": check_id,
            "label": label,
            "status": "skipped",
            "required": required,
            "summary": summary,
            "details": details or {},
        }
    )


def _warning(
    checks: list[dict[str, Any]],
    *,
    check_id: str,
    label: str,
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "id": check_id,
            "label": label,
            "status": "warning",
            "required": False,
            "summary": summary,
            "details": details or {},
        }
    )


def _evidence_missing_fields(payload: dict[str, Any]) -> list[str]:
    evidence = payload.get("evidence_summary")
    if not isinstance(evidence, dict):
        return ["evidence_summary"]
    missing: list[str] = []
    for key in ("trust_tier", "primary_baseline", "primary_error_metric", "recommended_action"):
        value = evidence.get(key)
        if value is None or value == "" or value == {}:
            missing.append(key)
    return missing


def _runtime_boundary_failure(payload: dict[str, Any]) -> str | None:
    if not payload.get("hardware_verified"):
        return None
    runtime_submission = payload.get("runtime_submission") or {}
    if not isinstance(runtime_submission, dict):
        return "hardware_verified_without_runtime_submission"
    if runtime_submission.get("submitted") and runtime_submission.get("succeeded"):
        return None
    return "hardware_verified_without_retrieved_runtime_result"


def _artifact_matrix_entry(name: str, kind: str, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    evidence = payload.get("evidence_summary") or {}
    return {
        "name": name,
        "kind": kind,
        "path": str(path),
        "verification_status": payload.get("verification_status"),
        "trust_tier": evidence.get("trust_tier"),
        "recommended_action": evidence.get("recommended_action"),
        "hardware_verified": payload.get("hardware_verified", False),
        "runtime_submission_status": (payload.get("runtime_submission") or {}).get("status")
        or (payload.get("runtime_submission") or {}).get("failure_category"),
        "acceptance_status": (payload.get("acceptance_summary") or {}).get("accepted"),
    }


def _payload_with_release_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a read-only payload view with Evidence Summary for legacy artifacts."""
    if isinstance(payload.get("evidence_summary"), dict):
        return payload
    try:
        summarized = summarize_artifact_payload(payload)
    except Exception:
        return payload
    evidence = summarized.get("evidence_summary")
    if not isinstance(evidence, dict):
        return payload
    return {**payload, "evidence_summary": evidence}


def _has_lr_ace_section(payload: dict[str, Any]) -> bool:
    variational = payload.get("variational_result") or {}
    ansatz = variational.get("ansatz") or {}
    if isinstance(ansatz, dict) and "lr_ace" in ansatz:
        return True
    return "lr_ace" in json.dumps(payload.get("metadata", {})).lower()


def _has_required_exploratory_section(kind: str, payload: dict[str, Any]) -> bool:
    if kind == "qft":
        return isinstance(payload.get("qft_model"), dict)
    if kind == "tc_qsci":
        return isinstance(payload.get("tc_qsci_result"), dict)
    if kind == "lr_ace":
        return _has_lr_ace_section(payload)
    return False


def _risk_notes(payload: dict[str, Any]) -> list[Any]:
    notes = payload.get("scientific_risk_notes") or []
    evidence = payload.get("evidence_summary") or {}
    trust = evidence.get("trust_judgment") or {}
    if isinstance(trust, dict):
        notes = [*notes, *(trust.get("scientific_risk_notes") or [])]
    return notes


def classify_exploratory_config(path: Path) -> str:
    """Classify a configured exploratory asset without executing it."""
    if not path.exists():
        return "missing"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return "unknown"
    solver = raw.get("solver") or {}
    problem = raw.get("problem") or {}
    exploratory = raw.get("exploratory") or {}
    modules = exploratory.get("modules") or []
    qft = (problem.get("qft") or {}) if isinstance(problem, dict) else {}
    solver_kind = str(solver.get("kind", "")).strip() if isinstance(solver, dict) else ""
    if isinstance(qft, dict) and qft.get("enabled"):
        return "qft"
    if solver_kind.startswith("lattice_qed") or solver_kind == "qft_dynamics_audit":
        return "qft"
    if solver_kind == "lr_ace":
        return "lr_ace"
    if "tc_qsci" in modules:
        return "tc_qsci"
    tc_qsci = raw.get("tc_qsci") or {}
    if isinstance(tc_qsci, dict) and tc_qsci.get("enabled"):
        return "tc_qsci"
    return "unknown"


def _audit_artifact(
    *,
    name: str,
    path: Path,
    required: bool,
    kind: str,
    checks: list[dict[str, Any]],
    evidence_matrix: list[dict[str, Any]],
    id_prefix: str,
    acceptance_required: bool = False,
) -> dict[str, Any] | None:
    if not path.exists():
        _check(
            checks,
            check_id=f"{id_prefix}:{name}:exists",
            label=f"{name} artifact exists",
            passed=False,
            required=required,
            summary=f"Missing artifact: {path}",
            details={"path": str(path)},
        )
        return None

    _check(
        checks,
        check_id=f"{id_prefix}:{name}:exists",
        label=f"{name} artifact exists",
        passed=True,
        required=required,
        summary=str(path),
    )
    payload = _read_json(path)
    evidence_payload = _payload_with_release_evidence(payload)
    evidence_matrix.append(_artifact_matrix_entry(name, kind, path, evidence_payload))

    missing = _evidence_missing_fields(evidence_payload)
    _check(
        checks,
        check_id=f"{id_prefix}:{name}:evidence_summary",
        label=f"{name} evidence summary is release-readable",
        passed=not missing,
        required=required,
        summary="Evidence summary contains release-facing fields." if not missing else "Evidence summary is incomplete.",
        details={"missing_fields": missing},
    )

    runtime_failure = _runtime_boundary_failure(evidence_payload)
    _check(
        checks,
        check_id=f"{id_prefix}:{name}:runtime_boundary",
        label=f"{name} hardware boundary is conservative",
        passed=runtime_failure is None,
        required=required,
        summary="hardware_verified is consistent with retrieved runtime evidence."
        if runtime_failure is None
        else "hardware_verified is inconsistent with runtime_submission.",
        details={"failure": runtime_failure},
    )
    acceptance = payload.get("acceptance_summary") or evidence_payload.get("acceptance_summary")
    sidecar_acceptance_path = path.parent / "acceptance_summary.json"
    if not isinstance(acceptance, dict) and sidecar_acceptance_path.exists():
        acceptance = _read_json(sidecar_acceptance_path)
    if not isinstance(acceptance, dict):
        if acceptance_required:
            _check(
                checks,
                check_id=f"{id_prefix}:{name}:acceptance_summary",
                label=f"{name} acceptance summary is present",
                passed=False,
                required=True,
                summary="Acceptance summary is required but missing.",
                details={"path": str(sidecar_acceptance_path)},
            )
        else:
            _warning(
                checks,
                check_id=f"{id_prefix}:{name}:acceptance_summary",
                label=f"{name} acceptance summary is missing",
                summary="Acceptance summary is not present; release audit treats this as a warning unless required.",
                details={"path": str(sidecar_acceptance_path)},
            )
    else:
        accepted = bool(acceptance.get("accepted"))
        _check(
            checks,
            check_id=f"{id_prefix}:{name}:acceptance_summary",
            label=f"{name} acceptance summary is accepted",
            passed=accepted,
            required=acceptance_required,
            summary=(
                "Acceptance summary is present and accepted."
                if accepted
                else "Acceptance summary is present but not accepted."
            ),
            details={"recommended_action": acceptance.get("recommended_action")},
        )
    return evidence_payload


def _audit_exploratory_asset(
    asset: ReleaseAuditExploratoryAssetSpec,
    *,
    repo_root: Path,
    checks: list[dict[str, Any]],
    evidence_matrix: list[dict[str, Any]],
) -> None:
    config_path = _resolve(repo_root, asset.config)
    classified = classify_exploratory_config(config_path)
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:config",
        label=f"{asset.name} exploratory config is classified",
        passed=classified == asset.kind,
        required=asset.required,
        summary=f"classified={classified}, expected={asset.kind}",
        details={"config": str(config_path)},
    )

    if asset.artifact is None:
        _skipped(
            checks,
            check_id=f"exploratory_asset:{asset.name}:artifact",
            label=f"{asset.name} exploratory artifact is optional in this manifest",
            summary="No artifact path configured; config classification is still audited.",
        )
        return

    artifact_path = _resolve(repo_root, asset.artifact)
    payload = _audit_artifact(
        name=asset.name,
        path=artifact_path,
        required=asset.required,
        kind=asset.kind,
        checks=checks,
            evidence_matrix=evidence_matrix,
            id_prefix="exploratory_asset",
            acceptance_required=False,
        )
    if payload is None:
        return

    evidence = payload.get("evidence_summary") or {}
    verification_status = payload.get("verification_status")
    trust_tier = evidence.get("trust_tier")
    boundary_ok = verification_status == "exploratory" and trust_tier == "exploratory"
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:boundary",
        label=f"{asset.name} remains exploratory",
        passed=boundary_ok,
        required=asset.required,
        summary=f"verification_status={verification_status}, trust_tier={trust_tier}",
        details={"kind": asset.kind},
    )
    section_ok = _has_required_exploratory_section(asset.kind, payload)
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:section",
        label=f"{asset.name} carries its algorithm section",
        passed=section_ok,
        required=asset.required,
        summary=f"Required section for {asset.kind} is present." if section_ok else f"Missing section for {asset.kind}.",
    )
    notes = _risk_notes(payload)
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:risk_notes",
        label=f"{asset.name} carries scientific risk notes",
        passed=bool(notes),
        required=asset.required,
        summary="Scientific risk notes are present." if notes else "Scientific risk notes are missing.",
    )


def _audit_docs(spec: ReleaseAuditSpec, *, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    for doc in spec.required_docs:
        path = _resolve(repo_root, doc.path)
        if not path.exists():
            _check(
                checks,
                check_id=f"doc:{doc.path}:exists",
                label=f"{doc.path} exists",
                passed=False,
                required=doc.required,
                details={"path": str(path)},
            )
            continue
        text = path.read_text(encoding="utf-8").lower()
        missing = [term for term in doc.terms if term.lower() not in text]
        _check(
            checks,
            check_id=f"doc:{doc.path}:terms",
            label=f"{doc.path} includes release terms",
            passed=not missing,
            required=doc.required,
            summary="All release terms are present." if not missing else "Some release terms are missing.",
            details={"missing_terms": missing},
        )


def _render_release_audit_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# QCchem Release Readiness Audit",
        "",
        "- output: `release_readiness.md`",
        f"- profile: `{summary['profile']}`",
        f"- release_version: `{summary['release_version']}`",
        f"- status: `{summary['status']}`",
        f"- recommended_action: `{summary['recommended_action']}`",
        f"- required_pass_count: `{summary['required_pass_count']}`",
        f"- required_fail_count: `{summary['required_fail_count']}`",
        f"- warning_count: `{summary.get('warning_count', 0)}`",
        "",
        "## Evidence Matrix",
        "",
    ]
    for entry in summary["evidence_matrix"]:
        lines.extend(
            [
                f"### {entry['name']}",
                "",
                f"- kind: `{entry['kind']}`",
                f"- trust_tier: `{entry.get('trust_tier')}`",
                f"- recommended_action: `{entry.get('recommended_action')}`",
                f"- hardware_verified: `{entry.get('hardware_verified')}`",
                f"- path: `{entry.get('path')}`",
                "",
            ]
        )
    lines.extend(["## Checks", ""])
    for check in summary["checks"]:
        lines.append(
            f"- `{check['status']}` `{check['id']}` required=`{check['required']}` - {check.get('summary', '')}"
        )
    lines.append("")
    return "\n".join(lines)


def run_release_audit(
    spec: ReleaseAuditSpec,
    *,
    repo_root: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the Trust-First release audit and write readiness artifacts."""
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_output_dir = (output_dir or resolved_repo_root / "artifacts" / "release_audit").resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    evidence_matrix: list[dict[str, Any]] = []

    project_version = _read_project_version(resolved_repo_root / "pyproject.toml")
    _check(
        checks,
        check_id="project:version",
        label="pyproject release version matches audit manifest",
        passed=project_version == spec.release_version,
        required=True,
        summary=f"pyproject={project_version}, expected={spec.release_version}",
    )

    for artifact in spec.curated_artifacts:
        _audit_artifact(
            name=artifact.name,
            path=_resolve(resolved_repo_root, artifact.path),
            required=artifact.required,
            kind="curated",
            checks=checks,
            evidence_matrix=evidence_matrix,
            id_prefix="curated_artifact",
            acceptance_required=artifact.acceptance_required,
        )

    for asset in spec.exploratory_assets:
        _audit_exploratory_asset(asset, repo_root=resolved_repo_root, checks=checks, evidence_matrix=evidence_matrix)

    _audit_docs(spec, repo_root=resolved_repo_root, checks=checks)

    required_pass_count = sum(1 for check in checks if check["required"] and check["status"] == "passed")
    required_fail_count = sum(1 for check in checks if check["required"] and check["status"] == "failed")
    warning_count = sum(1 for check in checks if check["status"] == "warning")
    status = "passed" if required_fail_count == 0 else "failed"
    summary = {
        "schema_version": RELEASE_AUDIT_SCHEMA_VERSION,
        "profile": spec.profile,
        "release_version": spec.release_version,
        "status": status,
        "required_pass_count": required_pass_count,
        "required_fail_count": required_fail_count,
        "warning_count": warning_count,
        "checks": checks,
        "evidence_matrix": evidence_matrix,
        "acceptance_commands": list(spec.acceptance_commands),
        "recommended_action": "promote_alpha_release_candidate" if status == "passed" else "resolve_release_audit_failures",
    }

    (resolved_output_dir / "release_readiness.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (resolved_output_dir / "release_readiness.md").write_text(
        _render_release_audit_markdown(summary),
        encoding="utf-8",
    )
    return summary


def run_release_audit_from_config(
    config_path: Path,
    *,
    output_dir: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Load and run a release audit manifest."""
    spec = load_release_audit_spec(config_path)
    return run_release_audit(spec, repo_root=repo_root, output_dir=output_dir)
