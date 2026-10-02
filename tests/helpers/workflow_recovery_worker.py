"""Owned subprocess fixture for crash/cancel recovery tests; no provider calls."""

from __future__ import annotations

import json
import sys
import time

from qcchem.cli.main import main
from qcchem.core import WorkflowPluginDescription
from qcchem.workflow import custom_workflow
from qcchem.workflow.workflow_plugins import WorkflowStepPlugin, builtin_workflow_plugins


def record(context, kind):
    with (context.base_dir / "calls.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": kind, "output_dir": str(context.step_output_dir)}) + "\n")
        handle.flush()


class CounterStep(WorkflowStepPlugin):
    def describe(self):
        return WorkflowPluginDescription(name="Counter", kind="counter", summary="Count actual subprocess invocations.")

    def run(self, inputs, context):
        record(context, inputs.get("label", "counter"))
        output = context.output_path("value.txt")
        output.write_text("committed counter output", encoding="utf-8")
        return {"file": str(output)}


class GateStep(WorkflowStepPlugin):
    def describe(self):
        return WorkflowPluginDescription(name="Gate", kind="gate", summary="Wait at a controlled test boundary.")

    def run(self, inputs, context):
        record(context, "gate")
        context.output_path("partial.txt").write_text("original partial result", encoding="utf-8")
        (context.base_dir / "ready").write_text("ready", encoding="utf-8")
        deadline = time.monotonic() + 30
        while not (context.base_dir / "release").exists():
            if inputs.get("cooperative", True):
                context.check_control()
            if time.monotonic() >= deadline:
                raise RuntimeError("Test gate was not released within 30 seconds.")
            time.sleep(0.01)
        return {"done": True}


if __name__ == "__main__":
    registry = {**builtin_workflow_plugins(), "counter": CounterStep(), "gate": GateStep()}
    custom_workflow.workflow_plugin_registry = lambda: registry
    raise SystemExit(main(sys.argv[1:]))
