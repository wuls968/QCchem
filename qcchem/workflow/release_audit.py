"""Trust-First release-readiness audit workflow."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from qcchem.core.evidence import summarize_artifact_payload
from qcchem.io.artifact_index import build_artifact_index
from qcchem.io.config import workspace_root_for_path
from qcchem.io.release_audit_config import (
    ReleaseAuditExploratoryAssetSpec,
    ReleaseAuditSpec,
    ReleaseAuditWarningPolicy,
    load_release_audit_spec,
)

RELEASE_AUDIT_SCHEMA_VERSION = "1.1"
RELEASE_HANDOFF_SCHEMA_VERSION = "qcchem.release_handoff.v0.1-alpha"
RELEASE_AUDIT_SCHEMA_FEATURES = [
    "failed_checks",
    "required_failed_checks",
    "warning_checks",
    "evidence_matrix_core_fields",
    "evidence_matrix_review_warnings",
    "warning_policy",
    "acceptance_commands",
    "acceptance_command_remediation",
    "ci_acceptance_command_alignment",
    "ci_acceptance_status_gate",
    "ci_release_diagnostic_artifacts",
    "acceptance_summary_source",
    "acceptance_schema_version",
    "acceptance_artifact_path",
    "acceptance_artifact_sha256",
    "acceptance_release_audit_check_id",
    "acceptance_trust_tier",
    "acceptance_runtime_evidence_status",
    "acceptance_status",
    "acceptance_recommended_action",
    "acceptance_blocking_failure_count",
    "acceptance_warning_count",
    "acceptance_contract_failure_count",
    "release_acceptance_sidecar_status",
    "release_acceptance_repair_plan",
    "audit_provenance",
]
RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION = "qcchem.release_artifact_acceptance.v0.1-alpha"
LEGACY_BENCHMARK_ACCEPTANCE_SCHEMA_VERSION = "qcchem.benchmark_acceptance.v0.1-alpha"
SUPPORTED_ACCEPTANCE_SCHEMA_VERSIONS = {
    RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION,
    LEGACY_BENCHMARK_ACCEPTANCE_SCHEMA_VERSION,
}
RELEASE_EVIDENCE_SUMMARY_REQUIRED_FIELDS = (
    "primary_scientific_claim",
    "primary_baseline",
    "primary_error_metric",
    "chemical_accuracy_status",
    "runtime_evidence_status",
    "trust_tier",
    "recommended_action",
)
SHELL_CONTROL_TOKENS = ("<<<", "&&", "||", "|&", ">>", "<<", ";", "|", "&", ">", "<")
SHELL_EXPANSION_TOKENS = ("$(", "${", "$", "`", "*", "?", "[")
PYTEST_PATH_VALUE_OPTIONS = {"--basetemp", "--rootdir", "--junitxml"}
PYTEST_VALUE_OPTIONS = PYTEST_PATH_VALUE_OPTIONS | {
    "-W",
    "-k",
    "-m",
    "--capture",
    "--color",
    "--durations",
    "--maxfail",
    "--tb",
}
CI_WORKFLOW_RELATIVE_PATH = Path(".github") / "workflows" / "ci.yml"
CI_ACCEPTANCE_STATUS_STEP_NAME = "Run release acceptance sidecar freshness"
CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_ENV = "QCCHEM_RELEASE_DIAGNOSTIC_ARTIFACT_NAME"
CI_ACCEPTANCE_STATUS_COMMAND_LINES = (
    "set -euo pipefail",
    "python -m qcchem.cli.main release acceptance-status \\",
    "-c configs/release/trust_first_audit.yaml \\",
    "--strict \\",
    "--repair-plan \\",
    "-o /tmp/qcchem-release-acceptance-status.json",
)
CI_RELEASE_DIAGNOSTIC_UPLOAD_STEP_NAME = "Upload release diagnostics"
CI_RELEASE_DIAGNOSTIC_UPLOAD_ACTION = "actions/upload-artifact@v7"
CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_PREFIX = "qcchem-release-diagnostics"
CI_RELEASE_DIAGNOSTIC_REQUIRED_PATHS = (
    "artifacts/workbench_smoke.json",
    "artifacts/release_audit/release_readiness.json",
    "artifacts/release_audit/release_readiness.md",
    "artifacts/release_audit/release_handoff.json",
    "artifacts/release_audit/release_handoff.md",
    "artifacts/release_audit/release_status.json",
    "/tmp/qcchem-release-acceptance-status.json",
    "/tmp/qcchem-wheel-smoke.json",
    "/tmp/qcchem-wheel-release-audit/release_readiness.json",
    "/tmp/qcchem-wheel-release-audit/release_readiness.md",
    "/tmp/qcchem-wheel-release-audit/release_handoff.json",
    "/tmp/qcchem-wheel-release-audit/release_handoff.md",
    "/tmp/qcchem-wheel-release-audit/release_status.json",
)
CI_RELEASE_DIAGNOSTIC_PRODUCER_STEPS = (
    "Build wheel and smoke installed package",
    "Run Workbench release smoke",
    "Run Trust-First release audit",
    CI_ACCEPTANCE_STATUS_STEP_NAME,
)


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _read_optional_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return _read_json(path), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _read_project_version(pyproject: Path) -> str | None:
    if not pyproject.exists():
        return None
    match = re.search(r'^\s*version\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def _check(
    checks: list[dict[str, Any]],
    *,
    check_id: str,
    label: str,
    passed: bool,
    required: bool = True,
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "id": check_id,
            "label": label,
            "status": "passed" if passed else "failed",
            "required": required,
            "summary": summary,
            "details": details or {},
        }
    )


def _skipped(
    checks: list[dict[str, Any]],
    *,
    check_id: str,
    label: str,
    required: bool = False,
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "id": check_id,
            "label": label,
            "status": "skipped",
            "required": required,
            "summary": summary,
            "details": details or {},
        }
    )


def _warning(
    checks: list[dict[str, Any]],
    *,
    check_id: str,
    label: str,
    summary: str = "",
    details: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "id": check_id,
            "label": label,
            "status": "warning",
            "required": False,
            "summary": summary,
            "details": details or {},
        }
    )


def _apply_warning_policy(
    checks: list[dict[str, Any]],
    policy: ReleaseAuditWarningPolicy | None,
) -> dict[str, Any] | None:
    if policy is None:
        return None

    warning_ids = [check["id"] for check in checks if check["status"] == "warning"]
    allowed_ids = set(policy.allowed_ids) if policy.allowed_ids is not None else None
    unexpected_ids = sorted(set(warning_ids) - allowed_ids) if allowed_ids is not None else []
    count_ok = policy.max_count is None or len(warning_ids) <= policy.max_count
    passed = count_ok and not unexpected_ids
    details = {
        "max_count": policy.max_count,
        "warning_count": len(warning_ids),
        "allowed_ids": sorted(allowed_ids) if allowed_ids is not None else None,
        "unexpected_ids": unexpected_ids,
    }
    _check(
        checks,
        check_id="release_warning_policy",
        label="Release audit warnings satisfy configured policy",
        passed=passed,
        required=True,
        summary=(
            "Warning count and warning ids satisfy the release policy."
            if passed
            else "Release audit produced warnings outside the configured policy."
        ),
        details=details,
    )
    return {"status": "passed" if passed else "failed", **details}


def _check_summaries(
    checks: list[dict[str, Any]],
    *,
    status: str,
    required: bool | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": check["id"],
            "label": check["label"],
            "status": check["status"],
            "required": check["required"],
            "summary": check.get("summary", ""),
            "details": check.get("details", {}),
        }
        for check in checks
        if check["status"] == status
        and (required is None or check["required"] is required)
    ]


def _repo_target_issue(repo_root: Path, value: str, *, require_file: bool = False) -> dict[str, str] | None:
    raw_path = value.split("::", 1)[0]
    if raw_path == "":
        return _empty_path_issue(repo_root, value)
    path = Path(raw_path)
    if path.is_absolute():
        return {"target": value, "resolved": str(path.resolve()), "reason": "absolute_path"}
    if raw_path.startswith("~"):
        return {"target": value, "resolved": str(path.expanduser()), "reason": "home_directory_path"}
    resolved = (repo_root / path).resolve()
    resolved_repo_root = repo_root.resolve()
    try:
        resolved.relative_to(resolved_repo_root)
    except ValueError:
        return {"target": value, "resolved": str(resolved), "reason": "outside_repo"}
    if ".." in path.parts:
        return {"target": value, "resolved": str(resolved), "reason": "parent_directory_path"}
    if not resolved.exists():
        return {"target": value, "resolved": str(resolved), "reason": "missing"}
    if require_file and not resolved.is_file():
        return {"target": value, "resolved": str(resolved), "reason": "not_file"}
    return None


def _empty_path_issue(repo_root: Path, value: str = "") -> dict[str, str]:
    return {"target": value, "resolved": str(repo_root.resolve()), "reason": "empty_path"}


def _repo_path_safety_issue(repo_root: Path, value: str) -> dict[str, str] | None:
    raw_path = value.split("::", 1)[0]
    if raw_path == "":
        return _empty_path_issue(repo_root, value)
    path = Path(raw_path)
    if path.is_absolute():
        return {"target": value, "resolved": str(path.resolve()), "reason": "absolute_path"}
    if raw_path.startswith("~"):
        return {"target": value, "resolved": str(path.expanduser()), "reason": "home_directory_path"}
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return {"target": value, "resolved": str(resolved), "reason": "outside_repo"}
    if ".." in path.parts:
        return {"target": value, "resolved": str(resolved), "reason": "parent_directory_path"}
    return None


def _repo_artifact_output_issue(repo_root: Path, value: str) -> dict[str, str] | None:
    path = Path(value)
    if value == "":
        return _empty_path_issue(repo_root, value)
    if path.is_absolute():
        return {"target": value, "resolved": str(path.resolve()), "reason": "absolute_path"}
    if value.startswith("~"):
        return {"target": value, "resolved": str(path.expanduser()), "reason": "home_directory_path"}
    resolved = (repo_root / path).resolve()
    resolved_repo_root = repo_root.resolve()
    try:
        resolved.relative_to(resolved_repo_root)
    except ValueError:
        return {"target": value, "resolved": str(resolved), "reason": "outside_repo"}
    if ".." in path.parts:
        return {"target": value, "resolved": str(resolved), "reason": "parent_directory_path"}
    if len(path.parts) < 2 or path.parts[0] != "artifacts":
        return {"target": value, "resolved": str(resolved), "reason": "outside_artifacts"}
    return None


def _looks_like_repo_path(value: str) -> bool:
    raw_path = value.split("::", 1)[0]
    path = Path(raw_path)
    top_level_roots = {"tests", "benchmarks", "configs", "docs", "examples"}
    return (
        path.is_absolute()
        or raw_path.startswith("~")
        or ".." in path.parts
        or (bool(path.parts) and path.parts[0] in top_level_roots)
        or raw_path.endswith((".py", ".yaml", ".yml", ".json", ".md"))
    )


def _shell_control_tokens(command: str) -> list[str]:
    return _unquoted_shell_tokens(command, SHELL_CONTROL_TOKENS)


def _shell_expansion_tokens(command: str) -> list[str]:
    tokens: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\":
            index += 2
            continue
        if quote == "'":
            if char == "'":
                quote = None
            index += 1
            continue
        if quote == '"':
            if char == '"':
                quote = None
                index += 1
                continue
            for token in ("$(", "${", "$", "`"):
                if command.startswith(token, index):
                    tokens.append(token)
                    index += len(token)
                    break
            else:
                index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        for token in SHELL_EXPANSION_TOKENS:
            if command.startswith(token, index):
                tokens.append(token)
                index += len(token)
                break
        else:
            index += 1
    return tokens


def _unquoted_shell_tokens(command: str, candidates: tuple[str, ...]) -> list[str]:
    tokens: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\":
            index += 2
            continue
        if quote is not None:
            if char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        for token in candidates:
            if command.startswith(token, index):
                tokens.append(token)
                index += len(token)
                break
        else:
            index += 1
    return tokens


def _protected_artifact_output_issue(
    repo_root: Path,
    value: str,
    protected_artifact_roots: set[Path],
) -> dict[str, str] | None:
    if not protected_artifact_roots:
        return None
    resolved = (repo_root / Path(value)).resolve()
    for protected_root in protected_artifact_roots:
        protected = (repo_root / protected_root).resolve()
        try:
            relative = resolved.relative_to(protected)
        except ValueError:
            continue
        if not relative.parts or relative.parts[0] != "preview_local":
            return {
                "target": value,
                "resolved": str(resolved),
                "reason": "protected_release_artifact_root",
                "protected_root": protected_root.as_posix(),
                "allowed_preview_root": (protected_root / "preview_local").as_posix(),
            }
    return None


def _acceptance_command_failures(
    commands: list[str],
    *,
    repo_root: Path,
    protected_artifact_roots: set[Path] | None = None,
) -> list[dict[str, Any]]:
    protected_artifact_roots = protected_artifact_roots or set()
    failures: list[dict[str, Any]] = []
    for index, command in enumerate(commands):
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            failures.append({"index": index, "command": command, "reason": "parse_error", "error": str(exc)})
            continue
        if not tokens:
            failures.append({"index": index, "command": command, "reason": "empty_command"})
            continue
        shell_tokens = _shell_control_tokens(command)
        if shell_tokens:
            failures.append(
                {
                    "index": index,
                    "command": command,
                    "reason": "shell_control_tokens",
                    "tokens": shell_tokens,
                }
            )
            continue
        expansion_tokens = _shell_expansion_tokens(command)
        if expansion_tokens:
            failures.append(
                {
                    "index": index,
                    "command": command,
                    "reason": "shell_expansion_tokens",
                    "tokens": expansion_tokens,
                }
            )
            continue

        python_module_pytest = len(tokens) >= 3 and tokens[0] in {"python", "python3"} and tokens[1:3] == ["-m", "pytest"]
        if len(tokens) >= 3 and Path(tokens[0]).name in {"python", "python3"} and tokens[1:3] == ["-m", "pytest"] and not python_module_pytest:
            failures.append(
                {
                    "index": index,
                    "command": command,
                    "reason": "nonportable_python_executable",
                    "executable": tokens[0],
                }
            )
            continue
        if python_module_pytest or tokens[0] == "pytest":
            args = tokens[3:] if python_module_pytest else tokens[1:]
            option_path_issues: list[dict[str, str]] = []
            option_value_positions: set[int] = set()
            for position, arg in enumerate(args):
                if arg.startswith("-") and "=" in arg:
                    option, value = arg.split("=", 1)
                    if option in PYTEST_PATH_VALUE_OPTIONS:
                        issue = _repo_path_safety_issue(repo_root, value)
                        if issue is not None:
                            option_path_issues.append({"option": option, **issue})
                    continue
                if arg in PYTEST_VALUE_OPTIONS and position + 1 < len(args):
                    value = args[position + 1]
                    if value.startswith("-"):
                        if arg in PYTEST_PATH_VALUE_OPTIONS:
                            option_path_issues.append({"option": arg, **_empty_path_issue(repo_root)})
                        continue
                    option_value_positions.add(position + 1)
                    if arg in PYTEST_PATH_VALUE_OPTIONS:
                        issue = _repo_path_safety_issue(repo_root, value)
                        if issue is not None:
                            option_path_issues.append({"option": arg, **issue})
                elif arg in PYTEST_PATH_VALUE_OPTIONS:
                    option_path_issues.append({"option": arg, **_empty_path_issue(repo_root)})
            if option_path_issues:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "unsafe_pytest_option_paths",
                        "option_paths": option_path_issues,
                    }
                )
                continue
            path_args = [
                arg
                for position, arg in enumerate(args)
                if position not in option_value_positions
                and not arg.startswith("-")
                and _looks_like_repo_path(arg)
            ]
            if not path_args:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "missing_pytest_targets",
                        "missing_targets": [],
                    }
                )
                continue
            target_issues = [
                issue
                for arg in path_args
                if (issue := _repo_target_issue(repo_root, arg)) is not None
            ]
            outside_targets = [issue for issue in target_issues if issue["reason"] == "outside_repo"]
            absolute_targets = [issue for issue in target_issues if issue["reason"] == "absolute_path"]
            home_targets = [issue for issue in target_issues if issue["reason"] == "home_directory_path"]
            parent_targets = [issue for issue in target_issues if issue["reason"] == "parent_directory_path"]
            missing_targets = [issue for issue in target_issues if issue["reason"] == "missing"]
            if absolute_targets:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "absolute_pytest_targets",
                        "absolute_targets": absolute_targets,
                    }
                )
            elif home_targets:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "home_directory_pytest_targets",
                        "home_directory_targets": home_targets,
                    }
                )
            elif parent_targets:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "parent_directory_pytest_targets",
                        "parent_directory_targets": parent_targets,
                    }
                )
            elif outside_targets:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "outside_repo_pytest_targets",
                        "outside_targets": outside_targets,
                    }
                )
            elif missing_targets:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "missing_pytest_targets",
                        "missing_targets": missing_targets,
                    }
                )
            continue

        if tokens[:3] == ["qcchem", "benchmark", "run"]:
            config_values: list[str] = []
            output_values: list[str] = []
            unsupported_output_options: list[str] = []
            for position, token in enumerate(tokens):
                if token in {"-c", "--config"} and position + 1 < len(tokens):
                    config_values.append(tokens[position + 1])
                elif token.startswith("--config="):
                    config_values.append(token.split("=", 1)[1])
                elif token in {"-o", "--output-dir"} and position + 1 < len(tokens):
                    output_values.append(tokens[position + 1])
                elif token.startswith("--output-dir="):
                    output_values.append(token.split("=", 1)[1])
                elif token == "--output" or token.startswith("--output="):
                    unsupported_output_options.append(token)
            if unsupported_output_options:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "unsupported_benchmark_output_options",
                        "options": unsupported_output_options,
                        "supported": ["-o", "--output-dir"],
                    }
                )
                continue
            if not config_values:
                failures.append({"index": index, "command": command, "reason": "missing_benchmark_config_option"})
                continue
            if len(config_values) > 1:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "multiple_benchmark_config_options",
                        "config_values": config_values,
                    }
                )
                continue
            config_issues = [
                issue
                for value in config_values
                if (issue := _repo_target_issue(repo_root, value, require_file=True)) is not None
            ]
            outside_configs = [issue for issue in config_issues if issue["reason"] == "outside_repo"]
            absolute_configs = [issue for issue in config_issues if issue["reason"] == "absolute_path"]
            home_configs = [issue for issue in config_issues if issue["reason"] == "home_directory_path"]
            parent_configs = [issue for issue in config_issues if issue["reason"] == "parent_directory_path"]
            empty_configs = [issue for issue in config_issues if issue["reason"] == "empty_path"]
            missing_configs = [issue for issue in config_issues if issue["reason"] == "missing"]
            not_file_configs = [issue for issue in config_issues if issue["reason"] == "not_file"]
            if absolute_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "absolute_benchmark_configs",
                        "absolute_configs": absolute_configs,
                    }
                )
            elif home_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "home_directory_benchmark_configs",
                        "home_directory_configs": home_configs,
                    }
                )
            elif parent_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "parent_directory_benchmark_configs",
                        "parent_directory_configs": parent_configs,
                    }
                )
            elif empty_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "empty_benchmark_configs",
                        "empty_configs": empty_configs,
                    }
                )
            elif not_file_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "non_file_benchmark_configs",
                        "non_file_configs": not_file_configs,
                    }
                )
            elif outside_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "outside_repo_benchmark_configs",
                        "outside_configs": outside_configs,
                    }
                )
            elif missing_configs:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "missing_benchmark_configs",
                        "missing_configs": missing_configs,
                    }
                )
            elif not output_values:
                failures.append({"index": index, "command": command, "reason": "missing_benchmark_output_option"})
            elif len(output_values) > 1:
                failures.append(
                    {
                        "index": index,
                        "command": command,
                        "reason": "multiple_benchmark_output_options",
                        "output_values": output_values,
                    }
                )
            else:
                output_issues = [
                    issue
                    for value in output_values
                    if (issue := _repo_artifact_output_issue(repo_root, value)) is not None
                ]
                outside_outputs = [issue for issue in output_issues if issue["reason"] == "outside_repo"]
                absolute_outputs = [issue for issue in output_issues if issue["reason"] == "absolute_path"]
                home_outputs = [issue for issue in output_issues if issue["reason"] == "home_directory_path"]
                parent_outputs = [issue for issue in output_issues if issue["reason"] == "parent_directory_path"]
                empty_outputs = [issue for issue in output_issues if issue["reason"] == "empty_path"]
                non_artifacts_outputs = [issue for issue in output_issues if issue["reason"] == "outside_artifacts"]
                protected_outputs = [
                    issue
                    for value in output_values
                    if (issue := _protected_artifact_output_issue(repo_root, value, protected_artifact_roots)) is not None
                ]
                if absolute_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "absolute_benchmark_outputs",
                            "absolute_outputs": absolute_outputs,
                        }
                    )
                elif home_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "home_directory_benchmark_outputs",
                            "home_directory_outputs": home_outputs,
                        }
                    )
                elif parent_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "parent_directory_benchmark_outputs",
                            "parent_directory_outputs": parent_outputs,
                        }
                    )
                elif outside_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "outside_repo_benchmark_outputs",
                            "outside_outputs": outside_outputs,
                        }
                    )
                elif empty_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "empty_benchmark_outputs",
                            "empty_outputs": empty_outputs,
                        }
                    )
                elif non_artifacts_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "non_artifacts_benchmark_outputs",
                            "non_artifacts_outputs": non_artifacts_outputs,
                        }
                    )
                elif protected_outputs:
                    failures.append(
                        {
                            "index": index,
                            "command": command,
                            "reason": "protected_release_artifact_outputs",
                            "protected_outputs": protected_outputs,
                        }
                    )
            continue

        failures.append({"index": index, "command": command, "reason": "unsupported_command"})
    return failures


def _acceptance_failure_remediation(failure: dict[str, Any]) -> str:
    reason = str(failure.get("reason") or "")
    remediations = {
        "parse_error": "Fix the shell-style quoting so the command can be parsed as one static recipe.",
        "empty_command": "Replace the empty recipe with a supported pytest or benchmark acceptance command.",
        "shell_control_tokens": "Split shell control operators into separate documented steps; acceptance_commands must contain one static command.",
        "shell_expansion_tokens": "Replace shell expansion, variables, globs, or command substitution with concrete repository-relative paths.",
        "nonportable_python_executable": "Use python or python3 literally instead of a machine-local interpreter path.",
        "missing_pytest_targets": "Add at least one concrete pytest target such as tests/unit/... or tests.",
        "absolute_pytest_targets": "Use repository-relative pytest targets instead of absolute paths.",
        "home_directory_pytest_targets": "Use repository-relative pytest targets instead of home-directory paths.",
        "parent_directory_pytest_targets": "Remove .. components from pytest targets and keep them inside the repository.",
        "outside_repo_pytest_targets": "Move the pytest target into the audited repository or remove it from release acceptance.",
        "unsafe_pytest_option_paths": "Use non-empty repository-relative values for pytest path options, without absolute, home, or .. paths.",
        "unsupported_benchmark_output_options": "Use -o or --output-dir for qcchem benchmark run output directories.",
        "missing_benchmark_config_option": "Add exactly one -c or --config benchmark suite path.",
        "multiple_benchmark_config_options": "Keep exactly one benchmark config option in the acceptance recipe.",
        "absolute_benchmark_configs": "Use a repository-relative benchmark config path.",
        "home_directory_benchmark_configs": "Use a repository-relative benchmark config path instead of a home-directory path.",
        "parent_directory_benchmark_configs": "Remove .. components from the benchmark config path.",
        "empty_benchmark_configs": "Provide a non-empty benchmark config path.",
        "non_file_benchmark_configs": "Point -c or --config at a benchmark config file, not a directory.",
        "outside_repo_benchmark_configs": "Move the benchmark config into the audited repository or remove it from release acceptance.",
        "missing_benchmark_configs": "Add the referenced benchmark config file or update the recipe to an existing one.",
        "missing_benchmark_output_option": "Add exactly one -o or --output-dir under artifacts/.",
        "multiple_benchmark_output_options": "Keep exactly one benchmark output option in the acceptance recipe.",
        "absolute_benchmark_outputs": "Use a repository-relative benchmark output path under artifacts/.",
        "home_directory_benchmark_outputs": "Use a repository-relative benchmark output path under artifacts/ instead of a home-directory path.",
        "parent_directory_benchmark_outputs": "Remove .. components from the benchmark output path.",
        "outside_repo_benchmark_outputs": "Keep benchmark outputs inside the audited repository under artifacts/.",
        "empty_benchmark_outputs": "Provide a non-empty benchmark output path under artifacts/.",
        "non_artifacts_benchmark_outputs": "Write benchmark outputs to a dedicated child directory under artifacts/.",
        "protected_release_artifact_outputs": "Write regeneration recipes to the protected artifact's preview_local child, not the curated artifact root.",
        "unsupported_command": "Use a supported release recipe: python -m pytest ... or qcchem benchmark run -c ... -o ...",
    }
    return remediations.get(reason, "Inspect this acceptance command and replace it with a supported static release recipe.")


def _annotate_acceptance_command_failures(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {**failure, "remediation": _acceptance_failure_remediation(failure)}
        for failure in failures
    ]


def _audit_acceptance_commands(spec: ReleaseAuditSpec, *, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    protected_artifact_roots = {artifact.path.parent for artifact in spec.curated_artifacts}
    protected_artifact_roots.update(
        asset.artifact.parent
        for asset in spec.exploratory_assets
        if asset.artifact is not None
    )
    failures = _acceptance_command_failures(
        spec.acceptance_commands,
        repo_root=repo_root,
        protected_artifact_roots=protected_artifact_roots,
    )
    failures = _annotate_acceptance_command_failures(failures)
    _check(
        checks,
        check_id="release_acceptance_commands:static_targets",
        label="Release acceptance commands reference local targets and artifact outputs",
        passed=not failures,
        required=True,
        summary=(
            "Acceptance command targets and outputs are statically resolvable."
            if not failures
            else "Acceptance commands reference missing, unsafe, or unsupported local targets or outputs."
        ),
        details={"command_count": len(spec.acceptance_commands), "failures": failures},
    )


def _ci_step_command_lines(command: str) -> list[str]:
    return [line.strip() for line in command.splitlines() if line.strip()]


def _ci_workflow_jobs(
    workflow_path: Path,
    workflow_relative_path: Path,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    try:
        raw = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [
            {
                "reason": "unreadable_ci_workflow",
                "workflow": workflow_relative_path.as_posix(),
                "error": f"{type(exc).__name__}: {exc}",
            }
        ]
    jobs = raw.get("jobs") if isinstance(raw, dict) else None
    if not isinstance(jobs, dict):
        failures.append({"reason": "missing_ci_jobs", "workflow": workflow_relative_path.as_posix()})
        return None, failures
    return jobs, failures


def _audit_ci_acceptance_alignment(spec: ReleaseAuditSpec, *, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    workflow_relative_path = CI_WORKFLOW_RELATIVE_PATH
    workflow_path = repo_root / workflow_relative_path
    if not workflow_path.exists():
        _skipped(
            checks,
            check_id="release_acceptance_commands:ci_alignment",
            label="CI test command is advertised as release acceptance evidence",
            summary="No GitHub Actions CI workflow was found; CI command alignment was not checked.",
            details={"workflow": workflow_relative_path.as_posix(), "step_name": "Run tests"},
        )
        return

    failures: list[dict[str, Any]] = []
    ci_commands: list[str] = []
    jobs, workflow_failures = _ci_workflow_jobs(workflow_path, workflow_relative_path)
    failures.extend(workflow_failures)

    if isinstance(jobs, dict):
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps")
            if not isinstance(steps, list):
                continue
            for step_index, step in enumerate(steps):
                if not isinstance(step, dict) or step.get("name") != "Run tests":
                    continue
                command = step.get("run")
                if not isinstance(command, str) or not command.strip():
                    failures.append(
                        {
                            "reason": "empty_ci_run_tests_command",
                            "job": str(job_name),
                            "step_index": step_index,
                        }
                    )
                    continue
                stripped = command.strip()
                if "\n" in stripped:
                    failures.append(
                        {
                            "reason": "multi_line_ci_run_tests_command",
                            "job": str(job_name),
                            "step_index": step_index,
                            "command": stripped,
                        }
                    )
                    continue
                if stripped not in ci_commands:
                    ci_commands.append(stripped)

    if jobs is not None and not ci_commands:
        failures.append({"reason": "missing_ci_run_tests_step", "workflow": workflow_relative_path.as_posix()})

    static_failures = _annotate_acceptance_command_failures(
        _acceptance_command_failures(ci_commands, repo_root=repo_root)
    )
    failures.extend({**failure, "reason": f"ci_{failure['reason']}"} for failure in static_failures)

    missing_from_manifest = [command for command in ci_commands if command not in spec.acceptance_commands]
    if missing_from_manifest:
        failures.append(
            {
                "reason": "ci_command_missing_from_acceptance_commands",
                "commands": missing_from_manifest,
            }
        )

    _check(
        checks,
        check_id="release_acceptance_commands:ci_alignment",
        label="CI test command is advertised as release acceptance evidence",
        passed=not failures,
        required=True,
        summary=(
            "CI Run tests commands are static and present in release acceptance_commands."
            if not failures
            else "CI Run tests commands are missing, unsafe, or not advertised by release acceptance_commands."
        ),
        details={
            "workflow": workflow_relative_path.as_posix(),
            "step_name": "Run tests",
            "ci_commands": ci_commands,
            "failures": failures,
        },
    )


def _audit_ci_acceptance_status_gate(*, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    workflow_relative_path = CI_WORKFLOW_RELATIVE_PATH
    workflow_path = repo_root / workflow_relative_path
    if not workflow_path.exists():
        _skipped(
            checks,
            check_id="release_acceptance_sidecars:ci_freshness_gate",
            label="CI checks release acceptance sidecar freshness",
            summary="No GitHub Actions CI workflow was found; sidecar freshness gate was not checked.",
            details={"workflow": workflow_relative_path.as_posix(), "step_name": CI_ACCEPTANCE_STATUS_STEP_NAME},
        )
        return

    failures: list[dict[str, Any]] = []
    matching_steps: list[dict[str, Any]] = []
    jobs, workflow_failures = _ci_workflow_jobs(workflow_path, workflow_relative_path)
    failures.extend(workflow_failures)
    if isinstance(jobs, dict):
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps")
            if not isinstance(steps, list):
                continue
            for step_index, step in enumerate(steps):
                if not isinstance(step, dict) or step.get("name") != CI_ACCEPTANCE_STATUS_STEP_NAME:
                    continue
                command = step.get("run")
                entry = {
                    "job": str(job_name),
                    "step_index": step_index,
                    "command_lines": _ci_step_command_lines(command) if isinstance(command, str) else [],
                }
                matching_steps.append(entry)
                if not isinstance(command, str) or not command.strip():
                    failures.append(
                        {
                            "reason": "empty_ci_acceptance_status_command",
                            "job": str(job_name),
                            "step_index": step_index,
                        }
                    )
                    continue
                command_lines = _ci_step_command_lines(command)
                if tuple(command_lines) != CI_ACCEPTANCE_STATUS_COMMAND_LINES:
                    failures.append(
                        {
                            "reason": "ci_acceptance_status_command_mismatch",
                            "job": str(job_name),
                            "step_index": step_index,
                            "expected_command_lines": list(CI_ACCEPTANCE_STATUS_COMMAND_LINES),
                            "actual_command_lines": command_lines,
                        }
                    )

    if jobs is not None and not matching_steps:
        failures.append(
            {
                "reason": "missing_ci_acceptance_status_step",
                "workflow": workflow_relative_path.as_posix(),
                "step_name": CI_ACCEPTANCE_STATUS_STEP_NAME,
            }
        )

    _check(
        checks,
        check_id="release_acceptance_sidecars:ci_freshness_gate",
        label="CI checks release acceptance sidecar freshness",
        passed=not failures,
        required=True,
        summary=(
            "CI runs release acceptance-status --strict --repair-plan with the Trust-First manifest."
            if not failures
            else "CI is missing or misconfigures the release acceptance sidecar freshness gate."
        ),
        details={
            "workflow": workflow_relative_path.as_posix(),
            "step_name": CI_ACCEPTANCE_STATUS_STEP_NAME,
            "expected_command_lines": list(CI_ACCEPTANCE_STATUS_COMMAND_LINES),
            "matching_steps": matching_steps,
            "failures": failures,
        },
    )


def _ci_artifact_upload_paths(value: Any) -> list[str]:
    if isinstance(value, str):
        return _ci_step_command_lines(value)
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _audit_ci_release_diagnostic_artifacts(*, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    workflow_relative_path = CI_WORKFLOW_RELATIVE_PATH
    workflow_path = repo_root / workflow_relative_path
    if not workflow_path.exists():
        _skipped(
            checks,
            check_id="release_diagnostics:ci_artifact_upload",
            label="CI uploads release diagnostic artifacts",
            summary="No GitHub Actions CI workflow was found; release diagnostic artifact upload was not checked.",
            details={"workflow": workflow_relative_path.as_posix(), "step_name": CI_RELEASE_DIAGNOSTIC_UPLOAD_STEP_NAME},
        )
        return

    failures: list[dict[str, Any]] = []
    matching_steps: list[dict[str, Any]] = []
    jobs, workflow_failures = _ci_workflow_jobs(workflow_path, workflow_relative_path)
    failures.extend(workflow_failures)
    if isinstance(jobs, dict):
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps")
            if not isinstance(steps, list):
                continue
            job_env = job.get("env") if isinstance(job.get("env"), dict) else {}
            env_artifact_name = job_env.get(CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_ENV)
            producer_indices = {
                step.get("name"): step_index
                for step_index, step in enumerate(steps)
                if isinstance(step, dict) and step.get("name") in CI_RELEASE_DIAGNOSTIC_PRODUCER_STEPS
            }
            for step_index, step in enumerate(steps):
                if not isinstance(step, dict) or step.get("name") != CI_RELEASE_DIAGNOSTIC_UPLOAD_STEP_NAME:
                    continue
                with_options = step.get("with")
                with_options = with_options if isinstance(with_options, dict) else {}
                paths = _ci_artifact_upload_paths(with_options.get("path"))
                artifact_name = with_options.get("name")
                if_no_files_found = with_options.get("if-no-files-found")
                entry = {
                    "job": str(job_name),
                    "step_index": step_index,
                    "uses": step.get("uses"),
                    "if_condition": step.get("if"),
                    "artifact_name": artifact_name,
                    "env_artifact_name": env_artifact_name,
                    "paths": paths,
                    "if_no_files_found": if_no_files_found,
                }
                matching_steps.append(entry)
                if step.get("uses") != CI_RELEASE_DIAGNOSTIC_UPLOAD_ACTION:
                    failures.append(
                        {
                            "reason": "ci_release_diagnostic_upload_action_mismatch",
                            "job": str(job_name),
                            "step_index": step_index,
                            "expected_action": CI_RELEASE_DIAGNOSTIC_UPLOAD_ACTION,
                            "actual_action": step.get("uses"),
                        }
                    )
                if step.get("if") != "always()":
                    failures.append(
                        {
                            "reason": "ci_release_diagnostic_upload_not_always",
                            "job": str(job_name),
                            "step_index": step_index,
                            "actual_if": step.get("if"),
                        }
                    )
                if not isinstance(artifact_name, str) or not artifact_name.startswith(
                    CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_PREFIX
                ):
                    failures.append(
                        {
                            "reason": "ci_release_diagnostic_upload_name_mismatch",
                            "job": str(job_name),
                            "step_index": step_index,
                            "expected_prefix": CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_PREFIX,
                            "actual_name": artifact_name,
                        }
                    )
                if env_artifact_name != artifact_name:
                    failures.append(
                        {
                            "reason": "ci_release_diagnostic_artifact_env_mismatch",
                            "job": str(job_name),
                            "step_index": step_index,
                            "env_name": CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_ENV,
                            "env_value": env_artifact_name,
                            "artifact_name": artifact_name,
                        }
                    )
                if if_no_files_found != "ignore":
                    failures.append(
                        {
                            "reason": "ci_release_diagnostic_upload_if_no_files_found_mismatch",
                            "job": str(job_name),
                            "step_index": step_index,
                            "expected": "ignore",
                            "actual": if_no_files_found,
                        }
                    )
                missing_paths = [path for path in CI_RELEASE_DIAGNOSTIC_REQUIRED_PATHS if path not in paths]
                if missing_paths:
                    failures.append(
                        {
                            "reason": "ci_release_diagnostic_upload_missing_paths",
                            "job": str(job_name),
                            "step_index": step_index,
                            "missing_paths": missing_paths,
                        }
                    )
                for producer_name, producer_index in producer_indices.items():
                    if step_index <= producer_index:
                        failures.append(
                            {
                                "reason": "ci_release_diagnostic_upload_before_producer",
                                "job": str(job_name),
                                "step_index": step_index,
                                "producer_step_name": producer_name,
                                "producer_step_index": producer_index,
                            }
                        )

    if jobs is not None and not matching_steps:
        failures.append(
            {
                "reason": "missing_ci_release_diagnostic_upload_step",
                "workflow": workflow_relative_path.as_posix(),
                "step_name": CI_RELEASE_DIAGNOSTIC_UPLOAD_STEP_NAME,
            }
        )

    _check(
        checks,
        check_id="release_diagnostics:ci_artifact_upload",
        label="CI uploads release diagnostic artifacts",
        passed=not failures,
        required=True,
        summary=(
            "CI preserves release audit, sidecar freshness, and Workbench smoke diagnostics as artifacts."
            if not failures
            else "CI is missing or misconfigures release diagnostic artifact upload."
        ),
        details={
            "workflow": workflow_relative_path.as_posix(),
            "step_name": CI_RELEASE_DIAGNOSTIC_UPLOAD_STEP_NAME,
            "expected_action": CI_RELEASE_DIAGNOSTIC_UPLOAD_ACTION,
            "required_paths": list(CI_RELEASE_DIAGNOSTIC_REQUIRED_PATHS),
            "matching_steps": matching_steps,
            "failures": failures,
        },
    )


def _markdown_code_span(value: Any) -> str:
    text = str(value)
    max_backtick_run = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * (max_backtick_run + 1)
    if "`" in text:
        return f"{fence} {text} {fence}"
    return f"{fence}{text}{fence}"


def _acceptance_command_repair_failures(summary: dict[str, Any]) -> list[dict[str, Any]]:
    for check in summary.get("checks", []):
        if not isinstance(check, dict) or check.get("id") != "release_acceptance_commands:static_targets":
            continue
        details = check.get("details")
        if not isinstance(details, dict):
            return []
        failures = details.get("failures")
        if not isinstance(failures, list):
            return []
        return [failure for failure in failures if isinstance(failure, dict)]
    return []


def _acceptance_contract_repair_failures(summary: dict[str, Any]) -> list[dict[str, Any]]:
    repairs: list[dict[str, Any]] = []
    for check in summary.get("checks", []):
        if not isinstance(check, dict):
            continue
        details = check.get("details")
        if not isinstance(details, dict):
            continue
        failures = details.get("contract_failures")
        if not isinstance(failures, list):
            continue
        for failure in failures:
            if not isinstance(failure, dict):
                continue
            repair = {
                "check_id": check.get("id"),
                "field": failure.get("field"),
                "expected": failure.get("expected"),
                "actual": failure.get("actual"),
                "source": details.get("source"),
            }
            if "reason" in failure:
                repair["reason"] = failure.get("reason")
            repairs.append(repair)
    return repairs


def _release_acceptance_repair_plan_items(summary: dict[str, Any]) -> list[dict[str, Any]]:
    sidecars = summary.get("release_acceptance_sidecars")
    if not isinstance(sidecars, dict):
        return []
    repair_plan = sidecars.get("repair_plan")
    if not isinstance(repair_plan, list):
        return []
    return [item for item in repair_plan if isinstance(item, dict)]


def _markdown_contract_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return _markdown_code_span(json.dumps(value, sort_keys=True))
    return _markdown_code_span(value)


def _acceptance_items(payload: dict[str, Any], field: str) -> list[Any]:
    value = payload.get(field)
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [{"reason": f"{field}_not_list", "value": value}]


def _evidence_missing_fields(payload: dict[str, Any]) -> list[str]:
    evidence = payload.get("evidence_summary")
    if not isinstance(evidence, dict):
        return ["evidence_summary"]
    missing: list[str] = []
    for key in RELEASE_EVIDENCE_SUMMARY_REQUIRED_FIELDS:
        value = evidence.get(key)
        if value is None or value == "" or value == {}:
            missing.append(key)
    return missing


def _evidence_review_warnings(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    baseline = evidence.get("primary_baseline") if isinstance(evidence.get("primary_baseline"), dict) else {}
    baseline_kind = baseline.get("baseline_kind")
    baseline_strength = baseline.get("baseline_strength")
    if baseline_kind in {None, "", "none", "unavailable"} or baseline_strength in {None, "", "weak"}:
        warnings.append(
            {
                "reason": "weak_or_missing_baseline",
                "baseline_kind": baseline_kind,
                "baseline_strength": baseline_strength,
            }
        )

    error_metric = evidence.get("primary_error_metric") if isinstance(evidence.get("primary_error_metric"), dict) else {}
    if error_metric.get("value") is None:
        warnings.append(
            {
                "reason": "missing_error_metric_value",
                "metric_kind": error_metric.get("metric_kind"),
            }
        )

    claim = evidence.get("primary_scientific_claim")
    if isinstance(claim, str) and "None" in claim:
        warnings.append({"reason": "claim_contains_null_placeholder"})
    return warnings


def _runtime_boundary_failure(payload: dict[str, Any]) -> str | None:
    if not payload.get("hardware_verified"):
        return None
    runtime_submission = payload.get("runtime_submission") or {}
    if not isinstance(runtime_submission, dict):
        return "hardware_verified_without_runtime_submission"
    if runtime_submission.get("submitted") and runtime_submission.get("succeeded"):
        return None
    return "hardware_verified_without_retrieved_runtime_result"


def _runtime_evidence_status(payload: dict[str, Any]) -> str | None:
    evidence = payload.get("evidence_summary") or {}
    if isinstance(evidence, dict) and evidence.get("runtime_evidence_status"):
        return str(evidence.get("runtime_evidence_status"))

    runtime_submission = payload.get("runtime_submission")
    if not isinstance(runtime_submission, dict):
        return None
    if runtime_submission.get("submitted") and runtime_submission.get("succeeded"):
        return "retrieved_result"
    if runtime_submission.get("submitted"):
        return "submitted"
    if runtime_submission.get("attempted"):
        return "runtime_attempt"
    return "none"


def _hardware_verified_cases(payload: dict[str, Any]) -> list[Any]:
    evidence = payload.get("evidence_summary") or {}
    execution_evidence = evidence.get("execution_evidence") if isinstance(evidence, dict) else {}
    cases = execution_evidence.get("hardware_verified_cases") if isinstance(execution_evidence, dict) else None
    if cases is None:
        summary = payload.get("summary")
        cases = summary.get("hardware_verified_cases") if isinstance(summary, dict) else None
    return cases if isinstance(cases, list) else []


def _is_hardware_campaign_payload(payload: dict[str, Any]) -> bool:
    evidence = payload.get("evidence_summary") or {}
    identity = evidence.get("result_identity") if isinstance(evidence, dict) else {}
    if isinstance(identity, dict) and identity.get("artifact_kind") == "hardware_campaign":
        return True
    summary = payload.get("summary")
    return (
        bool(payload.get("suite_name"))
        and isinstance(payload.get("cases"), list)
        and isinstance(summary, dict)
        and "runtime_evidence_status_counts" in summary
    )


def _runtime_evidence_boundary_failure(payload: dict[str, Any]) -> str | None:
    evidence = payload.get("evidence_summary") or {}
    if not isinstance(evidence, dict) or evidence.get("trust_tier") != "hardware_verified":
        return None

    runtime_status = _runtime_evidence_status(payload)
    if runtime_status != "retrieved_result":
        return "hardware_verified_trust_without_retrieved_runtime_evidence"

    if _is_hardware_campaign_payload(payload):
        if not _hardware_verified_cases(payload):
            return "hardware_campaign_without_hardware_verified_cases"
        return None

    if payload.get("hardware_verified") is not True:
        return "hardware_verified_trust_without_top_level_runtime_marker"
    if _runtime_boundary_failure(payload) is not None:
        return "hardware_verified_trust_without_top_level_runtime_submission"
    return None


def _artifact_path_for_report(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _path_for_audit_provenance(path: Path | None, *, repo_root: Path) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def _repo_relative_path_issue(value: str) -> str | None:
    path = Path(value)
    if path.is_absolute():
        return "absolute_path"
    if value.startswith("~"):
        return "home_directory_path"
    if ".." in path.parts:
        return "parent_directory_path"
    return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _acceptance_contract_failures(
    acceptance: dict[str, Any],
    *,
    expected_check_id: str,
    artifact_path: Path,
    artifact_payload: dict[str, Any],
    repo_root: Path,
    release_binding_required: bool,
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    schema_version = acceptance.get("schema_version")
    if schema_version not in SUPPORTED_ACCEPTANCE_SCHEMA_VERSIONS:
        failures.append(
            {
                "field": "schema_version",
                "expected": sorted(SUPPORTED_ACCEPTANCE_SCHEMA_VERSIONS),
                "actual": schema_version,
            }
        )
        return failures

    if schema_version != RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION:
        if release_binding_required:
            failures.append(
                {
                    "field": "schema_version",
                    "expected": RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION,
                    "actual": schema_version,
                    "reason": "legacy_schema_missing_release_binding",
                }
            )
        return failures

    for field in ("blocking_failures", "warnings"):
        value = acceptance.get(field)
        if not isinstance(value, list):
            failures.append(
                {
                    "field": field,
                    "expected": "list",
                    "actual": value,
                    "reason": "missing_or_not_list",
                }
            )

    recommended_action = acceptance.get("recommended_action")
    if not isinstance(recommended_action, str) or not recommended_action.strip():
        failures.append(
            {
                "field": "recommended_action",
                "expected": "non_empty_string",
                "actual": recommended_action,
            }
        )

    actual_check_id = acceptance.get("release_audit_check_id")
    if actual_check_id != expected_check_id:
        failures.append(
            {
                "field": "release_audit_check_id",
                "expected": expected_check_id,
                "actual": actual_check_id,
            }
        )

    actual_artifact_path = acceptance.get("artifact_path")
    expected_artifact_path = _artifact_path_for_report(artifact_path, repo_root=repo_root)
    if not isinstance(actual_artifact_path, str) or not actual_artifact_path.strip():
        failures.append(
            {
                "field": "artifact_path",
                "expected": expected_artifact_path,
                "actual": actual_artifact_path,
            }
        )
    else:
        path_issue = _repo_relative_path_issue(actual_artifact_path)
        if path_issue is not None:
            failures.append(
                {
                    "field": "artifact_path",
                    "expected": expected_artifact_path,
                    "actual": actual_artifact_path,
                    "reason": path_issue,
                }
            )
        raw_path = Path(actual_artifact_path).expanduser()
        resolved_path = raw_path.resolve() if raw_path.is_absolute() else (repo_root / raw_path).resolve()
        if resolved_path != artifact_path.resolve():
            failures.append(
                {
                    "field": "artifact_path",
                    "expected": expected_artifact_path,
                    "actual": actual_artifact_path,
                }
            )

    expected_artifact_sha256 = _file_sha256(artifact_path)
    actual_artifact_sha256 = acceptance.get("artifact_sha256")
    if not isinstance(actual_artifact_sha256, str) or not actual_artifact_sha256.strip():
        failures.append(
            {
                "field": "artifact_sha256",
                "expected": expected_artifact_sha256,
                "actual": actual_artifact_sha256,
            }
        )
    elif actual_artifact_sha256 != expected_artifact_sha256:
        failures.append(
            {
                "field": "artifact_sha256",
                "expected": expected_artifact_sha256,
                "actual": actual_artifact_sha256,
            }
        )

    evidence = artifact_payload.get("evidence_summary") or {}
    expected_trust_tier = evidence.get("trust_tier") if isinstance(evidence, dict) else None
    actual_trust_tier = acceptance.get("trust_tier")
    if actual_trust_tier != expected_trust_tier:
        failures.append(
            {
                "field": "trust_tier",
                "expected": expected_trust_tier,
                "actual": actual_trust_tier,
            }
        )

    expected_runtime_status = _runtime_evidence_status(artifact_payload)
    actual_runtime_status = acceptance.get("runtime_evidence_status")
    if expected_runtime_status is not None and actual_runtime_status != expected_runtime_status:
        failures.append(
            {
                "field": "runtime_evidence_status",
                "expected": expected_runtime_status,
                "actual": actual_runtime_status,
            }
        )
    elif expected_runtime_status is None and actual_runtime_status not in {None, ""}:
        failures.append(
            {
                "field": "runtime_evidence_status",
                "expected": expected_runtime_status,
                "actual": actual_runtime_status,
            }
        )
    return failures


def _artifact_matrix_entry(
    name: str,
    kind: str,
    path: Path,
    payload: dict[str, Any],
    *,
    acceptance: dict[str, Any] | None = None,
    acceptance_source: str | None = None,
    acceptance_contract_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evidence = payload.get("evidence_summary") or {}
    raw_acceptance_payload = acceptance if acceptance is not None else payload.get("acceptance_summary")
    acceptance_payload = raw_acceptance_payload if isinstance(raw_acceptance_payload, dict) else {}
    acceptance_blocking_failures = _acceptance_items(acceptance_payload, "blocking_failures")
    acceptance_warnings = _acceptance_items(acceptance_payload, "warnings")
    contract_failures = acceptance_contract_failures or []
    runtime_status = _runtime_evidence_status(payload)
    hardware_cases = _hardware_verified_cases(payload)
    review_warnings = _evidence_review_warnings(evidence) if isinstance(evidence, dict) else []
    return {
        "name": name,
        "kind": kind,
        "path": str(path),
        "verification_status": payload.get("verification_status"),
        "primary_scientific_claim": evidence.get("primary_scientific_claim"),
        "primary_baseline": evidence.get("primary_baseline"),
        "primary_error_metric": evidence.get("primary_error_metric"),
        "chemical_accuracy_status": evidence.get("chemical_accuracy_status"),
        "trust_tier": evidence.get("trust_tier"),
        "recommended_action": evidence.get("recommended_action"),
        "hardware_verified": payload.get("hardware_verified", False),
        "runtime_evidence_status": runtime_status,
        "review_warning_count": len(review_warnings),
        "review_warnings": review_warnings,
        "hardware_verified_case_count": len(hardware_cases),
        "runtime_submission_status": (payload.get("runtime_submission") or {}).get("status")
        or (payload.get("runtime_submission") or {}).get("failure_category"),
        "acceptance_summary_source": acceptance_source,
        "acceptance_schema_version": acceptance_payload.get("schema_version"),
        "acceptance_artifact_path": acceptance_payload.get("artifact_path"),
        "acceptance_artifact_sha256": acceptance_payload.get("artifact_sha256"),
        "acceptance_release_audit_check_id": acceptance_payload.get("release_audit_check_id"),
        "acceptance_trust_tier": acceptance_payload.get("trust_tier"),
        "acceptance_runtime_evidence_status": acceptance_payload.get("runtime_evidence_status"),
        "acceptance_status": acceptance_payload.get("accepted"),
        "acceptance_recommended_action": acceptance_payload.get("recommended_action"),
        "acceptance_blocking_failure_count": len(acceptance_blocking_failures),
        "acceptance_warning_count": len(acceptance_warnings),
        "acceptance_contract_failure_count": len(contract_failures),
    }


def _payload_with_release_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a read-only payload view with Evidence Summary for legacy artifacts."""
    if isinstance(payload.get("evidence_summary"), dict):
        return payload
    try:
        summarized = summarize_artifact_payload(payload)
    except Exception:
        return payload
    evidence = summarized.get("evidence_summary")
    if not isinstance(evidence, dict):
        return payload
    return {**payload, "evidence_summary": evidence}


def _has_lr_ace_section(payload: dict[str, Any]) -> bool:
    variational = payload.get("variational_result") or {}
    ansatz = variational.get("ansatz") or {}
    if isinstance(ansatz, dict) and "lr_ace" in ansatz:
        return True
    return "lr_ace" in json.dumps(payload.get("metadata", {})).lower()


def _has_required_exploratory_section(kind: str, payload: dict[str, Any]) -> bool:
    if kind == "qft":
        return isinstance(payload.get("qft_model"), dict)
    if kind == "tc_qsci":
        return isinstance(payload.get("tc_qsci_result"), dict)
    if kind == "lr_ace":
        return _has_lr_ace_section(payload)
    return False


def _risk_notes(payload: dict[str, Any]) -> list[Any]:
    notes = payload.get("scientific_risk_notes") or []
    evidence = payload.get("evidence_summary") or {}
    trust = evidence.get("trust_judgment") or {}
    if isinstance(trust, dict):
        notes = [*notes, *(trust.get("scientific_risk_notes") or [])]
    return notes


def _classify_exploratory_config(path: Path) -> tuple[str, str | None]:
    if not path.exists():
        return "missing", None
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return "unreadable", f"{type(exc).__name__}: {exc}"
    if not isinstance(raw, dict):
        return "unknown", None
    solver = raw.get("solver") or {}
    problem = raw.get("problem") or {}
    exploratory = raw.get("exploratory") or {}
    modules = exploratory.get("modules") or []
    qft = (problem.get("qft") or {}) if isinstance(problem, dict) else {}
    solver_kind = str(solver.get("kind", "")).strip() if isinstance(solver, dict) else ""
    if isinstance(qft, dict) and qft.get("enabled"):
        return "qft", None
    if solver_kind.startswith("lattice_qed") or solver_kind == "qft_dynamics_audit":
        return "qft", None
    if solver_kind == "lr_ace":
        return "lr_ace", None
    if "tc_qsci" in modules:
        return "tc_qsci", None
    tc_qsci = raw.get("tc_qsci") or {}
    if isinstance(tc_qsci, dict) and tc_qsci.get("enabled"):
        return "tc_qsci", None
    return "unknown", None


def classify_exploratory_config(path: Path) -> str:
    """Classify a configured exploratory asset without executing it."""
    classified, _error = _classify_exploratory_config(path)
    return classified


def _audit_artifact(
    *,
    name: str,
    path: Path,
    repo_root: Path,
    required: bool,
    kind: str,
    checks: list[dict[str, Any]],
    evidence_matrix: list[dict[str, Any]],
    id_prefix: str,
    acceptance_required: bool = False,
) -> dict[str, Any] | None:
    if not path.exists():
        _check(
            checks,
            check_id=f"{id_prefix}:{name}:exists",
            label=f"{name} artifact exists",
            passed=False,
            required=required,
            summary=f"Missing artifact: {path}",
            details={"path": str(path)},
        )
        return None

    _check(
        checks,
        check_id=f"{id_prefix}:{name}:exists",
        label=f"{name} artifact exists",
        passed=True,
        required=required,
        summary=str(path),
    )
    payload, payload_read_error = _read_optional_json_object(path)
    _check(
        checks,
        check_id=f"{id_prefix}:{name}:readable",
        label=f"{name} artifact is readable JSON",
        passed=payload_read_error is None,
        required=required,
        summary=(
            "Artifact payload is a readable JSON object."
            if payload_read_error is None
            else "Artifact payload must be a readable JSON object."
        ),
        details={"path": str(path), "error": payload_read_error},
    )
    if payload is None:
        return None

    evidence_payload = _payload_with_release_evidence(payload)

    missing = _evidence_missing_fields(evidence_payload)
    _check(
        checks,
        check_id=f"{id_prefix}:{name}:evidence_summary",
        label=f"{name} evidence summary is release-readable",
        passed=not missing,
        required=required,
        summary="Evidence summary contains release-facing fields." if not missing else "Evidence summary is incomplete.",
        details={"missing_fields": missing},
    )

    runtime_failure = _runtime_boundary_failure(evidence_payload)
    _check(
        checks,
        check_id=f"{id_prefix}:{name}:runtime_boundary",
        label=f"{name} hardware boundary is conservative",
        passed=runtime_failure is None,
        required=required,
        summary="hardware_verified is consistent with retrieved runtime evidence."
        if runtime_failure is None
        else "hardware_verified is inconsistent with runtime_submission.",
        details={"failure": runtime_failure},
    )
    runtime_evidence_failure = _runtime_evidence_boundary_failure(evidence_payload)
    _check(
        checks,
        check_id=f"{id_prefix}:{name}:runtime_evidence_boundary",
        label=f"{name} runtime evidence boundary is explicit",
        passed=runtime_evidence_failure is None,
        required=required,
        summary=(
            "Runtime evidence status is consistent with the declared trust tier."
            if runtime_evidence_failure is None
            else "hardware_verified trust tier is missing retrieved runtime evidence."
        ),
        details={
            "failure": runtime_evidence_failure,
            "runtime_evidence_status": _runtime_evidence_status(evidence_payload),
            "hardware_verified_case_count": len(_hardware_verified_cases(evidence_payload)),
        },
    )
    acceptance_check_id = f"{id_prefix}:{name}:acceptance_summary"
    sidecar_acceptance_path = path.parent / "acceptance_summary.json"
    acceptance_read_error: str | None = None
    embedded_acceptance = payload.get("acceptance_summary") or evidence_payload.get("acceptance_summary")
    if sidecar_acceptance_path.exists():
        acceptance, acceptance_read_error = _read_optional_json_object(sidecar_acceptance_path)
        acceptance_source = "sidecar" if isinstance(acceptance, dict) else None
    else:
        acceptance = embedded_acceptance
        acceptance_source = "embedded" if isinstance(acceptance, dict) else None
    if not isinstance(acceptance, dict):
        if acceptance_read_error is not None:
            if required or acceptance_required:
                _check(
                    checks,
                    check_id=acceptance_check_id,
                    label=f"{name} acceptance summary is readable",
                    passed=False,
                    required=True,
                    summary="Acceptance summary sidecar must be a readable JSON object.",
                    details={"path": str(sidecar_acceptance_path), "error": acceptance_read_error},
                )
            else:
                _warning(
                    checks,
                    check_id=acceptance_check_id,
                    label=f"{name} acceptance summary is unreadable",
                    summary="Acceptance summary sidecar is present but could not be read as a JSON object.",
                    details={"path": str(sidecar_acceptance_path), "error": acceptance_read_error},
                )
        elif required or acceptance_required:
            _check(
                checks,
                check_id=acceptance_check_id,
                label=f"{name} acceptance summary is present",
                passed=False,
                required=True,
                summary="Acceptance summary is required for this artifact but missing.",
                details={"path": str(sidecar_acceptance_path)},
            )
        else:
            _warning(
                checks,
                check_id=acceptance_check_id,
                label=f"{name} acceptance summary is missing",
                summary="Acceptance summary is not present; release audit treats this as a warning unless required.",
                details={"path": str(sidecar_acceptance_path)},
            )
    else:
        accepted = acceptance.get("accepted") is True
        blocking_failures = _acceptance_items(acceptance, "blocking_failures")
        acceptance_warnings = _acceptance_items(acceptance, "warnings")
        contract_failures = _acceptance_contract_failures(
            acceptance,
            expected_check_id=acceptance_check_id,
            artifact_path=path,
            artifact_payload=evidence_payload,
            repo_root=repo_root,
            release_binding_required=required or acceptance_required,
        )
        passed = accepted and not blocking_failures and not contract_failures
        _check(
            checks,
            check_id=acceptance_check_id,
            label=f"{name} acceptance summary is accepted",
            passed=passed,
            required=required or acceptance_required,
            summary=(
                "Acceptance summary is present, bound to this artifact, accepted, and has no blocking failures."
                if passed
                else "Acceptance summary is missing strict accepted=true, contains blocking failures, or is not bound to this artifact."
            ),
            details={
                "schema_version": acceptance.get("schema_version"),
                "artifact_path": acceptance.get("artifact_path"),
                "artifact_sha256": acceptance.get("artifact_sha256"),
                "release_audit_check_id": acceptance.get("release_audit_check_id"),
                "trust_tier": acceptance.get("trust_tier"),
                "runtime_evidence_status": acceptance.get("runtime_evidence_status"),
                "accepted": acceptance.get("accepted"),
                "source": acceptance_source,
                "blocking_failure_count": len(blocking_failures),
                "warning_count": len(acceptance_warnings),
                "contract_failure_count": len(contract_failures),
                "recommended_action": acceptance.get("recommended_action"),
                "blocking_failures": blocking_failures,
                "warnings": acceptance_warnings,
                "contract_failures": contract_failures,
            },
        )
        if acceptance_warnings:
            _warning(
                checks,
                check_id=f"{id_prefix}:{name}:acceptance_warnings",
                label=f"{name} acceptance summary has warnings",
                summary="Acceptance summary is accepted but still carries warnings for release review.",
                details={"warnings": acceptance_warnings},
            )
    evidence_matrix.append(
        _artifact_matrix_entry(
            name,
            kind,
            path,
            evidence_payload,
            acceptance=acceptance if isinstance(acceptance, dict) else None,
            acceptance_source=acceptance_source,
            acceptance_contract_failures=contract_failures if isinstance(acceptance, dict) else None,
        )
    )
    return evidence_payload


def _audit_exploratory_asset(
    asset: ReleaseAuditExploratoryAssetSpec,
    *,
    repo_root: Path,
    checks: list[dict[str, Any]],
    evidence_matrix: list[dict[str, Any]],
) -> None:
    config_path = _resolve(repo_root, asset.config)
    classified, classify_error = _classify_exploratory_config(config_path)
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:config",
        label=f"{asset.name} exploratory config is classified",
        passed=classified == asset.kind,
        required=asset.required,
        summary=f"classified={classified}, expected={asset.kind}",
        details={"config": str(config_path), "error": classify_error},
    )

    if asset.artifact is None:
        _skipped(
            checks,
            check_id=f"exploratory_asset:{asset.name}:artifact",
            label=f"{asset.name} exploratory artifact is optional in this manifest",
            summary="No artifact path configured; config classification is still audited.",
        )
        return

    artifact_path = _resolve(repo_root, asset.artifact)
    payload = _audit_artifact(
        name=asset.name,
        path=artifact_path,
        repo_root=repo_root,
        required=asset.required,
        kind=asset.kind,
        checks=checks,
        evidence_matrix=evidence_matrix,
        id_prefix="exploratory_asset",
        acceptance_required=False,
    )
    if payload is None:
        return

    evidence = payload.get("evidence_summary") or {}
    verification_status = payload.get("verification_status")
    trust_tier = evidence.get("trust_tier")
    boundary_ok = verification_status == "exploratory" and trust_tier == "exploratory"
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:boundary",
        label=f"{asset.name} remains exploratory",
        passed=boundary_ok,
        required=asset.required,
        summary=f"verification_status={verification_status}, trust_tier={trust_tier}",
        details={"kind": asset.kind},
    )
    section_ok = _has_required_exploratory_section(asset.kind, payload)
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:section",
        label=f"{asset.name} carries its algorithm section",
        passed=section_ok,
        required=asset.required,
        summary=f"Required section for {asset.kind} is present." if section_ok else f"Missing section for {asset.kind}.",
    )
    notes = _risk_notes(payload)
    _check(
        checks,
        check_id=f"exploratory_asset:{asset.name}:risk_notes",
        label=f"{asset.name} carries scientific risk notes",
        passed=bool(notes),
        required=asset.required,
        summary="Scientific risk notes are present." if notes else "Scientific risk notes are missing.",
    )


def _audit_docs(spec: ReleaseAuditSpec, *, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    for doc in spec.required_docs:
        path = _resolve(repo_root, doc.path)
        if not path.exists():
            _check(
                checks,
                check_id=f"doc:{doc.path}:exists",
                label=f"{doc.path} exists",
                passed=False,
                required=doc.required,
                details={"path": str(path)},
            )
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except (OSError, UnicodeError) as exc:
            _check(
                checks,
                check_id=f"doc:{doc.path}:readable",
                label=f"{doc.path} is readable text",
                passed=False,
                required=doc.required,
                summary="Document exists but could not be read as UTF-8 text.",
                details={"path": str(path), "error": f"{type(exc).__name__}: {exc}"},
            )
            continue
        missing = [term for term in doc.terms if term.lower() not in text]
        _check(
            checks,
            check_id=f"doc:{doc.path}:terms",
            label=f"{doc.path} includes release terms",
            passed=not missing,
            required=doc.required,
            summary="All release terms are present." if not missing else "Some release terms are missing.",
            details={"missing_terms": missing},
    )


def _audit_custom_workflow_extensions(*, repo_root: Path, checks: list[dict[str, Any]]) -> None:
    workflow_examples = [
        repo_root / "examples" / "workflows" / "h2_trust_first_workflow.yaml",
        repo_root / "examples" / "workflows" / "research_os_workflow.yaml",
        repo_root / "examples" / "workflows" / "branch_and_report_workflow.yaml",
        repo_root / "examples" / "workflows" / "plugin_loop_workflow.yaml",
    ]
    plugin_example_files = [
        repo_root / "examples" / "workflow_plugins" / "README.md",
        repo_root / "examples" / "workflow_plugins" / "qcchem_workflow_echo_plugin" / "pyproject.toml",
        repo_root
        / "examples"
        / "workflow_plugins"
        / "qcchem_workflow_echo_plugin"
        / "src"
        / "qcchem_workflow_echo_plugin"
        / "__init__.py",
    ]
    missing_examples = [
        str(path.relative_to(repo_root))
        for path in [*workflow_examples, *plugin_example_files]
        if not path.exists()
    ]
    _check(
        checks,
        check_id="custom_workflows:examples_exist",
        label="Custom workflow YAML and plugin examples exist",
        passed=not missing_examples,
        required=False,
        summary="Custom workflow examples are present." if not missing_examples else "Some custom workflow examples are missing.",
        details={"missing_examples": missing_examples},
    )

    try:
        from qcchem.workflow.custom_workflow import validate_workflow_from_config, workflow_plugins_summary

        h2_validation = validate_workflow_from_config(workflow_examples[0], include_installed=False)
        plugins = workflow_plugins_summary(include_installed=False)
        importable = True
        import_error = ""
    except Exception as exc:
        h2_validation = {}
        plugins = {}
        importable = False
        import_error = f"{type(exc).__name__}: {exc}"
    _check(
        checks,
        check_id="custom_workflows:builtin_example_validates",
        label="Built-in custom workflow example validates without installed plugins",
        passed=importable and h2_validation.get("status") == "valid",
        required=False,
        summary=(
            "Built-in workflow example validates."
            if importable and h2_validation.get("status") == "valid"
            else "Built-in workflow example failed validation."
        ),
        details={
            "workflow": str(workflow_examples[0].relative_to(repo_root)),
            "status": h2_validation.get("status"),
            "error": import_error,
        },
    )

    plugin_kinds = {item.get("kind") for item in plugins.get("plugins", [])} if isinstance(plugins, dict) else set()
    expected_builtin_plugins = {"run_config", "capsule_validate", "claim_check", "compare_artifacts"}
    missing_plugins = sorted(expected_builtin_plugins - plugin_kinds)
    _check(
        checks,
        check_id="custom_workflows:builtin_plugins_registered",
        label="Custom workflow built-in plugins are registered",
        passed=not missing_plugins,
        required=False,
        summary="Built-in workflow plugins are registered." if not missing_plugins else "Some built-in workflow plugins are missing.",
        details={"missing_plugins": missing_plugins},
    )

    index = build_artifact_index(repo_root / "artifacts")
    workflow_entries = [
        entry for entry in index.get("artifacts", []) if entry.get("artifact_kind") == "workflow"
    ]
    if workflow_entries:
        incomplete = [
            entry.get("artifact_name")
            for entry in workflow_entries
            if not (
                entry.get("has_workflow_graph")
                and entry.get("has_workflow_provenance")
                and entry.get("has_workflow_registry")
                and entry.get("has_report_markdown")
            )
        ]
        _check(
            checks,
            check_id="custom_workflows:index_contract",
            label="Workflow artifacts satisfy artifact-index contract",
            passed=not incomplete,
            required=False,
            summary="Indexed workflow artifacts carry graph, provenance, registry, and report files."
            if not incomplete
            else "Some indexed workflow artifacts are incomplete.",
            details={"workflow_artifacts": len(workflow_entries), "incomplete": incomplete},
        )
    else:
        _skipped(
            checks,
            check_id="custom_workflows:index_contract",
            label="Workflow artifacts satisfy artifact-index contract",
            summary="No workflow_result.json artifacts exist under artifacts/ yet; artifact-index support is covered by tests.",
        )


def _audit_research_os_extensions(*, repo_root: Path, checks: list[dict[str, Any]], evidence_matrix: list[dict[str, Any]]) -> None:
    examples = [
        repo_root / "configs" / "objectives" / "h2_local_validation.yaml",
        repo_root / "configs" / "objectives" / "lih_compression_trust_loop.yaml",
        repo_root / "examples" / "claims" / "hardware_overclaim.txt",
        repo_root / "examples" / "claims" / "local_validated_claim.txt",
        repo_root / "examples" / "claims" / "exploratory_lr_ace_claim.txt",
    ]
    missing_examples = [str(path.relative_to(repo_root)) for path in examples if not path.exists()]
    _check(
        checks,
        check_id="research_os:examples_exist",
        label="Research OS objective and claim examples exist",
        passed=not missing_examples,
        required=False,
        summary="Research OS examples are present." if not missing_examples else "Some Research OS examples are missing.",
        details={"missing_examples": missing_examples},
    )

    try:
        from qcchem.workflow.claim_compiler import compile_claim_review
        from qcchem.workflow.evidence_capsule import build_and_write_evidence_capsule
        from qcchem.workflow.objective import plan_research_objective
        from qcchem.workflow.promotion import review_exploratory_promotion

        importable = all([compile_claim_review, build_and_write_evidence_capsule, plan_research_objective, review_exploratory_promotion])
    except Exception as exc:
        importable = False
        import_error = f"{type(exc).__name__}: {exc}"
    else:
        import_error = ""
    _check(
        checks,
        check_id="research_os:cli_commands_importable",
        label="Research OS CLI workflow functions are importable",
        passed=importable,
        required=False,
        summary="Research OS workflow functions are importable." if importable else "Research OS workflow functions failed import.",
        details={"error": import_error},
    )

    curated_incomplete = [
        entry.get("name")
        for entry in evidence_matrix
        if not all(
            entry.get(key) is not None
            for key in ("trust_tier", "recommended_action")
        )
    ]
    _check(
        checks,
        check_id="research_os:curated_evidence_summary_complete",
        label="Curated artifacts expose release-readable evidence summaries",
        passed=not curated_incomplete,
        required=False,
        summary="Curated evidence summaries are release-readable." if not curated_incomplete else "Some curated artifacts still rely on derived release evidence.",
        details={"incomplete": curated_incomplete},
    )

    docs_to_scan = [
        repo_root / "README.md",
        repo_root / "docs" / "verified_scope.md",
        repo_root / "docs" / "release_showcase.md",
        repo_root / "docs" / "release_audit.md",
    ]
    forbidden_patterns = [
        "hardware_verified proves publication-grade chemical accuracy",
        "hardware_verified proves chemistry",
        "exploratory is validated",
    ]
    overclaim_hits: list[str] = []
    for path in docs_to_scan:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for pattern in forbidden_patterns:
            if pattern in text:
                overclaim_hits.append(f"{path.relative_to(repo_root)}:{pattern}")
    _check(
        checks,
        check_id="research_os:no_overclaim_language",
        label="Release docs avoid forbidden overclaim language",
        passed=not overclaim_hits,
        required=False,
        summary="No forbidden overclaim phrases found." if not overclaim_hits else "Forbidden overclaim phrases found.",
        details={"hits": overclaim_hits},
    )

    promotion_artifact = repo_root / "artifacts" / "h2_lr_ace" / "result.json"
    if promotion_artifact.exists() and importable:
        from qcchem.workflow.promotion import review_exploratory_promotion

        review = review_exploratory_promotion(
            artifact=promotion_artifact,
            target="validated_algorithm_candidate",
        )
        _check(
            checks,
            check_id="research_os:promotion_gate_blocks_exploratory",
            label="Promotion gate blocks direct exploratory promotion",
            passed=review.get("status") == "blocked",
            required=False,
            summary=f"Promotion review status={review.get('status')}",
            details={"artifact": str(promotion_artifact), "blocking_gaps": review.get("blocking_gaps")},
        )
    else:
        _skipped(
            checks,
            check_id="research_os:promotion_gate_blocks_exploratory",
            label="Promotion gate blocks direct exploratory promotion",
            summary="No h2_lr_ace artifact was available for optional promotion-gate smoke.",
        )


def _github_actions_handoff_context() -> dict[str, Any]:
    env = os.environ
    github_actions = env.get("GITHUB_ACTIONS") == "true"
    server_url = env.get("GITHUB_SERVER_URL") or "https://github.com"
    api_url = env.get("GITHUB_API_URL") or "https://api.github.com"
    repository = env.get("GITHUB_REPOSITORY")
    run_id = env.get("GITHUB_RUN_ID")
    run_url = f"{server_url}/{repository}/actions/runs/{run_id}" if github_actions and repository and run_id else None
    return {
        "provider": "github_actions" if github_actions else "local",
        "run_url": run_url,
        "api_url": api_url if github_actions else None,
        "run_id": run_id,
        "run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "repository": repository,
        "workflow": env.get("GITHUB_WORKFLOW"),
        "job": env.get("GITHUB_JOB"),
        "sha": env.get("GITHUB_SHA"),
        "ref": env.get("GITHUB_REF"),
    }


def _build_release_handoff(summary: dict[str, Any]) -> dict[str, Any]:
    audit_provenance = summary.get("audit_provenance") if isinstance(summary.get("audit_provenance"), dict) else {}
    ci = _github_actions_handoff_context()
    artifact_name = os.environ.get(CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_ENV) or None
    return {
        "schema_version": RELEASE_HANDOFF_SCHEMA_VERSION,
        "generated_at_utc": audit_provenance.get("generated_at_utc"),
        "status": summary.get("status"),
        "recommended_action": summary.get("recommended_action"),
        "release_readiness": {
            "json": "release_readiness.json",
            "markdown": "release_readiness.md",
        },
        "release_audit": {
            "profile": summary.get("profile"),
            "release_version": summary.get("release_version"),
            "manifest_path": audit_provenance.get("manifest_path"),
            "output_dir": audit_provenance.get("output_dir"),
            "required_fail_count": summary.get("required_fail_count"),
            "warning_count": summary.get("warning_count"),
            "release_acceptance_sidecars_status": (
                summary.get("release_acceptance_sidecars", {}).get("status")
                if isinstance(summary.get("release_acceptance_sidecars"), dict)
                else None
            ),
        },
        "ci": ci,
        "diagnostic_artifacts": {
            "names": [artifact_name] if artifact_name else [],
            "name_prefix": CI_RELEASE_DIAGNOSTIC_ARTIFACT_NAME_PREFIX,
            "artifact_listing_url": (
                f"{ci['api_url']}/repos/{ci['repository']}/actions/runs/{ci['run_id']}/artifacts"
                if ci.get("api_url") and ci.get("repository") and ci.get("run_id")
                else None
            ),
            "upload_paths": list(CI_RELEASE_DIAGNOSTIC_REQUIRED_PATHS),
        },
    }


def _render_release_handoff_markdown(handoff: dict[str, Any]) -> str:
    ci = handoff.get("ci") if isinstance(handoff.get("ci"), dict) else {}
    release_audit = handoff.get("release_audit") if isinstance(handoff.get("release_audit"), dict) else {}
    diagnostic_artifacts = (
        handoff.get("diagnostic_artifacts")
        if isinstance(handoff.get("diagnostic_artifacts"), dict)
        else {}
    )
    lines = [
        "# QCchem Release Handoff",
        "",
        "- output: `release_handoff.md`",
        f"- schema_version: `{handoff.get('schema_version')}`",
        f"- generated_at_utc: `{handoff.get('generated_at_utc')}`",
        f"- status: `{handoff.get('status')}`",
        f"- recommended_action: `{handoff.get('recommended_action')}`",
        f"- readiness_json: `{handoff.get('release_readiness', {}).get('json')}`",
        f"- readiness_markdown: `{handoff.get('release_readiness', {}).get('markdown')}`",
        f"- manifest_path: `{release_audit.get('manifest_path')}`",
        f"- output_dir: `{release_audit.get('output_dir')}`",
        f"- required_fail_count: `{release_audit.get('required_fail_count')}`",
        f"- warning_count: `{release_audit.get('warning_count')}`",
        f"- release_acceptance_sidecars_status: `{release_audit.get('release_acceptance_sidecars_status')}`",
        "",
        "## CI Run",
        "",
    ]
    if ci.get("provider") == "github_actions" and ci.get("run_url"):
        lines.extend(
            [
                f"- provider: `{ci.get('provider')}`",
                f"- run_url: {ci.get('run_url')}",
                f"- run_attempt: `{ci.get('run_attempt')}`",
                f"- workflow: `{ci.get('workflow')}`",
                f"- job: `{ci.get('job')}`",
                f"- sha: `{ci.get('sha')}`",
                f"- ref: `{ci.get('ref')}`",
            ]
        )
    else:
        lines.append("No GitHub Actions run context was available.")

    artifact_names = diagnostic_artifacts.get("names") if isinstance(diagnostic_artifacts.get("names"), list) else []
    lines.extend(["", "## Diagnostic Artifacts", ""])
    if artifact_names:
        for name in artifact_names:
            lines.append(f"- `{name}`")
    else:
        lines.append("- No run-specific diagnostic artifact name was available.")
    artifact_listing_url = diagnostic_artifacts.get("artifact_listing_url")
    if artifact_listing_url:
        lines.append(f"- artifact_listing_url: {artifact_listing_url}")
    lines.extend(["", "## Uploaded Paths", ""])
    for path in diagnostic_artifacts.get("upload_paths", []):
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


def _render_release_audit_markdown(summary: dict[str, Any]) -> str:
    audit_provenance = summary.get("audit_provenance") if isinstance(summary.get("audit_provenance"), dict) else {}
    lines = [
        "# QCchem Release Readiness Audit",
        "",
        "- output: `release_readiness.md`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- schema_features: `{', '.join(summary.get('schema_features', []))}`",
        f"- profile: `{summary['profile']}`",
        f"- release_version: `{summary['release_version']}`",
        f"- generated_at_utc: `{audit_provenance.get('generated_at_utc')}`",
        f"- repo_root: `{audit_provenance.get('repo_root')}`",
        f"- manifest_path: `{audit_provenance.get('manifest_path')}`",
        f"- output_dir: `{audit_provenance.get('output_dir')}`",
        f"- status: `{summary['status']}`",
        f"- recommended_action: `{summary['recommended_action']}`",
        f"- required_pass_count: `{summary['required_pass_count']}`",
        f"- required_fail_count: `{summary['required_fail_count']}`",
        f"- warning_count: `{summary.get('warning_count', 0)}`",
    ]
    warning_policy = summary.get("warning_policy")
    if isinstance(warning_policy, dict):
        allowed_ids = warning_policy.get("allowed_ids")
        unexpected_ids = warning_policy.get("unexpected_ids") or []
        lines.extend(
            [
                f"- warning_policy_status: `{warning_policy.get('status')}`",
                f"- warning_policy_max_count: `{warning_policy.get('max_count')}`",
                f"- warning_policy_unexpected_count: `{len(warning_policy.get('unexpected_ids') or [])}`",
                f"- warning_policy_allowed_ids: `{json.dumps(allowed_ids, sort_keys=True)}`",
                f"- warning_policy_unexpected_ids: `{json.dumps(unexpected_ids, sort_keys=True)}`",
            ]
        )
    release_acceptance_sidecars = (
        summary.get("release_acceptance_sidecars")
        if isinstance(summary.get("release_acceptance_sidecars"), dict)
        else {}
    )
    if release_acceptance_sidecars:
        lines.extend(
            [
                f"- release_acceptance_sidecars_status: `{release_acceptance_sidecars.get('status')}`",
                f"- release_acceptance_sidecars_fresh_count: `{release_acceptance_sidecars.get('fresh_count')}`",
                (
                    "- release_acceptance_sidecars_requires_update_count: "
                    f"`{release_acceptance_sidecars.get('requires_update_count')}`"
                ),
                f"- release_acceptance_repair_plan_count: `{release_acceptance_sidecars.get('repair_plan_count')}`",
            ]
        )
    required_failed_checks = summary.get("required_failed_checks") or []
    if required_failed_checks:
        lines.extend(["", "## Required Failed Checks", ""])
        for check in required_failed_checks:
            lines.extend(
                [
                    f"- `{check['id']}`",
                    f"  - summary: {check.get('summary', '')}",
                    f"  - details: `{json.dumps(check.get('details', {}), sort_keys=True)}`",
                ]
            )
    required_failed_ids = {item.get("id") for item in required_failed_checks}
    failed_checks = [
        check
        for check in summary.get("failed_checks", [])
        if check.get("id") not in required_failed_ids
    ]
    if failed_checks:
        lines.extend(["", "## Optional Failed Checks", ""])
        for check in failed_checks:
            lines.extend(
                [
                    f"- `{check['id']}` required=`{check['required']}`",
                    f"  - summary: {check.get('summary', '')}",
                    f"  - details: `{json.dumps(check.get('details', {}), sort_keys=True)}`",
                ]
            )
    warning_checks = summary.get("warning_checks") or []
    if warning_checks:
        lines.extend(["", "## Warning Checks", ""])
        for check in warning_checks:
            lines.extend(
                [
                    f"- `{check['id']}`",
                    f"  - summary: {check.get('summary', '')}",
                    f"  - details: `{json.dumps(check.get('details', {}), sort_keys=True)}`",
                ]
            )
    acceptance_command_failures = _acceptance_command_repair_failures(summary)
    if acceptance_command_failures:
        lines.extend(["", "## Acceptance Command Repairs", ""])
        for failure in acceptance_command_failures:
            reason = failure.get("reason", "unknown")
            remediation = failure.get("remediation") or _acceptance_failure_remediation(failure)
            lines.extend(
                [
                    f"- command[{failure.get('index')}]: {_markdown_code_span(failure.get('command', ''))}",
                    f"  - reason: {_markdown_code_span(reason)}",
                    f"  - remediation: {remediation}",
                ]
            )
    acceptance_contract_failures = _acceptance_contract_repair_failures(summary)
    if acceptance_contract_failures:
        lines.extend(["", "## Acceptance Contract Repairs", ""])
        for failure in acceptance_contract_failures:
            lines.extend(
                [
                    f"- `{failure.get('check_id')}` field={_markdown_code_span(failure.get('field'))}",
                    f"  - source: {_markdown_code_span(failure.get('source'))}",
                    f"  - expected: {_markdown_contract_value(failure.get('expected'))}",
                    f"  - actual: {_markdown_contract_value(failure.get('actual'))}",
                ]
            )
            if failure.get("reason") is not None:
                lines.append(f"  - reason: {_markdown_code_span(failure.get('reason'))}")
    release_acceptance_repairs = _release_acceptance_repair_plan_items(summary)
    if release_acceptance_repairs:
        lines.extend(["", "## Release Sidecar Repair Plan", ""])
        for item in release_acceptance_repairs:
            lines.extend(
                [
                    (
                        f"- {_markdown_code_span(item.get('artifact_name'))} "
                        f"status={_markdown_code_span(item.get('status'))} "
                        f"issue={_markdown_code_span(item.get('issue'))}"
                    ),
                    f"  - sidecar: {_markdown_code_span(item.get('sidecar_path'))}",
                ]
            )
            preview_command = item.get("preview_command")
            repair_command = item.get("repair_command")
            if preview_command:
                lines.append(f"  - preview: {_markdown_code_span(preview_command)}")
            if repair_command:
                lines.append(f"  - repair: {_markdown_code_span(repair_command)}")
            if not preview_command and not repair_command:
                lines.append(f"  - action: {_markdown_code_span(item.get('recommended_action'))}")
    lines.extend(["", "## Evidence Matrix", ""])
    for entry in summary["evidence_matrix"]:
        lines.extend(
            [
                f"### {entry['name']}",
                "",
                f"- kind: `{entry['kind']}`",
                f"- primary_scientific_claim: {_markdown_code_span(entry.get('primary_scientific_claim'))}",
                f"- primary_baseline: {_markdown_code_span(json.dumps(entry.get('primary_baseline'), sort_keys=True))}",
                f"- primary_error_metric: {_markdown_code_span(json.dumps(entry.get('primary_error_metric'), sort_keys=True))}",
                f"- chemical_accuracy_status: `{entry.get('chemical_accuracy_status')}`",
                f"- trust_tier: `{entry.get('trust_tier')}`",
                f"- recommended_action: `{entry.get('recommended_action')}`",
                f"- review_warning_count: `{entry.get('review_warning_count', 0)}`",
                f"- review_warnings: {_markdown_code_span(json.dumps(entry.get('review_warnings') or [], sort_keys=True))}",
                f"- hardware_verified: `{entry.get('hardware_verified')}`",
                f"- runtime_evidence_status: `{entry.get('runtime_evidence_status')}`",
                f"- hardware_verified_case_count: `{entry.get('hardware_verified_case_count', 0)}`",
                f"- runtime_submission_status: `{entry.get('runtime_submission_status')}`",
                f"- acceptance_summary_source: `{entry.get('acceptance_summary_source')}`",
                f"- acceptance_schema_version: `{entry.get('acceptance_schema_version')}`",
                f"- acceptance_artifact_path: `{entry.get('acceptance_artifact_path')}`",
                f"- acceptance_artifact_sha256: `{entry.get('acceptance_artifact_sha256')}`",
                f"- acceptance_release_audit_check_id: `{entry.get('acceptance_release_audit_check_id')}`",
                f"- acceptance_trust_tier: `{entry.get('acceptance_trust_tier')}`",
                f"- acceptance_runtime_evidence_status: `{entry.get('acceptance_runtime_evidence_status')}`",
                f"- acceptance_status: `{entry.get('acceptance_status')}`",
                f"- acceptance_recommended_action: `{entry.get('acceptance_recommended_action')}`",
                f"- acceptance_blocking_failure_count: `{entry.get('acceptance_blocking_failure_count', 0)}`",
                f"- acceptance_warning_count: `{entry.get('acceptance_warning_count', 0)}`",
                f"- acceptance_contract_failure_count: `{entry.get('acceptance_contract_failure_count', 0)}`",
                f"- path: `{entry.get('path')}`",
                "",
            ]
        )
    lines.extend(["## Checks", ""])
    for check in summary["checks"]:
        lines.append(
            f"- `{check['status']}` `{check['id']}` required=`{check['required']}` - {check.get('summary', '')}"
        )
    lines.append("")
    return "\n".join(lines)


def run_release_audit(
    spec: ReleaseAuditSpec,
    *,
    repo_root: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the Trust-First release audit and write readiness artifacts."""
    default_repo_root = workspace_root_for_path(spec.source_path) if spec.source_path is not None else Path.cwd()
    resolved_repo_root = (repo_root or default_repo_root).resolve()
    resolved_output_dir = (output_dir or resolved_repo_root / "artifacts" / "release_audit").resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    evidence_matrix: list[dict[str, Any]] = []

    project_version = _read_project_version(resolved_repo_root / "pyproject.toml")
    _check(
        checks,
        check_id="project:version",
        label="pyproject release version matches audit manifest",
        passed=project_version == spec.release_version,
        required=True,
        summary=f"pyproject={project_version}, expected={spec.release_version}",
    )

    _audit_acceptance_commands(spec, repo_root=resolved_repo_root, checks=checks)
    _audit_ci_acceptance_alignment(spec, repo_root=resolved_repo_root, checks=checks)
    _audit_ci_acceptance_status_gate(repo_root=resolved_repo_root, checks=checks)
    _audit_ci_release_diagnostic_artifacts(repo_root=resolved_repo_root, checks=checks)

    for artifact in spec.curated_artifacts:
        _audit_artifact(
            name=artifact.name,
            path=_resolve(resolved_repo_root, artifact.path),
            repo_root=resolved_repo_root,
            required=artifact.required,
            kind="curated",
            checks=checks,
            evidence_matrix=evidence_matrix,
            id_prefix="curated_artifact",
            acceptance_required=artifact.acceptance_required,
        )

    for asset in spec.exploratory_assets:
        _audit_exploratory_asset(asset, repo_root=resolved_repo_root, checks=checks, evidence_matrix=evidence_matrix)

    _audit_docs(spec, repo_root=resolved_repo_root, checks=checks)
    _audit_custom_workflow_extensions(repo_root=resolved_repo_root, checks=checks)
    _audit_research_os_extensions(repo_root=resolved_repo_root, checks=checks, evidence_matrix=evidence_matrix)
    warning_policy_summary = _apply_warning_policy(checks, spec.warning_policy)

    required_pass_count = sum(1 for check in checks if check["required"] and check["status"] == "passed")
    required_fail_count = sum(1 for check in checks if check["required"] and check["status"] == "failed")
    warning_count = sum(1 for check in checks if check["status"] == "warning")
    status = "passed" if required_fail_count == 0 else "failed"
    failed_checks = _check_summaries(checks, status="failed")
    required_failed_checks = _check_summaries(checks, status="failed", required=True)
    warning_checks = _check_summaries(checks, status="warning")
    from qcchem.workflow.release_acceptance import release_acceptance_status_report

    release_acceptance_sidecars = release_acceptance_status_report(
        spec,
        repo_root=resolved_repo_root,
    )
    audit_provenance = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "repo_root": str(resolved_repo_root),
        "manifest_path": _path_for_audit_provenance(spec.source_path, repo_root=resolved_repo_root),
        "output_dir": _path_for_audit_provenance(resolved_output_dir, repo_root=resolved_repo_root),
    }
    summary = {
        "schema_version": RELEASE_AUDIT_SCHEMA_VERSION,
        "schema_features": RELEASE_AUDIT_SCHEMA_FEATURES,
        "profile": spec.profile,
        "release_version": spec.release_version,
        "audit_provenance": audit_provenance,
        "status": status,
        "required_pass_count": required_pass_count,
        "required_fail_count": required_fail_count,
        "warning_count": warning_count,
        "failed_checks": failed_checks,
        "required_failed_checks": required_failed_checks,
        "warning_checks": warning_checks,
        "warning_policy": warning_policy_summary,
        "release_acceptance_sidecars": release_acceptance_sidecars,
        "checks": checks,
        "evidence_matrix": evidence_matrix,
        "acceptance_commands": list(spec.acceptance_commands),
        "recommended_action": "promote_alpha_release_candidate" if status == "passed" else "resolve_release_audit_failures",
    }

    (resolved_output_dir / "release_readiness.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (resolved_output_dir / "release_readiness.md").write_text(
        _render_release_audit_markdown(summary),
        encoding="utf-8",
    )
    handoff = _build_release_handoff(summary)
    (resolved_output_dir / "release_handoff.json").write_text(
        json.dumps(handoff, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (resolved_output_dir / "release_handoff.md").write_text(
        _render_release_handoff_markdown(handoff),
        encoding="utf-8",
    )
    return summary


def run_release_audit_from_config(
    config_path: Path,
    *,
    output_dir: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Load and run a release audit manifest."""
    resolved_config_path = config_path.expanduser()
    if not resolved_config_path.is_absolute() and repo_root is not None:
        resolved_config_path = repo_root.expanduser() / resolved_config_path
    spec = load_release_audit_spec(resolved_config_path)
    return run_release_audit(spec, repo_root=repo_root, output_dir=output_dir)
