"""Hardware runtime campaign summary and report rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.core.evidence import build_hardware_campaign_evidence_summary
from qcchem.io.serialization import to_primitive


def build_hardware_campaign_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build an agent-friendly summary from a hardware calibration suite payload."""
    cases = list(payload.get("cases", []))
    ranked = [case for case in cases if case.get("achieved_error") is not None]
    ranked.sort(key=lambda item: float(item["achieved_error"]))

    best_case = ranked[0] if ranked else None
    worst_case = ranked[-1] if ranked else None
    chemical_accuracy_target = 1.6e-3
    base_summary = {
        "suite_name": payload.get("suite_name"),
        "artifact_root": payload.get("artifact_root"),
        "total_cases": (payload.get("summary") or {}).get("total_cases", len(cases)),
        "runtime_evidence_status_counts": (payload.get("summary") or {}).get(
            "runtime_evidence_status_counts",
            {},
        ),
        "best_case": best_case,
        "worst_case": worst_case,
        "chemical_accuracy_target_hartree": chemical_accuracy_target,
        "best_distance_to_chemical_accuracy": (
            None if best_case is None else float(best_case["achieved_error"]) - chemical_accuracy_target
        ),
        "recommended_case_name": None if best_case is None else best_case.get("name"),
        "cases": cases,
        "summary": payload.get("summary") or {},
    }
    evidence_summary, decision_worthiness = build_hardware_campaign_evidence_summary(base_summary)

    return {
        **base_summary,
        "evidence_summary": to_primitive(evidence_summary),
        "decision_worthiness": decision_worthiness,
    }


def render_hardware_campaign_report(summary: dict[str, Any]) -> str:
    """Render a compact markdown report for the hardware runtime campaign."""
    lines = [
        "# QCchem Hardware Runtime Campaign Report",
        "",
        "## Evidence Summary",
        "",
        f"- suite_name: `{summary.get('suite_name')}`",
        f"- total_cases: `{summary.get('total_cases')}`",
        f"- chemical_accuracy_target_hartree: `{summary.get('chemical_accuracy_target_hartree')}`",
        f"- runtime_evidence_status_counts: `{summary.get('runtime_evidence_status_counts', {})}`",
        f"- trust_tier: `{(summary.get('evidence_summary') or {}).get('trust_tier')}`",
        f"- primary_scientific_claim: `{(summary.get('evidence_summary') or {}).get('primary_scientific_claim')}`",
        f"- recommended_action: `{(summary.get('evidence_summary') or {}).get('recommended_action')}`",
        "",
    ]
    best_case = summary.get("best_case")
    worst_case = summary.get("worst_case")
    if best_case is not None:
        lines.extend(
            [
                "## Best Case",
                "",
                f"- name: `{best_case.get('name')}`",
                f"- achieved_error: `{best_case.get('achieved_error')}`",
                f"- meets_chemical_accuracy: `{best_case.get('meets_chemical_accuracy')}`",
                "",
            ]
        )
    if worst_case is not None:
        lines.extend(
            [
                "## Worst Case",
                "",
                f"- name: `{worst_case.get('name')}`",
                f"- achieved_error: `{worst_case.get('achieved_error')}`",
                f"- meets_chemical_accuracy: `{worst_case.get('meets_chemical_accuracy')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision Worthiness",
            "",
            f"- recommended_action: `{(summary.get('decision_worthiness') or {}).get('recommended_action')}`",
            f"- why: `{(summary.get('decision_worthiness') or {}).get('why', [])}`",
            "",
            "## Cases",
            "",
            "| Name | Achieved Error | Meets Chemical Accuracy |",
            "| --- | --- | --- |",
        ]
    )
    for case in summary.get("cases", []):
        lines.append(
            f"| {case.get('name')} | {case.get('achieved_error')} | {case.get('meets_chemical_accuracy')} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_hardware_campaign_report(summary: dict[str, Any], output_path: Path) -> None:
    """Write the hardware runtime campaign report."""
    output_path.write_text(render_hardware_campaign_report(summary), encoding="utf-8")


def write_hardware_campaign_summary(summary: dict[str, Any], output_path: Path) -> None:
    """Write the machine-readable hardware campaign summary."""
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
