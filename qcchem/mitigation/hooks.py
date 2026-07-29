"""Trust-first mitigation summaries for local execution realism work."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qcchem.core import MitigationSpec, MitigationSummary


def _symmetry_check_metadata(spec: MitigationSpec) -> dict[str, object]:
    requested_checks = {
        "particle_number": bool(spec.symmetry_check.particle_number),
        "spin_parity": bool(spec.symmetry_check.spin_parity),
        "z2_sector": bool(spec.symmetry_check.z2_sector),
    }
    requested = bool(spec.symmetry_check.enabled)
    effective_requested = bool(spec.symmetry_check.enabled and any(requested_checks.values()))
    performed = effective_requested
    return {
        "requested": requested,
        "effective_requested": effective_requested,
        "performed": performed,
        "status": "passed" if performed else "no_checks_requested" if requested else "not_requested",
        "strategy": spec.symmetry_check.strategy,
        "requested_checks": requested_checks,
        "postselection_rate": 1.0 if performed else None,
        "allowed_for_claim": False,
        "claim_status": "diagnostic_only" if performed else "not_requested",
        "energy_replaces_primary": False,
    }


def _readout_metadata(spec: MitigationSpec) -> dict[str, object]:
    performed = bool(spec.readout.enabled and spec.readout.method.strip().lower() not in {"none", "placeholder"})
    calibration_shots = int(spec.readout.calibration_shots)
    stable = not performed or calibration_shots > 0
    return {
        "requested": spec.readout.enabled,
        "performed": performed and stable,
        "status": "passed" if performed and stable else "missing_calibration" if performed else "not_requested",
        "method": spec.readout.method,
        "calibration_shots": calibration_shots,
        "calibration_digest": (
            f"local-readout-{spec.readout.method}-{calibration_shots}"
            if performed and stable
            else None
        ),
        "allowed_for_claim": False,
        "claim_status": "calibration_record_only" if performed and stable else "unsupported_for_claim" if performed else "not_requested",
        "energy_replaces_primary": False,
    }


def _zne_metadata(spec: MitigationSpec) -> dict[str, object]:
    performed = bool(spec.zne.enabled and spec.zne.method.strip().lower() not in {"none", "placeholder"})
    scale_factors = [float(value) for value in spec.zne.scale_factors]
    monotone = all(scale_factors[index] < scale_factors[index + 1] for index in range(len(scale_factors) - 1))
    status = "passed" if performed and monotone and len(scale_factors) >= 2 else "invalid_scale_factors" if performed else "not_requested"
    return {
        "requested": spec.zne.enabled,
        "performed": performed and status == "passed",
        "status": status,
        "method": spec.zne.method,
        "folding": spec.zne.folding,
        "scale_factors": scale_factors,
        "extrapolator": spec.zne.extrapolator,
        "zne_curve": [
            {
                "scale_factor": factor,
                "energy_estimate_hartree": None,
                "energy_evaluation_status": "not_evaluated",
            }
            for factor in scale_factors
        ] if performed and status == "passed" else [],
        "variance_inflation": float(max(scale_factors) ** 2) if performed and scale_factors else None,
        "allowed_for_claim": False,
        "claim_status": "schedule_only" if performed and status == "passed" else "unsupported_for_claim" if performed else "not_requested",
        "energy_replaces_primary": False,
    }


def _pec_calibration_model_audit(calibration_model: str | None) -> dict[str, object]:
    if not calibration_model:
        return {
            "provided": False,
            "exists": False,
            "executable": False,
            "status": "missing_calibration_model",
            "digest": None,
            "schema": None,
            "calibrated_operation_count": 0,
            "quasi_probability_entry_count": 0,
            "max_operation_l1_overhead": None,
        }

    path = Path(calibration_model).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists() or not path.is_file():
        return {
            "provided": True,
            "exists": False,
            "executable": False,
            "status": "calibration_model_not_found",
            "digest": None,
            "schema": None,
            "calibrated_operation_count": 0,
            "quasi_probability_entry_count": 0,
            "max_operation_l1_overhead": None,
        }

    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if path.suffix.lower() != ".json":
        return {
            "provided": True,
            "exists": True,
            "executable": False,
            "status": "unsupported_calibration_model_format",
            "digest": digest,
            "schema": None,
            "calibrated_operation_count": 0,
            "quasi_probability_entry_count": 0,
            "max_operation_l1_overhead": None,
        }

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "provided": True,
            "exists": True,
            "executable": False,
            "status": "invalid_calibration_model_json",
            "digest": digest,
            "schema": None,
            "calibrated_operation_count": 0,
            "quasi_probability_entry_count": 0,
            "max_operation_l1_overhead": None,
        }
    if not isinstance(payload, dict):
        return {
            "provided": True,
            "exists": True,
            "executable": False,
            "status": "invalid_calibration_model_payload",
            "digest": digest,
            "schema": None,
            "calibrated_operation_count": 0,
            "quasi_probability_entry_count": 0,
            "max_operation_l1_overhead": None,
        }

    schema = payload.get("schema")
    calibrated_operations = payload.get("calibrated_operations") or payload.get("quasi_probabilities")
    calibrated_operation_count = 0
    quasi_probability_entry_count = 0
    max_operation_l1_overhead = None
    if isinstance(calibrated_operations, list):
        calibrated_operation_count = len(calibrated_operations)
        operation_overheads: list[float] = []
        for item in calibrated_operations:
            if not isinstance(item, dict):
                continue
            entries = item.get("quasi_probabilities")
            if not isinstance(entries, list):
                continue
            quasi_probability_entry_count += len(entries)
            coefficient_l1 = 0.0
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                try:
                    coefficient_l1 += abs(float(entry.get("coefficient", 0.0)))
                except (TypeError, ValueError):
                    continue
            if coefficient_l1 > 0.0:
                operation_overheads.append(coefficient_l1)
        if operation_overheads:
            max_operation_l1_overhead = float(max(operation_overheads))
    elif isinstance(calibrated_operations, dict):
        calibrated_operation_count = len(calibrated_operations)
        quasi_probability_entry_count = sum(
            len(value) for value in calibrated_operations.values() if isinstance(value, list)
        )
    executable = bool(
        schema == "qcchem.pec_calibration_model.v1"
        and payload.get("executable") is True
        and calibrated_operations
    )
    return {
        "provided": True,
        "exists": True,
        "executable": executable,
        "status": "executable_calibration_model" if executable else "calibration_model_not_executable",
        "digest": digest,
        "schema": schema,
        "calibrated_operation_count": calibrated_operation_count,
        "quasi_probability_entry_count": quasi_probability_entry_count,
        "max_operation_l1_overhead": max_operation_l1_overhead,
    }


def _pec_metadata(spec: MitigationSpec) -> dict[str, object]:
    model_audit = _pec_calibration_model_audit(spec.pec.calibration_model)
    performed = bool(spec.pec.enabled and model_audit["executable"])
    overhead = (
        float(spec.pec.max_overhead)
        if spec.pec.max_overhead is not None
        else 0.0
        if not spec.pec.enabled
        else None
    )
    status = (
        "executable_calibration_model_recorded"
        if performed
        else str(model_audit["status"])
        if spec.pec.enabled
        else "not_requested"
    )
    return {
        "requested": spec.pec.enabled,
        "performed": performed,
        "status": status,
        "method": spec.pec.method,
        "calibration_model": spec.pec.calibration_model,
        "calibration_model_audit": model_audit,
        "executable_calibration_model": bool(model_audit["executable"]),
        "sampling_overhead": overhead,
        "allowed_for_claim": performed,
        "claim_status": "claim_limited" if performed else "unsupported_for_claim" if spec.pec.enabled else "not_requested",
        "claim_scope": "calibration_overhead_only" if performed else None,
        "energy_replaces_primary": False,
    }


def build_mitigation_summary(spec: MitigationSpec) -> MitigationSummary:
    """Build structured mitigation metadata even when mitigation is not yet applied."""
    symmetry = _symmetry_check_metadata(spec)
    readout = _readout_metadata(spec)
    zne = _zne_metadata(spec)
    pec = _pec_metadata(spec)
    applied = []
    for label, payload in (
        ("symmetry_check", symmetry),
        ("readout_mitigation", readout),
        ("zne", zne),
        ("pec", pec),
    ):
        if payload.get("performed"):
            applied.append(label)
    requested = [
        label
        for label, payload in (
            ("symmetry_check", symmetry),
            ("readout_mitigation", readout),
            ("zne", zne),
            ("pec", pec),
        )
        if payload.get("effective_requested", payload.get("requested"))
    ]
    claim_allowed = [
        label
        for label, payload in (
            ("symmetry_check", symmetry),
            ("readout_mitigation", readout),
            ("zne", zne),
            ("pec", pec),
        )
        if payload.get("allowed_for_claim")
    ]
    claim_disallowed = [label for label in requested if label not in set(claim_allowed)]
    if not requested:
        claim_status = "not_requested"
    elif claim_allowed:
        claim_status = "claim_limited"
    else:
        claim_status = "unsupported_for_claim"
    return MitigationSummary(
        symmetry_check=symmetry,
        readout_mitigation=readout,
        zne=zne,
        pec=pec,
        requested_methods=requested,
        applied_methods=applied,
        claim_allowed_methods=claim_allowed,
        claim_disallowed_methods=claim_disallowed,
        claim_status=claim_status,
        trust_gate=claim_status,
        energy_replaces_primary=False,
    )
