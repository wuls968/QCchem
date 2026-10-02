"""Durable, session-bound control for custom workflows.

Checkpoints and hashes detect accidental changes; they are not signatures of
untrusted artifacts. OS locks protect cooperating QCchem processes, not plugins
which write independently of the workflow protocol.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import platform
import socket
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from shutil import copyfile
from typing import Any
from uuid import uuid4

from qcchem import __version__
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json
from qcchem.workflow.common import (
    contained_output_path,
    guard_output_path_symlinks,
    guard_output_target,
    resolve_artifact_root,
)

CHECKPOINT_SCHEMA = "qcchem.workflow_checkpoint.v1"
CHECKPOINT_FILE = "workflow_checkpoint.json"


class WorkflowBusyError(FileExistsError):
    """Another process owns this workflow's execution lock."""


class WorkflowCancelledError(Exception):
    """The owner observed a cancellation request for its execution session."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    content = json.dumps(to_primitive(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_checkpoint_data(value: Any) -> None:
    """Reject credential fields before workflow payloads are persisted."""
    primitive = to_primitive(value)

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                name = key.lower().replace("-", "_")
                if name in {"token", "api_key", "apikey", "password", "secret", "private_key", "authorization"} or name.endswith(("_token", "_api_key", "_password", "_secret", "_private_key")):
                    raise ValueError(f"Workflow checkpoint cannot persist credential field '{key}'; provide credentials outside workflow payloads.")
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(primitive)
    _digest(primitive)  # Require finite, JSON-safe values as well.


def workflow_root(path: Path) -> Path:
    """Resolve and guard a dedicated output root without changing it."""
    guard_output_path_symlinks(path, workflow_name="Workflow")
    root = resolve_artifact_root(path).resolve()
    guard_output_target(root, workflow_name="Workflow")
    return root


class WorkflowLock:
    """An OS-held lock whose inode is retained across runs and overwrites."""

    def __init__(self, root: Path, *, create: bool = True):
        self.path = root.with_name(f".{root.name}.workflow.lock")
        self.create = create
        self.handle: Any = None

    def __enter__(self) -> WorkflowLock:
        guard_output_path_symlinks(self.path, workflow_name="Workflow lock")
        if self.create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        elif not self.path.exists():
            return self
        flags = os.O_RDWR | (os.O_CREAT if self.create else 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.path, flags, 0o600)
        self.handle = os.fdopen(descriptor, "r+b")
        try:
            if os.name == "nt":
                import msvcrt

                # A stable byte range also works when the file is empty.
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise WorkflowBusyError(f"Workflow is already running; execution lock: {self.path}") from exc
        if self.create:
            try:
                self._write_owner({"phase": "preparing", "pid": os.getpid(), "hostname": socket.gethostname()})
            except BaseException:
                self.__exit__()
                raise
        return self

    def _write_owner(self, owner: dict[str, Any]) -> None:
        if self.handle is None:
            raise RuntimeError("Cannot publish workflow ownership without its execution lock.")
        # Windows byte-range locks deny reads of the locked first byte. Reserve
        # that byte as whitespace so other processes can read owner JSON from
        # offset 1 without touching the lock. The exclusion range stays at 0,
        # including when an older QCchem process holds the same stable inode.
        content = b" " + json.dumps(owner).encode("utf-8")
        self.handle.seek(0)
        self.handle.write(content)
        self.handle.truncate()
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def activate(self, state: dict[str, Any]) -> None:
        """Bind lock ownership to the checkpoint only after recovery validation."""
        self._write_owner({
            "phase": "executing", "run_id": state["run_id"], "session_id": state["session_id"],
            "pid": os.getpid(), "hostname": socket.gethostname(),
        })

    def __exit__(self, *_: Any) -> None:
        if self.handle is not None:
            if os.name == "nt":
                import msvcrt

                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            self.handle.close()
            self.handle = None


def _is_active(root: Path) -> bool:
    try:
        with WorkflowLock(root, create=False):
            return False
    except WorkflowBusyError:
        return True


def _lock_owner(root: Path) -> dict[str, Any]:
    path = root.with_name(f".{root.name}.workflow.lock")
    guard_output_path_symlinks(path, workflow_name="Workflow lock")
    try:
        with path.open("rb", buffering=0) as handle:
            if os.name == "nt":
                handle.seek(1)
            payload = json.loads(handle.read())
    except (OSError, ValueError):
        return {}  # Owner publication may overlap this read; never infer a PID.
    return payload if isinstance(payload, dict) else {}


def _plugin_identities(registry: dict[str, Any], steps: list[Any]) -> dict[str, Any]:
    from qcchem.workflow.workflow_plugins import ENTRY_POINT_GROUP, _entry_points_for_group

    entry_points = _entry_points_for_group(ENTRY_POINT_GROUP)
    plugins: dict[str, Any] = {}
    for key in sorted({step.plugin or step.kind for step in steps}):
        plugin = registry[key]
        cls = type(plugin)
        try:
            source = inspect.getsourcefile(cls)
        except TypeError:
            source = None
        distributions = {}
        for entry_point in entry_points:
            module = str(getattr(entry_point, "value", "")).split(":")[0]
            dist = getattr(entry_point, "dist", None)
            if dist is not None and module.split(".")[0] == cls.__module__.split(".")[0]:
                distributions[dist.metadata.get("Name", entry_point.name)] = dist.version
        plugins[key] = {
            "class": f"{cls.__module__}.{cls.__qualname__}",
            "description": to_primitive(plugin.describe()),
            "source_sha256": _file_digest(Path(source)) if source and Path(source).is_file() else None,
            "distributions": distributions,
        }
    return plugins


def implementation_identity(registry: dict[str, Any], steps: list[Any]) -> dict[str, Any]:
    """Bind recovery to source, scientific dependencies, and selected plugins."""
    package_root = Path(__file__).resolve().parents[1]
    sources = {
        path.relative_to(package_root).as_posix(): _file_digest(path)
        for path in sorted(package_root.rglob("*.py"))
    }
    versions: dict[str, str | None] = {}
    for name in (
        "numpy", "scipy", "PyYAML", "qiskit", "qiskit-aer", "qiskit-algorithms",
        "qiskit-nature", "pyscf", "qiskit-ibm-runtime", "cudaq", "openai",
    ):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "qcchem_version": __version__,
        "source_sha256": _digest(sources),
        "python": platform.python_version(),
        "dependencies": versions,
        "plugins": _plugin_identities(registry, steps),
    }


def detected_paths(value: Any, *, base_dir: Path, root: Path, include_containers: bool = False) -> list[Path]:
    """Find existing file/path inputs or outputs without guessing missing paths."""
    paths: set[Path] = set()
    if isinstance(value, (str, Path)):
        # Scalar text is often not a path and may exceed the OS filename limit.
        if str(value) and "\x00" not in str(value) and "\n" not in str(value):
            try:
                candidate = Path(value).expanduser()
                if not candidate.is_absolute():
                    candidate = base_dir / candidate
                exists = candidate.exists() or candidate.is_symlink()
            except OSError:
                exists = False
            if exists:
                guard_output_path_symlinks(candidate, workflow_name="Workflow manifest")
                candidate = candidate.resolve()
                # Container roots include changing control/provenance files.
                if include_containers or (candidate != root and not root.is_relative_to(candidate)):
                    paths.add(candidate)
    elif isinstance(value, dict):
        for item in value.values():
            paths.update(detected_paths(item, base_dir=base_dir, root=root, include_containers=include_containers))
    elif isinstance(value, (list, tuple)):
        for item in value:
            paths.update(detected_paths(item, base_dir=base_dir, root=root, include_containers=include_containers))
    return sorted(paths)


def file_manifest(paths: list[Path]) -> dict[str, Any]:
    """Hash files and directory membership; reject symlinks and special files."""
    entries: dict[str, Any] = {}
    roots = sorted({str(path.absolute()) for path in paths})
    for raw in roots:
        path = Path(raw)
        guard_output_path_symlinks(path, workflow_name="Workflow manifest")
        if not path.exists():
            raise ValueError(f"Workflow artifact/input is missing: {path}")
        children = [path, *sorted(path.rglob("*"))] if path.is_dir() else [path]
        for child in children:
            if child.is_symlink():
                raise ValueError(f"Workflow manifest cannot follow a symlink: {child}")
            if child.is_dir():
                entries[str(child)] = {"kind": "directory"}
            elif child.is_file():
                entries[str(child)] = {
                    "kind": "file", "size": child.stat().st_size, "sha256": _file_digest(child),
                }
            else:
                raise ValueError(f"Workflow manifest requires regular files/directories: {child}")
    return {"roots": roots, "entries": entries}


def verify_manifest(manifest: dict[str, Any], *, label: str) -> None:
    try:
        current = file_manifest([Path(path) for path in manifest["roots"]])
    except (KeyError, TypeError, OSError, ValueError) as exc:
        raise ValueError(f"Cannot reuse {label}: {exc}") from exc
    if current != manifest:
        raise ValueError(f"Cannot reuse {label}: artifact/input contents or directory membership changed.")


def read_checkpoint(root: Path) -> dict[str, Any]:
    path = contained_output_path(root, CHECKPOINT_FILE)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read workflow checkpoint at {path}: {exc}. Legacy bundles require a new run.") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != CHECKPOINT_SCHEMA:
        raise ValueError(f"Unsupported workflow checkpoint at {path}.")
    checksum = payload.get("checkpoint_sha256")
    content = {key: value for key, value in payload.items() if key != "checkpoint_sha256"}
    if checksum != _digest(content):
        raise ValueError(f"Workflow checkpoint integrity check failed: {path}")
    if payload.get("artifact_root") != str(root):
        raise ValueError("Workflow checkpoint belongs to a different output root; moving bundles requires a new run.")
    for key, expected in (("steps", list), ("results", dict), ("manifests", dict), ("implementation", dict)):
        if not isinstance(payload.get(key), expected):
            raise ValueError(f"Invalid workflow checkpoint field: {key}")
    statuses = {"running", "completed", "failed", "cancelled", "interrupted"}
    workflow = payload.get("workflow")
    if payload.get("status") not in statuses or not isinstance(workflow, dict) or not isinstance(workflow.get("name"), str):
        raise ValueError("Invalid workflow checkpoint status or workflow identity.")
    if payload.get("workflow_sha256") != _digest(workflow):
        raise ValueError("Invalid workflow checkpoint configuration fingerprint.")
    for key in ("run_id", "session_id"):
        value = payload.get(key)
        if not isinstance(value, str) or len(value) != 32 or any(ch not in "0123456789abcdef" for ch in value):
            raise ValueError(f"Invalid workflow checkpoint identity: {key}")
    for key, minimum in (("executed_step_count", 0), ("session_count", 1), ("revision", 1)):
        if type(payload.get(key)) is not int or payload[key] < minimum:
            raise ValueError(f"Invalid workflow checkpoint counter: {key}")
    if any(not isinstance(step, dict) or not isinstance(step.get("id"), str) or not isinstance(step.get("kind"), str) for step in payload["steps"]):
        raise ValueError("Invalid workflow checkpoint step definitions.")
    ids = {step["id"] for step in payload["steps"]}
    if len(ids) != len(payload["steps"]) or not set(payload["results"]) <= ids:
        raise ValueError("Invalid workflow checkpoint step/result identities.")
    for key, result in payload["results"].items():
        if not isinstance(result, dict) or result.get("step_id") != key or result.get("status") not in statuses | {"skipped"}:
            raise ValueError(f"Invalid workflow checkpoint result: {key}")
    active = payload.get("active_step")
    if active is not None and (not isinstance(active, dict) or active.get("step_id") not in ids):
        raise ValueError("Invalid workflow checkpoint active step.")
    if payload.get("run_result") is not None and not isinstance(payload["run_result"], dict):
        raise ValueError("Invalid workflow checkpoint final result.")
    return payload


def _cancel_path(root: Path, state: dict[str, Any]) -> Path:
    session_id = state["session_id"]
    if not isinstance(session_id, str) or len(session_id) != 32 or any(ch not in "0123456789abcdef" for ch in session_id):
        raise ValueError("Invalid workflow checkpoint session identity.")
    return contained_output_path(root, Path("workflow_control") / f"cancel-{session_id}.json")


def workflow_status(path: Path) -> dict[str, Any]:
    """Read durable status and probe actual lock ownership without executing work."""
    root = workflow_root(path)
    for _ in range(3):
        state = read_checkpoint(root)
        active = _is_active(root)
        owner = _lock_owner(root) if active else {}
        latest = read_checkpoint(root)
        if (state["run_id"], state["session_id"]) == (latest["run_id"], latest["session_id"]):
            state = latest
            break
    else:
        raise ValueError("Workflow execution session is changing; query status again.")
    status = state["status"]
    request_recorded = _cancel_path(root, state).is_file()
    executing = active and owner.get("phase") == "executing" and owner.get("session_id") == state["session_id"] and owner.get("run_id") == state["run_id"]
    cancel_requested = request_recorded and executing and status == "running"
    if active and not executing:
        status = "preparing"
    elif status == "running" and not active:
        status = "interrupted"
    elif status == "running" and cancel_requested:
        status = "cancel_requested"
    return {
        "schema_version": "qcchem.workflow_status.v1",
        "workflow_name": state["workflow"]["name"],
        "source_path": state["workflow"].get("source_path"),
        "artifact_root": str(root),
        "run_id": state["run_id"],
        "session_id": state["session_id"],
        "status": status,
        "persisted_status": state["status"],
        "worker_active": active,
        "cancel_requested": cancel_requested,
        "cancel_request_recorded": request_recorded,
        "current_step": state.get("active_step") if status != "preparing" else None,
        "completed_steps": [key for key, result in state["results"].items() if result["status"] == "completed"],
        "pending_steps": [step["id"] for step in state["steps"] if step["id"] not in state["results"]],
        "retry_steps": [key for key, result in state["results"].items() if result["status"] in {"failed", "cancelled", "interrupted"}],
        "steps": [{
            "step_id": step["id"], "kind": step["kind"], "needs": step.get("needs", []),
            "status": state["results"].get(step["id"], {}).get("status")
            or ("running" if (state.get("active_step") or {}).get("step_id") == step["id"] else "pending"),
        } for step in state["steps"]],
        "executed_step_count": state["executed_step_count"],
        "updated_at": state["updated_at"],
        "error": state.get("error", ""),
        "checkpoint_json": str(root / CHECKPOINT_FILE),
    }


def request_workflow_cancel(
    path: Path, *, reason: str = "Requested by user", expected_session_id: str | None = None,
) -> dict[str, Any]:
    """Request cooperative cancellation for this session; never signal a PID."""
    status = workflow_status(path)
    if expected_session_id is not None and status["session_id"] != expected_session_id:
        raise ValueError("Selected workflow session changed; refresh before requesting cancellation.")
    if status["status"] == "preparing":
        raise ValueError("Workflow is preparing recovery; no execution session is active yet. Query status again before requesting cancellation.")
    if status["status"] in {"completed", "failed", "cancelled", "interrupted"}:
        return {**status, "cancel_requested": False, "action": "already_stopped"}
    root = Path(status["artifact_root"])
    state = read_checkpoint(root)
    owner = _lock_owner(root)
    if (state["session_id"] != status["session_id"] or state["run_id"] != status["run_id"]
            or owner.get("session_id") != state["session_id"] or owner.get("phase") != "executing"):
        raise ValueError("Workflow execution session changed; query its status before requesting cancellation.")
    if state["status"] != "running" or not _is_active(root):
        return {**workflow_status(root), "action": "already_stopped"}
    target = _cancel_path(root, state)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_result_json({
        "run_id": state["run_id"], "session_id": state["session_id"],
        "requested_at": now(), "reason": str(reason),
    }, target)
    return {**status, "status": "cancel_requested", "cancel_requested": True,
            "action": "request_written", "cancel_request_json": str(target)}


class WorkflowControl:
    """Checkpoint writer used only while the caller owns the execution lock."""

    def __init__(self, root: Path, state: dict[str, Any]):
        self.root = root
        self.state = state
        self.input_manifest: dict[str, Any] = {"roots": [], "entries": {}}
        self.mutates_inputs = False

    @classmethod
    def create(cls, root: Path, spec: Any, registry: dict[str, Any]) -> WorkflowControl:
        workflow = to_primitive(spec)
        validate_checkpoint_data(workflow)
        state = {
            "schema_version": CHECKPOINT_SCHEMA,
            "artifact_root": str(root),
            "run_id": uuid4().hex, "session_id": uuid4().hex, "session_count": 1,
            "created_at": now(), "status": "running", "revision": 0,
            "workflow": workflow, "workflow_sha256": _digest(workflow),
            "implementation": implementation_identity(registry, spec.steps),
            "steps": to_primitive(spec.steps), "results": {}, "manifests": {},
            "executed_step_count": 0, "active_step": None, "error": "",
            "owner": {"pid": os.getpid(), "hostname": socket.gethostname()},
        }
        control = cls(root, state)
        control.save()
        return control

    def save(self) -> None:
        self.state["updated_at"] = now()
        self.state["revision"] += 1
        content = {key: value for key, value in self.state.items() if key != "checkpoint_sha256"}
        self.state["checkpoint_sha256"] = _digest(content)
        write_result_json(self.state, contained_output_path(self.root, CHECKPOINT_FILE))

    def check_cancel(self) -> None:
        target = _cancel_path(self.root, self.state)
        if not target.exists():
            return
        try:
            request = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise WorkflowCancelledError(f"Unreadable cancel request; stopped safely: {exc}") from exc
        if not isinstance(request, dict):
            raise WorkflowCancelledError("Invalid cancel request; stopped safely.")
        if request.get("run_id") == self.state["run_id"] and request.get("session_id") == self.state["session_id"]:
            raise WorkflowCancelledError(f"Workflow cancellation requested: {request.get('reason', 'Requested by user')}")

    def begin_step(self, step_id: str) -> Path:
        step_root = contained_output_path(self.root, Path("step_outputs") / step_id)
        output = step_root
        if self.state["session_count"] > 1 or step_root.exists():
            output = contained_output_path(step_root, f"resume-{self.state['session_id']}")
            if output.exists():
                raise FileExistsError(f"Retry output directory already exists: {output}")
        self.input_manifest = {"roots": [], "entries": {}}
        self.mutates_inputs = False
        self.state["active_step"] = {"step_id": step_id, "output_dir": str(output), "iteration": 0, "attempt": 0}
        self.save()
        return output

    def record_iteration(self, iteration: int, executed: int) -> None:
        self.state["active_step"]["iteration"] = iteration
        self.state["active_step"]["attempt"] = 0
        self.state["executed_step_count"] = executed
        self.save()

    def record_attempt(self, attempt: int) -> None:
        self.state["active_step"]["attempt"] = attempt
        self.save()

    def capture_inputs(self, inputs: dict[str, Any], context: Any, plugin: Any) -> None:
        source_inputs = {key: value for key, value in inputs.items() if key not in {"output_dir", "output_root", "report_markdown"}}
        paths = detected_paths(source_inputs, base_dir=context.base_dir, root=self.root, include_containers=True)
        if hasattr(plugin, "input_paths"):
            paths.extend(context.resolve_path(path) for path in plugin.input_paths(inputs, context))
        for path in paths:
            if path.is_dir() and self.root.is_relative_to(path.resolve()):
                raise ValueError("Workflow file inputs must use dedicated bundles outside the workflow control root.")
        self.input_manifest = file_manifest(paths)
        self.mutates_inputs = bool(getattr(plugin, "mutates_inputs", False))
        self.state["active_step"]["inputs"] = self.input_manifest
        self.save()

    def commit_step(self, result: Any, spec: Any, registry: dict[str, Any]) -> None:
        step_result_path = contained_output_path(self.root, Path("step_outputs") / result.step_id / "step_result.json")
        step_result_path.parent.mkdir(parents=True, exist_ok=True)
        write_result_json(result, step_result_path)
        base_dir = spec.source_path.parent if spec.source_path is not None else Path.cwd()
        paths = detected_paths(result.outputs, base_dir=base_dir, root=self.root)
        output = Path(self.state["active_step"]["output_dir"])
        paths.extend([step_result_path, *([output] if output.exists() else [])])
        manifest = file_manifest(paths)
        self.state["steps"] = to_primitive(spec.steps)
        # Keep the initial source/environment identity even if files are edited
        # while the process runs. Only add new dynamically selected plugin kinds.
        keys = {step.plugin or step.kind for step in spec.steps}
        selected = {key: item for key, item in self.state["implementation"]["plugins"].items() if key in keys}
        new_steps = [step for step in spec.steps if (step.plugin or step.kind) not in selected]
        selected.update(_plugin_identities(registry, new_steps))
        self.state["implementation"]["plugins"] = selected
        self.state["results"][result.step_id] = to_primitive(result)
        inputs_after = file_manifest([Path(path) for path in self.input_manifest["roots"]]) if self.mutates_inputs else self.input_manifest
        self.state["manifests"][result.step_id] = {
            "inputs": inputs_after, "inputs_before": self.input_manifest, "outputs": manifest,
            "step_output_dir": str(output),
            "iteration": self.state["active_step"].get("iteration", 0),
        }
        self.state["active_step"] = None
        self.save()

    def start_resume(self, *, results: dict[str, Any], steps: list[Any]) -> None:
        recovery = dict(self.state.get("computation_recovery", {}))
        for key, manifest in self.state["manifests"].items():
            if key not in results and manifest.get("step_output_dir"):
                recovery[key] = {"output_dir": manifest["step_output_dir"], "iteration": manifest.get("iteration", 0)}
        active = self.state.get("active_step")
        if active is not None:
            recovery[active["step_id"]] = {"output_dir": active["output_dir"], "iteration": active.get("iteration", 0)}
        session = uuid4().hex
        history = contained_output_path(self.root, Path("execution_history") / session)
        history.mkdir(parents=True, exist_ok=False)
        for name in (CHECKPOINT_FILE, "workflow_result.json", "workflow_graph.json", "workflow_report.md", "registry.json"):
            source = contained_output_path(self.root, name)
            if source.is_file():
                copyfile(source, history / name)
        self.state.update({
            "session_id": session, "session_count": self.state["session_count"] + 1,
            "status": "running", "error": "", "active_step": None,
            "results": to_primitive(results), "steps": to_primitive(steps),
            "owner": {"pid": os.getpid(), "hostname": socket.gethostname()},
            "computation_recovery": recovery,
        })
        self.state.pop("run_result", None)
        self.state.pop("final_outputs", None)
        self.state["manifests"] = {key: item for key, item in self.state["manifests"].items() if key in results}
        keys = {step.plugin or step.kind for step in steps}
        self.state["implementation"]["plugins"] = {
            key: item for key, item in self.state["implementation"]["plugins"].items() if key in keys
        }
        self.save()

    def finish(self, result: Any, *, error: str = "") -> None:
        self.state["status"] = result.status
        self.state["error"] = error
        self.state["run_result"] = to_primitive(result)
        # Provenance grows across sessions and has its own append-only contract.
        paths = [contained_output_path(self.root, name) for name in (
            "workflow_result.json", "workflow_graph.json", "workflow_report.md", "registry.json",
        )]
        self.state["final_outputs"] = file_manifest(paths)
        self.save()


def workflow_fingerprint(spec: Any) -> str:
    validate_checkpoint_data(spec)
    return _digest(spec)
