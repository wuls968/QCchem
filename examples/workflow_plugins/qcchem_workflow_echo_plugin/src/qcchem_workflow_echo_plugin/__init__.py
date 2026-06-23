"""Example entry-point workflow plugin for QCchem."""

from __future__ import annotations

from typing import Any

from qcchem.core import WorkflowPluginDescription
from qcchem.workflow.workflow_plugins import WorkflowExecutionContext, WorkflowStepPlugin


class EchoDecisionStep(WorkflowStepPlugin):
    """A small loop-capable example step for plugin authors."""

    def describe(self) -> WorkflowPluginDescription:
        return WorkflowPluginDescription(
            name="Echo Decision",
            kind="echo_decision",
            summary="Emit a message and continue until target_iterations is reached.",
            input_schema={"required": ["target_iterations", "message"]},
            output_schema={"keys": ["message", "iteration", "continue"]},
            capabilities=["analysis_only", "loop_demo"],
            risk_notes=["Example plugin only; it does not run chemistry or hardware jobs."],
            package="qcchem-workflow-echo-plugin",
            version="0.1.0",
        )

    def validate(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> list[str]:
        if int(inputs.get("target_iterations", 1)) < 1:
            raise ValueError("target_iterations must be >= 1.")
        return []

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        target = int(inputs.get("target_iterations", 1))
        iteration = int(context.loop_iteration) + 1
        return {
            "message": str(inputs.get("message", "")),
            "iteration": iteration,
            "continue": iteration < target,
        }
