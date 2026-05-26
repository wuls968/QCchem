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
    BoundaryCutBondSpec,
    BoundaryEmbeddingSpec,
    CavityQEDModeSpec,
    CavityQEDSpec,
    CompressionSpec,
    ContinuitySpec,
    EmbeddingSpec,
    EmbeddingExecutionSpec,
    EffectiveHamiltonianCacheSpec,
    EnvironmentEmbeddingSpec,
    EnvironmentPointChargeSpec,
    ExploratorySpec,
    ExternalPointChargeSpec,
    ExcitedStateTaskSpec,
    FragmentSpec,
    GeometryOptimizationTaskSpec,
    GradientTaskSpec,
    HardwareOptimizationSpec,
    LatticeQEDAnsatzSpec,
    LatticeQEDConstraintSpec,
    LatticeQEDDynamicsEvolutionSpec,
    LatticeQEDDynamicsInitialStateSpec,
    LatticeQEDDynamicsRuntimeSpec,
    LatticeQEDDynamicsSpec,
    LatticeQEDDynamicsTimeGridSpec,
    LatticeQEDEngineSpec,
    LatticeQEDGaugeSpec,
    LatticeQEDGridSpec,
    LatticeQEDMatterSpec,
    LatticeQEDSpec,
    LRACEAdaptiveSpec,
    MappingSpec,
    MappingSymmetryReductionSpec,
    MeasurementSpec,
    MitigationSpec,
    MoleculeSpec,
    MoleculePeriodicSpec,
    NoiseModelSpec,
    OptimizerSpec,
    PBCQMMMPeriodicPolicySpec,
    PBCSpec,
    PeriodicCellSpec,
    PECSpec,
    PointGroupSpec,
    PerturbativeCorrectionTaskSpec,
    PolicySpec,
    PointChargeDampingSpec,
    PointChargeSpec,
    ProblemSpec,
    PropertyTaskSpec,
    ResponsePropertyTaskSpec,
    ReadoutMitigationSpec,
    RunConfig,
    RunSpec,
    RuntimeOptionsSpec,
    SolverSpec,
    SymmetryCheckSpec,
    TCQSCICastModelSpec,
    TCQSCIInitialStateSpec,
    TCQSCIKickSpec,
    TCQSCIResourceEstimationSpec,
    TCQSCISelectionSpec,
    TCQSCISpec,
    TaskSpec,
    ZNESpec,
)
from qcchem.io.structure import (
    build_inline_geometry_provenance,
    load_structure_file,
    normalized_geometry_sha256,
)
from qcchem.pbc.geometry import (
    frac_to_cart,
    normalize_cell_unit,
    normalized_periodic_payload,
    periodic_fingerprint,
    validate_cell,
    validate_pbc_flags,
    wrap_positions,
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


def _parse_bool_triplet(value: Any, *, field_name: str) -> tuple[bool, bool, bool]:
    if not isinstance(value, list | tuple) or len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly three boolean values.")
    return validate_pbc_flags(value)


def _parse_cell(raw: Any, *, field_name: str, source: str | None = None) -> PeriodicCellSpec:
    if not isinstance(raw, dict):
        raise ValueError(f"{field_name} must be a mapping.")
    if "vectors" not in raw:
        raise ValueError(f"{field_name}.vectors is required.")
    unit = normalize_cell_unit(str(raw.get("unit", "angstrom")))
    vectors = validate_cell(raw["vectors"])
    lengths = None
    angles = None
    if raw.get("lengths") is not None:
        lengths = tuple(float(value) for value in raw["lengths"])
        if len(lengths) != 3:
            raise ValueError(f"{field_name}.lengths must contain exactly three values.")
    if raw.get("angles") is not None:
        angles = tuple(float(value) for value in raw["angles"])
        if len(angles) != 3:
            raise ValueError(f"{field_name}.angles must contain exactly three values.")
    return PeriodicCellSpec(
        vectors=vectors,
        lengths=lengths,
        angles=angles,
        unit=unit,
        source=str(raw.get("source", source)) if raw.get("source", source) is not None else None,
    )


def _periodic_to_payload(periodic: MoleculePeriodicSpec) -> dict[str, Any]:
    if not periodic.enabled:
        return {"enabled": False}
    if periodic.cell is None:
        raise ValueError("molecule.periodic.enabled=true requires molecule.periodic.cell.vectors.")
    payload = normalized_periodic_payload(
        enabled=True,
        vectors=periodic.cell.vectors,
        lengths=periodic.cell.lengths,
        angles=periodic.cell.angles,
        pbc=periodic.pbc,
        unit=periodic.cell.unit,
        coordinate_mode=periodic.coordinate_mode,
        wrap_policy=periodic.wrap_policy,
        source=periodic.source or periodic.cell.source,
    )
    return payload


def _periodic_from_payload(raw: dict[str, Any]) -> MoleculePeriodicSpec:
    if not raw or not bool(raw.get("enabled", False)):
        return MoleculePeriodicSpec()
    vectors = raw.get("cell_vectors") or raw.get("vectors")
    if vectors is None and isinstance(raw.get("cell"), dict):
        vectors = raw["cell"].get("vectors")
    unit = str(raw.get("cell_unit") or raw.get("unit") or "angstrom")
    lengths = None
    angles = None
    if isinstance(raw.get("cell"), dict):
        lengths = raw["cell"].get("lengths")
        angles = raw["cell"].get("angles")
    cell = PeriodicCellSpec(
        vectors=validate_cell(vectors),
        lengths=tuple(float(value) for value in lengths) if lengths is not None else None,
        angles=tuple(float(value) for value in angles) if angles is not None else None,
        unit=normalize_cell_unit(unit),
        source=str(raw.get("source")) if raw.get("source") is not None else None,
    )
    return MoleculePeriodicSpec(
        enabled=True,
        cell=cell,
        pbc=_parse_bool_triplet(raw.get("pbc", [True, True, True]), field_name="molecule.periodic.pbc"),
        coordinate_mode=str(raw.get("coordinate_mode", "cartesian")).strip().lower(),
        wrap_policy=str(raw.get("wrap_policy", "preserve")).strip().lower(),
        source=str(raw.get("source")) if raw.get("source") is not None else None,
        provenance=dict(raw.get("provenance", {})),
    )


def _parse_molecule_periodic(raw: Any, *, parsed_periodic: dict[str, Any] | None = None) -> MoleculePeriodicSpec:
    if raw is None:
        return _periodic_from_payload(parsed_periodic or {"enabled": False})
    if not isinstance(raw, dict):
        raise ValueError("molecule.periodic must be a mapping.")
    enabled = bool(raw.get("enabled", "cell" in raw or "pbc" in raw))
    if not enabled:
        return MoleculePeriodicSpec()
    cell_raw = raw.get("cell")
    if cell_raw is None and parsed_periodic and parsed_periodic.get("enabled"):
        base = dict(parsed_periodic)
        base.update({key: value for key, value in raw.items() if key != "cell"})
        return _periodic_from_payload(base)
    cell = _parse_cell(cell_raw, field_name="molecule.periodic.cell")
    coordinate_mode = str(raw.get("coordinate_mode", "cartesian")).strip().lower()
    if coordinate_mode not in {"cartesian", "fractional"}:
        raise ValueError("molecule.periodic.coordinate_mode must be cartesian or fractional.")
    wrap_policy = str(raw.get("wrap_policy", "preserve")).strip().lower()
    if wrap_policy not in {"preserve", "wrap", "none"}:
        raise ValueError("molecule.periodic.wrap_policy must be preserve, wrap, or none.")
    return MoleculePeriodicSpec(
        enabled=True,
        cell=cell,
        pbc=_parse_bool_triplet(raw.get("pbc", [True, True, True]), field_name="molecule.periodic.pbc"),
        coordinate_mode=coordinate_mode,
        wrap_policy=wrap_policy,
        source=str(raw.get("source")) if raw.get("source") is not None else None,
    )


def _parse_molecule(molecule_raw: dict[str, Any], *, base_dir: Path) -> MoleculeSpec:
    structure_file_raw = molecule_raw.get("structure_file")
    unit = str(molecule_raw.get("unit", "angstrom"))
    if structure_file_raw is not None:
        if "geometry" in molecule_raw and molecule_raw.get("geometry") is not None:
            raise ValueError("molecule.geometry and molecule.structure_file cannot both be set.")
        if unit.strip().lower() not in {"angstrom", "ang", "a"}:
            raise ValueError("molecule.structure_file inputs are interpreted as angstrom coordinates.")
        structure_path = resolve_user_path(base_dir, str(structure_file_raw))
        parsed = load_structure_file(
            structure_path,
            structure_format=(
                str(molecule_raw["structure_format"])
                if molecule_raw.get("structure_format") is not None
                else None
            ),
            source_path=str(structure_file_raw),
        )
        geometry = parsed.atoms
        periodic = _parse_molecule_periodic(
            molecule_raw.get("periodic"),
            parsed_periodic=parsed.periodic,
        )
        if (
            periodic.enabled
            and periodic.cell is not None
            and normalize_cell_unit(periodic.cell.unit) != normalize_cell_unit(unit)
        ):
            raise ValueError("PBC v1 requires molecule.periodic.cell.unit to match molecule.unit.")
        periodic_payload = _periodic_to_payload(periodic)
        input_provenance = dict(parsed.provenance)
        input_provenance["periodic"] = periodic_payload
    else:
        if molecule_raw.get("structure_format") is not None:
            raise ValueError("molecule.structure_format requires molecule.structure_file.")
        geometry_raw = molecule_raw.get("geometry", [])
        if not isinstance(geometry_raw, list) or not geometry_raw:
            raise ValueError("Molecule geometry must be a non-empty list or molecule.structure_file must be set.")
        geometry = _parse_atoms(geometry_raw)
        periodic = _parse_molecule_periodic(molecule_raw.get("periodic"))
        if (
            periodic.enabled
            and periodic.cell is not None
            and normalize_cell_unit(periodic.cell.unit) != normalize_cell_unit(unit)
        ):
            raise ValueError("PBC v1 requires molecule.periodic.cell.unit to match molecule.unit.")
        if periodic.enabled and periodic.coordinate_mode == "fractional":
            if periodic.cell is None:
                raise ValueError("fractional periodic coordinates require molecule.periodic.cell.vectors.")
            cartesian = [
                frac_to_cart(atom.coords, periodic.cell.vectors)
                for atom in geometry
            ]
            if periodic.wrap_policy == "wrap":
                cartesian = wrap_positions(cartesian, periodic.cell.vectors, periodic.pbc)
            geometry = [
                AtomSpec(
                    symbol=atom.symbol,
                    coords=(float(coords[0]), float(coords[1]), float(coords[2])),
                )
                for atom, coords in zip(geometry, cartesian)
            ]
        elif periodic.enabled and periodic.wrap_policy == "wrap":
            if periodic.cell is None:
                raise ValueError("molecule.periodic.wrap_policy=wrap requires cell vectors.")
            wrapped = wrap_positions([atom.coords for atom in geometry], periodic.cell.vectors, periodic.pbc)
            geometry = [
                AtomSpec(
                    symbol=atom.symbol,
                    coords=(float(coords[0]), float(coords[1]), float(coords[2])),
                )
                for atom, coords in zip(geometry, wrapped)
            ]
        periodic_payload = _periodic_to_payload(periodic)
        input_provenance = build_inline_geometry_provenance(
            geometry,
            unit=unit,
            periodic=periodic_payload,
        )

    return MoleculeSpec(
        name=str(molecule_raw["name"]),
        geometry=geometry,
        charge=int(molecule_raw.get("charge", 0)),
        multiplicity=int(molecule_raw.get("multiplicity", 1)),
        basis=str(molecule_raw.get("basis", "sto3g")),
        unit=unit,
        input_provenance=input_provenance,
        periodic=periodic,
    )


def _parse_active_space(problem_raw: dict[str, Any]) -> ActiveSpaceSpec | None:
    active_space_raw = problem_raw.get("active_space")
    if not isinstance(active_space_raw, dict):
        return None
    auto_raw = active_space_raw.get("auto")
    auto = AutoActiveSpaceSpec()
    if isinstance(auto_raw, dict):
        strategy = _choice(
            auto_raw.get("strategy", "frontier_orbitals"),
            field_name="problem.active_space.auto.strategy",
            allowed={"frontier_orbitals", "trusted_orbital_score"},
        )
        natural_occupation_source = _choice(
            auto_raw.get("natural_occupation_source", "mp2"),
            field_name="problem.active_space.auto.natural_occupation_source",
            allowed={"mp2", "scf", "none"},
        )
        min_spatial_orbitals = int(auto_raw.get("min_spatial_orbitals", 2))
        max_spatial_orbitals = (
            int(auto_raw["max_spatial_orbitals"])
            if auto_raw.get("max_spatial_orbitals") is not None
            else None
        )
        max_qubits = int(auto_raw["max_qubits"]) if auto_raw.get("max_qubits") is not None else None
        max_candidates = int(auto_raw.get("max_candidates", 5))
        if min_spatial_orbitals <= 0:
            raise ValueError("problem.active_space.auto.min_spatial_orbitals must be positive.")
        if max_spatial_orbitals is not None and max_spatial_orbitals < min_spatial_orbitals:
            raise ValueError(
                "problem.active_space.auto.max_spatial_orbitals must be greater than or equal to "
                "min_spatial_orbitals."
            )
        if max_qubits is not None and max_qubits <= 0:
            raise ValueError("problem.active_space.auto.max_qubits must be positive.")
        if max_candidates <= 0:
            raise ValueError("problem.active_space.auto.max_candidates must be positive.")
        if float(auto_raw.get("energy_window_hartree", 0.25)) < 0.0:
            raise ValueError("problem.active_space.auto.energy_window_hartree must be non-negative.")
        if float(auto_raw.get("occupation_tolerance", 0.02)) < 0.0:
            raise ValueError("problem.active_space.auto.occupation_tolerance must be non-negative.")
        auto = AutoActiveSpaceSpec(
            enabled=bool(auto_raw.get("enabled", False)),
            strategy=strategy,
            num_occupied=int(auto_raw.get("num_occupied", 1)),
            num_virtual=int(auto_raw.get("num_virtual", 1)),
            min_spatial_orbitals=min_spatial_orbitals,
            max_spatial_orbitals=max_spatial_orbitals,
            max_qubits=max_qubits,
            energy_window_hartree=float(auto_raw.get("energy_window_hartree", 0.25)),
            occupation_tolerance=float(auto_raw.get("occupation_tolerance", 0.02)),
            max_candidates=max_candidates,
            natural_occupation_source=natural_occupation_source,
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


def _choice(value: Any, *, field_name: str, allowed: set[str]) -> str:
    normalized = str(value).strip().lower()
    if normalized not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {allowed_text}.")
    return normalized


def _parse_point_group(problem_raw: dict[str, Any]) -> PointGroupSpec:
    point_group_raw = problem_raw.get("point_group")
    if not isinstance(point_group_raw, dict):
        return PointGroupSpec()
    return PointGroupSpec(
        subgroup=str(point_group_raw.get("subgroup", "auto")),
        reduction_mode=_choice(
            point_group_raw.get("reduction_mode", "audit"),
            field_name="problem.point_group.reduction_mode",
            allowed={"audit", "irrep_filter"},
        ),
        active_irreps=[str(value) for value in point_group_raw.get("active_irreps", [])],
        remove_irreps=[str(value) for value in point_group_raw.get("remove_irreps", [])],
    )


def _parse_mapping(raw: dict[str, Any]) -> MappingSpec:
    mapping_raw = _require_mapping(raw, "mapping")
    symmetry_raw = mapping_raw.get("symmetry_reduction", {})
    if symmetry_raw is None:
        symmetry_raw = {}
    if not isinstance(symmetry_raw, dict):
        raise ValueError("mapping.symmetry_reduction must be a mapping.")
    symmetry_reduction = MappingSymmetryReductionSpec(
        z2=_choice(
            symmetry_raw.get("z2", "auto"),
            field_name="mapping.symmetry_reduction.z2",
            allowed={"auto", "enabled", "disabled"},
        ),
        point_group=_choice(
            symmetry_raw.get("point_group", "auto"),
            field_name="mapping.symmetry_reduction.point_group",
            allowed={"auto", "enabled", "disabled"},
        ),
        strict=bool(symmetry_raw.get("strict", False)),
    )
    return MappingSpec(
        kind=str(mapping_raw.get("kind", "jordan_wigner")),
        symmetry_reduction=symmetry_reduction,
    )


def _parse_compression(problem_raw: dict[str, Any]) -> CompressionSpec:
    compression_raw = problem_raw.get("compression")
    if not isinstance(compression_raw, dict):
        return CompressionSpec()
    rank_schedule_raw = compression_raw.get("rank_schedule")
    rank_schedule = None
    if isinstance(rank_schedule_raw, list):
        rank_schedule = [int(value) for value in rank_schedule_raw]
    return CompressionSpec(
        enabled=bool(compression_raw.get("enabled", False)),
        method=str(compression_raw.get("method", "modified_cholesky")),
        threshold=float(compression_raw.get("threshold", 1.0e-8)),
        max_rank=(
            int(compression_raw["max_rank"])
            if compression_raw.get("max_rank") is not None
            else None
        ),
        rank_schedule=rank_schedule,
        term_budget_policy=str(compression_raw.get("term_budget_policy", "precision_first")),
        compression_error_budget_hartree=float(
            compression_raw.get("compression_error_budget_hartree", 8.0e-4)
        ),
        allow_pauli_truncation=bool(compression_raw.get("allow_pauli_truncation", False)),
        runtime_term_budget=(
            int(compression_raw["runtime_term_budget"])
            if compression_raw.get("runtime_term_budget") is not None
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


def _parse_continuity(
    raw: dict[str, Any],
    *,
    default_enabled: bool,
    default_mode: str = "previous_optimal",
    allowed_modes: set[str] | None = None,
) -> ContinuitySpec:
    """Parse aggregate workflow warm-start policy."""
    continuity_raw = raw.get("continuity")
    allowed = allowed_modes or {"previous_optimal"}
    if continuity_raw is None:
        return ContinuitySpec(enabled=default_enabled, mode=default_mode)
    if not isinstance(continuity_raw, dict):
        raise ValueError("continuity must be a mapping.")
    mode = str(continuity_raw.get("mode", default_mode)).strip().lower()
    if mode not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"continuity.mode must be one of {allowed_text}.")
    mismatch = str(continuity_raw.get("on_parameter_mismatch", "fallback")).strip().lower()
    if mismatch != "fallback":
        raise ValueError("continuity.on_parameter_mismatch currently supports only fallback.")
    return ContinuitySpec(
        enabled=bool(continuity_raw.get("enabled", default_enabled)),
        mode=mode,
        on_parameter_mismatch=mismatch,
    )


def _parse_lr_ace_adaptive(solver_raw: dict[str, Any]) -> LRACEAdaptiveSpec:
    adaptive_raw = solver_raw.get("lr_ace_adaptive")
    if not isinstance(adaptive_raw, dict):
        return LRACEAdaptiveSpec()
    defaults = LRACEAdaptiveSpec()
    return LRACEAdaptiveSpec(
        enabled=bool(adaptive_raw.get("enabled", False)),
        generator_schedule=[
            int(value) for value in adaptive_raw.get("generator_schedule", defaults.generator_schedule)
        ],
        optimizer_maxiter_schedule=[
            int(value)
            for value in adaptive_raw.get(
                "optimizer_maxiter_schedule",
                defaults.optimizer_maxiter_schedule,
            )
        ],
        initial_point_strategies=[
            str(value)
            for value in adaptive_raw.get(
                "initial_point_strategies",
                defaults.initial_point_strategies,
            )
        ],
        random_restarts=int(adaptive_raw.get("random_restarts", defaults.random_restarts)),
        target_error_hartree=float(
            adaptive_raw.get("target_error_hartree", defaults.target_error_hartree)
        ),
        max_wall_time_seconds=float(
            adaptive_raw.get("max_wall_time_seconds", defaults.max_wall_time_seconds)
        ),
        uncompressed_check_qubit_limit=int(
            adaptive_raw.get(
                "uncompressed_check_qubit_limit",
                defaults.uncompressed_check_qubit_limit,
            )
        ),
        candidate_pool_policy=str(
            adaptive_raw.get("candidate_pool_policy", defaults.candidate_pool_policy)
        ),
        candidate_scan_limit=int(
            adaptive_raw.get("candidate_scan_limit", defaults.candidate_scan_limit)
        ),
        residual_batch_size=int(
            adaptive_raw.get("residual_batch_size", defaults.residual_batch_size)
        ),
        residual_scan_angles=[
            float(value)
            for value in adaptive_raw.get(
                "residual_scan_angles",
                defaults.residual_scan_angles,
            )
        ],
        min_energy_improvement_hartree=float(
            adaptive_raw.get(
                "min_energy_improvement_hartree",
                defaults.min_energy_improvement_hartree,
            )
        ),
        max_adaptive_expansions=int(
            adaptive_raw.get("max_adaptive_expansions", defaults.max_adaptive_expansions)
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
    execution_raw = embedding_raw.get("execution", {})
    if execution_raw is None:
        execution_raw = {}
    if not isinstance(execution_raw, dict):
        raise ValueError("problem.embedding.execution must be a mapping.")
    return EmbeddingSpec(
        enabled=bool(embedding_raw.get("enabled", False)),
        method=str(embedding_raw.get("method", "dmet_skeleton")),
        bath_threshold=float(embedding_raw.get("bath_threshold", 0.05)),
        solver_plugin=str(embedding_raw.get("solver_plugin", "placeholder_fragment_solver")),
        fragments=fragments,
        execution=EmbeddingExecutionSpec(
            enabled=bool(execution_raw.get("enabled", False)),
            plugin=str(execution_raw.get("plugin", "pyscf_rhf_fragment")),
            validate_against_full_system=bool(execution_raw.get("validate_against_full_system", True)),
        ),
    )


def _parse_point_charge(
    item: dict[str, Any],
    *,
    index: int,
    prefix: str = "problem.external_point_charges.charges",
) -> PointChargeSpec:
    if not isinstance(item, dict):
        raise ValueError(f"{prefix}.{index} must be a mapping.")
    coords = item.get("coords")
    if not isinstance(coords, list) or len(coords) != 3:
        raise ValueError(f"{prefix}.{index}.coords must have three values.")
    if "charge" not in item:
        raise ValueError(f"{prefix}.{index}.charge is required.")
    label = item.get("label")
    return PointChargeSpec(
        label=(str(label) if label is not None else None),
        coords=(float(coords[0]), float(coords[1]), float(coords[2])),
        charge=float(item["charge"]),
    )


def _parse_external_point_charges(
    problem_raw: dict[str, Any],
    *,
    base_dir: Path,
) -> ExternalPointChargeSpec:
    raw = problem_raw.get("external_point_charges")
    if raw is None:
        return ExternalPointChargeSpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.external_point_charges must be a mapping.")
    unit_raw = raw.get("unit")
    unit = str(unit_raw) if unit_raw is not None else None
    if unit is not None and unit.strip().lower() not in {"angstrom", "ang", "a", "bohr", "au"}:
        raise ValueError("problem.external_point_charges.unit must be angstrom or bohr.")
    source_file = None
    if raw.get("source_file") is not None:
        source_file = resolve_user_path(base_dir, str(raw["source_file"]))
        if bool(raw.get("enabled", False)) and not source_file.exists():
            raise FileNotFoundError(f"External point-charge source_file not found: {source_file}")
    charges_raw = raw.get("charges", [])
    if charges_raw is None:
        charges_raw = []
    if not isinstance(charges_raw, list):
        raise ValueError("problem.external_point_charges.charges must be a list.")
    threshold = float(raw.get("min_distance_to_qm_atoms", 1.0e-6))
    if threshold <= 0.0:
        raise ValueError("problem.external_point_charges.min_distance_to_qm_atoms must be positive.")
    return ExternalPointChargeSpec(
        enabled=bool(raw.get("enabled", False)),
        unit=unit,
        source_file=source_file,
        charges=[
            _parse_point_charge(item, index=index)
            for index, item in enumerate(charges_raw)
        ],
        min_distance_to_qm_atoms=threshold,
    )


def _validate_distance_unit(unit: str, *, field_name: str) -> str:
    normalized = unit.strip().lower()
    if normalized not in {"angstrom", "ang", "a", "bohr", "au"}:
        raise ValueError(f"{field_name} must be angstrom or bohr.")
    if normalized in {"ang", "a"}:
        return "angstrom"
    if normalized == "au":
        return "bohr"
    return normalized


def _parse_point_charge_damping(raw: Any) -> PointChargeDampingSpec:
    if raw is None:
        return PointChargeDampingSpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.environment_embedding.point_charges.damping must be a mapping.")
    kind = str(raw.get("kind", "gaussian")).strip().lower()
    if kind not in {"gaussian", "none"}:
        raise ValueError("problem.environment_embedding.point_charges.damping.kind must be gaussian or none.")
    default_radius_raw = raw.get("default_radius", 0.40)
    default_radius = (
        float(default_radius_raw)
        if default_radius_raw is not None
        else None
    )
    radius_unit = _validate_distance_unit(
        str(raw.get("radius_unit", "angstrom")),
        field_name="problem.environment_embedding.point_charges.damping.radius_unit",
    )
    min_radius = float(raw.get("min_radius", 0.15))
    if min_radius <= 0.0:
        raise ValueError("problem.environment_embedding.point_charges.damping.min_radius must be positive.")
    if kind == "gaussian":
        if default_radius is None or default_radius <= 0.0:
            raise ValueError(
                "problem.environment_embedding.point_charges.damping.default_radius must be positive for gaussian damping."
            )
        if default_radius < min_radius:
            raise ValueError(
                "problem.environment_embedding.point_charges.damping.default_radius must be >= min_radius."
            )
    warning = float(raw.get("overpolarization_warning_potential_au", 2.0))
    if warning <= 0.0:
        raise ValueError(
            "problem.environment_embedding.point_charges.damping.overpolarization_warning_potential_au must be positive."
        )
    return PointChargeDampingSpec(
        kind=kind,
        default_radius=default_radius,
        radius_unit=radius_unit,
        min_radius=min_radius,
        overpolarization_warning_potential_au=warning,
    )


def _parse_environment_point_charges(
    raw: Any,
    *,
    base_dir: Path,
) -> EnvironmentPointChargeSpec:
    if raw is None:
        return EnvironmentPointChargeSpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.environment_embedding.point_charges must be a mapping.")
    unit_raw = raw.get("unit")
    unit = (
        _validate_distance_unit(
            str(unit_raw),
            field_name="problem.environment_embedding.point_charges.unit",
        )
        if unit_raw is not None
        else None
    )
    source_file = None
    if raw.get("source_file") is not None:
        source_file = resolve_user_path(base_dir, str(raw["source_file"]))
        if bool(raw.get("enabled", False)) and not source_file.exists():
            raise FileNotFoundError(f"Environment point-charge source_file not found: {source_file}")
    charges_raw = raw.get("charges", [])
    if charges_raw is None:
        charges_raw = []
    if not isinstance(charges_raw, list):
        raise ValueError("problem.environment_embedding.point_charges.charges must be a list.")
    threshold = float(raw.get("min_distance_to_qm_atoms", 1.0e-6))
    if threshold <= 0.0:
        raise ValueError(
            "problem.environment_embedding.point_charges.min_distance_to_qm_atoms must be positive."
        )
    return EnvironmentPointChargeSpec(
        enabled=bool(raw.get("enabled", False)),
        unit=unit,
        source_file=source_file,
        charges=[
            _parse_point_charge(
                item,
                index=index,
                prefix="problem.environment_embedding.point_charges.charges",
            )
            for index, item in enumerate(charges_raw)
        ],
        min_distance_to_qm_atoms=threshold,
        damping=_parse_point_charge_damping(raw.get("damping")),
    )


def _parse_boundary_embedding(raw: Any) -> BoundaryEmbeddingSpec:
    if raw is None:
        return BoundaryEmbeddingSpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.environment_embedding.boundary must be a mapping.")
    method = str(
        raw.get("method", "localized_orbital_freeze_project_downfold")
    ).strip().lower()
    if method != "localized_orbital_freeze_project_downfold":
        raise ValueError(
            "problem.environment_embedding.boundary.method must be localized_orbital_freeze_project_downfold."
        )
    localization = str(raw.get("localization", "iao_lowdin")).strip().lower()
    if localization not in {"iao_lowdin", "boys", "lowdin"}:
        raise ValueError(
            "problem.environment_embedding.boundary.localization must be iao_lowdin, boys, or lowdin."
        )
    cut_bonds_raw = raw.get("cut_bonds", [])
    if cut_bonds_raw is None:
        cut_bonds_raw = []
    if not isinstance(cut_bonds_raw, list):
        raise ValueError("problem.environment_embedding.boundary.cut_bonds must be a list.")
    cut_bonds: list[BoundaryCutBondSpec] = []
    for index, item in enumerate(cut_bonds_raw):
        if not isinstance(item, dict):
            raise ValueError(
                f"problem.environment_embedding.boundary.cut_bonds.{index} must be a mapping."
            )
        if "qm_atom" not in item or "mm_atom" not in item:
            raise ValueError(
                f"problem.environment_embedding.boundary.cut_bonds.{index} requires qm_atom and mm_atom."
            )
        label = item.get("label")
        cut_bonds.append(
            BoundaryCutBondSpec(
                label=(str(label) if label is not None else None),
                qm_atom=int(item["qm_atom"]),
                mm_atom=int(item["mm_atom"]),
            )
        )
    leakage_threshold = float(raw.get("leakage_threshold", 0.05))
    if leakage_threshold < 0.0:
        raise ValueError(
            "problem.environment_embedding.boundary.leakage_threshold must be non-negative."
        )
    return BoundaryEmbeddingSpec(
        enabled=bool(raw.get("enabled", False)),
        method=method,
        localization=localization,
        cut_bonds=cut_bonds,
        leakage_threshold=leakage_threshold,
        strict=bool(raw.get("strict", True)),
    )


def _parse_environment_cache(raw: Any, *, base_dir: Path) -> EffectiveHamiltonianCacheSpec:
    if raw is None:
        return EffectiveHamiltonianCacheSpec(
            directory=(base_dir / "artifacts/effective_hamiltonians").resolve()
        )
    if not isinstance(raw, dict):
        raise ValueError("problem.environment_embedding.cache must be a mapping.")
    directory_raw = Path(str(raw.get("directory", "artifacts/effective_hamiltonians"))).expanduser()
    directory = (
        directory_raw
        if directory_raw.is_absolute()
        else (base_dir / directory_raw).resolve()
    )
    return EffectiveHamiltonianCacheSpec(
        enabled=bool(raw.get("enabled", True)),
        directory=directory,
        refresh=bool(raw.get("refresh", False)),
    )


def _parse_environment_periodic_policy(raw: Any) -> PBCQMMMPeriodicPolicySpec:
    if raw is None:
        return PBCQMMMPeriodicPolicySpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.environment_embedding.periodic_policy must be a mapping.")
    mode = str(raw.get("mode", "finite")).strip().lower()
    if mode not in {"finite", "ewald"}:
        raise ValueError("problem.environment_embedding.periodic_policy.mode must be finite or ewald.")
    neutralization = str(raw.get("neutralization", "reject")).strip().lower()
    if neutralization not in {"reject", "uniform_background"}:
        raise ValueError(
            "problem.environment_embedding.periodic_policy.neutralization must be reject or uniform_background."
        )
    ewald_precision = float(raw.get("ewald_precision", 1.0e-8))
    if ewald_precision <= 0.0:
        raise ValueError("problem.environment_embedding.periodic_policy.ewald_precision must be positive.")
    real_space_cutoff = raw.get("real_space_cutoff")
    reciprocal_cutoff = raw.get("reciprocal_cutoff")
    return PBCQMMMPeriodicPolicySpec(
        mode=mode,
        require_charge_neutrality=bool(raw.get("require_charge_neutrality", True)),
        neutralization=neutralization,
        ewald_precision=ewald_precision,
        real_space_cutoff=(float(real_space_cutoff) if real_space_cutoff is not None else None),
        reciprocal_cutoff=(float(reciprocal_cutoff) if reciprocal_cutoff is not None else None),
    )


def _parse_environment_embedding(
    problem_raw: dict[str, Any],
    *,
    base_dir: Path,
) -> EnvironmentEmbeddingSpec:
    raw = problem_raw.get("environment_embedding")
    if raw is None:
        return EnvironmentEmbeddingSpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.environment_embedding must be a mapping.")
    mode = str(raw.get("mode", "effective_hamiltonian")).strip().lower()
    if mode != "effective_hamiltonian":
        raise ValueError("problem.environment_embedding.mode must be effective_hamiltonian.")
    return EnvironmentEmbeddingSpec(
        enabled=bool(raw.get("enabled", False)),
        mode=mode,
        point_charges=_parse_environment_point_charges(
            raw.get("point_charges"),
            base_dir=base_dir,
        ),
        boundary=_parse_boundary_embedding(raw.get("boundary")),
        cache=_parse_environment_cache(raw.get("cache"), base_dir=base_dir),
        periodic_policy=_parse_environment_periodic_policy(raw.get("periodic_policy")),
    )


def _parse_pbc(problem_raw: dict[str, Any]) -> PBCSpec:
    raw = problem_raw.get("pbc")
    if raw is None:
        return PBCSpec()
    if not isinstance(raw, dict):
        raise ValueError("problem.pbc must be a mapping.")
    driver = str(raw.get("driver", "pyscf_pbc")).strip().lower()
    if driver != "pyscf_pbc":
        raise ValueError("problem.pbc.driver must be pyscf_pbc.")
    mode = str(raw.get("mode", "gamma_supercell")).strip().lower()
    if mode != "gamma_supercell":
        raise ValueError("problem.pbc.mode must be gamma_supercell in v1.")
    kpoint_mesh_raw = raw.get("kpoint_mesh", [1, 1, 1])
    if not isinstance(kpoint_mesh_raw, list | tuple) or len(kpoint_mesh_raw) != 3:
        raise ValueError("problem.pbc.kpoint_mesh must contain exactly three positive integers.")
    kpoint_mesh = tuple(int(value) for value in kpoint_mesh_raw)
    if any(value < 1 for value in kpoint_mesh):
        raise ValueError("problem.pbc.kpoint_mesh entries must be positive.")
    density_fitting = str(raw.get("density_fitting", "fftdf")).strip().lower()
    if density_fitting not in {"fftdf", "gdf", "mdf", "aftdf"}:
        raise ValueError("problem.pbc.density_fitting must be fftdf, gdf, mdf, or aftdf.")
    precision = float(raw.get("precision", 1.0e-8))
    if precision <= 0.0:
        raise ValueError("problem.pbc.precision must be positive.")
    mesh_raw = raw.get("mesh")
    mesh = None
    if mesh_raw is not None:
        if not isinstance(mesh_raw, list | tuple) or len(mesh_raw) != 3:
            raise ValueError("problem.pbc.mesh must contain exactly three positive integers.")
        mesh = tuple(int(value) for value in mesh_raw)
        if any(value < 1 for value in mesh):
            raise ValueError("problem.pbc.mesh entries must be positive.")
    neutralization = str(raw.get("neutralization", "reject")).strip().lower()
    if neutralization not in {"reject", "uniform_background"}:
        raise ValueError("problem.pbc.neutralization must be reject or uniform_background.")
    cell = _parse_cell(raw.get("cell"), field_name="problem.pbc.cell") if raw.get("cell") is not None else None
    coordinate_mode = str(raw.get("coordinate_mode", "cartesian")).strip().lower()
    if coordinate_mode not in {"cartesian", "fractional"}:
        raise ValueError("problem.pbc.coordinate_mode must be cartesian or fractional.")
    wrap_policy = str(raw.get("wrap_policy", "preserve")).strip().lower()
    if wrap_policy not in {"preserve", "wrap", "none"}:
        raise ValueError("problem.pbc.wrap_policy must be preserve, wrap, or none.")
    return PBCSpec(
        enabled=bool(raw.get("enabled", False)),
        cell=cell,
        pbc=_parse_bool_triplet(raw.get("pbc", [True, True, True]), field_name="problem.pbc.pbc"),
        coordinate_mode=coordinate_mode,
        wrap_policy=wrap_policy,
        source=str(raw.get("source")) if raw.get("source") is not None else None,
        driver=driver,
        mode=mode,
        kpoint_mesh=kpoint_mesh,  # type: ignore[arg-type]
        density_fitting=density_fitting,
        precision=precision,
        mesh=mesh,  # type: ignore[arg-type]
        neutralization=neutralization,
    )


def _parse_lattice_qed(problem_raw: dict[str, Any]) -> LatticeQEDSpec:
    qft_raw = problem_raw.get("qft")
    if not isinstance(qft_raw, dict):
        return LatticeQEDSpec()
    grid_raw = qft_raw.get("grid", {})
    matter_raw = qft_raw.get("matter", {})
    gauge_raw = qft_raw.get("gauge", {})
    constraints_raw = qft_raw.get("constraints", {})
    ansatz_raw = qft_raw.get("ansatz", {})
    engine_raw = qft_raw.get("engine", {})
    dynamics_raw = qft_raw.get("dynamics", {})
    if not isinstance(grid_raw, dict):
        raise ValueError("problem.qft.grid must be a mapping.")
    if not isinstance(matter_raw, dict):
        raise ValueError("problem.qft.matter must be a mapping.")
    if not isinstance(gauge_raw, dict):
        raise ValueError("problem.qft.gauge must be a mapping.")
    if not isinstance(constraints_raw, dict):
        raise ValueError("problem.qft.constraints must be a mapping.")
    if not isinstance(ansatz_raw, dict):
        raise ValueError("problem.qft.ansatz must be a mapping.")
    if not isinstance(engine_raw, dict):
        raise ValueError("problem.qft.engine must be a mapping.")
    if not isinstance(dynamics_raw, dict):
        raise ValueError("problem.qft.dynamics must be a mapping.")

    dimensions = int(qft_raw.get("dimensions", 1))
    if dimensions < 1:
        raise ValueError("problem.qft.dimensions must be at least 1.")
    shape = [int(value) for value in grid_raw.get("shape", [2] * dimensions)]
    spacing = [float(value) for value in grid_raw.get("spacing", [1.0] * dimensions)]
    if len(shape) != dimensions:
        raise ValueError("problem.qft.grid.shape length must match problem.qft.dimensions.")
    if len(spacing) != dimensions:
        raise ValueError("problem.qft.grid.spacing length must match problem.qft.dimensions.")
    if any(value < 2 for value in shape):
        raise ValueError("problem.qft.grid.shape entries must be at least 2.")
    if any(value <= 0.0 for value in spacing):
        raise ValueError("problem.qft.grid.spacing entries must be positive.")

    target_electrons = matter_raw.get("target_electrons", "auto")
    if target_electrons != "auto":
        target_electrons = int(target_electrons)
        if target_electrons < 0:
            raise ValueError("problem.qft.matter.target_electrons must be non-negative.")

    electric_cutoff = int(gauge_raw.get("electric_cutoff", 1))
    if electric_cutoff < 0:
        raise ValueError("problem.qft.gauge.electric_cutoff must be non-negative.")
    gauss_law_tolerance = float(constraints_raw.get("gauss_law_tolerance", 1.0e-8))
    if gauss_law_tolerance <= 0.0:
        raise ValueError("problem.qft.constraints.gauss_law_tolerance must be positive.")
    max_sector_enumeration_qubits = int(
        constraints_raw.get("max_sector_enumeration_qubits", 10)
    )
    if max_sector_enumeration_qubits < 0:
        raise ValueError(
            "problem.qft.constraints.max_sector_enumeration_qubits must be non-negative."
        )
    dynamics_initial_raw = dynamics_raw.get("initial_state", {})
    dynamics_time_raw = dynamics_raw.get("time_grid", {})
    dynamics_evolution_raw = dynamics_raw.get("evolution", {})
    dynamics_runtime_raw = dynamics_raw.get("runtime", {})
    if not isinstance(dynamics_initial_raw, dict):
        raise ValueError("problem.qft.dynamics.initial_state must be a mapping.")
    if not isinstance(dynamics_time_raw, dict):
        raise ValueError("problem.qft.dynamics.time_grid must be a mapping.")
    if not isinstance(dynamics_evolution_raw, dict):
        raise ValueError("problem.qft.dynamics.evolution must be a mapping.")
    if not isinstance(dynamics_runtime_raw, dict):
        raise ValueError("problem.qft.dynamics.runtime must be a mapping.")
    dynamics_num_points = int(dynamics_time_raw.get("num_points", 41))
    if dynamics_num_points < 2:
        raise ValueError("problem.qft.dynamics.time_grid.num_points must be at least 2.")
    dynamics_trotter_step = float(dynamics_evolution_raw.get("trotter_step", 0.05))
    if dynamics_trotter_step <= 0.0:
        raise ValueError("problem.qft.dynamics.evolution.trotter_step must be positive.")
    dynamics_exact_qubit_limit = int(dynamics_evolution_raw.get("exact_qubit_limit", 12))
    if dynamics_exact_qubit_limit < 0:
        raise ValueError("problem.qft.dynamics.evolution.exact_qubit_limit must be non-negative.")
    dynamics_trotter_order = int(dynamics_evolution_raw.get("trotter_order", 1))
    if dynamics_trotter_order != 1:
        raise ValueError("problem.qft.dynamics.evolution.trotter_order currently supports only 1.")
    engine_representation = str(engine_raw.get("representation", "auto")).strip().lower()
    if engine_representation not in {"auto", "sparse_projected", "sparse_full", "dense_full"}:
        raise ValueError(
            "problem.qft.engine.representation must be one of auto, sparse_projected, sparse_full, or dense_full."
        )
    engine_materialize_pauli = str(engine_raw.get("materialize_pauli", "auto")).strip().lower()
    if engine_materialize_pauli not in {"auto", "always", "never"}:
        raise ValueError("problem.qft.engine.materialize_pauli must be one of auto, always, or never.")
    engine_store_basis_indices = str(engine_raw.get("store_basis_indices", "preview")).strip().lower()
    if engine_store_basis_indices not in {"preview", "full", "hash_only"}:
        raise ValueError("problem.qft.engine.store_basis_indices must be one of preview, full, or hash_only.")
    engine_max_projected_dimension = int(engine_raw.get("max_projected_dimension", 4096))
    if engine_max_projected_dimension < 1:
        raise ValueError("problem.qft.engine.max_projected_dimension must be positive.")
    engine_max_full_qubits_for_dense = int(engine_raw.get("max_full_qubits_for_dense", 10))
    if engine_max_full_qubits_for_dense < 0:
        raise ValueError("problem.qft.engine.max_full_qubits_for_dense must be non-negative.")
    engine_projector_tolerance = float(engine_raw.get("projector_tolerance", 1.0e-8))
    if engine_projector_tolerance <= 0.0:
        raise ValueError("problem.qft.engine.projector_tolerance must be positive.")

    return LatticeQEDSpec(
        enabled=bool(qft_raw.get("enabled", False)),
        model=str(qft_raw.get("model", "lattice_qed_minimal_coupling")),
        dimensions=dimensions,
        grid=LatticeQEDGridSpec(
            shape=shape,
            spacing=spacing,
            origin=str(grid_raw.get("origin", "molecule_center")),
            axes=str(grid_raw.get("axes", "principal")),
            boundary=str(grid_raw.get("boundary", "open")),
            softening=float(grid_raw.get("softening", 0.35)),
        ),
        matter=LatticeQEDMatterSpec(
            spin_components=int(matter_raw.get("spin_components", 2)),
            target_electrons=target_electrons,
            include_soft_coulomb_density=bool(
                matter_raw.get("include_soft_coulomb_density", False)
            ),
        ),
        gauge=LatticeQEDGaugeSpec(
            group=str(gauge_raw.get("group", "u1")),
            electric_cutoff=electric_cutoff,
            coupling=float(gauge_raw.get("coupling", 1.0)),
            include_magnetic_plaquettes=bool(gauge_raw.get("include_magnetic_plaquettes", True)),
        ),
        constraints=LatticeQEDConstraintSpec(
            gauss_law_penalty=float(constraints_raw.get("gauss_law_penalty", 10.0)),
            particle_number_penalty=float(constraints_raw.get("particle_number_penalty", 10.0)),
            padding_penalty=float(constraints_raw.get("padding_penalty", 50.0)),
            enforce_physical_sector=bool(
                constraints_raw.get("enforce_physical_sector", False)
            ),
            target_charge_sector=str(constraints_raw.get("target_charge_sector", "neutral")),
            gauss_law_tolerance=gauss_law_tolerance,
            max_sector_enumeration_qubits=max_sector_enumeration_qubits,
        ),
        ansatz=LatticeQEDAnsatzSpec(
            generator_policy=str(ansatz_raw.get("generator_policy", "gauge_invariant_hopping"))
        ),
        engine=LatticeQEDEngineSpec(
            representation=engine_representation,
            auto_project_physical_sector=bool(
                engine_raw.get("auto_project_physical_sector", True)
            ),
            max_projected_dimension=engine_max_projected_dimension,
            max_full_qubits_for_dense=engine_max_full_qubits_for_dense,
            materialize_pauli=engine_materialize_pauli,
            store_basis_indices=engine_store_basis_indices,
            projector_tolerance=engine_projector_tolerance,
        ),
        dynamics=LatticeQEDDynamicsSpec(
            enabled=bool(dynamics_raw.get("enabled", False)),
            method=str(dynamics_raw.get("method", "real_time_quench")),
            initial_state=LatticeQEDDynamicsInitialStateSpec(
                kind=str(dynamics_initial_raw.get("kind", "local_hopping_pulse")),
                base=str(dynamics_initial_raw.get("base", "physical_reference")),
                link_index=int(dynamics_initial_raw.get("link_index", 0)),
                pulse_time=float(dynamics_initial_raw.get("pulse_time", 0.05)),
                pulse_strength=float(dynamics_initial_raw.get("pulse_strength", 1.0)),
            ),
            time_grid=LatticeQEDDynamicsTimeGridSpec(
                start=float(dynamics_time_raw.get("start", 0.0)),
                stop=float(dynamics_time_raw.get("stop", 2.0)),
                num_points=dynamics_num_points,
            ),
            evolution=LatticeQEDDynamicsEvolutionSpec(
                exact_enabled=bool(dynamics_evolution_raw.get("exact_enabled", True)),
                exact_qubit_limit=dynamics_exact_qubit_limit,
                trotter_enabled=bool(dynamics_evolution_raw.get("trotter_enabled", True)),
                trotter_step=dynamics_trotter_step,
                trotter_order=dynamics_trotter_order,
            ),
            runtime=LatticeQEDDynamicsRuntimeSpec(
                enabled=bool(dynamics_runtime_raw.get("enabled", False)),
                runtime_observables=str(
                    dynamics_runtime_raw.get("runtime_observables", "aggregate_gauge")
                ),
            ),
        ),
    )


def _parse_cavity_qed(problem_raw: dict[str, Any]) -> CavityQEDSpec:
    cavity_raw = problem_raw.get("cavity_qed")
    if not isinstance(cavity_raw, dict):
        return CavityQEDSpec()

    model = str(cavity_raw.get("model", "pauli_fierz_cavity_qed")).strip().lower()
    if model != "pauli_fierz_cavity_qed":
        raise ValueError("problem.cavity_qed.model must be pauli_fierz_cavity_qed.")
    photon_encoding = str(cavity_raw.get("photon_encoding", "linear")).strip().lower()
    if photon_encoding != "linear":
        raise ValueError("problem.cavity_qed.photon_encoding must be linear.")
    penalty = float(cavity_raw.get("photon_physical_subspace_penalty", 25.0))
    if penalty < 0.0:
        raise ValueError("problem.cavity_qed.photon_physical_subspace_penalty must be non-negative.")

    modes_raw = cavity_raw.get("modes", [])
    if modes_raw is None:
        modes_raw = []
    if not isinstance(modes_raw, list):
        raise ValueError("problem.cavity_qed.modes must be a list.")
    if bool(cavity_raw.get("enabled", False)) and not modes_raw:
        modes_raw = [
            {
                "frequency": 0.4,
                "coupling_strength": 0.05,
                "polarization": [0.0, 0.0, 1.0],
                "max_occupation": 1,
            }
        ]

    modes: list[CavityQEDModeSpec] = []
    for index, item in enumerate(modes_raw):
        if not isinstance(item, dict):
            raise ValueError(f"problem.cavity_qed.modes.{index} must be a mapping.")
        frequency = float(item.get("frequency", 0.4))
        if frequency <= 0.0:
            raise ValueError(f"problem.cavity_qed.modes.{index}.frequency must be positive.")
        coupling_strength = float(item.get("coupling_strength", 0.05))
        if coupling_strength < 0.0:
            raise ValueError(f"problem.cavity_qed.modes.{index}.coupling_strength must be non-negative.")
        polarization = [float(value) for value in item.get("polarization", [0.0, 0.0, 1.0])]
        if len(polarization) != 3:
            raise ValueError(f"problem.cavity_qed.modes.{index}.polarization must have three entries.")
        norm = sum(value * value for value in polarization) ** 0.5
        if norm <= 1.0e-12:
            raise ValueError(f"problem.cavity_qed.modes.{index}.polarization must be non-zero.")
        max_occupation = int(item.get("max_occupation", 1))
        if max_occupation < 0:
            raise ValueError(f"problem.cavity_qed.modes.{index}.max_occupation must be non-negative.")
        modes.append(
            CavityQEDModeSpec(
                frequency=frequency,
                coupling_strength=coupling_strength,
                polarization=polarization,
                max_occupation=max_occupation,
            )
        )

    return CavityQEDSpec(
        enabled=bool(cavity_raw.get("enabled", False)),
        model=model,
        photon_encoding=photon_encoding,
        include_dipole_self_energy=bool(cavity_raw.get("include_dipole_self_energy", True)),
        photon_physical_subspace_penalty=penalty,
        modes=modes or [CavityQEDModeSpec()],
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


def _parse_geometry_optimization(tasks_raw: dict[str, Any]) -> GeometryOptimizationTaskSpec:
    raw = tasks_raw.get("geometry_optimization")
    if not isinstance(raw, dict):
        return GeometryOptimizationTaskSpec()
    return GeometryOptimizationTaskSpec(
        enabled=bool(raw.get("enabled", False)),
        method=str(raw.get("method", "pyscf_rhf")),
        max_steps=int(raw.get("max_steps", 50)),
        gradient_tolerance=float(raw.get("gradient_tolerance", 3.0e-4)),
    )


def _parse_gradient(tasks_raw: dict[str, Any]) -> GradientTaskSpec:
    raw = tasks_raw.get("gradient")
    if not isinstance(raw, dict):
        return GradientTaskSpec()
    return GradientTaskSpec(
        enabled=bool(raw.get("enabled", False)),
        method=str(raw.get("method", "pyscf_rhf")),
        state_index=int(raw.get("state_index", 0)),
    )


def _parse_response_properties(tasks_raw: dict[str, Any]) -> ResponsePropertyTaskSpec:
    raw = tasks_raw.get("response_properties")
    if not isinstance(raw, dict):
        return ResponsePropertyTaskSpec()
    properties = raw.get("properties", ["static_polarizability"])
    if not isinstance(properties, list):
        raise ValueError("tasks.response_properties.properties must be a list.")
    return ResponsePropertyTaskSpec(
        enabled=bool(raw.get("enabled", False)),
        properties=[str(item) for item in properties],
        method=str(raw.get("method", "finite_field_rhf")),
        finite_field_step=float(raw.get("finite_field_step", 1.0e-3)),
    )


def _parse_tc_qsci(raw: dict[str, Any], *, base_dir: Path) -> TCQSCISpec:
    tc_raw = raw.get("tc_qsci")
    if not isinstance(tc_raw, dict):
        return TCQSCISpec()
    cast_raw = tc_raw.get("cast_model", {})
    if not isinstance(cast_raw, dict):
        raise ValueError("tc_qsci.cast_model must be a mapping.")
    initial_raw = tc_raw.get("initial_state", {})
    if not isinstance(initial_raw, dict):
        raise ValueError("tc_qsci.initial_state must be a mapping.")
    kick_raw = tc_raw.get("kick", {})
    if not isinstance(kick_raw, dict):
        raise ValueError("tc_qsci.kick must be a mapping.")
    selection_raw = tc_raw.get("selection", {})
    if not isinstance(selection_raw, dict):
        raise ValueError("tc_qsci.selection must be a mapping.")
    resource_raw = tc_raw.get("resource_estimation", {})
    if not isinstance(resource_raw, dict):
        raise ValueError("tc_qsci.resource_estimation must be a mapping.")
    determinants_raw = initial_raw.get("determinants", [])
    if not isinstance(determinants_raw, list):
        raise ValueError("tc_qsci.initial_state.determinants must be a list.")
    return TCQSCISpec(
        enabled=bool(tc_raw.get("enabled", False)),
        resource_estimation_only=bool(tc_raw.get("resource_estimation_only", False)),
        cast_model=TCQSCICastModelSpec(
            kind=str(cast_raw.get("kind", "identity")),
            npz_path=(
                str(resolve_user_path(base_dir, str(cast_raw["npz_path"])))
                if cast_raw.get("npz_path") is not None
                else None
            ),
        ),
        initial_state=TCQSCIInitialStateSpec(
            kind=str(initial_raw.get("kind", "hf")),
            max_determinants=(
                int(initial_raw["max_determinants"])
                if initial_raw.get("max_determinants") is not None
                else None
            ),
            determinants=[dict(item) for item in determinants_raw],
        ),
        kick=TCQSCIKickSpec(
            time=float(kick_raw.get("time", 0.05)),
            num_kicks=int(kick_raw.get("num_kicks", 1)),
            pauli_term_budget=(
                int(kick_raw["pauli_term_budget"])
                if kick_raw.get("pauli_term_budget") is not None
                else None
            ),
            shots=int(kick_raw.get("shots", 1024)),
        ),
        selection=TCQSCISelectionSpec(
            max_determinants=int(selection_raw.get("max_determinants", 64)),
            min_count=int(selection_raw.get("min_count", 1)),
            symmetry_postselect=bool(selection_raw.get("symmetry_postselect", True)),
        ),
        resource_estimation=TCQSCIResourceEstimationSpec(
            enabled=bool(resource_raw.get("enabled", True)),
            target_precision=float(resource_raw.get("target_precision", 1.0e-3)),
        ),
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


def _parse_hardware_optimization(raw: dict[str, Any]) -> HardwareOptimizationSpec:
    hardware_raw = raw.get("hardware_optimization")
    if not isinstance(hardware_raw, dict):
        return HardwareOptimizationSpec()
    defaults = HardwareOptimizationSpec()
    return HardwareOptimizationSpec(
        enabled=bool(hardware_raw.get("enabled", False)),
        profile=str(hardware_raw.get("profile", defaults.profile)),
        max_real_jobs=int(hardware_raw.get("max_real_jobs", defaults.max_real_jobs)),
        max_total_budgeted_shots=int(
            hardware_raw.get("max_total_budgeted_shots", defaults.max_total_budgeted_shots)
        ),
        max_total_estimated_quantum_seconds=(
            float(hardware_raw["max_total_estimated_quantum_seconds"])
            if hardware_raw.get("max_total_estimated_quantum_seconds") is not None
            else defaults.max_total_estimated_quantum_seconds
        ),
        stop_if_error_below=float(hardware_raw.get("stop_if_error_below", defaults.stop_if_error_below)),
        candidate_strategies=[
            str(item) for item in hardware_raw.get("candidate_strategies", defaults.candidate_strategies)
        ],
        selection_metric=str(hardware_raw.get("selection_metric", defaults.selection_metric)),
        requires_confirmation=bool(hardware_raw.get("requires_confirmation", defaults.requires_confirmation)),
    )


def load_run_spec(path: Path) -> RunSpec:
    """Load a QCchem run specification from YAML."""
    resolved_path = path if path.is_absolute() else _resolve_path(Path.cwd(), str(path))
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Run configuration must deserialize to a mapping.")

    molecule_raw = _require_mapping(raw, "molecule")

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
        molecule=_parse_molecule(molecule_raw, base_dir=resolved_path.parent),
        problem=ProblemSpec(
            active_space=_parse_active_space(problem_raw),
            freeze_core=bool(problem_raw.get("freeze_core", False)),
            remove_orbitals=[int(value) for value in problem_raw.get("remove_orbitals", [])],
            compression=_parse_compression(problem_raw),
            measurement=_parse_measurement(problem_raw),
            embedding=_parse_embedding(problem_raw),
            external_point_charges=_parse_external_point_charges(
                problem_raw,
                base_dir=resolved_path.parent,
            ),
            environment_embedding=_parse_environment_embedding(
                problem_raw,
                base_dir=resolved_path.parent,
            ),
            pbc=_parse_pbc(problem_raw),
            qft=_parse_lattice_qed(problem_raw),
            cavity_qed=_parse_cavity_qed(problem_raw),
            point_group=_parse_point_group(problem_raw),
        ),
        mapping=_parse_mapping(raw),
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
            lr_ace_adaptive=_parse_lr_ace_adaptive(solver_raw),
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
            geometry_optimization=_parse_geometry_optimization(tasks_raw),
            gradient=_parse_gradient(tasks_raw),
            response_properties=_parse_response_properties(tasks_raw),
        ),
        tc_qsci=_parse_tc_qsci(raw, base_dir=resolved_path.parent),
        hardware_optimization=_parse_hardware_optimization(raw),
        run=RunConfig(
            seed=int(run_raw.get("seed", 7)),
            output_dir=Path(run_raw.get("output_dir", "artifacts")),
            overwrite=bool(run_raw.get("overwrite", False)),
            exports=_parse_artifact_exports(run_raw),
        ),
    )
