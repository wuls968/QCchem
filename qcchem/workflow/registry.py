"""Registry helpers for aggregate workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qcchem.core import RegistryEntry
from qcchem.reporting import write_result_json


def make_registry_entry(
    *,
    name: str,
    kind: str,
    status: str,
    artifact_root: Path,
    source: str,
    tags: list[str] | None = None,
) -> RegistryEntry:
    """Create a registry entry with a UTC timestamp."""
    return RegistryEntry(
        name=name,
        kind=kind,
        status=status,
        artifact_root=artifact_root,
        created_at=datetime.now(timezone.utc).isoformat(),
        source=source,
        tags=list(tags or []),
    )


def write_registry(entries: list[RegistryEntry], path: Path) -> None:
    """Persist registry entries to JSON."""
    write_result_json(entries, path)
