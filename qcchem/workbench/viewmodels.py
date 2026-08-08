from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalized_pbc_model(value: Any) -> dict[str, Any]:
    pbc = _safe_dict(value)
    if not pbc:
        return {}
    if "cell_vectors" not in pbc:
        return pbc
    return {
        **pbc,
        "enabled": pbc.get("enabled"),
        "status": "executed_gamma_supercell" if pbc.get("enabled") else None,
        "periodicity": "3d" if pbc.get("pbc") == [True, True, True] else "mixed",
        "cell": {
            "units": pbc.get("cell_unit"),
            "vectors": pbc.get("cell_vectors", []),
            "volume": pbc.get("volume"),
            "fingerprint": pbc.get("fingerprint"),
        },
        "kpoints": {"mode": "gamma", "grid": pbc.get("kpoint_mesh", [1, 1, 1])},
        "boundary_conditions": pbc.get("pbc"),
        "core_runner_implemented": True,
    }


def _normalized_pbc_qmmm_model(value: Any) -> dict[str, Any]:
    pbc_qmmm = _safe_dict(value)
    if not pbc_qmmm:
        return {}
    if "one_body_environment" not in pbc_qmmm:
        return pbc_qmmm
    return {
        **pbc_qmmm,
        "status": "executed_ewald" if pbc_qmmm.get("enabled") else None,
        "embedding_mode": pbc_qmmm.get("mode"),
        "qm_region": pbc_qmmm.get("provenance", {}).get("qm_region", {}),
        "mm_region": {
            "charge_count": pbc_qmmm.get("charge_count"),
            "total_charge": pbc_qmmm.get("total_mm_charge"),
        },
        "boundary": {
            "neutralization": pbc_qmmm.get("neutralization"),
            "background_energy": pbc_qmmm.get("background_energy"),
        },
        "core_runner_implemented": True,
    }


def build_runtime_comparison_model(model: dict[str, Any]) -> dict[str, Any]:
    benchmark = model.get("benchmark") or {}
    runtime = model.get("runtime") or {}
    confidence = model.get("confidence") or {}
    chemical_accuracy = confidence.get("chemical_accuracy") or {}
    runtime_chemical_accuracy = confidence.get("runtime_chemical_accuracy") or {}

    simulator_error = float(benchmark.get("absolute_error") or confidence.get("absolute_error") or 0.0)
    hardware_error = float(runtime_chemical_accuracy.get("absolute_error_hartree") or simulator_error)
    threshold = float(chemical_accuracy.get("threshold_hartree") or confidence.get("threshold") or benchmark.get("threshold") or 0.02)
    comparison_target = str(
        confidence.get("comparison_target")
        or confidence.get("boundary", {}).get("comparison_target")
        or benchmark.get("comparison_target")
        or "exact diagonalization"
    )
    backend_name = str(runtime.get("backend_name") or "n/a")
    backend_version = str(runtime.get("backend_version") or "")
    queue_stage = str(_safe_dict(runtime.get("result_provenance")).get("attempt_stage") or "pending")
    returned_job_metadata = _safe_dict(runtime.get("returned_job_metadata"))
    shots = _safe_dict(returned_job_metadata.get("metadata")).get("shots")
    if shots is None:
        shots = _safe_dict(runtime.get("options_snapshot")).get("shots")

    meets_hardware_threshold = runtime_chemical_accuracy.get("meets_chemical_accuracy")
    if meets_hardware_threshold is True:
        hardware_verdict = "Within threshold"
        verdict_note = "Runtime-backed hardware evidence stays inside the defended acceptance line."
    elif meets_hardware_threshold is False:
        hardware_verdict = "Needs review"
        verdict_note = "Runtime-backed hardware evidence misses the defended acceptance line."
    else:
        hardware_verdict = "Evidence pending"
        verdict_note = "Hardware accuracy has not been classified yet."

    backend_label = backend_name if not backend_version else f"{backend_name} ({backend_version})"
    shot_note = f"{shots} shots" if shots is not None else "Shots pending"
    return {
        "simulator_reference": comparison_target,
        "simulator_error_hartree": simulator_error,
        "hardware_backend": backend_name,
        "hardware_backend_label": backend_label,
        "hardware_error_hartree": hardware_error,
        "error_gap_hartree": abs(hardware_error - simulator_error),
        "threshold_hartree": threshold,
        "hardware_verdict": hardware_verdict,
        "hardware_verdict_note": verdict_note,
        "queue_stage": queue_stage,
        "shot_note": shot_note,
    }


def build_run_view_model(payload: dict[str, Any]) -> dict[str, Any]:
    problem = payload["problem"]
    energy = payload["energy"]
    benchmark = payload.get("benchmark") or {}
    runtime = _safe_dict(payload.get("runtime_submission"))
    reduction = payload.get("reduction_audit") or {}
    compression = payload.get("compression_result") or {}
    evidence_summary = payload.get("evidence_summary") or {}
    field_evidence = payload.get("field_evidence") or {}
    pbc = _normalized_pbc_model(payload.get("periodic_boundary") or payload.get("pbc"))
    pbc_qmmm = _normalized_pbc_qmmm_model(payload.get("pbc_qmmm"))
    variational = _safe_dict(payload.get("variational_result"))
    ansatz = _safe_dict(variational.get("ansatz"))
    lr_ace = _safe_dict(ansatz.get("lr_ace"))

    view_model = {
        "hero": {
            "molecule_name": problem["molecule_name"],
            "basis": problem.get("basis"),
            "total_energy": energy.get("total_energy"),
            "absolute_error": benchmark.get("absolute_error"),
            "primary_claim": evidence_summary.get("primary_scientific_claim"),
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
        "pbc": {
            "enabled": pbc.get("enabled"),
            "status": pbc.get("status"),
            "periodicity": pbc.get("periodicity"),
            "cell": pbc.get("cell", {}),
            "kpoints": pbc.get("kpoints", {}),
            "boundary_conditions": pbc.get("boundary_conditions"),
            "core_runner_implemented": pbc.get("core_runner_implemented"),
        },
        "pbc_qmmm": {
            "enabled": pbc_qmmm.get("enabled"),
            "status": pbc_qmmm.get("status"),
            "embedding_mode": pbc_qmmm.get("embedding_mode"),
            "qm_region": pbc_qmmm.get("qm_region", {}),
            "mm_region": pbc_qmmm.get("mm_region", {}),
            "boundary": pbc_qmmm.get("boundary", {}),
            "core_runner_implemented": pbc_qmmm.get("core_runner_implemented"),
            "notes": pbc_qmmm.get("notes", []),
        },
        "lr_ace": lr_ace,
        "evidence_summary": evidence_summary,
        "field_evidence": {
            "available": field_evidence.get("available"),
            "schema": field_evidence.get("schema"),
            "active_model_kind": field_evidence.get("active_model_kind"),
            "sidecars": field_evidence.get("sidecars", {}),
            "sidecar_sha256": field_evidence.get("sidecar_sha256", {}),
            "hamiltonian": field_evidence.get("hamiltonian", {}),
            "observables": field_evidence.get("observables", {}),
            "dynamics": field_evidence.get("dynamics", {}),
            "constraints": field_evidence.get("constraints", {}),
            "resources": field_evidence.get("resources", {}),
            "error_budget": field_evidence.get("error_budget", {}),
        },
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
            "recommended_action": evidence_summary.get("recommended_action"),
            "trust_tier": evidence_summary.get("trust_tier", payload.get("verification_status")),
        },
    }
    view_model["runtime_comparison"] = build_runtime_comparison_model(view_model)
    return view_model
