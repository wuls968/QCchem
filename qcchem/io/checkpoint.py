"""Atomic JSON checkpoints with accidental-corruption detection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json


def checkpoint_digest(value: Any) -> str:
    content = json.dumps(to_primitive(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def write_checkpoint(path: Path, state: dict[str, Any]) -> None:
    """Publish one complete, finite checkpoint using the atomic JSON writer."""
    content = {key: value for key, value in state.items() if key != "checkpoint_sha256"}
    write_result_json({**content, "checkpoint_sha256": checkpoint_digest(content)}, path)


def read_checkpoint(path: Path, *, schema: str) -> dict[str, Any]:
    """Require schema and integrity before the caller validates semantic fields."""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or state.get("schema_version") != schema:
            raise ValueError("unsupported schema")
        content = {key: value for key, value in state.items() if key != "checkpoint_sha256"}
        if state.get("checkpoint_sha256") != checkpoint_digest(content):
            raise ValueError("integrity mismatch")
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid computation checkpoint '{path}': {exc}") from exc
    return state
