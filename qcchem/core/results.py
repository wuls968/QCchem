"""Result models for QCchem runs and aggregate workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class BaselineDescriptorSummary:
    """Descriptor for the primary baseline used by an evidence summary."""

    baseline_kind: str
    baseline_source: str | None
    baseline_scope: str
    baseline_strength: str


@dataclass(slots=True)
class EvidenceSummary:
    """Cross-surface evidence summary consumed by UI, reports, and AI tools."""

    result_identity: dict[str, Any]
    primary_scientific_claim: str
    primary_baseline: BaselineDescriptorSummary
    primary_error_metric: dict[str, Any]
    chemical_accuracy_status: str
    runtime_evidence_status: str
    trust_tier: str
    recommended_action: str
    energy_evidence: dict[str, Any] = field(default_factory=dict)
    comparison_evidence: dict[str, Any] = field(default_factory=dict)
    execution_evidence: dict[str, Any] = field(default_factory=dict)
    trust_judgment: dict[str, Any] = field(default_factory=dict)
    scientific_accuracy: dict[str, Any] = field(default_factory=dict)
    runtime_derived_accuracy: dict[str, Any] = field(default_factory=dict)
    decision_worthiness: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EnergyResult:
    """Energy values exposed to users and persisted to artifacts."""

    solver_energy: float
    constant_energy_correction: float
    electronic_energy: float
    nuclear_repulsion_energy: float
    external_point_charge_nuclear_interaction_energy: float
    boundary_embedding_constant_energy: float
    total_energy: float
    hf_reference_energy: float | None
    exact_ground_energy: float | None
    correlation_energy: float | None
    energy_units: str
    energy_formula: str


@dataclass(slots=True)
class ExactBaselineSummary:
    """Exact diagonalization baseline persisted as a standalone artifact."""

    available: bool
    solver_hamiltonian_energy: float | None
    electronic_energy: float | None
    total_energy: float | None
    energy_units: str
    source: str = "exact_diagonalization"


@dataclass(slots=True)
class SampledResultSummary:
    """Shot-based post-optimization sampling summary."""

    available: bool
    backend_kind: str
    shots: int | None
    num_repeats: int
    seed: int | None
    repeat_seeds: list[int | None] = field(default_factory=list)
    repeat_solver_energies: list[float] = field(default_factory=list)
    repeat_reported_stds: list[float] = field(default_factory=list)
    repeat_metadata: list[dict[str, object]] = field(default_factory=list)
    sampled_solver_energy_mean: float | None = None
    sampled_solver_energy_std: float | None = None
    sampled_electronic_energy_mean: float | None = None
    sampled_total_energy_mean: float | None = None
    standard_error: float | None = None
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None


@dataclass(slots=True)
class VariationalResultSummary:
    """Summary of the variational optimization stage."""

    available: bool
    solver_kind: str
    optimizer: dict[str, object]
    ansatz: dict[str, object]
    initial_point_strategy: str
    parameter_count: int
    converged: bool
    iterations: int
    evaluations: int
    optimal_parameters: list[float] = field(default_factory=list)
    final_objective_energy: float | None = None
    optimizer_message: str | None = None
    initial_point_provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkSummary:
    """Exact-baseline comparison summary for a run."""

    exact_available: bool
    comparison_target: str
    absolute_error: float | None
    relative_error: float | None
    statistical_error: float | None
    absolute_error_threshold: float
    relative_error_threshold: float
    within_uncertainty: bool | None
    meets_threshold: bool | None
    exact_electronic_energy: float | None = None
    exact_total_energy: float | None = None
    compressed_vs_uncompressed: "CompressedExecutionComparisonSummary | None" = None


@dataclass(slots=True)
class CompressedExecutionComparisonSummary:
    """Comparison between compressed and uncompressed execution paths."""

    available: bool
    method: str
    rank: int
    threshold: float
    pre_term_count: int
    post_term_count: int
    compressed_solver_energy: float
    uncompressed_solver_energy: float
    compressed_total_energy: float
    uncompressed_total_energy: float
    absolute_error: float
    relative_error: float
    compressed_solve_wall_time_seconds: float
    uncompressed_solve_wall_time_seconds: float


@dataclass(slots=True)
class MappingSummary:
    """Summary of the mapped qubit Hamiltonian."""

    kind: str
    num_qubits: int
    fermionic_term_count: int
    qubit_term_count: int
    raw_num_qubits: int | None = None
    raw_qubit_term_count: int | None = None
    symmetry_tapered_qubits: int = 0
    z2_symmetry_count: int = 0
    z2_tapering_values: list[int] | None = None
    symmetry_reduction_status: str = "disabled"
    symmetry_reduction_notes: list[str] = field(default_factory=list)
    symmetry_reduction_validation: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ProblemSummary:
    """Human-readable chemistry problem summary."""

    molecule_name: str
    basis: str
    charge: int
    multiplicity: int
    num_particles: tuple[int, int]
    num_spatial_orbitals: int
    active_space_metadata: dict[str, object] | None = None
    transformers_applied: list[str] = field(default_factory=list)
    hamiltonian_constants: dict[str, float] = field(default_factory=dict)
    electronic_constant_correction: float = 0.0
    point_group_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReductionAuditSummary:
    """Audit of problem-reduction and constant-energy bookkeeping."""

    original_num_particles: tuple[int, int]
    original_num_spatial_orbitals: int
    reduced_num_particles: tuple[int, int]
    reduced_num_spatial_orbitals: int
    transformers_applied: list[str] = field(default_factory=list)
    active_space_metadata: dict[str, object] | None = None
    selection_mode: str = "none"
    selection_reason: str = ""
    selected_active_orbitals: list[int] = field(default_factory=list)
    selected_active_orbitals_original: list[int] = field(default_factory=list)
    frozen_core_orbitals: list[int] = field(default_factory=list)
    removed_orbitals: list[int] = field(default_factory=list)
    hamiltonian_constants: dict[str, float] = field(default_factory=dict)
    constant_energy_correction: float = 0.0
    nuclear_repulsion_energy: float = 0.0
    external_point_charge_nuclear_interaction_energy: float = 0.0
    boundary_embedding_constant_energy: float = 0.0
    total_constant_correction: float = 0.0
    energy_formula: str = ""
    point_group_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackendSummary:
    """Execution backend summary."""

    kind: str
    shots: int | None = None
    precision: float | None = None
    seed: int | None = None
    repetitions: int = 1
    abelian_grouping: bool = True
    noise_enabled: bool = False
    runtime_enabled: bool = False


@dataclass(slots=True)
class NoiseModelSummary:
    """Persisted noise-model provenance for noisy local execution."""

    enabled: bool
    profile: str
    model_kind: str
    local_simulation: bool
    parameters: dict[str, object] = field(default_factory=dict)
    basis_gates: list[str] = field(default_factory=list)
    provenance: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeOptionsSummary:
    """Runtime/session/batch readiness snapshot."""

    enabled: bool
    service: str
    instance: str | None
    runtime_ready: bool
    session_ready: bool
    batch_ready: bool
    precision_target: float | None = None
    max_budgeted_shots: int | None = None
    max_execution_seconds: float | None = None
    calibration_strategy: str = "default"
    resilience_level: int | None = None
    grouping_policy: str = "default"
    session_recommendation: str | None = None
    batch_recommendation: str | None = None
    low_rank_workload: bool = False
    measurement_group_count: int | None = None
    estimated_shot_cost: float | None = None
    options: dict[str, object] = field(default_factory=dict)
    provenance: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class MeasurementSummary:
    """Measurement-planning summary for the executed Hamiltonian."""

    strategy: str
    group_count: int
    low_rank_aware: bool
    estimated_shot_cost: float
    runtime_precision_target: float | None
    execution_mode: str
    grouping_policy: str = "default"
    term_count: int | None = None
    uncompressed_group_count: int | None = None
    uncompressed_estimated_shot_cost: float | None = None
    cost_reduction_ratio: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ChemicalAccuracySummary:
    """Chemical-accuracy comparison summary."""

    available: bool
    assessment_target: str
    meets_chemical_accuracy: bool | None
    absolute_error_hartree: float | None
    absolute_error_kcal_mol: float | None
    relative_error: float | None
    threshold_hartree: float
    threshold_kcal_mol: float
    statistical_error: float | None = None
    reference_energy: float | None = None
    computed_energy: float | None = None
    status: str = "no_reference"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReductionPlanResult:
    """Reduction planning summary distinct from the executed reduction audit."""

    enabled: bool
    mode: str
    strategy: str
    recommended_changes: dict[str, Any] = field(default_factory=dict)
    reduction_audit: ReductionAuditSummary | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PolicyEngineResult:
    """Resolved policy preset summary."""

    policy_name: str
    resolved_policy: dict[str, Any] = field(default_factory=dict)
    overrides_applied: list[str] = field(default_factory=list)
    presets_used: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CalibrationSummary:
    """Empirical calibration of planned vs observed low-rank execution cost."""

    available: bool
    measured_wall_time_seconds: float
    measured_shot_usage: float | None
    precision_target: float | None
    achieved_error: float | None
    estimated_measurement_cost: float | None
    estimated_vs_measured_cost: float | None
    reference_target: str = "exact_baseline"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RuntimeSubmissionSummary:
    """Runtime submission attempt summary, including real failure boundaries."""

    attempted: bool
    submitted: bool
    succeeded: bool
    service: str
    mode: str
    session_requested: bool
    batch_requested: bool
    options_snapshot: dict[str, Any] = field(default_factory=dict)
    job_id: str | None = None
    session_id: str | None = None
    batch_id: str | None = None
    backend_name: str | None = None
    provider: str | None = None
    layout_strategy: str | None = None
    selected_layout: list[int] = field(default_factory=list)
    layout_score: float | None = None
    transpiled_depth: int | None = None
    transpiled_two_qubit_gate_count: int | None = None
    transpilation_options: dict[str, Any] = field(default_factory=dict)
    submission_wall_time_seconds: float | None = None
    returned_job_metadata: dict[str, Any] = field(default_factory=dict)
    usage_estimation: dict[str, Any] = field(default_factory=dict)
    job_metrics: dict[str, Any] = field(default_factory=dict)
    result_provenance: dict[str, Any] = field(default_factory=dict)
    failure_category: str | None = None
    failure_message: str | None = None
    verification_status: str = "exploratory"


@dataclass(slots=True)
class CompressionResultSummary:
    """Hamiltonian compression and low-rank audit summary."""

    enabled: bool
    method: str
    threshold: float
    rank: int
    max_rank: int | None
    apply_to_solver: bool
    execution_enabled: bool
    original_num_qubits: int
    original_fermionic_term_count: int
    original_qubit_term_count: int
    compressed_term_count_estimate: int
    pre_term_count: int
    post_term_count: int
    primary_rank: int
    secondary_rank: int | None = None
    reconstruction_error_frobenius: float | None = None
    reconstruction_error: float | None = None
    compressed_num_qubits: int | None = None
    verification_status: str = "exploratory"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PerturbativeCorrectionResultSummary:
    """Perturbative correction result, initially NEVPT2-oriented."""

    enabled: bool
    method: str
    plugin: str
    active_space_energy: float
    perturbative_correction: float
    corrected_total_energy: float
    reduced_active_space_energy: float | None = None
    compressed_active_space_energy: float | None = None
    verification_status: str = "exploratory"
    provenance: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EmbeddingResultSummary:
    """Embedding/fragmentation audit and skeleton workflow result."""

    enabled: bool
    method: str
    solver_plugin: str
    bath_threshold: float
    fragments: list[dict[str, Any]] = field(default_factory=list)
    environment_metadata: dict[str, Any] = field(default_factory=dict)
    verification_status: str = "exploratory"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExternalPointChargeSummary:
    """Audit summary for static external point-charge embedding."""

    enabled: bool
    charge_count: int
    total_charge: float
    unit: str
    sources: list[str] = field(default_factory=list)
    source_file_digests: dict[str, str] = field(default_factory=dict)
    min_distance_to_qm_atoms: float | None = None
    min_distance_threshold: float = 1.0e-6
    qm_nuclear_interaction_energy: float = 0.0
    includes_mm_self_energy: bool = False
    adapter_strategy: str = "disabled"
    charges_preview: list[dict[str, Any]] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    risk_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BoundaryEmbeddingSummary:
    """Audit summary for localized boundary-orbital embedding corrections."""

    enabled: bool
    method: str
    localization: str
    cut_bonds: list[dict[str, Any]] = field(default_factory=list)
    leakage_threshold: float = 0.05
    max_boundary_leakage: float | None = None
    selected_boundary_orbitals: list[int] = field(default_factory=list)
    correction_frobenius_norm: float = 0.0
    constant_energy: float = 0.0
    adapter_strategy: str = "disabled"
    verification_status: str = "not_requested"
    provenance: dict[str, Any] = field(default_factory=dict)
    risk_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EffectiveHamiltonianSummary:
    """Audit summary for cached active-space effective Hamiltonians."""

    enabled: bool
    mode: str
    solver_surface: str
    cache_enabled: bool
    cache_hit: bool
    physics_fingerprint: str | None
    cache_fingerprint: str | None
    cache_paths: dict[str, str] = field(default_factory=dict)
    cache_validation: dict[str, Any] = field(default_factory=dict)
    storage_policy: dict[str, Any] = field(default_factory=dict)
    one_body_environment: dict[str, Any] = field(default_factory=dict)
    boundary: BoundaryEmbeddingSummary | None = None
    active_space_projection: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    risk_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BackendCapabilitySummary:
    """Backend capability snapshot persisted with artifacts."""

    backend_kind: str
    statevector: bool
    shot_based: bool
    exact_baseline: bool
    runtime_ready: bool
    session_ready: bool
    batch_ready: bool
    mitigation_ready: bool
    noise_model_ready: bool
    supports_grouping: bool
    supports_repetitions: bool
    supports_confidence_metrics: bool


@dataclass(slots=True)
class ExecutionPolicySummary:
    """Resolved execution-policy snapshot."""

    name: str
    default_shots: int | None
    default_repetitions: int
    exact_baseline_required: bool
    confidence_rule: str
    mitigation_posture: str
    runtime_ready_expected: bool
    session_ready_expected: bool
    batch_ready_expected: bool
    noise_ready_expected: bool


@dataclass(slots=True)
class MitigationSummary:
    """Formal mitigation metadata and hook results."""

    symmetry_check: dict[str, object]
    readout_mitigation: dict[str, object]
    zne: dict[str, object] = field(default_factory=dict)
    pec: dict[str, object] = field(default_factory=dict)
    applied_methods: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExcitedStateLevelResult:
    """One excited-state estimate."""

    state_index: int
    solver_energy: float
    total_energy: float
    excitation_energy: float
    reference_state_index: int
    solver_metadata: dict[str, Any] = field(default_factory=dict)
    baseline: dict[str, Any] = field(default_factory=dict)
    verification_status: str = "exploratory"


@dataclass(slots=True)
class ExcitedStateTaskResult:
    """Excited-state task summary."""

    enabled: bool
    method: str
    states: list[ExcitedStateLevelResult] = field(default_factory=list)
    verification_status: str = "exploratory"
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PropertyValueResult:
    """One property result entry."""

    property_name: str
    method: str
    state_indices: list[int]
    value: Any = None
    units: str = ""
    components: dict[str, float] = field(default_factory=dict)
    implementation_status: str = "exploratory"
    provenance: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PropertyTaskResult:
    """Property-task bundle summary."""

    enabled: bool
    properties: list[PropertyValueResult] = field(default_factory=list)
    verification_status: str = "exploratory"


@dataclass(slots=True)
class QFTModelSummary:
    """Exploratory finite-cutoff lattice-QED model metadata."""

    enabled: bool
    model: str
    dimensions: int
    grid_shape: list[int]
    grid_spacing: list[float]
    grid_origin: str
    grid_axes: str
    boundary: str
    softening: float
    site_count: int
    link_count: int
    plaquette_count: int
    matter_mode_count: int
    matter_qubits: int
    gauge_qubits: int
    total_qubits: int
    gauge_group: str
    gauge_electric_cutoff: int
    gauge_coupling: float
    target_electrons: int
    term_counts_by_sector: dict[str, int] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    constraint_residuals: dict[str, Any] = field(default_factory=dict)
    nuclear_charge_by_site: list[float] = field(default_factory=list)
    gauss_law_generators: list[dict[str, Any]] = field(default_factory=list)
    hamiltonian_gauge_commutator_norms: list[dict[str, Any]] = field(default_factory=list)
    physical_sector: dict[str, Any] = field(default_factory=dict)
    gauge_invariant_ansatz: dict[str, Any] = field(default_factory=dict)
    constraint_expectations: dict[str, Any] = field(default_factory=dict)
    engine: dict[str, Any] = field(default_factory=dict)
    external_point_charges: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FieldModelSummary:
    """Registry-level field-model metadata shared by QFT and cavity-QED paths."""

    model_kind: str
    registry_name: str
    capability_tier: str
    observables: list[str] = field(default_factory=list)
    resource_estimate: dict[str, Any] = field(default_factory=dict)
    error_budget: dict[str, Any] = field(default_factory=dict)
    risk_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CavityQEDModelSummary:
    """Exploratory molecular Pauli-Fierz cavity-QED model metadata."""

    enabled: bool
    model: str
    mode_count: int
    modes: list[dict[str, Any]]
    photon_encoding: str
    include_dipole_self_energy: bool
    photon_physical_subspace_penalty: float
    electronic_qubits: int
    photon_qubits: int
    total_qubits: int
    hamiltonian_formula: str
    term_counts_by_sector: dict[str, int] = field(default_factory=dict)
    observables: dict[str, Any] = field(default_factory=dict)
    resource_estimate: dict[str, Any] = field(default_factory=dict)
    error_budget: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProvenanceSummary:
    """Versions and provenance needed for reproducibility."""

    timestamp: str
    wall_time_seconds: float
    source_config: str
    seed: int
    git_commit: str | None
    git_commit_short: str | None
    git_branch: str | None
    git_describe: str | None
    git_remote_origin: str | None
    repo_root: str | None
    workspace_dirty: bool | None
    workspace_fingerprint: str
    dependency_versions: dict[str, str]
    input_sources: list[dict[str, Any]] = field(default_factory=list)
    git_status_summary: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class LogSummary:
    """Compact execution log for reports and JSON output."""

    events: list[str]


@dataclass(slots=True)
class ArtifactPaths:
    """Filesystem paths for run artifacts."""

    root: Path
    resolved_config: Path
    result_json: Path
    exact_result_json: Path
    report_markdown: Path
    log_file: Path
    calibration_json: Path | None = None
    calibration_report_markdown: Path | None = None
    runtime_submission_json: Path | None = None
    qcschema_json: Path | None = None
    hdf5_file: Path | None = None


@dataclass(slots=True)
class RunResult:
    """Top-level run result exposed to callers and the CLI."""

    schema_version: str
    run_id: str
    verification_status: str
    energy: EnergyResult
    exact_baseline: ExactBaselineSummary
    sampled_result: SampledResultSummary | None
    variational_result: VariationalResultSummary | None
    benchmark: BenchmarkSummary
    mitigation: MitigationSummary
    problem: ProblemSummary
    reduction_audit: ReductionAuditSummary | None
    mapping: MappingSummary
    backend: BackendSummary
    noise_model: NoiseModelSummary | None
    measurement: MeasurementSummary | None
    chemical_accuracy: ChemicalAccuracySummary | None
    runtime_chemical_accuracy: ChemicalAccuracySummary | None
    reduction_plan: ReductionPlanResult | None
    policy_engine: PolicyEngineResult | None
    calibration: CalibrationSummary | None
    runtime_options: RuntimeOptionsSummary | None
    runtime_submission: RuntimeSubmissionSummary | None
    compression_result: CompressionResultSummary | None
    backend_capability: BackendCapabilitySummary
    execution_policy: ExecutionPolicySummary
    excited_state_result: ExcitedStateTaskResult | None
    property_result: PropertyTaskResult | None
    geometry_optimization_result: dict[str, Any] | None
    gradient_result: dict[str, Any] | None
    response_property_result: dict[str, Any] | None
    perturbative_correction_result: PerturbativeCorrectionResultSummary | None
    embedding_result: EmbeddingResultSummary | None
    external_point_charges: ExternalPointChargeSummary | None
    environment_embedding: EffectiveHamiltonianSummary | None
    hardware_error_diagnostic: dict[str, Any] | None
    provenance: ProvenanceSummary
    log_summary: LogSummary
    artifacts: ArtifactPaths
    module_origin: str = "core"
    capability_tier: str = "validated"
    hardware_verified: bool = False
    hardware_evidence_tier: str | None = None
    verification_notes: list[str] = field(default_factory=list)
    scientific_risk_notes: list[str] = field(default_factory=list)
    evidence_summary: EvidenceSummary | None = None
    acceptance_summary: dict[str, Any] | None = None
    artifact_index_entry: dict[str, Any] | None = None
    tc_qsci_result: dict[str, Any] | None = None
    determinant_selection: dict[str, Any] | None = None
    symmetry_sector: dict[str, Any] | None = None
    cast_hamiltonian: dict[str, Any] | None = None
    low_rank_resource_estimate: dict[str, Any] | None = None
    qpe_resource_estimate: dict[str, Any] | None = None
    error_budget: dict[str, Any] | None = None
    field_model: FieldModelSummary | None = None
    qft_model: QFTModelSummary | None = None
    qft_dynamics: dict[str, Any] | None = None
    cavity_qed_model: CavityQEDModelSummary | None = None


@dataclass(slots=True)
class RegistryEntry:
    """Registry entry for study, benchmark, scan, or run artifacts."""

    name: str
    kind: str
    status: str
    artifact_root: Path
    created_at: str
    source: str
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RunRecord:
    """Compact record of one run inside a study."""

    name: str
    source_config: str
    artifact_root: Path
    verification_status: str
    mapping_kind: str
    backend_kind: str
    policy_name: str
    total_energy: float
    absolute_error: float | None
    tags: list[str] = field(default_factory=list)
    evidence_summary: EvidenceSummary | None = None
    initial_point_reused: bool | None = None
    initial_point_source: str | None = None
    initial_point_strategy: str | None = None
    history_sources: list[str] = field(default_factory=list)
    fallback_reason: str | None = None
    iterations: int | None = None
    evaluations: int | None = None
    parameter_count: int | None = None


@dataclass(slots=True)
class StudySummary:
    """Aggregate study summary."""

    total_runs: int
    status_counts: dict[str, int] = field(default_factory=dict)
    comparison_axes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StudyArtifactPaths:
    """Artifact paths for a study result."""

    root: Path
    study_result_json: Path
    study_report_markdown: Path
    registry_json: Path


@dataclass(slots=True)
class StudyResult:
    """Aggregate result for a study."""

    schema_version: str
    study_name: str
    description: str
    summary: StudySummary
    run_records: list[RunRecord] = field(default_factory=list)
    registry_entries: list[RegistryEntry] = field(default_factory=list)
    artifacts: StudyArtifactPaths | None = None
    evidence_summary: EvidenceSummary | None = None


@dataclass(slots=True)
class BenchmarkCaseResult:
    """One benchmark-case outcome."""

    name: str
    kind: str
    status: str
    expected_status: str
    artifact_root: Path | None
    notes: list[str] = field(default_factory=list)
    total_energy: float | None = None
    absolute_error: float | None = None
    relative_error: float | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence_summary: EvidenceSummary | None = None


@dataclass(slots=True)
class BenchmarkSuiteSummary:
    """Aggregate benchmark-suite summary."""

    total_cases: int
    status_counts: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkArtifactPaths:
    """Artifact paths for a benchmark suite."""

    root: Path
    result_json: Path
    report_markdown: Path
    registry_json: Path


@dataclass(slots=True)
class BenchmarkSuiteResult:
    """Top-level benchmark-suite result."""

    schema_version: str
    suite_name: str
    description: str
    summary: BenchmarkSuiteSummary
    cases: list[BenchmarkCaseResult] = field(default_factory=list)
    calibration_summary: dict[str, Any] = field(default_factory=dict)
    dashboard_summary: dict[str, Any] = field(default_factory=dict)
    acceptance_summary: dict[str, Any] = field(default_factory=dict)
    artifact_index_entry: dict[str, Any] | None = None
    registry_entries: list[RegistryEntry] = field(default_factory=list)
    artifacts: BenchmarkArtifactPaths | None = None
    evidence_summary: EvidenceSummary | None = None


@dataclass(slots=True)
class ScanPointResult:
    """One point in a PES scan."""

    point_label: str
    parameter_value: float
    total_energy: float
    verification_status: str
    run_artifact_root: Path
    exact_error: float | None = None
    evidence_summary: EvidenceSummary | None = None
    initial_point_reused: bool | None = None
    initial_point_source: str | None = None
    initial_point_strategy: str | None = None
    history_sources: list[str] = field(default_factory=list)
    fallback_reason: str | None = None
    iterations: int | None = None
    evaluations: int | None = None
    parameter_count: int | None = None


@dataclass(slots=True)
class ScanArtifactPaths:
    """Artifact paths for a scan result."""

    root: Path
    result_json: Path
    report_markdown: Path
    scan_table_csv: Path
    registry_json: Path


@dataclass(slots=True)
class ScanResult:
    """Top-level scan result."""

    schema_version: str
    scan_name: str
    parameter_name: str
    summary: StudySummary
    points: list[ScanPointResult] = field(default_factory=list)
    registry_entries: list[RegistryEntry] = field(default_factory=list)
    artifacts: ScanArtifactPaths | None = None
    evidence_summary: EvidenceSummary | None = None
