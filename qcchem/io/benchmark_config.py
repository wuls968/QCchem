"""Benchmark-suite config loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from qcchem.core import BenchmarkAcceptanceSpec, BenchmarkCaseSpec, BenchmarkSuiteSpec
from qcchem.io.config import _project_root, _require_mapping, resolve_user_path


@dataclass(slots=True)
class HardwareCalibrationCaseSpec:
    """One run artifact included in a hardware-calibration dashboard."""

    name: str
    result_json: Path


@dataclass(slots=True)
class HardwareCalibrationSuiteSpec:
    """Top-level hardware-calibration dashboard specification."""

    name: str
    description: str = ""
    output_root: Path = Path("artifacts/hardware_calibration_suite")
    cases: list[HardwareCalibrationCaseSpec] = field(default_factory=list)


def _load_benchmark_config_mapping(path: Path) -> dict[str, Any]:
    resolved_path = path if path.is_absolute() else resolve_user_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Benchmark-suite configuration must deserialize to a mapping.")
    return raw


def _resolve_project_path(value: str | Path) -> Path:
    candidate = Path(str(value))
    return candidate if candidate.is_absolute() else (_project_root() / candidate).resolve()


def load_benchmark_suite_spec(path: Path) -> BenchmarkSuiteSpec:
    """Load a benchmark-suite specification from YAML."""
    raw = _load_benchmark_config_mapping(path)
    suite_raw = _require_mapping(raw, "benchmark_suite")
    cases_raw = suite_raw.get("cases", [])
    if not isinstance(cases_raw, list) or not cases_raw:
        raise ValueError("benchmark_suite.cases must be a non-empty list.")

    cases: list[BenchmarkCaseSpec] = []
    for item in cases_raw:
        if not isinstance(item, dict):
            raise ValueError("Each benchmark case must be a mapping.")
        config_value = item.get("config")
        config_path = None
        if config_value is not None:
            config_path = _resolve_project_path(config_value)
        cases.append(
            BenchmarkCaseSpec(
                name=str(item["name"]),
                kind=str(item["kind"]),
                config=config_path,
                overrides=dict(item.get("overrides", {})),
                expected_status=str(item.get("expected_status", "validated")),
                profile=(str(item["profile"]) if item.get("profile") is not None else None),
                shots=[int(value) for value in item.get("shots", [])],
                optimizers=[str(value) for value in item.get("optimizers", [])],
                tags=[str(value) for value in item.get("tags", [])],
            )
        )

    acceptance_raw = suite_raw.get("acceptance", {})
    if acceptance_raw is None:
        acceptance_raw = {}
    if not isinstance(acceptance_raw, dict):
        raise ValueError("benchmark_suite.acceptance must be a mapping.")

    return BenchmarkSuiteSpec(
        name=str(suite_raw["name"]),
        description=str(suite_raw.get("description", "")),
        registry_name=str(suite_raw.get("registry_name", suite_raw["name"])),
        cases=cases,
        tags=[str(value) for value in suite_raw.get("tags", [])],
        acceptance=BenchmarkAcceptanceSpec(
            enabled=bool(acceptance_raw.get("enabled", True)),
            required_files=[str(value) for value in acceptance_raw.get("required_files", ["result.json"])],
            require_evidence_summary=bool(acceptance_raw.get("require_evidence_summary", True)),
            require_runtime_sidecar_for_hardware_verified=bool(
                acceptance_raw.get("require_runtime_sidecar_for_hardware_verified", True)
            ),
            fail_on_runtime_accuracy_promotion=bool(
                acceptance_raw.get("fail_on_runtime_accuracy_promotion", True)
            ),
            strict_exit_code=bool(acceptance_raw.get("strict_exit_code", True)),
        ),
    )


def load_hardware_calibration_suite_spec(path: Path) -> HardwareCalibrationSuiteSpec:
    """Load a hardware-calibration dashboard specification from YAML."""
    raw = _load_benchmark_config_mapping(path)
    suite_raw = _require_mapping(raw, "hardware_calibration_suite")
    cases_raw = suite_raw.get("cases", [])
    if not isinstance(cases_raw, list) or not cases_raw:
        raise ValueError("hardware_calibration_suite.cases must be a non-empty list.")

    cases: list[HardwareCalibrationCaseSpec] = []
    for item in cases_raw:
        if not isinstance(item, dict):
            raise ValueError("Each hardware calibration case must be a mapping.")
        result_json_value = item.get("result_json")
        if result_json_value is None:
            raise ValueError("hardware_calibration_suite.cases[].result_json is required.")
        cases.append(
            HardwareCalibrationCaseSpec(
                name=str(item["name"]),
                result_json=_resolve_project_path(result_json_value),
            )
        )

    output_root = _resolve_project_path(
        suite_raw.get("output_root", Path("artifacts") / str(suite_raw["name"]))
    )
    return HardwareCalibrationSuiteSpec(
        name=str(suite_raw["name"]),
        description=str(suite_raw.get("description", "")),
        output_root=output_root,
        cases=cases,
    )


def load_benchmark_entry_spec(path: Path) -> BenchmarkSuiteSpec | HardwareCalibrationSuiteSpec:
    """Load any config supported by the benchmark entry point."""
    raw = _load_benchmark_config_mapping(path)
    if "benchmark_suite" in raw:
        return load_benchmark_suite_spec(path)
    if "hardware_calibration_suite" in raw:
        return load_hardware_calibration_suite_spec(path)
    raise ValueError(
        "Benchmark entry-point configuration must contain either 'benchmark_suite' "
        "or 'hardware_calibration_suite'."
    )
