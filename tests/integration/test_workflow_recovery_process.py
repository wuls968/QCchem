"""Real process recovery and cancellation, including preserved H2 evidence."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import pytest
import yaml

from qcchem.cli.main import main
from qcchem.workflow.workflow_control import CHECKPOINT_FILE, workflow_status

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKER = REPO_ROOT / "tests" / "helpers" / "workflow_recovery_worker.py"


def _environment():
    return {
        **os.environ, "PYTHONPATH": str(REPO_ROOT), "PYTHONDONTWRITEBYTECODE": "1",
        "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
    }


def _config(tmp_path, *, cooperative=True, chemistry=False):
    first = {"id": "first", "kind": "counter", "inputs": {"label": "first"}}
    if chemistry:
        first = {"id": "first", "kind": "run_config", "inputs": {"config": str(REPO_ROOT / "configs" / "h2_exact.yaml")}}
    path = tmp_path / "workflow.yaml"
    path.write_text(yaml.safe_dump({"workflow": {
        "name": "process_recovery", "output_root": str(tmp_path / "out"),
        "steps": [first,
                  {"id": "gate", "kind": "gate", "needs": ["first"], "inputs": {"cooperative": cooperative}},
                  {"id": "last", "kind": "counter", "needs": ["gate"], "inputs": {"label": "last"}}],
    }}), encoding="utf-8")
    return path


def _invoke(*arguments):
    return subprocess.run([sys.executable, str(WORKER), "workflow", *map(str, arguments)],
                          env=_environment(), text=True, capture_output=True, timeout=30, check=False)


def _start(tmp_path, config):
    log = (tmp_path / "worker.log").open("w", encoding="utf-8")
    process = subprocess.Popen([sys.executable, str(WORKER), "workflow", "run", "-c", str(config)],
                               env=_environment(), stdout=log, stderr=subprocess.STDOUT)
    log.close()
    return process


def _wait_ready(tmp_path, process):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if (tmp_path / "ready").exists():
            return
        if process.poll() is not None:
            pytest.fail((tmp_path / "worker.log").read_text(encoding="utf-8"))
        time.sleep(0.02)
    pytest.fail("Owned recovery test worker did not reach its gate.")


def _stop_owned(process):
    if process.poll() is None:
        process.kill()
        process.wait(timeout=5)


def _calls(tmp_path):
    return Counter(json.loads(line)["kind"] for line in (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines())


def test_crash_releases_lock_and_resume_never_duplicates_committed_work(tmp_path):
    config = _config(tmp_path)
    process = _start(tmp_path, config)
    root = tmp_path / "out"
    try:
        _wait_ready(tmp_path, process)
        status = _invoke("status", root)
        assert status.returncode == 0, status.stdout + status.stderr
        assert json.loads(status.stdout)["worker_active"] is True
        checkpoint = (root / CHECKPOINT_FILE).read_bytes()
        for arguments in (("resume", "-c", config, "--retry-step", "gate"), ("run", "-c", config, "--overwrite")):
            rejected = _invoke(*arguments)
            assert rejected.returncode == 2, rejected.stdout + rejected.stderr
            assert "already running" in rejected.stdout
        assert (root / CHECKPOINT_FILE).read_bytes() == checkpoint
        assert not list(tmp_path.glob("out.backup-*"))
        _stop_owned(process)
        interrupted = workflow_status(root)
        assert interrupted["status"] == "interrupted"
        assert interrupted["persisted_status"] == "running"
        assert interrupted["worker_active"] is False
        assert interrupted["current_step"]["step_id"] == "gate"
        rejected = _invoke("resume", "-c", config)
        assert rejected.returncode == 2
        assert "--retry-step: gate" in rejected.stdout
        assert (root / CHECKPOINT_FILE).read_bytes() == checkpoint
        partial = root / "step_outputs" / "gate" / "partial.txt"
        original = partial.read_bytes()
        (tmp_path / "release").write_text("release", encoding="utf-8")
        resumed = _invoke("resume", "-c", config, "--retry-step", "gate")
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert _calls(tmp_path) == Counter(first=1, gate=2, last=1)
        assert partial.read_bytes() == original
        completed = (root / CHECKPOINT_FILE).read_bytes()
        repeated = _invoke("resume", "-c", config)
        assert repeated.returncode == 0, repeated.stdout + repeated.stderr
        assert (root / CHECKPOINT_FILE).read_bytes() == completed
        assert _calls(tmp_path) == Counter(first=1, gate=2, last=1)
        assert len(list((root / "execution_history").iterdir())) == 1
    finally:
        _stop_owned(process)


@pytest.mark.parametrize("cooperative", [True, False])
def test_cancel_from_another_process_waits_for_a_safe_boundary(tmp_path, cooperative):
    config = _config(tmp_path, cooperative=cooperative)
    process = _start(tmp_path, config)
    root = tmp_path / "out"
    try:
        _wait_ready(tmp_path, process)
        cancel = _invoke("cancel", root, "--reason", "cancel from second process")
        assert cancel.returncode == 0, cancel.stdout + cancel.stderr
        assert json.loads(cancel.stdout)["action"] == "request_written"
        if not cooperative:
            assert process.poll() is None
            pending = workflow_status(root)
            assert pending["status"] == "cancel_requested"
            assert pending["worker_active"] is True
            (tmp_path / "release").write_text("release", encoding="utf-8")
        assert process.wait(timeout=10) == 130, (tmp_path / "worker.log").read_text(encoding="utf-8")
        result = json.loads((root / "workflow_result.json").read_text(encoding="utf-8"))
        assert result["status"] == "cancelled"
        assert result["acceptance_summary"]["accepted"] is False
        assert _calls(tmp_path) == Counter(first=1, gate=1)
        assert not (root / "step_outputs" / "last").exists()
        (tmp_path / "release").write_text("release", encoding="utf-8")
        resumed = _invoke("resume", "-c", config, "--retry-step", "gate")
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert _calls(tmp_path) == Counter(first=1, gate=2, last=1)
        assert workflow_status(root)["status"] == "completed"
        assert workflow_status(root)["cancel_requested"] is False
    finally:
        _stop_owned(process)


@pytest.mark.integration
def test_real_h2_evidence_survives_process_crash_without_recalculation(tmp_path):
    config = _config(tmp_path, chemistry=True)
    process = _start(tmp_path, config)
    root = tmp_path / "out"
    try:
        _wait_ready(tmp_path, process)
        result_file = root / "step_outputs" / "first" / "artifact" / "result.json"
        initial = result_file.read_bytes()
        result = json.loads(initial)
        assert result["energy"]["total_energy"] == pytest.approx(-1.1373060357534, abs=1e-10)
        assert result["exact_baseline"]["sector"]["num_particles"] == [1, 1]
        _stop_owned(process)
        (tmp_path / "release").write_text("release", encoding="utf-8")
        resumed = _invoke("resume", "-c", config, "--retry-step", "gate")
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        assert hashlib.sha256(result_file.read_bytes()).digest() == hashlib.sha256(initial).digest()
        events = [json.loads(line) for line in (root / "provenance.jsonl").read_text(encoding="utf-8").splitlines()]
        assert sum(event.get("event_type") == "step_started" and event.get("step_id") == "first" for event in events) == 1
        workflow = json.loads((root / "workflow_result.json").read_text(encoding="utf-8"))
        assert workflow["status"] == "completed"
        assert workflow["acceptance_summary"]["accepted"] is True
        assert workflow["summary"]["reused_steps"] == ["first"]
    finally:
        _stop_owned(process)


def test_cli_recovery_of_missing_and_legacy_checkpoints_is_readable(tmp_path, capsys):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "workflow_result.json").write_text("{}", encoding="utf-8")
    config = _config(tmp_path)
    config.write_text(yaml.safe_dump({"workflow": {
        "name": "legacy", "output_root": str(root),
        "steps": [{"id": "report", "kind": "report", "inputs": {"result_json": str(root / "result.json")}}],
    }}), encoding="utf-8")
    assert main(["workflow", "status", str(root)]) == 2
    assert "Cannot read workflow checkpoint" in capsys.readouterr().out
    assert main(["workflow", "cancel", str(root)]) == 2
    assert "Legacy bundles require a new run" in capsys.readouterr().out
    assert main(["workflow", "resume", "-c", str(config), "-o", str(root)]) == 2
    assert "Cannot read workflow checkpoint" in capsys.readouterr().out
    assert (root / "workflow_result.json").read_text(encoding="utf-8") == "{}"
