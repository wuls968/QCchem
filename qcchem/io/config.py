"""Configuration loading for QCchem run specs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from qcchem.backends.policy import apply_policy_defaults
from qcchem.core import (
    ActiveSpaceSpec,
    ArtifactExportSpec,
    AutoActiveSpaceSpec,
    AnsatzSpec,
    AtomSpec,
    BackendSpec,
    BenchmarkSpec,
    CompressionSpec,
    EmbeddingSpec,
    ExploratorySpec,
    ExcitedStateTaskSpec,
    FragmentSpec,
    MappingSpec,
    MeasurementSpec,
    MitigationSpec,
    MoleculeSpec,
    NoiseModelSpec,
    OptimizerSpec,
    PECSpec,
    PerturbativeCorrectionTaskSpec,
    PolicySpec,
    ProblemSpec,
    PropertyTaskSpec,
    ReadoutMitigationSpec,
    RunConfig,
    RunSpec,
    RuntimeOptionsSpec,
    SolverSpec,
    SymmetryCheckSpec,
    TaskSpec,
    ZNESpec,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_user_path(base_dir: Path, value: str) -> Path:
    """Resolve a user-specified path relative to a base directory or project root."""
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate
    local = (base_dir / candidate).resolve()
    if local.exists():
        return local
    return (_project_root() / candidate).resolve()


def _resolve_path(base_dir: Path, value: str) -> Path:
    candidate = (base_dir / value).resolve()
    if candidate.exists():
        return candidate
    return (_project_root() / value).resolve()


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"Expected '{key}' to be a mapping, got {type(value).__name__}.")
    return value


def _parse_atoms(items: list[dict[str, Any]]) -> list[AtomSpec]:
    atoms: list[AtomSpec] = []
    for item in items:
        if "symbol" not in item or "coords" not in item:
            raise ValueError("Each geometry item must contain 'symbol' and 'coords'.")
        coords = item["coords"]
        if len(coords) != 3:
            raise ValueError("Geometry coordinates must have exactly three values.")
        atoms.append(
            AtomSpec(
                symbol=str(item["symbol"]),
                coords=(float(coords[0]), float(coords[1]), float(coords[2])),
            )
        )
    return atoms


def _parse_active_space(problem_raw: dict[str, Any]) -> ActiveSpaceSpec | None:
    active_space_raw = problem_raw.get("active_space")
    if not isinstance(active_space_raw, dict):
        return None
    auto_raw = active_space_raw.get("auto")
    auto = AutoActiveSpaceSpec()
    if isinstance(auto_raw, dict):
        auto = AutoActiveSpaceSpec(
            enabled=bool(auto_raw.get("enabled", False)),
            strategy=str(auto_raw.get("strategy", "frontier_orbitals")),
            num_occupied=int(auto_raw.get("num_occupied", 1)),
            num_virtual=int(auto_raw.get("num_virtual", 1)),
        )
    return ActiveSpaceSpec(
        num_electrons=active_space_raw.get("num_electrons"),
        num_spatial_orbitals=(
            int(active_space_raw["num_spatial_orbitals"])
            if active_space_raw.get("num_spatial_orbitals") is not None
            else None
        ),
        active_orbitals=active_space_raw.get("active_orbitals"),
        selection_mode=str(active_space_raw.get("selection_mode", "manual")),
        auto=auto,
    )


def _parse_compression(problem_raw: dict[str, Any]) -> CompressionSpec:
    compression_raw = problem_raw.get("compression")
    if not isinstance(compression_raw, dict):
        return CompressionSpec()
    return CompressionSpec(
        enabled=bool(compression_raw.get("enabled", False)),
        method=str(compression_raw.get("method", "modified_cholesky")),
        threshold=float(compression_raw.get("threshold", 1.0e-8)),
        max_rank=(
            int(compression_raw["max_rank"])
            if compression_raw.get("max_rank") is not None
            else None
        ),
        apply_to_solver=bool(compression_raw.get("apply_to_solver", False)),
        execution_enabled=bool(
            compression_raw.get(
                "execution_enabled",
                compression_raw.get("apply_to_solver", False),
            )
        ),
    )


def _parse_measurement(problem_raw: dict[str, Any]) -> MeasurementSpec:
    measurement_raw = problem_raw.get("measurement")
    if not isinstance(measurement_raw, dict):
        return MeasurementSpec()
    return MeasurementSpec(
        strategy=str(measurement_raw.get("strategy", "default")),
        runtime_precision_target=(
            float(measurement_raw["runtime_precision_target"])
            if measurement_raw.get("runtime_precision_target") is not None
            else None
        ),
        execution_mode=str(measurement_raw.get("execution_mode", "estimator")),
        grouping_policy=str(measurement_raw.get("grouping_policy", "default")),
    )


def _parse_embedding(problem_raw: dict[str, Any]) -> EmbeddingSpec:
    embedding_raw = problem_raw.get("embedding")
    if not isinstance(embedding_raw, dict):
        return EmbeddingSpec()
    fragments_raw = embedding_raw.get("fragments", [])
    fragments = []
    if not isinstance(fragments_raw, list):
        raise ValueError("problem.embedding.fragments must be a list.")
    for item in fragments_raw:
        if not isinstance(item, dict):
            raise ValueError("Each fragment entry must be a mapping.")
        fragments.append(
            FragmentSpec(
                name=str(item["name"]),
                atom_indices=[int(value) for value in item.get("atom_indices", [])],
            )
        )
    return EmbeddingSpec(
        enabled=bool(embedding_raw.get("enabled", False)),
        method=str(embedding_raw.get("method", "dmet_skeleton")),
        bath_threshold=float(embedding_raw.get("bath_threshold", 0.05)),
        solver_plugin=str(embedding_raw.get("solver_plugin", "placeholder_fragment_solver")),
        fragments=fragments,
    )


def _parse_property_tasks(tasks_raw: dict[str, Any]) -> list[PropertyTaskSpec]:
    properties_raw = tasks_raw.get("properties", [])
    if not isinstance(properties_raw, list):
        raise ValueError("tasks.properties must be a list.")
    parsed: list[PropertyTaskSpec] = []
    for item in properties_raw:
        if not isinstance(item, dict):
            raise ValueError("Each property task must be a mapping.")
        parsed.append(
            PropertyTaskSpec(
                property_name=str(item["property_name"]),
                enabled=bool(item.get("enabled", True)),
                method=str(item.get("method", "exact_expectation")),
                state_indices=[int(value) for value in item.get("state_indices", [0])],
            )
        )
    return parsed


def _parse_perturbative_correction(tasks_raw: dict[str, Any]) -> PerturbativeCorrectionTaskSpec:
    raw = tasks_raw.get("perturbative_correction")
    if not isinstance(raw, dict):
        return PerturbativeCorrectionTaskSpec()
    return PerturbativeCorrectionTaskSpec(
        enabled=bool(raw.get("enabled", False)),
        method=str(raw.get("method", "nevpt2")),
        plugin=str(raw.get("plugin", "pyscf")),
        root=int(raw.get("root", 0)),
    )


def _parse_noise_spec(backend_raw: dict[str, Any]) -> NoiseModelSpec:
    noise_raw = backend_raw.get("noise")
    if not isinstance(noise_raw, dict):
        return NoiseModelSpec()
    return NoiseModelSpec(
        enabled=bool(noise_raw.get("enabled", False)),
        profile=str(noise_raw.get("profile", "none")),
        depolarizing_probability_1q=float(noise_raw.get("depolarizing_probability_1q", 0.0)),
        depolarizing_probability_2q=float(noise_raw.get("depolarizing_probability_2q", 0.0)),
        readout_error_probability=float(noise_raw.get("readout_error_probability", 0.0)),
        basis_gates=[str(item) for item in noise_raw.get("basis_gates", [])],
    )


def _parse_runtime_options(backend_raw: dict[str, Any]) -> RuntimeOptionsSpec:
    runtime_raw = backend_raw.get("runtime")
    if not isinstance(runtime_raw, dict):
        return RuntimeOptionsSpec()
    return RuntimeOptionsSpec(
        enabled=bool(runtime_raw.get("enabled", False)),
        service=str(runtime_raw.get("service", "local")),
        instance=(str(runtime_raw["instance"]) if runtime_raw.get("instance") is not None else None),
        runtime_ready=bool(runtime_raw.get("runtime_ready", False)),
        session_ready=bool(runtime_raw.get("session_ready", False)),
        batch_ready=bool(runtime_raw.get("batch_ready", False)),
        precision_target=(
            float(runtime_raw["precision_target"])
            if runtime_raw.get("precision_target") is not None
            else None
        ),
        max_budgeted_shots=(
            int(runtime_raw["max_budgeted_shots"])
            if runtime_raw.get("max_budgeted_shots") is not None
            else None
        ),
        max_execution_seconds=(
            float(runtime_raw["max_execution_seconds"])
            if runtime_raw.get("max_execution_seconds") is not None
            else None
        ),
        calibration_strategy=str(runtime_raw.get("calibration_strategy", "default")),
        resilience_level=(
            int(runtime_raw["resilience_level"])
            if runtime_raw.get("resilience_level") is not None
            else None
        ),
        grouping_policy=str(runtime_raw.get("grouping_policy", "default")),
        options=dict(runtime_raw.get("options", {})),
    )


def _parse_artifact_exports(run_raw: dict[str, Any]) -> ArtifactExportSpec:
    exports_raw = run_raw.get("exports")
    if not isinstance(exports_raw, dict):
        return ArtifactExportSpec()
    return ArtifactExportSpec(
        qcschema_json=bool(exports_raw.get("qcschema_json", False)),
        hdf5=bool(exports_raw.get("hdf5", False)),
    )


def load_run_spec(path: Path) -> RunSpec:
    """Load a QCchem run specification from YAML."""
    resolved_path = path if path.is_absolute() else _resolve_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Run configuration must deserialize to a mapping.")

    base_dir = resolved_path.parent
    molecule_raw = _require_mapping(raw, "molecule")
    geometry_raw = molecule_raw.get("geometry", [])
    if not isinstance(geometry_raw, list) or not geometry_raw:
        raise ValueError("Molecule geometry must be a non-empty list.")

    policy_raw = _require_mapping(raw, "policy")
    policy_name = str(policy_raw.get("name", "benchmark"))
    exploratory_raw = _require_mapping(raw, "exploratory")

    problem_raw = _require_mapping(raw, "problem")
    solver_raw = _require_mapping(raw, "solver")
    optimizer_raw = _require_mapping(solver_raw, "optimizer")
    ansatz_raw = _require_mapping(solver_raw, "ansatz")
    benchmark_raw = _require_mapping(raw, "benchmark")
    mitigation_raw = _require_mapping(raw, "mitigation")
    backend_raw = _require_mapping(raw, "backend")
    backend_raw, benchmark_raw, mitigation_raw = apply_policy_defaults(
        policy_name,
        backend_raw,
        benchmark_raw,
        mitigation_raw,
    )

    symmetry_raw = _require_mapping(mitigation_raw, "symmetry_check")
    readout_raw = _require_mapping(mitigation_raw, "readout")
    zne_raw = _require_mapping(mitigation_raw, "zne")
    pec_raw = _require_mapping(mitigation_raw, "pec")
    tasks_raw = _require_mapping(raw, "tasks")
    excited_raw = _require_mapping(tasks_raw, "excited_state")
    run_raw = _require_mapping(raw, "run")

    return RunSpec(
        molecule=MoleculeSpec(
            name=str(molecule_raw["name"]),
            geometry=_parse_atoms(geometry_raw),
            charge=int(molecule_raw.get("charge", 0)),
            multiplicity=int(molecule_raw.get("multiplicity", 1)),
            basis=str(molecule_raw.get("basis", "sto3g")),
            unit=str(molecule_raw.get("unit", "angstrom")),
        ),
        problem=ProblemSpec(
            active_space=_parse_active_space(problem_raw),
            freeze_core=bool(problem_raw.get("freeze_core", False)),
            remove_orbitals=[int(value) for value in problem_raw.get("remove_orbitals", [])],
            compression=_parse_compression(problem_raw),
            measurement=_parse_measurement(problem_raw),
            embedding=_parse_embedding(problem_raw),
        ),
        mapping=MappingSpec(kind=str(_require_mapping(raw, "mapping").get("kind", "jordan_wigner"))),
        backend=BackendSpec(
            kind=str(backend_raw.get("kind", "statevector")),
            shots=int(backend_raw["shots"]) if backend_raw.get("shots") is not None else None,
            precision=float(backend_raw["precision"]) if backend_raw.get("precision") is not None else None,
            seed=int(backend_raw["seed"]) if backend_raw.get("seed") is not None else None,
            repetitions=int(backend_raw.get("repetitions", 1)),
            abelian_grouping=bool(backend_raw.get("abelian_grouping", True)),
            noise=_parse_noise_spec(backend_raw),
            runtime=_parse_runtime_options(backend_raw),
        ),
        solver=SolverSpec(
            kind=str(solver_raw.get("kind", "vqe")),
            optimizer=OptimizerSpec(
                kind=str(optimizer_raw.get("kind", "COBYLA")),
                maxiter=int(optimizer_raw.get("maxiter", 100)),
                tol=float(optimizer_raw["tol"]) if optimizer_raw.get("tol") is not None else None,
            ),
            ansatz=AnsatzSpec(
                kind=str(ansatz_raw.get("kind", "twolocal")),
                rotation_blocks=[str(item) for item in ansatz_raw.get("rotation_blocks", ["ry", "rz"])],
                entanglement_blocks=str(ansatz_raw.get("entanglement_blocks", "cz")),
                entanglement=str(ansatz_raw.get("entanglement", "full")),
                reps=int(ansatz_raw.get("reps", 2)),
                skip_final_rotation_layer=bool(ansatz_raw.get("skip_final_rotation_layer", False)),
            ),
            initial_point=solver_raw.get("initial_point", "zeros"),
            experimental=bool(solver_raw.get("experimental", False)),
        ),
        benchmark=BenchmarkSpec(
            enabled=bool(benchmark_raw.get("enabled", True)),
            exact_baseline_qubit_limit=int(benchmark_raw.get("exact_baseline_qubit_limit", 12)),
            absolute_error_threshold=float(benchmark_raw.get("absolute_error_threshold", 1.0e-3)),
            relative_error_threshold=float(benchmark_raw.get("relative_error_threshold", 1.0e-3)),
        ),
        mitigation=MitigationSpec(
            symmetry_check=SymmetryCheckSpec(
                enabled=bool(symmetry_raw.get("enabled", False)),
                strategy=str(symmetry_raw.get("strategy", "placeholder")),
            ),
            readout=ReadoutMitigationSpec(
                enabled=bool(readout_raw.get("enabled", False)),
                method=str(readout_raw.get("method", "none")),
            ),
            zne=ZNESpec(
                enabled=bool(zne_raw.get("enabled", False)),
                method=str(zne_raw.get("method", "placeholder")),
            ),
            pec=PECSpec(
                enabled=bool(pec_raw.get("enabled", False)),
                method=str(pec_raw.get("method", "placeholder")),
            ),
            experimental=bool(mitigation_raw.get("experimental", False)),
        ),
        policy=PolicySpec(
            name=policy_name,
            allow_exploratory=bool(policy_raw.get("allow_exploratory", False)),
        ),
        exploratory=ExploratorySpec(
            enabled=bool(exploratory_raw.get("enabled", False)),
            modules=[str(item) for item in exploratory_raw.get("modules", [])],
            notes=[str(item) for item in exploratory_raw.get("notes", [])],
        ),
        tasks=TaskSpec(
            excited_state=ExcitedStateTaskSpec(
                enabled=bool(excited_raw.get("enabled", False)),
                method=str(excited_raw.get("method", "exact_spectrum")),
                num_states=int(excited_raw.get("num_states", 2)),
                state_indices=[int(value) for value in excited_raw.get("state_indices", [1])],
            ),
            properties=_parse_property_tasks(tasks_raw),
            perturbative_correction=_parse_perturbative_correction(tasks_raw),
        ),
        run=RunConfig(
            seed=int(run_raw.get("seed", 7)),
            output_dir=Path(run_raw.get("output_dir", "artifacts")),
            overwrite=bool(run_raw.get("overwrite", False)),
            exports=_parse_artifact_exports(run_raw),
        ),
    )
