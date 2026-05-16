"""Shared workflow helpers."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path


def _resolve_override_target(root, dotted_path: str):
    parts = dotted_path.split(".")
    target = root
    for part in parts[:-1]:
        if isinstance(target, list):
            target = target[int(part)]
        else:
            target = getattr(target, part)
    return target, parts[-1]


def clone_spec_with_overrides(spec, overrides: dict[str, object]):
    """Deep-copy a dataclass spec and apply dotted-path overrides."""
    cloned = deepcopy(spec)
    for dotted_path, value in overrides.items():
        target, attr = _resolve_override_target(cloned, dotted_path)
        if isinstance(target, list):
            target[int(attr)] = value
        else:
            setattr(target, attr, value)
    return cloned


def resolve_artifact_root(root: Path) -> Path:
    """Resolve an artifact root relative to the repository root."""
    if root.is_absolute():
        return root
    return (Path(__file__).resolve().parents[2] / root).resolve()
