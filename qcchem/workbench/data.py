from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_qcschema_payload(qcschema: dict[str, Any]) -> dict[str, Any]:
    extras = qcschema.get("extras") or {}
    properties = qcschema.get("properties") or {}
    molecule = qcschema.get("molecule") or {}
    model = qcschema.get("model") or {}

    return {
        "problem": {
            "molecule_name": molecule.get("name"),
            "basis": model.get("basis"),
            "charge": molecule.get("charge"),
            "multiplicity": molecule.get("multiplicity"),
        },
        "energy": {
            "total_energy": properties.get("return_energy"),
            "electronic_energy": properties.get("electronic_energy"),
            "nuclear_repulsion_energy": properties.get("nuclear_repulsion_energy"),
        },
        "mapping": extras.get("mapping") or {},
        "benchmark": extras.get("benchmark"),
        "reduction_audit": extras.get("reduction_audit"),
        "runtime_submission": extras.get("runtime_submission"),
        "compression_result": extras.get("compression_result"),
        "verification_status": qcschema.get("success") if qcschema.get("success") is not None else extras.get("verification_status"),
        "hardware_verified": extras.get("hardware_verified"),
        "hardware_evidence_tier": extras.get("hardware_evidence_tier"),
        "chemical_accuracy": extras.get("chemical_accuracy"),
        "runtime_chemical_accuracy": extras.get("runtime_chemical_accuracy"),
        "measurement": extras.get("measurement"),
        "calibration": extras.get("calibration"),
        "runtime_options": extras.get("runtime_options"),
        "perturbative_correction_result": extras.get("perturbative_correction_result"),
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
        "preferred_source": preferred_source,
        "run": run,
        "result": result,
        "qcschema": qcschema,
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
