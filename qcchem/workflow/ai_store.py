"""Persistence helpers for the AI workspace state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def workspace_root(base: Path | None = None) -> Path:
    """Return the AI workspace root and ensure its artifact directories exist."""
    root = (base or Path.cwd()) / "artifacts" / "ai_workspace"
    for name in ("sessions", "tickets", "deliveries", "providers", "bindings"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def write_ticket_record(root: Path, record: dict[str, Any]) -> Path:
    """Write a ticket record into the workspace tickets directory."""
    path = root / "tickets" / f"{record['task_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path


def read_ticket_record(path: Path) -> dict[str, Any]:
    """Read a ticket record from JSON."""
    return json.loads(path.read_text(encoding="utf-8"))
