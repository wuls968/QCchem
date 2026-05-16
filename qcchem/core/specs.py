"""Configuration specifications owned by QCchem."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AtomSpec:
    """One atom in a molecular geometry."""

    symbol: str
    coords: tuple[float, float, float]


@dataclass(slots=True)
class MoleculeSpec:
    """User-facing molecular input."""

    name: str
    geometry: list[AtomSpec]
    charge: int = 0
    multiplicity: int = 1
    basis: str = "sto3g"
    unit: str = "angstrom"

    @property
    def spin(self) -> int:
        """Return the 2S spin value expected by PySCF/Qiskit Nature."""
        return self.multiplicity - 1

    def geometry_string(self) -> str:
        """Render geometry to the format expected by PySCFDriver."""
        return "; ".join(
            f"{atom.symbol} {atom.coords[0]} {atom.coords[1]} {atom.coords[2]}"
            for atom in self.geometry
        )


@dataclass(slots=True)
class AutoActiveSpaceSpec:
    """Automatic active-space recommendation settings."""

    enabled: bool = False
    strategy: str = "frontier_orbitals"
    num_occupied: int = 1
    num_virtual: int = 1


@dataclass(slots=True)
class ActiveSpaceSpec:
    """Active-space reduction specification."""

    num_electrons: int | tuple[int, int] | None = None
    num_spatial_orbitals: int | None = None
    active_orbitals: list[int] | tuple[list[int], list[int]] | None = None
    selection_mode: str = "manual"
    auto: AutoActiveSpaceSpec = field(default_factory=AutoActiveSpaceSpec)


@dataclass(slots=True)
class CompressionSpec:
    """Low-rank Hamiltonian compression settings."""

    enabled: bool = False
    method: str = "modified_cholesky"
    threshold: float = 1.0e-8
    max_rank: int | None = None
    rank_schedule: list[int] | None = None
    term_budget_policy: str = "precision_first"
    compression_error_budget_hartree: float = 8.0e-4
    allow_pauli_truncation: bool = False
    runtime_term_budget: int | None = None
    apply_to_solver: bool = False
    execution_enabled: bool = False


@dataclass(slots=True)
class MeasurementSpec:
    """Measurement-planning configuration, including low-rank-aware execution hints."""

    strategy: str = "default"
    runtime_precision_target: float | None = None
    execution_mode: str = "estimator"
    grouping_policy: str = "default"


@dataclass(slots=True)
class FragmentSpec:
    """One fragment used by an embedding or fragmentation workflow."""

    name: str
    atom_indices: list[int] = field(default_factory=list)


@dataclass(slots=True)
class EmbeddingExecutionSpec:
    """Optional fragment execution settings for embedding workflows."""

    enabled: bool = False
    plugin: str = "pyscf_rhf_fragment"
    validate_against_full_system: bool = True


@dataclass(slots=True)
class EmbeddingSpec:
    """Embedding/fragmentation workflow configuration."""

    enabled: bool = False
    method: str = "dmet_skeleton"
    bath_threshold: float = 0.05
    solver_plugin: str = "placeholder_fragment_solver"
    fragments: list[FragmentSpec] = field(default_factory=list)
    execution: EmbeddingExecutionSpec = field(default_factory=EmbeddingExecutionSpec)


@dataclass(slots=True)
class PointChargeSpec:
    """One fixed external point charge used for electrostatic embedding."""

    label: str | None
    coords: tuple[float, float, float]
    charge: float


@dataclass(slots=True)
class ExternalPointChargeSpec:
    """Static external point-charge electrostatic embedding configuration."""

    enabled: bool = False
    unit: str | None = None
    source_file: Path | None = None
    charges: list[PointChargeSpec] = field(default_factory=list)
    min_distance_to_qm_atoms: float = 1.0e-6


@dataclass(slots=True)
class PointChargeDampingSpec:
    """Damping model for classical environment charges."""

    kind: str = "gaussian"
    default_radius: float | None = 0.40
    radius_unit: str = "angstrom"
    min_radius: float = 0.15
    overpolarization_warning_potential_au: float = 2.0


@dataclass(slots=True)
class EnvironmentPointChargeSpec:
    """Point-charge source used by the effective environment Hamiltonian path."""

    enabled: bool = False
    unit: str | None = None
    source_file: Path | None = None
    charges: list[PointChargeSpec] = field(default_factory=list)
    min_distance_to_qm_atoms: float = 1.0e-6
    damping: PointChargeDampingSpec = field(default_factory=PointChargeDampingSpec)


@dataclass(slots=True)
class BoundaryCutBondSpec:
    """One declared QM/MM covalent boundary crossing."""

    label: str | None
    qm_atom: int
    mm_atom: int


@dataclass(slots=True)
class BoundaryEmbeddingSpec:
    """Localized-boundary-orbital audit and correction settings."""

    enabled: bool = False
    method: str = "localized_orbital_freeze_project_downfold"
    localization: str = "iao_lowdin"
    cut_bonds: list[BoundaryCutBondSpec] = field(default_factory=list)
    leakage_threshold: float = 0.05
    strict: bool = True


@dataclass(slots=True)
class EffectiveHamiltonianCacheSpec:
    """Cache policy for generated environment effective-Hamiltonian artifacts."""

    enabled: bool = True
    directory: Path = Path("artifacts/effective_hamiltonians")
    refresh: bool = False


@dataclass(slots=True)
class EnvironmentEmbeddingSpec:
    """Quantum-algorithm-oriented classical-environment embedding."""

    enabled: bool = False
    mode: str = "effective_hamiltonian"
    point_charges: EnvironmentPointChargeSpec = field(
        default_factory=EnvironmentPointChargeSpec
    )
    boundary: BoundaryEmbeddingSpec = field(default_factory=BoundaryEmbeddingSpec)
    cache: EffectiveHamiltonianCacheSpec = field(
        default_factory=EffectiveHamiltonianCacheSpec
    )


@dataclass(slots=True)
class LatticeQEDGridSpec:
    """Real-space grid settings for exploratory lattice-QED models."""

    shape: list[int] = field(default_factory=lambda: [2])
    spacing: list[float] = field(default_factory=lambda: [1.0])
    origin: str = "molecule_center"
    axes: str = "principal"
    boundary: str = "open"
    softening: float = 0.35


@dataclass(slots=True)
class LatticeQEDMatterSpec:
    """Matter-field settings for exploratory lattice-QED models."""

    spin_components: int = 2
    target_electrons: str | int = "auto"
    include_soft_coulomb_density: bool = False


@dataclass(slots=True)
class LatticeQEDGaugeSpec:
    """Gauge-field settings for exploratory compact U(1) lattice QED."""

    group: str = "u1"
    electric_cutoff: int = 1
    coupling: float = 1.0
    include_magnetic_plaquettes: bool = True


@dataclass(slots=True)
class LatticeQEDConstraintSpec:
    """Penalty terms used to keep finite lattice-QED calculations auditable."""

    gauss_law_penalty: float = 10.0
    particle_number_penalty: float = 10.0
    padding_penalty: float = 50.0
    enforce_physical_sector: bool = False
    target_charge_sector: str = "neutral"
    gauss_law_tolerance: float = 1.0e-8
    max_sector_enumeration_qubits: int = 10


@dataclass(slots=True)
class LatticeQEDAnsatzSpec:
    """Gauge-aware ansatz settings for exploratory lattice-QED solvers."""

    generator_policy: str = "gauge_invariant_hopping"


@dataclass(slots=True)
class LatticeQEDEngineSpec:
    """Operator-representation settings for exploratory lattice-QED engines."""

    representation: str = "auto"
    auto_project_physical_sector: bool = True
    max_projected_dimension: int = 4096
    max_full_qubits_for_dense: int = 10
    materialize_pauli: str = "auto"
    store_basis_indices: str = "preview"
    projector_tolerance: float = 1.0e-8


@dataclass(slots=True)
class LatticeQEDDynamicsInitialStateSpec:
    """Initial-state preparation for QFT real-time dynamics."""

    kind: str = "local_hopping_pulse"
    base: str = "physical_reference"
    link_index: int = 0
    pulse_time: float = 0.05
    pulse_strength: float = 1.0


@dataclass(slots=True)
class LatticeQEDDynamicsTimeGridSpec:
    """Time grid for QFT real-time dynamics."""

    start: float = 0.0
    stop: float = 2.0
    num_points: int = 41


@dataclass(slots=True)
class LatticeQEDDynamicsEvolutionSpec:
    """Exact and Trotter evolution settings for QFT dynamics."""

    exact_enabled: bool = True
    exact_qubit_limit: int = 12
    trotter_enabled: bool = True
    trotter_step: float = 0.05
    trotter_order: int = 1


@dataclass(slots=True)
class LatticeQEDDynamicsRuntimeSpec:
    """Guarded runtime batch settings for QFT dynamics."""

    enabled: bool = False
    runtime_observables: str = "aggregate_gauge"


@dataclass(slots=True)
class LatticeQEDDynamicsSpec:
    """Exploratory real-time lattice-QED dynamics task configuration."""

    enabled: bool = False
    method: str = "real_time_quench"
    initial_state: LatticeQEDDynamicsInitialStateSpec = field(
        default_factory=LatticeQEDDynamicsInitialStateSpec
    )
    time_grid: LatticeQEDDynamicsTimeGridSpec = field(
        default_factory=LatticeQEDDynamicsTimeGridSpec
    )
    evolution: LatticeQEDDynamicsEvolutionSpec = field(
        default_factory=LatticeQEDDynamicsEvolutionSpec
    )
    runtime: LatticeQEDDynamicsRuntimeSpec = field(default_factory=LatticeQEDDynamicsRuntimeSpec)


@dataclass(slots=True)
class LatticeQEDSpec:
    """Exploratory real-space lattice-QED field model configuration."""

    enabled: bool = False
    model: str = "lattice_qed_minimal_coupling"
    dimensions: int = 1
    grid: LatticeQEDGridSpec = field(default_factory=LatticeQEDGridSpec)
    matter: LatticeQEDMatterSpec = field(default_factory=LatticeQEDMatterSpec)
    gauge: LatticeQEDGaugeSpec = field(default_factory=LatticeQEDGaugeSpec)
    constraints: LatticeQEDConstraintSpec = field(default_factory=LatticeQEDConstraintSpec)
    ansatz: LatticeQEDAnsatzSpec = field(default_factory=LatticeQEDAnsatzSpec)
    engine: LatticeQEDEngineSpec = field(default_factory=LatticeQEDEngineSpec)
    dynamics: LatticeQEDDynamicsSpec = field(default_factory=LatticeQEDDynamicsSpec)


@dataclass(slots=True)
class CavityQEDModeSpec:
    """Single photon-mode settings for Pauli-Fierz cavity-QED models."""

    frequency: float = 0.4
    coupling_strength: float = 0.05
    polarization: list[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    max_occupation: int = 1


@dataclass(slots=True)
class CavityQEDSpec:
    """Molecular Pauli-Fierz cavity-QED model configuration."""

    enabled: bool = False
    model: str = "pauli_fierz_cavity_qed"
    photon_encoding: str = "linear"
    include_dipole_self_energy: bool = True
    photon_physical_subspace_penalty: float = 25.0
    modes: list[CavityQEDModeSpec] = field(default_factory=lambda: [CavityQEDModeSpec()])


@dataclass(slots=True)
class PointGroupSpec:
    """Point-group symmetry audit and explicit irrep filtering settings."""

    subgroup: str = "auto"
    reduction_mode: str = "audit"
    active_irreps: list[str] = field(default_factory=list)
    remove_irreps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProblemSpec:
    """Electronic-structure problem configuration."""

    active_space: ActiveSpaceSpec | None = None
    freeze_core: bool = False
    remove_orbitals: list[int] = field(default_factory=list)
    compression: CompressionSpec = field(default_factory=CompressionSpec)
    measurement: MeasurementSpec = field(default_factory=MeasurementSpec)
    embedding: EmbeddingSpec = field(default_factory=EmbeddingSpec)
    external_point_charges: ExternalPointChargeSpec = field(
        default_factory=ExternalPointChargeSpec
    )
    environment_embedding: EnvironmentEmbeddingSpec = field(
        default_factory=EnvironmentEmbeddingSpec
    )
    qft: LatticeQEDSpec = field(default_factory=LatticeQEDSpec)
    cavity_qed: CavityQEDSpec = field(default_factory=CavityQEDSpec)
    point_group: PointGroupSpec = field(default_factory=PointGroupSpec)


@dataclass(slots=True)
class MappingSymmetryReductionSpec:
    """Fermion-to-qubit symmetry-reduction policy."""

    z2: str = "auto"
    point_group: str = "auto"
    strict: bool = False


@dataclass(slots=True)
class MappingSpec:
    """Fermion-to-qubit mapping configuration."""

    kind: str = "jordan_wigner"
    symmetry_reduction: MappingSymmetryReductionSpec = field(default_factory=MappingSymmetryReductionSpec)


@dataclass(slots=True)
class NoiseModelSpec:
    """Local noise-model configuration for Aer-backed execution."""

    enabled: bool = False
    profile: str = "none"
    depolarizing_probability_1q: float = 0.0
    depolarizing_probability_2q: float = 0.0
    readout_error_probability: float = 0.0
    basis_gates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RuntimeOptionsSpec:
    """Runtime/session/batch readiness metadata and options snapshot."""

    enabled: bool = False
    service: str = "local"
    instance: str | None = None
    runtime_ready: bool = False
    session_ready: bool = False
    batch_ready: bool = False
    precision_target: float | None = None
    max_budgeted_shots: int | None = None
    max_execution_seconds: float | None = None
    calibration_strategy: str = "default"
    resilience_level: int | None = None
    grouping_policy: str = "default"
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackendSpec:
    """Execution backend configuration."""

    kind: str = "statevector"
    shots: int | None = None
    precision: float | None = None
    seed: int | None = None
    repetitions: int = 1
    abelian_grouping: bool = True
    noise: NoiseModelSpec = field(default_factory=NoiseModelSpec)
    runtime: RuntimeOptionsSpec = field(default_factory=RuntimeOptionsSpec)


@dataclass(slots=True)
class OptimizerSpec:
    """Classical optimizer configuration for variational solvers."""

    kind: str = "COBYLA"
    maxiter: int = 100
    tol: float | None = None


@dataclass(slots=True)
class AnsatzSpec:
    """Parameterized circuit specification."""

    kind: str = "twolocal"
    rotation_blocks: list[str] = field(default_factory=lambda: ["ry", "rz"])
    entanglement_blocks: str = "cz"
    entanglement: str = "full"
    reps: int = 2
    skip_final_rotation_layer: bool = False


@dataclass(slots=True)
class LRACEAdaptiveSpec:
    """Adaptive budget and trust-gate settings for exploratory LR-ACE."""

    enabled: bool = False
    generator_schedule: list[int] = field(default_factory=lambda: [8, 16, 24, 32])
    optimizer_maxiter_schedule: list[int] = field(default_factory=lambda: [1000, 2000, 5000])
    initial_point_strategies: list[str] = field(default_factory=lambda: ["zeros", "random"])
    random_restarts: int = 3
    target_error_hartree: float = 1.6e-3
    max_wall_time_seconds: float = 1200.0
    uncompressed_check_qubit_limit: int = 12
    candidate_pool_policy: str = "residual_guided"
    candidate_scan_limit: int = 64
    residual_batch_size: int = 8
    residual_scan_angles: list[float] = field(default_factory=lambda: [-0.15, -0.05, 0.05, 0.15])
    min_energy_improvement_hartree: float = 2.0e-4
    max_adaptive_expansions: int = 3


@dataclass(slots=True)
class SolverSpec:
    """Solver configuration."""

    kind: str = "vqe"
    optimizer: OptimizerSpec = field(default_factory=OptimizerSpec)
    ansatz: AnsatzSpec = field(default_factory=AnsatzSpec)
    initial_point: str | list[float] = "zeros"
    experimental: bool = False
    lr_ace_adaptive: LRACEAdaptiveSpec = field(default_factory=LRACEAdaptiveSpec)


@dataclass(slots=True)
class BenchmarkSpec:
    """Exact-baseline and regression threshold configuration."""

    enabled: bool = True
    exact_baseline_qubit_limit: int = 12
    absolute_error_threshold: float = 1.0e-3
    relative_error_threshold: float = 1.0e-3


@dataclass(slots=True)
class SymmetryCheckSpec:
    """Symmetry-based mitigation hook configuration."""

    enabled: bool = False
    strategy: str = "placeholder"


@dataclass(slots=True)
class ReadoutMitigationSpec:
    """Readout mitigation placeholder configuration."""

    enabled: bool = False
    method: str = "none"


@dataclass(slots=True)
class ZNESpec:
    """Zero-noise extrapolation placeholder configuration."""

    enabled: bool = False
    method: str = "placeholder"


@dataclass(slots=True)
class PECSpec:
    """Probabilistic error cancellation placeholder configuration."""

    enabled: bool = False
    method: str = "placeholder"


@dataclass(slots=True)
class MitigationSpec:
    """Mitigation configuration placeholders for future execution realism work."""

    symmetry_check: SymmetryCheckSpec = field(default_factory=SymmetryCheckSpec)
    readout: ReadoutMitigationSpec = field(default_factory=ReadoutMitigationSpec)
    zne: ZNESpec = field(default_factory=ZNESpec)
    pec: PECSpec = field(default_factory=PECSpec)
    experimental: bool = False


@dataclass(slots=True)
class PolicySpec:
    """Execution-policy selection and intent."""

    name: str = "benchmark"
    allow_exploratory: bool = False


@dataclass(slots=True)
class ExploratorySpec:
    """Explicit opt-in for exploratory modules and workflows."""

    enabled: bool = False
    modules: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExcitedStateTaskSpec:
    """Excited-state task request."""

    enabled: bool = False
    method: str = "exact_spectrum"
    num_states: int = 2
    state_indices: list[int] = field(default_factory=lambda: [1])


@dataclass(slots=True)
class PropertyTaskSpec:
    """One chemistry property request."""

    property_name: str
    enabled: bool = True
    method: str = "exact_expectation"
    state_indices: list[int] = field(default_factory=lambda: [0])


@dataclass(slots=True)
class PerturbativeCorrectionTaskSpec:
    """Perturbative correction request."""

    enabled: bool = False
    method: str = "nevpt2"
    plugin: str = "pyscf"
    root: int = 0


@dataclass(slots=True)
class GeometryOptimizationTaskSpec:
    """Classical geometry optimization reference task."""

    enabled: bool = False
    method: str = "pyscf_rhf"
    max_steps: int = 50
    gradient_tolerance: float = 3.0e-4


@dataclass(slots=True)
class GradientTaskSpec:
    """Classical nuclear-gradient reference task."""

    enabled: bool = False
    method: str = "pyscf_rhf"
    state_index: int = 0


@dataclass(slots=True)
class ResponsePropertyTaskSpec:
    """Response-property task bundle."""

    enabled: bool = False
    properties: list[str] = field(default_factory=lambda: ["static_polarizability"])
    method: str = "finite_field_rhf"
    finite_field_step: float = 1.0e-3


@dataclass(slots=True)
class TaskSpec:
    """Optional chemistry tasks attached to a run."""

    excited_state: ExcitedStateTaskSpec = field(default_factory=ExcitedStateTaskSpec)
    properties: list[PropertyTaskSpec] = field(default_factory=list)
    perturbative_correction: PerturbativeCorrectionTaskSpec = field(
        default_factory=PerturbativeCorrectionTaskSpec
    )
    geometry_optimization: GeometryOptimizationTaskSpec = field(
        default_factory=GeometryOptimizationTaskSpec
    )
    gradient: GradientTaskSpec = field(default_factory=GradientTaskSpec)
    response_properties: ResponsePropertyTaskSpec = field(default_factory=ResponsePropertyTaskSpec)


@dataclass(slots=True)
class TCQSCICastModelSpec:
    """CAST-QC Hamiltonian plugin configuration for TC-kicked QSCI."""

    kind: str = "identity"
    npz_path: str | None = None


@dataclass(slots=True)
class TCQSCIInitialStateSpec:
    """Initial determinant-state configuration for TC-kicked QSCI."""

    kind: str = "hf"
    max_determinants: int | None = None
    determinants: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TCQSCIKickSpec:
    """Short-time kicking and sampling configuration for TC-kicked QSCI."""

    time: float = 0.05
    num_kicks: int = 1
    pauli_term_budget: int | None = None
    shots: int = 1024


@dataclass(slots=True)
class TCQSCISelectionSpec:
    """Selected determinant subspace policy for TC-kicked QSCI."""

    max_determinants: int = 64
    min_count: int = 1
    symmetry_postselect: bool = True


@dataclass(slots=True)
class TCQSCIResourceEstimationSpec:
    """Coarse resource-estimation options for TC-kicked QSCI."""

    enabled: bool = True
    target_precision: float = 1.0e-3


@dataclass(slots=True)
class TCQSCISpec:
    """Exploratory TC-kicked QSCI workflow configuration."""

    enabled: bool = False
    resource_estimation_only: bool = False
    cast_model: TCQSCICastModelSpec = field(default_factory=TCQSCICastModelSpec)
    initial_state: TCQSCIInitialStateSpec = field(default_factory=TCQSCIInitialStateSpec)
    kick: TCQSCIKickSpec = field(default_factory=TCQSCIKickSpec)
    selection: TCQSCISelectionSpec = field(default_factory=TCQSCISelectionSpec)
    resource_estimation: TCQSCIResourceEstimationSpec = field(default_factory=TCQSCIResourceEstimationSpec)


@dataclass(slots=True)
class HardwareOptimizationSpec:
    """Budget-guarded hardware precision optimization settings."""

    enabled: bool = False
    profile: str = "h2_precision_push"
    max_real_jobs: int = 3
    max_total_budgeted_shots: int = 40_960
    max_total_estimated_quantum_seconds: float | None = 600.0
    stop_if_error_below: float = 1.6e-3
    candidate_strategies: list[str] = field(
        default_factory=lambda: [
            "jw_puccd_layout_baseline",
            "parity_puccd_layout",
            "parity_succd_layout",
            "parity_uccsd_layout",
        ]
    )
    selection_metric: str = "accuracy_then_cost"
    requires_confirmation: bool = True


@dataclass(slots=True)
class RunConfig:
    """Run-level execution and artifact options."""

    seed: int = 7
    output_dir: Path = Path("artifacts")
    overwrite: bool = False
    exports: "ArtifactExportSpec" = field(default_factory=lambda: ArtifactExportSpec())


@dataclass(slots=True)
class ArtifactExportSpec:
    """Optional interoperability and provenance exports."""

    qcschema_json: bool = False
    hdf5: bool = False


@dataclass(slots=True)
class RunSpec:
    """Root specification for one QCchem calculation."""

    molecule: MoleculeSpec
    problem: ProblemSpec = field(default_factory=ProblemSpec)
    mapping: MappingSpec = field(default_factory=MappingSpec)
    backend: BackendSpec = field(default_factory=BackendSpec)
    solver: SolverSpec = field(default_factory=SolverSpec)
    benchmark: BenchmarkSpec = field(default_factory=BenchmarkSpec)
    mitigation: MitigationSpec = field(default_factory=MitigationSpec)
    policy: PolicySpec = field(default_factory=PolicySpec)
    exploratory: ExploratorySpec = field(default_factory=ExploratorySpec)
    tasks: TaskSpec = field(default_factory=TaskSpec)
    tc_qsci: TCQSCISpec = field(default_factory=TCQSCISpec)
    hardware_optimization: HardwareOptimizationSpec = field(default_factory=HardwareOptimizationSpec)
    run: RunConfig = field(default_factory=RunConfig)


@dataclass(slots=True)
class StudyRunSpec:
    """One run entry within a study."""

    name: str
    config: Path
    overrides: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StudySpec:
    """A collection of related runs composing one study."""

    name: str
    description: str = ""
    registry_name: str | None = None
    policy_name: str | None = None
    runs: list[StudyRunSpec] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CampaignEntrySpec:
    """One entry in a trust-loop campaign workflow."""

    name: str
    kind: str
    config: Path | None = None
    artifact: Path | None = None
    output_dir: Path | None = None
    allow_runtime_submission: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CampaignSpec:
    """A higher-level grouping of artifact-producing workflows."""

    name: str
    entries: list[CampaignEntrySpec] = field(default_factory=list)
    description: str = ""
    output_root: Path = Path("artifacts/campaign")
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BenchmarkAcceptanceSpec:
    """Benchmark-suite acceptance policy."""

    enabled: bool = True
    required_files: list[str] = field(default_factory=lambda: ["result.json"])
    require_evidence_summary: bool = True
    require_runtime_sidecar_for_hardware_verified: bool = True
    fail_on_runtime_accuracy_promotion: bool = True
    strict_exit_code: bool = True


@dataclass(slots=True)
class BenchmarkCaseSpec:
    """One case inside a benchmark suite."""

    name: str
    kind: str
    config: Path | None = None
    overrides: dict[str, Any] = field(default_factory=dict)
    expected_status: str = "validated"
    shots: list[int] = field(default_factory=list)
    optimizers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BenchmarkSuiteSpec:
    """Top-level benchmark suite specification."""

    name: str
    description: str = ""
    registry_name: str | None = None
    cases: list[BenchmarkCaseSpec] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    acceptance: BenchmarkAcceptanceSpec = field(default_factory=BenchmarkAcceptanceSpec)


@dataclass(slots=True)
class ScanParameterSpec:
    """1D scan parameter specification."""

    name: str
    kind: str
    values: list[float]
    atom_indices: tuple[int, int] = (0, 1)
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    target: str | None = None


@dataclass(slots=True)
class ScanSpec:
    """Potential-energy-scan specification."""

    name: str
    description: str = ""
    base_config: Path = Path("configs/h2.yaml")
    parameter: ScanParameterSpec = field(
        default_factory=lambda: ScanParameterSpec(
            name="bond_length",
            kind="bond_distance",
            atom_indices=(0, 1),
            values=[0.7, 0.9, 1.1],
        )
    )
    policy_name: str | None = None
    tags: list[str] = field(default_factory=list)
