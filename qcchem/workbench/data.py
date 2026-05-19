from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.io.artifact_index import build_artifact_index
from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary
from qcchem.workbench.viewmodels import build_run_view_model


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_qcschema_payload(qcschema: dict[str, Any]) -> dict[str, Any]:
    extras = qcschema.get("extras") or {}
    properties = qcschema.get("properties") or {}
    molecule = qcschema.get("molecule") or {}
    model = qcschema.get("model") or {}
    reduction_audit = extras.get("reduction_audit") or {}
    verification_status = extras.get("verification_status")
    success = qcschema.get("success")
    if verification_status is None:
        verification_status = success

    return {
        "problem": {
            "molecule_name": molecule.get("name"),
            "basis": model.get("basis"),
            "charge": molecule.get("charge"),
            "multiplicity": molecule.get("multiplicity"),
            "active_space_metadata": reduction_audit.get("active_space_metadata"),
        },
        "energy": {
            "total_energy": properties.get("return_energy"),
            "electronic_energy": properties.get("electronic_energy"),
            "nuclear_repulsion_energy": properties.get("nuclear_repulsion_energy"),
        },
        "mapping": extras.get("mapping") or {},
        "benchmark": extras.get("benchmark"),
        "reduction_audit": reduction_audit,
        "runtime_submission": extras.get("runtime_submission"),
        "compression_result": extras.get("compression_result"),
        "verification_status": verification_status,
        "success": success,
        "hardware_verified": extras.get("hardware_verified"),
        "hardware_evidence_tier": extras.get("hardware_evidence_tier"),
        "chemical_accuracy": extras.get("chemical_accuracy"),
        "runtime_chemical_accuracy": extras.get("runtime_chemical_accuracy"),
        "measurement": extras.get("measurement"),
        "calibration": extras.get("calibration"),
        "runtime_options": extras.get("runtime_options"),
        "perturbative_correction_result": extras.get("perturbative_correction_result"),
        "evidence_summary": extras.get("evidence_summary"),
        "quantum_evidence": extras.get("quantum_evidence"),
        "provenance": qcschema.get("provenance"),
        "schema_version": qcschema.get("schema_version"),
        "run_id": extras.get("qcchem_run_id"),
    }


def load_artifact_bundle(root: Path) -> dict[str, Any]:
    result_path = root / "result.json"
    qcschema_path = root / "qcschema.json"
    hdf5_path = root / "result.h5"
    result = _load_json(result_path)
    qcschema = _load_json(qcschema_path)
    preferred_source = "result" if result is not None else "qcschema" if qcschema is not None else None
    run = result or (_normalize_qcschema_payload(qcschema) if qcschema is not None else None)
    bundle = {
        "root": str(root),
        "result": result,
        "qcschema": qcschema,
        "hdf5_path": str(hdf5_path) if hdf5_path.exists() else None,
        "preferred_source": preferred_source,
        "run": run,
        "artifacts": {
            "result": {
                "source": "result.json",
                "path": str(result_path),
                "present": result is not None,
            },
            "qcschema": {
                "source": "qcschema.json",
                "path": str(qcschema_path),
                "present": qcschema is not None,
            },
            "hdf5": {
                "source": "result.h5",
                "path": str(hdf5_path),
                "present": hdf5_path.exists(),
            },
        },
    }
    return bundle


def _repo_artifact_root() -> Path:
    return Path(__file__).resolve().parents[2] / "artifacts"


def _preferred_entry(entries: list[dict[str, Any]], *, kinds: set[str]) -> dict[str, Any] | None:
    matching = [entry for entry in entries if str(entry.get("artifact_kind")) in kinds]
    if not matching:
        return None
    preferred_names = [
        "h2_runtime_hardware_probe_puccd_layout",
        "h2",
        "benchmark_suite_v1",
        "hardware_calibration_suite_v1",
    ]
    for name in preferred_names:
        for entry in matching:
            if str(entry.get("artifact_root", "")).endswith(f"/{name}") or entry.get("artifact_name") == name:
                return entry
    return max(matching, key=lambda item: float(item.get("mtime") or 0.0))


def load_featured_run_view_model(artifact_root: Path | None = None) -> dict[str, Any] | None:
    """Load the best available run artifact for workbench pages."""

    root = artifact_root or _repo_artifact_root()
    index = build_artifact_index(root)
    entry = _preferred_entry(list(index.get("artifacts") or []), kinds={"run"})
    if not entry:
        return None
    bundle = load_artifact_bundle(Path(str(entry["artifact_root"])))
    run = bundle.get("run")
    if not isinstance(run, dict):
        return None
    view = build_run_view_model(run)
    view["artifact_index_entry"] = entry
    return view


def load_featured_benchmark_model(artifact_root: Path | None = None) -> dict[str, Any] | None:
    root = artifact_root or _repo_artifact_root()
    index = build_artifact_index(root)
    entry = _preferred_entry(list(index.get("artifacts") or []), kinds={"benchmark_suite"})
    if not entry:
        return None
    payload = _load_json(Path(str(entry["result_json"])))
    if isinstance(payload, dict):
        payload["artifact_index_entry"] = entry
        return payload
    return None


def load_featured_hardware_campaign_model(artifact_root: Path | None = None) -> dict[str, Any] | None:
    root = artifact_root or _repo_artifact_root()
    index = build_artifact_index(root)
    entry = _preferred_entry(list(index.get("artifacts") or []), kinds={"hardware_calibration"})
    if not entry:
        return None
    payload = _load_json(Path(str(entry["result_json"])))
    if not isinstance(payload, dict):
        return None
    summary = build_hardware_campaign_summary(payload)
    summary["artifact_index_entry"] = entry
    return summary
