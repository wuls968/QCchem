from __future__ import annotations

from typing import Any


def build_run_view_model(payload: dict[str, Any]) -> dict[str, Any]:
    problem = payload["problem"]
    energy = payload["energy"]
    benchmark = payload.get("benchmark") or {}

    return {
        "hero": {
            "molecule_name": problem["molecule_name"],
            "basis": problem.get("basis"),
            "total_energy": energy.get("total_energy"),
            "absolute_error": benchmark.get("absolute_error"),
        },
        "structure": {
            "molecule_name": problem["molecule_name"],
            "active_space_metadata": problem.get("active_space_metadata"),
        },
        "mapping": payload.get("mapping") or {},
        "runtime": payload.get("runtime_submission") or {},
        "reduction": payload.get("reduction_audit") or {},
        "compression": payload.get("compression_result") or {},
        "confidence": {
            "verification_status": payload.get("verification_status"),
            "hardware_verified": payload.get("hardware_verified"),
            "chemical_accuracy": payload.get("chemical_accuracy"),
            "runtime_chemical_accuracy": payload.get("runtime_chemical_accuracy"),
        },
    }
