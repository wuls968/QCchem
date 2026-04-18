"""Agent-friendly wrappers around QCchem workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.io.agent_config import AgentTaskSpec, load_agent_task_spec
from qcchem.io.config import resolve_user_path
from qcchem.reporting.hardware_campaign import (
    build_hardware_campaign_summary,
    write_hardware_campaign_report,
    write_hardware_campaign_summary,
)
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config
from qcchem.workflow.runtime_collect import collect_runtime_artifact


def run_analysis_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    """Run one AI workspace analysis ticket through the existing agent path."""
    linked_artifacts = ticket.get("linked_artifacts") or []
    if not linked_artifacts:
        raise ValueError("Analysis tickets require at least one linked artifact.")
    summaries = [summarize_agent_target(Path(str(artifact))) for artifact in linked_artifacts]
    result = {
        "task_id": ticket.get("task_id"),
        "status": "completed",
        "delivery_kind": "analysis_note",
        "summaries": summaries,
    }
    if len(summaries) == 1:
        result["summary"] = summaries[0]
    return result


def summarize_agent_target(target: Path) -> dict[str, Any]:
    """Summarize a hardware calibration suite for AI-agent consumption."""
    resolved_target = target.expanduser().resolve()
    if resolved_target.is_dir():
        summary_path = resolved_target / "hardware_calibration_summary.json"
        output_root = resolved_target
    else:
        summary_path = resolved_target
        output_root = resolved_target.parent
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    summary = build_hardware_campaign_summary(payload)
    summary_json = output_root / "hardware_runtime_campaign_summary.json"
    report_markdown = output_root / "hardware_runtime_campaign_report.md"
    write_hardware_campaign_summary(summary, summary_json)
    write_hardware_campaign_report(summary, report_markdown)
    summary["summary_json"] = str(summary_json)
    summary["report_markdown"] = str(report_markdown)
    return summary


def _write_optional_summary_output(
    base_dir: Path,
    relative_or_abs_path: str | None,
    payload: dict[str, Any],
) -> str | None:
    if not relative_or_abs_path:
        return None
    output_path = resolve_user_path(base_dir, relative_or_abs_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(output_path)


def run_agent_task(spec: AgentTaskSpec) -> dict[str, Any]:
    """Execute one agent task against QCchem."""
    base_dir = spec.source_path.parent if spec.source_path is not None else Path.cwd()
    if spec.kind == "runtime_collect":
        artifact_root = resolve_user_path(base_dir, str(spec.inputs["artifact_root"]))
        result = collect_runtime_artifact(artifact_root)
        summary = {
            "task_name": spec.name,
            "task_kind": spec.kind,
            **result,
        }
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "run_config":
        config = resolve_user_path(base_dir, str(spec.inputs["config"]))
        output_dir = spec.inputs.get("output_dir")
        result = run_from_config(
            config,
            output_dir=(resolve_user_path(base_dir, str(output_dir)) if output_dir else None),
        )
        summary = {
            "task_name": spec.name,
            "task_kind": spec.kind,
            "verification_status": result.verification_status,
            "artifact_root": str(result.artifacts.root),
            "total_energy": result.energy.total_energy,
        }
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "benchmark_suite":
        config = resolve_user_path(base_dir, str(spec.inputs["config"]))
        output_dir = spec.inputs.get("output_dir")
        result = run_benchmark_suite_from_config(
            config,
            output_dir=(resolve_user_path(base_dir, str(output_dir)) if output_dir else None),
        )
        if isinstance(result, dict):
            summary = {
                "task_name": spec.name,
                "task_kind": spec.kind,
                "suite_name": result.get("suite_name"),
                "artifact_root": result.get("artifact_root"),
                "total_cases": (result.get("summary") or {}).get("total_cases"),
            }
        else:
            summary = {
                "task_name": spec.name,
                "task_kind": spec.kind,
                "suite_name": result.suite_name,
                "artifact_root": str(result.artifacts.root),
                "total_cases": result.summary.total_cases,
            }
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "hardware_campaign_summary":
        target = resolve_user_path(base_dir, str(spec.inputs["target"]))
        summary = summarize_agent_target(target)
        summary_json_output = spec.outputs.get("summary_json")
        if summary_json_output:
            output_path = resolve_user_path(base_dir, str(summary_json_output))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_hardware_campaign_summary(summary, output_path)
            summary["summary_json"] = str(output_path)
        report_output = spec.outputs.get("report_markdown")
        if report_output:
            output_path = resolve_user_path(base_dir, str(report_output))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_hardware_campaign_report(summary, output_path)
            summary["report_markdown"] = str(output_path)
        return {
            "task_name": spec.name,
            "task_kind": spec.kind,
            **summary,
        }
    raise ValueError(f"Unsupported agent task kind: {spec.kind}")


def run_agent_task_from_config(path: Path) -> dict[str, Any]:
    """Load and execute one agent task file."""
    spec = load_agent_task_spec(path)
    return run_agent_task(spec)
