"""Native process locks without the scientific or UI execution stack."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from qcchem.workflow.computation_control import ComputationLock
from qcchem.workflow.workflow_control import WorkflowBusyError, WorkflowLock, _lock_owner

REPO = Path(__file__).resolve().parents[2]
WORKER = """
import sys, time
from pathlib import Path
from qcchem.workflow.computation_control import ComputationLock
from qcchem.workflow.workflow_control import WorkflowLock
root, ready = map(Path, sys.argv[2:4])
lock_class = ComputationLock if sys.argv[1] == 'computation' else WorkflowLock
with lock_class(root) as lock:
    lock.activate({'run_id': 'platform-run', 'session_id': 'a' * 32})
    ready.write_text('ready')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        time.sleep(0.02)
raise RuntimeError('Platform test parent did not stop its owned worker.')
"""


@pytest.mark.parametrize("kind,lock_class", [("workflow", WorkflowLock), ("computation", ComputationLock)])
def test_native_lock_excludes_another_process_and_releases_after_crash(tmp_path, kind, lock_class):
    root = tmp_path.resolve() / "output"
    ready = root.parent / "ready"
    root.mkdir()
    env = {**os.environ, "PYTHONPATH": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"}
    log_path = root.parent / "owned-worker.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "-c", WORKER, kind, str(root), str(ready)],
                                   stdout=log, stderr=subprocess.STDOUT, env=env)
    try:
        deadline = time.monotonic() + 20
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), log_path.read_text(encoding="utf-8")
        if kind == "workflow":
            # Windows must read JSON without touching its mandatory locked byte.
            owner = _lock_owner(root)
            assert owner["phase"] == "executing"
            assert owner["session_id"] == "a" * 32
        with pytest.raises(WorkflowBusyError):
            with lock_class(root, create=False):
                pytest.fail("A concurrent process acquired an owned lock.")
        process.kill()  # Only the worker created by this test.
        process.wait(timeout=5)
        with lock_class(root) as lock:
            lock.activate({"run_id": "new-run", "session_id": "b" * 32})
        owner_bytes = lock.path.read_bytes()
        assert owner_bytes[:1] == b" "
        assert len(owner_bytes) < 4096
        assert json.loads(owner_bytes)["run_id"] == "new-run"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_control_import_does_not_require_scientific_or_ui_stack():
    code = """
import builtins
original = builtins.__import__
blocked = {'pyscf', 'dash', 'qiskit', 'qiskit_aer', 'qiskit_nature', 'qiskit_algorithms'}
def restricted(name, *args, **kwargs):
    if name.split('.')[0] in blocked:
        raise ImportError(f'Scientific/UI execution deliberately unavailable: {name}')
    return original(name, *args, **kwargs)
builtins.__import__ = restricted
from qcchem.workflow.workflow_control import WorkflowLock
from qcchem.workflow.computation_control import ComputationLock
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=20,
                            env={**os.environ, "PYTHONPATH": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stdout + result.stderr
