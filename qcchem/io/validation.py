"""Early validation shared by YAML loading and direct Python execution."""

from __future__ import annotations

import math
from dataclasses import fields
from typing import Union, get_args, get_origin, get_type_hints
from types import UnionType

from qcchem.core import specs


def validate_run_mapping(raw: dict) -> None:
    """Reject typos and coerced scalar types in the public execution contract."""
    schemas = {
        "": specs.RunSpec, "molecule": specs.MoleculeSpec, "problem": specs.ProblemSpec,
        "mapping": specs.MappingSpec, "mapping.symmetry_reduction": specs.MappingSymmetryReductionSpec,
        "backend": specs.BackendSpec, "backend.noise": specs.NoiseModelSpec,
        "backend.runtime": specs.RuntimeOptionsSpec, "solver": specs.SolverSpec,
        "solver.optimizer": specs.OptimizerSpec, "solver.ansatz": specs.AnsatzSpec,
        "solver.lr_ace": specs.LRACESpec, "solver.lr_ace_adaptive": specs.LRACEAdaptiveSpec,
        "benchmark": specs.BenchmarkSpec, "run": specs.RunConfig,
        "run.exports": specs.ArtifactExportSpec, "policy": specs.PolicySpec,
        "exploratory": specs.ExploratorySpec, "tasks": specs.TaskSpec,
        "tasks.excited_state": specs.ExcitedStateTaskSpec,
    }
    for path, schema in schemas.items():
        value = raw
        for key in path.split(".") if path else []:
            value = value.get(key, {}) if isinstance(value, dict) else None
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ValueError(f"{path or 'run configuration'} must be a mapping.")
        allowed = {item.name for item in fields(schema)}
        if path == "molecule":
            allowed |= {"structure_file", "structure_format"}
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"Unknown configuration key(s) in {path or 'root'}: {', '.join(sorted(unknown))}.")
        for key, annotation in get_type_hints(schema).items():
            if key not in value or value[key] is None:
                continue
            item = value[key]
            choices = get_args(annotation) if get_origin(annotation) in {Union, UnionType} else (annotation,)
            label = f"{path}.{key}".lstrip(".")
            if annotation is bool and type(item) is not bool:
                raise ValueError(f"{label} must be a boolean, not {item!r}.")
            if int in choices and float not in choices and type(item) is not int:
                raise ValueError(f"{label} must be an integer.")
            if float in choices and (isinstance(item, bool) or not isinstance(item, (int, float))):
                raise ValueError(f"{label} must be a number.")
            if get_origin(annotation) is list and get_args(annotation) == (int,):
                if not isinstance(item, list) or any(type(index) is not int for index in item):
                    raise ValueError(f"{label} must be a list of integers.")
    _validate_finite(raw)
    properties = (raw.get("tasks") or {}).get("properties") or []
    if not isinstance(properties, list):
        raise ValueError("tasks.properties must be a list of property tasks.")
    for item in properties:
        if not isinstance(item, dict):
            raise ValueError("Each property task must be a mapping.")
        unknown = set(item) - {field.name for field in fields(specs.PropertyTaskSpec)}
        if unknown:
            raise ValueError(f"Unknown property task key(s): {', '.join(sorted(unknown))}.")
        if "enabled" in item and type(item["enabled"]) is not bool:
            raise ValueError("Property task enabled must be a boolean.")
        indices = item.get("state_indices", [0])
        if not isinstance(indices, list) or any(type(index) is not int or index < 0 for index in indices):
            raise ValueError("Property task state_indices must be non-negative integers.")


def _validate_finite(value, path: str = "configuration") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_finite(item, f"{path}[{index}]")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} must be finite.")


def validate_run_spec(spec):
    """Validate execution-sensitive values before opening output files."""
    from qcchem.exploratory.solvers.registry import EXPLORATORY_SOLVERS
    from qcchem.io.serialization import to_primitive

    validate_run_mapping(to_primitive(spec))
    choices = {
        "mapping.kind": (spec.mapping.kind, {"jordan_wigner", "bravyi_kitaev", "parity_two_qubit_reduction"}),
        "backend.kind": (spec.backend.kind, {"statevector", "shot_estimator", "aer_shot_estimator", "cudaq_statevector", "cudaq_sample"}),
        "solver.kind": (spec.solver.kind, {"exact", "reference", "vqe", "lr_ace", "qft_dynamics_audit", *EXPLORATORY_SOLVERS}),
        "molecule.unit": (spec.molecule.unit, {"angstrom", "bohr"}),
        "solver.optimizer.kind": (spec.solver.optimizer.kind, {"cobyla", "slsqp", "l-bfgs-b", "bfgs", "nelder-mead", "powell", "cg", "cobyqa", "tnc", "trust-constr"}),
    }
    for label, (value, allowed) in choices.items():
        if str(value).strip().lower() not in allowed:
            raise ValueError(f"Unsupported {label}: {value!r}; expected {', '.join(sorted(allowed))}.")
    positive = {
        "molecule.multiplicity": spec.molecule.multiplicity,
        "backend.repetitions": spec.backend.repetitions,
        "solver.optimizer.maxiter": spec.solver.optimizer.maxiter,
        "tasks.excited_state.num_states": spec.tasks.excited_state.num_states,
    }
    optional_positive = {
        "backend.shots": spec.backend.shots, "backend.precision": spec.backend.precision,
        "solver.optimizer.tol": spec.solver.optimizer.tol,
        "backend.runtime.max_budgeted_shots": spec.backend.runtime.max_budgeted_shots,
        "backend.runtime.max_execution_seconds": spec.backend.runtime.max_execution_seconds,
        "backend.runtime.precision_target": spec.backend.runtime.precision_target,
    }
    positive.update({key: value for key, value in optional_positive.items() if value is not None})
    for label, value in positive.items():
        if isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be positive.")
    for label, value in {
        "benchmark.exact_baseline_qubit_limit": spec.benchmark.exact_baseline_qubit_limit,
        "benchmark.absolute_error_threshold": spec.benchmark.absolute_error_threshold,
        "benchmark.relative_error_threshold": spec.benchmark.relative_error_threshold,
        "solver.ansatz.reps": spec.solver.ansatz.reps,
    }.items():
        if value < 0:
            raise ValueError(f"{label} must be non-negative.")
    for key in ("depolarizing_probability_1q", "depolarizing_probability_2q", "readout_error_probability"):
        if not 0 <= getattr(spec.backend.noise, key) <= 1:
            raise ValueError(f"backend.noise.{key} must be between 0 and 1.")
    for task in [spec.tasks.excited_state, *spec.tasks.properties]:
        if any(type(index) is not int or index < 0 for index in task.state_indices):
            raise ValueError("Task state_indices must contain non-negative integers.")
    if spec.problem.qft.enabled and spec.problem.cavity_qed.enabled:
        raise ValueError("Enable either problem.qft or problem.cavity_qed, not both.")
    return spec
