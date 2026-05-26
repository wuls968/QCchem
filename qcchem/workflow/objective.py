"""Research Objective planning and status workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.core.objective import OBJECTIVE_SCHEMA_VERSION, ResearchObjectiveSpec
from qcchem.io.config import resolve_user_path
from qcchem.io.objective_config import load_research_objective
from qcchem.io.serialization import to_primitive
from qcchem.workflow.claim_compiler import compile_claim_review
from qcchem.workflow.evidence_capsule import build_and_write_evidence_capsule
from qcchem.workflow.evidence_agent import summarize_evidence_artifacts


def _base_dir(spec: ResearchObjectiveSpec) -> Path:
    if spec.source_path is None:
        return Path.cwd()
    return spec.source_path.parent


def _resolve(base: Path, path: Path) -> Path:
    return path if path.is_absolute() else resolve_user_path(base, str(path))


def _linked_artifacts(spec: ResearchObjectiveSpec) -> list[Path]:
    base = _base_dir(spec)
    return [_resolve(base, path) for path in spec.linked_artifacts]


def _config_status(spec: ResearchObjectiveSpec) -> tuple[list[dict[str, Any]], list[str]]:
    base = _base_dir(spec)
    graph: list[dict[str, Any]] = []
    missing: list[str] = []
    for config in spec.candidate_configs:
        path = _resolve(base, config)
        exists = path.exists()
        if not exists:
            missing.append(str(config))
        graph.append(
            {
                "node_id": f"config:{config}",
                "kind": "candidate_config",
                "path": str(config),
                "resolved_path": str(path),
                "exists": exists,
                "recommended_command": f"qcchem run -c {config} -o <artifact_root>",
            }
        )
    for config in spec.optional_configs:
        path = _resolve(base, config)
        graph.append(
            {
                "node_id": f"optional_config:{config}",
                "kind": "optional_config",
                "path": str(config),
                "resolved_path": str(path),
                "exists": path.exists(),
                "recommended_command": f"qcchem run -c {config} -o <artifact_root>",
            }
        )
    return graph, missing


def _available_evidence_from_capsules(capsules: list[dict[str, Any]]) -> list[str]:
    available: set[str] = set()
    for capsule in capsules:
        if capsule.get("evidence_summary_status") == "complete":
            available.add("evidence_summary_complete")
        evidence = capsule.get("evidence_summary") or {}
        if isinstance(evidence, dict):
            baseline = evidence.get("primary_baseline") or {}
            if isinstance(baseline, dict) and baseline.get("baseline_strength") == "strong":
                available.add("exact_active_space_baseline")
        if capsule.get("capsule_status") == "complete":
            available.add("artifact_completeness")
    return sorted(available)


def _required_evidence_status(
    spec: ResearchObjectiveSpec,
    capsules: list[dict[str, Any]],
    graph: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    available = set(_available_evidence_from_capsules(capsules))
    if graph:
        for source in graph.get("sources") or []:
            baseline = source.get("primary_baseline") or {}
            if isinstance(baseline, dict) and baseline.get("baseline_strength") == "strong":
                available.add("exact_active_space_baseline")
            if source.get("chemical_accuracy_status") == "met":
                available.add("benchmark_acceptance")
            metric = source.get("primary_error_metric") or {}
            if isinstance(metric, dict) and metric.get("value") is not None:
                available.add("compressed_vs_uncompressed_error")
            if source.get("output_links"):
                available.add("measurement_cost_summary")
    missing = [item for item in spec.required_evidence if item not in available]
    return sorted(available), missing


def _recommended_action(status: str, missing_configs: list[str], missing_evidence: list[str]) -> str:
    if missing_configs:
        return "fix_missing_candidate_configs"
    if missing_evidence:
        return "collect_missing_evidence"
    if status == "ready_for_review":
        return "run_claim_compiler_and_promotion_gate"
    return "compare_against_best_evidence"


def _objective_record(
    spec: ResearchObjectiveSpec,
    *,
    status: str,
    run_graph: list[dict[str, Any]],
    linked_artifacts: list[str],
    available_evidence: list[str],
    missing_evidence: list[str],
    missing_configs: list[str],
    capsules: list[dict[str, Any]] | None = None,
    evidence_graph: dict[str, Any] | None = None,
    claim_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": OBJECTIVE_SCHEMA_VERSION,
        "objective_name": spec.name,
        "title": spec.title,
        "claim": spec.claim,
        "status": status,
        "required_evidence": list(spec.required_evidence),
        "available_evidence": available_evidence,
        "missing_evidence": missing_evidence,
        "missing_candidate_configs": missing_configs,
        "recommended_action": _recommended_action(status, missing_configs, missing_evidence),
        "run_graph": run_graph,
        "linked_artifacts": linked_artifacts,
        "capsules": capsules or [],
        "evidence_graph": evidence_graph,
        "claim_review": claim_review,
        "trust_boundary": {
            "hardware_scope": spec.system_scope.get("hardware_scope", "preview_only"),
            "hardware_verification_boundary": "Runtime evidence must not be described as chemistry validation unless runtime chemical accuracy is met.",
            "exploratory_boundary": "Exploratory artifacts require promotion gate review before candidate language.",
        },
    }


def render_objective_markdown(payload: dict[str, Any], *, title: str) -> str:
    """Render objective plan/status Markdown."""
    lines = [
        f"# {title}",
        "",
        f"- objective_name: `{payload.get('objective_name')}`",
        f"- status: `{payload.get('status')}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        "",
        "## Claim",
        "",
        str(payload.get("claim") or ""),
        "",
        "## Required Evidence Checklist",
        "",
    ]
    available = set(payload.get("available_evidence") or [])
    for item in payload.get("required_evidence") or []:
        marker = "x" if item in available else " "
        lines.append(f"- [{marker}] `{item}`")
    lines.extend(["", "## Missing Evidence", ""])
    lines.extend([f"- `{item}`" for item in payload.get("missing_evidence") or []] or ["- None"])
    lines.extend(["", "## Run Graph", ""])
    for node in payload.get("run_graph") or []:
        lines.append(f"- `{node.get('node_id')}` exists=`{node.get('exists')}` path=`{node.get('path')}`")
    lines.extend(["", "## Linked Artifacts", ""])
    lines.extend([f"- `{item}`" for item in payload.get("linked_artifacts") or []] or ["- None"])
    return "\n".join(lines) + "\n"


def _write_objective_outputs(payload: dict[str, Any], output_dir: Path, *, stem: str, title: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(to_primitive(payload), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_objective_markdown(payload, title=title), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def plan_research_objective(config: Path, output_dir: Path) -> dict[str, Any]:
    """Create a no-execution objective plan."""
    spec = load_research_objective(config)
    run_graph, missing_configs = _config_status(spec)
    linked = [str(path) for path in _linked_artifacts(spec) if path.exists()]
    capsules = [build_and_write_evidence_capsule(path, output_dir / "capsules" / path.name) for path in _linked_artifacts(spec) if path.exists()]
    evidence_graph = summarize_evidence_artifacts(linked, workspace_base=Path.cwd()) if linked else None
    available, missing = _required_evidence_status(spec, capsules, evidence_graph)
    status = "blocked" if missing_configs else "planned" if missing else "planned"
    payload = _objective_record(
        spec,
        status=status,
        run_graph=run_graph,
        linked_artifacts=linked,
        available_evidence=available,
        missing_evidence=missing,
        missing_configs=missing_configs,
        capsules=capsules,
        evidence_graph=evidence_graph,
    )
    payload["outputs"] = _write_objective_outputs(payload, output_dir, stem="objective_plan", title="QCchem Research Objective Plan")
    return payload


def status_research_objective(config_or_artifact_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    """Create an objective status report from objective YAML."""
    path = config_or_artifact_root
    if path.is_dir():
        candidates = [path / "objective.yaml", path / "research_objective.yaml"]
        found = next((candidate for candidate in candidates if candidate.exists()), None)
        if found is None:
            existing = next(
                (
                    candidate
                    for candidate in (path / "objective_status.json", path / "objective_plan.json")
                    if candidate.exists()
                ),
                None,
            )
            if existing is not None:
                payload = json.loads(existing.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError(f"{existing} must contain a JSON object.")
                if output_dir is not None:
                    payload["outputs"] = _write_objective_outputs(
                        payload,
                        output_dir,
                        stem="objective_status",
                        title="QCchem Research Objective Status",
                    )
                return payload
        if found is None:
            raise FileNotFoundError(f"No objective YAML found under '{path}'.")
        path = found
    spec = load_research_objective(path)
    out = output_dir or Path(spec.outputs.get("artifact_root") or "artifacts/objectives") / spec.name
    run_graph, missing_configs = _config_status(spec)
    linked_paths = [path for path in _linked_artifacts(spec) if path.exists()]
    linked = [str(path) for path in linked_paths]
    capsules = [build_and_write_evidence_capsule(path, out / "capsules" / path.name) for path in linked_paths]
    evidence_graph = summarize_evidence_artifacts(linked, workspace_base=Path.cwd()) if linked else None
    available, missing = _required_evidence_status(spec, capsules, evidence_graph)
    claim_review = compile_claim_review(claim_text=spec.claim, targets=linked, workspace_base=Path.cwd()) if linked else None
    if missing_configs or missing:
        status = "blocked"
    elif claim_review and claim_review.get("status") == "passed":
        status = "ready_for_review"
    else:
        status = "in_progress"
    payload = _objective_record(
        spec,
        status=status,
        run_graph=run_graph,
        linked_artifacts=linked,
        available_evidence=available,
        missing_evidence=missing,
        missing_configs=missing_configs,
        capsules=capsules,
        evidence_graph=evidence_graph,
        claim_review=claim_review,
    )
    payload["outputs"] = _write_objective_outputs(payload, out, stem="objective_status", title="QCchem Research Objective Status")
    return payload
