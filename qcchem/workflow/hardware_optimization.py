"""Budget-guarded hardware precision optimization workflow."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qcchem.core import HardwareOptimizationSpec, RunResult, RunSpec
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json
from qcchem.workflow.runner import run_spec
from qcchem.workflow.runtime_collect import collect_runtime_artifact

SCHEMA_VERSION = "qcchem.hardware_optimization.v0.1-alpha"
CONFIRMATION_HINT = "I understand IBM Runtime budget"


class HardwareOptimizationBudgetError(RuntimeError):
    """Raised when a hardware optimization submission would exceed its budget."""


@dataclass(slots=True)
class HardwareOptimizationCandidate:
    """One hardware-aware candidate in the H2 precision push."""

    candidate_id: str
    mapping_kind: str
    ansatz_kind: str
    local_accuracy_pass: bool
    qubits: int
    terms: int
    transpiled_two_qubit_gate_count: int | None
    transpiled_depth: int | None
    layout_score: float | None
    local_error_hartree: float | None
    preview_artifact_root: str | None = None
    runtime_artifact_root: str | None = None
    preview_status: str = "previewed"

    @property
    def eligible_for_runtime(self) -> bool:
        """Return whether the candidate may spend real hardware budget."""
        return bool(self.local_accuracy_pass and self.preview_status == "previewed")

    @property
    def selection_score(self) -> list[float | int | str]:
        """Sort key persisted to explain candidate ordering."""
        return [
            0 if self.local_accuracy_pass else 1,
            int(self.qubits),
            int(self.transpiled_two_qubit_gate_count if self.transpiled_two_qubit_gate_count is not None else 1_000_000),
            int(self.transpiled_depth if self.transpiled_depth is not None else 1_000_000),
            float(self.layout_score if self.layout_score is not None else 1.0e9),
            str(self.candidate_id),
        ]


def candidate_to_dict(candidate: HardwareOptimizationCandidate) -> dict[str, Any]:
    """Serialize a candidate with derived runtime-eligibility fields."""
    payload = asdict(candidate)
    payload["eligible_for_runtime"] = candidate.eligible_for_runtime
    payload["selection_score"] = list(candidate.selection_score)
    return payload


def rank_candidates(
    candidates: list[HardwareOptimizationCandidate],
) -> list[HardwareOptimizationCandidate]:
    """Rank candidates by local validity first, then smaller hardware workload."""
    return sorted(candidates, key=lambda item: tuple(item.selection_score))


def build_budget_ledger(
    spec: HardwareOptimizationSpec,
    *,
    submitted_attempts: list[dict[str, Any]],
    strict: bool = False,
) -> dict[str, Any]:
    """Build and optionally validate the hardware optimization budget ledger."""
    submitted = [item for item in submitted_attempts if bool(item.get("submitted"))]
    total_budgeted_shots = int(sum(int(item.get("budgeted_shots") or 0) for item in submitted))
    real_jobs_submitted = len(submitted)
    total_estimated_quantum_seconds = sum(
        float(item.get("estimated_quantum_seconds") or 0.0) for item in submitted
    )
    if strict and real_jobs_submitted > spec.max_real_jobs:
        raise HardwareOptimizationBudgetError(
            f"Hardware optimization exceeds max_real_jobs={spec.max_real_jobs}."
        )
    if strict and total_budgeted_shots > spec.max_total_budgeted_shots:
        raise HardwareOptimizationBudgetError(
            "Hardware optimization exceeds "
            f"max_total_budgeted_shots={spec.max_total_budgeted_shots}."
        )
    if (
        strict
        and spec.max_total_estimated_quantum_seconds is not None
        and total_estimated_quantum_seconds > spec.max_total_estimated_quantum_seconds
    ):
        raise HardwareOptimizationBudgetError(
            "Hardware optimization exceeds "
            f"max_total_estimated_quantum_seconds={spec.max_total_estimated_quantum_seconds}."
        )
    return {
        "real_jobs_submitted": real_jobs_submitted,
        "max_real_jobs": spec.max_real_jobs,
        "total_budgeted_shots": total_budgeted_shots,
        "max_total_budgeted_shots": spec.max_total_budgeted_shots,
        "total_estimated_quantum_seconds": total_estimated_quantum_seconds,
        "max_total_estimated_quantum_seconds": spec.max_total_estimated_quantum_seconds,
        "can_submit_more": (
            real_jobs_submitted < spec.max_real_jobs
            and total_budgeted_shots < spec.max_total_budgeted_shots
            and (
                spec.max_total_estimated_quantum_seconds is None
                or total_estimated_quantum_seconds < spec.max_total_estimated_quantum_seconds
            )
        ),
    }


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_root(spec: RunSpec, output_dir: Path | None) -> Path:
    root = Path(output_dir) if output_dir is not None else spec.run.output_dir
    if not root.is_absolute():
        root = (_project_root() / root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _candidate_config(strategy: str) -> tuple[str, str]:
    normalized = strategy.strip().lower()
    mapping = "parity_two_qubit_reduction" if normalized.startswith("parity_") else "jordan_wigner"
    if "uccsd" in normalized:
        ansatz = "uccsd"
    elif "succd" in normalized:
        ansatz = "succd"
    else:
        ansatz = "puccd"
    return mapping, ansatz


def _candidate_spec(base: RunSpec, strategy: str, *, output_dir: Path, submit: bool, budgeted_shots: int | None = None) -> RunSpec:
    spec = copy.deepcopy(base)
    mapping_kind, ansatz_kind = _candidate_config(strategy)
    spec.mapping.kind = mapping_kind
    spec.solver.ansatz.kind = ansatz_kind
    spec.backend.runtime.enabled = True
    spec.backend.runtime.runtime_ready = True
    spec.backend.runtime.session_ready = True
    spec.backend.runtime.options["submit_real_job"] = bool(submit)
    spec.backend.runtime.options["wait_for_result"] = False
    spec.backend.runtime.options["requires_action_time_confirmation"] = True
    spec.backend.runtime.options.setdefault("layout_strategy", "min_weighted_error")
    spec.backend.runtime.options.setdefault("layout_method", "sabre")
    spec.backend.runtime.options.setdefault("routing_method", "sabre")
    spec.backend.runtime.options.setdefault("optimization_level", 3)
    if budgeted_shots is not None:
        spec.backend.runtime.max_budgeted_shots = int(budgeted_shots)
        spec.backend.runtime.options["default_shots"] = int(budgeted_shots)
    spec.run.output_dir = output_dir
    spec.run.overwrite = not submit
    return spec


def _fallback_transpile_metrics(result: RunResult) -> tuple[int, int]:
    parameter_count = 0
    if result.variational_result is not None:
        parameter_count = int(result.variational_result.parameter_count)
    qubits = max(int(result.mapping.num_qubits), 1)
    terms = max(int(result.mapping.qubit_term_count), 1)
    two_qubit = max(parameter_count * qubits * 2 + terms, qubits - 1)
    depth = max(two_qubit * 3 + qubits * 5, two_qubit)
    return int(depth), int(two_qubit)


def _candidate_from_result(strategy: str, result: RunResult) -> HardwareOptimizationCandidate:
    runtime_submission = result.runtime_submission
    depth, two_qubit = _fallback_transpile_metrics(result)
    layout_score = None
    if runtime_submission is not None:
        if runtime_submission.transpiled_depth is not None:
            depth = int(runtime_submission.transpiled_depth)
        if runtime_submission.transpiled_two_qubit_gate_count is not None:
            two_qubit = int(runtime_submission.transpiled_two_qubit_gate_count)
        layout_score = runtime_submission.layout_score
    local_error = None
    local_pass = False
    if result.chemical_accuracy is not None and result.chemical_accuracy.available:
        local_error = result.chemical_accuracy.absolute_error_hartree
        local_pass = bool(result.chemical_accuracy.meets_chemical_accuracy)
    return HardwareOptimizationCandidate(
        candidate_id=strategy,
        mapping_kind=result.mapping.kind,
        ansatz_kind=(
            str(result.variational_result.ansatz.get("kind"))
            if result.variational_result is not None
            else "unknown"
        ),
        local_accuracy_pass=local_pass,
        qubits=int(result.mapping.num_qubits),
        terms=int(result.mapping.qubit_term_count),
        transpiled_two_qubit_gate_count=two_qubit,
        transpiled_depth=depth,
        layout_score=layout_score,
        local_error_hartree=local_error,
        preview_artifact_root=str(result.artifacts.root),
    )


def _existing_runtime_attempts(root: Path) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    for result_path in sorted((root / "runtime_jobs").glob("*/result.json")):
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        runtime_submission = payload.get("runtime_submission") or {}
        runtime_options = payload.get("runtime_options") or {}
        hardware_optimization = payload.get("hardware_optimization") or {}
        attempts.append(
            {
                "candidate_id": hardware_optimization.get("candidate_id") or result_path.parent.name,
                "mapping_kind": (payload.get("mapping") or {}).get("kind"),
                "ansatz_kind": ((payload.get("variational_result") or {}).get("ansatz") or {}).get("kind"),
                "artifact_root": str(result_path.parent),
                "budgeted_shots": runtime_options.get("max_budgeted_shots"),
                "estimated_quantum_seconds": (
                    (runtime_submission.get("usage_estimation") or {}).get("quantum_seconds")
                ),
                "backend_name": runtime_submission.get("backend_name"),
                "job_id": runtime_submission.get("job_id"),
                "transpiled_depth": runtime_submission.get("transpiled_depth"),
                "transpiled_two_qubit_gate_count": runtime_submission.get("transpiled_two_qubit_gate_count"),
                "submitted": bool(runtime_submission.get("submitted")),
                "succeeded": bool(runtime_submission.get("succeeded")),
                "runtime_error_hartree": (
                    (payload.get("runtime_chemical_accuracy") or {}).get("absolute_error_hartree")
                ),
                "meets_chemical_accuracy": (
                    (payload.get("runtime_chemical_accuracy") or {}).get("meets_chemical_accuracy")
                ),
            }
        )
    return attempts


def _best_runtime_attempt(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the collected attempt with the smallest runtime-derived error."""
    collected = [
        item for item in attempts if item.get("runtime_error_hartree") is not None
    ]
    if not collected:
        return None
    return min(collected, key=lambda item: float(item.get("runtime_error_hartree") or 1.0e9))


def _best_existing_reference_summary() -> dict[str, Any]:
    """Summarize the strongest pre-existing H2 hardware reference if present."""
    reference_path = _project_root() / "artifacts" / "h2_runtime_hardware_probe_puccd_layout" / "result.json"
    summary: dict[str, Any] = {
        "artifact_root": str(reference_path.parent),
        "available": False,
    }
    if not reference_path.exists():
        return summary
    try:
        payload = json.loads(reference_path.read_text(encoding="utf-8"))
    except Exception as exc:
        summary["load_error"] = f"{type(exc).__name__}: {exc}"
        return summary

    runtime_accuracy = payload.get("runtime_chemical_accuracy") or {}
    runtime_submission = payload.get("runtime_submission") or {}
    summary.update(
        {
            "available": bool(runtime_accuracy.get("available", runtime_submission.get("succeeded"))),
            "candidate_id": "h2_runtime_hardware_probe_puccd_layout",
            "runtime_error_hartree": runtime_accuracy.get("absolute_error_hartree"),
            "meets_chemical_accuracy": runtime_accuracy.get("meets_chemical_accuracy"),
            "backend_name": runtime_submission.get("backend_name"),
            "job_id": runtime_submission.get("job_id"),
            "transpiled_depth": runtime_submission.get("transpiled_depth"),
            "transpiled_two_qubit_gate_count": runtime_submission.get("transpiled_two_qubit_gate_count"),
        }
    )
    return summary


def _hardware_recommendation(stop_reason: str) -> str:
    """Map an optimization stop reason to a conservative next action."""
    mapping = {
        "chemical_accuracy_reached": "stop_and_promote_result",
        "stop_threshold_reached": "stop_and_review_result",
        "budget_cap_reached": "pause_budget_exhausted",
        "waiting_for_runtime_collect": "collect_pending_runtime_job",
        "preview_only": "review_ranked_candidates_before_submission",
        "high_shot_refinement_recommended": "consider_one_high_shot_refinement",
        "strategy_comparison_recommended": "submit_one_diverse_strategy_probe_if_budget_allows",
        "pause_after_diverse_strategy_probe": "pause_hardware_spend_and_analyze_bias",
        "no_runtime_eligible_candidates": "improve_local_candidate_before_runtime",
    }
    return mapping.get(stop_reason, "review_runtime_gap")


def _stop_reason(
    *,
    mode: str,
    optimization_spec: HardwareOptimizationSpec,
    attempts: list[dict[str, Any]],
    ledger: dict[str, Any],
) -> str:
    collected_errors = [
        float(item["runtime_error_hartree"])
        for item in attempts
        if item.get("runtime_error_hartree") is not None
    ]
    if any(bool(item.get("meets_chemical_accuracy")) for item in attempts):
        return "chemical_accuracy_reached"
    if collected_errors and min(collected_errors) <= optimization_spec.stop_if_error_below:
        return "stop_threshold_reached"
    if not ledger.get("can_submit_more", False):
        return "budget_cap_reached"
    if any(item.get("submitted") and not item.get("succeeded") for item in attempts):
        return "waiting_for_runtime_collect"
    if mode == "preview":
        return "preview_only"
    if collected_errors:
        best_error = min(collected_errors)
        collected_mappings = {
            str(item.get("mapping_kind"))
            for item in attempts
            if item.get("runtime_error_hartree") is not None and item.get("mapping_kind")
        }
        if best_error <= 1.0e-2:
            return "high_shot_refinement_recommended"
        if len(collected_mappings) >= 2:
            return "pause_after_diverse_strategy_probe"
        return "strategy_comparison_recommended"
    return "continue_collecting_runtime_evidence"


def _write_report(plan: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# QCchem Hardware Optimization Report",
        "",
        "## Optimization Trial",
        "",
        f"- profile: `{plan.get('profile')}`",
        f"- mode: `{plan.get('mode')}`",
        f"- stop_reason: `{plan.get('stop_reason')}`",
        f"- recommended_action: `{plan.get('recommended_action')}`",
        f"- best_existing_reference: `{plan.get('best_existing_reference')}`",
        "",
        "## Hardware Evidence Snapshot",
        "",
    ]
    empirical_best = plan.get("empirical_best_attempt") or {}
    reference = plan.get("best_existing_reference_summary") or {}
    if empirical_best:
        lines.append(
            "- empirical_best_attempt: `{candidate}` error=`{error}` Ha meets_chemical_accuracy=`{meets}`".format(
                candidate=empirical_best.get("candidate_id"),
                error=empirical_best.get("runtime_error_hartree"),
                meets=empirical_best.get("meets_chemical_accuracy"),
            )
        )
    else:
        lines.append("- empirical_best_attempt: `not collected yet`")
    if reference:
        lines.append(
            "- best_existing_reference_summary: `{candidate}` error=`{error}` Ha depth=`{depth}` 2Q=`{twoq}`".format(
                candidate=reference.get("candidate_id", "n/a"),
                error=reference.get("runtime_error_hartree"),
                depth=reference.get("transpiled_depth"),
                twoq=reference.get("transpiled_two_qubit_gate_count"),
            )
        )
    if plan.get("runtime_accuracy_delta_vs_best_existing") is not None:
        lines.append(
            "- runtime_accuracy_delta_vs_best_existing: "
            f"`{plan.get('runtime_accuracy_delta_vs_best_existing')}` Ha "
            "(negative means the optimization trial improved the prior hardware reference)"
        )
    lines.append(f"- chemical_accuracy_target: `{plan.get('chemical_accuracy_target_hartree')}` Ha")
    if plan.get("empirical_gap_to_chemical_accuracy_hartree") is not None:
        lines.append(
            "- empirical_gap_to_chemical_accuracy: "
            f"`{plan.get('empirical_gap_to_chemical_accuracy_hartree')}` Ha"
        )
    if plan.get("reference_gap_to_chemical_accuracy_hartree") is not None:
        lines.append(
            "- prior_reference_gap_to_chemical_accuracy: "
            f"`{plan.get('reference_gap_to_chemical_accuracy_hartree')}` Ha"
        )
    lines.extend(
        [
            "",
            "Interpretation: local algorithmic accuracy is validated for the selected H2 workloads, "
            "but the retrieved hardware-derived chemistry estimates remain exploratory until the "
            "runtime error reaches the chemical-accuracy threshold.",
        ]
    )
    lines.extend(
        [
            "",
            "## Runtime Budget Ledger",
            "",
        ]
    )
    for key, value in (plan.get("runtime_budget_ledger") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Ranked Candidates",
            "",
            "| Candidate | Mapping | Ansatz | Local pass | Qubits | Terms | 2Q Gates | Depth | Local error | Runtime eligible |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for candidate in plan.get("ranked_candidates", []):
        lines.append(
            "| {candidate_id} | {mapping_kind} | {ansatz_kind} | {local_accuracy_pass} | "
            "{qubits} | {terms} | {twoq} | {depth} | {error} | {eligible} |".format(
                candidate_id=candidate.get("candidate_id"),
                mapping_kind=candidate.get("mapping_kind"),
                ansatz_kind=candidate.get("ansatz_kind"),
                local_accuracy_pass=candidate.get("local_accuracy_pass"),
                qubits=candidate.get("qubits"),
                terms=candidate.get("terms"),
                twoq=candidate.get("transpiled_two_qubit_gate_count"),
                depth=candidate.get("transpiled_depth"),
                error=candidate.get("local_error_hartree"),
                eligible=candidate.get("eligible_for_runtime"),
            )
        )
    attempts = plan.get("submitted_attempts") or []
    if attempts:
        lines.extend(["", "## Submitted Attempts", ""])
        for attempt in attempts:
            lines.append(
                "- `{candidate}` shots=`{shots}` submitted=`{submitted}` succeeded=`{succeeded}` "
                "runtime_error=`{error}` artifact=`{artifact}`".format(
                    candidate=attempt.get("candidate_id"),
                    shots=attempt.get("budgeted_shots"),
                    submitted=attempt.get("submitted"),
                    succeeded=attempt.get("succeeded"),
                    error=attempt.get("runtime_error_hartree"),
                    artifact=attempt.get("artifact_root"),
                )
            )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_plan(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    plan_path = root / "hardware_optimization_plan.json"
    report_path = root / "hardware_optimization_report.md"
    campaign_path = root / "hardware_optimization_campaign_summary.json"
    write_result_json(plan, plan_path)
    _write_report(plan, report_path)
    campaign = {
        "schema_version": SCHEMA_VERSION,
        "suite_name": plan.get("suite_name"),
        "hardware_optimization": plan,
        "cases": [
            {
                "name": item.get("candidate_id"),
                "achieved_error": item.get("runtime_error_hartree"),
                "meets_chemical_accuracy": item.get("meets_chemical_accuracy"),
                "runtime_evidence_status": "retrieved_result" if item.get("succeeded") else "submitted",
                "hardware_verified": bool(item.get("succeeded")),
                "runtime_usage_seconds": item.get("estimated_quantum_seconds"),
                "backend_name": item.get("backend_name"),
                "job_id": item.get("job_id"),
                "mapping_kind": item.get("mapping_kind"),
                "ansatz_kind": item.get("ansatz_kind"),
                "transpiled_depth": item.get("transpiled_depth"),
                "transpiled_two_qubit_gate_count": item.get("transpiled_two_qubit_gate_count"),
            }
            for item in plan.get("submitted_attempts", [])
        ],
        "summary": {
            "total_cases": len(plan.get("submitted_attempts", [])),
            "hardware_verified_cases": [
                item.get("candidate_id")
                for item in plan.get("submitted_attempts", [])
                if item.get("succeeded")
            ],
        },
    }
    write_result_json(campaign, campaign_path)
    return {
        **plan,
        "plan_json": str(plan_path),
        "report_markdown": str(report_path),
        "campaign_summary_json": str(campaign_path),
    }


def _preview_candidates(spec: RunSpec, root: Path, *, source_config: str) -> list[HardwareOptimizationCandidate]:
    candidates: list[HardwareOptimizationCandidate] = []
    for strategy in spec.hardware_optimization.candidate_strategies:
        preview_dir = root / "candidates" / strategy / "preview"
        candidate_spec = _candidate_spec(
            spec,
            strategy,
            output_dir=preview_dir,
            submit=False,
        )
        result = run_spec(candidate_spec, source_config=source_config, output_dir=preview_dir)
        candidates.append(_candidate_from_result(strategy, result))
    return rank_candidates(candidates)


def _next_submission(
    ranked: list[HardwareOptimizationCandidate],
    attempts: list[dict[str, Any]],
    optimization_spec: HardwareOptimizationSpec,
) -> tuple[HardwareOptimizationCandidate | None, int | None, str | None]:
    ledger = build_budget_ledger(optimization_spec, submitted_attempts=attempts)
    stop = _stop_reason(mode="submit", optimization_spec=optimization_spec, attempts=attempts, ledger=ledger)
    if stop in {"chemical_accuracy_reached", "stop_threshold_reached", "budget_cap_reached", "waiting_for_runtime_collect"}:
        return None, None, stop
    eligible = [item for item in ranked if item.eligible_for_runtime]
    if not eligible:
        return None, None, "no_runtime_eligible_candidates"
    submitted_ids = [str(item.get("candidate_id")) for item in attempts if item.get("submitted")]
    collected_errors = [
        float(item["runtime_error_hartree"])
        for item in attempts
        if item.get("runtime_error_hartree") is not None
    ]
    if len(submitted_ids) == 1 and collected_errors and min(collected_errors) <= 1.0e-2:
        first = next((item for item in eligible if item.candidate_id == submitted_ids[0]), eligible[0])
        return first, 16_384, "high_shot_refinement"
    if collected_errors and min(collected_errors) > 1.0e-2:
        submitted_mappings = {
            str(item.get("mapping_kind"))
            for item in attempts
            if item.get("submitted") and item.get("mapping_kind")
        }
        for candidate in eligible:
            if candidate.candidate_id in submitted_ids:
                continue
            if candidate.mapping_kind not in submitted_mappings:
                return candidate, 8_192, "diverse_mapping_strategy_probe"
        return None, None, "pause_after_systematic_bias"
    for candidate in eligible:
        if candidate.candidate_id not in submitted_ids:
            return candidate, 8_192, "new_strategy_probe"
    return None, None, "all_candidates_already_submitted"


def run_hardware_optimization_from_config(
    config_path: Path,
    *,
    output_dir: Path | None = None,
    mode: str = "preview",
    confirm_runtime_budget: str | None = None,
) -> dict[str, Any]:
    """Run the H2 hardware optimization preview/submit/collect workflow."""
    spec = load_run_spec(config_path)
    if not spec.hardware_optimization.enabled:
        raise ValueError("hardware_optimization.enabled must be true.")
    root = _resolve_root(spec, output_dir)
    if (
        mode == "submit"
        and spec.hardware_optimization.requires_confirmation
        and not confirm_runtime_budget
    ):
        raise PermissionError(
            "Hardware optimization submit requires --confirm-runtime-budget. "
            f"Suggested phrase: {CONFIRMATION_HINT}"
        )
    attempts = _existing_runtime_attempts(root)

    if mode == "collect":
        collect_summaries: list[dict[str, Any]] = []
        for sidecar_path in sorted((root / "runtime_jobs").glob("*/runtime_submission.json")):
            try:
                collect_summaries.append(dict(collect_runtime_artifact(sidecar_path.parent)))
            except Exception as exc:  # pragma: no cover - environment dependent
                collect_summaries.append(
                    {
                        "artifact_root": str(sidecar_path.parent),
                        "status": "collect_failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        attempts = _existing_runtime_attempts(root)
    else:
        collect_summaries = []

    ranked = _preview_candidates(spec, root, source_config=str(config_path))

    submitted_result: RunResult | None = None
    submitted_candidate_id: str | None = None
    submit_decision = None
    if mode == "submit":
        candidate, budgeted_shots, submit_decision = _next_submission(
            ranked,
            attempts,
            spec.hardware_optimization,
        )
        if candidate is not None and budgeted_shots is not None:
            job_index = len([item for item in attempts if item.get("submitted")]) + 1
            runtime_dir = root / "runtime_jobs" / f"job_{job_index:02d}_{candidate.candidate_id}_{budgeted_shots}"
            submit_spec = _candidate_spec(
                spec,
                candidate.candidate_id,
                output_dir=runtime_dir,
                submit=True,
                budgeted_shots=budgeted_shots,
            )
            submitted_result = run_spec(submit_spec, source_config=str(config_path), output_dir=runtime_dir)
            submitted_candidate_id = candidate.candidate_id
            submitted_payload = to_primitive(submitted_result)
            submitted_payload["hardware_optimization"] = {"candidate_id": submitted_candidate_id}
            write_result_json(submitted_payload, submitted_result.artifacts.result_json)
            attempts = _existing_runtime_attempts(root)
        elif submit_decision is None:
            submit_decision = "no_submission_selected"

    ledger = build_budget_ledger(spec.hardware_optimization, submitted_attempts=attempts)
    stop_reason = submit_decision or _stop_reason(
        mode=mode,
        optimization_spec=spec.hardware_optimization,
        attempts=attempts,
        ledger=ledger,
    )
    best_attempt = _best_runtime_attempt(attempts)
    reference_summary = _best_existing_reference_summary()
    reference_error = reference_summary.get("runtime_error_hartree")
    attempt_error = None if best_attempt is None else best_attempt.get("runtime_error_hartree")
    delta_vs_reference = None
    empirical_gap_to_target = None
    reference_gap_to_target = None
    if attempt_error is not None and reference_error is not None:
        delta_vs_reference = float(attempt_error) - float(reference_error)
    if attempt_error is not None:
        empirical_gap_to_target = float(attempt_error) - float(spec.hardware_optimization.stop_if_error_below)
    if reference_error is not None:
        reference_gap_to_target = float(reference_error) - float(spec.hardware_optimization.stop_if_error_below)
    best_candidate = next((item for item in ranked if item.eligible_for_runtime), ranked[0] if ranked else None)
    plan = {
        "schema_version": SCHEMA_VERSION,
        "suite_name": root.name,
        "profile": spec.hardware_optimization.profile,
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_root": str(root),
        "best_existing_reference": "artifacts/h2_runtime_hardware_probe_puccd_layout",
        "best_existing_reference_summary": reference_summary,
        "ranked_candidates": [candidate_to_dict(item) for item in ranked],
        "submitted_attempts": attempts,
        "collect_summaries": collect_summaries,
        "runtime_budget_ledger": ledger,
        "stop_reason": stop_reason,
        "empirical_best_attempt": best_attempt,
        "runtime_accuracy_delta_vs_best_existing": delta_vs_reference,
        "chemical_accuracy_target_hartree": spec.hardware_optimization.stop_if_error_below,
        "empirical_gap_to_chemical_accuracy_hartree": empirical_gap_to_target,
        "reference_gap_to_chemical_accuracy_hartree": reference_gap_to_target,
        "recommended_action": _hardware_recommendation(stop_reason),
        "hardware_optimization": {
            "candidate_id": None if best_candidate is None else best_candidate.candidate_id,
            "selection_score": None if best_candidate is None else best_candidate.selection_score,
            "local_accuracy_pass": None if best_candidate is None else best_candidate.local_accuracy_pass,
            "transpiled_depth": None if best_candidate is None else best_candidate.transpiled_depth,
            "transpiled_two_qubit_gate_count": (
                None if best_candidate is None else best_candidate.transpiled_two_qubit_gate_count
            ),
            "runtime_budget_ledger": ledger,
            "stop_reason": stop_reason,
            "empirical_best_attempt": best_attempt,
            "best_existing_reference_summary": reference_summary,
            "runtime_accuracy_delta_vs_best_existing": delta_vs_reference,
            "chemical_accuracy_target_hartree": spec.hardware_optimization.stop_if_error_below,
            "empirical_gap_to_chemical_accuracy_hartree": empirical_gap_to_target,
            "reference_gap_to_chemical_accuracy_hartree": reference_gap_to_target,
            "recommended_action": _hardware_recommendation(stop_reason),
        },
    }
    if submitted_result is not None:
        submitted_payload = to_primitive(submitted_result)
        submitted_payload["hardware_optimization"] = {
            "candidate_id": submitted_candidate_id,
            "runtime_budget_ledger": ledger,
            "stop_reason": stop_reason,
        }
        write_result_json(submitted_payload, submitted_result.artifacts.result_json)
    return _write_plan(root, plan)
