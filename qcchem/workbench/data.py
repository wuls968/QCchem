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
        "periodic_boundary": extras.get("periodic_boundary") or extras.get("pbc"),
        "pbc": extras.get("pbc") or extras.get("periodic_boundary"),
        "pbc_qmmm": extras.get("pbc_qmmm"),
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
        "field_evidence": extras.get("field_evidence"),
        "field_model": extras.get("field_model"),
        "qft_model": extras.get("qft_model"),
        "qft_dynamics": extras.get("qft_dynamics"),
        "cavity_qed_model": extras.get("cavity_qed_model"),
        "provenance": qcschema.get("provenance"),
        "schema_version": qcschema.get("schema_version"),
        "run_id": extras.get("qcchem_run_id"),
    }


def load_artifact_bundle(root: Path) -> dict[str, Any]:
    result_path = root / "result.json"
    qcschema_path = root / "qcschema.json"
    hdf5_path = root / "result.h5"
    field_sidecars = {
        "field_model_registry": root / "field_model_registry.json",
        "field_hamiltonian": root / "field_hamiltonian.json",
        "field_observables": root / "field_observables.json",
        "field_dynamics": root / "field_dynamics.json",
        "field_constraints": root / "field_constraints.json",
        "field_resources": root / "field_resources.json",
        "field_error_budget": root / "field_error_budget.json",
    }
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
            "field_evidence": {
                name: {
                    "source": f"{name}.json",
                    "path": str(path),
                    "present": path.exists(),
                }
                for name, path in field_sidecars.items()
            },
            "pbc": {
                "source": "result.json/qcschema extras",
                "present": bool((run or {}).get("periodic_boundary") or (run or {}).get("pbc"))
                if isinstance(run, dict)
                else False,
            },
            "pbc_qmmm": {
                "source": "result.json/qcschema extras",
                "present": bool((run or {}).get("pbc_qmmm")) if isinstance(run, dict) else False,
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


def _latest_json(root: Path, pattern: str) -> dict[str, Any] | None:
    candidates = [path for path in root.glob(pattern) if path.is_file()]
    if not candidates:
        return None
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    payload = _load_json(latest)
    if isinstance(payload, dict):
        payload["source_path"] = str(latest)
        return payload
    return None


def load_research_os_snapshot(artifact_root: Path | None = None) -> dict[str, Any]:
    """Load latest Research OS review artifacts for workbench summaries."""
    root = artifact_root or _repo_artifact_root()
    objective_status = _latest_json(root, "objectives/**/objective_status.json")
    objective_plan = _latest_json(root, "objectives/**/objective_plan.json")
    claim_review = _latest_json(root, "claim_reviews/**/claim_review.json")
    promotion_review = _latest_json(root, "promotion/**/promotion_review.json")
    capsule = _latest_json(root, "**/evidence_capsule.json")
    objective = objective_status or objective_plan or {}
    missing_evidence = objective.get("missing_evidence") if isinstance(objective, dict) else []
    return {
        "objective": objective,
        "claim_review": claim_review or {},
        "promotion_review": promotion_review or {},
        "capsule": capsule or {},
        "open_evidence_gaps": missing_evidence if isinstance(missing_evidence, list) else [],
    }
