"""Real molecular checkpoint continuity and safe recovery rejection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from qcchem.cli.main import main
from qcchem.io.config import load_run_spec
from qcchem.io.checkpoint import read_checkpoint, write_checkpoint
from qcchem.workflow.runner import run_from_config, run_spec
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.workflow_control import file_manifest

REPO = Path(__file__).resolve().parents[2]


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _run_config(tmp_path):
    config = yaml.safe_load((REPO / "configs/h2.yaml").read_text())
    config["solver"]["optimizer"]["maxiter"] = 60
    path = tmp_path / "h2.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def _cancel_after(root, count=5):
    def check():
        path = root / "vqe_checkpoint.json"
        if path.is_file() and len(_read(path)["evaluation_trajectory"]) >= count:
            raise KeyboardInterrupt
    return check


@pytest.mark.integration
def test_real_h2_resume_preserves_scientific_trajectory_and_original_bundle(tmp_path):
    config = _run_config(tmp_path)
    old = tmp_path / "old"
    with pytest.raises(KeyboardInterrupt):
        run_from_config(config, output_dir=old, control_check=_cancel_after(old))
    assert not (old / "result.json").exists()
    before = file_manifest([old])
    resumed = run_from_config(config, output_dir=tmp_path / "new", resume_from=old)
    full = run_from_config(config, output_dir=tmp_path / "full")
    assert file_manifest([old]) == before
    resumed_trajectory = _read(resumed.artifacts.root / "vqe_checkpoint.json")["evaluation_trajectory"]
    assert resumed_trajectory == _read(full.artifacts.root / "vqe_checkpoint.json")["evaluation_trajectory"]
    assert resumed.energy.total_energy == full.energy.total_energy
    assert resumed.problem.num_particles == (1, 1)
    assert resumed.verification_status == full.verification_status == "validated"
    recovery = resumed.variational_result.initial_point_provenance["checkpoint_recovery"]
    assert recovery["replayed_evaluations"] == 5
    assert recovery["new_evaluations"] + 5 == resumed.variational_result.evaluations
    assert _read(resumed.artifacts.root / "run_checkpoint.json")["status"] == "completed"
    assert main(["run", "-c", str(config), "-o", str(old), "--resume-from", str(old)]) == 2
    assert file_manifest([old]) == before


@pytest.mark.integration
@pytest.mark.parametrize("change", ["geometry", "input_file", "implementation"])
def test_recovery_rejects_changes_before_creating_output(tmp_path, monkeypatch, change):
    config = _run_config(tmp_path)
    old = tmp_path / "old"
    with pytest.raises(KeyboardInterrupt):
        run_from_config(config, output_dir=old, control_check=_cancel_after(old, 2))
    spec = load_run_spec(config)
    if change == "geometry":
        spec.molecule.geometry[1].coords = (0.0, 0.0, 0.8)
    elif change == "input_file":
        config.write_text(config.read_text() + "\n# changed input\n", encoding="utf-8")
    else:
        import qcchem.workflow.computation_control as control

        original = control.implementation_identity
        monkeypatch.setattr(control, "implementation_identity", lambda *args: {**original(*args), "source_sha256": "changed"})
    new = tmp_path / "new"
    with pytest.raises(ValueError, match="changed"):
        run_spec(spec, source_config=str(config), output_dir=new, resume_from=old)
    assert not new.exists()


def _scan_config(tmp_path):
    base = _run_config(tmp_path)
    path = tmp_path / "scan.yaml"
    path.write_text(yaml.safe_dump({"scan": {
        "name": "h2_checkpoint_scan", "base_config": str(base),
        "parameter": {"name": "bond_length", "kind": "bond_distance", "values": [0.65, 0.735, 0.9]},
        "continuity": {"enabled": True, "mode": "linear_predictor"},
    }}), encoding="utf-8")
    return path


@pytest.mark.integration
@pytest.mark.parametrize("inside_point", [False, True])
def test_scan_reuses_completed_points_and_preserves_predictor_history(tmp_path, inside_point):
    config = _scan_config(tmp_path)
    old = tmp_path / "old"

    def cancel():
        path = old / "scan_checkpoint.json"
        if not path.is_file():
            return
        state = _read(path)
        if len(state["points"]) != 1:
            return
        if not inside_point:
            raise KeyboardInterrupt
        active = state.get("active_point")
        if active:
            _cancel_after(Path(active["artifact_root"]), 5)()

    with pytest.raises(KeyboardInterrupt):
        run_scan_from_config(config, output_dir=old, control_check=cancel)
    state = _read(old / "scan_checkpoint.json")
    first = Path(state["points"][0]["summary"]["run_artifact_root"])
    original_point = file_manifest([first])
    resumed = run_scan_from_config(config, output_dir=tmp_path / "new", resume_from=old)
    full = run_scan_from_config(config, output_dir=tmp_path / "full")
    assert file_manifest([first]) == original_point
    assert resumed.points[0].run_artifact_root == first
    assert not (resumed.artifacts.root / "points" / resumed.points[0].point_label).exists()
    assert [point.total_energy for point in resumed.points] == [point.total_energy for point in full.points]
    assert resumed.points[2].initial_point_strategy == "linear_predictor"
    assert resumed.points[2].history_sources == [resumed.points[0].point_label, resumed.points[1].point_label]
    assert resumed.points[0].evidence_summary.primary_scientific_claim
    for actual, expected in zip(resumed.points[1:], full.points[1:], strict=True):
        actual_cp = _read(actual.run_artifact_root / "vqe_checkpoint.json")
        expected_cp = _read(expected.run_artifact_root / "vqe_checkpoint.json")
        assert actual_cp["evaluation_trajectory"] == expected_cp["evaluation_trajectory"]
    if inside_point:
        point_result = _read(resumed.points[1].run_artifact_root / "result.json")
        assert point_result["variational_result"]["initial_point_provenance"]["checkpoint_recovery"]["replayed_evaluations"] == 5
    complete = run_scan_from_config(config, output_dir=tmp_path / "again", resume_from=resumed.artifacts.root)
    assert [point.run_artifact_root for point in complete.points] == [point.run_artifact_root for point in resumed.points]
    assert not any((complete.artifacts.root / "points").iterdir())
    (first / "result.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        run_scan_from_config(config, output_dir=tmp_path / "rejected", resume_from=resumed.artifacts.root)
    assert not (tmp_path / "rejected").exists()


def test_cli_exposes_recovery_options_and_rejects_missing_checkpoint(tmp_path, capsys):
    with pytest.raises(SystemExit) as exited:
        main(["run", "--help"])
    assert exited.value.code == 0
    assert "--resume-from" in capsys.readouterr().out
    assert main(["scan", "run", "-c", str(_scan_config(tmp_path)), "-o", str(tmp_path / "new"),
                 "--resume-from", str(tmp_path / "missing")]) == 2


@pytest.mark.integration
def test_malformed_scan_checkpoint_is_rejected_before_new_output(tmp_path):
    config = _scan_config(tmp_path)
    old = tmp_path / "old"

    def cancel():
        path = old / "scan_checkpoint.json"
        if path.is_file() and len(_read(path)["points"]) == 1:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_scan_from_config(config, output_dir=old, control_check=cancel)
    path = old / "scan_checkpoint.json"
    state = read_checkpoint(path, schema="qcchem.scan_checkpoint.v1")
    state["active_point"] = {"index": 0, "artifact_root": str(old)}
    write_checkpoint(path, state)
    with pytest.raises(ValueError, match="invalid active scan point"):
        run_scan_from_config(config, output_dir=tmp_path / "new", resume_from=old)
    assert not (tmp_path / "new").exists()
