"""Artifact selection and honest presentation of incomplete numerical evidence."""

from __future__ import annotations

import json

import pytest

from qcchem.io.checkpoint import write_checkpoint
from qcchem.workbench.aggregates import DEMO_SELECTION, aggregate_catalog, aggregate_selection, finite_value
from qcchem.workbench.pages.scans import _scan_curve_figure, build_scans_page
from qcchem.workbench.pages.studies import _study_energy_figure, build_studies_page


def _write(root, kind, name, rows):
    root.mkdir(parents=True, exist_ok=True)
    model = {f"{kind}_name": name, "points" if kind == "scan" else "run_records": rows}
    (root / f"{kind}_result.json").write_text(json.dumps(model))
    return model


@pytest.mark.parametrize("kind", ["scan", "study"])
def test_selects_real_artifacts_and_retains_explicit_demo(tmp_path, kind):
    root = tmp_path / "evidence"
    _write(root / "older", kind, "Real older", [])
    _write(root / "newer", kind, "Real newer", [])
    catalog = aggregate_catalog(kind, root)
    assert len(catalog) == 2
    options, value, model = aggregate_selection(kind, "artifact:older", root)
    assert value == "artifact:older"
    assert model[f"{kind}_name"] == "Real older"
    assert model["source_path"].startswith(str(root))
    assert options[-1]["value"] == DEMO_SELECTION
    assert aggregate_selection(kind, DEMO_SELECTION, root)[2]["demo"] is True
    assert "unavailable" in aggregate_selection(kind, "../../other", root)[2]["source_error"]


def test_empty_workspace_does_not_present_demo_as_real(tmp_path):
    options, value, model = aggregate_selection("scan", None, tmp_path)
    assert value is None and len(options) == 1
    assert "No real scan" in model["source_error"]
    assert not model.get("demo")


def test_catalog_excludes_history_previews_and_symlinks(tmp_path):
    root = tmp_path / "evidence"
    _write(root / "real", "scan", "Real", [])
    _write(root / "execution_history" / "old", "scan", "Old", [])
    _write(root / "preview_local", "scan", "Preview", [])
    outside = tmp_path / "outside"
    _write(outside, "scan", "Outside", [])
    (root / "link").symlink_to(outside, target_is_directory=True)
    (root / "real" / "study_result.json").symlink_to(outside / "scan_result.json")
    assert [row["model"]["scan_name"] for row in aggregate_catalog("scan", root)] == ["Real"]
    assert aggregate_catalog("study", root) == []


def test_corrupt_real_artifact_is_visible_without_falling_back(tmp_path):
    (tmp_path / "scan_result.json").write_text("{")
    row = aggregate_catalog("scan", tmp_path)[0]
    assert row["model"]["source_error"]
    assert aggregate_selection("scan", row["value"], tmp_path)[2]["source_error"]


def test_checkpoint_only_scan_shows_committed_points_and_planned_count(tmp_path):
    path = tmp_path / "scan_checkpoint.json"
    state = {"schema_version": "qcchem.scan_checkpoint.v1", "scan_name": "Actual scan",
             "parameter_name": "bond", "parameter_unit": "bohr", "parameter_values": [1, 2, 3],
             "status": "interrupted", "active_point": {"index": 1},
             "points": [{"summary": {"point_label": "p0", "parameter_value": 1, "total_energy": -1, "verification_status": "validated"}}]}
    write_checkpoint(path, state)
    model = aggregate_catalog("scan", tmp_path)[0]["model"]
    assert model["partial"] and model["expected_points"] == 3
    assert model["parameter_unit"] == "bohr"
    assert model["summary"]["total_runs"] == 1
    assert model["evidence_summary"]["trust_tier"] == "incomplete"
    assert _scan_curve_figure(model).layout.xaxis.title.text == "bond (bohr)"
    _write(tmp_path, "scan", "Stale result", [])
    assert aggregate_catalog("scan", tmp_path)[0]["model"]["partial"]
    state["status"] = "completed"
    write_checkpoint(path, state)
    assert aggregate_catalog("scan", tmp_path)[0]["model"]["scan_name"] == "Stale result"


def test_scan_missing_energy_is_a_gap_and_not_a_false_minimum():
    model = {"points": [{"point_label": "missing", "parameter_value": 1, "total_energy": None},
                         {"point_label": "positive", "parameter_value": 2, "total_energy": 1.5},
                         {"point_label": "nan", "parameter_value": 3, "total_energy": float("nan")}]}
    graph = _scan_curve_figure(model)
    assert tuple(graph.data[0].y) == (None, 1.5, None)
    assert graph.data[0].connectgaps is False
    assert tuple(graph.data[1].y) == (1.5,)
    assert graph.data[1].text == ("Lowest sampled energy",)
    assert "Unavailable" in str(build_scans_page(model))


def test_unowned_running_scan_checkpoint_is_interrupted(tmp_path):
    from qcchem.workflow.computation_control import ComputationLock

    write_checkpoint(tmp_path / "scan_checkpoint.json", {
        "schema_version": "qcchem.scan_checkpoint.v1", "points": [], "status": "running"})
    assert aggregate_catalog("scan", tmp_path)[0]["model"]["artifact_status"] == "interrupted"
    with ComputationLock(tmp_path):
        assert aggregate_catalog("scan", tmp_path)[0]["model"]["artifact_status"] == "running"


def test_study_missing_error_does_not_claim_zero_error():
    model = {"run_records": [{"name": "unknown", "total_energy": None, "absolute_error": None},
                              {"name": "measured", "total_energy": 1.2}]}
    graph = _study_energy_figure(model)
    assert tuple(graph.data[0].y) == (None, 1.2)
    assert tuple(graph.data[1].y) == (None, None)
    text = str(build_studies_page(model))
    assert "1.200000 Ha" in text and "Unavailable" in text
    assert "0.000000 Ha" not in text


@pytest.mark.parametrize("value", [None, True, "1", float("inf"), float("nan"), 10**1000])
def test_non_numeric_or_non_finite_values_remain_missing(value):
    assert finite_value(value) is None
