"""Evidence-grounded research-agent helpers for QCchem AI workspace."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qcchem.core.ai_workspace import (
    AIModelCallRecord,
    AIProvenanceEvent,
    EvidenceGraphSummary,
    EvidenceSourceRecord,
    ResearchActionProposal,
)
from qcchem.core.chemical_accuracy import CHEMICAL_ACCURACY_HARTREE
from qcchem.core.evidence import summarize_artifact_payload
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json
from qcchem.workflow.ai_assistant import build_openai_client_kwargs

SUPPORTED_ARTIFACT_FILES = {
    "hardware_calibration_summary.json": "hardware_campaign",
    "benchmark_result.json": "benchmark_suite",
    "study_result.json": "study",
    "scan_result.json": "scan",
    "result.json": "run",
    "runtime_submission.json": "runtime_submission",
}

ARTIFACT_FILE_PRIORITY = (
    "hardware_calibration_summary.json",
    "benchmark_result.json",
    "study_result.json",
    "scan_result.json",
    "result.json",
    "runtime_submission.json",
)

LOCAL_ACTION_KINDS = {
    "run_config",
    "benchmark_suite",
    "study",
    "scan",
    "runtime_collect",
    "hardware_optimize_preview",
    "report",
    "compare_artifacts",
    "review_claims",
}

BLOCKED_ACTION_KINDS = {
    "hardware_optimize_submit",
    "hardware_submit",
    "runtime_submit",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _short_hash(value: str) -> str:
    return _sha256_text(value)[:12]


def _resolve_user_path(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def detect_artifact_summary_path(target: Path) -> tuple[str, Path, Path]:
    """Return ``(artifact_kind, summary_path, artifact_root)`` for a supported target."""
    resolved = target.expanduser().resolve()
    if resolved.is_dir():
        for filename in ARTIFACT_FILE_PRIORITY:
            candidate = resolved / filename
            if candidate.exists():
                return SUPPORTED_ARTIFACT_FILES[filename], candidate, resolved
        raise FileNotFoundError(f"No supported QCchem artifact summary found under '{resolved}'.")

    kind = SUPPORTED_ARTIFACT_FILES.get(resolved.name)
    if kind is None:
        raise ValueError(f"Unsupported QCchem artifact summary path: '{resolved}'.")
    return kind, resolved, resolved.parent


def _runtime_sidecar_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    submitted = bool(payload.get("submitted"))
    succeeded = bool(payload.get("succeeded"))
    attempted = bool(payload.get("attempted"))
    runtime_status = "retrieved_result" if submitted and succeeded else "submitted" if submitted else "runtime_attempt" if attempted else "none"
    failure = payload.get("failure_category") or payload.get("failure_message")
    claim = (
        f"Runtime sidecar records job {payload.get('job_id')} with runtime evidence status {runtime_status}."
    )
    if failure:
        claim = f"Runtime sidecar records unresolved runtime attempt: {failure}."
    return {
        "primary_scientific_claim": claim,
        "primary_baseline": {
            "baseline_kind": "runtime_sidecar",
            "baseline_source": payload.get("job_id"),
            "baseline_scope": "runtime_submission",
            "baseline_strength": "weak",
        },
        "primary_error_metric": {
            "metric_kind": "runtime_submission_status",
            "value": runtime_status,
            "units": "status",
        },
        "chemical_accuracy_status": "unavailable",
        "runtime_evidence_status": runtime_status,
        "trust_tier": "hardware_verified" if runtime_status == "retrieved_result" else "exploratory",
        "recommended_action": "review_runtime_gap" if runtime_status == "retrieved_result" else "collect_runtime_result",
    }


def _evidence_from_payload(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    if kind == "runtime_submission":
        return _runtime_sidecar_evidence(payload)
    normalized = summarize_artifact_payload(payload, artifact_kind=kind)
    evidence = normalized.get("evidence_summary")
    if not isinstance(evidence, dict):
        raise ValueError(f"Unable to build evidence summary for artifact kind '{kind}'.")
    return evidence


def _output_links(root: Path) -> dict[str, str]:
    links: dict[str, str] = {}
    for name in (
        "result.json",
        "report.md",
        "benchmark_result.json",
        "benchmark_report.md",
        "study_result.json",
        "study_report.md",
        "scan_result.json",
        "scan_report.md",
        "hardware_calibration_summary.json",
        "hardware_calibration_report.md",
        "runtime_submission.json",
        "artifact_evidence_summary.json",
        "artifact_evidence_report.md",
    ):
        path = root / name
        if path.exists():
            links[name] = str(path)
    return links


def _evidence_warnings(evidence: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    trust_tier = str(evidence.get("trust_tier") or payload.get("verification_status") or "exploratory")
    baseline = evidence.get("primary_baseline") or {}
    chemical_status = str(evidence.get("chemical_accuracy_status") or "unavailable")
    runtime_status = str(evidence.get("runtime_evidence_status") or "none")
    if trust_tier == "exploratory":
        warnings.append("Exploratory evidence cannot be promoted to validated without a stronger baseline gate.")
    if trust_tier == "unstable":
        warnings.append("Unstable evidence requires a stronger baseline before it can support a defended claim.")
    if payload.get("hardware_verified") or trust_tier == "hardware_verified":
        warnings.append("hardware_verified means a runtime result was retrieved; it is not publication-grade chemistry validation.")
    if chemical_status == "not_met":
        warnings.append("Chemical accuracy is not met for this evidence source.")
    if runtime_status in {"submitted", "runtime_attempt"}:
        warnings.append("Runtime evidence is incomplete; collect the runtime result before drawing hardware conclusions.")
    if baseline.get("baseline_strength") in {None, "", "weak"}:
        warnings.append("Primary baseline is weak or missing.")
    return warnings


def load_evidence_source(target: Path, *, workspace_base: Path | None = None) -> EvidenceSourceRecord:
    """Load one supported artifact target into a normalized evidence source record."""
    base = workspace_base or Path.cwd()
    resolved_target = _resolve_user_path(base, target)
    kind, summary_path, root = detect_artifact_summary_path(resolved_target)
    raw_bytes = summary_path.read_bytes()
    payload = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{summary_path} must contain a JSON object.")
    evidence = _evidence_from_payload(kind, payload)
    trust_tier = str(evidence.get("trust_tier") or payload.get("verification_status") or "exploratory")
    runtime_submission = payload.get("runtime_submission") if isinstance(payload.get("runtime_submission"), dict) else {}
    return EvidenceSourceRecord(
        source_id=f"{kind}-{_short_hash(str(summary_path))}",
        artifact_kind=kind,
        artifact_path=str(summary_path),
        artifact_root=str(root),
        path_hash=_sha256_text(str(summary_path)),
        payload_hash=_sha256_bytes(raw_bytes),
        trust_tier=trust_tier,
        verification_status=payload.get("verification_status"),
        primary_scientific_claim=str(evidence.get("primary_scientific_claim") or ""),
        primary_baseline=dict(evidence.get("primary_baseline") or {}),
        primary_error_metric=dict(evidence.get("primary_error_metric") or {}),
        chemical_accuracy_status=str(evidence.get("chemical_accuracy_status") or "unavailable"),
        runtime_evidence_status=str(evidence.get("runtime_evidence_status") or "none"),
        hardware_verified=bool(payload.get("hardware_verified") or trust_tier == "hardware_verified"),
        hardware_evidence_tier=payload.get("hardware_evidence_tier") or runtime_submission.get("hardware_evidence_tier"),
        recommended_action=str(evidence.get("recommended_action") or "review_evidence_boundary"),
        output_links=_output_links(root),
        warnings=_evidence_warnings(evidence, payload),
    )


def load_evidence_sources(
    targets: list[str | Path],
    *,
    workspace_base: Path | None = None,
    max_sources: int = 24,
) -> list[EvidenceSourceRecord]:
    """Load a bounded set of evidence sources from artifact paths."""
    if len(targets) > max_sources:
        raise ValueError(f"Too many evidence sources: {len(targets)} > {max_sources}.")
    return [load_evidence_source(Path(target), workspace_base=workspace_base) for target in targets]


def _chemistry_rank(source: EvidenceSourceRecord) -> tuple[int, float, str]:
    baseline_strength = str(source.primary_baseline.get("baseline_strength") or "weak")
    metric_value = source.primary_error_metric.get("value")
    try:
        error = float(metric_value) if metric_value is not None else float("inf")
    except (TypeError, ValueError):
        error = float("inf")
    score = 0
    if source.trust_tier == "validated":
        score += 80
    if source.chemical_accuracy_status == "met":
        score += 40
    if baseline_strength == "strong":
        score += 20
    elif baseline_strength == "medium":
        score += 10
    if source.trust_tier == "hardware_verified":
        score -= 15
    if source.trust_tier == "exploratory":
        score -= 20
    if source.trust_tier == "unstable":
        score -= 100
    return score, -error, source.source_id


def _runtime_rank(source: EvidenceSourceRecord) -> tuple[int, str]:
    runtime_score = {
        "retrieved_result": 80,
        "submitted": 50,
        "runtime_attempt": 30,
        "none": 0,
    }.get(source.runtime_evidence_status, 0)
    if source.hardware_verified:
        runtime_score += 20
    return runtime_score, source.source_id


def build_evidence_graph(sources: list[EvidenceSourceRecord]) -> EvidenceGraphSummary:
    """Build a compact evidence graph with separate chemistry/runtime judgments."""
    graph_id = f"evidence-{uuid.uuid4().hex[:10]}"
    best_chemistry = max(sources, key=_chemistry_rank, default=None)
    best_runtime = max(sources, key=_runtime_rank, default=None)
    trust_gap: list[str] = []
    open_questions: list[str] = []
    boundary_notes = [
        "LLM output is not authoritative for trust tier, hardware boundary, budget permission, or validated/exploratory promotion."
    ]

    for source in sources:
        for warning in source.warnings:
            if warning not in boundary_notes:
                boundary_notes.append(warning)
        if source.trust_tier == "unstable":
            trust_gap.append(f"{source.source_id}: unstable evidence blocks defended conclusions.")
        if source.trust_tier == "exploratory":
            trust_gap.append(f"{source.source_id}: exploratory evidence needs a stronger baseline.")
        if source.runtime_evidence_status in {"submitted", "runtime_attempt"}:
            open_questions.append(f"{source.source_id}: collect runtime result before hardware conclusions.")
        if source.chemical_accuracy_status in {"not_met", "unavailable"}:
            open_questions.append(f"{source.source_id}: chemical accuracy is {source.chemical_accuracy_status}.")
        baseline_strength = str(source.primary_baseline.get("baseline_strength") or "weak")
        if baseline_strength == "weak":
            open_questions.append(f"{source.source_id}: primary baseline is weak.")

    if any(source.trust_tier == "unstable" for source in sources):
        trust_tier = "unstable"
    elif best_chemistry is not None and best_chemistry.trust_tier == "validated" and best_chemistry.chemical_accuracy_status == "met":
        trust_tier = "validated"
    elif best_runtime is not None and best_runtime.runtime_evidence_status == "retrieved_result":
        trust_tier = "hardware_verified"
    else:
        trust_tier = "exploratory"

    if any(source.recommended_action == "collect_runtime_result" for source in sources):
        recommended_action = "collect_runtime_result"
    elif trust_tier == "validated":
        recommended_action = "promote_validated_result"
    elif trust_tier == "unstable":
        recommended_action = "collect_stronger_baseline"
    elif best_runtime is not None and best_runtime.runtime_evidence_status == "retrieved_result":
        recommended_action = "review_runtime_gap"
    else:
        recommended_action = "compare_against_best_evidence"

    return EvidenceGraphSummary(
        graph_id=graph_id,
        sources=sources,
        best_chemistry_evidence=None if best_chemistry is None else best_chemistry.to_record(),
        best_runtime_evidence=None if best_runtime is None else best_runtime.to_record(),
        trust_tier=trust_tier,
        recommended_action=recommended_action,
        trust_gap=sorted(set(trust_gap)),
        open_questions=sorted(set(open_questions)),
        boundary_notes=boundary_notes,
    )


def summarize_evidence_artifacts(
    artifacts: list[str | Path],
    *,
    workspace_base: Path | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe evidence graph summary for the requested artifacts."""
    sources = load_evidence_sources(artifacts, workspace_base=workspace_base)
    return build_evidence_graph(sources).to_record()


def _infer_action_kind(task_type: str, request_text: str, linked_artifacts: list[str]) -> str:
    lowered = request_text.lower()
    if task_type == "analysis":
        return "compare_artifacts" if linked_artifacts else "review_claims"
    if "runtime collect" in lowered or "collect runtime" in lowered:
        return "runtime_collect"
    if "hardware" in lowered and "preview" in lowered:
        return "hardware_optimize_preview"
    if "benchmark" in lowered and "config" in lowered:
        return "benchmark_suite"
    if "scan" in lowered and "config" in lowered:
        return "scan"
    if "study" in lowered and "config" in lowered:
        return "study"
    if "report" in lowered:
        return "report"
    return "compare_artifacts" if linked_artifacts else "review_claims"


def build_action_proposal(
    *,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
    evidence_graph: dict[str, Any],
    action_kind: str | None = None,
    inputs: dict[str, Any] | None = None,
) -> ResearchActionProposal:
    """Build and locally gate a single research action proposal."""
    selected_kind = (action_kind or _infer_action_kind(task_type, request_text, linked_artifacts)).strip()
    blocked_reason = ""
    allowed = True
    route = "qcchem_agent_protocol" if task_type == "execution" else "analysis_only_assistant"
    if selected_kind in BLOCKED_ACTION_KINDS:
        allowed = False
        blocked_reason = "Real hardware/runtime submission is not allowed by the v1 AI route."
    elif selected_kind not in LOCAL_ACTION_KINDS:
        allowed = False
        blocked_reason = f"Unsupported research action kind: {selected_kind}."

    risk_tier = "high" if selected_kind in {"runtime_collect", "hardware_optimize_preview"} else "standard"
    if evidence_graph.get("trust_tier") in {"unstable", "hardware_verified"}:
        risk_tier = "high"
    return ResearchActionProposal(
        action_id=f"action-{uuid.uuid4().hex[:10]}",
        action_kind=selected_kind,
        title=f"{selected_kind.replace('_', ' ').title()}",
        rationale="Grounded in linked QCchem artifact evidence and local trust/budget rules.",
        inputs=inputs or ({"artifacts": linked_artifacts} if linked_artifacts else {}),
        outputs={},
        requires_confirmation=True,
        risk_tier=risk_tier,
        allowed=allowed,
        blocked_reason=blocked_reason,
        route=route,
    )


def build_cost_estimate(action: dict[str, Any], evidence_graph: dict[str, Any]) -> dict[str, Any]:
    """Return a conservative local cost estimate for a proposed action."""
    action_kind = str(action.get("action_kind") or "")
    if action_kind in {"run_config", "benchmark_suite", "study", "scan"}:
        return {
            "cost_tier": "local_compute",
            "budget_boundary": "Local CPU/simulator execution only unless the target config itself requires runtime gates.",
        }
    if action_kind == "runtime_collect":
        return {
            "cost_tier": "runtime_poll",
            "budget_boundary": "Collects an existing job only; it must not submit a new hardware job.",
        }
    if action_kind == "hardware_optimize_preview":
        return {
            "cost_tier": "local_preview",
            "budget_boundary": "Preview only; real hardware submit is blocked in the v1 AI route.",
        }
    return {
        "cost_tier": "analysis_only",
        "budget_boundary": "No calculation or hardware budget is spent.",
        "evidence_trust_tier": evidence_graph.get("trust_tier"),
    }


def classify_research_risk(action: dict[str, Any], evidence_graph: dict[str, Any]) -> dict[str, Any]:
    """Classify execution risk using local action and evidence rules."""
    reasons: list[str] = []
    action_kind = str(action.get("action_kind") or "")
    if action_kind in {"runtime_collect", "hardware_optimize_preview"}:
        reasons.append(f"{action_kind} touches runtime or hardware-facing workflow state.")
    if action_kind in BLOCKED_ACTION_KINDS or action.get("allowed") is False:
        reasons.append(str(action.get("blocked_reason") or "action is blocked by local policy"))
    if evidence_graph.get("trust_tier") == "unstable":
        reasons.append("Linked evidence includes unstable claims.")
    if evidence_graph.get("trust_tier") == "hardware_verified":
        reasons.append("Best evidence is hardware_verified, which is not the same as chemistry validation.")
    return {
        "is_high_risk": bool(reasons),
        "risk_tier": "high" if reasons else "standard",
        "reasons": reasons,
        "confirm_run": bool(reasons),
        "allowed": action.get("allowed") is not False,
    }


def _fallback_ticket_payload(
    *,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
    evidence_graph: dict[str, Any],
    action_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action = build_action_proposal(
        task_type=task_type,
        request_text=request_text,
        linked_artifacts=linked_artifacts,
        evidence_graph=evidence_graph,
        inputs=action_inputs,
    ).to_record()
    risk = classify_research_risk(action, evidence_graph)
    return {
        "title": "Evidence-Grounded Research Ticket",
        "plan_summary": (
            "Read the linked QCchem artifacts, preserve the trust boundary, and route only the approved local action."
        ),
        "expected_outputs": [
            "evidence_context",
            "reviewable delivery record",
        ],
        "risk_notes": list(risk["reasons"]),
        "boundary_notes": list(evidence_graph.get("boundary_notes") or []),
        "evidence_context": evidence_graph,
        "action_plan": action,
        "risk_assessment": risk,
        "cost_estimate": build_cost_estimate(action, evidence_graph),
    }


def _coerce_model_ticket_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Model ticket payload must be a JSON object.")
    allowed_keys = {
        "title",
        "plan_summary",
        "expected_outputs",
        "risk_notes",
        "boundary_notes",
    }
    payload = {key: value[key] for key in allowed_keys if key in value}
    for key in ("expected_outputs", "risk_notes", "boundary_notes"):
        item = payload.get(key)
        if item is None:
            payload[key] = []
        elif isinstance(item, str):
            payload[key] = [item]
        elif not isinstance(item, list):
            raise ValueError(f"{key} must be a list or string.")
        else:
            payload[key] = [str(entry) for entry in item]
    for key in ("title", "plan_summary"):
        if key in payload:
            payload[key] = str(payload[key]).strip()
    return payload


def draft_ticket_payload_with_optional_model(
    *,
    provider: Any,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
    evidence_graph: dict[str, Any],
    action_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Draft a ticket payload using an optional model, then local deterministic rules."""
    fallback = _fallback_ticket_payload(
        task_type=task_type,
        request_text=request_text,
        linked_artifacts=linked_artifacts,
        evidence_graph=evidence_graph,
        action_inputs=action_inputs,
    )
    request_payload = {
        "task_type": task_type,
        "request_text": request_text,
        "linked_artifacts": linked_artifacts,
        "evidence_graph": evidence_graph,
    }
    request_hash = _sha256_text(json.dumps(request_payload, sort_keys=True))
    model_record = AIModelCallRecord(
        call_id=f"model-{uuid.uuid4().hex[:10]}",
        provider_name=getattr(provider, "provider_name", "") if provider is not None else "",
        provider_kind=getattr(provider, "provider_kind", "") if provider is not None else "",
        model=getattr(provider, "model", "") if provider is not None else "",
        request_hash=request_hash,
        created_at=_now(),
        fallback_used=True,
    )
    if provider is None or not getattr(provider, "enabled", False):
        model_record.status = "not_called"
        fallback["model_provenance"] = [model_record.to_record()]
        return fallback

    try:
        kwargs = build_openai_client_kwargs(provider)
        from openai import OpenAI  # type: ignore

        client = OpenAI(**kwargs)
        response = client.chat.completions.create(
            model=provider.model,
            temperature=provider.default_temperature,
            max_tokens=provider.default_max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Draft a compact QCchem research ticket JSON object. "
                        "Only include title, plan_summary, expected_outputs, risk_notes, boundary_notes. "
                        "Do not change trust tiers or promote exploratory evidence."
                    ),
                },
                {"role": "user", "content": json.dumps(request_payload, sort_keys=True)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        model_payload = _coerce_model_ticket_payload(json.loads(content))
        model_record.response_hash = _sha256_text(content)
        model_record.status = "succeeded"
        model_record.fallback_used = False
        fallback.update(model_payload)
    except Exception as exc:
        model_record.status = "provider_error"
        model_record.error = f"{type(exc).__name__}: {exc}"
        model_record.fallback_used = True
    fallback["model_provenance"] = [model_record.to_record()]
    return fallback


OVERCLAIM_PATTERNS = (
    r"\bvalidated\b",
    r"\bpublication[- ]grade\b",
    r"\bpublishable\b",
    r"\bchemically accurate\b",
    r"\bchemical accuracy\b",
    r"\bvalidated chemistry\b",
)


def review_claims(
    *,
    targets: list[str | Path],
    claim_text: str | None = None,
    workspace_base: Path | None = None,
) -> dict[str, Any]:
    """Review claims against artifact evidence boundaries."""
    graph = summarize_evidence_artifacts(targets, workspace_base=workspace_base)
    findings: list[dict[str, Any]] = []
    claim = claim_text or " ".join(
        str(source.get("primary_scientific_claim") or "") for source in graph.get("sources", [])
    )
    lowered = claim.lower()
    has_promotion_language = any(re.search(pattern, lowered) for pattern in OVERCLAIM_PATTERNS)
    for source in graph.get("sources", []):
        source_id = source.get("source_id")
        trust_tier = source.get("trust_tier")
        chemical_status = source.get("chemical_accuracy_status")
        hardware_verified = bool(source.get("hardware_verified"))
        if trust_tier in {"exploratory", "unstable"} and has_promotion_language:
            findings.append(
                {
                    "finding_id": f"overclaim-{source_id}",
                    "severity": "high",
                    "source_id": source_id,
                    "message": "Promotion language is not supported by exploratory or unstable evidence.",
                    "recommended_fix": "State the result as exploratory/unstable and name the next baseline needed.",
                }
            )
        if hardware_verified and chemical_status != "met" and has_promotion_language:
            findings.append(
                {
                    "finding_id": f"hardware-boundary-{source_id}",
                    "severity": "high",
                    "source_id": source_id,
                    "message": "hardware_verified is runtime retrieval evidence, not publication-grade chemistry validation.",
                    "recommended_fix": "Separate runtime retrieval from chemical-accuracy validation.",
                }
            )
        if chemical_status == "not_met" and "chemical accuracy" in lowered:
            findings.append(
                {
                    "finding_id": f"accuracy-gap-{source_id}",
                    "severity": "medium",
                    "source_id": source_id,
                    "message": "The claim mentions chemical accuracy, but the linked evidence does not meet it.",
                    "recommended_fix": f"Report the gap against {CHEMICAL_ACCURACY_HARTREE} Hartree instead.",
                }
            )
    status = "passed" if not findings else "failed"
    return {
        "schema_version": "qcchem.ai_review.v0.1-alpha",
        "status": status,
        "claim_text": claim,
        "evidence_graph": graph,
        "findings": findings,
    }


def render_review_markdown(payload: dict[str, Any]) -> str:
    """Render deterministic claim-review findings."""
    lines = [
        "# QCchem AI Claim Review",
        "",
        f"- status: `{payload.get('status')}`",
        f"- findings: `{len(payload.get('findings') or [])}`",
        "",
        "## Claim",
        "",
        payload.get("claim_text") or "",
        "",
        "## Findings",
        "",
    ]
    findings = payload.get("findings") or []
    if not findings:
        lines.append("No overclaim findings detected.")
    for finding in findings:
        lines.extend(
            [
                f"### {finding.get('finding_id')}",
                "",
                f"- severity: `{finding.get('severity')}`",
                f"- source_id: `{finding.get('source_id')}`",
                f"- message: {finding.get('message')}",
                f"- recommended_fix: {finding.get('recommended_fix')}",
                "",
            ]
        )
    return "\n".join(lines)


def write_review_outputs(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Write review JSON and Markdown outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "review_findings.json"
    md_path = output_dir / "review_findings.md"
    write_result_json(payload, json_path)
    md_path.write_text(render_review_markdown(payload), encoding="utf-8")
    return {"review_findings_json": str(json_path), "review_findings_markdown": str(md_path)}


def append_ai_provenance_event(
    *,
    workspace_base: Path,
    event_type: str,
    summary: str,
    artifacts: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    actor: str = "qcchem_ai",
) -> dict[str, Any]:
    """Append one JSONL provenance event under the AI workspace."""
    provenance_dir = workspace_base / "artifacts" / "ai_workspace" / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    event = AIProvenanceEvent(
        event_id=f"event-{uuid.uuid4().hex[:12]}",
        timestamp=_now(),
        event_type=event_type,
        actor=actor,
        summary=summary,
        artifacts=list(artifacts or []),
        metadata=to_primitive(metadata or {}),
    )
    path = provenance_dir / "ai_provenance.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_record(), sort_keys=True) + "\n")
    return {**event.to_record(), "provenance_log": str(path)}
