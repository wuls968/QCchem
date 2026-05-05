"""Shared workflow helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path


def clone_spec_with_overrides(spec, overrides: dict[str, object]):
    """Deep-copy a dataclass spec and apply dotted-path overrides."""
    cloned = deepcopy(spec)
    for dotted_path, value in overrides.items():
        parts = dotted_path.split(".")
        target = cloned
        for part in parts[:-1]:
            target = getattr(target, part)
        setattr(target, parts[-1], value)
    return cloned


def resolve_artifact_root(root: Path) -> Path:
    """Resolve an artifact root relative to the repository root."""
    if root.is_absolute():
        return root
    return (Path(__file__).resolve().parents[2] / root).resolve()
