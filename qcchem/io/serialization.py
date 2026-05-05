"""Serialization helpers for dataclasses and JSON/YAML artifacts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np


def to_primitive(value: Any) -> Any:
    """Convert dataclasses and path-like values to JSON/YAML-safe primitives."""
    if is_dataclass(value):
        return to_primitive(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return to_primitive(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [to_primitive(item) for item in value]
    if isinstance(value, list):
        return [to_primitive(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    return value
