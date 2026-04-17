"""Optional interoperability and provenance exports."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

import h5py

from qcchem.io.serialization import to_primitive


def build_qcschema_payload(result: Any) -> dict[str, Any]:
    """Build a minimal QCSchema-style export from a QCchem run result."""
    data = to_primitive(result)
    return {
        "schema_name": "qcschema_output",
        "schema_version": 1,
        "driver": "energy",
        "model": {
            "method": data["solver"]["kind"] if "solver" in data else "qcchem",
            "basis": data["problem"]["basis"],
        },
        "molecule": {
            "name": data["problem"]["molecule_name"],
            "charge": data["problem"]["charge"],
            "multiplicity": data["problem"]["multiplicity"],
        },
        "properties": {
            "return_energy": data["energy"]["total_energy"],
            "electronic_energy": data["energy"]["electronic_energy"],
            "nuclear_repulsion_energy": data["energy"]["nuclear_repulsion_energy"],
        },
        "provenance": {
            "creator": "QCchem",
            "version": data["schema_version"],
            "routine": "qcchem.workflow.runner.run_spec",
            "git_commit": data["provenance"]["git_commit"],
            "git_branch": data["provenance"].get("git_branch"),
            "workspace_fingerprint": data["provenance"].get("workspace_fingerprint"),
        },
        "extras": {
            "qcchem_run_id": data["run_id"],
            "verification_status": data["verification_status"],
            "hardware_verified": data.get("hardware_verified", False),
            "hardware_evidence_tier": data.get("hardware_evidence_tier"),
            "mapping": data["mapping"],
            "reduction_audit": data.get("reduction_audit"),
            "measurement": data.get("measurement"),
            "calibration": data.get("calibration"),
            "runtime_options": data.get("runtime_options"),
            "runtime_submission": data.get("runtime_submission"),
            "compression_result": data.get("compression_result"),
            "perturbative_correction_result": data.get("perturbative_correction_result"),
        },
        "return_result": data["energy"]["total_energy"],
        "success": data["verification_status"] != "failed",
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
