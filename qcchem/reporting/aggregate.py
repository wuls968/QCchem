"""Aggregate report renderers for study, benchmark, and scan workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qcchem.core.chemical_accuracy import CHEMICAL_ACCURACY_HARTREE
from qcchem.io.serialization import to_primitive


def _split_items_by_scope(items: list[dict[str, Any]], status_key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exploratory = [item for item in items if item.get(status_key) == "exploratory"]
    validated_like = [item for item in items if item.get(status_key) != "exploratory"]
    return validated_like, exploratory


def _distance_to_chemical_accuracy(value: Any, *, target: float = CHEMICAL_ACCURACY_HARTREE) -> float | None:
    if value is None:
        return None
    return max(float(value) - float(target), 0.0)


def _benchmark_case_error(case: dict[str, Any]) -> float | None:
    absolute_error = case.get("absolute_error")
    if absolute_error is not None:
        return float(absolute_error)
    metrics = case.get("metrics") or {}
    achieved_error = metrics.get("achieved_error")
    if achieved_error is not None:
        return float(achieved_error)
    return None


def _best_benchmark_case(cases: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = [case for case in cases if _benchmark_case_error(case) is not None]
    if not ranked:
        return None
    return min(ranked, key=lambda case: float(_benchmark_case_error(case) or 0.0))


def _best_hardware_case(cases: list[dict[str, Any]]) -> dict[str, Any] | None:
    preferred = [
        case
        for case in cases
        if case.get("achieved_error") is not None
        and str(case.get("runtime_evidence_status") or "").lower() in {"retrieved", "retrieved_result"}
    ]
    if preferred:
        return min(preferred, key=lambda case: float(case.get("achieved_error") or 0.0))
    ranked = [case for case in cases if case.get("achieved_error") is not None]
    if not ranked:
        return None
    return min(ranked, key=lambda case: float(case.get("achieved_error") or 0.0))


def render_study_report(result: Any) -> str:
    """Render a study result as Markdown."""
    data = to_primitive(result)
    validated_runs, exploratory_runs = _split_items_by_scope(data["run_records"], "verification_status")
    evidence = data.get("evidence_summary") or {}
    lines = [
        f"# Study Report: {data['study_name']}",
        "",
        "## Best Evidence",
        "",
        f"- primary_scientific_claim: `{evidence.get('primary_scientific_claim')}`",
        f"- trust_tier: `{evidence.get('trust_tier')}`",
        f"- recommended_action: `{evidence.get('recommended_action')}`",
        "",
        "## Report Cover",
        "",
        "> Study reports now open with a concise editorial frame so the run inventory reads like a research companion instead of a registry dump.",
        "",
        f"- total_runs: `{data['summary']['total_runs']}`",
        f"- comparison_axes: `{data['summary']['comparison_axes']}`",
        f"- validated_like_runs: `{len(validated_runs)}`",
        f"- exploratory_runs: `{len(exploratory_runs)}`",
        "",
        "## Study Summary",
        "",
        f"- total_runs: `{data['summary']['total_runs']}`",
        f"- status_counts: `{data['summary']['status_counts']}`",
        f"- comparison_axes: `{data['summary']['comparison_axes']}`",
        f"- validated_like_runs: `{len(validated_runs)}`",
        f"- exploratory_runs: `{len(exploratory_runs)}`",
        "",
        "## Validated-Like Runs",
        "",
    ]
    for item in validated_runs:
        lines.append(
            f"- `{item['name']}` | status=`{item['verification_status']}` | "
            f"backend=`{item['backend_kind']}` | mapping=`{item['mapping_kind']}` | "
            f"total_energy=`{item['total_energy']}`"
        )
    if exploratory_runs:
        lines.extend(["", "## Exploratory Runs", ""])
        for item in exploratory_runs:
            lines.append(
                f"- `{item['name']}` | status=`{item['verification_status']}` | "
                f"backend=`{item['backend_kind']}` | mapping=`{item['mapping_kind']}` | "
                f"total_energy=`{item['total_energy']}`"
            )
    lines.append("")
    return "\n".join(lines)


def render_benchmark_report(result: Any) -> str:
    """Render a benchmark-suite result as Markdown."""
    data = to_primitive(result)
    validated_cases, exploratory_cases = _split_items_by_scope(data["cases"], "status")
    evidence = data.get("evidence_summary") or {}
    best_case = _best_benchmark_case(validated_cases or data["cases"])
    best_case_error = None if best_case is None else _benchmark_case_error(best_case)
    best_case_distance = _distance_to_chemical_accuracy(best_case_error)
    lines = [
        f"# Benchmark Suite Report: {data['suite_name']}",
        "",
        "> Validated-like and exploratory cases are separated below to avoid mixing benchmark scopes.",
        "",
        "## Best Evidence",
        "",
        f"- primary_scientific_claim: `{evidence.get('primary_scientific_claim')}`",
        f"- trust_tier: `{evidence.get('trust_tier')}`",
        f"- recommended_action: `{evidence.get('recommended_action')}`",
        "",
        "## Report Cover",
        "",
        f"- total_cases: `{data['summary']['total_cases']}`",
        f"- validated_like_cases: `{len(validated_cases)}`",
        f"- exploratory_cases: `{len(exploratory_cases)}`",
        f"- chemical_accuracy_target_hartree: `{CHEMICAL_ACCURACY_HARTREE}`",
        f"- dashboard_summary: `{data.get('dashboard_summary', {})}`",
        "",
        "## Best Case",
        "",
        f"- case: `{None if best_case is None else best_case.get('name')}`",
        f"- status: `{None if best_case is None else best_case.get('status')}`",
        f"- absolute_error: `{best_case_error}`",
        f"- distance_to_chemical_accuracy: `{best_case_distance}`",
        "",
        "## Benchmark Suite Summary",
        "",
        f"- total_cases: `{data['summary']['total_cases']}`",
        f"- status_counts: `{data['summary']['status_counts']}`",
        f"- calibration_summary: `{data.get('calibration_summary', {})}`",
        f"- dashboard_summary: `{data.get('dashboard_summary', {})}`",
        f"- validated_like_cases: `{len(validated_cases)}`",
        f"- exploratory_cases: `{len(exploratory_cases)}`",
        "",
        "## Validated-Like Cases",
        "",
    ]
    for item in validated_cases:
        metrics = item.get("metrics", {})
        lines.append(
            f"- `{item['name']}` | kind=`{item['kind']}` | status=`{item['status']}` | "
            f"expected=`{item['expected_status']}` | wall_time=`{metrics.get('wall_time_seconds')}`"
        )
        if metrics.get("compression_method") is not None:
            lines.append(
                f"  compression=`{metrics.get('compression_method')}` "
                f"execution_enabled=`{metrics.get('execution_enabled')}` "
                f"rank=`{metrics.get('compression_rank')}` "
                f"terms=`{metrics.get('compression_pre_term_count')}`->`{metrics.get('compression_post_term_count')}` "
                f"compression_status=`{metrics.get('compression_verification_status')}`"
            )
        if metrics.get("measurement_group_count") is not None:
            lines.append(
                f"  measurement groups=`{metrics.get('measurement_group_count')}` "
                f"estimated_cost=`{metrics.get('estimated_measurement_cost')}` "
                f"measured_cost=`{metrics.get('measured_shot_usage')}` "
                f"achieved_error=`{metrics.get('achieved_error')}` "
                f"hardware_verified=`{metrics.get('hardware_verified')}` "
                f"runtime_service=`{metrics.get('runtime_service')}` "
                f"grouping_policy=`{metrics.get('runtime_grouping_policy')}` "
                f"resilience_level=`{metrics.get('runtime_resilience_level')}`"
            )
        comparison = metrics.get("compressed_vs_uncompressed")
        if comparison is not None:
            lines.append(
                f"  compressed_vs_uncompressed abs_error=`{comparison.get('absolute_error')}` "
                f"relative_error=`{comparison.get('relative_error')}` "
                f"compressed_solve_s=`{comparison.get('compressed_solve_wall_time_seconds')}` "
                f"uncompressed_solve_s=`{comparison.get('uncompressed_solve_wall_time_seconds')}`"
            )
    if exploratory_cases:
        lines.extend(["", "## Exploratory Cases", ""])
        for item in exploratory_cases:
            metrics = item.get("metrics", {})
            lines.append(
                f"- `{item['name']}` | kind=`{item['kind']}` | status=`{item['status']}` | "
                f"expected=`{item['expected_status']}` | wall_time=`{metrics.get('wall_time_seconds')}`"
            )
    lines.append("")
    return "\n".join(lines)


def render_scan_report(result: Any) -> str:
    """Render a scan result as Markdown."""
    data = to_primitive(result)
    validated_points, exploratory_points = _split_items_by_scope(data["points"], "verification_status")
    evidence = data.get("evidence_summary") or {}
    best_point = None
    ranked_points = [point for point in data["points"] if point.get("total_energy") is not None]
    if ranked_points:
        best_point = min(ranked_points, key=lambda point: float(point.get("total_energy") or 0.0))
    lines = [
        f"# Scan Report: {data['scan_name']}",
        "",
        "## Best Evidence",
        "",
        f"- primary_scientific_claim: `{evidence.get('primary_scientific_claim')}`",
        f"- trust_tier: `{evidence.get('trust_tier')}`",
        f"- recommended_action: `{evidence.get('recommended_action')}`",
        "",
        "## Report Cover",
        "",
        f"- parameter_name: `{data['parameter_name']}`",
        f"- validated_like_points: `{len(validated_points)}`",
        f"- exploratory_points: `{len(exploratory_points)}`",
        f"- lowest_energy_point: `{None if best_point is None else best_point.get('point_label')}`",
        "",
        "## Scan Summary",
        "",
        f"- parameter_name: `{data['parameter_name']}`",
        f"- total_points: `{data['summary']['total_runs']}`",
        f"- status_counts: `{data['summary']['status_counts']}`",
        f"- validated_like_points: `{len(validated_points)}`",
        f"- exploratory_points: `{len(exploratory_points)}`",
        "",
        "## Validated-Like Points",
        "",
    ]
    for point in validated_points:
        lines.append(
            f"- `{point['point_label']}` | value=`{point['parameter_value']}` | "
            f"total_energy=`{point['total_energy']}` | status=`{point['verification_status']}`"
        )
    if exploratory_points:
        lines.extend(["", "## Exploratory Points", ""])
        for point in exploratory_points:
            lines.append(
                f"- `{point['point_label']}` | value=`{point['parameter_value']}` | "
                f"total_energy=`{point['total_energy']}` | status=`{point['verification_status']}`"
            )
    lines.append("")
    return "\n".join(lines)


def write_aggregate_report(result: Any, path: Path, *, kind: str) -> None:
    """Write an aggregate report based on kind."""
    if kind == "study":
        content = render_study_report(result)
    elif kind == "benchmark":
        content = render_benchmark_report(result)
    elif kind == "scan":
        content = render_scan_report(result)
    else:
        raise ValueError(f"Unsupported aggregate report kind: {kind}")
    path.write_text(content, encoding="utf-8")


def write_hardware_calibration_report(summary: dict[str, object], output_path: Path) -> None:
    """Write a compact hardware calibration dashboard report."""
    cases = summary.get("cases", [])
    if not isinstance(cases, list):
        cases = []
    best_case = _best_hardware_case(cases)
    evidence = summary.get("evidence_summary") or {}
    decision = summary.get("decision_worthiness") or {}
    best_case_distance = None
    if best_case is not None:
        best_case_distance = best_case.get("distance_to_chemical_accuracy")
        if best_case_distance is None:
            best_case_distance = _distance_to_chemical_accuracy(best_case.get("achieved_error"))
    lines = [
        "# Hardware Calibration Dashboard",
        "",
        "## Best Evidence",
        "",
        f"- primary_scientific_claim: `{evidence.get('primary_scientific_claim')}`",
        f"- trust_tier: `{evidence.get('trust_tier')}`",
        f"- recommended_action: `{evidence.get('recommended_action')}`",
        f"- decision_worthiness: `{decision}`",
        "",
        "## Report Cover",
        "",
        "> Hardware campaign reports foreground the cleanest retrieved evidence first, then preserve the full runtime submission table for auditability.",
        "",
        "## Runtime Submission Evidence",
        "",
    ]
    summary_block = summary.get("summary")
    if isinstance(summary_block, dict):
        lines.extend(
            [
                f"- total_cases: `{summary_block.get('total_cases')}`",
                f"- runtime_evidence_status_counts: `{summary_block.get('runtime_evidence_status_counts')}`",
                f"- hardware_verified_cases: `{summary_block.get('hardware_verified_cases')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Best Case",
            "",
            f"- case: `{None if best_case is None else best_case.get('name')}`",
            f"- backend_name: `{None if best_case is None else best_case.get('backend_name')}`",
            f"- runtime_evidence_status: `{None if best_case is None else best_case.get('runtime_evidence_status')}`",
            f"- achieved_error: `{None if best_case is None else best_case.get('achieved_error')}`",
            f"- meets_chemical_accuracy: `{None if best_case is None else best_case.get('meets_chemical_accuracy')}`",
            f"- distance_to_chemical_accuracy: `{best_case_distance}`",
            "",
        ]
    )
    lines.extend(
        [
            "| Case | Backend | Layout Strategy | Layout | 2Q Gates | Depth | Runtime Evidence Status | Evidence Tier | Submission Status | Submission Wall Time (s) | Runtime Shots | Runtime Usage (s) | Runtime Quantum (s) | Requested Precision | Budget Strategy | Achieved Error | Meets Chem Acc | Distance to Target | Achieved Error Status | Hardware Verified |",
            "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | --- |",
        ]
    )
    for case in cases:
        layout = case.get("selected_layout") or []
        if isinstance(layout, list):
            layout_text = ",".join(str(item) for item in layout)
        else:
            layout_text = str(layout)
        runtime_evidence_status = case.get("runtime_evidence_status", "none")
        runtime_evidence_tier = case.get("runtime_evidence_tier")
        runtime_submission_status = case.get("runtime_submission_status", runtime_evidence_status)
        runtime_submission_wall_time_seconds = case.get("runtime_submission_wall_time_seconds")
        layout_strategy = case.get("layout_strategy")
        transpiled_two_qubit_gate_count = case.get("transpiled_two_qubit_gate_count")
        transpiled_depth = case.get("transpiled_depth")
        runtime_shots = case.get("runtime_shots")
        runtime_usage_seconds = case.get("runtime_usage_seconds")
        runtime_usage_quantum_seconds = case.get("runtime_usage_quantum_seconds")
        requested_precision_target = case.get("requested_precision_target")
        requested_budget_strategy = case.get("requested_budget_strategy")
        achieved_error = case.get("achieved_error")
        meets_chemical_accuracy = case.get("meets_chemical_accuracy")
        distance_to_chemical_accuracy = case.get("distance_to_chemical_accuracy")
        achieved_error_status = case.get("achieved_error_status")
        lines.append(
            f"| {case['name']} | {case.get('backend_name')} | {layout_strategy} | {layout_text} | {transpiled_two_qubit_gate_count} | {transpiled_depth} | "
            f"{runtime_evidence_status} | {runtime_evidence_tier} | {runtime_submission_status} | "
            f"{runtime_submission_wall_time_seconds} | {runtime_shots} | {runtime_usage_seconds} | {runtime_usage_quantum_seconds} | "
            f"{requested_precision_target} | {requested_budget_strategy} | {achieved_error} | {meets_chemical_accuracy} | {distance_to_chemical_accuracy} | {achieved_error_status} | "
            f"{case['hardware_verified']} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
