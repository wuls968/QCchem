"""Shared workflow helpers."""

from __future__ import annotations

import shutil
from copy import deepcopy
from pathlib import Path


def _resolve_override_target(root, dotted_path: str):
    parts = dotted_path.split(".")
    target = root
    for part in parts[:-1]:
        if isinstance(target, list):
            target = target[int(part)]
        else:
            target = getattr(target, part)
    return target, parts[-1]


def clone_spec_with_overrides(spec, overrides: dict[str, object]):
    """Deep-copy a dataclass spec and apply dotted-path overrides."""
    cloned = deepcopy(spec)
    for dotted_path, value in overrides.items():
        target, attr = _resolve_override_target(cloned, dotted_path)
        if isinstance(target, list):
            target[int(attr)] = value
        else:
            setattr(target, attr, value)
    return cloned


def resolve_artifact_root(root: Path) -> Path:
    """Resolve an artifact root relative to the repository root."""
    if root.is_absolute():
        return root
    return (Path(__file__).resolve().parents[2] / root).resolve()


def _candidate_output_root(root: Path) -> Path:
    expanded = root.expanduser()
    if expanded.is_absolute():
        return expanded
    return Path(__file__).resolve().parents[2] / expanded


def _existing_symlink_component(path: Path) -> Path | None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            return current
        if not current.exists():
            break
    return None


def guard_output_path_symlinks(root: Path, *, workflow_name: str) -> None:
    """Reject symlinked output paths before any overwrite deletion follows them."""
    candidate = _candidate_output_root(root)
    symlink = _existing_symlink_component(candidate)
    if symlink is not None:
        raise FileExistsError(
            f"{workflow_name} output path '{candidate}' uses symlink component '{symlink}'. "
            "Choose a real output directory instead of a symlink."
        )


def guard_output_target(resolved_root: Path, *, workflow_name: str) -> None:
    """Reject output roots that are too broad or would pollute source files."""
    project_root = Path(__file__).resolve().parents[2].resolve()
    project_artifacts_root = project_root / "artifacts"
    resolved_root = resolved_root.resolve()
    dangerous_targets = {
        Path(resolved_root.anchor).resolve(),
        Path.home().resolve(),
        project_root,
        project_artifacts_root,
    }
    if resolved_root in dangerous_targets:
        raise FileExistsError(
            f"{workflow_name} output path '{resolved_root}' is too broad for workflow output. "
            "Choose a dedicated child output directory."
        )
    if resolved_root.is_relative_to(project_root) and not resolved_root.is_relative_to(project_artifacts_root):
        raise FileExistsError(
            f"{workflow_name} output path '{resolved_root}' is inside the QCchem source tree outside artifacts. "
            "Choose a dedicated child under artifacts/ or an external output directory."
        )


def guard_overwrite_target(resolved_root: Path, *, workflow_name: str) -> None:
    """Backward-compatible alias for output-root safety checks."""
    guard_output_target(resolved_root, workflow_name=workflow_name)


def prepare_clean_output_root(root: Path, *, workflow_name: str, overwrite: bool) -> Path:
    """Create an aggregate workflow output root without implicit data loss."""
    guard_output_path_symlinks(root, workflow_name=workflow_name)
    resolved_root = resolve_artifact_root(root)
    guard_output_target(resolved_root, workflow_name=workflow_name)
    if resolved_root.exists():
        if not resolved_root.is_dir():
            raise FileExistsError(
                f"{workflow_name} output path '{resolved_root}' already exists and is not a directory. "
                "Choose a new output directory."
            )
        if overwrite:
            shutil.rmtree(resolved_root)
        elif any(resolved_root.iterdir()):
            raise FileExistsError(
                f"{workflow_name} output directory '{resolved_root}' already exists and is not empty. "
                "Pass overwrite=True, rerun the CLI with --overwrite, or choose a new output directory."
            )
    resolved_root.mkdir(parents=True, exist_ok=True)
    return resolved_root
