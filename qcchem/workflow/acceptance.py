"""Benchmark acceptance policy evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json


DEFAULT_REQUIRED_FILES = ["result.json"]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _artifact_root(case: dict[str, Any], benchmark_result_path: Path | None = None) -> Path | None:
    raw = case.get("artifact_root")
    if not raw:
        return None
    root = Path(str(raw))
    if root.is_absolute():
        return root
    if benchmark_result_path is not None:
        candidate = (benchmark_result_path.parent / root).resolve()
        if candidate.exists():
            return candidate
    return root.resolve()


def _case_evidence_missing(case: dict[str, Any], artifact_payload: dict[str, Any] | None) -> bool:
    if isinstance(case.get("evidence_summary"), dict):
        return False
    if artifact_payload is not None and isinstance(artifact_payload.get("evidence_summary"), dict):
        return False
    return True


def _runtime_accuracy_promoted(artifact_payload: dict[str, Any]) -> bool:
    runtime_accuracy = _safe_dict(artifact_payload.get("runtime_chemical_accuracy"))
    if runtime_accuracy.get("meets_chemical_accuracy") is not False:
        return False
    evidence = _safe_dict(artifact_payload.get("evidence_summary"))
    promoted_action = evidence.get("recommended_action") == "promote_validated_result"
    runtime_status = evidence.get("runtime_evidence_status")
    promoted_runtime_status = runtime_status in {"validated", "chemical_accuracy_met"}
    return bool(promoted_action or promoted_runtime_status)


def _evaluate_case(
    case: dict[str, Any],
    *,
    benchmark_result_path: Path | None,
    required_files: list[str],
    require_evidence_summary: bool,
    require_runtime_sidecar_for_hardware_verified: bool,
    fail_on_runtime_accuracy_promotion: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    name = str(case.get("name") or "unnamed_case")
    status = str(case.get("status") or "")
    expected = str(case.get("expected_status") or "validated")
    if expected and status != expected:
        failures.append(
            {
                "case": name,
                "reason": "status_mismatch",
                "status": status,
                "expected_status": expected,
            }
        )

    root = _artifact_root(case, benchmark_result_path)
    artifact_payload = None
    if root is None:
        warnings.append({"case": name, "reason": "missing_artifact_root"})
    else:
        for filename in required_files:
            required_path = root / filename
            if not required_path.exists():
                failures.append(
                    {
                        "case": name,
                        "reason": "missing_required_artifact_file",
                        "path": str(required_path),
                    }
                )
        artifact_payload = _read_json(root / "result.json")
        sidecar = _read_json(root / "runtime_submission.json")
        payload_hardware_verified = bool((artifact_payload or {}).get("hardware_verified"))
        metric_hardware_verified = bool(_safe_dict(case.get("metrics")).get("hardware_verified"))
        if require_runtime_sidecar_for_hardware_verified and (payload_hardware_verified or metric_hardware_verified):
            if sidecar is None:
                failures.append(
                    {
                        "case": name,
                        "reason": "hardware_verified_without_runtime_sidecar",
                        "artifact_root": str(root),
                    }
                )
            elif not (sidecar.get("submitted") and sidecar.get("succeeded")):
                failures.append(
                    {
                        "case": name,
                        "reason": "hardware_verified_without_retrieved_runtime_result",
                        "artifact_root": str(root),
                    }
                )
        if artifact_payload is not None and fail_on_runtime_accuracy_promotion:
            if _runtime_accuracy_promoted(artifact_payload):
                failures.append(
                    {
                        "case": name,
                        "reason": "runtime_accuracy_promoted_despite_miss",
                        "artifact_root": str(root),
                    }
                )

    if require_evidence_summary and _case_evidence_missing(case, artifact_payload):
        failures.append({"case": name, "reason": "missing_evidence_summary"})

    return failures, warnings


def build_benchmark_acceptance_summary(
    benchmark_payload: dict[str, Any],
    *,
    benchmark_result_path: Path | None = None,
    required_files: list[str] | None = None,
    require_evidence_summary: bool = True,
    require_runtime_sidecar_for_hardware_verified: bool = True,
    fail_on_runtime_accuracy_promotion: bool = True,
    strict_exit_code: bool = False,
) -> dict[str, Any]:
    """Evaluate a benchmark-result payload against the default trust-loop policy."""

    required_files = list(required_files or DEFAULT_REQUIRED_FILES)
    cases = list(benchmark_payload.get("cases") or [])
    blocking_failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            warnings.append({"case": "unknown", "reason": "non_mapping_case"})
            continue
        failures, case_warnings = _evaluate_case(
            case,
            benchmark_result_path=benchmark_result_path,
            required_files=required_files,
            require_evidence_summary=require_evidence_summary,
            require_runtime_sidecar_for_hardware_verified=require_runtime_sidecar_for_hardware_verified,
            fail_on_runtime_accuracy_promotion=fail_on_runtime_accuracy_promotion,
        )
        blocking_failures.extend(failures)
        warnings.extend(case_warnings)

    if require_evidence_summary and not isinstance(benchmark_payload.get("evidence_summary"), dict):
        blocking_failures.append({"suite": benchmark_payload.get("suite_name"), "reason": "missing_suite_evidence_summary"})

    accepted = not blocking_failures
    recommended_action = (
        "promote_accepted_benchmark"
        if accepted and not warnings
        else "review_acceptance_warnings"
        if accepted
        else "resolve_benchmark_acceptance_failures"
    )
    return {
        "schema_version": "qcchem.benchmark_acceptance.v0.1-alpha",
        "suite_name": benchmark_payload.get("suite_name"),
        "accepted": accepted,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "case_count": len(cases),
        "required_files": required_files,
        "policy": {
            "require_evidence_summary": require_evidence_summary,
            "require_runtime_sidecar_for_hardware_verified": require_runtime_sidecar_for_hardware_verified,
            "fail_on_runtime_accuracy_promotion": fail_on_runtime_accuracy_promotion,
            "strict_exit_code": strict_exit_code,
        },
        "recommended_action": recommended_action,
    }


def accept_benchmark_result(
    benchmark_result_json: Path,
    *,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate and optionally persist acceptance for a benchmark result file."""

    payload = json.loads(benchmark_result_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Benchmark result must contain a JSON object.")
    summary = build_benchmark_acceptance_summary(
        payload,
        benchmark_result_path=benchmark_result_json,
    )
    if output_path is None:
        output_path = benchmark_result_json.with_name("acceptance_summary.json")
    write_result_json(to_primitive(summary), output_path)
    return summary
