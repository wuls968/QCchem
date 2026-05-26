"""Trust-First claim compiler workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.core.claim import CLAIM_SCHEMA_VERSION, claim_uses_overclaim_language, conservative_safe_rewrite
from qcchem.io.serialization import to_primitive
from qcchem.workflow.evidence_agent import review_claims, summarize_evidence_artifacts


def _support_from_graph(claim: str, graph: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    if findings:
        if any(str(item.get("severity")) == "high" for item in findings) or claim_uses_overclaim_language(claim):
            return "overclaimed"
        return "partially_supported"
    if not graph.get("sources"):
        return "unsupported"
    best = graph.get("best_chemistry_evidence") or {}
    if best.get("trust_tier") == "validated" and best.get("chemical_accuracy_status") == "met":
        return "supported"
    if graph.get("trust_tier") == "validated":
        return "partially_supported"
    return "unsupported" if claim_uses_overclaim_language(claim) else "partially_supported"


def _supported_points(graph: dict[str, Any]) -> list[str]:
    points: list[str] = []
    best = graph.get("best_chemistry_evidence") or {}
    runtime = graph.get("best_runtime_evidence") or {}
    if best:
        points.append(
            "Best chemistry evidence: "
            f"trust_tier={best.get('trust_tier')}, "
            f"chemical_accuracy_status={best.get('chemical_accuracy_status')}."
        )
    if runtime:
        points.append(
            "Best runtime evidence: "
            f"runtime_evidence_status={runtime.get('runtime_evidence_status')}, "
            f"hardware_verified={runtime.get('hardware_verified')}."
        )
    return points


def _required_next_evidence(graph: dict[str, Any], support_level: str) -> list[str]:
    required: list[str] = []
    if support_level in {"unsupported", "overclaimed", "partially_supported"}:
        required.extend(str(item) for item in graph.get("open_questions") or [])
    if support_level == "overclaimed":
        required.append("Show runtime-derived chemical accuracy against the stated baseline before hardware chemistry claims.")
        required.append("Provide a strong exact or accepted benchmark baseline before publication-grade language.")
    if not required:
        required.append("Keep release audit and evidence capsule checks current.")
    return sorted(set(required))


def compile_claim_review(
    *,
    claim_text: str,
    targets: list[str | Path],
    workspace_base: Path | None = None,
) -> dict[str, Any]:
    """Compile one scientific claim against linked artifacts."""
    graph = summarize_evidence_artifacts(targets, workspace_base=workspace_base)
    ai_review = review_claims(targets=targets, claim_text=claim_text, workspace_base=workspace_base)
    findings = [dict(item) for item in ai_review.get("findings") or []]
    support_level = _support_from_graph(claim_text, graph, findings)
    unsupported = list(graph.get("trust_gap") or []) + list(graph.get("open_questions") or [])
    required_next = _required_next_evidence(graph, support_level)
    recommended_action = (
        "rewrite_claim_with_hardware_boundary"
        if support_level == "overclaimed"
        else graph.get("recommended_action") or "review_evidence_boundary"
    )
    return {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "claim_text": claim_text,
        "support_level": support_level,
        "status": "passed" if support_level in {"supported", "partially_supported"} else "failed",
        "evidence_graph": graph,
        "supported_points": _supported_points(graph),
        "unsupported_points": sorted(set(str(item) for item in unsupported)),
        "overclaim_findings": findings,
        "required_next_evidence": required_next,
        "recommended_action": recommended_action,
        "safe_rewrite": conservative_safe_rewrite(claim_text, support_level=support_level),
    }


def render_claim_review_markdown(payload: dict[str, Any]) -> str:
    """Render a claim compiler report."""
    lines = [
        "# QCchem Claim Compiler Review",
        "",
        f"- support_level: `{payload.get('support_level')}`",
        f"- status: `{payload.get('status')}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        "",
        "## Claim",
        "",
        str(payload.get("claim_text") or ""),
        "",
        "## Supported Points",
        "",
    ]
    lines.extend([f"- {item}" for item in payload.get("supported_points") or []] or ["- None"])
    lines.extend(["", "## Unsupported Points", ""])
    lines.extend([f"- {item}" for item in payload.get("unsupported_points") or []] or ["- None"])
    lines.extend(["", "## Overclaim Findings", ""])
    findings = payload.get("overclaim_findings") or []
    if findings:
        for finding in findings:
            lines.append(f"- `{finding.get('finding_id')}`: {finding.get('message')}")
    else:
        lines.append("- None")
    lines.extend(["", "## Required Next Evidence", ""])
    lines.extend([f"- {item}" for item in payload.get("required_next_evidence") or []] or ["- None"])
    lines.extend(["", "## Safe Rewrite", "", str(payload.get("safe_rewrite") or "")])
    return "\n".join(lines) + "\n"


def write_claim_review_outputs(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Write claim review JSON and Markdown outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "claim_review.json"
    md_path = output_dir / "claim_review.md"
    json_path.write_text(json.dumps(to_primitive(payload), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_claim_review_markdown(payload), encoding="utf-8")
    return {"claim_review_json": str(json_path), "claim_review_markdown": str(md_path)}
