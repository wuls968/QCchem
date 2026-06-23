"""Plugin protocol and registry for QCchem custom workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from qcchem.core import WorkflowPluginDescription, WorkflowSpec, WorkflowStepResult
from qcchem.io.serialization import to_primitive

ENTRY_POINT_GROUP = "qcchem.workflow_steps"


@dataclass(slots=True)
class WorkflowExecutionContext:
    """Runtime context passed to workflow step plugins."""

    workflow: WorkflowSpec
    output_root: Path
    step_output_dir: Path
    base_dir: Path
    parameters: dict[str, Any]
    step_results: dict[str, WorkflowStepResult]
    loop_iteration: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve_path(self, value: str | Path) -> Path:
        """Resolve a user path relative to the workflow file."""
        path = Path(value).expanduser()
        return path if path.is_absolute() else (self.base_dir / path).resolve()

    def output_path(self, name: str) -> Path:
        """Return a path inside this step's output directory."""
        return self.step_output_dir / name

    def read_json(self, value: str | Path) -> dict[str, Any]:
        """Read a JSON object from a workflow-relative path."""
        payload = json.loads(self.resolve_path(value).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object at {value}.")
        return payload


class WorkflowStepPlugin:
    """Base class for built-in and installed custom workflow steps."""

    def describe(self) -> WorkflowPluginDescription:
        """Return plugin metadata for validation, Workbench, and docs."""
        raise NotImplementedError

    def validate(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> list[str]:
        """Return validation warnings. Raise ``ValueError`` to reject inputs."""
        return []

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        """Execute the step and return JSON-safe outputs."""
        raise NotImplementedError

    def plan_next(
        self,
        result: WorkflowStepResult,
        context: WorkflowExecutionContext,
    ) -> list[dict[str, Any]]:
        """Optionally return additional validated workflow step definitions."""
        return []


def _description(
    *,
    kind: str,
    summary: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    capabilities: list[str] | None = None,
    risk_notes: list[str] | None = None,
) -> WorkflowPluginDescription:
    return WorkflowPluginDescription(
        name=kind.replace("_", " ").title(),
        kind=kind,
        summary=summary,
        input_schema={"required": list(inputs or [])},
        output_schema={"keys": list(outputs or [])},
        capabilities=list(capabilities or ["local"]),
        risk_notes=list(risk_notes or []),
    )


class BuiltinWorkflowStep(WorkflowStepPlugin):
    """Small helper for declarative built-in workflow steps."""

    kind = "builtin"
    summary = ""
    required_inputs: tuple[str, ...] = ()
    output_keys: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ("local",)
    risk_notes: tuple[str, ...] = ()

    def describe(self) -> WorkflowPluginDescription:
        return _description(
            kind=self.kind,
            summary=self.summary,
            inputs=list(self.required_inputs),
            outputs=list(self.output_keys),
            capabilities=list(self.capabilities),
            risk_notes=list(self.risk_notes),
        )

    def validate(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> list[str]:
        missing = [key for key in self.required_inputs if key not in inputs]
        if missing:
            raise ValueError(f"{self.kind} requires inputs: {', '.join(missing)}")
        return []


class RunConfigStep(BuiltinWorkflowStep):
    kind = "run_config"
    summary = "Run a QCchem run config and persist its artifact bundle."
    required_inputs = ("config",)
    output_keys = ("artifact_root", "result_json", "verification_status", "total_energy")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.runner import run_from_config

        output_dir = inputs.get("output_dir")
        result = run_from_config(
            context.resolve_path(str(inputs["config"])),
            output_dir=context.resolve_path(str(output_dir)) if output_dir else context.output_path("artifact"),
            confirm_runtime_budget=inputs.get("confirm_runtime_budget"),
        )
        return {
            "artifact_root": str(result.artifacts.root),
            "result_json": str(result.artifacts.result_json),
            "verification_status": result.verification_status,
            "total_energy": result.energy.total_energy,
            "evidence_summary": to_primitive(result.evidence_summary),
        }


class BenchmarkSuiteStep(BuiltinWorkflowStep):
    kind = "benchmark_suite"
    summary = "Run a benchmark suite config."
    required_inputs = ("config",)
    output_keys = ("artifact_root", "result_json", "total_cases")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.benchmark import run_benchmark_suite_from_config

        result = run_benchmark_suite_from_config(
            context.resolve_path(str(inputs["config"])),
            output_dir=context.resolve_path(str(inputs["output_dir"])) if inputs.get("output_dir") else context.output_path("artifact"),
            confirm_runtime_budget=inputs.get("confirm_runtime_budget"),
            include_tags=inputs.get("include_tags"),
            exclude_tags=inputs.get("exclude_tags"),
        )
        payload = to_primitive(result)
        artifact_root = payload.get("artifact_root") or str(getattr(getattr(result, "artifacts", None), "root", context.output_path("artifact")))
        return {
            "artifact_root": artifact_root,
            "result_json": str(Path(str(artifact_root)) / "benchmark_result.json"),
            "total_cases": (payload.get("summary") or {}).get("total_cases"),
            "evidence_summary": payload.get("evidence_summary"),
        }


class StudyStep(BuiltinWorkflowStep):
    kind = "study"
    summary = "Run a study config."
    required_inputs = ("config",)
    output_keys = ("artifact_root", "result_json", "total_runs")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.study import run_study_from_config

        result = run_study_from_config(
            context.resolve_path(str(inputs["config"])),
            output_dir=context.resolve_path(str(inputs["output_dir"])) if inputs.get("output_dir") else context.output_path("artifact"),
        )
        return {
            "artifact_root": str(result.artifacts.root),
            "result_json": str(result.artifacts.study_result_json),
            "total_runs": result.summary.total_runs,
            "evidence_summary": to_primitive(result.evidence_summary),
        }


class ScanStep(BuiltinWorkflowStep):
    kind = "scan"
    summary = "Run a scan config."
    required_inputs = ("config",)
    output_keys = ("artifact_root", "result_json", "total_runs")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.scan import run_scan_from_config

        result = run_scan_from_config(
            context.resolve_path(str(inputs["config"])),
            output_dir=context.resolve_path(str(inputs["output_dir"])) if inputs.get("output_dir") else context.output_path("artifact"),
        )
        return {
            "artifact_root": str(result.artifacts.root),
            "result_json": str(result.artifacts.result_json),
            "total_runs": result.summary.total_runs,
            "evidence_summary": to_primitive(result.evidence_summary),
        }


class ReportStep(BuiltinWorkflowStep):
    kind = "report"
    summary = "Render a run Markdown report from result.json."
    required_inputs = ("result_json",)
    output_keys = ("report_markdown",)

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.reporting import write_markdown_report

        result_json = context.resolve_path(str(inputs["result_json"]))
        output = context.resolve_path(str(inputs["report_markdown"])) if inputs.get("report_markdown") else context.output_path("report.md")
        output.parent.mkdir(parents=True, exist_ok=True)
        write_markdown_report(json.loads(result_json.read_text(encoding="utf-8")), output)
        return {"report_markdown": str(output)}


class CompareArtifactsStep(BuiltinWorkflowStep):
    kind = "compare_artifacts"
    summary = "Build an evidence graph from linked artifacts."
    required_inputs = ("artifacts",)
    output_keys = ("summary_json", "evidence_graph")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.reporting import write_result_json
        from qcchem.workflow.evidence_agent import summarize_evidence_artifacts

        artifacts = [str(item) for item in inputs["artifacts"]]
        graph = summarize_evidence_artifacts(artifacts, workspace_base=context.base_dir)
        output = context.output_path("evidence_graph.json")
        write_result_json(graph, output)
        return {"summary_json": str(output), "evidence_graph": graph}


class ClaimCheckStep(BuiltinWorkflowStep):
    kind = "claim_check"
    summary = "Check a scientific claim against artifact evidence."
    required_inputs = ("targets",)
    output_keys = ("claim_review_json", "claim_review_markdown", "support_level")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.claim_compiler import compile_claim_review, write_claim_review_outputs

        claim_text = str(inputs.get("claim_text") or "")
        if inputs.get("claim_file"):
            claim_text = context.resolve_path(str(inputs["claim_file"])).read_text(encoding="utf-8").strip()
        review = compile_claim_review(
            claim_text=claim_text,
            targets=[str(item) for item in inputs["targets"]],
            workspace_base=context.base_dir,
        )
        outputs = write_claim_review_outputs(review, context.step_output_dir)
        return {**outputs, "support_level": review.get("support_level"), "status": review.get("status"), "review": review}


class CapsuleValidateStep(BuiltinWorkflowStep):
    kind = "capsule_validate"
    summary = "Validate an artifact root as an Evidence Capsule."
    required_inputs = ("artifact_root",)
    output_keys = ("capsule_json", "capsule_markdown", "capsule_status")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.evidence_capsule import build_and_write_evidence_capsule

        capsule = build_and_write_evidence_capsule(context.resolve_path(str(inputs["artifact_root"])), context.step_output_dir)
        outputs = dict(capsule.get("outputs") or {})
        return {**outputs, "capsule_status": capsule.get("capsule_status"), "capsule": capsule}


class PromotionReviewStep(BuiltinWorkflowStep):
    kind = "promotion_review"
    summary = "Run the exploratory promotion gate."
    required_inputs = ("artifact", "target")
    output_keys = ("promotion_review_json", "promotion_review_markdown", "status")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.promotion import review_exploratory_promotion, write_promotion_outputs

        review = review_exploratory_promotion(
            artifact=context.resolve_path(str(inputs["artifact"])),
            target=str(inputs["target"]),
        )
        outputs = write_promotion_outputs(review, context.step_output_dir)
        return {**outputs, "status": review.get("status"), "recommended_action": review.get("recommended_action"), "review": review}


class ObjectivePlanStep(BuiltinWorkflowStep):
    kind = "objective_plan"
    summary = "Plan a Research Objective without running calculations."
    required_inputs = ("config",)
    output_keys = ("plan_json", "report_markdown")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.objective import plan_research_objective

        plan = plan_research_objective(context.resolve_path(str(inputs["config"])), context.step_output_dir)
        outputs = plan.get("outputs") or {}
        return {"plan_json": outputs.get("json"), "report_markdown": outputs.get("markdown"), "objective_plan": plan}


class ObjectiveStatusStep(BuiltinWorkflowStep):
    kind = "objective_status"
    summary = "Summarize a Research Objective status."
    required_inputs = ("target",)
    output_keys = ("status_json", "report_markdown")

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.objective import status_research_objective

        status = status_research_objective(context.resolve_path(str(inputs["target"])), context.step_output_dir)
        outputs = status.get("outputs") or {}
        return {"status_json": outputs.get("json"), "report_markdown": outputs.get("markdown"), "objective_status": status}


class RuntimeCollectStep(BuiltinWorkflowStep):
    kind = "runtime_collect"
    summary = "Collect an existing runtime sidecar result."
    required_inputs = ("artifact_root",)
    output_keys = ("artifact_root", "job_id", "status")
    capabilities = ("runtime_collect",)
    risk_notes = ("Collects an existing runtime job only; it does not submit a new job.",)

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.runtime_collect import collect_runtime_artifact

        return collect_runtime_artifact(context.resolve_path(str(inputs["artifact_root"])))


class HardwareOptimizePreviewStep(BuiltinWorkflowStep):
    kind = "hardware_optimize_preview"
    summary = "Build a local hardware optimization preview."
    required_inputs = ("config",)
    output_keys = ("plan_json", "report_markdown")
    capabilities = ("hardware_preview",)
    risk_notes = ("Preview only; real hardware submission remains outside this step.",)

    def run(self, inputs: dict[str, Any], context: WorkflowExecutionContext) -> dict[str, Any]:
        from qcchem.workflow.hardware_optimization import run_hardware_optimization_from_config

        return run_hardware_optimization_from_config(
            context.resolve_path(str(inputs["config"])),
            output_dir=context.resolve_path(str(inputs["output_dir"])) if inputs.get("output_dir") else context.step_output_dir,
            mode="preview",
        )


BUILTIN_WORKFLOW_STEP_CLASSES: tuple[type[WorkflowStepPlugin], ...] = (
    RunConfigStep,
    BenchmarkSuiteStep,
    StudyStep,
    ScanStep,
    ReportStep,
    CompareArtifactsStep,
    ClaimCheckStep,
    CapsuleValidateStep,
    PromotionReviewStep,
    ObjectivePlanStep,
    ObjectiveStatusStep,
    RuntimeCollectStep,
    HardwareOptimizePreviewStep,
)


def builtin_workflow_plugins() -> dict[str, WorkflowStepPlugin]:
    """Return built-in workflow step plugins keyed by kind."""
    plugins: dict[str, WorkflowStepPlugin] = {}
    for cls in BUILTIN_WORKFLOW_STEP_CLASSES:
        plugin = cls()
        plugins[plugin.describe().kind] = plugin
    return plugins


def _entry_points_for_group(group: str) -> list[Any]:
    eps = metadata.entry_points()
    if hasattr(eps, "select"):
        return list(eps.select(group=group))
    return list(eps.get(group, []))  # type: ignore[union-attr]


def installed_workflow_plugins() -> dict[str, WorkflowStepPlugin]:
    """Load installed workflow step plugins from Python entry points."""
    plugins: dict[str, WorkflowStepPlugin] = {}
    for entry_point in _entry_points_for_group(ENTRY_POINT_GROUP):
        loaded = entry_point.load()
        plugin = loaded() if isinstance(loaded, type) else loaded
        if not isinstance(plugin, WorkflowStepPlugin) and not all(
            hasattr(plugin, attr) for attr in ("describe", "validate", "run")
        ):
            raise TypeError(f"Workflow entry point '{entry_point.name}' does not expose a workflow step plugin.")
        description = plugin.describe()
        dist = getattr(entry_point, "dist", None)
        if dist is not None:
            description.package = dist.metadata.get("Name", entry_point.name)
            description.version = dist.version
        else:
            description.package = entry_point.name
        plugins[description.kind or entry_point.name] = plugin
    return plugins


def workflow_plugin_registry(*, include_installed: bool = True) -> dict[str, WorkflowStepPlugin]:
    """Return the merged built-in and installed workflow step registry."""
    registry = builtin_workflow_plugins()
    if include_installed:
        registry.update(installed_workflow_plugins())
    return registry


def describe_workflow_plugins(*, include_installed: bool = True) -> list[dict[str, Any]]:
    """Return JSON-safe plugin descriptions for CLI and Workbench."""
    descriptions = [plugin.describe() for plugin in workflow_plugin_registry(include_installed=include_installed).values()]
    return sorted((to_primitive(item) for item in descriptions), key=lambda item: str(item.get("kind")))
