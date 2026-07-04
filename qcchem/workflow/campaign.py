"""Artifact-driven campaign workflow orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qcchem.core import CampaignEntrySpec, CampaignSpec, RegistryEntry
from qcchem.io.artifact_index import build_artifact_index, build_artifact_index_entry
from qcchem.io.campaign_config import load_campaign_spec
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json
from qcchem.workflow.acceptance import accept_benchmark_result, build_benchmark_acceptance_summary
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.common import prepare_clean_output_root
from qcchem.workflow.registry import make_registry_entry, write_registry
from qcchem.workflow.runner import run_spec
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.study import run_study_from_config

SCHEMA_VERSION = "qcchem.campaign.v0.1-alpha"


def _result_path_for_artifact(path: Path) -> Path:
    if path.is_file():
        return path
    for name in (
        "result.json",
        "benchmark_result.json",
        "study_result.json",
        "scan_result.json",
        "hardware_calibration_summary.json",
        "campaign_result.json",
    ):
        candidate = path / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No supported artifact result JSON found under {path}.")


def _reject_real_runtime_without_confirmation(spec, entry: CampaignEntrySpec) -> None:
    runtime = spec.backend.runtime
    if not runtime.enabled:
        return
    if bool(runtime.options.get("submit_real_job")) and not entry.allow_runtime_submission:
        raise PermissionError(
            f"Campaign entry '{entry.name}' requests a real runtime submission. "
            "Set allow_runtime_submission=true on that entry and use the existing runtime confirmation flow."
        )


def _run_entry(entry: CampaignEntrySpec, campaign_root: Path) -> dict[str, Any]:
    output_dir = entry.output_dir or campaign_root / "entries" / entry.name
    if entry.kind == "artifact":
        if entry.artifact is None:
            raise ValueError(f"Campaign artifact entry '{entry.name}' requires artifact.")
        result_path = _result_path_for_artifact(entry.artifact)
        return {
            "name": entry.name,
            "kind": entry.kind,
            "status": "indexed",
            "artifact_root": str(result_path.parent),
            "result_json": str(result_path),
            "artifact_index_entry": build_artifact_index_entry(result_path),
            "tags": entry.tags,
        }
    if entry.config is None:
        raise ValueError(f"Campaign entry '{entry.name}' requires config.")
    if entry.kind == "run":
        spec = load_run_spec(entry.config)
        _reject_real_runtime_without_confirmation(spec, entry)
        result = run_spec(spec, source_config=str(entry.config), output_dir=output_dir)
        return {
            "name": entry.name,
            "kind": entry.kind,
            "status": result.verification_status,
            "artifact_root": str(result.artifacts.root),
            "result_json": str(result.artifacts.result_json),
            "evidence_summary": to_primitive(result.evidence_summary),
            "artifact_index_entry": result.artifact_index_entry,
            "tags": entry.tags,
        }
    if entry.kind in {"benchmark", "hardware_calibration"}:
        result = run_benchmark_suite_from_config(entry.config, output_dir=output_dir)
        if isinstance(result, dict):
            result_json = Path(result["artifact_root"]) / "hardware_calibration_summary.json"
            status = "hardware_calibration"
            acceptance = {}
            evidence = result.get("evidence_summary")
        else:
            result_json = result.artifacts.result_json
            status = "accepted" if result.acceptance_summary.get("accepted") else "acceptance_failed"
            acceptance = result.acceptance_summary
            evidence = to_primitive(result.evidence_summary)
        return {
            "name": entry.name,
            "kind": entry.kind,
            "status": status,
            "artifact_root": str(result_json.parent),
            "result_json": str(result_json),
            "acceptance_summary": acceptance,
            "evidence_summary": evidence,
            "artifact_index_entry": build_artifact_index_entry(result_json),
            "tags": entry.tags,
        }
    if entry.kind == "study":
        result = run_study_from_config(entry.config, output_dir=output_dir)
        return {
            "name": entry.name,
            "kind": entry.kind,
            "status": "validated" if result.summary.status_counts == {"validated": result.summary.total_runs} else "exploratory",
            "artifact_root": str(result.artifacts.root if result.artifacts else output_dir),
            "result_json": str(result.artifacts.study_result_json if result.artifacts else output_dir / "study_result.json"),
            "evidence_summary": to_primitive(result.evidence_summary),
            "artifact_index_entry": build_artifact_index_entry(result.artifacts.study_result_json),
            "tags": entry.tags,
        }
    if entry.kind == "scan":
        result = run_scan_from_config(entry.config, output_dir=output_dir)
        return {
            "name": entry.name,
            "kind": entry.kind,
            "status": result.summary.status_counts and "exploratory" or "exploratory",
            "artifact_root": str(result.artifacts.root if result.artifacts else output_dir),
            "result_json": str(result.artifacts.result_json if result.artifacts else output_dir / "scan_result.json"),
            "evidence_summary": to_primitive(result.evidence_summary),
            "artifact_index_entry": build_artifact_index_entry(result.artifacts.result_json),
            "tags": entry.tags,
        }
    raise ValueError(f"Unsupported campaign entry kind: {entry.kind}")


def _build_campaign_acceptance(entries: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("kind") == "benchmark" and entry.get("acceptance_summary"):
            acceptance = entry["acceptance_summary"]
            if not acceptance.get("accepted"):
                failures.append(
                    {
                        "entry": entry.get("name"),
                        "reason": "benchmark_acceptance_failed",
                        "blocking_failures": acceptance.get("blocking_failures", []),
                    }
                )
        if not entry.get("evidence_summary") and entry.get("kind") != "artifact":
            warnings.append({"entry": entry.get("name"), "reason": "missing_entry_evidence_summary"})
    accepted = not failures
    return {
        "schema_version": "qcchem.campaign_acceptance.v0.1-alpha",
        "accepted": accepted,
        "blocking_failures": failures,
        "warnings": warnings,
        "recommended_action": "promote_campaign_artifacts" if accepted and not warnings else "review_campaign_warnings" if accepted else "resolve_campaign_acceptance_failures",
    }


def _write_campaign_report(payload: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# QCchem Campaign Report",
        "",
        f"- campaign: `{payload.get('campaign_name')}`",
        f"- status: `{payload.get('status')}`",
        f"- recommended_action: `{(payload.get('acceptance_summary') or {}).get('recommended_action')}`",
        "",
        "## Entries",
        "",
    ]
    for entry in payload.get("entries", []):
        lines.append(
            "- `{name}` kind=`{kind}` status=`{status}` artifact=`{artifact}`".format(
                name=entry.get("name"),
                kind=entry.get("kind"),
                status=entry.get("status"),
                artifact=entry.get("artifact_root"),
            )
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def run_campaign(spec: CampaignSpec, *, overwrite: bool = False) -> dict[str, Any]:
    """Run a campaign and write aggregate artifacts."""

    root = prepare_clean_output_root(spec.output_root, workflow_name="Campaign", overwrite=overwrite)
    entries = [_run_entry(entry, root) for entry in spec.entries]
    acceptance = _build_campaign_acceptance(entries)
    registry_entries: list[RegistryEntry] = [
        make_registry_entry(
            name=str(entry.get("name")),
            kind=f"campaign:{entry.get('kind')}",
            status=str(entry.get("status")),
            artifact_root=Path(str(entry.get("artifact_root"))),
            source=str(entry.get("result_json")),
            tags=list(entry.get("tags") or []),
        )
        for entry in entries
    ]
    status = "accepted" if acceptance["accepted"] else "acceptance_failed"
    registry_entries.append(
        make_registry_entry(
            name=spec.name,
            kind="campaign",
            status=status,
            artifact_root=root,
            source="campaign",
            tags=spec.tags,
        )
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "campaign_name": spec.name,
        "description": spec.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_root": str(root),
        "status": status,
        "entries": entries,
        "campaign_summary": {
            "total_entries": len(entries),
            "accepted": acceptance["accepted"],
            "entry_status_counts": {
                str(entry.get("status")): sum(1 for item in entries if item.get("status") == entry.get("status"))
                for entry in entries
            },
        },
        "acceptance_summary": acceptance,
    }
    result_path = root / "campaign_result.json"
    write_result_json(payload, result_path)
    _write_campaign_report(payload, root / "campaign_report.md")
    write_registry(registry_entries, root / "registry.json")
    artifact_index = build_artifact_index(root)
    write_result_json(artifact_index, root / "artifact_index.json")
    write_result_json(acceptance, root / "acceptance_summary.json")
    payload["artifact_index_entry"] = build_artifact_index_entry(result_path)
    write_result_json(payload, result_path)
    return payload


def run_campaign_from_config(
    config_path: Path,
    *,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    spec = load_campaign_spec(config_path)
    if output_dir is not None:
        spec.output_root = output_dir
    return run_campaign(spec, overwrite=overwrite)


def report_campaign_result(result_json: Path, *, output_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(result_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Campaign result must be a JSON object.")
    _write_campaign_report(payload, output_path or result_json.with_name("campaign_report.md"))
    return payload


def accept_campaign_result(result_json: Path, *, output_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(result_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Campaign result must be a JSON object.")
    entries = list(payload.get("entries") or [])
    acceptance = _build_campaign_acceptance(entries)
    for entry in entries:
        if entry.get("kind") == "benchmark" and not entry.get("acceptance_summary"):
            result_path = entry.get("result_json")
            if result_path:
                benchmark_acceptance = accept_benchmark_result(Path(str(result_path)))
                if not benchmark_acceptance.get("accepted"):
                    acceptance["accepted"] = False
                    acceptance["blocking_failures"].append(
                        {
                            "entry": entry.get("name"),
                            "reason": "benchmark_acceptance_failed",
                            "blocking_failures": benchmark_acceptance.get("blocking_failures", []),
                        }
                    )
    acceptance["recommended_action"] = (
        "promote_campaign_artifacts"
        if acceptance["accepted"] and not acceptance["warnings"]
        else "review_campaign_warnings"
        if acceptance["accepted"]
        else "resolve_campaign_acceptance_failures"
    )
    write_result_json(acceptance, output_path or result_json.with_name("acceptance_summary.json"))
    return acceptance
