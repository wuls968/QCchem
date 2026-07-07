"""Command-line interface for QCchem."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml


RELEASE_MATRIX_SUMMARY_SCHEMA_VERSION = "qcchem.release_matrix_summary.v0.1-alpha"
RELEASE_HISTORY_SUMMARY_SCHEMA_VERSION = "qcchem.release_history_summary.v0.1-alpha"
RELEASE_MATRIX_COMPARE_FIELDS = (
    "status",
    "release_status_count",
    "release_status_failed_count",
    "source_tree_release_status",
    "wheel_release_status",
    "diagnostics_manifest_count",
    "diagnostics_file_count",
    "diagnostics_present_count",
    "diagnostics_digest_count",
    "acceptance_status",
    "acceptance_fresh_count",
    "acceptance_requires_update_count",
    "acceptance_repair_plan_count",
    "failure_count",
)


def _load_attr(module_name: str, attribute: str):
    return getattr(importlib.import_module(module_name), attribute)


def load_agent_task_spec(*args, **kwargs):
    return _load_attr("qcchem.io.agent_config", "load_agent_task_spec")(*args, **kwargs)


def build_artifact_index(*args, **kwargs):
    return _load_attr("qcchem.io.artifact_index", "build_artifact_index")(*args, **kwargs)


def load_run_spec(*args, **kwargs):
    return _load_attr("qcchem.io.config", "load_run_spec")(*args, **kwargs)


def write_objective_template(*args, **kwargs):
    return _load_attr("qcchem.io.objective_config", "write_objective_template")(*args, **kwargs)


def to_primitive(*args, **kwargs):
    return _load_attr("qcchem.io.serialization", "to_primitive")(*args, **kwargs)


def write_aggregate_report(*args, **kwargs):
    return _load_attr("qcchem.reporting", "write_aggregate_report")(*args, **kwargs)


def write_markdown_report(*args, **kwargs):
    return _load_attr("qcchem.reporting", "write_markdown_report")(*args, **kwargs)


def run_agent_task_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.agent", "run_agent_task_from_config")(*args, **kwargs)


def summarize_agent_target(*args, **kwargs):
    return _load_attr("qcchem.workflow.agent", "summarize_agent_target")(*args, **kwargs)


def accept_benchmark_result(*args, **kwargs):
    return _load_attr("qcchem.workflow.acceptance", "accept_benchmark_result")(*args, **kwargs)


def compile_claim_review(*args, **kwargs):
    return _load_attr("qcchem.workflow.claim_compiler", "compile_claim_review")(*args, **kwargs)


def write_claim_review_outputs(*args, **kwargs):
    return _load_attr("qcchem.workflow.claim_compiler", "write_claim_review_outputs")(*args, **kwargs)


def append_ai_provenance_event(*args, **kwargs):
    return _load_attr("qcchem.workflow.evidence_agent", "append_ai_provenance_event")(*args, **kwargs)


def review_claims(*args, **kwargs):
    return _load_attr("qcchem.workflow.evidence_agent", "review_claims")(*args, **kwargs)


def summarize_evidence_artifacts(*args, **kwargs):
    return _load_attr("qcchem.workflow.evidence_agent", "summarize_evidence_artifacts")(*args, **kwargs)


def write_review_outputs(*args, **kwargs):
    return _load_attr("qcchem.workflow.evidence_agent", "write_review_outputs")(*args, **kwargs)


def build_and_write_evidence_capsule(*args, **kwargs):
    return _load_attr("qcchem.workflow.evidence_capsule", "build_and_write_evidence_capsule")(*args, **kwargs)


def run_benchmark_suite_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.benchmark", "run_benchmark_suite_from_config")(*args, **kwargs)


def accept_campaign_result(*args, **kwargs):
    return _load_attr("qcchem.workflow.campaign", "accept_campaign_result")(*args, **kwargs)


def report_campaign_result(*args, **kwargs):
    return _load_attr("qcchem.workflow.campaign", "report_campaign_result")(*args, **kwargs)


def run_campaign_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.campaign", "run_campaign_from_config")(*args, **kwargs)


def report_custom_workflow_result(*args, **kwargs):
    return _load_attr("qcchem.workflow.custom_workflow", "report_custom_workflow_result")(*args, **kwargs)


def run_custom_workflow_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.custom_workflow", "run_custom_workflow_from_config")(*args, **kwargs)


def validate_workflow_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.custom_workflow", "validate_workflow_from_config")(*args, **kwargs)


def workflow_plugins_summary(*args, **kwargs):
    return _load_attr("qcchem.workflow.custom_workflow", "workflow_plugins_summary")(*args, **kwargs)


def write_workflow_template(*args, **kwargs):
    return _load_attr("qcchem.workflow.custom_workflow", "write_workflow_template")(*args, **kwargs)


def run_hardware_optimization_from_config(*args, **kwargs):
    return _load_attr(
        "qcchem.workflow.hardware_optimization",
        "run_hardware_optimization_from_config",
    )(*args, **kwargs)


def plan_research_objective(*args, **kwargs):
    return _load_attr("qcchem.workflow.objective", "plan_research_objective")(*args, **kwargs)


def status_research_objective(*args, **kwargs):
    return _load_attr("qcchem.workflow.objective", "status_research_objective")(*args, **kwargs)


def review_exploratory_promotion(*args, **kwargs):
    return _load_attr("qcchem.workflow.promotion", "review_exploratory_promotion")(*args, **kwargs)


def write_promotion_outputs(*args, **kwargs):
    return _load_attr("qcchem.workflow.promotion", "write_promotion_outputs")(*args, **kwargs)


def run_release_audit_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.release_audit", "run_release_audit_from_config")(*args, **kwargs)


def build_release_status_summary(*args, **kwargs):
    return _load_attr("qcchem.workflow.release_status", "build_release_status_summary")(*args, **kwargs)


def verify_release_diagnostics_artifacts(*args, **kwargs):
    return _load_attr("qcchem.workflow.release_status", "verify_release_diagnostics_artifacts")(*args, **kwargs)


def write_release_artifact_acceptance_summary_from_config(*args, **kwargs):
    return _load_attr(
        "qcchem.workflow.release_acceptance",
        "write_release_artifact_acceptance_summary_from_config",
    )(*args, **kwargs)


def preview_release_artifact_acceptance_summary_from_config(*args, **kwargs):
    return _load_attr(
        "qcchem.workflow.release_acceptance",
        "preview_release_artifact_acceptance_summary_from_config",
    )(*args, **kwargs)


def release_acceptance_status_report_from_config(*args, **kwargs):
    return _load_attr(
        "qcchem.workflow.release_acceptance",
        "release_acceptance_status_report_from_config",
    )(*args, **kwargs)


def release_acceptance_status_contract_failures(*args, **kwargs):
    return _load_attr(
        "qcchem.workflow.release_acceptance",
        "release_acceptance_status_contract_failures",
    )(*args, **kwargs)


def run_workbench_smoke_from_docs(*args, **kwargs):
    return _load_attr("qcchem.workbench.smoke", "run_workbench_smoke_from_docs")(*args, **kwargs)


def run_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.runner", "run_from_config")(*args, **kwargs)


def collect_runtime_artifact(*args, **kwargs):
    return _load_attr("qcchem.workflow.runtime_collect", "collect_runtime_artifact")(*args, **kwargs)


def run_scan_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.scan", "run_scan_from_config")(*args, **kwargs)


def run_study_from_config(*args, **kwargs):
    return _load_attr("qcchem.workflow.study", "run_study_from_config")(*args, **kwargs)


def build_electronic_structure_context(*args, **kwargs):
    return _load_attr("qcchem.chem.problem_builder", "build_electronic_structure_context")(*args, **kwargs)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qcchem", description="QCchem quantum chemistry workflow CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a QCchem calculation from YAML config.")
    run_parser.add_argument("-c", "--config", type=Path, required=True, help="Path to YAML config.")
    run_parser.add_argument("-o", "--output-dir", type=Path, help="Override artifact output directory.")
    run_parser.add_argument(
        "--confirm-runtime-budget",
        help="Required before any config-requested real IBM Runtime submission can proceed.",
    )

    report_parser = subparsers.add_parser("report", help="Regenerate a run Markdown report from result.json.")
    report_parser.add_argument("result_json", type=Path, help="Path to result.json.")
    report_parser.add_argument("-o", "--output", type=Path, help="Optional report output path.")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a config and print a summary.")
    inspect_parser.add_argument("-c", "--config", type=Path, required=True, help="Path to YAML config.")

    active_space_parser = subparsers.add_parser("active-space", help="Active-space recommendation commands.")
    active_space_subparsers = active_space_parser.add_subparsers(dest="active_space_command", required=True)
    active_space_recommend = active_space_subparsers.add_parser(
        "recommend",
        help="Preview an auditable active-space recommendation without running the quantum solver.",
    )
    active_space_recommend.add_argument("-c", "--config", type=Path, required=True)
    active_space_recommend.add_argument("-o", "--output", type=Path)
    active_space_recommend.add_argument("--emit-yaml-patch", action="store_true")

    study_parser = subparsers.add_parser("study", help="Study workflow commands.")
    study_subparsers = study_parser.add_subparsers(dest="study_command", required=True)
    study_run = study_subparsers.add_parser("run", help="Run a study from YAML config.")
    study_run.add_argument("-c", "--config", type=Path, required=True)
    study_run.add_argument("-o", "--output-dir", type=Path)
    study_run.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty study output directory.",
    )
    study_report = study_subparsers.add_parser("report", help="Regenerate a study report from JSON.")
    study_report.add_argument("result_json", type=Path)
    study_report.add_argument("-o", "--output", type=Path)

    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark workflow commands.")
    benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
    benchmark_run = benchmark_subparsers.add_parser("run", help="Run a benchmark suite from YAML config.")
    benchmark_run.add_argument("-c", "--config", type=Path, required=True)
    benchmark_run.add_argument("-o", "--output-dir", type=Path)
    benchmark_run.add_argument(
        "--include-tag",
        action="append",
        default=[],
        help="Run only benchmark cases carrying this tag. Repeat to include any of several tags.",
    )
    benchmark_run.add_argument(
        "--exclude-tag",
        action="append",
        default=[],
        help="Skip benchmark cases carrying this tag. Repeat to exclude several tags.",
    )
    benchmark_run.add_argument(
        "--confirm-runtime-budget",
        help="Required before any benchmark case can submit a real IBM Runtime job.",
    )
    benchmark_run.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty benchmark output directory.",
    )
    benchmark_report = benchmark_subparsers.add_parser("report", help="Regenerate a benchmark report from JSON.")
    benchmark_report.add_argument("result_json", type=Path)
    benchmark_report.add_argument("-o", "--output", type=Path)
    benchmark_accept = benchmark_subparsers.add_parser("accept", help="Evaluate benchmark acceptance from JSON.")
    benchmark_accept.add_argument("result_json", type=Path)
    benchmark_accept.add_argument("-o", "--output", type=Path)

    artifacts_parser = subparsers.add_parser("artifacts", help="Artifact index commands.")
    artifacts_subparsers = artifacts_parser.add_subparsers(dest="artifacts_command", required=True)
    artifacts_index = artifacts_subparsers.add_parser("index", help="Build a normalized artifact index.")
    artifacts_index.add_argument("artifact_root", type=Path, nargs="?", default=Path("artifacts"))
    artifacts_index.add_argument("-o", "--output", type=Path)
    artifacts_capsule = artifacts_subparsers.add_parser("capsule", help="Validate an artifact root as an evidence capsule.")
    artifacts_capsule.add_argument("artifact_root", type=Path, help="Artifact root, or artifacts root with --recursive.")
    artifacts_capsule.add_argument("-o", "--output-dir", type=Path)
    artifacts_capsule.add_argument("--recursive", action="store_true", help="Validate every indexed artifact under the root.")

    objective_parser = subparsers.add_parser("objective", help="Research Objective planning commands.")
    objective_subparsers = objective_parser.add_subparsers(dest="objective_command", required=True)
    objective_init = objective_subparsers.add_parser("init", help="Write a Research Objective YAML template.")
    objective_init.add_argument("--name", required=True)
    objective_init.add_argument("--claim", required=True)
    objective_init.add_argument("-o", "--output", type=Path, required=True)
    objective_plan = objective_subparsers.add_parser("plan", help="Plan a Research Objective without running calculations.")
    objective_plan.add_argument("-c", "--config", type=Path, required=True)
    objective_plan.add_argument("-o", "--output-dir", type=Path, required=True)
    objective_status = objective_subparsers.add_parser("status", help="Summarize Research Objective status.")
    objective_status.add_argument("target", type=Path, nargs="?", help="Objective artifact root or objective YAML.")
    objective_status.add_argument("-c", "--config", type=Path, help="Objective YAML.")
    objective_status.add_argument("-o", "--output-dir", type=Path)

    claim_parser = subparsers.add_parser("claim", help="Claim compiler commands.")
    claim_subparsers = claim_parser.add_subparsers(dest="claim_command", required=True)
    claim_check = claim_subparsers.add_parser("check", help="Check a scientific claim against artifact evidence.")
    claim_text_group = claim_check.add_mutually_exclusive_group(required=True)
    claim_text_group.add_argument("--claim", help="Claim text to check.")
    claim_text_group.add_argument("--claim-file", type=Path, help="Text file containing the claim.")
    claim_check.add_argument("--target", action="append", required=True, help="Artifact root or result JSON. Repeat for multiple targets.")
    claim_check.add_argument("-o", "--output-dir", type=Path, required=True)

    promote_parser = subparsers.add_parser("promote", help="Promotion gate commands.")
    promote_subparsers = promote_parser.add_subparsers(dest="promote_command", required=True)
    promote_exploratory = promote_subparsers.add_parser(
        "exploratory",
        help="Review whether exploratory evidence can enter a candidate promotion path.",
    )
    promote_exploratory.add_argument("--artifact", type=Path, required=True)
    promote_exploratory.add_argument("--target", required=True)
    promote_exploratory.add_argument("-o", "--output-dir", type=Path, required=True)

    campaign_parser = subparsers.add_parser("campaign", help="Artifact-driven campaign workflow commands.")
    campaign_subparsers = campaign_parser.add_subparsers(dest="campaign_command", required=True)
    campaign_run = campaign_subparsers.add_parser("run", help="Run a campaign from YAML config.")
    campaign_run.add_argument("-c", "--config", type=Path, required=True)
    campaign_run.add_argument("-o", "--output-dir", type=Path)
    campaign_run.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty campaign output directory.",
    )
    campaign_report = campaign_subparsers.add_parser("report", help="Regenerate a campaign report from JSON.")
    campaign_report.add_argument("result_json", type=Path)
    campaign_report.add_argument("-o", "--output", type=Path)
    campaign_accept = campaign_subparsers.add_parser("accept", help="Evaluate campaign acceptance from JSON.")
    campaign_accept.add_argument("result_json", type=Path)
    campaign_accept.add_argument("-o", "--output", type=Path)

    scan_parser = subparsers.add_parser("scan", help="Scan workflow commands.")
    scan_subparsers = scan_parser.add_subparsers(dest="scan_command", required=True)
    scan_run = scan_subparsers.add_parser("run", help="Run a scan from YAML config.")
    scan_run.add_argument("-c", "--config", type=Path, required=True)
    scan_run.add_argument("-o", "--output-dir", type=Path)
    scan_run.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty scan output directory.",
    )
    scan_report = scan_subparsers.add_parser("report", help="Regenerate a scan report from JSON.")
    scan_report.add_argument("result_json", type=Path)
    scan_report.add_argument("-o", "--output", type=Path)

    exploratory_parser = subparsers.add_parser("exploratory", help="Exploratory workflow commands.")
    exploratory_subparsers = exploratory_parser.add_subparsers(dest="exploratory_command", required=True)
    exploratory_run = exploratory_subparsers.add_parser("run", help="Run an exploratory QCchem calculation.")
    exploratory_run.add_argument("-c", "--config", type=Path, required=True)
    exploratory_run.add_argument("-o", "--output-dir", type=Path)
    exploratory_run.add_argument(
        "--confirm-runtime-budget",
        help="Required before any exploratory config can submit a real IBM Runtime job.",
    )

    workbench_parser = subparsers.add_parser("workbench", help="Local QCchem visual workbench.")
    workbench_subparsers = workbench_parser.add_subparsers(dest="workbench_command", required=True)
    workbench_serve = workbench_subparsers.add_parser("serve", help="Serve the local QCchem workbench.")
    workbench_serve.add_argument("--host", default="127.0.0.1")
    workbench_serve.add_argument("--port", type=int, default=8050)
    workbench_serve.add_argument("--debug", action="store_true")
    workbench_serve.add_argument(
        "--artifact-root",
        type=Path,
        help="Artifact root to index; defaults to ./artifacts when present.",
    )
    workbench_smoke = workbench_subparsers.add_parser(
        "smoke",
        help="Validate the documented Workbench showcase routes without starting a server.",
    )
    workbench_smoke.add_argument("--docs", type=Path, default=Path("docs") / "workbench.md")
    workbench_smoke.add_argument(
        "--artifact-root",
        type=Path,
        help="Artifact root to render page evidence from; defaults to ./artifacts when present.",
    )
    workbench_smoke.add_argument("-o", "--output", type=Path, help="Optional JSON summary output path.")

    runtime_parser = subparsers.add_parser("runtime", help="Runtime artifact commands.")
    runtime_subparsers = runtime_parser.add_subparsers(dest="runtime_command", required=True)
    runtime_collect = runtime_subparsers.add_parser(
        "collect",
        help="Poll a submitted runtime job and merge returned data back into an artifact directory.",
    )
    runtime_collect.add_argument("artifact_root", type=Path, help="Artifact directory containing runtime_submission.json.")

    release_parser = subparsers.add_parser("release", help="Release-readiness commands.")
    release_subparsers = release_parser.add_subparsers(dest="release_command", required=True)
    release_audit = release_subparsers.add_parser("audit", help="Run the Trust-First release readiness audit.")
    release_audit.add_argument("-c", "--config", type=Path, required=True)
    release_audit.add_argument("-o", "--output-dir", type=Path)
    release_audit.add_argument("--repo-root", type=Path, help="Repository root to audit; defaults to current directory.")
    release_status = release_subparsers.add_parser(
        "status",
        help="Summarize existing release audit handoff outputs without rerunning the audit.",
    )
    release_status.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("artifacts") / "release_audit",
        help="Directory containing release_readiness.json and release_handoff.json.",
    )
    release_status.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root used to resolve a relative --audit-dir.",
    )
    release_status.add_argument("-o", "--output", type=Path, help="Optional compact JSON status output path.")
    release_status.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 2 when the summarized release audit status is not passed.",
    )
    release_verify_artifacts = release_subparsers.add_parser(
        "verify-artifacts",
        help="Verify downloaded CI release diagnostic artifacts without network access.",
    )
    release_verify_artifacts.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Directory produced by downloading qcchem-release-diagnostics-* artifacts.",
    )
    release_verify_artifacts.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional JSON verification report output path.",
    )
    release_collect_evidence = release_subparsers.add_parser(
        "collect-evidence",
        help="Create a post-download release evidence handoff from CI diagnostic artifacts.",
    )
    release_collect_evidence.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="Directory produced by downloading qcchem-release-diagnostics-* artifacts.",
    )
    release_collect_evidence.add_argument(
        "--docs",
        type=Path,
        default=Path("docs") / "workbench.md",
        help="Workbench documentation containing the Browser Smoke Checklist.",
    )
    release_collect_evidence.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Directory for release_artifact_verification.json, release_matrix_summary.json, "
            "workbench_smoke.json, release_evidence_summary.json, and release_evidence_handoff.md; "
            "defaults to --artifact-dir."
        ),
    )
    release_collect_evidence.add_argument(
        "--history-root",
        type=Path,
        help=(
            "Retained release-evidence history root. Outputs are written under "
            "<history-root>/<history-label>, and --baseline-search-root defaults to this root."
        ),
    )
    release_collect_evidence.add_argument(
        "--history-label",
        help=(
            "Single directory name for --history-root output; defaults to a UTC timestamp. "
            "Rejected when --history-root is not set."
        ),
    )
    release_collect_evidence.add_argument(
        "--baseline-summary",
        type=Path,
        help="Optional release_matrix_summary.json from a previous collect-evidence run.",
    )
    release_collect_evidence.add_argument(
        "--baseline-search-root",
        type=Path,
        help=(
            "Optional retained release-evidence directory tree. When --baseline-summary is omitted, "
            "the newest prior release_matrix_summary.json under this root is used as the matrix baseline."
        ),
    )
    release_fetch_ci_evidence = release_subparsers.add_parser(
        "fetch-ci-evidence",
        help="Download a GitHub Actions run's release diagnostics and retain post-CI evidence.",
    )
    release_fetch_ci_evidence.add_argument(
        "--run-id",
        required=True,
        help="GitHub Actions run id to download with gh run download.",
    )
    release_fetch_ci_evidence.add_argument(
        "--repo",
        help="Optional GitHub repository passed to gh, for example owner/name.",
    )
    release_fetch_ci_evidence.add_argument(
        "--download-dir",
        type=Path,
        help="Optional empty directory for downloaded CI artifacts; defaults to a retained /tmp directory.",
    )
    release_fetch_ci_evidence.add_argument(
        "--docs",
        type=Path,
        default=Path("docs") / "workbench.md",
        help="Workbench documentation containing the Browser Smoke Checklist.",
    )
    release_fetch_ci_evidence.add_argument(
        "--history-root",
        type=Path,
        required=True,
        help="Retained release-evidence history root passed to collect-evidence.",
    )
    release_fetch_ci_evidence.add_argument(
        "--history-label",
        help="Single directory name for retained evidence; defaults to --run-id.",
    )
    release_fetch_ci_evidence.add_argument(
        "--baseline-summary",
        type=Path,
        help="Optional explicit release_matrix_summary.json baseline for collect-evidence.",
    )
    release_fetch_ci_evidence.add_argument(
        "--baseline-search-root",
        type=Path,
        help="Optional baseline search root; defaults to --history-root.",
    )
    release_history = release_subparsers.add_parser(
        "history",
        help="Inspect retained release-evidence history directories.",
    )
    release_history_subparsers = release_history.add_subparsers(dest="release_history_command", required=True)
    release_history_summarize = release_history_subparsers.add_parser(
        "summarize",
        help="Summarize retained release-evidence runs, baselines, and matrix deltas.",
    )
    release_history_summarize.add_argument(
        "--history-root",
        type=Path,
        required=True,
        help="Directory containing one retained release-evidence subdirectory per run.",
    )
    release_history_summarize.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional JSON summary output path.",
    )
    release_history_summarize.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 2 when the retained history summary status is not passed.",
    )
    release_evidence_handoff = release_subparsers.add_parser(
        "evidence-handoff",
        help="Write a local CI release evidence handoff from generated diagnostics.",
    )
    release_evidence_handoff.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("artifacts") / "release_audit",
        help="Directory containing release_readiness.json and release_handoff.json.",
    )
    release_evidence_handoff.add_argument(
        "--workbench-smoke",
        type=Path,
        default=Path("artifacts") / "workbench_smoke.json",
        help="Workbench smoke JSON produced by qcchem workbench smoke.",
    )
    release_evidence_handoff.add_argument(
        "--acceptance-status",
        type=Path,
        default=Path("/tmp") / "qcchem-release-acceptance-status.json",
        help="Release acceptance status JSON produced by qcchem release acceptance-status.",
    )
    release_evidence_handoff.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts") / "release_evidence",
        help="Directory for release_evidence_summary.json and release_evidence_handoff.md.",
    )
    release_evidence_handoff.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 2 when the local release evidence handoff status is not passed.",
    )
    release_accept = release_subparsers.add_parser(
        "accept-artifact",
        help="Write a release-bound acceptance_summary.json for one manifest artifact.",
    )
    release_accept.add_argument("-c", "--config", type=Path, required=True)
    release_accept.add_argument("--name", required=True, help="Artifact or artifact-backed exploratory asset name.")
    release_accept.add_argument("--repo-root", type=Path, help="Repository root; defaults to the manifest workspace.")
    release_accept.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing sibling acceptance_summary.json.",
    )
    release_accept.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the sidecar payload and current sidecar status without writing.",
    )
    release_accept.add_argument(
        "--boundary",
        action="append",
        default=[],
        help="Release-boundary note to record in the sidecar. Repeat for multiple notes.",
    )
    release_acceptance_status = release_subparsers.add_parser(
        "acceptance-status",
        help="Report whether manifest-bound release acceptance sidecars are fresh.",
    )
    release_acceptance_status.add_argument("-c", "--config", type=Path, required=True)
    release_acceptance_status.add_argument("--repo-root", type=Path, help="Repository root; defaults to the manifest workspace.")
    release_acceptance_status.add_argument("-o", "--output", type=Path, help="Optional JSON status output path.")
    release_acceptance_status.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 2 when any manifest-bound sidecar is missing, stale, unreadable, or blocked.",
    )
    release_acceptance_status.add_argument(
        "--repair-plan",
        action="store_true",
        help="Print read-only preview and refresh commands for non-fresh sidecars.",
    )

    validation_parser = subparsers.add_parser("validation", help="Validation harness commands.")
    validation_subparsers = validation_parser.add_subparsers(dest="validation_command", required=True)
    validation_qmmm = validation_subparsers.add_parser(
        "qmmm",
        help="Run the QM/MM environment-embedding validation harness.",
    )
    validation_qmmm.add_argument("--profile", choices=["smoke", "full"], default="smoke")
    validation_qmmm.add_argument("-o", "--output-dir", type=Path, required=True)
    validation_pbc_qmmm = validation_subparsers.add_parser(
        "pbc-qmmm",
        help="Run the Gamma-only PBC/PBC-QMMM Ewald validation harness.",
    )
    validation_pbc_qmmm.add_argument("--profile", choices=["smoke", "full"], default="smoke")
    validation_pbc_qmmm.add_argument("-o", "--output-dir", type=Path, required=True)

    hardware_parser = subparsers.add_parser("hardware", help="Hardware optimization workflow commands.")
    hardware_subparsers = hardware_parser.add_subparsers(dest="hardware_command", required=True)
    hardware_optimize = hardware_subparsers.add_parser(
        "optimize",
        help="Preview, submit, or collect a budget-guarded hardware optimization campaign.",
    )
    hardware_optimize.add_argument("-c", "--config", type=Path, required=True)
    hardware_optimize.add_argument("-o", "--output-dir", type=Path)
    hardware_mode = hardware_optimize.add_mutually_exclusive_group(required=True)
    hardware_mode.add_argument("--preview", action="store_true", help="Build local candidate ranking only.")
    hardware_mode.add_argument("--submit", action="store_true", help="Submit one guarded real runtime job.")
    hardware_mode.add_argument("--collect", action="store_true", help="Collect submitted runtime jobs.")
    hardware_optimize.add_argument(
        "--confirm-runtime-budget",
        help="Required for --submit when the config requests action-time confirmation.",
    )

    workflow_parser = subparsers.add_parser("workflow", help="Custom workflow engine commands.")
    workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command", required=True)
    workflow_validate = workflow_subparsers.add_parser("validate", help="Validate a custom workflow YAML file.")
    workflow_validate.add_argument("-c", "--config", type=Path, required=True)
    workflow_run = workflow_subparsers.add_parser("run", help="Run a custom workflow YAML file.")
    workflow_run.add_argument("-c", "--config", type=Path, required=True)
    workflow_run.add_argument("-o", "--output-dir", type=Path)
    workflow_run.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty workflow output directory.",
    )
    workflow_report = workflow_subparsers.add_parser("report", help="Regenerate a workflow Markdown report.")
    workflow_report.add_argument("result_json", type=Path)
    workflow_report.add_argument("-o", "--output", type=Path)
    workflow_plugins = workflow_subparsers.add_parser("plugins", help="List built-in and installed workflow step plugins.")
    workflow_plugins.add_argument("--builtins-only", action="store_true", help="List only QCchem built-in workflow step plugins.")
    workflow_template = workflow_subparsers.add_parser("template", help="Write a starter custom workflow YAML file.")
    workflow_template.add_argument("-o", "--output", type=Path, required=True)

    agent_parser = subparsers.add_parser("agent", help="Agent-friendly QCchem task commands.")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command", required=True)
    agent_validate = agent_subparsers.add_parser("validate-task", help="Validate one agent task file.")
    agent_validate.add_argument("task_file", type=Path, help="Path to one agent task YAML/JSON file.")
    agent_run = agent_subparsers.add_parser("run-task", help="Run one agent task file and emit JSON summary.")
    agent_run.add_argument("task_file", type=Path, help="Path to one agent task YAML/JSON file.")
    agent_summarize = agent_subparsers.add_parser(
        "summarize",
        help="Summarize a hardware runtime campaign directory or summary JSON into agent-friendly outputs.",
    )
    agent_summarize.add_argument("target", type=Path, help="Hardware suite artifact root or summary JSON path.")

    ai_parser = subparsers.add_parser("ai", help="AI workspace commands.")
    ai_subparsers = ai_parser.add_subparsers(dest="ai_command", required=True)
    ai_draft = ai_subparsers.add_parser("draft-ticket", help="Draft an AI workspace task ticket.")
    ai_draft.add_argument("--provider-config", type=Path, required=True, help="Path to AI provider YAML config.")
    ai_draft.add_argument(
        "--task-type",
        choices=["analysis", "execution", "delivery"],
        required=True,
        help="Ticket category to draft.",
    )
    ai_draft.add_argument("--request", required=True, help="Free-form user request to structure into a ticket.")
    ai_draft.add_argument(
        "--artifact",
        action="append",
        default=[],
        help="Linked artifact path. Repeat for multiple artifacts.",
    )
    ai_run = ai_subparsers.add_parser("run-ticket", help="Run an accepted AI workspace ticket.")
    ai_run.add_argument("ticket", type=Path, help="Path to one AI workspace ticket JSON file.")
    ai_summarize = ai_subparsers.add_parser(
        "summarize-evidence",
        help="Summarize linked QCchem artifacts into an evidence graph.",
    )
    ai_summarize.add_argument(
        "--artifact",
        action="append",
        required=True,
        help="QCchem artifact directory or summary JSON path. Repeat for multiple artifacts.",
    )
    ai_summarize.add_argument("-o", "--output", type=Path, help="Optional JSON output path.")
    ai_review = ai_subparsers.add_parser(
        "review",
        help="Review claims against QCchem artifact evidence boundaries.",
    )
    ai_review.add_argument(
        "--target",
        action="append",
        required=True,
        help="QCchem artifact directory or summary JSON path. Repeat for multiple targets.",
    )
    ai_review.add_argument("--claim", help="Claim text to review. Defaults to artifact claims.")
    ai_review.add_argument("-o", "--output-dir", type=Path, help="Optional output directory for review files.")
    return parser


def _acceptance_exit_code(summary: dict[str, object] | None) -> int:
    if not isinstance(summary, dict):
        return 0
    policy = summary.get("policy")
    strict_exit_code = bool(policy.get("strict_exit_code")) if isinstance(policy, dict) else False
    return 2 if strict_exit_code and not bool(summary.get("accepted")) else 0


def _write_aggregate_from_json(result_json: Path, output: Path | None, *, kind: str) -> int:
    payload = json.loads(result_json.read_text(encoding="utf-8"))
    output_path = output or result_json.with_suffix(".md")
    write_aggregate_report(payload, output_path, kind=kind)
    print(f"{kind.capitalize()} report written to {output_path}")
    return 0


def _run_workbench_command(host: str, port: int, debug: bool, artifact_root: Path | None = None) -> int:
    try:
        workbench_server = importlib.import_module("qcchem.workbench.server")
    except ModuleNotFoundError as exc:
        optional_ui_modules = {"dash", "plotly", "pandas"}
        if exc.name not in optional_ui_modules:
            raise
        print('QCchem workbench requires optional UI dependencies. Install with: pip install -e ".[ui]"')
        return 2

    try:
        if hasattr(workbench_server, "prepare_workbench") and hasattr(workbench_server, "launch_app"):
            app, summary = workbench_server.prepare_workbench(
                host=host,
                port=port,
                debug=debug,
                artifact_root=artifact_root,
            )
            workbench_server.print_workbench_startup(summary)
            workbench_server.launch_app(app, host=host, port=port, debug=debug)
            return 0

        summary = workbench_server.serve_workbench(host=host, port=port, debug=debug, artifact_root=artifact_root)
    except (OSError, ValueError) as exc:
        print(f"QCchem workbench rejected: {exc}")
        return 2
    workbench_server.print_workbench_startup(summary)
    return 0


def _workbench_smoke_failed_checks(item: dict[str, object]) -> str:
    failed_checks = item.get("failed_checks")
    if isinstance(failed_checks, list):
        names = [str(name) for name in failed_checks]
    else:
        checks = item.get("checks")
        names = [str(name) for name, passed in checks.items() if not passed] if isinstance(checks, dict) else []
    return ",".join(names) if names else "unknown"


def _print_workbench_smoke_failed_summary(summary: dict[str, object], *, limit: int = 8) -> None:
    failed_checks = summary.get("failed_checks")
    if not isinstance(failed_checks, list) or not failed_checks:
        return
    names = [str(name) for name in failed_checks]
    line = ", ".join(names[:limit])
    remaining = len(names) - limit
    if remaining > 0:
        line = f"{line}, ... {remaining} more"
    print(f"Failed checks: {line}")


def _run_workbench_smoke_command(docs_path: Path, output: Path | None, artifact_root: Path | None = None) -> int:
    try:
        summary = run_workbench_smoke_from_docs(docs_path, artifact_root=artifact_root)
    except ModuleNotFoundError as exc:
        optional_ui_modules = {"dash", "plotly", "pandas"}
        if exc.name not in optional_ui_modules:
            raise
        print('QCchem workbench smoke requires optional UI dependencies. Install with: pip install -e ".[ui]"')
        return 2
    except (OSError, ValueError) as exc:
        print(f"QCchem workbench smoke rejected: {exc}")
        return 2

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Workbench smoke summary written to {output}")

    print(f"Workbench smoke completed: {summary['status']}")
    print(f"Routes: {summary['passed_routes']} passed, {summary['failed_routes']} failed")
    print(f"Registered pages: {summary['passed_pages']} passed, {summary['failed_pages']} failed")
    _print_workbench_smoke_failed_summary(summary)
    for route in summary.get("routes", []):
        if not isinstance(route, dict) or route.get("status") == "passed":
            continue
        render_error = route.get("render_error")
        print(
            "Failed route: "
            f"{route.get('route')} "
            f"failed_checks={_workbench_smoke_failed_checks(route)} "
            f"label={route.get('actual_active_label')!r} "
            f"expected_label={route.get('expected_active_label')!r} "
            f"expected_text={route.get('expected_text')!r} "
            f"text_excerpt={route.get('text_excerpt')!r}"
            + (f" render_error={render_error!r}" if render_error else "")
        )
    for page in summary.get("pages", []):
        if not isinstance(page, dict) or page.get("status") == "passed":
            continue
        render_error = page.get("render_error")
        print(
            "Failed page: "
            f"{page.get('path')} "
            f"failed_checks={_workbench_smoke_failed_checks(page)} "
            f"title={page.get('title')!r} "
            f"route_label={page.get('route_label')!r} "
            f"text_excerpt={page.get('text_excerpt')!r}"
            + (f" render_error={render_error!r}" if render_error else "")
        )
    return 0 if summary["status"] == "passed" else 2


def _print_release_audit_triage(summary: dict[str, object], *, limit: int = 5) -> None:
    required_failed = summary.get("required_failed_checks")
    if isinstance(required_failed, list) and required_failed:
        print("Required failed checks:")
        for check in required_failed[:limit]:
            if isinstance(check, dict):
                print(_release_audit_triage_line(check))
        remaining = len(required_failed) - limit
        if remaining > 0:
            print(f"- ... {remaining} more required failure(s)")

    warning_checks = summary.get("warning_checks")
    if isinstance(warning_checks, list) and warning_checks:
        print("Warning checks:")
        for check in warning_checks[:limit]:
            if isinstance(check, dict):
                print(_release_audit_triage_line(check))
        remaining = len(warning_checks) - limit
        if remaining > 0:
            print(f"- ... {remaining} more warning(s)")


def _release_audit_triage_line(check: dict[str, object]) -> str:
    line = f"- {check.get('id')}: {check.get('summary', '')}"
    detail_hint = _release_audit_detail_hint(check.get("details"))
    if detail_hint:
        line += f" ({detail_hint})"
    return line


def _release_audit_detail_hint(details: object) -> str:
    if not isinstance(details, dict):
        return ""
    fragments: list[str] = []
    labels: set[str] = set()

    def _append(label: str, value: object) -> None:
        if label in labels:
            return
        labels.add(label)
        fragments.append(f"{label}={_release_audit_hint_value(value)}")

    for list_key, prefix in (
        ("failures", "failure"),
        ("contract_failures", "contract_failure"),
        ("blocking_failures", "blocking_failure"),
        ("warnings", "warning"),
    ):
        value = details.get(list_key)
        if not isinstance(value, list) or not value:
            continue
        first = next((item for item in value if isinstance(item, dict)), None)
        if first is None:
            first = value[0]
        if isinstance(first, dict):
            for key in ("reason", "remediation", "field", "workflow", "step_name", "job", "step_index"):
                if key in first:
                    label = f"{prefix}_{key}" if key == "reason" else key
                    _append(label, first[key])
        else:
            _append(prefix, first)
        break
    for key in ("reason", "remediation", "field", "workflow", "step_name", "job", "step_index"):
        if key in details:
            _append(key, details[key])
    return " ".join(fragments[:5])


def _release_audit_hint_value(value: object, *, limit: int = 120) -> str:
    text = str(value).replace("\n", " ").strip()
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def _release_acceptance_status_issue_line(item: dict[str, object]) -> str:
    changed = _release_acceptance_status_list_hint(item.get("changed_fields")) or "none"
    line = (
        f"{item.get('artifact_name')} "
        f"status={item.get('status')} "
        f"changed_fields={changed} "
        f"sidecar={item.get('sidecar_path')}"
    )
    detail_hint = _release_acceptance_status_detail_hint(item)
    if detail_hint:
        line += f" ({detail_hint})"
    return line


def _release_acceptance_status_detail_hint(item: dict[str, object]) -> str:
    status = item.get("status")
    if status == "missing":
        return "reason=sidecar_missing"

    error = item.get("error")
    if error:
        return f"error={_release_audit_hint_value(error)}"

    contract_failures = item.get("contract_failures")
    if isinstance(contract_failures, list) and contract_failures:
        first = next((failure for failure in contract_failures if isinstance(failure, dict)), None)
        if first is None:
            return f"contract_failure={_release_audit_hint_value(contract_failures[0])}"
        fragments: list[str] = []
        for key in ("field", "reason", "expected", "actual"):
            if key not in first:
                continue
            label = f"contract_failure_{key}" if key in {"field", "reason"} else key
            fragments.append(f"{label}={_release_audit_hint_value(first[key])}")
        if fragments:
            return " ".join(fragments[:5])

    missing = _release_acceptance_status_list_hint(item.get("missing_fields"))
    if missing:
        return f"missing_fields={missing}"

    return ""


def _release_acceptance_status_list_hint(value: object, *, limit: int = 5) -> str:
    if not isinstance(value, list) or not value:
        return ""
    fields = [str(field) for field in value[:limit]]
    remaining = len(value) - limit
    if remaining > 0:
        fields.append(f"+{remaining} more")
    return ",".join(fields)


def _print_release_acceptance_repair_plan(report: dict[str, object]) -> None:
    plan = report.get("repair_plan")
    if not isinstance(plan, list) or not plan:
        print("Release acceptance repair plan: none")
        return

    print("Release acceptance repair plan:")
    for raw_item in plan:
        if not isinstance(raw_item, dict):
            continue
        print(
            f"- {raw_item.get('artifact_name')} "
            f"status={raw_item.get('status')} "
            f"issue={raw_item.get('issue')} "
            f"sidecar={raw_item.get('sidecar_path')}"
        )
        preview_command = raw_item.get("preview_command")
        repair_command = raw_item.get("repair_command")
        if preview_command:
            print(f"  preview: {preview_command}")
        if repair_command:
            print(f"  repair: {repair_command}")
        if not preview_command and not repair_command:
            print(f"  action: {raw_item.get('recommended_action')}")


def _print_release_audit_sidecar_repair_triage(summary: dict[str, object]) -> None:
    sidecars = summary.get("release_acceptance_sidecars")
    if not isinstance(sidecars, dict):
        return
    plan = sidecars.get("repair_plan")
    if not isinstance(plan, list) or not plan:
        return
    first = next((item for item in plan if isinstance(item, dict)), None)
    if first is None:
        return

    print("Release sidecar repair:")
    print(
        f"- {first.get('artifact_name')} "
        f"status={first.get('status')} "
        f"issue={first.get('issue')} "
        f"sidecar={first.get('sidecar_path')}"
    )
    preview_command = first.get("preview_command")
    repair_command = first.get("repair_command")
    if preview_command:
        print(f"  preview: {preview_command}")
    if repair_command:
        print(f"  repair: {repair_command}")
    if not preview_command and not repair_command:
        print(f"  action: {first.get('recommended_action')}")
    remaining_count = len([item for item in plan if isinstance(item, dict)]) - 1
    if remaining_count > 0:
        print(f"  more: {remaining_count} additional sidecar repair item(s); see release_readiness.md")


def _release_audit_output_dir(summary: dict[str, object], output_dir: Path | None) -> Path:
    report_dir = output_dir or Path("artifacts") / "release_audit"
    if output_dir is not None:
        return report_dir

    provenance = summary.get("audit_provenance")
    if not isinstance(provenance, dict):
        return report_dir
    repo_root_text = provenance.get("repo_root")
    output_dir_text = provenance.get("output_dir")
    if not repo_root_text or not output_dir_text:
        return report_dir

    output_path = Path(str(output_dir_text))
    return output_path if output_path.is_absolute() else Path(str(repo_root_text)) / output_path


def _print_release_audit_handoff_summary(output_dir: Path) -> None:
    print(f"Handoff: {output_dir / 'release_handoff.md'}")
    try:
        handoff = json.loads((output_dir / "release_handoff.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(handoff, dict):
        return

    diagnostic_artifacts = handoff.get("diagnostic_artifacts")
    if not isinstance(diagnostic_artifacts, dict):
        return
    artifact_names = diagnostic_artifacts.get("names")
    if isinstance(artifact_names, list) and artifact_names:
        print(f"Diagnostic artifact: {', '.join(str(name) for name in artifact_names)}")
    artifact_listing_url = diagnostic_artifacts.get("artifact_listing_url")
    if isinstance(artifact_listing_url, str) and artifact_listing_url:
        print(f"Artifact listing: {artifact_listing_url}")
    manifest = diagnostic_artifacts.get("manifest")
    if isinstance(manifest, dict) and manifest.get("path"):
        print(f"Diagnostics manifest: {manifest.get('path')}")


def _release_status_audit_dir(audit_dir: Path, repo_root: Path | None) -> Path:
    if audit_dir.is_absolute():
        return audit_dir
    if repo_root is not None:
        return repo_root / audit_dir
    return audit_dir


def _print_release_status_summary(summary: dict[str, object]) -> None:
    status = summary.get("status")
    print(f"Release status: {status}")
    print(f"Audit dir: {summary.get('audit_dir')}")
    missing = summary.get("missing_files")
    if isinstance(missing, list) and missing:
        print("Release status unavailable: missing outputs")
        print(f"Missing outputs: {', '.join(str(item) for item in missing)}")
        return
    error = summary.get("error")
    if error:
        print("Release status unavailable: unreadable outputs")
        print(f"Error: {error}")
        return
    schema_mismatches = summary.get("schema_mismatches")
    if isinstance(schema_mismatches, list) and schema_mismatches:
        print("Release status unavailable: schema mismatch")
        for item in schema_mismatches:
            if isinstance(item, dict):
                print(
                    "Schema mismatch: "
                    f"{item.get('file')} {item.get('field')} "
                    f"expected={item.get('expected')} actual={item.get('actual')}"
                )
        return
    contract_mismatches = summary.get("contract_mismatches")
    if isinstance(contract_mismatches, list) and contract_mismatches:
        print("Release status unavailable: contract mismatch")
        for item in contract_mismatches:
            if isinstance(item, dict):
                line = (
                    "Contract mismatch: "
                    f"{item.get('file')} {item.get('field')} "
                    f"expected={item.get('expected')}"
                )
                if "actual_type" in item:
                    line += f" actual_type={item.get('actual_type')}"
                elif "actual" in item:
                    line += f" actual={item.get('actual')}"
                if item.get("reason"):
                    line += f" reason={item.get('reason')}"
                print(line)
        return

    required_pass_count = summary.get("required_pass_count")
    required_fail_count = summary.get("required_fail_count")
    print(f"Required checks: {required_pass_count} passed, {required_fail_count} failed")
    sidecar_status = summary.get("release_acceptance_sidecars_status")
    if sidecar_status:
        print(f"Release acceptance sidecars: {sidecar_status}")

    release_readiness = summary.get("release_readiness")
    if isinstance(release_readiness, dict):
        print(f"Report: {release_readiness.get('markdown')}")
    release_handoff = summary.get("release_handoff")
    if isinstance(release_handoff, dict):
        print(f"Handoff: {release_handoff.get('markdown')}")

    first_required_failure = summary.get("first_required_failure")
    if isinstance(first_required_failure, dict) and first_required_failure.get("id"):
        line = f"First required failure: {first_required_failure.get('id')}"
        if first_required_failure.get("summary"):
            line += f": {first_required_failure.get('summary')}"
        if first_required_failure.get("detail_hint"):
            line += f" ({first_required_failure.get('detail_hint')})"
        print(line)

    first_warning = summary.get("first_warning")
    if isinstance(first_warning, dict) and first_warning.get("id"):
        line = f"First warning: {first_warning.get('id')}"
        if first_warning.get("summary"):
            line += f": {first_warning.get('summary')}"
        if first_warning.get("detail_hint"):
            line += f" ({first_warning.get('detail_hint')})"
        print(line)

    first_sidecar_repair = summary.get("first_sidecar_repair")
    if isinstance(first_sidecar_repair, dict) and first_sidecar_repair.get("artifact_name"):
        print(
            "First sidecar repair: "
            f"{first_sidecar_repair.get('artifact_name')} "
            f"status={first_sidecar_repair.get('status')} "
            f"issue={first_sidecar_repair.get('issue')} "
            f"sidecar={first_sidecar_repair.get('sidecar_path')}"
        )

    diagnostic_artifacts = summary.get("diagnostic_artifacts")
    if isinstance(diagnostic_artifacts, dict):
        artifact_names = diagnostic_artifacts.get("names")
        if isinstance(artifact_names, list) and artifact_names:
            print(f"Diagnostic artifact: {', '.join(str(name) for name in artifact_names)}")
        artifact_listing_url = diagnostic_artifacts.get("artifact_listing_url")
        if isinstance(artifact_listing_url, str) and artifact_listing_url:
            print(f"Artifact listing: {artifact_listing_url}")
        manifest = diagnostic_artifacts.get("manifest")
        if isinstance(manifest, dict) and manifest.get("path"):
            print(f"Diagnostics manifest: {manifest.get('path')}")


def _print_release_artifact_verification_summary(report: dict[str, object]) -> None:
    print(f"Release artifact verification: {report.get('status')}")
    print(f"Artifact dir: {report.get('artifact_dir')}")
    summary = report.get("summary")
    if isinstance(summary, dict):
        print(f"Release status bundles: {summary.get('release_status_count')}")
        print(f"Diagnostics manifests: {summary.get('diagnostics_manifest_count')}")
        print(f"Acceptance status files: {summary.get('acceptance_status_count')}")
        print(f"Failures: {summary.get('failure_count')}")
    failures = report.get("failures")
    if isinstance(failures, list) and failures:
        first = next((item for item in failures if isinstance(item, dict)), None)
        if first is not None:
            line = f"First failure: {first.get('reason')}"
            if first.get("path"):
                line += f" path={first.get('path')}"
            print(line)


def _release_evidence_summary(
    *,
    artifact_dir: Path,
    evidence_root: Path,
    release_history: dict[str, object],
    verification_path: Path,
    verification_report: dict[str, object],
    workbench_smoke_path: Path,
    workbench_summary: dict[str, object],
    docs_path: Path,
    matrix_summary_path: Path,
    matrix_summary: dict[str, object],
    matrix_delta: dict[str, object],
    matrix_baseline_selection: dict[str, object],
    summary_path: Path,
    handoff_path: Path,
) -> dict[str, object]:
    verification_status = str(verification_report.get("status") or "unknown")
    workbench_status = str(workbench_summary.get("status") or "unknown")
    matrix_delta_status = str(matrix_delta.get("status") or "not_compared")
    status = (
        "passed"
        if verification_status == "passed" and workbench_status == "passed" and matrix_delta_status != "failed"
        else "failed"
    )
    release_verification = workbench_summary.get("release_verification")
    verification_failures = verification_report.get("failures")
    first_verification_failure = (
        next((failure for failure in verification_failures if isinstance(failure, dict)), None)
        if isinstance(verification_failures, list)
        else None
    )
    workbench_failed_checks = (
        workbench_summary.get("failed_checks") if isinstance(workbench_summary.get("failed_checks"), list) else []
    )
    first_failure = first_verification_failure
    if first_failure is None and workbench_failed_checks:
        first_failure = {"reason": "workbench_smoke_failed", "check": str(workbench_failed_checks[0])}
    if first_failure is None and matrix_delta_status == "failed":
        first_failure = (
            matrix_delta.get("first_failure") if isinstance(matrix_delta.get("first_failure"), dict) else None
        )
    matrix_artifacts = matrix_summary.get("artifacts") if isinstance(matrix_summary.get("artifacts"), list) else []
    return {
        "schema_version": "qcchem.release_evidence_collection.v0.1-alpha",
        "collection_mode": "downloaded_artifact_verification",
        "status": status,
        "recommended_action": "review_release_evidence" if status == "passed" else "inspect_release_evidence_failures",
        "first_failure": first_failure,
        "artifact_dir": str(artifact_dir),
        "evidence_root": str(evidence_root),
        "release_history": release_history,
        "docs_path": str(docs_path),
        "outputs": {
            "release_evidence_summary": str(summary_path),
            "release_evidence_handoff": str(handoff_path),
            "release_artifact_verification": str(verification_path),
            "release_matrix_summary": str(matrix_summary_path),
            "workbench_smoke": str(workbench_smoke_path),
        },
        "release_artifact_verification": {
            "status": verification_status,
            "summary": verification_report.get("summary") if isinstance(verification_report.get("summary"), dict) else {},
            "failure_count": len(verification_report.get("failures") or []),
            "first_failure": first_verification_failure,
            "matrix_artifacts": matrix_artifacts,
        },
        "release_matrix_summary": matrix_summary,
        "release_matrix_baseline_selection": matrix_baseline_selection,
        "release_matrix_delta": matrix_delta,
        "workbench_smoke": {
            "status": workbench_status,
            "route_count": workbench_summary.get("route_count"),
            "failed_routes": workbench_summary.get("failed_routes"),
            "page_count": workbench_summary.get("page_count"),
            "failed_pages": workbench_summary.get("failed_pages"),
            "failed_checks": workbench_summary.get("failed_checks")
            if isinstance(workbench_summary.get("failed_checks"), list)
            else [],
            "release_verification": release_verification if isinstance(release_verification, dict) else {},
        },
    }


def _release_artifact_name_from_path(path_value: object, artifact_dir: object) -> str:
    if not isinstance(path_value, str) or not path_value:
        return "unknown"
    path = Path(path_value)
    if isinstance(artifact_dir, str) and artifact_dir:
        try:
            relative = path.resolve().relative_to(Path(artifact_dir).resolve())
        except ValueError:
            relative = None
        if relative is not None and relative.parts:
            return relative.parts[0]
    for part in path.parts:
        if part.startswith("qcchem-release-diagnostics-"):
            return part
    return "unknown"


def _release_verification_matrix_artifacts(report: dict[str, object]) -> list[dict[str, object]]:
    artifact_dir = report.get("artifact_dir")
    artifacts: dict[str, dict[str, object]] = {}

    def ensure(name: str) -> dict[str, object]:
        if name not in artifacts:
            artifacts[name] = {
                "artifact_name": name,
                "status": "passed",
                "release_status_count": 0,
                "release_status_failed_count": 0,
                "source_tree_release_status": None,
                "wheel_release_status": None,
                "diagnostics_manifest_count": 0,
                "diagnostics_file_count": 0,
                "diagnostics_present_count": 0,
                "diagnostics_digest_count": 0,
                "acceptance_status": None,
                "acceptance_fresh_count": None,
                "acceptance_requires_update_count": None,
                "acceptance_repair_plan_count": None,
                "failure_count": 0,
                "first_failure": None,
            }
        return artifacts[name]

    release_statuses = report.get("release_statuses")
    if isinstance(release_statuses, list):
        for status_entry in release_statuses:
            if not isinstance(status_entry, dict):
                continue
            artifact = ensure(_release_artifact_name_from_path(status_entry.get("path"), artifact_dir))
            artifact["release_status_count"] = int(artifact["release_status_count"]) + 1
            if status_entry.get("status") != "passed":
                artifact["release_status_failed_count"] = int(artifact["release_status_failed_count"]) + 1
                artifact["status"] = "failed"
            entry_path = str(status_entry.get("path") or "")
            if "/tmp/qcchem-wheel-release-audit/" in entry_path:
                artifact["wheel_release_status"] = status_entry.get("status")
            else:
                artifact["source_tree_release_status"] = status_entry.get("status")

    manifests = report.get("diagnostics_manifests")
    if isinstance(manifests, list):
        for manifest_entry in manifests:
            if not isinstance(manifest_entry, dict):
                continue
            artifact = ensure(_release_artifact_name_from_path(manifest_entry.get("path"), artifact_dir))
            artifact["diagnostics_manifest_count"] = int(artifact["diagnostics_manifest_count"]) + 1
            artifact["diagnostics_file_count"] = int(artifact["diagnostics_file_count"]) + int(
                manifest_entry.get("file_count") or 0
            )
            artifact["diagnostics_present_count"] = int(artifact["diagnostics_present_count"]) + int(
                manifest_entry.get("present_count") or 0
            )
            artifact["diagnostics_digest_count"] = int(artifact["diagnostics_digest_count"]) + int(
                manifest_entry.get("digest_count") or 0
            )

    acceptance_statuses = report.get("acceptance_statuses")
    if isinstance(acceptance_statuses, list):
        for acceptance_entry in acceptance_statuses:
            if not isinstance(acceptance_entry, dict):
                continue
            artifact = ensure(_release_artifact_name_from_path(acceptance_entry.get("path"), artifact_dir))
            artifact["acceptance_status"] = acceptance_entry.get("status")
            artifact["acceptance_fresh_count"] = acceptance_entry.get("fresh_count")
            artifact["acceptance_requires_update_count"] = acceptance_entry.get("requires_update_count")
            artifact["acceptance_repair_plan_count"] = acceptance_entry.get("repair_plan_count")
            if acceptance_entry.get("status") != "fresh" or acceptance_entry.get("repair_plan_count") not in (0, None):
                artifact["status"] = "failed"

    failures = report.get("failures")
    if isinstance(failures, list):
        for failure in failures:
            if not isinstance(failure, dict):
                continue
            failure_path = failure.get("local_path") or failure.get("path") or failure.get("record_path")
            artifact = ensure(_release_artifact_name_from_path(failure_path, artifact_dir))
            artifact["status"] = "failed"
            artifact["failure_count"] = int(artifact["failure_count"]) + 1
            if artifact["first_failure"] is None:
                artifact["first_failure"] = failure

    return [artifacts[name] for name in sorted(artifacts)]


def _release_matrix_summary(
    matrix_artifacts: list[dict[str, object]],
    *,
    source_verification_path: Path,
) -> dict[str, object]:
    failed_artifacts = [item for item in matrix_artifacts if item.get("status") != "passed"]
    return {
        "schema_version": RELEASE_MATRIX_SUMMARY_SCHEMA_VERSION,
        "source_verification": str(source_verification_path),
        "artifact_count": len(matrix_artifacts),
        "failed_artifact_count": len(failed_artifacts),
        "artifacts": matrix_artifacts,
    }


def _load_release_matrix_baseline(
    baseline_summary_path: Path | None,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    if baseline_summary_path is None:
        return None, None
    try:
        payload = json.loads(baseline_summary_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, {"reason": "matrix_baseline_missing", "path": str(baseline_summary_path)}
    except (OSError, json.JSONDecodeError) as exc:
        return None, {
            "reason": "matrix_baseline_unreadable",
            "path": str(baseline_summary_path),
            "error": f"{type(exc).__name__}: {exc}",
        }
    if not isinstance(payload, dict):
        return None, {"reason": "matrix_baseline_not_object", "path": str(baseline_summary_path)}
    return payload, None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _resolve_release_matrix_baseline_summary_path(
    *,
    explicit_baseline_summary_path: Path | None,
    baseline_search_root: Path | None,
    current_evidence_root: Path,
) -> tuple[Path | None, dict[str, object]]:
    if explicit_baseline_summary_path is not None:
        return explicit_baseline_summary_path, {
            "mode": "explicit",
            "path": str(explicit_baseline_summary_path),
            "search_root": None,
            "candidate_count": None,
            "reason": None,
        }
    if baseline_search_root is None:
        return None, {
            "mode": "not_requested",
            "path": None,
            "search_root": None,
            "candidate_count": 0,
            "reason": "baseline_not_provided",
        }

    search_root = baseline_search_root
    if not search_root.exists():
        return None, {
            "mode": "auto_not_found",
            "path": None,
            "search_root": str(search_root),
            "candidate_count": 0,
            "reason": "baseline_search_root_missing",
        }
    if not search_root.is_dir():
        return None, {
            "mode": "auto_not_found",
            "path": None,
            "search_root": str(search_root),
            "candidate_count": 0,
            "reason": "baseline_search_root_not_directory",
        }

    current_root = current_evidence_root.resolve()
    candidates: list[tuple[int, str, Path]] = []
    for candidate in search_root.rglob("release_matrix_summary.json"):
        try:
            resolved_candidate = candidate.resolve()
            if _is_relative_to(resolved_candidate, current_root):
                continue
            stat = candidate.stat()
        except OSError:
            continue
        candidates.append((stat.st_mtime_ns, str(resolved_candidate), candidate))

    if not candidates:
        return None, {
            "mode": "auto_not_found",
            "path": None,
            "search_root": str(search_root),
            "candidate_count": 0,
            "reason": "auto_baseline_not_found",
        }

    candidates.sort(reverse=True)
    selected = candidates[0][2]
    return selected, {
        "mode": "auto",
        "path": str(selected),
        "search_root": str(search_root),
        "candidate_count": len(candidates),
        "reason": None,
    }


def _release_history_label_path(history_label: str | None) -> Path:
    label = history_label or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    stripped = label.strip()
    path = Path(stripped)
    if not stripped or path.is_absolute() or len(path.parts) != 1 or path.parts[0] in {".", ".."}:
        raise ValueError("release history label must be one relative directory name")
    return path


def _resolve_release_evidence_root(
    *,
    artifact_dir: Path,
    output_dir: Path | None,
    history_root: Path | None,
    history_label: str | None,
    baseline_search_root: Path | None,
) -> tuple[Path, Path | None, dict[str, object]]:
    if history_root is None:
        if history_label is not None:
            raise ValueError("--history-label requires --history-root")
        evidence_root = output_dir if output_dir is not None else artifact_dir
        mode = "explicit_output" if output_dir is not None else "artifact_dir"
        return evidence_root, baseline_search_root, {
            "mode": mode,
            "root": None,
            "label": None,
            "path": str(evidence_root),
            "baseline_search_root": str(baseline_search_root) if baseline_search_root is not None else None,
        }

    if output_dir is not None:
        raise ValueError("--history-root cannot be combined with --output-dir")
    if history_root.exists() and not history_root.is_dir():
        raise ValueError(f"--history-root is not a directory: {history_root}")

    label_path = _release_history_label_path(history_label)
    evidence_root = history_root / label_path
    try:
        if evidence_root.exists() and any(evidence_root.iterdir()):
            raise ValueError(f"release history output directory is not empty: {evidence_root}")
    except OSError as exc:
        raise ValueError(f"release history output directory is not readable: {evidence_root}") from exc

    effective_baseline_search_root = baseline_search_root if baseline_search_root is not None else history_root
    return evidence_root, effective_baseline_search_root, {
        "mode": "retained_history",
        "root": str(history_root),
        "label": str(label_path),
        "path": str(evidence_root),
        "baseline_search_root": str(effective_baseline_search_root),
    }


def _release_matrix_artifacts_by_name(matrix_summary: dict[str, object]) -> dict[str, dict[str, object]]:
    artifacts = matrix_summary.get("artifacts")
    if not isinstance(artifacts, list):
        return {}
    named_artifacts: dict[str, dict[str, object]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_name = artifact.get("artifact_name")
        if isinstance(artifact_name, str) and artifact_name:
            named_artifacts[artifact_name] = artifact
    return named_artifacts


def _release_matrix_first_change(delta: dict[str, object]) -> dict[str, object] | None:
    added = delta.get("added") if isinstance(delta.get("added"), list) else []
    if added and isinstance(added[0], dict):
        return {"change_type": "added", "artifact_name": added[0].get("artifact_name")}
    removed = delta.get("removed") if isinstance(delta.get("removed"), list) else []
    if removed and isinstance(removed[0], dict):
        return {"change_type": "removed", "artifact_name": removed[0].get("artifact_name")}
    changed = delta.get("changed") if isinstance(delta.get("changed"), list) else []
    if changed and isinstance(changed[0], dict):
        return {
            "change_type": "changed",
            "artifact_name": changed[0].get("artifact_name"),
            "changed_fields": changed[0].get("changed_fields"),
        }
    return None


def _release_matrix_artifact_delta(
    current_matrix_summary: dict[str, object],
    baseline_summary: dict[str, object] | None,
    baseline_failure: dict[str, object] | None,
    *,
    baseline_summary_path: Path | None,
    missing_baseline_reason: str = "baseline_not_provided",
) -> dict[str, object]:
    current_artifacts = _release_matrix_artifacts_by_name(current_matrix_summary)
    if baseline_summary_path is None:
        return {
            "status": "not_compared",
            "reason": missing_baseline_reason,
            "baseline_path": None,
            "current_artifact_count": len(current_artifacts),
            "baseline_artifact_count": None,
            "added": [],
            "removed": [],
            "changed": [],
            "unchanged_count": 0,
            "first_change": None,
            "first_failure": None,
        }
    if baseline_failure is not None:
        return {
            "status": "failed",
            "reason": "baseline_unavailable",
            "baseline_path": str(baseline_summary_path),
            "current_artifact_count": len(current_artifacts),
            "baseline_artifact_count": None,
            "added": [],
            "removed": [],
            "changed": [],
            "unchanged_count": 0,
            "first_change": None,
            "first_failure": baseline_failure,
        }

    baseline_artifacts = _release_matrix_artifacts_by_name(baseline_summary or {})
    added = [current_artifacts[name] for name in sorted(current_artifacts.keys() - baseline_artifacts.keys())]
    removed = [baseline_artifacts[name] for name in sorted(baseline_artifacts.keys() - current_artifacts.keys())]
    changed: list[dict[str, object]] = []
    unchanged_count = 0
    for name in sorted(current_artifacts.keys() & baseline_artifacts.keys()):
        current = current_artifacts[name]
        baseline = baseline_artifacts[name]
        changed_fields = [
            field for field in RELEASE_MATRIX_COMPARE_FIELDS if current.get(field) != baseline.get(field)
        ]
        if changed_fields:
            changed.append(
                {
                    "artifact_name": name,
                    "changed_fields": changed_fields,
                    "before": baseline,
                    "after": current,
                }
            )
        else:
            unchanged_count += 1

    delta = {
        "status": "changed" if added or removed or changed else "passed",
        "reason": None,
        "baseline_path": str(baseline_summary_path),
        "current_artifact_count": len(current_artifacts),
        "baseline_artifact_count": len(baseline_artifacts),
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": unchanged_count,
        "first_change": None,
        "first_failure": None,
    }
    delta["first_change"] = _release_matrix_first_change(delta)
    return delta


def _release_failure_handoff_text(failure: object) -> str:
    if not isinstance(failure, dict):
        return "none"
    failure_text = str(failure.get("reason") or "unknown")
    if failure.get("path"):
        failure_text = f"{failure_text} path={failure.get('path')}"
    if failure.get("local_path"):
        failure_text = f"{failure_text} local_path={failure.get('local_path')}"
    elif failure.get("record_path"):
        failure_text = f"{failure_text} record_path={failure.get('record_path')}"
    elif failure.get("check"):
        failure_text = f"{failure_text} check={failure.get('check')}"
    return failure_text


def _release_handoff_value(value: object, *, missing: str = "not_applicable") -> str:
    return missing if value is None else str(value)


def _release_handoff_count_pair(passed: object, failed: object, *, missing: str = "not_applicable") -> str:
    if passed is None and failed is None:
        return f"`{missing}`"
    return f"`{_release_handoff_value(passed, missing=missing)}` passed / `{_release_handoff_value(failed, missing=missing)}` failed"


def _read_optional_json_object(path: Path, *, label: str, failures: list[dict[str, object]]) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append({"reason": f"{label}_missing", "path": str(path)})
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        failures.append({"reason": f"{label}_unreadable", "path": str(path), "error": f"{type(exc).__name__}: {exc}"})
        return {}
    if not isinstance(payload, dict):
        failures.append({"reason": f"{label}_not_object", "path": str(path)})
        return {}
    return payload


def _local_release_evidence_summary(
    *,
    audit_dir: Path,
    workbench_smoke_path: Path,
    acceptance_status_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    failures: list[dict[str, object]] = []
    summary_path = output_dir / "release_evidence_summary.json"
    handoff_path = output_dir / "release_evidence_handoff.md"
    release_status = build_release_status_summary(audit_dir)
    if release_status.get("status") != "passed":
        failures.append(
            {
                "reason": "release_status_not_passed",
                "path": str(audit_dir),
                "status": release_status.get("status"),
                "recommended_action": release_status.get("recommended_action"),
            }
        )

    workbench_summary = _read_optional_json_object(workbench_smoke_path, label="workbench_smoke", failures=failures)
    if workbench_summary and workbench_summary.get("status") != "passed":
        failed_checks = workbench_summary.get("failed_checks")
        first_check = failed_checks[0] if isinstance(failed_checks, list) and failed_checks else None
        failures.append(
            {
                "reason": "workbench_smoke_not_passed",
                "path": str(workbench_smoke_path),
                "status": workbench_summary.get("status"),
                "check": str(first_check) if first_check is not None else None,
            }
        )

    acceptance_status = _read_optional_json_object(
        acceptance_status_path,
        label="acceptance_status",
        failures=failures,
    )
    if acceptance_status and acceptance_status.get("status") != "fresh":
        failures.append(
            {
                "reason": "acceptance_status_not_fresh",
                "path": str(acceptance_status_path),
                "status": acceptance_status.get("status"),
                "repair_plan_count": acceptance_status.get("repair_plan_count"),
            }
        )

    first_failure = next((failure for failure in failures if isinstance(failure, dict)), None)
    status = "passed" if not failures else "failed"
    return {
        "schema_version": "qcchem.release_evidence_collection.v0.1-alpha",
        "collection_mode": "ci_diagnostics_handoff",
        "status": status,
        "recommended_action": "review_release_evidence" if status == "passed" else "inspect_release_evidence_failures",
        "first_failure": first_failure,
        "artifact_dir": str(audit_dir.parent),
        "evidence_root": str(output_dir),
        "release_history": {
            "mode": "not_applicable",
            "root": None,
            "label": None,
            "path": str(output_dir),
            "baseline_search_root": None,
        },
        "docs_path": None,
        "outputs": {
            "release_evidence_summary": str(summary_path),
            "release_evidence_handoff": str(handoff_path),
            "workbench_smoke": str(workbench_smoke_path),
        },
        "release_status": {
            "status": release_status.get("status"),
            "required_pass_count": release_status.get("required_pass_count"),
            "required_fail_count": release_status.get("required_fail_count"),
            "warning_count": release_status.get("warning_count"),
            "recommended_action": release_status.get("recommended_action"),
            "release_handoff": release_status.get("release_handoff"),
        },
        "acceptance_status": {
            "status": acceptance_status.get("status"),
            "fresh_count": acceptance_status.get("fresh_count"),
            "requires_update_count": acceptance_status.get("requires_update_count"),
            "repair_plan_count": acceptance_status.get("repair_plan_count"),
        },
        "release_artifact_verification": {
            "status": "not_run",
            "summary": {},
            "failure_count": None,
            "first_failure": None,
        },
        "release_matrix_delta": {
            "status": "not_applicable",
            "reason": "downloaded_artifact_verification_not_run",
            "baseline_path": None,
            "current_artifact_count": None,
            "baseline_artifact_count": None,
            "added": [],
            "removed": [],
            "changed": [],
            "unchanged_count": None,
            "first_change": None,
            "first_failure": None,
        },
        "release_matrix_baseline_selection": {
            "mode": "not_applicable",
            "path": None,
            "search_root": None,
            "candidate_count": None,
            "reason": "downloaded_artifact_verification_not_run",
        },
        "workbench_smoke": {
            "status": workbench_summary.get("status"),
            "route_count": workbench_summary.get("route_count"),
            "failed_routes": workbench_summary.get("failed_routes"),
            "page_count": workbench_summary.get("page_count"),
            "failed_pages": workbench_summary.get("failed_pages"),
            "failed_checks": workbench_summary.get("failed_checks")
            if isinstance(workbench_summary.get("failed_checks"), list)
            else [],
            "release_verification": workbench_summary.get("release_verification")
            if isinstance(workbench_summary.get("release_verification"), dict)
            else {},
        },
        "failures": failures,
    }


def _release_evidence_handoff_markdown(summary: dict[str, object]) -> str:
    outputs = summary.get("outputs") if isinstance(summary.get("outputs"), dict) else {}
    verification = (
        summary.get("release_artifact_verification")
        if isinstance(summary.get("release_artifact_verification"), dict)
        else {}
    )
    verification_counts = verification.get("summary") if isinstance(verification.get("summary"), dict) else {}
    workbench = summary.get("workbench_smoke") if isinstance(summary.get("workbench_smoke"), dict) else {}
    linked_release_verification = (
        workbench.get("release_verification") if isinstance(workbench.get("release_verification"), dict) else {}
    )
    release_status = summary.get("release_status") if isinstance(summary.get("release_status"), dict) else {}
    acceptance_status = summary.get("acceptance_status") if isinstance(summary.get("acceptance_status"), dict) else {}
    release_history = (
        summary.get("release_history")
        if isinstance(summary.get("release_history"), dict)
        else {
            "mode": "not_available",
            "root": None,
            "label": None,
            "path": summary.get("evidence_root"),
            "baseline_search_root": None,
        }
    )
    failed_checks = workbench.get("failed_checks") if isinstance(workbench.get("failed_checks"), list) else []
    first_failure = verification.get("first_failure") if isinstance(verification.get("first_failure"), dict) else None
    first_summary_failure = summary.get("first_failure") if isinstance(summary.get("first_failure"), dict) else None
    failure_for_handoff = first_summary_failure if first_summary_failure is not None else first_failure
    first_failure_text = _release_failure_handoff_text(failure_for_handoff)
    failed_checks_text = ", ".join(str(item) for item in failed_checks) if failed_checks else "none"
    matrix_artifacts = (
        verification.get("matrix_artifacts") if isinstance(verification.get("matrix_artifacts"), list) else []
    )
    matrix_delta = (
        summary.get("release_matrix_delta")
        if isinstance(summary.get("release_matrix_delta"), dict)
        else {
            "status": "not_available",
            "reason": "release_matrix_delta_missing",
            "baseline_path": None,
            "current_artifact_count": None,
            "baseline_artifact_count": None,
            "added": [],
            "removed": [],
            "changed": [],
            "unchanged_count": None,
            "first_change": None,
            "first_failure": None,
        }
    )
    matrix_baseline_selection = (
        summary.get("release_matrix_baseline_selection")
        if isinstance(summary.get("release_matrix_baseline_selection"), dict)
        else {
            "mode": "not_available",
            "path": None,
            "search_root": None,
            "candidate_count": None,
            "reason": "release_matrix_baseline_selection_missing",
        }
    )
    matrix_delta_added = matrix_delta.get("added") if isinstance(matrix_delta.get("added"), list) else []
    matrix_delta_removed = matrix_delta.get("removed") if isinstance(matrix_delta.get("removed"), list) else []
    matrix_delta_changed = matrix_delta.get("changed") if isinstance(matrix_delta.get("changed"), list) else []
    matrix_delta_first_change = (
        matrix_delta.get("first_change") if isinstance(matrix_delta.get("first_change"), dict) else None
    )
    first_change_text = "none"
    if matrix_delta_first_change is not None:
        first_change_text = str(matrix_delta_first_change.get("change_type") or "unknown")
        if matrix_delta_first_change.get("artifact_name"):
            first_change_text = f"{first_change_text} artifact={matrix_delta_first_change.get('artifact_name')}"
        changed_fields = matrix_delta_first_change.get("changed_fields")
        if isinstance(changed_fields, list) and changed_fields:
            first_change_text = f"{first_change_text} fields={','.join(str(field) for field in changed_fields)}"
    lines = [
        "# QCchem Release Evidence Handoff",
        "",
        "- output: `release_evidence_handoff.md`",
        f"- schema_version: `{summary.get('schema_version')}`",
        f"- status: `{summary.get('status')}`",
        f"- recommended_action: `{summary.get('recommended_action')}`",
        f"- first_failure: `{first_failure_text}`",
        f"- artifact_dir: `{_release_handoff_value(summary.get('artifact_dir'), missing='not_available')}`",
        f"- evidence_root: `{_release_handoff_value(summary.get('evidence_root'), missing='not_available')}`",
        f"- docs_path: `{_release_handoff_value(summary.get('docs_path'))}`",
        f"- collection_mode: `{summary.get('collection_mode')}`",
        f"- history_mode: `{_release_handoff_value(release_history.get('mode'), missing='not_available')}`",
        f"- history_root: `{_release_handoff_value(release_history.get('root'), missing='not_provided')}`",
        f"- history_label: `{_release_handoff_value(release_history.get('label'), missing='not_provided')}`",
        "",
        "## Generated Outputs",
        "",
        f"- release_evidence_summary_json: `{_release_handoff_value(outputs.get('release_evidence_summary'), missing='not_available')}`",
        f"- release_evidence_handoff_markdown: `{_release_handoff_value(outputs.get('release_evidence_handoff'), missing='not_available')}`",
        f"- release_artifact_verification_json: `{_release_handoff_value(outputs.get('release_artifact_verification'))}`",
        f"- release_matrix_summary_json: `{_release_handoff_value(outputs.get('release_matrix_summary'))}`",
        f"- workbench_smoke_json: `{_release_handoff_value(outputs.get('workbench_smoke'), missing='not_available')}`",
        "",
        "## CI Diagnostics Handoff",
        "",
        f"- release_status: `{_release_handoff_value(release_status.get('status'))}`",
        f"- required_checks: {_release_handoff_count_pair(release_status.get('required_pass_count'), release_status.get('required_fail_count'))}",
        f"- warnings: `{_release_handoff_value(release_status.get('warning_count'))}`",
        f"- release_status_action: `{_release_handoff_value(release_status.get('recommended_action'))}`",
        f"- acceptance_status: `{_release_handoff_value(acceptance_status.get('status'))}`",
        f"- acceptance_repair_plan_count: `{_release_handoff_value(acceptance_status.get('repair_plan_count'))}`",
        "",
        "## Release Artifact Verification",
        "",
        f"- status: `{_release_handoff_value(verification.get('status'), missing='not_available')}`",
        f"- release_status_count: `{_release_handoff_value(verification_counts.get('release_status_count'))}`",
        f"- diagnostics_manifest_count: `{_release_handoff_value(verification_counts.get('diagnostics_manifest_count'))}`",
        f"- acceptance_status_count: `{_release_handoff_value(verification_counts.get('acceptance_status_count'))}`",
        f"- failure_count: `{_release_handoff_value(verification.get('failure_count'))}`",
        f"- first_failure: `{first_failure_text}`",
        "",
        "## Matrix Artifact Verification",
        "",
    ]
    if matrix_artifacts:
        for item in matrix_artifacts:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('artifact_name')}`: status=`{item.get('status')}`; "
                f"release_statuses=`{item.get('release_status_count')}`; "
                f"source=`{_release_handoff_value(item.get('source_tree_release_status'))}`; "
                f"wheel=`{_release_handoff_value(item.get('wheel_release_status'))}`; "
                f"manifests=`{item.get('diagnostics_manifest_count')}`; "
                f"digests=`{item.get('diagnostics_digest_count')}/{item.get('diagnostics_file_count')}`; "
                f"acceptance=`{_release_handoff_value(item.get('acceptance_status'))}`; "
                f"failures=`{item.get('failure_count')}`; "
                f"first_failure=`{_release_failure_handoff_text(item.get('first_failure'))}`"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Matrix Artifact Delta",
            "",
            f"- baseline_selection: `{_release_handoff_value(matrix_baseline_selection.get('mode'), missing='not_available')}`",
            f"- baseline_search_root: `{_release_handoff_value(matrix_baseline_selection.get('search_root'), missing='not_provided')}`",
            f"- baseline_candidate_count: `{_release_handoff_value(matrix_baseline_selection.get('candidate_count'))}`",
            f"- status: `{_release_handoff_value(matrix_delta.get('status'), missing='not_available')}`",
            f"- reason: `{_release_handoff_value(matrix_delta.get('reason'), missing='none')}`",
            f"- baseline_path: `{_release_handoff_value(matrix_delta.get('baseline_path'), missing='not_provided')}`",
            f"- current_artifact_count: `{_release_handoff_value(matrix_delta.get('current_artifact_count'))}`",
            f"- baseline_artifact_count: `{_release_handoff_value(matrix_delta.get('baseline_artifact_count'))}`",
            f"- added: `{len(matrix_delta_added)}`",
            f"- removed: `{len(matrix_delta_removed)}`",
            f"- changed: `{len(matrix_delta_changed)}`",
            f"- unchanged: `{_release_handoff_value(matrix_delta.get('unchanged_count'))}`",
            f"- first_change: `{first_change_text}`",
        ]
    )
    if matrix_delta_added:
        for item in matrix_delta_added:
            if isinstance(item, dict):
                lines.append(f"- added `{item.get('artifact_name')}`")
    if matrix_delta_removed:
        for item in matrix_delta_removed:
            if isinstance(item, dict):
                lines.append(f"- removed `{item.get('artifact_name')}`")
    if matrix_delta_changed:
        for item in matrix_delta_changed:
            if not isinstance(item, dict):
                continue
            changed_fields = item.get("changed_fields") if isinstance(item.get("changed_fields"), list) else []
            lines.append(
                f"- changed `{item.get('artifact_name')}`: fields=`{','.join(str(field) for field in changed_fields)}`"
            )
    lines.extend(
        [
            "",
            "## Workbench Smoke",
            "",
            f"- status: `{_release_handoff_value(workbench.get('status'), missing='not_available')}`",
            f"- route_count: `{_release_handoff_value(workbench.get('route_count'))}`",
            f"- failed_routes: `{_release_handoff_value(workbench.get('failed_routes'))}`",
            f"- page_count: `{_release_handoff_value(workbench.get('page_count'))}`",
            f"- failed_pages: `{_release_handoff_value(workbench.get('failed_pages'))}`",
            f"- failed_checks: `{failed_checks_text}`",
            f"- linked_release_verification_status: `{_release_handoff_value(linked_release_verification.get('status'), missing='not_available')}`",
            f"- linked_release_verification_source: `{_release_handoff_value(linked_release_verification.get('source_path'), missing='not_available')}`",
            "",
            "## Review Notes",
            "",
            "- `ci_diagnostics_handoff` summarizes local CI diagnostics before artifact upload.",
            "- `downloaded_artifact_verification` verifies downloaded CI diagnostics and component-tree Workbench routes.",
            "- Run `qcchem release collect-evidence` after downloading CI artifacts for digest verification.",
            "- It does not replace the real browser console checklist before a release candidate.",
            "- Keep the generated files outside tracked source unless you intentionally archive release evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def _run_release_collect_evidence_command(
    artifact_dir: Path,
    docs_path: Path,
    output_dir: Path | None,
    baseline_summary_path: Path | None,
    baseline_search_root: Path | None,
    history_root: Path | None,
    history_label: str | None,
) -> int:
    try:
        evidence_root, effective_baseline_search_root, release_history = _resolve_release_evidence_root(
            artifact_dir=artifact_dir,
            output_dir=output_dir,
            history_root=history_root,
            history_label=history_label,
            baseline_search_root=baseline_search_root,
        )
    except ValueError as exc:
        print(f"QCchem release evidence collection rejected: {exc}")
        return 2

    evidence_root.mkdir(parents=True, exist_ok=True)
    verification_path = evidence_root / "release_artifact_verification.json"
    matrix_summary_path = evidence_root / "release_matrix_summary.json"
    workbench_smoke_path = evidence_root / "workbench_smoke.json"
    summary_path = evidence_root / "release_evidence_summary.json"
    handoff_path = evidence_root / "release_evidence_handoff.md"

    verification_report = verify_release_diagnostics_artifacts(artifact_dir)
    verification_path.write_text(json.dumps(verification_report, indent=2, sort_keys=True), encoding="utf-8")
    matrix_artifacts = _release_verification_matrix_artifacts(verification_report)
    matrix_summary = _release_matrix_summary(matrix_artifacts, source_verification_path=verification_path)
    matrix_summary_path.write_text(json.dumps(matrix_summary, indent=2, sort_keys=True), encoding="utf-8")
    resolved_baseline_summary_path, matrix_baseline_selection = _resolve_release_matrix_baseline_summary_path(
        explicit_baseline_summary_path=baseline_summary_path,
        baseline_search_root=effective_baseline_search_root,
        current_evidence_root=evidence_root,
    )
    baseline_summary, baseline_failure = _load_release_matrix_baseline(resolved_baseline_summary_path)
    matrix_delta = _release_matrix_artifact_delta(
        matrix_summary,
        baseline_summary,
        baseline_failure,
        baseline_summary_path=resolved_baseline_summary_path,
        missing_baseline_reason=str(matrix_baseline_selection.get("reason") or "baseline_not_provided"),
    )
    _print_release_artifact_verification_summary(verification_report)
    print(f"Verification JSON: {verification_path}")
    print(f"Release matrix summary: {matrix_summary_path}")
    if matrix_baseline_selection.get("path"):
        print(f"Matrix baseline selection: {matrix_baseline_selection['mode']} ({matrix_baseline_selection['path']})")
    else:
        print(f"Matrix baseline selection: {matrix_baseline_selection['mode']}")
    print(f"Matrix artifact comparison: {matrix_delta['status']}")

    try:
        workbench_summary = run_workbench_smoke_from_docs(docs_path, artifact_root=evidence_root)
    except ModuleNotFoundError as exc:
        optional_ui_modules = {"dash", "plotly", "pandas"}
        if exc.name not in optional_ui_modules:
            raise
        print('QCchem workbench smoke requires optional UI dependencies. Install with: pip install -e ".[ui]"')
        return 2
    except (OSError, ValueError) as exc:
        print(f"QCchem release evidence collection rejected: {exc}")
        return 2

    workbench_smoke_path.write_text(json.dumps(workbench_summary, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Workbench smoke summary written to {workbench_smoke_path}")
    print(f"Workbench smoke completed: {workbench_summary['status']}")
    print(f"Routes: {workbench_summary['passed_routes']} passed, {workbench_summary['failed_routes']} failed")
    print(f"Registered pages: {workbench_summary['passed_pages']} passed, {workbench_summary['failed_pages']} failed")
    _print_workbench_smoke_failed_summary(workbench_summary)

    summary = _release_evidence_summary(
        artifact_dir=artifact_dir,
        evidence_root=evidence_root,
        release_history=release_history,
        verification_path=verification_path,
        verification_report=verification_report,
        workbench_smoke_path=workbench_smoke_path,
        workbench_summary=workbench_summary,
        docs_path=docs_path,
        matrix_summary_path=matrix_summary_path,
        matrix_summary=matrix_summary,
        matrix_delta=matrix_delta,
        matrix_baseline_selection=matrix_baseline_selection,
        summary_path=summary_path,
        handoff_path=handoff_path,
    )
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    handoff_path.write_text(_release_evidence_handoff_markdown(summary), encoding="utf-8")
    print(f"Release evidence summary: {summary['status']}")
    print(f"Release evidence JSON: {summary_path}")
    print(f"Release evidence handoff: {handoff_path}")
    return 0 if summary["status"] == "passed" else 2


def _resolve_ci_artifact_download_dir(run_id: str, download_dir: Path | None) -> tuple[Path, bool]:
    if download_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"qcchem-ci-{run_id}-artifacts."))
        return temp_dir, True
    try:
        if download_dir.exists() and any(download_dir.iterdir()):
            raise ValueError(f"CI artifact download directory is not empty: {download_dir}")
    except OSError as exc:
        raise ValueError(f"CI artifact download directory is not readable: {download_dir}") from exc
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir, False


def _download_ci_release_artifacts(
    *,
    run_id: str,
    repo: str | None,
    download_dir: Path,
) -> int:
    command = ["gh", "run", "download", run_id, "--dir", str(download_dir)]
    if repo:
        command.extend(["--repo", repo])
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("QCchem release evidence fetch requires the GitHub CLI (`gh`) on PATH.")
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"QCchem release evidence fetch failed: gh run download exited with code {exc.returncode}")
        return 2
    return 0


def _run_release_fetch_ci_evidence_command(
    *,
    run_id: str,
    repo: str | None,
    download_dir: Path | None,
    docs_path: Path,
    history_root: Path,
    history_label: str | None,
    baseline_summary_path: Path | None,
    baseline_search_root: Path | None,
) -> int:
    try:
        resolved_download_dir, generated_download_dir = _resolve_ci_artifact_download_dir(run_id, download_dir)
    except ValueError as exc:
        print(f"QCchem release evidence fetch rejected: {exc}")
        return 2

    print(f"Downloading CI release artifacts: run_id={run_id}")
    if repo:
        print(f"GitHub repository: {repo}")
    print(f"CI artifact download dir: {resolved_download_dir}")
    download_status = _download_ci_release_artifacts(
        run_id=run_id,
        repo=repo,
        download_dir=resolved_download_dir,
    )
    if download_status != 0:
        return download_status

    effective_history_label = history_label or run_id
    if generated_download_dir:
        print("CI artifact download dir was created automatically and left on disk for provenance review.")
    return _run_release_collect_evidence_command(
        resolved_download_dir,
        docs_path,
        None,
        baseline_summary_path,
        baseline_search_root,
        history_root,
        effective_history_label,
    )


def _release_history_list_count(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _release_history_first_list_item(value: object) -> object | None:
    if isinstance(value, list) and value:
        return value[0]
    return None


def _release_history_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _release_history_incomplete_run_summary(
    *,
    run_root: Path,
    status: str,
    reason: str,
    error: str | None = None,
) -> dict[str, object]:
    summary_path = run_root / "release_evidence_summary.json"
    first_failure: dict[str, object] = {
        "reason": reason,
        "path": str(summary_path),
    }
    if error is not None:
        first_failure["error"] = error
    return {
        "label": run_root.name,
        "status": status,
        "recommended_action": "rerun_collect_evidence_or_remove_incomplete_run",
        "collection_mode": None,
        "artifact_dir": None,
        "evidence_root": str(run_root),
        "summary_path": str(summary_path),
        "outputs": {},
        "first_failure": first_failure,
        "release_history": {
            "mode": "retained_history",
            "root": str(run_root.parent),
            "label": run_root.name,
            "path": str(run_root),
            "baseline_search_root": str(run_root.parent),
        },
        "release_artifact_verification": {
            "status": "not_available",
            "failure_count": None,
            "first_failure": None,
        },
        "release_matrix_summary": {
            "artifact_count": None,
            "failed_artifact_count": None,
            "first_failed_artifact": None,
        },
        "release_matrix_baseline_selection": {
            "mode": "not_available",
            "path": None,
            "search_root": None,
            "candidate_count": None,
            "reason": reason,
        },
        "release_matrix_delta": {
            "status": "not_available",
            "reason": reason,
            "baseline_path": None,
            "current_artifact_count": None,
            "baseline_artifact_count": None,
            "added_count": 0,
            "removed_count": 0,
            "changed_count": 0,
            "unchanged_count": None,
            "first_change": None,
            "first_failure": first_failure,
        },
        "workbench_smoke": {
            "status": "not_available",
            "route_count": None,
            "failed_routes": None,
            "page_count": None,
            "failed_pages": None,
            "failed_check_count": None,
            "first_failed_check": None,
        },
    }


def _release_history_matrix_delta_summary(delta: dict[str, object]) -> dict[str, object]:
    return {
        "status": delta.get("status") or "not_available",
        "reason": delta.get("reason"),
        "baseline_path": delta.get("baseline_path"),
        "current_artifact_count": delta.get("current_artifact_count"),
        "baseline_artifact_count": delta.get("baseline_artifact_count"),
        "added_count": _release_history_list_count(delta.get("added")),
        "removed_count": _release_history_list_count(delta.get("removed")),
        "changed_count": _release_history_list_count(delta.get("changed")),
        "unchanged_count": delta.get("unchanged_count"),
        "first_change": delta.get("first_change") if isinstance(delta.get("first_change"), dict) else None,
        "first_failure": delta.get("first_failure") if isinstance(delta.get("first_failure"), dict) else None,
    }


def _release_history_run_summary(run_root: Path) -> dict[str, object]:
    summary_path = run_root / "release_evidence_summary.json"
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _release_history_incomplete_run_summary(
            run_root=run_root,
            status="missing_summary",
            reason="release_evidence_summary_missing",
        )
    except (OSError, json.JSONDecodeError) as exc:
        return _release_history_incomplete_run_summary(
            run_root=run_root,
            status="unreadable_summary",
            reason="release_evidence_summary_unreadable",
            error=f"{type(exc).__name__}: {exc}",
        )
    if not isinstance(payload, dict):
        return _release_history_incomplete_run_summary(
            run_root=run_root,
            status="invalid_summary",
            reason="release_evidence_summary_not_object",
        )

    verification = _release_history_dict(payload.get("release_artifact_verification"))
    matrix_summary = _release_history_dict(payload.get("release_matrix_summary"))
    matrix_artifacts = matrix_summary.get("artifacts") if isinstance(matrix_summary.get("artifacts"), list) else []
    failed_matrix_artifacts = [
        artifact
        for artifact in matrix_artifacts
        if isinstance(artifact, dict) and artifact.get("status") != "passed"
    ]
    baseline_selection = _release_history_dict(payload.get("release_matrix_baseline_selection"))
    matrix_delta = _release_history_matrix_delta_summary(_release_history_dict(payload.get("release_matrix_delta")))
    workbench = _release_history_dict(payload.get("workbench_smoke"))
    failed_checks = workbench.get("failed_checks") if isinstance(workbench.get("failed_checks"), list) else []
    status = str(payload.get("status") or "unknown")
    first_failure = payload.get("first_failure") if isinstance(payload.get("first_failure"), dict) else None
    if status != "passed" and first_failure is None:
        first_failure = {
            "reason": "release_evidence_status_not_passed",
            "path": str(summary_path),
            "status": status,
        }
    release_history = _release_history_dict(payload.get("release_history"))
    if not release_history:
        release_history = {
            "mode": "not_available",
            "root": str(run_root.parent),
            "label": run_root.name,
            "path": str(run_root),
            "baseline_search_root": None,
        }

    return {
        "label": run_root.name,
        "status": status,
        "recommended_action": payload.get("recommended_action"),
        "collection_mode": payload.get("collection_mode"),
        "artifact_dir": payload.get("artifact_dir"),
        "evidence_root": payload.get("evidence_root") or str(run_root),
        "summary_path": str(summary_path),
        "outputs": payload.get("outputs") if isinstance(payload.get("outputs"), dict) else {},
        "first_failure": first_failure,
        "release_history": release_history,
        "release_artifact_verification": {
            "status": verification.get("status") or "not_available",
            "failure_count": verification.get("failure_count"),
            "first_failure": verification.get("first_failure")
            if isinstance(verification.get("first_failure"), dict)
            else None,
        },
        "release_matrix_summary": {
            "artifact_count": matrix_summary.get("artifact_count"),
            "failed_artifact_count": matrix_summary.get("failed_artifact_count"),
            "first_failed_artifact": failed_matrix_artifacts[0] if failed_matrix_artifacts else None,
        },
        "release_matrix_baseline_selection": {
            "mode": baseline_selection.get("mode") or "not_available",
            "path": baseline_selection.get("path"),
            "search_root": baseline_selection.get("search_root"),
            "candidate_count": baseline_selection.get("candidate_count"),
            "reason": baseline_selection.get("reason"),
        },
        "release_matrix_delta": matrix_delta,
        "workbench_smoke": {
            "status": workbench.get("status") or "not_available",
            "route_count": workbench.get("route_count"),
            "failed_routes": workbench.get("failed_routes"),
            "page_count": workbench.get("page_count"),
            "failed_pages": workbench.get("failed_pages"),
            "failed_check_count": len(failed_checks),
            "first_failed_check": _release_history_first_list_item(failed_checks),
        },
    }


def _release_history_first_failure(runs: list[dict[str, object]]) -> dict[str, object] | None:
    for run in runs:
        if run.get("status") == "passed":
            continue
        first_failure = run.get("first_failure") if isinstance(run.get("first_failure"), dict) else None
        reason = first_failure.get("reason") if first_failure is not None else "release_history_run_not_passed"
        path = first_failure.get("path") if first_failure is not None else run.get("summary_path")
        return {
            "label": run.get("label"),
            "status": run.get("status"),
            "reason": reason,
            "path": path,
            "failure": first_failure,
        }
    return None


def _release_history_status_counts(runs: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        value = run.get(key)
        if isinstance(value, dict):
            status = str(value.get("status") or "not_available")
        else:
            status = str(value or "not_available")
        counts[status] = counts.get(status, 0) + 1
    return {name: counts[name] for name in sorted(counts)}


def _release_history_summary(history_root: Path) -> dict[str, object]:
    if not history_root.exists() or not history_root.is_dir():
        raise ValueError(f"--history-root is not a directory: {history_root}")
    try:
        children = sorted(history_root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise ValueError(f"--history-root is not readable: {history_root}") from exc

    run_roots = [child for child in children if child.is_dir()]
    skipped_non_directory_count = len(children) - len(run_roots)
    runs = [_release_history_run_summary(run_root) for run_root in run_roots]
    passed_run_count = sum(1 for run in runs if run.get("status") == "passed")
    failed_run_count = sum(1 for run in runs if run.get("status") == "failed")
    incomplete_run_count = sum(1 for run in runs if run.get("status") not in {"passed", "failed"})
    if not runs:
        status = "empty"
    elif passed_run_count == len(runs):
        status = "passed"
    elif failed_run_count:
        status = "failed"
    else:
        status = "incomplete"

    return {
        "schema_version": RELEASE_HISTORY_SUMMARY_SCHEMA_VERSION,
        "status": status,
        "recommended_action": "review_release_history"
        if status == "passed"
        else "collect_release_evidence"
        if status == "empty"
        else "inspect_release_history_failures",
        "history_root": str(history_root),
        "run_count": len(runs),
        "passed_run_count": passed_run_count,
        "failed_run_count": failed_run_count,
        "incomplete_run_count": incomplete_run_count,
        "skipped_non_directory_count": skipped_non_directory_count,
        "first_failure": _release_history_first_failure(runs),
        "run_status_counts": _release_history_status_counts(runs, "status"),
        "matrix_delta_status_counts": _release_history_status_counts(runs, "release_matrix_delta"),
        "release_artifact_verification_status_counts": _release_history_status_counts(
            runs,
            "release_artifact_verification",
        ),
        "workbench_smoke_status_counts": _release_history_status_counts(runs, "workbench_smoke"),
        "runs": runs,
    }


def _print_release_history_summary(summary: dict[str, object]) -> None:
    print(f"Release history summary: {summary.get('status')}")
    print(f"History root: {summary.get('history_root')}")
    print(
        "Runs: "
        f"{summary.get('run_count')} total, "
        f"{summary.get('passed_run_count')} passed, "
        f"{summary.get('failed_run_count')} failed, "
        f"{summary.get('incomplete_run_count')} incomplete"
    )
    runs = summary.get("runs") if isinstance(summary.get("runs"), list) else []
    for run in runs:
        if not isinstance(run, dict):
            continue
        delta = _release_history_dict(run.get("release_matrix_delta"))
        baseline = _release_history_dict(run.get("release_matrix_baseline_selection"))
        verification = _release_history_dict(run.get("release_artifact_verification"))
        workbench = _release_history_dict(run.get("workbench_smoke"))
        print(
            f"- {run.get('label')}: "
            f"status={run.get('status')} "
            f"delta={delta.get('status')} "
            f"baseline={baseline.get('mode')} "
            f"verification={verification.get('status')} "
            f"workbench={workbench.get('status')}"
        )
    first_failure = summary.get("first_failure")
    if isinstance(first_failure, dict):
        line = (
            f"First failure: label={first_failure.get('label')} "
            f"reason={first_failure.get('reason')}"
        )
        if first_failure.get("path"):
            line += f" path={first_failure.get('path')}"
        failure = first_failure.get("failure")
        if isinstance(failure, dict):
            line += f" detail={_release_failure_handoff_text(failure)}"
        print(line)


def _run_release_history_summarize_command(
    *,
    history_root: Path,
    output_path: Path | None,
    strict: bool,
) -> int:
    try:
        summary = _release_history_summary(history_root)
    except ValueError as exc:
        print(f"QCchem release history summary rejected: {exc}")
        return 2
    _print_release_history_summary(summary)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Release history summary JSON: {output_path}")
    return 2 if strict and summary.get("status") != "passed" else 0


def _run_release_evidence_handoff_command(
    *,
    audit_dir: Path,
    workbench_smoke_path: Path,
    acceptance_status_path: Path,
    output_dir: Path,
    strict: bool,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = _local_release_evidence_summary(
        audit_dir=audit_dir,
        workbench_smoke_path=workbench_smoke_path,
        acceptance_status_path=acceptance_status_path,
        output_dir=output_dir,
    )
    summary_path = output_dir / "release_evidence_summary.json"
    handoff_path = output_dir / "release_evidence_handoff.md"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    handoff_path.write_text(_release_evidence_handoff_markdown(summary), encoding="utf-8")
    print(f"Release evidence handoff: {summary.get('status')}")
    print(f"Release evidence JSON: {summary_path}")
    print(f"Release evidence handoff Markdown: {handoff_path}")
    first_failure = summary.get("first_failure")
    if isinstance(first_failure, dict):
        line = f"First failure: {first_failure.get('reason')}"
        if first_failure.get("path"):
            line += f" path={first_failure.get('path')}"
        print(line)
    return 2 if strict and summary.get("status") != "passed" else 0


def _ensure_active_space_recommendation_spec(spec) -> None:
    from qcchem.core import ActiveSpaceSpec, AutoActiveSpaceSpec

    active_space = spec.problem.active_space
    if active_space is None or active_space.selection_mode.strip().lower() != "auto":
        spec.problem.active_space = ActiveSpaceSpec(
            num_spatial_orbitals=(active_space.num_spatial_orbitals if active_space is not None else None),
            selection_mode="auto",
            auto=AutoActiveSpaceSpec(enabled=True, strategy="trusted_orbital_score"),
        )
        return
    if active_space.auto.strategy.strip().lower() == "frontier_orbitals":
        active_space.auto.strategy = "trusted_orbital_score"
    active_space.auto.enabled = True


def _active_space_yaml_patch(recommendation: dict[str, object]) -> dict[str, object]:
    selected = recommendation.get("selected") if isinstance(recommendation, dict) else {}
    if not isinstance(selected, dict):
        selected = {}
    return {
        "problem": {
            "active_space": {
                "selection_mode": "auto",
                "num_electrons": selected.get("num_electrons"),
                "num_spatial_orbitals": selected.get("num_spatial_orbitals"),
                "active_orbitals": selected.get("active_orbitals_original"),
                "auto": {
                    "enabled": True,
                    "strategy": "trusted_orbital_score",
                },
            }
        }
    }


def recommend_active_space_from_config(config: Path) -> dict[str, object]:
    """Build a classical active-space recommendation preview from a run config."""
    spec = load_run_spec(config)
    _ensure_active_space_recommendation_spec(spec)
    chemistry = build_electronic_structure_context(spec)
    active_space_metadata = chemistry.summary.active_space_metadata or {}
    recommendation = active_space_metadata.get("recommendation")
    if not isinstance(recommendation, dict):
        selected = {
            "num_electrons": list(active_space_metadata.get("num_electrons", [])),
            "num_spatial_orbitals": active_space_metadata.get("num_spatial_orbitals"),
            "active_orbitals": active_space_metadata.get("active_orbitals", []),
            "active_orbitals_original": active_space_metadata.get("active_orbitals_original", []),
        }
        recommendation = {
            "strategy": chemistry.reduction_audit.selection_mode,
            "confidence": None,
            "selected": selected,
            "candidates": [selected],
            "warnings": ["No trusted-score recommendation metadata was produced."],
            "provenance": {"source": "qcchem.cli.active_space_recommend"},
        }
    payload = dict(recommendation)
    payload["yaml_patch"] = _active_space_yaml_patch(payload)
    payload["reduction_audit"] = to_primitive(chemistry.reduction_audit)
    return to_primitive(payload)


def main(argv: list[str] | None = None) -> int:
    """Run the QCchem CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            result = run_from_config(
                args.config,
                output_dir=args.output_dir,
                confirm_runtime_budget=args.confirm_runtime_budget,
            )
        except (FileExistsError, ValueError) as exc:
            print(f"QCchem run rejected: {exc}")
            return 2
        print(f"QCchem run completed: {result.problem.molecule_name}")
        print(f"Verification status: {result.verification_status}")
        print(f"Total energy: {result.energy.total_energy:.12f} {result.energy.energy_units}")
        if result.evidence_summary is not None:
            print(f"Best evidence: {result.evidence_summary.primary_scientific_claim}")
            print(f"Trust tier: {result.evidence_summary.trust_tier}")
            print(f"Recommended action: {result.evidence_summary.recommended_action}")
        if result.noise_model is not None:
            print(f"Noise model: {result.noise_model.profile} ({result.noise_model.model_kind})")
        if result.runtime_options is not None:
            print(
                "Runtime snapshot: "
                f"service={result.runtime_options.service}, "
                f"session_ready={result.runtime_options.session_ready}, "
                f"batch_ready={result.runtime_options.batch_ready}, "
                f"low_rank_workload={result.runtime_options.low_rank_workload}"
            )
        if result.measurement is not None:
            measurement_scope = ""
            if (
                result.qft_model is not None
                and (result.qft_model.engine or {}).get("pauli_materialization") == "skipped"
            ):
                measurement_scope = " (sparse/exploratory estimate; not hardware measurement cost)"
            print(
                "Measurement plan: "
                f"strategy={result.measurement.strategy}, "
                f"groups={result.measurement.group_count}, "
                f"estimated_cost={result.measurement.estimated_shot_cost:.0f}"
                f"{measurement_scope}"
            )
        if result.calibration is not None:
            print(
                "Calibration: "
                f"measured_wall_time={result.calibration.measured_wall_time_seconds:.3f}s, "
                f"measured_cost={result.calibration.measured_shot_usage}, "
                f"achieved_error={result.calibration.achieved_error}"
            )
        if result.reduction_audit is not None and result.reduction_audit.selection_mode != "none":
            print(
                "Reduction audit: "
                f"mode={result.reduction_audit.selection_mode}, "
                f"transformers={result.reduction_audit.transformers_applied}"
            )
        if result.compression_result is not None:
            print(
                "Compression audit: "
                f"method={result.compression_result.method}, "
                f"status={result.compression_result.verification_status}"
            )
        if result.benchmark.compressed_vs_uncompressed is not None:
            print(
                "Compressed comparison: "
                f"abs_error={result.benchmark.compressed_vs_uncompressed.absolute_error:.6e}, "
                f"terms={result.benchmark.compressed_vs_uncompressed.pre_term_count}"
                f"->{result.benchmark.compressed_vs_uncompressed.post_term_count}"
            )
        if result.perturbative_correction_result is not None:
            print(
                "Perturbative correction: "
                f"method={result.perturbative_correction_result.method}, "
                f"status={result.perturbative_correction_result.verification_status}"
            )
        if result.embedding_result is not None:
            print(
                "Embedding audit: "
                f"method={result.embedding_result.method}, "
                f"status={result.embedding_result.verification_status}"
            )
        if result.tc_qsci_result is not None:
            print(
                "TC-QSCI: "
                f"subspace_dimension={result.tc_qsci_result.get('subspace_dimension')}, "
                f"status={result.tc_qsci_result.get('verification_status')}"
            )
        if result.runtime_submission is not None:
            print(
                "Runtime submission: "
                f"attempted={result.runtime_submission.attempted}, "
                f"submitted={result.runtime_submission.submitted}, "
                f"failure={result.runtime_submission.failure_category}"
            )
        if result.excited_state_result is not None:
            print(f"Excited-state task: {result.excited_state_result.verification_status}")
        if result.property_result is not None:
            print(f"Property task: {result.property_result.verification_status}")
        if result.artifacts.qcschema_json is not None:
            print(f"QCSchema export: {result.artifacts.qcschema_json}")
        if result.artifacts.hdf5_file is not None:
            print(f"HDF5 export: {result.artifacts.hdf5_file}")
        print(f"Artifacts: {result.artifacts.root}")
        return 0

    if args.command == "report":
        payload = json.loads(args.result_json.read_text(encoding="utf-8"))
        output_path = args.output or args.result_json.with_name("report.md")
        write_markdown_report(payload, output_path)
        print(f"Report written to {output_path}")
        return 0

    if args.command == "inspect":
        spec = load_run_spec(args.config)
        print(json.dumps(to_primitive(spec), indent=2, sort_keys=True))
        return 0

    if args.command == "active-space":
        if args.active_space_command == "recommend":
            try:
                payload = recommend_active_space_from_config(args.config)
            except ValueError as exc:
                print(f"Active-space recommendation rejected: {exc}")
                return 2
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
                print(f"Active-space recommendation written to {args.output}")
            else:
                print(json.dumps(payload, indent=2, sort_keys=True))
            if args.emit_yaml_patch:
                print(yaml.safe_dump(payload.get("yaml_patch", {}), sort_keys=False).strip())
            return 0

    if args.command == "study":
        if args.study_command == "run":
            try:
                result = run_study_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    overwrite=args.overwrite,
                )
            except FileExistsError as exc:
                print(f"Study rejected: {exc}")
                return 2
            print(f"Study completed: {result.study_name}")
            print(f"Runs: {result.summary.total_runs}")
            if result.evidence_summary is not None:
                print(f"Best evidence: {result.evidence_summary.primary_scientific_claim}")
                print(f"Trust tier: {result.evidence_summary.trust_tier}")
                print(f"Recommended action: {result.evidence_summary.recommended_action}")
            print(f"Artifacts: {result.artifacts.root}")
            return 0
        if args.study_command == "report":
            return _write_aggregate_from_json(args.result_json, args.output, kind="study")

    if args.command == "benchmark":
        if args.benchmark_command == "run":
            try:
                result = run_benchmark_suite_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    confirm_runtime_budget=args.confirm_runtime_budget,
                    include_tags=args.include_tag,
                    exclude_tags=args.exclude_tag,
                    overwrite=args.overwrite,
                )
            except (FileExistsError, ValueError) as exc:
                print(f"Benchmark suite rejected: {exc}")
                return 2
            if isinstance(result, dict):
                summary = result.get("summary", {})
                print(f"Benchmark suite completed: {result.get('suite_name')}")
                print(f"Cases: {summary.get('total_cases')}")
                evidence_summary = result.get("evidence_summary") or {}
                if evidence_summary:
                    print(f"Best evidence: {evidence_summary.get('primary_scientific_claim')}")
                    print(f"Trust tier: {evidence_summary.get('trust_tier')}")
                    print(f"Recommended action: {evidence_summary.get('recommended_action')}")
                print(
                    "Runtime evidence status counts: "
                    f"{summary.get('runtime_evidence_status_counts', {})}"
                )
                print(f"Artifacts: {result.get('artifact_root')}")
                return _acceptance_exit_code(result.get("acceptance_summary"))
            print(f"Benchmark suite completed: {result.suite_name}")
            print(f"Cases: {result.summary.total_cases}")
            print(f"Status counts: {result.summary.status_counts}")
            if result.evidence_summary is not None:
                print(f"Best evidence: {result.evidence_summary.primary_scientific_claim}")
                print(f"Trust tier: {result.evidence_summary.trust_tier}")
                print(f"Recommended action: {result.evidence_summary.recommended_action}")
            print(f"Artifacts: {result.artifacts.root}")
            return _acceptance_exit_code(getattr(result, "acceptance_summary", None))
        if args.benchmark_command == "report":
            return _write_aggregate_from_json(args.result_json, args.output, kind="benchmark")
        if args.benchmark_command == "accept":
            summary = accept_benchmark_result(args.result_json, output_path=args.output)
            print(f"Benchmark acceptance: {'accepted' if summary['accepted'] else 'failed'}")
            print(f"Blocking failures: {len(summary['blocking_failures'])}")
            print(f"Recommended action: {summary['recommended_action']}")
            return 0 if summary["accepted"] else 2

    if args.command == "artifacts":
        if args.artifacts_command == "index":
            index = build_artifact_index(args.artifact_root)
            output = args.output or args.artifact_root / "artifact_index.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(to_primitive(index), indent=2, sort_keys=True), encoding="utf-8")
            print(f"Artifact index written to {output}")
            print(f"Artifacts: {index['total_artifacts']}")
            return 0
        if args.artifacts_command == "capsule":
            if args.recursive:
                index = build_artifact_index(args.artifact_root)
                output_dir = args.output_dir or args.artifact_root / "capsules"
                capsules = []
                for entry in index.get("artifacts", []):
                    root = Path(str(entry["artifact_root"]))
                    capsules.append(build_and_write_evidence_capsule(root, output_dir / root.name))
                summary = {
                    "schema_version": "qcchem.evidence_capsule.batch.v0.1-alpha",
                    "artifact_root": str(args.artifact_root),
                    "total_capsules": len(capsules),
                    "capsules": capsules,
                }
                output_dir.mkdir(parents=True, exist_ok=True)
                output = output_dir / "evidence_capsules.json"
                output.write_text(json.dumps(to_primitive(summary), indent=2, sort_keys=True), encoding="utf-8")
                print(f"Evidence capsule batch written to {output}")
                print(f"Capsules: {len(capsules)}")
                return 0 if all(item.get("capsule_status") != "invalid" for item in capsules) else 2
            capsule = build_and_write_evidence_capsule(args.artifact_root, args.output_dir)
            print(f"Evidence capsule written to {capsule['outputs']['capsule_json']}")
            print(f"Capsule status: {capsule['capsule_status']}")
            print(f"Trust tier: {capsule['trust_tier']}")
            print(f"Recommended action: {capsule['recommended_action']}")
            return 0 if capsule["capsule_status"] != "invalid" else 2

    if args.command == "objective":
        if args.objective_command == "init":
            path = write_objective_template(name=args.name, claim=args.claim, output_path=args.output)
            print(f"Objective template written to {path}")
            return 0
        if args.objective_command == "plan":
            payload = plan_research_objective(args.config, args.output_dir)
            print(f"Objective plan written to {payload['outputs']['json']}")
            print(f"Objective: {payload['objective_name']}")
            print(f"Status: {payload['status']}")
            print(f"Recommended action: {payload['recommended_action']}")
            return 0
        if args.objective_command == "status":
            target = args.config or args.target
            if target is None:
                print("Objective status requires either -c/--config or a target path.")
                return 2
            payload = status_research_objective(target, args.output_dir)
            print(f"Objective status written to {payload['outputs']['json']}")
            print(f"Objective: {payload['objective_name']}")
            print(f"Status: {payload['status']}")
            print(f"Recommended action: {payload['recommended_action']}")
            return 0

    if args.command == "claim":
        if args.claim_command == "check":
            claim_text = args.claim_file.read_text(encoding="utf-8").strip() if args.claim_file else str(args.claim)
            review = compile_claim_review(claim_text=claim_text, targets=args.target, workspace_base=Path.cwd())
            outputs = write_claim_review_outputs(review, args.output_dir)
            review["outputs"] = outputs
            print(f"Claim review written to {outputs['claim_review_json']}")
            print(f"Support level: {review['support_level']}")
            print(f"Recommended action: {review['recommended_action']}")
            return 0 if review["status"] == "passed" else 2

    if args.command == "promote":
        if args.promote_command == "exploratory":
            review = review_exploratory_promotion(artifact=args.artifact, target=args.target)
            outputs = write_promotion_outputs(review, args.output_dir)
            review["outputs"] = outputs
            print(f"Promotion review written to {outputs['promotion_review_json']}")
            print(f"Status: {review['status']}")
            print(f"Recommended action: {review['recommended_action']}")
            return 0 if review["status"] != "blocked" else 2

    if args.command == "campaign":
        if args.campaign_command == "run":
            try:
                summary = run_campaign_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    overwrite=args.overwrite,
                )
            except FileExistsError as exc:
                print(f"Campaign rejected: {exc}")
                return 2
            print(f"Campaign completed: {summary['campaign_name']}")
            print(f"Status: {summary['status']}")
            print(f"Artifacts: {summary['artifact_root']}")
            return 0 if summary["acceptance_summary"]["accepted"] else 2
        if args.campaign_command == "report":
            report_campaign_result(args.result_json, output_path=args.output)
            print(f"Campaign report written to {args.output or args.result_json.with_name('campaign_report.md')}")
            return 0
        if args.campaign_command == "accept":
            summary = accept_campaign_result(args.result_json, output_path=args.output)
            print(f"Campaign acceptance: {'accepted' if summary['accepted'] else 'failed'}")
            print(f"Blocking failures: {len(summary['blocking_failures'])}")
            print(f"Recommended action: {summary['recommended_action']}")
            return 0 if summary["accepted"] else 2

    if args.command == "scan":
        if args.scan_command == "run":
            try:
                result = run_scan_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    overwrite=args.overwrite,
                )
            except FileExistsError as exc:
                print(f"Scan rejected: {exc}")
                return 2
            print(f"Scan completed: {result.scan_name}")
            print(f"Points: {result.summary.total_runs}")
            if result.evidence_summary is not None:
                print(f"Best evidence: {result.evidence_summary.primary_scientific_claim}")
                print(f"Trust tier: {result.evidence_summary.trust_tier}")
                print(f"Recommended action: {result.evidence_summary.recommended_action}")
            print(f"Artifacts: {result.artifacts.root}")
            return 0
        if args.scan_command == "report":
            return _write_aggregate_from_json(args.result_json, args.output, kind="scan")

    if args.command == "exploratory":
        if args.exploratory_command == "run":
            try:
                result = run_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    exploratory_command=True,
                    confirm_runtime_budget=args.confirm_runtime_budget,
                )
            except (FileExistsError, ValueError) as exc:
                print(f"QCchem exploratory run rejected: {exc}")
                return 2
            print(f"QCchem exploratory run completed: {result.problem.molecule_name}")
            print(f"Verification status: {result.verification_status}")
            print(f"Module origin: {result.module_origin}")
            print(f"Capability tier: {result.capability_tier}")
            if result.evidence_summary is not None:
                print(f"Trust tier: {result.evidence_summary.trust_tier}")
                print(f"Recommended action: {result.evidence_summary.recommended_action}")
            if getattr(result, "qft_model", None) is not None:
                engine = result.qft_model.engine or {}
                print(
                    "QFT engine: "
                    f"representation={engine.get('actual_representation')}, "
                    f"projected_dimension={engine.get('projected_dimension')}"
                )
            if result.tc_qsci_result is not None:
                print(
                    "TC-QSCI: "
                    f"subspace_dimension={result.tc_qsci_result.get('subspace_dimension')}, "
                    f"status={result.tc_qsci_result.get('verification_status')}"
                )
            print(f"Artifacts: {result.artifacts.root}")
            return 0

    if args.command == "workbench":
        if args.workbench_command == "serve":
            return _run_workbench_command(args.host, args.port, args.debug, artifact_root=args.artifact_root)
        if args.workbench_command == "smoke":
            return _run_workbench_smoke_command(args.docs, args.output, artifact_root=args.artifact_root)

    if args.command == "runtime":
        if args.runtime_command == "collect":
            summary = collect_runtime_artifact(args.artifact_root)
            print("Runtime collect completed")
            print(f"Artifact root: {summary['artifact_root']}")
            print(f"Job id: {summary['job_id']}")
            print(f"Status: {summary['status']}")
            print(f"Result updated: {summary['result_updated']}")
            return 0

    if args.command == "release":
        if args.release_command == "audit":
            output_dir = args.output_dir
            if output_dir is None and args.repo_root is not None:
                output_dir = args.repo_root / "artifacts" / "release_audit"
            try:
                summary = run_release_audit_from_config(
                    args.config,
                    output_dir=output_dir,
                    repo_root=args.repo_root,
                )
            except (OSError, ValueError, yaml.YAMLError) as exc:
                print(f"Release audit rejected: {exc}")
                return 2
            print(f"Release audit completed: {summary['status']}")
            print(f"Required checks: {summary['required_pass_count']} passed, {summary['required_fail_count']} failed")
            _print_release_audit_triage(summary)
            _print_release_audit_sidecar_repair_triage(summary)
            report_dir = _release_audit_output_dir(summary, output_dir)
            print(f"Report: {report_dir / 'release_readiness.md'}")
            _print_release_audit_handoff_summary(report_dir)
            return 0 if summary["status"] == "passed" else 2
        if args.release_command == "status":
            audit_dir = _release_status_audit_dir(args.audit_dir, args.repo_root)
            summary = build_release_status_summary(audit_dir)
            _print_release_status_summary(summary)
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
                print(f"Status JSON: {args.output}")
            if summary.get("status") in {
                "missing_outputs",
                "unreadable_outputs",
                "schema_mismatch",
                "contract_mismatch",
            }:
                return 2
            if args.strict and summary.get("status") != "passed":
                return 2
            return 0
        if args.release_command == "verify-artifacts":
            report = verify_release_diagnostics_artifacts(args.artifact_dir)
            _print_release_artifact_verification_summary(report)
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
                print(f"Verification JSON: {args.output}")
            return 0 if report.get("status") == "passed" else 2
        if args.release_command == "collect-evidence":
            return _run_release_collect_evidence_command(
                args.artifact_dir,
                args.docs,
                args.output_dir,
                args.baseline_summary,
                args.baseline_search_root,
                args.history_root,
                args.history_label,
            )
        if args.release_command == "fetch-ci-evidence":
            return _run_release_fetch_ci_evidence_command(
                run_id=args.run_id,
                repo=args.repo,
                download_dir=args.download_dir,
                docs_path=args.docs,
                history_root=args.history_root,
                history_label=args.history_label,
                baseline_summary_path=args.baseline_summary,
                baseline_search_root=args.baseline_search_root,
            )
        if args.release_command == "history":
            if args.release_history_command == "summarize":
                return _run_release_history_summarize_command(
                    history_root=args.history_root,
                    output_path=args.output,
                    strict=args.strict,
                )
        if args.release_command == "evidence-handoff":
            return _run_release_evidence_handoff_command(
                audit_dir=args.audit_dir,
                workbench_smoke_path=args.workbench_smoke,
                acceptance_status_path=args.acceptance_status,
                output_dir=args.output_dir,
                strict=args.strict,
            )
        if args.release_command == "accept-artifact":
            try:
                if args.dry_run:
                    summary, output_path, status = preview_release_artifact_acceptance_summary_from_config(
                        args.config,
                        artifact_name=args.name,
                        repo_root=args.repo_root,
                        release_boundaries=args.boundary or None,
                    )
                else:
                    summary, output_path = write_release_artifact_acceptance_summary_from_config(
                        args.config,
                        artifact_name=args.name,
                        repo_root=args.repo_root,
                        overwrite=args.overwrite,
                        release_boundaries=args.boundary or None,
                    )
                    status = {}
            except (FileExistsError, OSError, ValueError, yaml.YAMLError) as exc:
                print(f"Release acceptance rejected: {exc}")
                return 2
            if args.dry_run:
                print(f"Release acceptance sidecar dry run: {output_path}")
                print(f"Current sidecar status: {status.get('status')}")
                print(
                    "Changed fields: "
                    f"{_release_acceptance_status_list_hint(status.get('changed_fields')) or 'none'}"
                )
                print(
                    "Preserved extra fields: "
                    f"{_release_acceptance_status_list_hint(status.get('would_preserve_extra_fields')) or 'none'}"
                )
                detail_hint = _release_acceptance_status_detail_hint(status)
                if detail_hint:
                    print(f"Current sidecar detail: {detail_hint}")
            else:
                print(f"Release acceptance sidecar written to {output_path}")
            print(f"Artifact: {summary['artifact_name']}")
            print(f"Trust tier: {summary['trust_tier']}")
            print(f"Runtime evidence status: {summary['runtime_evidence_status']}")
            print(f"Recommended action: {summary['recommended_action']}")
            return 0 if summary["accepted"] else 2
        if args.release_command == "acceptance-status":
            try:
                report = release_acceptance_status_report_from_config(
                    args.config,
                    repo_root=args.repo_root,
                )
                contract_failures = release_acceptance_status_contract_failures(report)
                if contract_failures:
                    raise ValueError(f"contract mismatch: {contract_failures}")
            except (OSError, ValueError, yaml.YAMLError) as exc:
                print(f"Release acceptance status rejected: {exc}")
                return 2
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
                print(f"Release acceptance status written to {args.output}")
            print(f"Release acceptance sidecars: {report['status']}")
            print(
                "Sidecars: "
                f"{report['fresh_count']} fresh, "
                f"{report['requires_update_count']} require update, "
                f"{report['total_sidecars']} total"
            )
            for item in report.get("items", []):
                if not isinstance(item, dict) or item.get("status") == "fresh":
                    continue
                print(
                    "Sidecar issue: "
                    f"{_release_acceptance_status_issue_line(item)}"
                )
            if args.repair_plan:
                _print_release_acceptance_repair_plan(report)
            return 2 if args.strict and report["status"] != "fresh" else 0

    if args.command == "validation":
        if args.validation_command == "qmmm":
            from qcchem.validation import run_qmmm_embedding_validation

            summary = run_qmmm_embedding_validation(args.output_dir, profile=args.profile)
            artifacts = summary.get("artifacts", {})
            print(f"QMMM validation completed: {summary.get('overall_status')}")
            print(f"Profile: {summary.get('profile')}")
            print(f"Cases: {summary.get('passed_cases')}/{summary.get('case_count')}")
            print(f"Result JSON: {artifacts.get('json')}")
            print(f"Report: {artifacts.get('markdown')}")
            print(f"Metrics CSV: {artifacts.get('csv')}")
            return 0 if summary.get("overall_status") == "passed" else 2
        if args.validation_command == "pbc-qmmm":
            from qcchem.validation import run_pbc_qmmm_validation

            summary = run_pbc_qmmm_validation(args.output_dir, profile=args.profile)
            artifacts = summary.get("artifacts", {})
            print(f"PBC-QMMM validation completed: {summary.get('overall_status')}")
            print(f"Profile: {summary.get('profile')}")
            print(f"Cases: {summary.get('passed_cases')}/{summary.get('case_count')}")
            print(f"Result JSON: {artifacts.get('json')}")
            print(f"Report: {artifacts.get('markdown')}")
            print(f"Metrics CSV: {artifacts.get('csv')}")
            return 0 if summary.get("overall_status") == "passed" else 2

    if args.command == "hardware":
        if args.hardware_command == "optimize":
            mode = "preview"
            if args.submit:
                mode = "submit"
            elif args.collect:
                mode = "collect"
            try:
                summary = run_hardware_optimization_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    mode=mode,
                    confirm_runtime_budget=args.confirm_runtime_budget,
                )
            except PermissionError as exc:
                print(f"Hardware optimization rejected: {exc}")
                return 2
            except ValueError as exc:
                print(f"Hardware optimization rejected: {exc}")
                return 2
            print(f"Hardware optimization {mode} completed: {summary.get('suite_name')}")
            print(f"Stop reason: {summary.get('stop_reason')}")
            print(f"Budget ledger: {summary.get('runtime_budget_ledger')}")
            print(f"Plan: {summary.get('plan_json')}")
            print(f"Report: {summary.get('report_markdown')}")
            return 0

    if args.command == "workflow":
        if args.workflow_command == "validate":
            try:
                summary = validate_workflow_from_config(args.config)
            except ValueError as exc:
                print(f"Workflow validation rejected: {exc}")
                return 2
            print(json.dumps(to_primitive(summary), indent=2, sort_keys=True))
            return 0
        if args.workflow_command == "run":
            try:
                result = run_custom_workflow_from_config(
                    args.config,
                    output_dir=args.output_dir,
                    overwrite=args.overwrite,
                )
            except (FileExistsError, ValueError) as exc:
                print(f"Workflow run rejected: {exc}")
                return 2
            print(f"Workflow completed: {result.workflow_name}")
            print(f"Status: {result.status}")
            print(f"Artifacts: {result.artifact_root}")
            print(f"Report: {result.outputs['workflow_report_markdown']}")
            return 0 if result.status == "completed" else 2
        if args.workflow_command == "report":
            outputs = report_custom_workflow_result(args.result_json, output_path=args.output)
            print(f"Workflow report written to {outputs['workflow_report_markdown']}")
            return 0
        if args.workflow_command == "plugins":
            print(json.dumps(to_primitive(workflow_plugins_summary(include_installed=not args.builtins_only)), indent=2, sort_keys=True))
            return 0
        if args.workflow_command == "template":
            path = write_workflow_template(args.output)
            print(f"Workflow template written to {path}")
            return 0

    if args.command == "agent":
        if args.agent_command == "validate-task":
            spec = load_agent_task_spec(args.task_file)
            print(f"Agent task is valid: {spec.name}")
            print(f"Kind: {spec.kind}")
            print(f"Source: {spec.source_path}")
            return 0
        if args.agent_command == "run-task":
            summary = run_agent_task_from_config(args.task_file)
            print(json.dumps(to_primitive(summary), indent=2, sort_keys=True))
            return 0
        if args.agent_command == "summarize":
            summary = summarize_agent_target(args.target)
            print(json.dumps(to_primitive(summary), indent=2, sort_keys=True))
            return 0

    if args.command == "ai":
        from qcchem.workflow.ai_workspace import draft_ticket_from_request, run_ticket

        if args.ai_command == "draft-ticket":
            ticket_path = draft_ticket_from_request(
                provider_config=args.provider_config,
                task_type=args.task_type,
                request_text=args.request,
                linked_artifacts=args.artifact,
            )
            print(json.dumps({"ticket_path": str(ticket_path)}, indent=2, sort_keys=True))
            return 0
        if args.ai_command == "run-ticket":
            result = run_ticket(args.ticket)
            print(json.dumps(to_primitive(result), indent=2, sort_keys=True))
            return 0
        if args.ai_command == "summarize-evidence":
            result = summarize_evidence_artifacts(args.artifact, workspace_base=Path.cwd())
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(to_primitive(result), indent=2, sort_keys=True), encoding="utf-8")
                append_ai_provenance_event(
                    workspace_base=Path.cwd(),
                    event_type="evidence_loaded",
                    summary="Summarized QCchem evidence artifacts from CLI.",
                    artifacts=[str(item) for item in args.artifact],
                    metadata={"output": str(args.output)},
                )
            print(json.dumps(to_primitive(result), indent=2, sort_keys=True))
            return 0
        if args.ai_command == "review":
            result = review_claims(targets=args.target, claim_text=args.claim, workspace_base=Path.cwd())
            if args.output_dir is not None:
                outputs = write_review_outputs(result, args.output_dir)
                result["outputs"] = outputs
                append_ai_provenance_event(
                    workspace_base=Path.cwd(),
                    event_type="claim_reviewed",
                    summary="Reviewed QCchem claim boundaries from CLI.",
                    artifacts=[str(item) for item in args.target],
                    metadata=outputs,
                )
            print(json.dumps(to_primitive(result), indent=2, sort_keys=True))
            return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
