"""Optional interoperability and provenance exports."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

import h5py

from qcchem.io.serialization import to_primitive


def _require_sections(data: dict[str, Any], required: tuple[str, ...]) -> None:
    missing = [section for section in required if data.get(section) in (None, {})]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"missing required sections: {missing_list}")


def _require_present_value(section: dict[str, Any], section_name: str, key_path: str) -> None:
    current: Any = section
    for key in key_path.split("."):
        if not isinstance(current, dict) or key not in current:
            raise ValueError(f"missing required field: {section_name}.{key_path}")
        current = current[key]
    if current in (None, ""):
        raise ValueError(f"missing required field: {section_name}.{key_path}")


def build_qcschema_payload(result: Any) -> dict[str, Any]:
    """Build a minimal QCSchema-style export from a QCchem run result."""
    data = to_primitive(result)
    _require_sections(data, ("problem", "energy"))
    problem = data.get("problem") or {}
    energy = data.get("energy") or {}
    provenance = data.get("provenance") or {}
    input_sources = provenance.get("input_sources", [])
    _require_present_value(problem, "problem", "molecule_name")
    _require_present_value(energy, "energy", "total_energy")
    verification_status = data.get("verification_status")
    success = data.get("success")
    if success is None:
        success = verification_status not in (None, "failed", False)
    return {
        "schema_name": "qcschema_output",
        "schema_version": 1,
        "driver": "energy",
        "model": {
            "method": (data.get("solver") or {}).get("kind", "qcchem"),
            "basis": problem.get("basis"),
        },
        "molecule": {
            "name": problem.get("molecule_name"),
            "charge": problem.get("charge"),
            "multiplicity": problem.get("multiplicity"),
        },
        "properties": {
            "return_energy": energy.get("total_energy"),
            "electronic_energy": energy.get("electronic_energy"),
            "nuclear_repulsion_energy": energy.get("nuclear_repulsion_energy"),
            "external_point_charge_nuclear_interaction_energy": energy.get(
                "external_point_charge_nuclear_interaction_energy"
            ),
            "boundary_embedding_constant_energy": energy.get(
                "boundary_embedding_constant_energy"
            ),
        },
        "provenance": {
            "creator": "QCchem",
            "version": data.get("schema_version"),
            "routine": "qcchem.workflow.runner.run_spec",
            "git_commit": provenance.get("git_commit"),
            "git_branch": provenance.get("git_branch"),
            "workspace_fingerprint": provenance.get("workspace_fingerprint"),
        },
        "extras": {
            "qcchem_run_id": data.get("run_id"),
            "verification_status": verification_status,
            "hardware_verified": data.get("hardware_verified", False),
            "hardware_evidence_tier": data.get("hardware_evidence_tier"),
            "mapping": data.get("mapping"),
            "reduction_audit": data.get("reduction_audit"),
            "measurement": data.get("measurement"),
            "calibration": data.get("calibration"),
            "chemical_accuracy": data.get("chemical_accuracy"),
            "runtime_chemical_accuracy": data.get("runtime_chemical_accuracy"),
            "runtime_options": data.get("runtime_options"),
            "runtime_submission": data.get("runtime_submission"),
            "input_provenance": input_sources,
            "compression_result": data.get("compression_result"),
            "perturbative_correction_result": data.get("perturbative_correction_result"),
            "external_point_charges": data.get("external_point_charges"),
            "environment_embedding": data.get("environment_embedding"),
            "tc_qsci_result": data.get("tc_qsci_result"),
            "determinant_selection": data.get("determinant_selection"),
            "symmetry_sector": data.get("symmetry_sector"),
            "cast_hamiltonian": data.get("cast_hamiltonian"),
            "low_rank_resource_estimate": data.get("low_rank_resource_estimate"),
            "qpe_resource_estimate": data.get("qpe_resource_estimate"),
            "error_budget": data.get("error_budget"),
            "field_model": data.get("field_model"),
            "qft_model": data.get("qft_model"),
            "qft_dynamics": data.get("qft_dynamics"),
            "cavity_qed_model": data.get("cavity_qed_model"),
        },
        "return_result": energy.get("total_energy"),
        "success": success,
    }


def write_qcschema_json(result: Any, path: Path) -> None:
    """Write a QCSchema-style JSON export."""
    path.write_text(json.dumps(build_qcschema_payload(result), indent=2, sort_keys=True), encoding="utf-8")


def write_hdf5_result(result: Any, path: Path) -> None:
    """Write a generic HDF5 export of the QCchem result."""
    data = to_primitive(result)

    def _write(group, key: str, value: Any) -> None:
        if value is None:
            group.attrs[key] = "__none__"
            return
        if isinstance(value, dict):
            subgroup = group.create_group(key)
            for child_key, child_value in value.items():
                _write(subgroup, str(child_key), child_value)
            return
        if isinstance(value, list):
            if not value:
                group.create_dataset(key, data=[])
                return
            if all(not isinstance(item, (dict, list)) for item in value):
                group.create_dataset(key, data=[json.dumps(item) if isinstance(item, (bool, str)) else item for item in value])
                return
            subgroup = group.create_group(key)
            for index, item in enumerate(value):
                _write(subgroup, str(index), item)
            return
        if isinstance(value, (str, bool)):
            group.attrs[key] = json.dumps(value)
            return
        group.attrs[key] = value

    with h5py.File(path, "w") as handle:
        for top_key, top_value in data.items():
            _write(handle, str(top_key), top_value)


def workspace_fingerprint(payloads: list[str]) -> str:
    """Build a stable fingerprint from provenance-relevant payloads."""
    digest = hashlib.sha256()
    for item in payloads:
        digest.update(item.encode("utf-8"))
    return digest.hexdigest()
