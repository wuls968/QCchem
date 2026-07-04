"""Study config loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.core import StudyRunSpec, StudySpec
from qcchem.io.config import _parse_continuity, _require_mapping, resolve_project_path, resolve_user_path


def load_study_spec(path: Path) -> StudySpec:
    """Load a study specification from YAML."""
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Study configuration must deserialize to a mapping.")
    study_raw = _require_mapping(raw, "study")
    runs_raw = study_raw.get("runs", [])
    if not isinstance(runs_raw, list) or not runs_raw:
        raise ValueError("study.runs must be a non-empty list.")

    runs: list[StudyRunSpec] = []
    for item in runs_raw:
        if not isinstance(item, dict):
            raise ValueError("Each study run must be a mapping.")
        config_path = resolve_project_path(resolved_path, item["config"])
        runs.append(
            StudyRunSpec(
                name=str(item["name"]),
                config=config_path,
                overrides=dict(item.get("overrides", {})),
                tags=[str(value) for value in item.get("tags", [])],
            )
        )

    return StudySpec(
        name=str(study_raw["name"]),
        description=str(study_raw.get("description", "")),
        registry_name=str(study_raw.get("registry_name", study_raw["name"])),
        policy_name=study_raw.get("policy_name"),
        runs=runs,
        tags=[str(value) for value in study_raw.get("tags", [])],
        continuity=_parse_continuity(
            study_raw,
            default_enabled=False,
            default_mode="previous_optimal",
            allowed_modes={"previous_optimal"},
        ),
    )
