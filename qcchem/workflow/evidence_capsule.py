"""Workflow helpers for evidence capsule outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.core.evidence_capsule import render_evidence_capsule_markdown, validate_evidence_capsule
from qcchem.io.serialization import to_primitive


def write_evidence_capsule_outputs(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Write evidence capsule JSON and Markdown outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evidence_capsule.json"
    md_path = output_dir / "evidence_capsule.md"
    json_path.write_text(json.dumps(to_primitive(payload), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_evidence_capsule_markdown(payload), encoding="utf-8")
    return {"capsule_json": str(json_path), "capsule_markdown": str(md_path)}


def build_and_write_evidence_capsule(artifact_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    """Validate an evidence capsule and optionally write outputs."""
    capsule = validate_evidence_capsule(artifact_root)
    out = output_dir or Path(capsule["artifact_root"])
    capsule["outputs"] = write_evidence_capsule_outputs(capsule, out)
    return capsule
