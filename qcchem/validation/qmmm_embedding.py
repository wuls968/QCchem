"""Closed-loop validation harness for QM/MM-like environment embedding."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from qcchem.chem.effective_hamiltonian import resolve_environment_inputs
from qcchem.chem.external_charges import pyscf_qmmm_nuclear_interaction_energy
from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.workflow.runner import run_from_config


FORMULA_TOLERANCE_HARTREE = 1.0e-10
PYSCF_NUCLEAR_TOLERANCE_HARTREE = 1.0e-10
HERMITICITY_TOLERANCE = 1.0e-12
CACHE_RELOAD_TOLERANCE = 1.0e-12


@dataclass(slots=True)
class QMMMValidationCase:
    """One QM/MM embedding validation case."""

    name: str
    config: dict[str, Any]
    exploratory_command: bool = False
    repeat_for_cache: bool = True
    expected_environment_qubit_growth: int = 0
    notes: list[str] = field(default_factory=list)


def _h2_molecule(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "geometry": [
            {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
            {"symbol": "H", "coords": [0.0, 0.0, 0.735]},
        ],
        "charge": 0,
        "multiplicity": 1,
        "basis": "sto3g",
        "unit": "angstrom",
    }


def _h2_environment_problem(
    *,
    charge: float = -0.5,
    distance: float = 2.0,
    radius: float = 0.4,
    boundary: bool = False,
    cache_dir: str = "cache",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "environment_embedding": {
            "enabled": True,
            "mode": "effective_hamiltonian",
            "point_charges": {
                "enabled": True,
                "unit": "angstrom",
                "charges": [
                    {
                        "label": "mm_probe",
                        "coords": [0.0, 0.0, distance],
                        "charge": charge,
                    }
                ],
                "damping": {
                    "kind": "gaussian",
                    "default_radius": radius,
                    "radius_unit": "angstrom",
                    "min_radius": 0.15,
                    "overpolarization_warning_potential_au": 2.0,
                },
            },
            "boundary": {
                "enabled": boundary,
                "cut_bonds": (
                    [{"label": "H0-MM", "qm_atom": 0, "mm_atom": 10}]
                    if boundary
                    else []
                ),
                "leakage_threshold": 1.0,
                "strict": False,
            },
            "cache": {
                "enabled": True,
                "directory": cache_dir,
                "refresh": False,
            },
        }
    }
    return payload


def _base_run_config(*, name: str, problem: dict[str, Any], solver: str = "exact") -> dict[str, Any]:
    return {
        "molecule": _h2_molecule(name),
        "problem": problem,
        "mapping": {"kind": "jordan_wigner"},
        "backend": {"kind": "statevector"},
        "solver": {"kind": solver},
        "benchmark": {
            "enabled": True,
            "exact_baseline_qubit_limit": 12,
            "absolute_error_threshold": 1.0e-8,
            "relative_error_threshold": 1.0e-8,
        },
        "run": {
            "seed": 17,
            "output_dir": "run",
            "overwrite": True,
            "exports": {"qcschema_json": True},
        },
    }


def _legacy_external_config() -> dict[str, Any]:
    return _base_run_config(
        name="H2-qmmm-legacy",
        problem={
            "external_point_charges": {
                "enabled": True,
                "unit": "angstrom",
                "charges": [
                    {
                        "label": "legacy_probe",
                        "coords": [0.0, 0.0, 2.0],
                        "charge": -0.5,
                    }
                ],
            }
        },
    )


def _tc_qsci_config(cache_dir: str) -> dict[str, Any]:
    config = _base_run_config(
        name="H2-qmmm-tc-qsci",
        problem=_h2_environment_problem(cache_dir=cache_dir),
    )
    config["policy"] = {"allow_exploratory": True}
    config["exploratory"] = {"enabled": True, "modules": ["tc_qsci"]}
    config["tc_qsci"] = {
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
        "resource_estimation": {"enabled": True, "target_precision": 1.0e-3},
    }
    return config


def _compression_config(cache_dir: str) -> dict[str, Any]:
    problem = _h2_environment_problem(cache_dir=cache_dir)
    problem["compression"] = {
        "enabled": True,
        "method": "modified_cholesky",
        "threshold": 1.0e-10,
        "max_rank": 4,
        "apply_to_solver": True,
        "execution_enabled": True,
    }
    return _base_run_config(name="H2-qmmm-compressed", problem=problem)


def _active_space_config(cache_dir: str) -> dict[str, Any]:
    problem = _h2_environment_problem(cache_dir=cache_dir)
    problem["active_space"] = {
        "num_electrons": 2,
        "num_spatial_orbitals": 1,
    }
    return _base_run_config(name="H2-qmmm-active-space", problem=problem)


def _cavity_config(cache_dir: str) -> dict[str, Any]:
    config = _base_run_config(
        name="H2-qmmm-cavity",
        problem=_h2_environment_problem(cache_dir=cache_dir),
    )
    config["policy"] = {"allow_exploratory": True}
    config["exploratory"] = {"enabled": True, "modules": ["cavity_qed"]}
    config["problem"]["cavity_qed"] = {
        "enabled": True,
        "modes": [
            {
                "frequency": 0.4,
                "coupling_strength": 0.02,
                "polarization": [0.0, 0.0, 1.0],
                "max_occupation": 1,
            }
        ],
    }
    return config


def _lr_ace_config(cache_dir: str) -> dict[str, Any]:
    config = _compression_config(cache_dir)
    config["molecule"]["name"] = "H2-qmmm-lr-ace"
    config["policy"] = {"allow_exploratory": True}
    config["exploratory"] = {"enabled": True, "modules": ["lr_ace"]}
    config["mapping"] = {"kind": "parity_two_qubit_reduction"}
    config["solver"] = {
        "kind": "lr_ace",
        "experimental": True,
        "optimizer": {"kind": "COBYLA", "maxiter": 40},
        "ansatz": {"kind": "lr_ace", "reps": 1},
        "initial_point": "zeros",
    }
    config["benchmark"]["absolute_error_threshold"] = 1.6e-3
    config["benchmark"]["relative_error_threshold"] = 1.6e-3
    return config


def default_qmmm_validation_cases(*, profile: str = "smoke") -> list[QMMMValidationCase]:
    """Return the built-in QM/MM validation cases."""
    profile = profile.strip().lower()
    cases = [
        QMMMValidationCase(
            name="h2_damped_exact_radius_0p40",
            config=_base_run_config(
                name="H2-qmmm-damped",
                problem=_h2_environment_problem(cache_dir="cache"),
            ),
            notes=["Baseline damped H2 exact embedding case."],
        ),
        QMMMValidationCase(
            name="h2_boundary_diagnostic",
            config=_base_run_config(
                name="H2-qmmm-boundary",
                problem=_h2_environment_problem(boundary=True, cache_dir="cache"),
            ),
            notes=["Non-strict boundary leakage diagnostic case."],
        ),
        QMMMValidationCase(
            name="h2_legacy_alias",
            config=_legacy_external_config(),
            repeat_for_cache=False,
            notes=["Legacy external_point_charges compatibility case."],
        ),
    ]
    if profile == "smoke":
        return cases
    if profile != "full":
        raise ValueError("QMMM validation profile must be smoke or full.")
    cases.extend(
        [
            QMMMValidationCase(
                name="h2_damped_scan_close_charge",
                config=_base_run_config(
                    name="H2-qmmm-close-damped",
                    problem=_h2_environment_problem(
                        charge=-0.75,
                        distance=1.5,
                        radius=0.55,
                        cache_dir="cache",
                    ),
                ),
                notes=["Charge/distance/radius scan case for overpolarization risk checks."],
            ),
            QMMMValidationCase(
                name="h2_tc_qsci_environment",
                config=_tc_qsci_config("cache"),
                exploratory_command=True,
                notes=["TC-QSCI consumes the same embedded physical Hamiltonian."],
            ),
            QMMMValidationCase(
                name="h2_active_space_environment",
                config=_active_space_config("cache"),
                notes=["Active-space projection keeps environment-induced qubit growth at zero."],
            ),
            QMMMValidationCase(
                name="h2_compression_environment",
                config=_compression_config("cache"),
                notes=["Compression consumes the same embedded Hamiltonian convention."],
            ),
            QMMMValidationCase(
                name="h2_cavity_environment",
                config=_cavity_config("cache"),
                exploratory_command=True,
                notes=["Cavity-QED inherits the embedded electronic Hamiltonian."],
            ),
            QMMMValidationCase(
                name="h2_lr_ace_environment",
                config=_lr_ace_config("cache"),
                exploratory_command=True,
                notes=["LR-ACE consumes the embedded/compressed Hamiltonian surface."],
            ),
        ]
    )
    return cases


def _write_case_config(case: QMMMValidationCase, case_dir: Path) -> Path:
    config = json.loads(json.dumps(case.config))
    env = (config.get("problem") or {}).get("environment_embedding")
    if isinstance(env, dict):
        cache = env.setdefault("cache", {})
        if cache.get("enabled", True):
            cache["directory"] = str(case_dir / str(cache.get("directory", "cache")))
    config_path = case_dir / f"{case.name}.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def _formula_closure_error(result: Any) -> float:
    energy = result.energy
    return abs(
        float(energy.total_energy)
        - (
            float(energy.solver_energy)
            + float(energy.constant_energy_correction)
            + float(energy.nuclear_repulsion_energy)
            + float(energy.external_point_charge_nuclear_interaction_energy)
            + float(energy.boundary_embedding_constant_energy)
        )
    )


def _pyscf_nuclear_delta_error(config_path: Path, result: Any) -> float:
    spec = load_run_spec(config_path)
    env_inputs = resolve_environment_inputs(spec)
    point_charges = env_inputs.point_charges
    if not point_charges.enabled:
        return 0.0
    reference = pyscf_qmmm_nuclear_interaction_energy(
        spec.molecule,
        point_charges.charges,
        charge_unit=point_charges.unit,
        radii=point_charges.radii,
    )
    return abs(float(result.energy.external_point_charge_nuclear_interaction_energy) - reference)


def _qcschema_has_embedding(result: Any) -> bool:
    path = result.artifacts.qcschema_json
    if path is None or not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    extras = payload.get("extras") or {}
    return bool(extras.get("environment_embedding"))


def _report_has_embedding(result: Any) -> bool:
    path = result.artifacts.report_markdown
    return path.exists() and "Environment Effective Hamiltonian" in path.read_text(
        encoding="utf-8"
    )


def _case_metrics(
    *,
    case: QMMMValidationCase,
    config_path: Path,
    first_result: Any,
    second_result: Any | None,
) -> dict[str, Any]:
    result = second_result or first_result
    embedding = result.environment_embedding
    external = result.external_point_charges
    one_body = embedding.one_body_environment if embedding is not None else {}
    cache_validation = embedding.cache_validation if embedding is not None else {}
    boundary = embedding.boundary if embedding is not None else None
    formula_error = _formula_closure_error(result)
    nuclear_error = _pyscf_nuclear_delta_error(config_path, result)
    hermitian_deviation = float(one_body.get("hermitian_deviation") or 0.0)
    cache_reload_error = cache_validation.get("reload_matrix_error")
    if cache_reload_error is None:
        cache_reload_error = 0.0
    environment_growth = (
        int((embedding.active_space_projection or {}).get("environment_qubit_growth", -1))
        if embedding is not None
        else -1
    )
    cache_hit = bool(embedding.cache_hit) if embedding is not None else False
    cache_validated = bool(cache_validation.get("validated", False))
    legacy_alias = (
        external is not None
        and (external.provenance or {}).get("compatibility_mode")
        == "external_point_charges_compatibility_alias"
    )
    risk_notes = list(embedding.risk_notes if embedding is not None else [])
    pass_fail = {
        "formula_closure": formula_error < FORMULA_TOLERANCE_HARTREE,
        "pyscf_nuclear_delta": nuclear_error < PYSCF_NUCLEAR_TOLERANCE_HARTREE,
        "hcore_hermiticity": hermitian_deviation < HERMITICITY_TOLERANCE,
        "cache_reload": (
            True
            if not case.repeat_for_cache
            else cache_hit and cache_validated and float(cache_reload_error) < CACHE_RELOAD_TOLERANCE
        ),
        "qubit_growth": environment_growth == case.expected_environment_qubit_growth,
        "qcschema_embedding": _qcschema_has_embedding(result),
        "report_embedding": _report_has_embedding(result),
        "risk_notes": bool(risk_notes),
    }
    metrics = {
        "case": case.name,
        "formula_closure_error_hartree": formula_error,
        "pyscf_nuclear_delta_error_hartree": nuclear_error,
        "hcore_hermiticity_deviation": hermitian_deviation,
        "cache_reload_matrix_error": float(cache_reload_error),
        "cache_hit": cache_hit,
        "cache_validated": cache_validated,
        "environment_qubit_growth": environment_growth,
        "qcschema_has_environment_embedding": _qcschema_has_embedding(result),
        "report_has_environment_embedding": _report_has_embedding(result),
        "legacy_alias": legacy_alias,
        "boundary_enabled": bool(boundary.enabled) if boundary is not None else False,
        "boundary_max_leakage": (
            boundary.max_boundary_leakage if boundary is not None else None
        ),
        "pass_fail": pass_fail,
        "passed": all(pass_fail.values()),
        "notes": list(case.notes),
    }
    if not metrics["passed"]:
        metrics["recommendation"] = _recommendation(pass_fail)
    else:
        metrics["recommendation"] = "No optimization required; all trust-first gates passed."
    return metrics


def _recommendation(pass_fail: dict[str, bool]) -> str:
    failed = [name for name, passed in pass_fail.items() if not passed]
    if not failed:
        return "No optimization required."
    priority = [
        "formula_closure",
        "pyscf_nuclear_delta",
        "hcore_hermiticity",
        "cache_reload",
        "qubit_growth",
        "risk_notes",
        "qcschema_embedding",
        "report_embedding",
    ]
    first = next((name for name in priority if name in failed), failed[0])
    return f"Optimize the {first} gate before changing lower-priority behavior."


def _write_metrics_csv(metrics: list[dict[str, Any]], path: Path) -> None:
    columns = [
        "case",
        "passed",
        "formula_closure_error_hartree",
        "pyscf_nuclear_delta_error_hartree",
        "hcore_hermiticity_deviation",
        "cache_reload_matrix_error",
        "cache_hit",
        "cache_validated",
        "environment_qubit_growth",
        "qcschema_has_environment_embedding",
        "report_has_environment_embedding",
        "legacy_alias",
        "boundary_enabled",
        "boundary_max_leakage",
        "recommendation",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for item in metrics:
            writer.writerow({column: item.get(column) for column in columns})


def _write_markdown_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# QMMM Environment Embedding Validation",
        "",
        f"- Profile: `{summary['profile']}`",
        f"- Overall status: `{summary['overall_status']}`",
        f"- Passed cases: `{summary['passed_cases']}/{summary['case_count']}`",
        "",
        "## Acceptance Criteria",
        "",
        f"- Formula closure: `< {FORMULA_TOLERANCE_HARTREE}` Hartree",
        f"- PySCF nuclear delta: `< {PYSCF_NUCLEAR_TOLERANCE_HARTREE}` Hartree",
        f"- Hcore hermiticity: `< {HERMITICITY_TOLERANCE}`",
        f"- Cache reload matrix equality: `< {CACHE_RELOAD_TOLERANCE}`",
        "- Environment-induced qubit growth: `0`",
        "",
        "## Case Metrics",
        "",
        "| case | passed | formula error | PySCF delta error | hcore hermiticity | cache reload | recommendation |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in summary["metrics"]:
        lines.append(
            "| {case} | {passed} | {formula:.3e} | {nuclear:.3e} | {herm:.3e} | {cache:.3e} | {rec} |".format(
                case=item["case"],
                passed=item["passed"],
                formula=float(item["formula_closure_error_hartree"]),
                nuclear=float(item["pyscf_nuclear_delta_error_hartree"]),
                herm=float(item["hcore_hermiticity_deviation"]),
                cache=float(item["cache_reload_matrix_error"]),
                rec=item["recommendation"],
            )
        )
    lines.extend(
        [
            "",
            "## Optimization Rule",
            "",
            "Only change the embedding algorithm when a trust gate fails or a metric exposes weak evidence. Prioritize physics and reproducibility before speed.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_qmmm_embedding_validation(
    output_dir: Path,
    *,
    profile: str = "smoke",
    cases: list[QMMMValidationCase] | None = None,
) -> dict[str, Any]:
    """Run the QM/MM environment embedding validation loop and write artifacts."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_cases = cases if cases is not None else default_qmmm_validation_cases(profile=profile)
    metrics: list[dict[str, Any]] = []
    for case in selected_cases:
        case_dir = output_dir / case.name
        case_dir.mkdir(parents=True, exist_ok=True)
        config_path = _write_case_config(case, case_dir)
        first_result = run_from_config(
            config_path,
            output_dir=case_dir / "run_1",
            exploratory_command=case.exploratory_command,
        )
        second_result = None
        if case.repeat_for_cache and first_result.environment_embedding is not None:
            second_result = run_from_config(
                config_path,
                output_dir=case_dir / "run_2",
                exploratory_command=case.exploratory_command,
            )
        metrics.append(
            _case_metrics(
                case=case,
                config_path=config_path,
                first_result=first_result,
                second_result=second_result,
            )
        )
    passed_cases = sum(1 for item in metrics if item["passed"])
    summary = {
        "schema": "qcchem.qmmm_validation.v1",
        "profile": profile,
        "case_count": len(metrics),
        "passed_cases": passed_cases,
        "overall_status": "passed" if passed_cases == len(metrics) else "failed",
        "acceptance_criteria": {
            "formula_closure_hartree": FORMULA_TOLERANCE_HARTREE,
            "pyscf_nuclear_delta_hartree": PYSCF_NUCLEAR_TOLERANCE_HARTREE,
            "hcore_hermiticity_deviation": HERMITICITY_TOLERANCE,
            "cache_reload_matrix_error": CACHE_RELOAD_TOLERANCE,
            "environment_qubit_growth": 0,
        },
        "metrics": metrics,
        "artifacts": {
            "json": str(output_dir / "qmmm_validation.json"),
            "markdown": str(output_dir / "qmmm_validation.md"),
            "csv": str(output_dir / "metrics.csv"),
        },
    }
    (output_dir / "qmmm_validation.json").write_text(
        json.dumps(to_primitive(summary), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_metrics_csv(metrics, output_dir / "metrics.csv")
    _write_markdown_report(summary, output_dir / "qmmm_validation.md")
    return summary
