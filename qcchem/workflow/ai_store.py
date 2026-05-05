"""Persistence helpers for the AI workspace state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.core.ai_workspace import ticket_lane_for_status


def workspace_root(base: Path | None = None, *, create: bool = True) -> Path:
    """Return the AI workspace root and ensure its artifact directories exist."""
    root = (base or Path.cwd()) / "artifacts" / "ai_workspace"
    if create:
        for name in ("sessions", "tickets", "deliveries", "providers", "bindings"):
            (root / name).mkdir(parents=True, exist_ok=True)
    return root


def write_ticket_record(root: Path, record: dict[str, Any]) -> Path:
    """Write a ticket record into the workspace tickets directory."""
    path = root / "tickets" / f"{record['task_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_delivery_record(root: Path, record: dict[str, Any]) -> Path:
    """Write a delivery record into the workspace deliveries directory."""
    path = root / "deliveries" / f"{record['delivery_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path


def read_ticket_record(path: Path) -> dict[str, Any]:
    """Read a ticket record from JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def read_delivery_record(path: Path) -> dict[str, Any]:
    """Read a delivery record from JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def list_ticket_records(
    root: Path,
    *,
    lane: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Return persisted ticket records, optionally filtered by lane or status."""
    tickets: list[dict[str, Any]] = []
    tickets_dir = root / "tickets"
    if not tickets_dir.exists():
        return tickets
    for path in sorted(tickets_dir.glob("*.json")):
        payload = read_ticket_record(path)
        payload_status = payload.get("status")
        payload_lane = ticket_lane_for_status(payload_status if isinstance(payload_status, str) else None)
        if status is not None and payload_status != status:
            continue
        if lane is not None and payload_lane != lane:
            continue
        tickets.append(payload)
    return tickets


def list_delivery_records(root: Path) -> list[dict[str, Any]]:
    """Return persisted delivery records ordered by file name."""
    deliveries: list[dict[str, Any]] = []
    deliveries_dir = root / "deliveries"
    if not deliveries_dir.exists():
        return deliveries
    for path in sorted(deliveries_dir.glob("*.json")):
        deliveries.append(read_delivery_record(path))
    return deliveries
