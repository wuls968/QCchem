"""Exercise crash, concurrent writer rejection, and workflow cancellation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from qcchem.workflow.custom_workflow import resume_custom_workflow_from_config
from qcchem.workflow.workflow_control import file_manifest, request_workflow_cancel, workflow_status

REPO = Path(__file__).resolve().parents[2]
WORKER = REPO / "tests/helpers/inner_checkpoint_worker.py"


def _config(tmp_path):
    config = yaml.safe_load((REPO / "configs/h2.yaml").read_text())
    config["solver"]["optimizer"]["maxiter"] = 60
    path = tmp_path / "h2.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def _env(tmp_path):
    return {**os.environ, "PYTHONPATH": str(REPO), "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "QCCHEM_TEST_GATE": str(tmp_path)}


def _start(tmp_path, *args):
    with (tmp_path / "worker.log").open("w", encoding="utf-8") as log:
        return subprocess.Popen([sys.executable, str(WORKER), *map(str, args)], env=_env(tmp_path),
                                stdout=log, stderr=subprocess.STDOUT)


def _ready(tmp_path, process):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if (tmp_path / "ready").exists():
            return
        if process.poll() is not None:
            pytest.fail((tmp_path / "worker.log").read_text())
        time.sleep(0.02)
    pytest.fail("Owned checkpoint test worker did not reach its gate.")


def _stop(process):
    if process.poll() is None:
        process.kill()
        process.wait(timeout=5)


def _invoke(tmp_path, *args):
    return subprocess.run([sys.executable, "-m", "qcchem.cli.main", *map(str, args)], env=_env(tmp_path),
                          cwd=REPO, capture_output=True, text=True, timeout=30, check=False)


@pytest.mark.integration
def test_killed_vqe_preserves_pending_work_and_rejects_competing_writer(tmp_path):
    config = _config(tmp_path)
    old = tmp_path / "old"
    process = _start(tmp_path, "run", "-c", config, "-o", old)
    try:
        _ready(tmp_path, process)
        checkpoint = (old / "vqe_checkpoint.json").read_bytes()
        state = json.loads(checkpoint)
        assert len(state["evaluation_trajectory"]) == 5
        assert state["pending_evaluation"]["evaluation_index"] == 6
        rejected = _invoke(tmp_path, "run", "-c", config, "-o", old)
        assert rejected.returncode == 2, rejected.stdout + rejected.stderr
        assert "already running" in rejected.stdout
        assert (old / "vqe_checkpoint.json").read_bytes() == checkpoint
        _stop(process)
        before = file_manifest([old])
        new = tmp_path / "new"
        resumed = _invoke(tmp_path, "run", "-c", config, "-o", new, "--resume-from", old)
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert file_manifest([old]) == before
        result = json.loads((new / "result.json").read_text())
        assert result["verification_status"] == "validated"
        assert result["variational_result"]["initial_point_provenance"]["checkpoint_recovery"]["replayed_evaluations"] == 5
        assert json.loads((new / "vqe_checkpoint.json").read_text())["evaluation_trajectory"][:5] == state["evaluation_trajectory"]
    finally:
        _stop(process)


@pytest.mark.integration
def test_workflow_cancel_observed_inside_vqe_and_explicit_retry_resumes_inner_checkpoint(tmp_path):
    config = _config(tmp_path)
    workflow = tmp_path / "workflow.yaml"
    root = tmp_path / "workflow"
    workflow.write_text(yaml.safe_dump({"workflow": {
        "name": "inner_recovery", "output_root": str(root),
        "steps": [{"id": "vqe", "kind": "run_config", "inputs": {"config": str(config)}}],
    }}), encoding="utf-8")
    process = _start(tmp_path, "workflow", "run", "-c", workflow)
    try:
        _ready(tmp_path, process)
        old = root / "step_outputs/vqe/artifact"
        request = request_workflow_cancel(root)
        assert request["cancel_requested"] is True
        (tmp_path / "release").write_text("release", encoding="utf-8")
        assert process.wait(timeout=20) == 130, (tmp_path / "worker.log").read_text()
        assert workflow_status(root)["status"] == "cancelled"
        assert not (old / "result.json").exists()
        assert json.loads((old / "run_checkpoint.json").read_text())["status"] == "interrupted"
        partial = json.loads((old / "vqe_checkpoint.json").read_text())
        assert len(partial["evaluation_trajectory"]) == 6
        before = file_manifest([old])
        resumed = resume_custom_workflow_from_config(workflow, retry_steps=["vqe"])
        assert resumed.status == "completed"
        assert resumed.acceptance_summary["accepted"] is True
        new = Path(resumed.steps[0].outputs["artifact_root"])
        assert new != old
        assert file_manifest([old]) == before
        result = json.loads((new / "result.json").read_text())
        assert result["variational_result"]["initial_point_provenance"]["checkpoint_recovery"]["replayed_evaluations"] == 6
    finally:
        _stop(process)


@pytest.mark.integration
def test_cancelled_scan_step_automatically_recovers_partial_vqe_point(tmp_path):
    base = _config(tmp_path)
    scan = tmp_path / "scan.yaml"
    scan.write_text(yaml.safe_dump({"scan": {
        "name": "process_scan", "base_config": str(base),
        "parameter": {"name": "bond_length", "kind": "bond_distance", "values": [0.7, 0.8]},
    }}), encoding="utf-8")
    workflow = tmp_path / "workflow.yaml"
    root = tmp_path / "workflow"
    workflow.write_text(yaml.safe_dump({"workflow": {
        "name": "scan_inner_recovery", "output_root": str(root),
        "steps": [{"id": "scan", "kind": "scan", "inputs": {"config": str(scan)}}],
    }}), encoding="utf-8")
    process = _start(tmp_path, "workflow", "run", "-c", workflow)
    try:
        _ready(tmp_path, process)
        old = root / "step_outputs/scan/artifact"
        request_workflow_cancel(root)
        (tmp_path / "release").write_text("release", encoding="utf-8")
        assert process.wait(timeout=20) == 130, (tmp_path / "worker.log").read_text()
        old_state = json.loads((old / "scan_checkpoint.json").read_text())
        assert len(old_state["points"]) == 0
        old_point = Path(old_state["active_point"]["artifact_root"])
        original = file_manifest([old_point])
        resumed = resume_custom_workflow_from_config(workflow, retry_steps=["scan"])
        assert resumed.status == "completed"
        new = Path(resumed.steps[0].outputs["artifact_root"])
        first = json.loads((new / "scan_result.json").read_text())["points"][0]
        first_result = json.loads((Path(first["run_artifact_root"]) / "result.json").read_text())
        assert first_result["variational_result"]["initial_point_provenance"]["checkpoint_recovery"]["replayed_evaluations"] == 6
        assert file_manifest([old_point]) == original
    finally:
        _stop(process)
