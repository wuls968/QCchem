"""Scan config loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.core import ScanParameterSpec, ScanSpec
from qcchem.io.config import _project_root, _require_mapping


def load_scan_spec(path: Path) -> ScanSpec:
    """Load a 1D scan specification from YAML."""
    resolved_path = path if path.is_absolute() else (_project_root() / path).resolve()
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Scan configuration must deserialize to a mapping.")
    scan_raw = _require_mapping(raw, "scan")
    parameter_raw = _require_mapping(scan_raw, "parameter")

    base_config = Path(str(scan_raw["base_config"]))
    if not base_config.is_absolute():
        base_config = (_project_root() / base_config).resolve()

    return ScanSpec(
        name=str(scan_raw["name"]),
        description=str(scan_raw.get("description", "")),
        base_config=base_config,
        parameter=ScanParameterSpec(
            name=str(parameter_raw["name"]),
            kind=str(parameter_raw["kind"]),
            atom_indices=(int(parameter_raw["atom_indices"][0]), int(parameter_raw["atom_indices"][1])),
            values=[float(value) for value in parameter_raw.get("values", [])],
            axis=tuple(float(value) for value in parameter_raw.get("axis", [0.0, 0.0, 1.0])),
        ),
        policy_name=scan_raw.get("policy_name"),
        tags=[str(value) for value in scan_raw.get("tags", [])],
    )
