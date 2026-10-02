"""Read-only selection and normalization of persisted scan/study artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from qcchem.io.checkpoint import read_checkpoint
from qcchem.workbench.data import resolve_workbench_artifact_root
from qcchem.workflow.computation_control import ComputationLock
from qcchem.workflow.workflow_control import WorkflowBusyError

DEMO_SELECTION = "demo:bundled"
_EXCLUDED = {"execution_history", "preview_local"}


def finite_value(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def energy_label(value: Any) -> str:
    number = finite_value(value)
    return f"{number:.6f} Ha" if number is not None else "Unavailable"


def catalog_paths(root: Path, names: set[str]) -> list[Path]:
    """Never follow a result or parent symlink outside the configured root."""
    root = root.resolve()
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.name in names and path.is_file()
                  and not (_EXCLUDED & set(path.relative_to(root).parts))
                  and not any(part.is_symlink() for part in (path, *path.parents) if part != root)
                  and path.resolve().is_relative_to(root))


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Artifact JSON must contain an object.")
    return value


def _normalize_model(model: dict[str, Any], kind: str) -> dict[str, Any]:
    key = "points" if kind == "scan" else "run_records"
    rows = model.get(key)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Artifact requires a list of {key} objects.")
    model = dict(model)
    normalized = []
    for index, original in enumerate(rows):
        row = dict(original)
        label = "point_label" if kind == "scan" else "name"
        row[label] = str(row.get(label) or f"Unnamed record {index + 1}")
        row["verification_status"] = str(row.get("verification_status") or "unknown")
        for field in ("total_energy", "parameter_value", "exact_error", "absolute_error"):
            row[field] = finite_value(row.get(field))
        normalized.append(row)
    model[key] = normalized
    for field in ("summary", "evidence_summary"):
        if not isinstance(model.get(field), dict):
            model[field] = {}
    if not isinstance(model["summary"].get("comparison_axes"), list):
        model["summary"]["comparison_axes"] = []
    return model


def _checkpoint_scan(path: Path) -> dict[str, Any]:
    state = read_checkpoint(path, schema="qcchem.scan_checkpoint.v1")
    saved = state.get("points")
    if not isinstance(saved, list) or any(not isinstance(point, dict) or not isinstance(point.get("summary"), dict) for point in saved):
        raise ValueError("Scan checkpoint has invalid committed points.")
    points = [point["summary"] for point in saved]
    counts: dict[str, int] = {}
    for point in points:
        status = str(point.get("verification_status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    status = str(state.get("status") or "unknown")
    if status == "running":
        try:
            with ComputationLock(path.parent, create=False):
                status = "interrupted"
        except WorkflowBusyError:
            pass
    return {
        "scan_name": state.get("scan_name") or path.parent.name,
        "parameter_name": state.get("parameter_name") or "parameter (name unavailable)",
        "parameter_unit": state.get("parameter_unit"),
        "points": points,
        "summary": {"total_runs": len(points), "status_counts": counts},
        "expected_points": len(state["parameter_values"]) if isinstance(state.get("parameter_values"), list) else None,
        "artifact_status": status,
        "partial": True,
        "active_point": state.get("active_point"),
        "evidence_summary": {"trust_tier": "incomplete", "recommended_action": "review_checkpoint",
                             "primary_scientific_claim": "Only committed points are shown; the scan result has not been published."},
    }


def aggregate_catalog(kind: str, artifact_root: Path | None = None) -> list[dict[str, Any]]:
    if kind not in {"scan", "study"}:
        raise ValueError("Aggregate kind must be scan or study.")
    root = Path(artifact_root).resolve() if artifact_root is not None else resolve_workbench_artifact_root()
    names = {f"{kind}_result.json"} | ({"scan_checkpoint.json"} if kind == "scan" else set())
    groups: dict[Path, set[str]] = {}
    for path in catalog_paths(root, names):
        groups.setdefault(path.parent, set()).add(path.name)
    catalog = []
    for directory, files in groups.items():
        path = directory / f"{kind}_result.json"
        try:
            checkpoint = directory / "scan_checkpoint.json"
            # A checkpoint-only bundle is meaningful even with zero saved points.
            # Never prefer stale final data over a newer unfinished checkpoint.
            if kind == "scan" and "scan_checkpoint.json" in files:
                partial = _checkpoint_scan(checkpoint)
                if path.name not in files or partial["artifact_status"] != "completed":
                    model, path = partial, checkpoint
                else:
                    model = _json_object(path)
            else:
                model = _json_object(path)
            model = _normalize_model(model, kind)
            model.setdefault("artifact_status", "result published")
            error = None
        except (OSError, ValueError, TypeError, KeyError) as exc:
            model, error = {}, f"Cannot read aggregate: {exc}"
        relative = directory.relative_to(root).as_posix()
        name = str(model.get(f"{kind}_name") or directory.name)
        try:
            mtime = max((directory / filename).stat().st_mtime for filename in files)
        except OSError:
            mtime = 0.0  # A writer may replace or withdraw a bundle during refresh.
        catalog.append({"value": f"artifact:{relative}", "label": f"{name} · {relative}",
                        "model": {**model, "source_path": str(path), "source_error": error},
                        "mtime": mtime})
    return sorted(catalog, key=lambda row: (row["mtime"], row["value"]), reverse=True)


def aggregate_selection(kind: str, selection: str | None, artifact_root: Path | None = None):
    """Resolve a browser value through the server catalog, never as a file path."""
    catalog = aggregate_catalog(kind, artifact_root)
    options = [{"label": row["label"], "value": row["value"]} for row in catalog]
    options.append({"label": "Demo · bundled example", "value": DEMO_SELECTION})
    selected = selection or (catalog[0]["value"] if catalog else None)
    row = next((item for item in catalog if item["value"] == selected), None)
    if selected == DEMO_SELECTION:
        from qcchem.workbench.pages.scans import sample_scan_model
        from qcchem.workbench.pages.studies import sample_study_model

        model = sample_scan_model() if kind == "scan" else sample_study_model()
        return options, selected, {**model, "demo": True}
    if row:
        return options, selected, row["model"]
    message = "Selected artifact is unavailable; choose another source." if selected else f"No real {kind} artifacts found. Choose Demo to inspect the bundled example."
    return options, None, {"source_error": message}
