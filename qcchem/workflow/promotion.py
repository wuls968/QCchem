"""Promotion gate workflow for exploratory artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.core.promotion import (
    LR_ACE_REQUIRED_STUDIES,
    PROMOTION_SCHEMA_VERSION,
    QFT_REQUIRED_STUDIES,
    TC_QSCI_REQUIRED_STUDIES,
)
from qcchem.io.serialization import to_primitive


def _read_artifact(path: Path) -> tuple[Path, dict[str, Any]]:
    target = path.expanduser().resolve()
    if target.is_dir():
        target = target / "result.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{target} must contain a JSON object.")
    return target, payload


def _module_origin(payload: dict[str, Any], path: Path) -> str:
    text = json.dumps(payload, sort_keys=True).lower()
    name = path.as_posix().lower()
    if "tc_qsci_result" in payload or "tc_qsci" in text:
        return "tc_qsci"
    if "qft_model" in payload or "lattice_qed" in text or "lattice_qed" in name:
        return "qft"
    if "lr_ace" in text or "lr_ace" in name:
        return "lr_ace"
    return str(payload.get("module_origin") or "unknown")


def _rules_for(module: str) -> tuple[str, list[str], list[str]]:
    if module == "qft":
        return (
            "finite_cutoff_algorithm_candidate",
            QFT_REQUIRED_STUDIES,
            [
                "configs/exploratory/h2_lattice_qed_sector_audit.yaml",
                "configs/exploratory/h2_cavity_pf_cutoff_convergence.yaml",
            ],
        )
    if module == "lr_ace":
        return (
            "validated_algorithm_candidate",
            LR_ACE_REQUIRED_STUDIES,
            [
                "configs/exploratory/h2_lr_ace.yaml",
                "configs/exploratory/lih_active_lr_ace.yaml",
            ],
        )
    if module == "tc_qsci":
        return (
            "exploratory_algorithm_candidate",
            TC_QSCI_REQUIRED_STUDIES,
            [
                "configs/exploratory/h2_tc_qsci.yaml",
                "configs/exploratory/lih_active_tc_qsci.yaml",
            ],
        )
    return ("exploratory_algorithm_candidate", ["exact baseline", "ablation study"], [])


def _evidence_flags(payload: dict[str, Any]) -> set[str]:
    flags: set[str] = set()
    evidence = payload.get("evidence_summary") if isinstance(payload.get("evidence_summary"), dict) else {}
    baseline = evidence.get("primary_baseline") if isinstance(evidence.get("primary_baseline"), dict) else {}
    benchmark = payload.get("benchmark") if isinstance(payload.get("benchmark"), dict) else {}
    if baseline.get("baseline_strength") == "strong" or (payload.get("exact_baseline") or {}).get("available"):
        flags.add("exact baseline")
    if benchmark.get("compressed_vs_uncompressed") or "compressed_vs_uncompressed" in json.dumps(payload).lower():
        flags.add("compression-vs-uncompressed comparison")
    coverage = payload.get("promotion_evidence") if isinstance(payload.get("promotion_evidence"), dict) else {}
    for key, enabled in coverage.items():
        if enabled:
            flags.add(str(key).replace("_", " "))
    return flags


def review_exploratory_promotion(*, artifact: Path, target: str) -> dict[str, Any]:
    """Review whether an exploratory artifact can enter a promotion pipeline."""
    artifact_path, payload = _read_artifact(artifact)
    evidence = payload.get("evidence_summary") if isinstance(payload.get("evidence_summary"), dict) else {}
    source_trust = str(evidence.get("trust_tier") or payload.get("verification_status") or "exploratory")
    module = _module_origin(payload, artifact_path)
    allowed_target, required, suggested = _rules_for(module)
    flags = _evidence_flags(payload)
    required_missing = [item for item in required if item not in flags]
    blocking: list[str] = []
    if source_trust in {"exploratory", "unstable"}:
        blocking.append("Exploratory or unstable artifact cannot be directly promoted to validated.")
    if target != allowed_target:
        blocking.append(f"{module} can only enter `{allowed_target}` in this promotion gate.")
    if required_missing:
        blocking.append(f"Missing required studies: {', '.join(required_missing)}.")
    status = "allowed" if not blocking and source_trust == "validated" else "candidate_allowed" if not blocking else "blocked"
    if status == "allowed" and source_trust != "validated":
        status = "candidate_allowed"
    recommended = "compare_against_best_evidence"
    if required_missing:
        recommended = "run_ablation_study" if any("ablation" in item for item in required_missing) else "collect_stronger_baseline"
    return {
        "schema_version": PROMOTION_SCHEMA_VERSION,
        "artifact": str(artifact_path),
        "source_trust_tier": source_trust,
        "module_origin": module,
        "target": target,
        "allowed_target": allowed_target,
        "status": status,
        "blocking_gaps": blocking,
        "required_studies": required,
        "missing_required_studies": required_missing,
        "suggested_configs": suggested,
        "safe_claim": (
            f"{module} evidence may be discussed as bounded exploratory algorithm evidence; "
            f"broader validated or publication-grade claims require the promotion gate studies first."
        ),
        "recommended_action": recommended,
    }


def render_promotion_markdown(payload: dict[str, Any]) -> str:
    """Render a promotion gate review."""
    lines = [
        "# QCchem Promotion Gate Review",
        "",
        f"- artifact: `{payload.get('artifact')}`",
        f"- source_trust_tier: `{payload.get('source_trust_tier')}`",
        f"- module_origin: `{payload.get('module_origin')}`",
        f"- target: `{payload.get('target')}`",
        f"- status: `{payload.get('status')}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        "",
        "## Blocking Gaps",
        "",
    ]
    lines.extend([f"- {item}" for item in payload.get("blocking_gaps") or []] or ["- None"])
    lines.extend(["", "## Required Studies", ""])
    lines.extend([f"- {item}" for item in payload.get("required_studies") or []] or ["- None"])
    lines.extend(["", "## Suggested Configs", ""])
    lines.extend([f"- `{item}`" for item in payload.get("suggested_configs") or []] or ["- None"])
    lines.extend(["", "## Safe Claim", "", str(payload.get("safe_claim") or "")])
    return "\n".join(lines) + "\n"


def write_promotion_outputs(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Write promotion review JSON and Markdown outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "promotion_review.json"
    md_path = output_dir / "promotion_review.md"
    json_path.write_text(json.dumps(to_primitive(payload), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_promotion_markdown(payload), encoding="utf-8")
    return {"promotion_review_json": str(json_path), "promotion_review_markdown": str(md_path)}
