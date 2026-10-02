"""Local reviewed dispatch over the existing durable workflow engine."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from qcchem.reporting import write_result_json
from qcchem.workbench.aggregates import catalog_paths
from qcchem.workflow.common import guard_output_path_symlinks
from qcchem.workflow.custom_workflow import preview_workflow_resume_from_config, resume_custom_workflow_from_config
from qcchem.workflow.workflow_control import request_workflow_cancel, verify_manifest, workflow_status


def _loopback(host: str | None) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host or "").is_loopback
    except ValueError:
        return False


def require_local_control_request() -> None:
    """Control callbacks are local-only, including Host and Origin checks."""
    from flask import request

    address = urlsplit(request.host_url)
    origin = request.headers.get("Origin")
    if not _loopback(request.remote_addr) or not _loopback(address.hostname):
        raise ValueError("Workflow controls require a local browser on localhost or a loopback address.")
    if origin and origin != f"{address.scheme}://{address.netloc}":
        raise ValueError("Workflow control request must come from this Workbench origin.")


def workflow_control_catalog(artifact_root: Path) -> list[dict[str, Any]]:
    rows = []
    root = artifact_root.resolve()
    for checkpoint in catalog_paths(root, {"workflow_checkpoint.json"}):
        relative = checkpoint.parent.relative_to(root).as_posix()
        try:
            status = workflow_status(checkpoint.parent)
            error = None
        except (OSError, ValueError, KeyError, TypeError) as exc:
            status, error = {"status": "unavailable", "workflow_name": checkpoint.parent.name}, str(exc)
        rows.append({"value": f"artifact:{relative}", "path": checkpoint.parent,
                     "label": f"{status['workflow_name']} · {status['status']} · {relative}",
                     "status": status, "error": error})
    return rows


class WorkbenchWorkflowController:
    """Own only subprocesses dispatched by this app; never cancel by process ID."""

    def __init__(self, artifact_root: Path, workspace: Path):
        self.artifact_root = artifact_root.resolve()
        self.workspace = workspace.resolve()
        self.control_root = self.artifact_root.with_name(f".{self.artifact_root.name}.workbench-control")
        self._reviews: dict[str, dict[str, Any]] = {}
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def catalog(self) -> list[dict[str, Any]]:
        with self._lock:
            for value in self._jobs:
                self.job_status(value)
        return workflow_control_catalog(self.artifact_root)

    def _selected(self, value: str | None) -> dict[str, Any]:
        row = next((row for row in self.catalog() if row["value"] == value), None)
        if row is None:
            raise ValueError("Selected workflow is unavailable; refresh and select a checkpoint.")
        if row["error"]:
            raise ValueError(row["error"])
        return row

    def cancel(self, value: str, session_id: str) -> dict[str, Any]:
        row = self._selected(value)
        if not session_id:
            raise ValueError("Refresh the selected workflow session before cancelling.")
        return request_workflow_cancel(row["path"], reason="Requested from Workbench",
                                       expected_session_id=session_id)

    def review(self, value: str, retry_steps: list[str], session_id: str) -> dict[str, Any]:
        row = self._selected(value)
        status = row["status"]
        if not session_id or session_id != status["session_id"]:
            raise ValueError("Selected workflow session changed; refresh and review again.")
        if not isinstance(retry_steps, list) or any(not isinstance(step, str) for step in retry_steps) or len(set(retry_steps)) != len(retry_steps):
            raise ValueError("Retry steps must be a list of unique step IDs.")
        source = status.get("source_path")
        if not source:
            raise ValueError("Original workflow configuration path is unavailable; use the CLI with the original YAML.")
        preview = preview_workflow_resume_from_config(Path(source), output_dir=row["path"], retry_steps=retry_steps)
        token = uuid4().hex
        review = {**preview, "token": token, "value": value, "created_monotonic": time.monotonic()}
        with self._lock:
            self._reviews = {key: item for key, item in self._reviews.items()
                             if time.monotonic() - item["created_monotonic"] < 600}
            self._reviews[token] = review
        return review

    def start(self, token: str) -> dict[str, Any]:
        with self._lock:
            review = self._reviews.pop(token, None)
            if not review or time.monotonic() - review["created_monotonic"] >= 600:
                raise ValueError("Resume review expired or was already used; review again.")
            value = review["value"]
            job = self.job_status(value)
            if job and job["status"] in {"queued", "running"}:
                raise ValueError("This Workbench already has an active recovery job for the selected workflow.")
            current = self._selected(value)["status"]
            if current["worker_active"] or (current["session_id"], current["run_id"]) != (review["session_id"], review["run_id"]):
                raise ValueError("Workflow execution changed after review; refresh and review again.")
            preview = preview_workflow_resume_from_config(Path(review["source_path"]),
                        output_dir=Path(review["artifact_root"]), retry_steps=review["retry_steps"])
            if preview != {key: item for key, item in review.items() if key not in {"token", "value", "created_monotonic"}}:
                raise ValueError("Workflow checkpoint or inputs changed after review; review again.")
            job_id = uuid4().hex
            guard_output_path_symlinks(self.control_root, workflow_name="Workbench control")
            directory = self.control_root / job_id
            directory.mkdir(parents=True, exist_ok=False)
            request_path = directory / "request.json"
            log_path = directory / "worker.log"
            write_result_json(preview, request_path)
            receipt = {"job_id": job_id, "status": "queued", "artifact_root": preview["artifact_root"],
                       "request_path": str(request_path), "log_path": str(log_path)}
            write_result_json(receipt, directory / "receipt.json")
            env = os.environ.copy()
            package_root = str(Path(__file__).resolve().parents[2])
            env["PYTHONPATH"] = os.pathsep.join([package_root, *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])])
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                with log_path.open("xb") as log:
                    process = subprocess.Popen(
                        [sys.executable, "-m", "qcchem.workbench.workflow_controls", "--request", str(request_path)],
                        cwd=self.workspace, env=env, stdin=subprocess.DEVNULL, stdout=log,
                        stderr=subprocess.STDOUT, start_new_session=True,
                    )
            except Exception as exc:
                write_result_json({**receipt, "status": "failed", "error": f"Could not launch recovery worker: {exc}"}, directory / "receipt.json")
                raise
            self._jobs[value] = {"process": process, "directory": directory}
            return receipt

    def job_status(self, value: str | None) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(value)
            if not job:
                return None
            receipt_path = job["directory"] / "receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            returncode = job["process"].poll()
            if returncode is not None and receipt["status"] in {"queued", "running"}:
                receipt.update(status="failed", returncode=returncode, error="Recovery worker stopped without a final receipt; inspect its log and workflow checkpoint.")
                write_result_json(receipt, receipt_path)
            return receipt


def worker_main(request_path: Path) -> int:
    """Execute a server-created reviewed request with a durable terminal receipt."""
    preview = json.loads(request_path.read_text(encoding="utf-8"))
    receipt_path = request_path.with_name("receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    write_result_json({**receipt, "status": "running"}, receipt_path)
    try:
        if preview.get("review_inputs"):
            verify_manifest(preview["review_inputs"], label="reviewed workflow inputs")
        result = resume_custom_workflow_from_config(Path(preview["source_path"]),
            output_dir=Path(preview["artifact_root"]), retry_steps=preview["retry_steps"],
            expected_checkpoint_sha256=preview["checkpoint_sha256"])
        receipt.update(status=result.status, workflow_status=result.status,
                       accepted=(result.acceptance_summary or {}).get("accepted"))
        code = 0 if result.status == "completed" else 130 if result.status in {"cancelled", "interrupted"} else 2
    except BaseException as exc:
        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        code = 130 if isinstance(exc, KeyboardInterrupt) else 2
        print(receipt["error"], flush=True)
    receipt["returncode"] = code
    write_result_json(receipt, receipt_path)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute a reviewed local Workbench workflow request.")
    parser.add_argument("--request", required=True, type=Path)
    raise SystemExit(worker_main(parser.parse_args().request))
