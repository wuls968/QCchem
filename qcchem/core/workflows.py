"""Custom workflow specifications and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class WorkflowLimitsSpec:
    """Execution limits for one custom workflow run."""

    max_steps: int = 64
    max_iterations: int = 16
    max_wall_time_seconds: float | None = None


@dataclass(slots=True)
class WorkflowRetrySpec:
    """Retry policy for one workflow step."""

    max_retries: int = 0


@dataclass(slots=True)
class WorkflowStepSpec:
    """One declarative workflow step."""

    id: str
    kind: str
    plugin: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    needs: list[str] = field(default_factory=list)
    when: Any = True
    loop: dict[str, Any] = field(default_factory=dict)
    retry: WorkflowRetrySpec = field(default_factory=WorkflowRetrySpec)
    continue_on_error: bool = False
    required_for_success: bool = True
    generated_by: str | None = None


@dataclass(slots=True)
class WorkflowAcceptanceSpec:
    """Workflow-level success policy."""

    required_steps: list[str] = field(default_factory=list)
    fail_on_required_failure: bool = True


@dataclass(slots=True)
class WorkflowSpec:
    """Root custom workflow configuration."""

    version: str
    name: str
    description: str = ""
    output_root: Path = Path("artifacts/workflows/workflow")
    limits: WorkflowLimitsSpec = field(default_factory=WorkflowLimitsSpec)
    parameters: dict[str, Any] = field(default_factory=dict)
    steps: list[WorkflowStepSpec] = field(default_factory=list)
    acceptance: WorkflowAcceptanceSpec = field(default_factory=WorkflowAcceptanceSpec)
    source_path: Path | None = None


@dataclass(slots=True)
class WorkflowPluginDescription:
    """Metadata exposed by a built-in or installed workflow step plugin."""

    name: str
    kind: str
    summary: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    package: str = "qcchem"
    version: str | None = None


@dataclass(slots=True)
class WorkflowStepResult:
    """Execution result for one workflow step."""

    step_id: str
    kind: str
    status: str
    plugin: str | None = None
    attempts: int = 1
    iteration_count: int = 1
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    generated_by: str | None = None
    required_for_success: bool = True


@dataclass(slots=True)
class WorkflowRunResult:
    """Top-level custom workflow artifact payload."""

    schema_version: str
    workflow_name: str
    status: str
    artifact_root: Path
    summary: dict[str, Any]
    steps: list[WorkflowStepResult] = field(default_factory=list)
    acceptance_summary: dict[str, Any] = field(default_factory=dict)
    graph: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    source_path: Path | None = None
