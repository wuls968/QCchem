"""Agent-friendly wrappers around QCchem workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.io.agent_config import AgentTaskSpec, load_agent_task_spec
from qcchem.io.config import resolve_user_path
from qcchem.io.serialization import to_primitive
from qcchem.reporting.hardware_campaign import (
    build_hardware_campaign_summary,
    write_hardware_campaign_report,
    write_hardware_campaign_summary,
)
from qcchem.reporting import write_markdown_report
from qcchem.reporting.jsonio import write_result_json
from qcchem.core.evidence import summarize_artifact_payload
from qcchem.workflow.evidence_agent import (
    review_claims,
    summarize_evidence_artifacts,
    write_review_outputs,
)
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.hardware_optimization import run_hardware_optimization_from_config
from qcchem.workflow.runner import run_from_config
from qcchem.workflow.runtime_collect import collect_runtime_artifact
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.study import run_study_from_config


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
    """Summarize one QCchem artifact target for AI-agent consumption."""
    resolved_target = target.expanduser().resolve()
    if resolved_target.is_dir():
        candidates = [
            ("hardware_campaign", resolved_target / "hardware_calibration_summary.json"),
            ("benchmark_suite", resolved_target / "benchmark_result.json"),
            ("study", resolved_target / "study_result.json"),
            ("scan", resolved_target / "scan_result.json"),
            ("run", resolved_target / "result.json"),
        ]
        artifact_kind, summary_path = next(
            ((kind, path) for kind, path in candidates if path.exists()),
            (None, None),
        )
        if summary_path is None:
            raise FileNotFoundError(f"No supported QCchem artifact summary found under '{resolved_target}'.")
        output_root = resolved_target
    else:
        summary_path = resolved_target
        output_root = resolved_target.parent
        name = summary_path.name
        artifact_kind = {
            "hardware_calibration_summary.json": "hardware_campaign",
            "benchmark_result.json": "benchmark_suite",
            "study_result.json": "study",
            "scan_result.json": "scan",
            "result.json": "run",
        }.get(name)
        if artifact_kind is None:
            raise ValueError(f"Unsupported artifact summary path: '{summary_path}'.")

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if artifact_kind == "hardware_campaign":
        summary = build_hardware_campaign_summary(payload)
        summary_json = output_root / "hardware_runtime_campaign_summary.json"
        report_markdown = output_root / "hardware_runtime_campaign_report.md"
        write_hardware_campaign_summary(summary, summary_json)
        write_hardware_campaign_report(summary, report_markdown)
        summary["summary_json"] = str(summary_json)
        summary["report_markdown"] = str(report_markdown)
        summary["artifact_kind"] = "hardware_campaign"
        return summary

    normalized = summarize_artifact_payload(payload, artifact_kind=artifact_kind)
    evidence_summary = normalized["evidence_summary"]
    summary = {
        "artifact_kind": artifact_kind,
        "artifact_root": str(output_root),
        "evidence_summary": evidence_summary,
        "summary_title": f"{artifact_kind.replace('_', ' ').title()} Evidence Summary",
    }
    summary_json = output_root / "artifact_evidence_summary.json"
    report_markdown = output_root / "artifact_evidence_report.md"
    write_result_json(summary, summary_json)
    report_lines = [
        f"# {summary['summary_title']}",
        "",
        f"- artifact_kind: `{artifact_kind}`",
        f"- primary_scientific_claim: `{evidence_summary.get('primary_scientific_claim')}`",
        f"- trust_tier: `{evidence_summary.get('trust_tier')}`",
        f"- runtime_evidence_status: `{evidence_summary.get('runtime_evidence_status')}`",
        f"- recommended_action: `{evidence_summary.get('recommended_action')}`",
        f"- baseline: `{evidence_summary.get('primary_baseline')}`",
        f"- primary_error_metric: `{evidence_summary.get('primary_error_metric')}`",
        "",
    ]
    report_markdown.write_text("\n".join(report_lines), encoding="utf-8")
    summary["summary_json"] = str(summary_json)
    summary["report_markdown"] = str(report_markdown)
    return to_primitive(summary)


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
    if spec.kind == "study":
        config = resolve_user_path(base_dir, str(spec.inputs["config"]))
        output_dir = spec.inputs.get("output_dir")
        result = run_study_from_config(
            config,
            output_dir=(resolve_user_path(base_dir, str(output_dir)) if output_dir else None),
        )
        summary = {
            "task_name": spec.name,
            "task_kind": spec.kind,
            "study_name": result.study_name,
            "artifact_root": str(result.artifacts.root) if result.artifacts else None,
            "total_runs": result.summary.total_runs,
        }
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "scan":
        config = resolve_user_path(base_dir, str(spec.inputs["config"]))
        output_dir = spec.inputs.get("output_dir")
        result = run_scan_from_config(
            config,
            output_dir=(resolve_user_path(base_dir, str(output_dir)) if output_dir else None),
        )
        summary = {
            "task_name": spec.name,
            "task_kind": spec.kind,
            "scan_name": result.scan_name,
            "artifact_root": str(result.artifacts.root) if result.artifacts else None,
            "total_runs": result.summary.total_runs,
        }
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "hardware_optimize_preview":
        config = resolve_user_path(base_dir, str(spec.inputs["config"]))
        output_dir = spec.inputs.get("output_dir")
        result = run_hardware_optimization_from_config(
            config,
            output_dir=(resolve_user_path(base_dir, str(output_dir)) if output_dir else None),
            mode="preview",
        )
        summary = {"task_name": spec.name, "task_kind": spec.kind, **result}
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "compare_artifacts":
        artifacts = [str(item) for item in spec.inputs["artifacts"]]
        summary = summarize_evidence_artifacts(artifacts, workspace_base=base_dir)
        summary = {"task_name": spec.name, "task_kind": spec.kind, **summary}
        written_summary = _write_optional_summary_output(base_dir, spec.outputs.get("summary_json"), summary)
        if written_summary is not None:
            summary["summary_json"] = written_summary
        return summary
    if spec.kind == "review_claims":
        targets = [str(item) for item in spec.inputs["targets"]]
        review = review_claims(
            targets=targets,
            claim_text=spec.inputs.get("claim_text"),
            workspace_base=base_dir,
        )
        output_dir_text = spec.outputs.get("output_dir")
        if output_dir_text:
            review.update(write_review_outputs(review, resolve_user_path(base_dir, str(output_dir_text))))
        return {"task_name": spec.name, "task_kind": spec.kind, **review}
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
    if spec.kind == "report":
        result_json = resolve_user_path(base_dir, str(spec.inputs["result_json"]))
        output = resolve_user_path(
            base_dir,
            str(spec.outputs.get("report_markdown") or result_json.with_name("report.md")),
        )
        payload = json.loads(result_json.read_text(encoding="utf-8"))
        output.parent.mkdir(parents=True, exist_ok=True)
        write_markdown_report(payload, output)
        return {
            "task_name": spec.name,
            "task_kind": spec.kind,
            "report_markdown": str(output),
        }
    raise ValueError(f"Unsupported agent task kind: {spec.kind}")


def run_agent_task_from_config(path: Path) -> dict[str, Any]:
    """Load and execute one agent task file."""
    spec = load_agent_task_spec(path)
    return run_agent_task(spec)
