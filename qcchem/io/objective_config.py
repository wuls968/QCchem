"""Research Objective YAML loading and template writing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from qcchem.core.objective import ResearchObjectiveSpec
from qcchem.io.config import resolve_user_path


DEFAULT_REQUIRED_EVIDENCE = [
    "exact_active_space_baseline",
    "compressed_vs_uncompressed_error",
    "benchmark_acceptance",
    "measurement_cost_summary",
    "evidence_summary_complete",
]


def _mapping(value: Any, *, key: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"research_objective.{key} must be a mapping.")
    return value


def _string_list(value: Any, *, key: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"research_objective.{key} must be a list.")
    return [str(item) for item in value]


def load_research_objective(path: Path) -> ResearchObjectiveSpec:
    """Load a research objective YAML file."""
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Research objective configuration must be a mapping.")
    data = raw.get("research_objective")
    if not isinstance(data, dict):
        raise ValueError("Research objective configuration requires a research_objective mapping.")
    name = str(data.get("name") or "").strip()
    claim = str(data.get("claim") or "").strip()
    if not name:
        raise ValueError("research_objective.name is required.")
    if not claim:
        raise ValueError("research_objective.claim is required.")
    return ResearchObjectiveSpec(
        name=name,
        title=str(data.get("title") or name).strip(),
        claim=claim,
        system_scope=_mapping(data.get("system_scope"), key="system_scope"),
        required_evidence=_string_list(data.get("required_evidence") or DEFAULT_REQUIRED_EVIDENCE, key="required_evidence"),
        candidate_configs=[Path(item) for item in _string_list(data.get("candidate_configs"), key="candidate_configs")],
        optional_configs=[Path(item) for item in _string_list(data.get("optional_configs"), key="optional_configs")],
        linked_artifacts=[Path(item) for item in _string_list(data.get("linked_artifacts"), key="linked_artifacts")],
        promotion_policy=_mapping(data.get("promotion_policy"), key="promotion_policy"),
        outputs={str(key): str(value) for key, value in _mapping(data.get("outputs"), key="outputs").items()},
        source_path=resolved_path,
    )


def write_objective_template(*, name: str, claim: str, output_path: Path) -> Path:
    """Write a conservative Research Objective YAML template."""
    if not name.strip():
        raise ValueError("--name is required.")
    if not claim.strip():
        raise ValueError("--claim is required.")
    payload = {
        "research_objective": {
            "name": name,
            "title": name.replace("_", " ").title(),
            "claim": claim,
            "system_scope": {
                "molecule": "H2",
                "basis": "sto3g",
                "hardware_scope": "preview_only",
            },
            "required_evidence": list(DEFAULT_REQUIRED_EVIDENCE),
            "candidate_configs": ["configs/h2.yaml"],
            "optional_configs": [],
            "linked_artifacts": [],
            "promotion_policy": {
                "local_validated_requires": {
                    "chemical_accuracy_status": "met",
                    "baseline_strength": "strong",
                },
                "hardware_claim_requires": {
                    "runtime_evidence_status": "retrieved_result",
                    "runtime_chemical_accuracy_status": "met",
                },
                "exploratory_promotion_requires": {
                    "cross_molecule_coverage": True,
                    "exact_baseline": True,
                    "ablation": True,
                },
            },
            "outputs": {
                "artifact_root": f"artifacts/objectives/{name}",
            },
        }
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path
