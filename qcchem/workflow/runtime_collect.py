"""Utilities for polling and rehydrating real runtime artifacts."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from qcchem.core.chemical_accuracy import check_chemical_accuracy
from qcchem.io.config import load_run_spec
from qcchem.io.exports import write_hdf5_result, write_qcschema_json
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_markdown_report, write_result_json
from qcchem.core.evidence import build_run_evidence_summary
from qcchem.workflow.runner import run_spec


def _normalize_status(status: Any) -> str:
    if hasattr(status, "name"):
        return str(status.name)
    return str(status)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _materialize_result_payload(artifact_root: Path) -> dict[str, Any]:
    result_path = artifact_root / "result.json"
    if result_path.exists():
        return _load_json(result_path)

    resolved_config_path = artifact_root / "resolved_config.yaml"
    if not resolved_config_path.exists():
        raise FileNotFoundError(
            f"No result.json or resolved_config.yaml found under '{artifact_root}'."
        )

    spec = load_run_spec(resolved_config_path)
    spec.backend.runtime.options["submit_real_job"] = False
    spec.backend.runtime.options["wait_for_result"] = False

    with tempfile.TemporaryDirectory(prefix="qcchem-runtime-collect-", dir=artifact_root.parent) as tmp_dir:
        tmp_root = Path(tmp_dir)
        result = run_spec(
            spec,
            source_config=str(resolved_config_path),
            output_dir=tmp_root,
        )
        payload = to_primitive(result)

    payload.setdefault("artifacts", {})
    payload["run_id"] = artifact_root.name
    payload["artifacts"].update(
        {
            "root": str(artifact_root),
            "resolved_config": str(artifact_root / "resolved_config.yaml"),
            "result_json": str(artifact_root / "result.json"),
            "exact_result_json": str(artifact_root / "exact_result.json"),
            "report_markdown": str(artifact_root / "report.md"),
            "log_file": str(artifact_root / "run.log"),
            "calibration_json": str(artifact_root / "calibration.json"),
            "calibration_report_markdown": str(artifact_root / "calibration_report.md"),
            "runtime_submission_json": str(artifact_root / "runtime_submission.json"),
        }
    )
    return payload


def _update_runtime_result_payload(
    artifact_root: Path,
    payload: dict[str, Any],
    runtime_submission: dict[str, Any],
) -> None:
    payload["run_id"] = artifact_root.name
    payload["runtime_submission"] = runtime_submission
    payload["hardware_verified"] = bool(
        runtime_submission.get("submitted") and runtime_submission.get("succeeded")
    )
    payload["hardware_evidence_tier"] = (
        "retrieved_result" if payload["hardware_verified"] else payload.get("hardware_evidence_tier")
    )

    exact_total = (((payload.get("exact_baseline") or {}).get("total_energy")))
    energy = payload.get("energy") or {}
    returned = runtime_submission.get("returned_job_metadata") or {}
    evs = returned.get("evs") or []
    stds = returned.get("stds") or []
    if exact_total is not None and evs:
        runtime_total = (
            float(evs[0])
            + float(energy.get("constant_energy_correction") or 0.0)
            + float(energy.get("nuclear_repulsion_energy") or 0.0)
        )
        payload["runtime_chemical_accuracy"] = to_primitive(
            check_chemical_accuracy(
                runtime_total,
                float(exact_total),
                assessment_target="runtime_derived",
                statistical_error=(float(stds[0]) if stds else None),
            )
        )

    payload.setdefault("verification_notes", [])
    if payload["hardware_verified"]:
        note = "Real runtime result retrieved and merged into the run artifact."
        if note not in payload["verification_notes"]:
            payload["verification_notes"].append(note)

    payload.setdefault("scientific_risk_notes", [])
    runtime_accuracy = payload.get("runtime_chemical_accuracy") or {}
    if (
        runtime_accuracy.get("available")
        and runtime_accuracy.get("meets_chemical_accuracy") is False
    ):
        note = "Runtime-derived chemistry estimate still does not meet chemical accuracy."
        if note not in payload["scientific_risk_notes"]:
            payload["scientific_risk_notes"].append(note)
    payload["evidence_summary"] = to_primitive(build_run_evidence_summary(payload))

    result_path = artifact_root / "result.json"
    report_path = artifact_root / "report.md"
    write_result_json(payload, result_path)
    write_markdown_report(payload, report_path)

    artifacts = payload.get("artifacts") or {}
    qcschema_path = artifacts.get("qcschema_json")
    if qcschema_path:
        write_qcschema_json(payload, Path(qcschema_path))
    hdf5_path = artifacts.get("hdf5_file")
    if hdf5_path:
        write_hdf5_result(payload, Path(hdf5_path))


def collect_runtime_artifact(artifact_root: Path) -> dict[str, object]:
    """Poll a runtime job and merge returned data back into an artifact directory."""
    resolved_root = artifact_root.expanduser().resolve()
    sidecar_path = resolved_root / "runtime_submission.json"
    if not sidecar_path.exists():
        raise FileNotFoundError(f"Missing runtime submission sidecar: '{sidecar_path}'.")

    runtime_submission = _load_json(sidecar_path)
    job_id = runtime_submission.get("job_id")
    if not job_id:
        raise ValueError(f"Runtime submission sidecar at '{sidecar_path}' does not contain a job_id.")

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(f"Unable to import qiskit_ibm_runtime: {type(exc).__name__}: {exc}") from exc

    service = QiskitRuntimeService()
    job = service.job(str(job_id))
    status_name = _normalize_status(job.status())

    runtime_submission.setdefault("result_provenance", {})
    runtime_submission["result_provenance"]["last_polled_status"] = status_name
    runtime_submission["result_provenance"]["last_polled_at"] = datetime.now(timezone.utc).isoformat()
    runtime_submission["provider"] = runtime_submission.get("provider") or type(service).__name__

    result_updated = False
    if status_name == "DONE":
        runtime_result = job.result()
        pub_result = runtime_result[0]
        runtime_submission["submitted"] = True
        runtime_submission["succeeded"] = True
        runtime_submission["failure_category"] = None
        runtime_submission["failure_message"] = None
        runtime_submission["returned_job_metadata"] = {
            "evs": np.asarray(pub_result.data.evs).tolist(),
            "stds": np.asarray(pub_result.data.stds).tolist(),
            "metadata": dict(pub_result.metadata),
        }
        usage_estimation = getattr(job, "usage_estimation", None)
        runtime_submission["usage_estimation"] = dict(usage_estimation) if usage_estimation else {}
        metrics = job.metrics()
        runtime_submission["job_metrics"] = dict(metrics) if metrics else {}
        runtime_submission["result_provenance"]["attempt_stage"] = "result_retrieved"

        payload = _materialize_result_payload(resolved_root)
        _update_runtime_result_payload(resolved_root, payload, runtime_submission)
        result_updated = True
    else:
        runtime_submission["result_provenance"]["attempt_stage"] = "status_polled"

    write_result_json(runtime_submission, sidecar_path)
    return {
        "artifact_root": str(resolved_root),
        "job_id": str(job_id),
        "status": status_name,
        "result_updated": result_updated,
    }
