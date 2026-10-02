"""Recovery identity and locks shared by individual runs and scans."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

from qcchem.io.checkpoint import checkpoint_digest
from qcchem.io.serialization import to_primitive
from qcchem.workflow.common import guard_output_path_symlinks, guard_output_target
from qcchem.workflow.workflow_control import (
    WorkflowLock,
    file_manifest,
    implementation_identity,
    validate_checkpoint_data,
    verify_manifest,
)

ControlCheck = Callable[[], None] | None


def check_control(callback: ControlCheck) -> None:
    if callback is not None:
        callback()


class ComputationLock(WorkflowLock):
    """Use a separate stable inode from the containing custom workflow."""

    def __init__(self, root: Path, *, create: bool = True):
        super().__init__(root, create=create)
        self.path = root.with_name(f".{root.name}.computation.lock")


@contextmanager
def computation_locks(root: Path, source: Path | None) -> Iterator[None]:
    if source is not None and (source == root or source.is_relative_to(root) or root.is_relative_to(source)):
        raise ValueError("Recovery requires a separate, non-overlapping new output directory.")
    with ExitStack() as stack:
        for path in sorted({root, *([source] if source else [])}):
            guard_output_path_symlinks(path, workflow_name="Computation")
            guard_output_target(path, workflow_name="Computation")
            stack.enter_context(ComputationLock(path, create=path == root))
        yield


def computation_identity(spec: Any, paths: list[Path]) -> dict[str, Any]:
    """Bind normalized scientific configuration, file inputs, and implementation."""
    normalized = to_primitive(spec)
    normalized.pop("run", None)  # Output location is operational, not scientific.
    if hasattr(spec, "run"):
        normalized["run_seed"] = spec.run.seed
        normalized["exports"] = to_primitive(spec.run.exports)
    validate_checkpoint_data(normalized)
    return {
        "configuration_sha256": checkpoint_digest(normalized),
        "inputs": file_manifest(paths),
        "implementation": implementation_identity({}, []),
    }


def validate_recovery_identity(state: dict[str, Any], identity: dict[str, Any]) -> None:
    if state.get("identity") != identity:
        raise ValueError("Recovery inputs, configuration, source, or dependency versions changed.")
    verify_manifest(identity["inputs"], label="computation inputs")


def run_input_paths(spec: Any, source_config: str) -> list[Path]:
    paths = []
    config = Path(source_config).expanduser()
    if config.is_file():
        paths.append(config)
    if config.is_file():
        from qcchem.workflow.workflow_plugins import _config_input_paths

        paths.extend(_config_input_paths(config))

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"source_file", "structure_file", "npz_path", "resolved_path"} and item:
                    paths.append(Path(item))
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(to_primitive(spec))
    return paths
