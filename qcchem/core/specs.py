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
class EmbeddingSpec:
    """Embedding/fragmentation workflow configuration."""

    enabled: bool = False
    method: str = "dmet_skeleton"
    bath_threshold: float = 0.05
    solver_plugin: str = "placeholder_fragment_solver"
    fragments: list[FragmentSpec] = field(default_factory=list)


@dataclass(slots=True)
class ProblemSpec:
    """Electronic-structure problem configuration."""

    active_space: ActiveSpaceSpec | None = None
    freeze_core: bool = False
    remove_orbitals: list[int] = field(default_factory=list)
    compression: CompressionSpec = field(default_factory=CompressionSpec)
    measurement: MeasurementSpec = field(default_factory=MeasurementSpec)
    embedding: EmbeddingSpec = field(default_factory=EmbeddingSpec)


@dataclass(slots=True)
class MappingSpec:
    """Fermion-to-qubit mapping configuration."""

    kind: str = "jordan_wigner"


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
class SolverSpec:
    """Solver configuration."""

    kind: str = "vqe"
    optimizer: OptimizerSpec = field(default_factory=OptimizerSpec)
    ansatz: AnsatzSpec = field(default_factory=AnsatzSpec)
    initial_point: str | list[float] = "zeros"
    experimental: bool = False


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
class TaskSpec:
    """Optional chemistry tasks attached to a run."""

    excited_state: ExcitedStateTaskSpec = field(default_factory=ExcitedStateTaskSpec)
    properties: list[PropertyTaskSpec] = field(default_factory=list)
    perturbative_correction: PerturbativeCorrectionTaskSpec = field(
        default_factory=PerturbativeCorrectionTaskSpec
    )


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
class CampaignSpec:
    """A higher-level grouping of studies."""

    name: str
    studies: list[Path] = field(default_factory=list)
    description: str = ""


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


@dataclass(slots=True)
class ScanParameterSpec:
    """1D scan parameter specification."""

    name: str
    kind: str
    atom_indices: tuple[int, int]
    values: list[float]
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)


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
