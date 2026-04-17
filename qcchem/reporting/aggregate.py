"""Aggregate report renderers for study, benchmark, and scan workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qcchem.io.serialization import to_primitive


def _split_items_by_scope(items: list[dict[str, Any]], status_key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exploratory = [item for item in items if item.get(status_key) == "exploratory"]
    validated_like = [item for item in items if item.get(status_key) != "exploratory"]
    return validated_like, exploratory


def render_study_report(result: Any) -> str:
    """Render a study result as Markdown."""
    data = to_primitive(result)
    validated_runs, exploratory_runs = _split_items_by_scope(data["run_records"], "verification_status")
    lines = [
        f"# Study Report: {data['study_name']}",
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
    lines = [
        f"# Benchmark Suite Report: {data['suite_name']}",
        "",
        "> Validated-like and exploratory cases are separated below to avoid mixing benchmark scopes.",
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
    lines = [
        f"# Scan Report: {data['scan_name']}",
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
    lines = [
        "# Hardware Calibration Dashboard",
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
            "| Case | Backend | Runtime Evidence Status | Evidence Tier | Submission Status | Submission Wall Time (s) | Runtime Shots | Achieved Error | Achieved Error Status | Hardware Verified |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for case in cases:
        runtime_evidence_status = case.get("runtime_evidence_status", "none")
        runtime_evidence_tier = case.get("runtime_evidence_tier")
        runtime_submission_status = case.get("runtime_submission_status", runtime_evidence_status)
        runtime_submission_wall_time_seconds = case.get("runtime_submission_wall_time_seconds")
        runtime_shots = case.get("runtime_shots")
        achieved_error = case.get("achieved_error")
        achieved_error_status = case.get("achieved_error_status")
        lines.append(
            f"| {case['name']} | {case.get('backend_name')} | "
            f"{runtime_evidence_status} | {runtime_evidence_tier} | {runtime_submission_status} | "
            f"{runtime_submission_wall_time_seconds} | {runtime_shots} | {achieved_error} | {achieved_error_status} | "
            f"{case['hardware_verified']} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
