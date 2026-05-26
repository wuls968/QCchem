"""Executable validation harness for Gamma-only PBC and PBC-QM/MM."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from qcchem.io.serialization import to_primitive
from qcchem.workbench.viewmodels import build_run_view_model
from qcchem.workflow.runner import run_from_config


SCHEMA = "qcchem.pbc_qmmm_validation.v1"


@dataclass(slots=True)
class PBCQMMMValidationCase:
    """One PBC/PBC-QM/MM validation case."""

    name: str
    config_path: Path
    expected_status: str = "executed"
    expect_error: str | None = None
    requires_pbc_qmmm: bool = False
    overrides: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _to_primitive(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _to_primitive(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_primitive(item) for item in value]
    return to_primitive(value)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _case(name: str, config: str, **kwargs: Any) -> PBCQMMMValidationCase:
    return PBCQMMMValidationCase(
        name=name,
        config_path=_repo_root() / "configs" / config,
        **kwargs,
    )


def default_pbc_qmmm_validation_cases(*, profile: str = "smoke") -> list[PBCQMMMValidationCase]:
    """Return built-in executable validation cases for PBC/PBC-QM/MM."""

    normalized = profile.strip().lower()
    smoke = [
        _case(
            "pbc_gamma_exact",
            "pbc_h2_gamma.yaml",
            notes=["Plain Gamma-only supercell PBC exact workflow."],
        ),
        _case(
            "pbc_qmmm_ewald_exact",
            "pbc_h2_qmmm.yaml",
            requires_pbc_qmmm=True,
            notes=["Periodic QM/MM Ewald one-body and nuclear constant workflow."],
        ),
        _case(
            "pbc_non_gamma_reject",
            "pbc_h2_non_gamma_reject.yaml",
            expected_status="rejected",
            expect_error="Gamma-only",
            notes=["Non-Gamma k-point mesh must fail before quantum-algorithm execution."],
        ),
    ]
    if normalized == "smoke":
        return smoke
    if normalized != "full":
        raise ValueError("PBC-QMMM validation profile must be smoke or full.")
    return [
        *smoke,
        _case(
            "pbc_gamma_vqe_twolocal",
            "pbc_h2_gamma.yaml",
            overrides={
                "solver": {
                    "kind": "vqe",
                    "optimizer": {"kind": "COBYLA", "maxiter": 2},
                    "ansatz": {"kind": "twolocal", "reps": 1},
                    "initial_point": "zeros",
                },
                "benchmark.absolute_error_threshold": 2.0,
                "benchmark.relative_error_threshold": 2.0,
            },
            notes=["Gamma-only PBC through the generic VQE/twolocal solver surface."],
        ),
        _case(
            "pbc_gamma_active_space",
            "pbc_h2_gamma.yaml",
            overrides={
                "problem.active_space": {
                    "selection_mode": "manual",
                    "num_electrons": 2,
                    "num_spatial_orbitals": 1,
                    "active_orbitals": [0],
                },
                "benchmark.absolute_error_threshold": 2.0,
                "benchmark.relative_error_threshold": 2.0,
            },
            notes=["Gamma-only PBC with active-space projection."],
        ),
        _case(
            "pbc_gamma_compression",
            "pbc_h2_gamma.yaml",
            overrides={
                "problem.compression": {
                    "enabled": True,
                    "method": "modified_cholesky",
                    "threshold": 1.0e-3,
                    "max_rank": 2,
                    "execution_enabled": True,
                },
                "benchmark.absolute_error_threshold": 2.0,
                "benchmark.relative_error_threshold": 2.0,
            },
            notes=["Gamma-only PBC with low-rank compression execution metadata."],
        ),
        _case(
            "pbc_gamma_lr_ace",
            "pbc_h2_gamma.yaml",
            overrides={
                "policy.allow_exploratory": True,
                "exploratory": {
                    "enabled": True,
                    "modules": ["lr_ace"],
                    "notes": ["PBC validation full profile exercises LR-ACE routing."],
                },
                "problem.compression": {
                    "enabled": True,
                    "method": "modified_cholesky",
                    "threshold": 1.0e-3,
                    "max_rank": 2,
                    "apply_to_solver": True,
                    "execution_enabled": True,
                },
                "solver": {
                    "kind": "lr_ace",
                    "experimental": True,
                    "optimizer": {"kind": "COBYLA", "maxiter": 2},
                    "ansatz": {"kind": "lr_ace", "reps": 1},
                    "initial_point": "zeros",
                },
                "benchmark.absolute_error_threshold": 2.0,
                "benchmark.relative_error_threshold": 2.0,
            },
            notes=["Gamma-only PBC through the exploratory LR-ACE solver route."],
        ),
        _case(
            "pbc_gamma_tc_qsci",
            "pbc_h2_gamma.yaml",
            overrides={
                "policy.allow_exploratory": True,
                "exploratory": {
                    "enabled": True,
                    "modules": ["tc_qsci"],
                    "notes": ["PBC validation full profile exercises TC-QSCI routing."],
                },
                "tc_qsci": {
                    "enabled": True,
                    "cast_model": {"kind": "identity"},
                    "initial_state": {"kind": "hf"},
                    "kick": {
                        "time": 0.05,
                        "num_kicks": 1,
                        "pauli_term_budget": 8,
                        "shots": 128,
                    },
                    "selection": {
                        "max_determinants": 4,
                        "min_count": 1,
                        "symmetry_postselect": True,
                    },
                    "resource_estimation": {
                        "enabled": True,
                        "target_precision": 1.0e-3,
                    },
                },
            },
            notes=["Gamma-only PBC through the TC-QSCI determinant-selection route."],
        ),
    ]


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _set_mapping_path(payload: dict[str, Any], dotted_path: str, value: Any) -> None:
    target = payload
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        child = target.get(part)
        if not isinstance(child, dict):
            child = {}
            target[part] = child
        target = child
    target[parts[-1]] = value


def _materialize_case_config(case: PBCQMMMValidationCase, case_root: Path) -> Path:
    if not case.overrides:
        return case.config_path
    payload = _load_yaml(case.config_path)
    for dotted_path, value in case.overrides.items():
        _set_mapping_path(payload, dotted_path, value)
    path = case_root / "case_config.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _config_pbc_payload(config_path: Path) -> dict[str, Any]:
    raw = _load_yaml(config_path)
    molecule_periodic = _as_dict(_as_dict(raw.get("molecule")).get("periodic"))
    pbc = _as_dict(_as_dict(raw.get("problem")).get("pbc"))
    cell = _as_dict(molecule_periodic.get("cell"))
    return {
        "enabled": bool(pbc.get("enabled") or molecule_periodic.get("enabled")),
        "cell": {
            "units": cell.get("unit") or cell.get("units"),
            "vectors": cell.get("vectors", []),
        },
        "kpoints": {"mode": "gamma", "grid": pbc.get("kpoint_mesh", [1, 1, 1])},
        "core_runner_implemented": pbc.get("kpoint_mesh", [1, 1, 1]) == [1, 1, 1],
    }


def _valid_cell_vectors(pbc: dict[str, Any]) -> bool:
    vectors = _as_dict(pbc.get("cell")).get("vectors")
    if not isinstance(vectors, list) or len(vectors) != 3:
        return False
    for row in vectors:
        if not isinstance(row, list) or len(row) != 3:
            return False
        try:
            [float(value) for value in row]
        except (TypeError, ValueError):
            return False
    return True


def _run_case(case: PBCQMMMValidationCase, case_root: Path) -> dict[str, Any]:
    case_root.mkdir(parents=True, exist_ok=True)
    config_path = _materialize_case_config(case, case_root)
    if case.expect_error:
        try:
            run_from_config(config_path, output_dir=case_root / "run")
        except Exception as exc:
            message = str(exc)
            passed = case.expect_error in message
            return {
                "case": case.name,
                "status": "rejected" if passed else "failed",
                "passed": passed,
                "failed_checks": [] if passed else ["expected_error_message"],
                "error_message": message,
                "config_path": str(config_path),
                "pbc": _config_pbc_payload(config_path),
                "pbc_qmmm": {},
                "artifacts": {},
                "notes": list(case.notes),
            }
        return {
            "case": case.name,
            "status": "failed",
            "passed": False,
            "failed_checks": ["expected_rejection"],
            "error_message": None,
            "config_path": str(config_path),
            "pbc": _config_pbc_payload(config_path),
            "pbc_qmmm": {},
            "artifacts": {},
            "notes": list(case.notes),
        }

    result = run_from_config(config_path, output_dir=case_root / "run")
    payload = to_primitive(result)
    pbc = _as_dict(payload.get("periodic_boundary") or payload.get("pbc"))
    pbc_qmmm = _as_dict(payload.get("pbc_qmmm"))
    artifacts = {
        "result_json": str(case_root / "run" / "result.json"),
        "report_markdown": str(case_root / "run" / "report.md"),
        "quantum_evidence_json": str(case_root / "run" / "quantum_evidence.json"),
        "qcschema_json": str(case_root / "run" / "qcschema.json"),
        "hdf5": str(case_root / "run" / "result.h5"),
    }
    artifact_checks = {
        key: Path(value).exists()
        for key, value in artifacts.items()
    }
    artifact_index = _as_dict(payload.get("artifact_index_entry"))
    view_model = build_run_view_model(payload)
    view_pbc = _as_dict(view_model.get("pbc"))
    view_pbc_qmmm = _as_dict(view_model.get("pbc_qmmm"))
    pass_fail = {
        "pbc_summary_present": bool(pbc),
        "pbc_enabled": pbc.get("enabled") is True,
        "cell_vectors_3x3": _valid_cell_vectors({"cell": {"vectors": pbc.get("cell_vectors", [])}}),
        "gamma_kpoint_executed": pbc.get("kpoint_mesh") == [1, 1, 1],
        "result_json_export": artifact_checks["result_json"],
        "report_markdown_export": artifact_checks["report_markdown"],
        "qcschema_export": artifact_checks["qcschema_json"],
        "quantum_evidence_export": artifact_checks["quantum_evidence_json"],
        "hdf5_export": artifact_checks["hdf5"],
        "artifact_index_pbc_flag": artifact_index.get("has_pbc_metadata") is True,
        "workbench_pbc_model": view_pbc.get("core_runner_implemented") is True,
        "pbc_qmmm_required": (bool(pbc_qmmm) if case.requires_pbc_qmmm else True),
        "workbench_pbc_qmmm_model": (
            view_pbc_qmmm.get("core_runner_implemented") is True
            if case.requires_pbc_qmmm
            else True
        ),
    }
    failed = [name for name, passed in pass_fail.items() if not passed]
    return {
        "case": case.name,
        "status": "executed" if not failed else "failed",
        "passed": not failed,
        "failed_checks": failed,
        "config_path": str(config_path),
        "verification_status": payload.get("verification_status"),
        "total_energy": _as_dict(payload.get("energy")).get("total_energy"),
        "periodicity": "3d" if pbc.get("pbc") == [True, True, True] else "mixed",
        "kpoint_mode": "gamma",
        "kpoint_grid": pbc.get("kpoint_mesh"),
        "embedding_mode": pbc_qmmm.get("mode"),
        "pbc": pbc,
        "pbc_qmmm": pbc_qmmm,
        "pass_fail": pass_fail,
        "artifacts": artifacts,
        "artifact_checks": artifact_checks,
        "notes": list(case.notes),
    }


def _write_metrics_csv(metrics: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "case",
        "passed",
        "status",
        "periodicity",
        "kpoint_mode",
        "kpoint_grid",
        "embedding_mode",
        "failed_checks",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in metrics:
            writer.writerow({name: _to_primitive(item.get(name)) for name in fieldnames})


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# PBC/PBC-QMMM Validation",
        "",
        "> Executes the QCchem Gamma-only PBC runner, PBC-QM/MM Ewald workflow, and non-Gamma rejection path.",
        "",
        f"- schema: `{summary['schema']}`",
        f"- profile: `{summary['profile']}`",
        f"- overall_status: `{summary['overall_status']}`",
        f"- cases: `{summary['passed_cases']}/{summary['case_count']}`",
        "",
        "## Acceptance Criteria",
        "",
    ]
    for key, value in summary["acceptance_criteria"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Cases", ""])
    for item in summary["metrics"]:
        lines.extend(
            [
                f"### {item['case']}",
                "",
                f"- passed: `{item['passed']}`",
                f"- status: `{item['status']}`",
                f"- periodicity: `{item.get('periodicity')}`",
                f"- kpoint_grid: `{item.get('kpoint_grid')}`",
                f"- embedding_mode: `{item.get('embedding_mode')}`",
                f"- failed_checks: `{item.get('failed_checks', [])}`",
                f"- notes: `{item.get('notes', [])}`",
                "",
            ]
        )
    return "\n".join(lines)


def run_pbc_qmmm_validation(
    output_dir: Path,
    *,
    profile: str = "smoke",
    cases: list[PBCQMMMValidationCase] | None = None,
) -> dict[str, Any]:
    """Execute PBC/PBC-QM/MM validation cases and write report artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    selected_cases = cases if cases is not None else default_pbc_qmmm_validation_cases(profile=profile)
    metrics = [
        _run_case(case, output_dir / "cases" / case.name)
        for case in selected_cases
    ]
    passed_cases = sum(1 for item in metrics if item["passed"])
    summary = {
        "schema": SCHEMA,
        "profile": profile,
        "case_count": len(metrics),
        "passed_cases": passed_cases,
        "overall_status": "passed" if passed_cases == len(metrics) else "failed",
        "acceptance_criteria": {
            "executes_gamma_pbc": True,
            "executes_pbc_qmmm_ewald": True,
            "rejects_non_gamma_kpoints": True,
            "core_runner_implemented": True,
            "requires_quantum_evidence": True,
            "requires_qcschema_export": True,
        },
        "metrics": metrics,
        "artifacts": {
            "json": str(output_dir / "pbc_qmmm_validation.json"),
            "markdown": str(output_dir / "pbc_qmmm_validation.md"),
            "csv": str(output_dir / "metrics.csv"),
        },
    }
    (output_dir / "pbc_qmmm_validation.json").write_text(
        json.dumps(_to_primitive(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "pbc_qmmm_validation.md").write_text(_render_markdown(summary), encoding="utf-8")
    _write_metrics_csv(metrics, output_dir / "metrics.csv")
    return summary
