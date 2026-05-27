"""Evidence-summary builders shared across QCchem workflows."""

from __future__ import annotations

from typing import Any

from qcchem.core.chemical_accuracy import CHEMICAL_ACCURACY_HARTREE
from qcchem.core.results import BaselineDescriptorSummary, EvidenceSummary
from qcchem.io.serialization import to_primitive


def _normalize_status(value: Any, *, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def chemical_accuracy_status(summary: dict[str, Any] | None) -> str:
    if not isinstance(summary, dict) or not summary.get("available", False):
        return "unavailable"
    continuum = summary.get("continuum_chemistry_accuracy")
    if isinstance(continuum, dict) and continuum.get("status"):
        return str(continuum["status"])
    meets = summary.get("meets_chemical_accuracy")
    if meets is True:
        return "met"
    if meets is False:
        return "not_met"
    return "pending"


def runtime_evidence_status(runtime_submission: dict[str, Any] | None, hardware_evidence_tier: str | None = None) -> str:
    if hardware_evidence_tier:
        return str(hardware_evidence_tier)
    if not isinstance(runtime_submission, dict):
        return "none"
    if runtime_submission.get("submitted") and runtime_submission.get("succeeded"):
        return "retrieved_result"
    if runtime_submission.get("submitted"):
        return "submitted"
    if runtime_submission.get("attempted"):
        return "runtime_attempt"
    return "none"


def build_baseline_descriptor(
    *,
    baseline_kind: str,
    baseline_source: str,
    baseline_scope: str,
    baseline_strength: str,
) -> BaselineDescriptorSummary:
    return BaselineDescriptorSummary(
        baseline_kind=baseline_kind,
        baseline_source=baseline_source,
        baseline_scope=baseline_scope,
        baseline_strength=baseline_strength,
    )


def _recommended_action_for_run(
    *,
    trust_tier: str,
    chemical_status: str,
    runtime_status: str,
    runtime_accuracy_status: str,
) -> str:
    if runtime_status in {"submitted", "runtime_attempt"}:
        return "collect_runtime_result"
    if trust_tier == "unstable":
        return "collect_stronger_baseline"
    if runtime_status == "retrieved_result" and runtime_accuracy_status == "not_met":
        return "review_runtime_gap"
    if trust_tier == "validated" and chemical_status == "met":
        return "promote_validated_result"
    if trust_tier == "validated":
        return "compare_against_best_evidence"
    if trust_tier == "exploratory":
        return "collect_stronger_baseline"
    if trust_tier == "hardware_verified":
        return "worth_one_more_controlled_attempt"
    return "review_evidence_boundary"


def build_run_evidence_summary(payload: dict[str, Any]) -> EvidenceSummary:
    problem = payload.get("problem") or {}
    energy = payload.get("energy") or {}
    benchmark = payload.get("benchmark") or {}
    backend = payload.get("backend") or {}
    mapping = payload.get("mapping") or {}
    runtime_submission = payload.get("runtime_submission") or {}
    measurement = payload.get("measurement") or {}
    field_model = payload.get("field_model") or {}
    calibration = payload.get("calibration") or {}
    reduction = payload.get("reduction_audit") or {}
    compression = payload.get("compression_result") or {}
    perturbative = payload.get("perturbative_correction_result") or {}
    exact = payload.get("exact_baseline") or {}
    chemical = payload.get("chemical_accuracy") or {}
    runtime_chemical = payload.get("runtime_chemical_accuracy") or {}
    verification_status = _normalize_status(payload.get("verification_status"), default="exploratory")
    runtime_status = runtime_evidence_status(runtime_submission, payload.get("hardware_evidence_tier"))
    chem_status = chemical_accuracy_status(chemical)
    runtime_acc_status = chemical_accuracy_status(runtime_chemical)

    baseline_kind = "exact" if exact.get("available") else "none"
    baseline_source = str(exact.get("source") or "exact_diagonalization" if exact.get("available") else "unavailable")
    baseline_strength = "strong" if exact.get("available") else "weak"
    baseline = build_baseline_descriptor(
        baseline_kind=baseline_kind,
        baseline_source=baseline_source,
        baseline_scope="single_run",
        baseline_strength=baseline_strength,
    )
    comparison_target = str(benchmark.get("comparison_target") or "exact diagonalization")
    absolute_error = benchmark.get("absolute_error")
    recommended_action = _recommended_action_for_run(
        trust_tier=verification_status,
        chemical_status=chem_status,
        runtime_status=runtime_status,
        runtime_accuracy_status=runtime_acc_status,
    )
    method_bits = []
    variational = payload.get("variational_result") or {}
    lr_ace_payload = {}
    ansatz_payload = variational.get("ansatz")
    if isinstance(ansatz_payload, dict):
        lr_ace_payload = ansatz_payload.get("lr_ace") or {}
        if not isinstance(lr_ace_payload, dict):
            lr_ace_payload = {}
    lr_ace_gate = lr_ace_payload.get("validation_gate") or {}
    if not isinstance(lr_ace_gate, dict):
        lr_ace_gate = {}
    if variational.get("solver_kind"):
        method_bits.append(str(variational.get("solver_kind")))
    ansatz = variational.get("ansatz")
    if ansatz:
        method_bits.append(str(ansatz))
    if not method_bits and backend.get("kind"):
        method_bits.append(str(backend.get("kind")))
    method_label = " / ".join(method_bits) or "configured workflow"

    primary_claim = (
        f"{problem.get('molecule_name', 'System')} total energy {energy.get('total_energy')} Hartree "
        f"from {method_label} compared against {comparison_target}."
    )
    if field_model.get("model_kind") == "pauli_fierz_cavity_qed":
        primary_claim = (
            f"{problem.get('molecule_name', 'System')} Pauli-Fierz cavity-QED result uses a finite photon cutoff "
            f"and is compared against {comparison_target} within the configured electron-photon Hamiltonian."
        )
    elif field_model.get("model_kind") == "lattice_qed":
        primary_claim = (
            f"{problem.get('molecule_name', 'System')} lattice-QED result is finite-cutoff sparse/exact evidence "
            f"for the configured Hamiltonian; continuum chemistry accuracy is not claimed."
        )
    if chem_status == "met" and not field_model.get("model_kind"):
        primary_claim = (
            f"{problem.get('molecule_name', 'System')} stays within chemical accuracy against {comparison_target} "
            f"for the defended local execution path."
        )
    elif verification_status == "unstable":
        primary_claim = (
            f"{problem.get('molecule_name', 'System')} currently yields an unstable claim against {comparison_target}; "
            "treat this artifact as pressure-test evidence, not a defended result."
        )

    return EvidenceSummary(
        result_identity={
            "artifact_kind": "run",
            "artifact_name": payload.get("run_id"),
            "molecule_name": problem.get("molecule_name"),
            "basis": problem.get("basis"),
            "backend_kind": backend.get("kind"),
            "mapping_kind": mapping.get("kind"),
            "field_model_kind": field_model.get("model_kind"),
        },
        primary_scientific_claim=primary_claim,
        primary_baseline=baseline,
        primary_error_metric={
            "metric_kind": "absolute_error_hartree",
            "value": absolute_error,
            "units": energy.get("energy_units", "Hartree"),
            "threshold": benchmark.get("absolute_error_threshold")
            or chemical.get("threshold_hartree")
            or CHEMICAL_ACCURACY_HARTREE,
            "comparison_target": comparison_target,
        },
        chemical_accuracy_status=chem_status,
        runtime_evidence_status=runtime_status,
        trust_tier=verification_status,
        recommended_action=recommended_action,
        energy_evidence={
            "total_energy": energy.get("total_energy"),
            "electronic_energy": energy.get("electronic_energy"),
            "solver_energy": energy.get("solver_energy"),
            "constant_energy_correction": energy.get("constant_energy_correction"),
            "perturbative_correction": perturbative.get("perturbative_correction"),
        },
        comparison_evidence={
            "comparison_target": comparison_target,
            "absolute_error": absolute_error,
            "relative_error": benchmark.get("relative_error"),
            "statistical_error": benchmark.get("statistical_error"),
            "baseline_strength": baseline.baseline_strength,
            "compressed_vs_uncompressed": benchmark.get("compressed_vs_uncompressed"),
        },
        execution_evidence={
            "wall_time_seconds": (payload.get("provenance") or {}).get("wall_time_seconds"),
            "shots": backend.get("shots"),
            "measurement_strategy": measurement.get("strategy"),
            "measurement_group_count": measurement.get("group_count"),
            "measured_shot_usage": calibration.get("measured_shot_usage"),
            "runtime_backend": runtime_submission.get("backend_name"),
            "runtime_job_id": runtime_submission.get("job_id"),
            "field_model_kind": field_model.get("model_kind"),
        },
        trust_judgment={
            "verification_status": verification_status,
            "module_origin": payload.get("module_origin", "core"),
            "hardware_verified": payload.get("hardware_verified", False),
            "hardware_evidence_tier": payload.get("hardware_evidence_tier"),
            "verification_notes": payload.get("verification_notes", []),
            "scientific_risk_notes": payload.get("scientific_risk_notes", []),
            "lr_ace_trust_label": lr_ace_gate.get("trust_label"),
            "lr_ace_validation_gate": lr_ace_gate or None,
        },
        scientific_accuracy={
            "status": chem_status,
            "assessment_target": chemical.get("assessment_target"),
            "meets_chemical_accuracy": chemical.get("meets_chemical_accuracy"),
            "absolute_error_hartree": chemical.get("absolute_error_hartree"),
            "threshold_hartree": chemical.get("threshold_hartree"),
            "finite_model_exactness": chemical.get("finite_model_exactness"),
            "continuum_chemistry_accuracy": chemical.get("continuum_chemistry_accuracy"),
            "hardware_accuracy": chemical.get("hardware_accuracy"),
        },
        runtime_derived_accuracy={
            "status": runtime_acc_status,
            "assessment_target": runtime_chemical.get("assessment_target"),
            "meets_chemical_accuracy": runtime_chemical.get("meets_chemical_accuracy"),
            "absolute_error_hartree": runtime_chemical.get("absolute_error_hartree"),
            "threshold_hartree": runtime_chemical.get("threshold_hartree"),
        },
        decision_worthiness={
            "recommended_action": recommended_action,
            "blocking_issues": payload.get("scientific_risk_notes", []),
            "why": [
                f"trust_tier={verification_status}",
                f"chemical_accuracy_status={chem_status}",
                f"runtime_evidence_status={runtime_status}",
                f"runtime_accuracy_status={runtime_acc_status}",
            ],
            "reduction_context": {
                "selection_mode": reduction.get("selection_mode"),
                "transformers_applied": reduction.get("transformers_applied"),
            },
            "compression_context": {
                "method": compression.get("method"),
                "verification_status": compression.get("verification_status"),
            },
        },
    )


def _aggregate_trust_tier(status_counts: dict[str, int], *, default: str = "exploratory") -> str:
    if not status_counts:
        return default
    if set(status_counts) == {"validated"}:
        return "validated"
    if "unstable" in status_counts:
        return "unstable"
    if "exploratory" in status_counts:
        return "exploratory"
    return default


def _study_recommended_action(trust_tier: str) -> str:
    if trust_tier == "validated":
        return "promote_validated_result"
    if trust_tier == "unstable":
        return "collect_stronger_baseline"
    return "compare_against_best_evidence"


def build_study_evidence_summary(payload: dict[str, Any]) -> EvidenceSummary:
    runs = list(payload.get("run_records") or [])
    summary = payload.get("summary") or {}
    best_run = None
    ranked_runs = [run for run in runs if run.get("absolute_error") is not None]
    if ranked_runs:
        best_run = min(ranked_runs, key=lambda run: float(run.get("absolute_error") or 0.0))
    elif runs:
        best_run = min(runs, key=lambda run: float(run.get("total_energy") or 0.0))
    trust_tier = _aggregate_trust_tier(summary.get("status_counts") or {})
    recommended_action = _study_recommended_action(trust_tier)
    baseline = build_baseline_descriptor(
        baseline_kind="study_internal_reference",
        baseline_source=(best_run or {}).get("name") or "none",
        baseline_scope="study",
        baseline_strength="medium" if best_run is not None else "weak",
    )
    return EvidenceSummary(
        result_identity={
            "artifact_kind": "study",
            "artifact_name": payload.get("study_name"),
            "description": payload.get("description"),
        },
        primary_scientific_claim=(
            f"Study {payload.get('study_name')} supports a {trust_tier} comparison across "
            f"{summary.get('total_runs', len(runs))} registered runs."
        ),
        primary_baseline=baseline,
        primary_error_metric={
            "metric_kind": "best_run_absolute_error_hartree",
            "value": None if best_run is None else best_run.get("absolute_error"),
            "units": "Hartree",
            "comparison_target": "best available study run",
        },
        chemical_accuracy_status="met" if trust_tier == "validated" else "unavailable",
        runtime_evidence_status="none",
        trust_tier=trust_tier,
        recommended_action=recommended_action,
        comparison_evidence={
            "comparison_axes": summary.get("comparison_axes", []),
            "status_counts": summary.get("status_counts", {}),
            "best_run": None if best_run is None else best_run.get("name"),
        },
        trust_judgment={"verification_status": trust_tier},
        decision_worthiness={
            "recommended_action": recommended_action,
            "why": [f"status_counts={summary.get('status_counts', {})}"],
        },
    )


def build_benchmark_case_evidence_summary(case: dict[str, Any]) -> EvidenceSummary:
    trust_tier = _normalize_status(case.get("status"), default="exploratory")
    recommended_action = (
        "promote_validated_result"
        if trust_tier == "validated"
        else "collect_stronger_baseline" if trust_tier == "unstable" else "compare_against_best_evidence"
    )
    return EvidenceSummary(
        result_identity={"artifact_kind": "benchmark_case", "artifact_name": case.get("name"), "case_kind": case.get("kind")},
        primary_scientific_claim=(
            f"Benchmark case {case.get('name')} is currently classified as {trust_tier} for kind={case.get('kind')}."
        ),
        primary_baseline=build_baseline_descriptor(
            baseline_kind="benchmark_reference",
            baseline_source=str((case.get("metrics") or {}).get("comparison_target") or "configured_reference"),
            baseline_scope="benchmark_case",
            baseline_strength="strong" if trust_tier == "validated" else "medium",
        ),
        primary_error_metric={
            "metric_kind": "absolute_error_hartree",
            "value": case.get("absolute_error"),
            "units": "Hartree",
        },
        chemical_accuracy_status="met" if trust_tier == "validated" and (case.get("absolute_error") or 0.0) <= CHEMICAL_ACCURACY_HARTREE else "not_met",
        runtime_evidence_status=str((case.get("metrics") or {}).get("runtime_evidence_status") or "none"),
        trust_tier=trust_tier,
        recommended_action=recommended_action,
        comparison_evidence={"expected_status": case.get("expected_status"), "metrics": case.get("metrics", {})},
        trust_judgment={"verification_status": trust_tier},
        decision_worthiness={"recommended_action": recommended_action},
    )


def build_benchmark_suite_evidence_summary(payload: dict[str, Any]) -> EvidenceSummary:
    cases = list(payload.get("cases") or [])
    summary = payload.get("summary") or {}
    best_case = min(
        [case for case in cases if case.get("absolute_error") is not None],
        key=lambda case: float(case.get("absolute_error") or 0.0),
        default=None,
    )
    trust_tier = _aggregate_trust_tier(summary.get("status_counts") or {})
    recommended_action = (
        "promote_validated_result"
        if trust_tier == "validated"
        else "compare_against_best_evidence" if trust_tier == "exploratory" else "collect_stronger_baseline"
    )
    return EvidenceSummary(
        result_identity={"artifact_kind": "benchmark_suite", "artifact_name": payload.get("suite_name")},
        primary_scientific_claim=(
            f"Benchmark suite {payload.get('suite_name')} currently defends a {trust_tier} scope across "
            f"{summary.get('total_cases', len(cases))} cases."
        ),
        primary_baseline=build_baseline_descriptor(
            baseline_kind="benchmark_suite_reference",
            baseline_source="best_case",
            baseline_scope="benchmark_suite",
            baseline_strength="strong" if best_case is not None else "weak",
        ),
        primary_error_metric={
            "metric_kind": "best_case_absolute_error_hartree",
            "value": None if best_case is None else best_case.get("absolute_error"),
            "units": "Hartree",
        },
        chemical_accuracy_status="met" if best_case is not None and (best_case.get("absolute_error") or 0.0) <= CHEMICAL_ACCURACY_HARTREE else "not_met",
        runtime_evidence_status="none",
        trust_tier=trust_tier,
        recommended_action=recommended_action,
        comparison_evidence={
            "status_counts": summary.get("status_counts", {}),
            "best_case": None if best_case is None else best_case.get("name"),
        },
        trust_judgment={"verification_status": trust_tier},
        decision_worthiness={"recommended_action": recommended_action},
    )


def build_scan_point_evidence_summary(point: dict[str, Any], *, parameter_name: str) -> EvidenceSummary:
    trust_tier = _normalize_status(point.get("verification_status"), default="exploratory")
    recommended_action = "promote_validated_result" if trust_tier == "validated" else "collect_stronger_baseline"
    return EvidenceSummary(
        result_identity={"artifact_kind": "scan_point", "artifact_name": point.get("point_label"), "parameter_name": parameter_name},
        primary_scientific_claim=(
            f"Scan point {point.get('point_label')} at {point.get('parameter_value')} yields total energy "
            f"{point.get('total_energy')} Hartree."
        ),
        primary_baseline=build_baseline_descriptor(
            baseline_kind="scan_internal_reference",
            baseline_source="scan_path",
            baseline_scope="scan_point",
            baseline_strength="medium",
        ),
        primary_error_metric={"metric_kind": "absolute_error_hartree", "value": point.get("exact_error"), "units": "Hartree"},
        chemical_accuracy_status="met" if point.get("exact_error") is not None and float(point.get("exact_error") or 0.0) <= CHEMICAL_ACCURACY_HARTREE else "unavailable",
        runtime_evidence_status="none",
        trust_tier=trust_tier,
        recommended_action=recommended_action,
        comparison_evidence={"parameter_value": point.get("parameter_value")},
        trust_judgment={"verification_status": trust_tier},
        decision_worthiness={"recommended_action": recommended_action},
    )


def build_scan_evidence_summary(payload: dict[str, Any]) -> EvidenceSummary:
    points = list(payload.get("points") or [])
    summary = payload.get("summary") or {}
    best_point = min(points, key=lambda point: float(point.get("total_energy") or 0.0), default=None)
    trust_tier = _aggregate_trust_tier(summary.get("status_counts") or {})
    recommended_action = "promote_validated_result" if trust_tier == "validated" else "compare_against_best_evidence"
    return EvidenceSummary(
        result_identity={"artifact_kind": "scan", "artifact_name": payload.get("scan_name"), "parameter_name": payload.get("parameter_name")},
        primary_scientific_claim=(
            f"Scan {payload.get('scan_name')} traces {payload.get('parameter_name')} across "
            f"{summary.get('total_runs', len(points))} points with a {trust_tier} sweep."
        ),
        primary_baseline=build_baseline_descriptor(
            baseline_kind="scan_internal_reference",
            baseline_source=None if best_point is None else best_point.get("point_label"),
            baseline_scope="scan",
            baseline_strength="medium" if best_point is not None else "weak",
        ),
        primary_error_metric={
            "metric_kind": "minimum_total_energy_hartree",
            "value": None if best_point is None else best_point.get("total_energy"),
            "units": "Hartree",
        },
        chemical_accuracy_status="met" if trust_tier == "validated" else "unavailable",
        runtime_evidence_status="none",
        trust_tier=trust_tier,
        recommended_action=recommended_action,
        comparison_evidence={
            "status_counts": summary.get("status_counts", {}),
            "best_point": None if best_point is None else best_point.get("point_label"),
        },
        trust_judgment={"verification_status": trust_tier},
        decision_worthiness={"recommended_action": recommended_action},
    )


def build_hardware_campaign_evidence_summary(payload: dict[str, Any]) -> tuple[EvidenceSummary, dict[str, Any]]:
    cases = list(payload.get("cases") or [])
    best_case = min(
        [case for case in cases if case.get("achieved_error") is not None],
        key=lambda case: float(case.get("achieved_error") or 0.0),
        default=None,
    )
    runtime_status = str((best_case or {}).get("runtime_evidence_status") or "none")
    achieved_error = None if best_case is None else best_case.get("achieved_error")
    if best_case is None:
        recommended_action = "pause"
    elif runtime_status in {"submitted", "runtime_attempt"}:
        recommended_action = "continue"
    elif achieved_error is None:
        recommended_action = "pause"
    elif float(achieved_error) <= CHEMICAL_ACCURACY_HARTREE:
        recommended_action = "promote_validated_result"
    elif float(achieved_error) <= 0.02:
        recommended_action = "worth_one_more_controlled_attempt"
    elif float(achieved_error) <= 0.1:
        recommended_action = "pause"
    else:
        recommended_action = "not_worth_additional_budget"
    decision = {
        "recommended_action": recommended_action,
        "best_case_name": None if best_case is None else best_case.get("name"),
        "best_case_achieved_error": achieved_error,
        "best_case_runtime_status": runtime_status,
        "why": [
            f"achieved_error={achieved_error}",
            f"runtime_evidence_status={runtime_status}",
        ],
    }
    summary = EvidenceSummary(
        result_identity={"artifact_kind": "hardware_campaign", "artifact_name": payload.get("suite_name")},
        primary_scientific_claim=(
            f"Hardware campaign {payload.get('suite_name')} currently provides "
            f"{runtime_status or 'no'} runtime-backed evidence, with best achieved error {achieved_error} Hartree."
        ),
        primary_baseline=build_baseline_descriptor(
            baseline_kind="hardware_probe_reference",
            baseline_source=None if best_case is None else best_case.get("name"),
            baseline_scope="hardware_campaign",
            baseline_strength="medium" if runtime_status == "retrieved_result" else "weak",
        ),
        primary_error_metric={
            "metric_kind": "achieved_error_hartree",
            "value": achieved_error,
            "units": "Hartree",
            "threshold": payload.get("chemical_accuracy_target_hartree", CHEMICAL_ACCURACY_HARTREE),
        },
        chemical_accuracy_status=(
            "met"
            if best_case is not None and best_case.get("meets_chemical_accuracy") is True
            else "not_met" if best_case is not None else "unavailable"
        ),
        runtime_evidence_status=runtime_status,
        trust_tier="hardware_verified" if runtime_status == "retrieved_result" else "exploratory",
        recommended_action=recommended_action,
        comparison_evidence={
            "runtime_evidence_status_counts": payload.get("runtime_evidence_status_counts")
            or (payload.get("summary") or {}).get("runtime_evidence_status_counts", {}),
            "best_distance_to_chemical_accuracy": payload.get("best_distance_to_chemical_accuracy"),
        },
        execution_evidence={
            "hardware_verified_cases": (payload.get("summary") or {}).get("hardware_verified_cases", []),
        },
        trust_judgment={
            "verification_status": "hardware_verified" if runtime_status == "retrieved_result" else "exploratory",
            "boundary": "hardware_verified means runtime result retrieved, not chemistry claim validated.",
        },
        runtime_derived_accuracy={
            "status": "met"
            if best_case is not None and best_case.get("meets_chemical_accuracy") is True
            else "not_met" if best_case is not None else "unavailable",
            "absolute_error_hartree": achieved_error,
            "threshold_hartree": payload.get("chemical_accuracy_target_hartree", CHEMICAL_ACCURACY_HARTREE),
        },
        decision_worthiness=decision,
    )
    return summary, decision


def summarize_artifact_payload(payload: dict[str, Any], *, artifact_kind: str | None = None) -> dict[str, Any]:
    normalized = to_primitive(payload)
    detected_kind = artifact_kind or (
        "benchmark_suite" if "suite_name" in normalized and "cases" in normalized and "summary" in normalized and "dashboard_summary" in normalized
        else "hardware_campaign" if "suite_name" in normalized and "cases" in normalized and "summary" in normalized
        and "runtime_evidence_status_counts" in (normalized.get("summary") or {})
        else "study" if "study_name" in normalized
        else "scan" if "scan_name" in normalized
        else "run"
    )
    if detected_kind == "run":
        evidence = build_run_evidence_summary(normalized)
        return {"artifact_kind": "run", "evidence_summary": to_primitive(evidence), "payload": normalized}
    if detected_kind == "study":
        evidence = build_study_evidence_summary(normalized)
        return {"artifact_kind": "study", "evidence_summary": to_primitive(evidence), "payload": normalized}
    if detected_kind == "scan":
        evidence = build_scan_evidence_summary(normalized)
        return {"artifact_kind": "scan", "evidence_summary": to_primitive(evidence), "payload": normalized}
    if detected_kind == "benchmark_suite":
        evidence = build_benchmark_suite_evidence_summary(normalized)
        return {"artifact_kind": "benchmark_suite", "evidence_summary": to_primitive(evidence), "payload": normalized}
    if detected_kind == "hardware_campaign":
        evidence, decision = build_hardware_campaign_evidence_summary(normalized)
        return {
            "artifact_kind": "hardware_campaign",
            "evidence_summary": to_primitive(evidence),
            "decision_worthiness": decision,
            "payload": normalized,
        }
    raise ValueError(f"Unsupported artifact kind for evidence summary: {detected_kind}")
