from __future__ import annotations

from typing import Any


def build_run_view_model(payload: dict[str, Any]) -> dict[str, Any]:
    problem = payload["problem"]
    energy = payload["energy"]
    benchmark = payload.get("benchmark") or {}
    runtime = payload.get("runtime_submission") or {}
    reduction = payload.get("reduction_audit") or {}
    compression = payload.get("compression_result") or {}

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
        "benchmark": {
            "absolute_error": benchmark.get("absolute_error"),
            "relative_error": benchmark.get("relative_error"),
            "meets_threshold": benchmark.get("meets_threshold"),
            "within_uncertainty": benchmark.get("within_uncertainty"),
            "threshold": benchmark.get("threshold"),
            "comparison_target": benchmark.get("comparison_target"),
            "compressed_vs_uncompressed": benchmark.get("compressed_vs_uncompressed"),
        },
        "runtime": {
            "backend_name": runtime.get("backend_name"),
            "backend_version": runtime.get("backend_version"),
            "provider": runtime.get("provider"),
            "job_id": runtime.get("job_id"),
            "attempted": runtime.get("attempted"),
            "submitted": runtime.get("submitted"),
            "succeeded": runtime.get("succeeded"),
            "runtime_kind": runtime.get("runtime_kind"),
            "mode": runtime.get("mode"),
            "service": runtime.get("service"),
            "transpiled_depth": runtime.get("transpiled_depth"),
            "transpiled_two_qubit_gate_count": runtime.get("transpiled_two_qubit_gate_count"),
            "transpilation": runtime.get("transpilation"),
            "failure_category": runtime.get("failure_category"),
            "failure_message": runtime.get("failure_message"),
            "options_snapshot": runtime.get("options_snapshot"),
            "result_provenance": runtime.get("result_provenance"),
            "returned_job_metadata": runtime.get("returned_job_metadata"),
            "verification_status": runtime.get("verification_status"),
        },
        "reduction": reduction,
        "compression": compression,
        "confidence": {
            "verification_status": payload.get("verification_status"),
            "hardware_verified": payload.get("hardware_verified"),
            "chemical_accuracy": payload.get("chemical_accuracy"),
            "runtime_chemical_accuracy": payload.get("runtime_chemical_accuracy"),
            "absolute_error": benchmark.get("absolute_error"),
            "relative_error": benchmark.get("relative_error"),
            "threshold": benchmark.get("threshold"),
            "meets_threshold": benchmark.get("meets_threshold"),
            "within_uncertainty": benchmark.get("within_uncertainty"),
            "boundary": {
                "absolute_error": benchmark.get("absolute_error"),
                "relative_error": benchmark.get("relative_error"),
                "threshold": benchmark.get("threshold"),
                "meets_threshold": benchmark.get("meets_threshold"),
                "within_uncertainty": benchmark.get("within_uncertainty"),
                "comparison_target": benchmark.get("comparison_target"),
                "compressed_vs_uncompressed": benchmark.get("compressed_vs_uncompressed"),
            },
        },
    }
