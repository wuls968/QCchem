"""Campaign workflow configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from qcchem.core import CampaignEntrySpec, CampaignSpec
from qcchem.io.config import _project_root, _require_mapping, resolve_user_path


SUPPORTED_CAMPAIGN_ENTRY_KINDS = {
    "run",
    "benchmark",
    "study",
    "scan",
    "hardware_calibration",
    "artifact",
}


def _resolve_project_path(value: str | Path | None) -> Path | None:
    if value in {None, ""}:
        return None
    candidate = Path(str(value))
    return candidate if candidate.is_absolute() else (_project_root() / candidate).resolve()


def load_campaign_spec(path: Path) -> CampaignSpec:
    """Load a trust-loop campaign configuration from YAML."""

    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Campaign configuration must deserialize to a mapping.")
    data = _require_mapping(raw, "campaign")
    entries_raw = data.get("entries", [])
    if not isinstance(entries_raw, list) or not entries_raw:
        raise ValueError("campaign.entries must be a non-empty list.")
    entries: list[CampaignEntrySpec] = []
    for item in entries_raw:
        if not isinstance(item, dict):
            raise ValueError("campaign.entries entries must be mappings.")
        kind = str(item.get("kind", "")).strip()
        if kind not in SUPPORTED_CAMPAIGN_ENTRY_KINDS:
            raise ValueError(
                "campaign.entries.kind must be one of "
                f"{sorted(SUPPORTED_CAMPAIGN_ENTRY_KINDS)}, got '{kind}'."
            )
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError("campaign.entries.name is required.")
        entries.append(
            CampaignEntrySpec(
                name=name,
                kind=kind,
                config=_resolve_project_path(item.get("config")),
                artifact=_resolve_project_path(item.get("artifact")),
                output_dir=_resolve_project_path(item.get("output_dir")),
                allow_runtime_submission=bool(item.get("allow_runtime_submission", False)),
                tags=[str(value) for value in item.get("tags", [])],
            )
        )
    return CampaignSpec(
        name=str(data["name"]),
        description=str(data.get("description", "")),
        output_root=_resolve_project_path(data.get("output_root")) or (_project_root() / "artifacts" / str(data["name"])),
        entries=entries,
        tags=[str(value) for value in data.get("tags", [])],
    )
