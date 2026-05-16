"""Markdown report renderer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qcchem.io.serialization import to_primitive


def _fmt_energy(value: float | None, units: str) -> str:
    if value is None:
        return "`None`"
    return f"`{value:.12f}` {units}"


def _calibration_summary_lines(data: dict[str, Any], units: str) -> list[str]:
    calibration = data.get("calibration") or {}
    return [
        "## Local Calibration Summary",
        "",
        "> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.",
        "",
        f"- available: `{calibration.get('available', False)}`",
        f"- measured_wall_time_seconds: `{calibration.get('measured_wall_time_seconds')}`",
        f"- measured_shot_usage: `{calibration.get('measured_shot_usage')}`",
        f"- precision_target: `{calibration.get('precision_target')}`",
        f"- achieved_error: {_fmt_energy(calibration.get('achieved_error'), units)}",
        f"- estimated_measurement_cost: `{calibration.get('estimated_measurement_cost')}`",
        f"- estimated_vs_measured_cost: `{calibration.get('estimated_vs_measured_cost')}`",
        f"- reference_target: `{calibration.get('reference_target')}`",
        f"- notes: `{calibration.get('notes', [])}`",
        "",
    ]


def _hardware_execution_lines(data: dict[str, Any]) -> list[str]:
    runtime_submission = data.get("runtime_submission") or {}
    return [
        "## Hardware Execution",
        "",
        f"- hardware_verified: `{data.get('hardware_verified', False)}`",
        f"- hardware_evidence_tier: `{data.get('hardware_evidence_tier')}`",
        f"- attempted: `{runtime_submission.get('attempted')}`",
        f"- submitted: `{runtime_submission.get('submitted')}`",
        f"- succeeded: `{runtime_submission.get('succeeded')}`",
        f"- service: `{runtime_submission.get('service')}`",
        f"- mode: `{runtime_submission.get('mode')}`",
        f"- session_requested: `{runtime_submission.get('session_requested')}`",
        f"- batch_requested: `{runtime_submission.get('batch_requested')}`",
        f"- backend_name: `{runtime_submission.get('backend_name')}`",
        f"- provider: `{runtime_submission.get('provider')}`",
        f"- layout_strategy: `{runtime_submission.get('layout_strategy')}`",
        f"- selected_layout: `{runtime_submission.get('selected_layout', [])}`",
        f"- layout_score: `{runtime_submission.get('layout_score')}`",
        f"- transpiled_depth: `{runtime_submission.get('transpiled_depth')}`",
        f"- transpiled_two_qubit_gate_count: `{runtime_submission.get('transpiled_two_qubit_gate_count')}`",
        f"- transpilation_options: `{runtime_submission.get('transpilation_options', {})}`",
        f"- job_id: `{runtime_submission.get('job_id')}`",
        f"- session_id: `{runtime_submission.get('session_id')}`",
        f"- batch_id: `{runtime_submission.get('batch_id')}`",
        f"- submission_wall_time_seconds: `{runtime_submission.get('submission_wall_time_seconds')}`",
        f"- usage_estimation: `{runtime_submission.get('usage_estimation', {})}`",
        f"- job_metrics: `{runtime_submission.get('job_metrics', {})}`",
        f"- failure_category: `{runtime_submission.get('failure_category')}`",
        f"- failure_message: `{runtime_submission.get('failure_message')}`",
        f"- verification_status: `{runtime_submission.get('verification_status')}`",
        f"- options_snapshot: `{runtime_submission.get('options_snapshot', {})}`",
        f"- returned_job_metadata: `{runtime_submission.get('returned_job_metadata', {})}`",
        f"- result_provenance: `{runtime_submission.get('result_provenance', {})}`",
        "",
    ]


def _chemical_accuracy_lines(summary: dict[str, Any], units: str) -> list[str]:
    assessment_target = str(summary.get("assessment_target", "local_execution"))
    title_suffix = "Local Execution" if assessment_target == "local_execution" else "Runtime-Derived"
    return [
        f"## Chemical Accuracy ({title_suffix})",
        "",
        f"- available: `{summary.get('available')}`",
        f"- assessment_target: `{assessment_target}`",
        f"- status: `{summary.get('status')}`",
        f"- meets_chemical_accuracy: `{summary.get('meets_chemical_accuracy')}`",
        f"- absolute_error_hartree: {_fmt_energy(summary.get('absolute_error_hartree'), units)}",
        f"- absolute_error_kcal_mol: `{summary.get('absolute_error_kcal_mol')}`",
        f"- threshold_hartree: `{summary.get('threshold_hartree')}`",
        f"- threshold_kcal_mol: `{summary.get('threshold_kcal_mol')}`",
        f"- statistical_error: {_fmt_energy(summary.get('statistical_error'), units)}",
        f"- notes: `{summary.get('notes', [])}`",
        "",
    ]


def _method_label(data: dict[str, Any]) -> str:
    variational = data.get("variational_result") or {}
    sampled = data.get("sampled_result") or {}
    solver_kind = variational.get("solver_kind")
    ansatz = variational.get("ansatz")
    if solver_kind and ansatz:
        return f"{solver_kind} / {ansatz}"
    if solver_kind:
        return str(solver_kind)
    if sampled.get("backend_kind"):
        return f"sampled / {sampled.get('backend_kind')}"
    backend = data.get("backend") or {}
    return str(backend.get("kind", "n/a"))


def _chemical_accuracy_distance(summary: dict[str, Any]) -> float | None:
    absolute_error = summary.get("absolute_error_hartree")
    threshold = summary.get("threshold_hartree")
    if absolute_error is None or threshold is None:
        return None
    return max(float(absolute_error) - float(threshold), 0.0)


def _explicit_available_chemical_accuracy_summaries(data: dict[str, Any]) -> list[dict[str, Any]]:
    available: list[dict[str, Any]] = []
    for summary in (data.get("chemical_accuracy"), data.get("runtime_chemical_accuracy")):
        if isinstance(summary, dict) and summary.get("available") is True:
            available.append(summary)
    return available


def _primary_chemical_accuracy_summary(data: dict[str, Any]) -> dict[str, Any] | None:
    candidates = _explicit_available_chemical_accuracy_summaries(data)
    if not candidates:
        legacy_candidates: list[dict[str, Any]] = []
        for summary in (data.get("chemical_accuracy"), data.get("runtime_chemical_accuracy")):
            if (
                isinstance(summary, dict)
                and "available" not in summary
                and summary.get("absolute_error_hartree") is not None
            ):
                legacy_candidates.append(summary)
        candidates = legacy_candidates
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: float(item.get("absolute_error_hartree"))
        if item.get("absolute_error_hartree") is not None
        else float("inf"),
    )


def _report_cover_lines(data: dict[str, Any], units: str) -> list[str]:
    problem = data["problem"]
    mapping = data["mapping"]
    backend = data["backend"]
    benchmark = data["benchmark"]
    confidence = _primary_chemical_accuracy_summary(data) or {}
    return [
        "## Report Cover",
        "",
        "> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.",
        "",
        f"- molecule: `{problem['molecule_name']}`",
        f"- basis: `{problem['basis']}`",
        f"- method: `{_method_label(data)}`",
        f"- mapping_kind: `{mapping['kind']}`",
        f"- num_qubits: `{mapping['num_qubits']}`",
        f"- verification_status: `{data.get('verification_status')}`",
        f"- hardware_verified: `{data.get('hardware_verified', False)}`",
        f"- hardware_evidence_tier: `{data.get('hardware_evidence_tier')}`",
        f"- benchmark_absolute_error: {_fmt_energy(benchmark.get('absolute_error'), units)}",
        f"- best_available_assessment: `{confidence.get('assessment_target')}`",
        f"- backend_kind: `{backend['kind']}`",
        "",
    ]


def _hero_lines(data: dict[str, Any], units: str) -> list[str]:
    energy = data["energy"]
    benchmark = data["benchmark"]
    problem = data["problem"]
    runtime_submission = data.get("runtime_submission") or {}
    return [
        "## Hero",
        "",
        f"- headline_total_energy: {_fmt_energy(energy.get('total_energy'), units)}",
        f"- headline_correlation_energy: {_fmt_energy(energy.get('correlation_energy'), units)}",
        f"- headline_absolute_error: {_fmt_energy(benchmark.get('absolute_error'), units)}",
        f"- comparison_target: `{benchmark.get('comparison_target')}`",
        f"- active_space_metadata: `{problem.get('active_space_metadata')}`",
        f"- runtime_backend: `{runtime_submission.get('backend_name')}`",
        f"- runtime_job_id: `{runtime_submission.get('job_id')}`",
        "",
    ]


def _chemical_accuracy_frame_lines(data: dict[str, Any], units: str) -> list[str]:
    primary = _primary_chemical_accuracy_summary(data) or {}
    assessments = [
        summary.get("assessment_target")
        for summary in _explicit_available_chemical_accuracy_summaries(data)
    ]
    distance = _chemical_accuracy_distance(primary)
    return [
        "## Chemical Accuracy Frame",
        "",
        f"- available_assessments: `{assessments}`",
        f"- best_available_assessment: `{primary.get('assessment_target')}`",
        f"- status: `{primary.get('status')}`",
        f"- meets_chemical_accuracy: `{primary.get('meets_chemical_accuracy')}`",
        f"- absolute_error_hartree: {_fmt_energy(primary.get('absolute_error_hartree'), units)}",
        f"- threshold_hartree: `{primary.get('threshold_hartree')}`",
        f"- distance_to_chemical_accuracy: `{distance}`",
        f"- statistical_error: {_fmt_energy(primary.get('statistical_error'), units)}",
        f"- notes: `{primary.get('notes', [])}`",
        "",
    ]


def _runtime_evidence_frame_lines(data: dict[str, Any]) -> list[str]:
    runtime_submission = data.get("runtime_submission") or {}
    return [
        "## Runtime Evidence",
        "",
        "> Runtime evidence is surfaced explicitly so exported reports separate chemistry confidence from execution provenance.",
        "",
        f"- hardware_verified: `{data.get('hardware_verified', False)}`",
        f"- hardware_evidence_tier: `{data.get('hardware_evidence_tier')}`",
        f"- service: `{runtime_submission.get('service')}`",
        f"- provider: `{runtime_submission.get('provider')}`",
        f"- backend_name: `{runtime_submission.get('backend_name')}`",
        f"- job_id: `{runtime_submission.get('job_id')}`",
        f"- verification_status: `{runtime_submission.get('verification_status')}`",
        f"- layout_strategy: `{runtime_submission.get('layout_strategy')}`",
        f"- selected_layout: `{runtime_submission.get('selected_layout', [])}`",
        f"- transpiled_depth: `{runtime_submission.get('transpiled_depth')}`",
        f"- transpiled_two_qubit_gate_count: `{runtime_submission.get('transpiled_two_qubit_gate_count')}`",
        "",
    ]


def _qft_model_lines(data: dict[str, Any]) -> list[str]:
    qft = data.get("qft_model") or {}
    engine = qft.get("engine", {}) if isinstance(qft.get("engine"), dict) else {}
    lines = [
        "## Lattice QED Field Model",
        "",
        "> This section describes an exploratory finite-cutoff field Hamiltonian; exact baselines are for this discretized model.",
        "",
        f"- model: `{qft.get('model')}`",
        f"- dimensions: `{qft.get('dimensions')}`",
        f"- grid_shape: `{qft.get('grid_shape')}`",
        f"- grid_spacing: `{qft.get('grid_spacing')}`",
        f"- boundary: `{qft.get('boundary')}`",
        f"- site_count: `{qft.get('site_count')}`",
        f"- link_count: `{qft.get('link_count')}`",
        f"- plaquette_count: `{qft.get('plaquette_count')}`",
        f"- matter_mode_count: `{qft.get('matter_mode_count')}`",
        f"- gauge_group: `{qft.get('gauge_group')}`",
        f"- gauge_electric_cutoff: `{qft.get('gauge_electric_cutoff')}`",
        f"- gauge_coupling: `{qft.get('gauge_coupling')}`",
        f"- total_qubits: `{qft.get('total_qubits')}`",
        f"- target_electrons: `{qft.get('target_electrons')}`",
        f"- term_counts_by_sector: `{qft.get('term_counts_by_sector', {})}`",
        f"- constraints: `{qft.get('constraints', {})}`",
        f"- engine: `{engine}`",
        f"- nuclear_charge_by_site: `{qft.get('nuclear_charge_by_site', [])}`",
        f"- notes: `{qft.get('notes', [])}`",
        "",
    ]
    lines.extend(
        [
            "## Gauge Constraint Audit",
            "",
            "> finite-cutoff QFT correctness means the configured lattice/cutoff Hamiltonian is internally audited; gauge-constraint consistency means Gauss-law generators and physical-sector checks are tracked; continuum chemistry accuracy is not claimed here.",
            "",
            f"- gauss_law_generators: `{qft.get('gauss_law_generators', [])}`",
            f"- hamiltonian_gauge_commutator_norms: `{qft.get('hamiltonian_gauge_commutator_norms', [])}`",
            f"- physical_sector: `{qft.get('physical_sector', {})}`",
            f"- gauge_invariant_ansatz: `{qft.get('gauge_invariant_ansatz', {})}`",
            f"- constraint_expectations: `{qft.get('constraint_expectations', {})}`",
            f"- finite_cutoff_qft_correctness: `audited against the persisted finite Hamiltonian`",
            f"- gauge_constraint_consistency: `Gauss-law residuals and commutators are finite-cutoff checks`",
            f"- continuum_chemistry_accuracy: `not asserted by this exploratory artifact`",
            "",
        ]
    )
    if engine:
        lines.extend(
            [
                "## QFT Physical-Sector Engine Audit",
                "",
                "> This section separates sparse/projection correctness from hardware full-register circuits and from continuum chemistry accuracy.",
                "",
                f"- requested_representation: `{engine.get('requested_representation')}`",
                f"- actual_representation: `{engine.get('actual_representation')}`",
                f"- projected_dimension: `{engine.get('projected_dimension')}`",
                f"- full_dimension: `{engine.get('full_dimension')}`",
                f"- pauli_materialization: `{engine.get('pauli_materialization')}`",
                f"- dense_full_matrix_materialized: `{engine.get('dense_full_matrix_materialized')}`",
                f"- basis_hash: `{qft.get('physical_sector', {}).get('basis_hash')}`",
                f"- basis_index_count: `{qft.get('physical_sector', {}).get('basis_index_count')}`",
                f"- sparse_projection_correctness: `projected operators are finite-cutoff indexed submatrices when projection is active`",
                f"- runtime_circuit_boundary: `Runtime previews still target the full qubit register unless separately transformed`",
                f"- continuum_chemistry_accuracy: `not asserted by this exploratory engine audit`",
                "",
            ]
        )
    return lines


def _qft_dynamics_lines(data: dict[str, Any]) -> list[str]:
    dynamics = data.get("qft_dynamics") or {}
    exact = dynamics.get("exact") or {}
    trotter = dynamics.get("trotter") or {}
    runtime_batch = dynamics.get("runtime_batch") or {}
    return [
        "## QFT Real-Time Dynamics",
        "",
        "> This section reports exploratory finite-cutoff real-time lattice-QED dynamics; Trotter and runtime evidence are approximation/execution evidence, not continuum chemistry accuracy.",
        "",
        f"- enabled: `{dynamics.get('enabled')}`",
        f"- method: `{dynamics.get('method')}`",
        f"- quench: `{dynamics.get('quench', {})}`",
        f"- time_grid: `{dynamics.get('time_grid', {})}`",
        f"- observable_summary: `{dynamics.get('observables', {})}`",
        f"- exact_available: `{exact.get('available')}`",
        f"- exact_time_point_count: `{len(exact.get('time_points', []) or [])}`",
        f"- exact_skipped_reason: `{exact.get('skipped_reason')}`",
        f"- trotter_available: `{trotter.get('available')}`",
        f"- trotter_circuit_resources: `{trotter.get('circuit_resources', {})}`",
        f"- trotter_error_summary: `{dynamics.get('trotter_error_summary', {})}`",
        f"- runtime_batch: `{runtime_batch}`",
        f"- finite_cutoff_dynamics: `exact/statevector curves are for the persisted finite Hamiltonian`",
        f"- trotter_approximation: `reported against finite-cutoff exact dynamics when available`",
        f"- continuum_chemistry_accuracy: `not asserted by this exploratory dynamics artifact`",
        "",
    ]


def _field_model_lines(data: dict[str, Any]) -> list[str]:
    field_model = data.get("field_model") or {}
    return [
        "## Field Model Registry",
        "",
        f"- model_kind: `{field_model.get('model_kind')}`",
        f"- registry_name: `{field_model.get('registry_name')}`",
        f"- capability_tier: `{field_model.get('capability_tier')}`",
        f"- observables: `{field_model.get('observables', [])}`",
        f"- resource_estimate: `{field_model.get('resource_estimate', {})}`",
        f"- error_budget: `{field_model.get('error_budget', {})}`",
        f"- risk_notes: `{field_model.get('risk_notes', [])}`",
        "",
    ]


def _cavity_qed_model_lines(data: dict[str, Any]) -> list[str]:
    cavity = data.get("cavity_qed_model") or {}
    observables = cavity.get("observables", {}) if isinstance(cavity.get("observables"), dict) else {}
    return [
        "## Pauli-Fierz Cavity-QED Model",
        "",
        "> This section reports exploratory molecular cavity-QED evidence for the configured finite photon cutoff; exact baselines are exact for this electron-photon Hamiltonian only.",
        "",
        f"- model: `{cavity.get('model')}`",
        f"- mode_count: `{cavity.get('mode_count')}`",
        f"- modes: `{cavity.get('modes', [])}`",
        f"- photon_encoding: `{cavity.get('photon_encoding')}`",
        f"- include_dipole_self_energy: `{cavity.get('include_dipole_self_energy')}`",
        f"- photon_physical_subspace_penalty: `{cavity.get('photon_physical_subspace_penalty')}`",
        f"- electronic_qubits: `{cavity.get('electronic_qubits')}`",
        f"- photon_qubits: `{cavity.get('photon_qubits')}`",
        f"- total_qubits: `{cavity.get('total_qubits')}`",
        f"- hamiltonian_formula: `{cavity.get('hamiltonian_formula')}`",
        f"- term_counts_by_sector: `{cavity.get('term_counts_by_sector', {})}`",
        f"- photon occupation: `{observables.get('photon_occupation', [])}`",
        f"- dipole_expectation: `{observables.get('dipole_expectation', [])}`",
        f"- electron_photon_coupling_energy: `{observables.get('electron_photon_coupling_energy', [])}`",
        f"- dipole_self_energy: `{observables.get('dipole_self_energy', [])}`",
        f"- polaritonic_state_composition: `{observables.get('polaritonic_state_composition', [])}`",
        f"- photon_physical_subspace_leakage: `{observables.get('photon_physical_subspace_leakage')}`",
        f"- exact_residual_norm: `{observables.get('exact_residual_norm')}`",
        f"- vqe_vs_exact_error: `{observables.get('vqe_vs_exact_error')}`",
        f"- resource_estimate: `{cavity.get('resource_estimate', {})}`",
        f"- error_budget: `{cavity.get('error_budget', {})}`",
        f"- notes: `{cavity.get('notes', [])}`",
        "",
    ]


def _evidence_summary_lines(data: dict[str, Any]) -> list[str]:
    evidence = data.get("evidence_summary") or {}
    baseline = evidence.get("primary_baseline") or {}
    metric = evidence.get("primary_error_metric") or {}
    return [
        "## Evidence Summary",
        "",
        f"- result_identity: `{evidence.get('result_identity')}`",
        f"- primary_scientific_claim: `{evidence.get('primary_scientific_claim')}`",
        f"- primary_baseline: `{baseline}`",
        f"- primary_error_metric: `{metric}`",
        f"- chemical_accuracy_status: `{evidence.get('chemical_accuracy_status')}`",
        f"- runtime_evidence_status: `{evidence.get('runtime_evidence_status')}`",
        f"- trust_tier: `{evidence.get('trust_tier')}`",
        f"- recommended_action: `{evidence.get('recommended_action')}`",
        "",
    ]


def _claim_lines(data: dict[str, Any]) -> list[str]:
    evidence = data.get("evidence_summary") or {}
    return [
        "## Claim",
        "",
        f"- primary_scientific_claim: `{evidence.get('primary_scientific_claim')}`",
        f"- trust_tier: `{evidence.get('trust_tier')}`",
        f"- recommended_action: `{evidence.get('recommended_action')}`",
        "",
    ]


def _chain_lines(data: dict[str, Any], units: str) -> list[str]:
    evidence = data.get("evidence_summary") or {}
    reduction = data.get("reduction_audit") or {}
    compression = data.get("compression_result") or {}
    perturbative = data.get("perturbative_correction_result") or {}
    return [
        "## Chain",
        "",
        f"- reduction: `{reduction.get('selection_mode')}` / transformers=`{reduction.get('transformers_applied', [])}`",
        f"- compression: `{compression.get('method')}` / status=`{compression.get('verification_status')}`",
        f"- correction: `{perturbative.get('method')}` / delta={_fmt_energy(perturbative.get('perturbative_correction'), units)}",
        f"- comparison_evidence: `{evidence.get('comparison_evidence')}`",
        "",
    ]


def _proof_lines(data: dict[str, Any]) -> list[str]:
    evidence = data.get("evidence_summary") or {}
    provenance = data.get("provenance") or {}
    runtime_submission = data.get("runtime_submission") or {}
    artifacts = data.get("artifacts") or {}
    return [
        "## Proof",
        "",
        f"- execution_evidence: `{evidence.get('execution_evidence')}`",
        f"- trust_judgment: `{evidence.get('trust_judgment')}`",
        f"- provenance_timestamp: `{provenance.get('timestamp')}`",
        f"- runtime_job_id: `{runtime_submission.get('job_id')}`",
        f"- artifact_root: `{artifacts.get('root')}`",
        "",
    ]


def render_markdown_report(result: Any) -> str:
    """Render a QCchem result as a Markdown report."""
    data = to_primitive(result)
    energy = data["energy"]
    benchmark = data["benchmark"]
    exact = data.get("exact_baseline") or {}
    sampled = data.get("sampled_result")
    variational = data.get("variational_result")
    excited = data.get("excited_state_result")
    properties = data.get("property_result")
    field_model = data.get("field_model")
    qft_model = data.get("qft_model")
    qft_dynamics = data.get("qft_dynamics")
    cavity_qed_model = data.get("cavity_qed_model")
    reduction = data.get("reduction_audit")
    compression = data.get("compression_result")
    perturbative = data.get("perturbative_correction_result")
    embedding = data.get("embedding_result")
    tc_qsci = data.get("tc_qsci_result")
    determinant_selection = data.get("determinant_selection")
    symmetry_sector = data.get("symmetry_sector")
    cast_hamiltonian = data.get("cast_hamiltonian")
    low_rank_resource = data.get("low_rank_resource_estimate")
    qpe_resource = data.get("qpe_resource_estimate")
    error_budget = data.get("error_budget")
    noise_model = data.get("noise_model")
    measurement = data.get("measurement")
    runtime_options = data.get("runtime_options")
    chemical_accuracy = data.get("chemical_accuracy")
    runtime_chemical_accuracy = data.get("runtime_chemical_accuracy")
    reduction_plan = data.get("reduction_plan")
    module_origin = data.get("module_origin", "core")
    capability_tier = data.get("capability_tier", data.get("verification_status"))
    verification_notes = data.get("verification_notes", [])
    scientific_risk_notes = data.get("scientific_risk_notes", [])
    capability = data.get("backend_capability") or {}
    policy = data.get("execution_policy") or {}
    mitigation = data.get("mitigation") or {}
    backend = data["backend"]
    problem = data["problem"]
    mapping = data["mapping"]
    provenance = data["provenance"]
    units = energy["energy_units"]

    lines = [
        f"# QCchem Report: {data['problem']['molecule_name']}",
        "",
    ]
    if module_origin == "exploratory" or capability_tier == "exploratory":
        lines.extend(
            [
                "> This result is exploratory and is not part of the validated QCchem benchmark path.",
                "",
            ]
        )
    lines.extend(
        [
        *_report_cover_lines(data, units),
        *_hero_lines(data, units),
        *_evidence_summary_lines(data),
        *_claim_lines(data),
        *_chain_lines(data, units),
        *_proof_lines(data),
        *_chemical_accuracy_frame_lines(data, units),
        *_runtime_evidence_frame_lines(data),
        "## Verification",
        "",
        f"- verification_status: `{data.get('verification_status')}`",
        "",
        "## Validation Boundary",
        "",
        f"- Module Origin: `{module_origin}`",
        f"- Capability Tier: `{capability_tier}`",
        f"- Verification Notes: `{verification_notes}`",
        f"- Scientific Risk Notes: `{scientific_risk_notes}`",
        "",
        "## Energy Summary",
        "",
        f"- electronic_energy: {_fmt_energy(energy['electronic_energy'], units)}",
        f"- nuclear_repulsion_energy: {_fmt_energy(energy['nuclear_repulsion_energy'], units)}",
        f"- total_energy: {_fmt_energy(energy['total_energy'], units)}",
        f"- hf_reference_energy: {_fmt_energy(energy['hf_reference_energy'], units)}",
        f"- solver_energy: {_fmt_energy(energy['solver_energy'], units)} (raw solver-Hamiltonian energy, before QCchem constant-shift correction)",
        f"- exact_ground_energy: {_fmt_energy(energy['exact_ground_energy'], units)} (raw exact baseline in the same solver-Hamiltonian convention)",
        f"- correlation_energy: {_fmt_energy(energy['correlation_energy'], units)}",
        f"- energy_units: `{units}`",
        f"- constant_energy_correction: {_fmt_energy(energy['constant_energy_correction'], units)}",
        f"- energy_formula: `{energy['energy_formula']}`",
        "",
        "## Field Definitions",
        "",
        "- `solver_energy` is the raw energy returned by the configured solver on the mapped qubit Hamiltonian.",
        "- `exact_ground_energy` is the raw exact-diagonalization energy of that same mapped Hamiltonian.",
        "- `electronic_energy` is QCchem's corrected electronic energy after adding any non-nuclear Hamiltonian constants, such as active-space offsets.",
        "- `total_energy` is reconstructed from the explicit `energy_formula`, so active-space and transformed problems remain auditable.",
        "- `hf_reference_energy` is the Hartree-Fock total reference energy exposed by Qiskit Nature.",
        "- `correlation_energy` is `total_energy - hf_reference_energy` and therefore measures post-HF improvement in the total-energy convention.",
        "",
        "## Exact Baseline",
        "",
        f"- available: `{exact.get('available')}`",
        f"- source: `{exact.get('source')}`",
        f"- solver_hamiltonian_energy: {_fmt_energy(exact.get('solver_hamiltonian_energy'), units)}",
        f"- electronic_energy: {_fmt_energy(exact.get('electronic_energy'), units)}",
        f"- total_energy: {_fmt_energy(exact.get('total_energy'), units)}",
        "",
        "## Benchmark",
        "",
        f"- exact_available: `{benchmark['exact_available']}`",
        f"- comparison_target: `{benchmark['comparison_target']}`",
        f"- exact_electronic_energy: {_fmt_energy(benchmark.get('exact_electronic_energy'), units)}",
        f"- exact_total_energy: {_fmt_energy(benchmark.get('exact_total_energy'), units)}",
        f"- absolute_error: {_fmt_energy(benchmark.get('absolute_error'), units)}",
        f"- relative_error: `{benchmark.get('relative_error')}`",
        f"- statistical_error: {_fmt_energy(benchmark.get('statistical_error'), units)}",
        f"- absolute_error_threshold: `{benchmark['absolute_error_threshold']}`",
        f"- relative_error_threshold: `{benchmark['relative_error_threshold']}`",
        f"- within_uncertainty: `{benchmark.get('within_uncertainty')}`",
        f"- meets_threshold: `{benchmark.get('meets_threshold')}`",
        "",
        "## Problem Summary",
        "",
        f"- Basis: `{problem['basis']}`",
        f"- Charge: `{problem['charge']}`",
        f"- Multiplicity: `{problem['multiplicity']}`",
        f"- Num particles: `{tuple(problem['num_particles'])}`",
        f"- Num spatial orbitals: `{problem['num_spatial_orbitals']}`",
        f"- Active space metadata: `{problem.get('active_space_metadata')}`",
        f"- Transformers applied: `{problem.get('transformers_applied', [])}`",
        f"- Hamiltonian constants: `{problem['hamiltonian_constants']}`",
        f"- Electronic constant correction: {_fmt_energy(problem.get('electronic_constant_correction'), units)}",
        f"- Point-group metadata: `{problem.get('point_group_metadata', {})}`",
        "",
        "## Mapping",
        "",
        f"- Mapping kind: `{mapping['kind']}`",
        f"- Qubit count: `{mapping['num_qubits']}`",
        f"- Fermionic Hamiltonian terms: `{mapping['fermionic_term_count']}`",
        f"- Qubit Hamiltonian terms: `{mapping['qubit_term_count']}`",
        f"- Raw qubit count: `{mapping.get('raw_num_qubits')}`",
        f"- Raw qubit Hamiltonian terms: `{mapping.get('raw_qubit_term_count')}`",
        f"- Symmetry tapered qubits: `{mapping.get('symmetry_tapered_qubits', 0)}`",
        f"- Z2 symmetry count: `{mapping.get('z2_symmetry_count', 0)}`",
        f"- Z2 tapering values: `{mapping.get('z2_tapering_values')}`",
        f"- Symmetry reduction status: `{mapping.get('symmetry_reduction_status')}`",
        f"- Symmetry reduction validation: `{mapping.get('symmetry_reduction_validation', {})}`",
        f"- Symmetry reduction notes: `{mapping.get('symmetry_reduction_notes', [])}`",
        "",
        "## Backend",
        "",
        f"- Backend kind: `{backend['kind']}`",
        f"- Precision: `{backend['precision']}`",
        f"- Shots: `{backend['shots']}`",
        f"- Seed: `{backend.get('seed')}`",
        f"- Repetitions: `{backend.get('repetitions')}`",
        f"- Abelian grouping: `{backend.get('abelian_grouping')}`",
        f"- Noise enabled: `{backend.get('noise_enabled')}`",
        f"- Runtime enabled: `{backend.get('runtime_enabled')}`",
        "",
        "## Backend Capability",
        "",
        f"- backend_kind: `{capability.get('backend_kind')}`",
        f"- statevector: `{capability.get('statevector')}`",
        f"- shot_based: `{capability.get('shot_based')}`",
        f"- exact_baseline: `{capability.get('exact_baseline')}`",
        f"- runtime_ready: `{capability.get('runtime_ready')}`",
        f"- session_ready: `{capability.get('session_ready')}`",
        f"- batch_ready: `{capability.get('batch_ready')}`",
        f"- mitigation_ready: `{capability.get('mitigation_ready')}`",
        f"- noise_model_ready: `{capability.get('noise_model_ready')}`",
        f"- supports_grouping: `{capability.get('supports_grouping')}`",
        f"- supports_repetitions: `{capability.get('supports_repetitions')}`",
        f"- supports_confidence_metrics: `{capability.get('supports_confidence_metrics')}`",
        "",
        "## Execution Policy",
        "",
        f"- name: `{policy.get('name')}`",
        f"- default_shots: `{policy.get('default_shots')}`",
        f"- default_repetitions: `{policy.get('default_repetitions')}`",
        f"- exact_baseline_required: `{policy.get('exact_baseline_required')}`",
        f"- confidence_rule: `{policy.get('confidence_rule')}`",
        f"- mitigation_posture: `{policy.get('mitigation_posture')}`",
        f"- runtime_ready_expected: `{policy.get('runtime_ready_expected')}`",
        f"- session_ready_expected: `{policy.get('session_ready_expected')}`",
        f"- batch_ready_expected: `{policy.get('batch_ready_expected')}`",
        f"- noise_ready_expected: `{policy.get('noise_ready_expected')}`",
        "",
        ]
    )

    if field_model is not None:
        lines.extend(_field_model_lines(data))
    if qft_model is not None:
        lines.extend(_qft_model_lines(data))
    if qft_dynamics is not None:
        lines.extend(_qft_dynamics_lines(data))
    if cavity_qed_model is not None:
        lines.extend(_cavity_qed_model_lines(data))

    if chemical_accuracy is not None:
        lines.extend(_chemical_accuracy_lines(chemical_accuracy, units))
    if runtime_chemical_accuracy is not None:
        lines.extend(_chemical_accuracy_lines(runtime_chemical_accuracy, units))

    compressed_comparison = benchmark.get("compressed_vs_uncompressed")
    if compressed_comparison is not None:
        lines.extend(
            [
                "## Compressed vs Uncompressed",
                "",
                f"- available: `{compressed_comparison.get('available')}`",
                f"- method: `{compressed_comparison.get('method')}`",
                f"- rank: `{compressed_comparison.get('rank')}`",
                f"- threshold: `{compressed_comparison.get('threshold')}`",
                f"- pre_term_count: `{compressed_comparison.get('pre_term_count')}`",
                f"- post_term_count: `{compressed_comparison.get('post_term_count')}`",
                f"- compressed_solver_energy: {_fmt_energy(compressed_comparison.get('compressed_solver_energy'), units)}",
                f"- uncompressed_solver_energy: {_fmt_energy(compressed_comparison.get('uncompressed_solver_energy'), units)}",
                f"- compressed_total_energy: {_fmt_energy(compressed_comparison.get('compressed_total_energy'), units)}",
                f"- uncompressed_total_energy: {_fmt_energy(compressed_comparison.get('uncompressed_total_energy'), units)}",
                f"- absolute_error: {_fmt_energy(compressed_comparison.get('absolute_error'), units)}",
                f"- relative_error: `{compressed_comparison.get('relative_error')}`",
                f"- compressed_solve_wall_time_seconds: `{compressed_comparison.get('compressed_solve_wall_time_seconds')}`",
                f"- uncompressed_solve_wall_time_seconds: `{compressed_comparison.get('uncompressed_solve_wall_time_seconds')}`",
                "",
            ]
        )

    if noise_model is not None:
        lines.extend(
            [
                "## Noise Model",
                "",
                f"- enabled: `{noise_model.get('enabled')}`",
                f"- profile: `{noise_model.get('profile')}`",
                f"- model_kind: `{noise_model.get('model_kind')}`",
                f"- local_simulation: `{noise_model.get('local_simulation')}`",
                f"- basis_gates: `{noise_model.get('basis_gates', [])}`",
                f"- parameters: `{noise_model.get('parameters', {})}`",
                f"- provenance: `{noise_model.get('provenance', {})}`",
                "",
            ]
        )

    if runtime_options is not None:
        lines.extend(
            [
                "## Runtime Options",
                "",
                f"- enabled: `{runtime_options.get('enabled')}`",
                f"- service: `{runtime_options.get('service')}`",
                f"- instance: `{runtime_options.get('instance')}`",
                f"- runtime_ready: `{runtime_options.get('runtime_ready')}`",
                f"- session_ready: `{runtime_options.get('session_ready')}`",
                f"- batch_ready: `{runtime_options.get('batch_ready')}`",
                f"- precision_target: `{runtime_options.get('precision_target')}`",
                f"- max_budgeted_shots: `{runtime_options.get('max_budgeted_shots')}`",
                f"- max_execution_seconds: `{runtime_options.get('max_execution_seconds')}`",
                f"- calibration_strategy: `{runtime_options.get('calibration_strategy')}`",
                f"- resilience_level: `{runtime_options.get('resilience_level')}`",
                f"- grouping_policy: `{runtime_options.get('grouping_policy')}`",
                f"- session_recommendation: `{runtime_options.get('session_recommendation')}`",
                f"- batch_recommendation: `{runtime_options.get('batch_recommendation')}`",
                f"- low_rank_workload: `{runtime_options.get('low_rank_workload')}`",
                f"- measurement_group_count: `{runtime_options.get('measurement_group_count')}`",
                f"- estimated_shot_cost: `{runtime_options.get('estimated_shot_cost')}`",
                f"- options: `{runtime_options.get('options', {})}`",
                f"- provenance: `{runtime_options.get('provenance', {})}`",
                "",
            ]
        )

    if reduction is not None:
        lines.extend(
            [
                "## Reduction Audit",
                "",
                f"- original_num_particles: `{tuple(reduction.get('original_num_particles', []))}`",
                f"- original_num_spatial_orbitals: `{reduction.get('original_num_spatial_orbitals')}`",
                f"- reduced_num_particles: `{tuple(reduction.get('reduced_num_particles', []))}`",
                f"- reduced_num_spatial_orbitals: `{reduction.get('reduced_num_spatial_orbitals')}`",
                f"- transformers_applied: `{reduction.get('transformers_applied', [])}`",
                f"- active_space_metadata: `{reduction.get('active_space_metadata')}`",
                f"- selection_mode: `{reduction.get('selection_mode')}`",
                f"- selection_reason: `{reduction.get('selection_reason')}`",
                f"- selected_active_orbitals: `{reduction.get('selected_active_orbitals', [])}`",
                f"- selected_active_orbitals_original: `{reduction.get('selected_active_orbitals_original', [])}`",
                f"- frozen_core_orbitals: `{reduction.get('frozen_core_orbitals', [])}`",
                f"- removed_orbitals: `{reduction.get('removed_orbitals', [])}`",
                f"- hamiltonian_constants: `{reduction.get('hamiltonian_constants', {})}`",
                f"- constant_energy_correction: {_fmt_energy(reduction.get('constant_energy_correction'), units)}",
                f"- nuclear_repulsion_energy: {_fmt_energy(reduction.get('nuclear_repulsion_energy'), units)}",
                f"- total_constant_correction: {_fmt_energy(reduction.get('total_constant_correction'), units)}",
                f"- energy_formula: `{reduction.get('energy_formula')}`",
                f"- point_group_metadata: `{reduction.get('point_group_metadata', {})}`",
                "",
            ]
        )

    if reduction_plan is not None:
        lines.extend(
            [
                "## Reduction Plan",
                "",
                f"- enabled: `{reduction_plan.get('enabled')}`",
                f"- mode: `{reduction_plan.get('mode')}`",
                f"- strategy: `{reduction_plan.get('strategy')}`",
                f"- recommended_changes: `{reduction_plan.get('recommended_changes', {})}`",
                f"- notes: `{reduction_plan.get('notes', [])}`",
                f"- provenance: `{reduction_plan.get('provenance', {})}`",
                "",
            ]
        )

    if compression is not None:
        lines.extend(
            [
                "## Compression Audit",
                "",
                f"- enabled: `{compression.get('enabled')}`",
                f"- method: `{compression.get('method')}`",
                f"- rank: `{compression.get('rank')}`",
                f"- threshold: `{compression.get('threshold')}`",
                f"- max_rank: `{compression.get('max_rank')}`",
                f"- apply_to_solver: `{compression.get('apply_to_solver')}`",
                f"- execution_enabled: `{compression.get('execution_enabled')}`",
                f"- original_num_qubits: `{compression.get('original_num_qubits')}`",
                f"- compressed_num_qubits: `{compression.get('compressed_num_qubits')}`",
                f"- original_fermionic_term_count: `{compression.get('original_fermionic_term_count')}`",
                f"- original_qubit_term_count: `{compression.get('original_qubit_term_count')}`",
                f"- compressed_term_count_estimate: `{compression.get('compressed_term_count_estimate')}`",
                f"- pre_term_count: `{compression.get('pre_term_count')}`",
                f"- post_term_count: `{compression.get('post_term_count')}`",
                f"- primary_rank: `{compression.get('primary_rank')}`",
                f"- secondary_rank: `{compression.get('secondary_rank')}`",
                f"- reconstruction_error_frobenius: `{compression.get('reconstruction_error_frobenius')}`",
                f"- reconstruction_error: `{compression.get('reconstruction_error')}`",
                f"- verification_status: `{compression.get('verification_status')}`",
                f"- notes: `{compression.get('notes', [])}`",
                "",
            ]
        )

    if measurement is not None:
        lines.extend(
            [
                "## Measurement Plan",
                "",
                f"- strategy: `{measurement.get('strategy')}`",
                f"- grouping_policy: `{measurement.get('grouping_policy')}`",
                f"- execution_mode: `{measurement.get('execution_mode')}`",
                f"- low_rank_aware: `{measurement.get('low_rank_aware')}`",
                f"- term_count: `{measurement.get('term_count')}`",
                f"- group_count: `{measurement.get('group_count')}`",
                f"- estimated_shot_cost: `{measurement.get('estimated_shot_cost')}`",
                f"- runtime_precision_target: `{measurement.get('runtime_precision_target')}`",
                f"- uncompressed_group_count: `{measurement.get('uncompressed_group_count')}`",
                f"- uncompressed_estimated_shot_cost: `{measurement.get('uncompressed_estimated_shot_cost')}`",
                f"- cost_reduction_ratio: `{measurement.get('cost_reduction_ratio')}`",
                f"- notes: `{measurement.get('notes', [])}`",
                "",
            ]
        )

    lines.extend(_calibration_summary_lines(data, units))
    lines.extend(_hardware_execution_lines(data))

    if perturbative is not None:
        lines.extend(
            [
                "## Perturbative Correction",
                "",
                f"- enabled: `{perturbative.get('enabled')}`",
                f"- method: `{perturbative.get('method')}`",
                f"- plugin: `{perturbative.get('plugin')}`",
                f"- active_space_energy: {_fmt_energy(perturbative.get('active_space_energy'), units)}",
                f"- reduced_active_space_energy: {_fmt_energy(perturbative.get('reduced_active_space_energy'), units)}",
                f"- compressed_active_space_energy: {_fmt_energy(perturbative.get('compressed_active_space_energy'), units)}",
                f"- perturbative_correction: {_fmt_energy(perturbative.get('perturbative_correction'), units)}",
                f"- corrected_total_energy: {_fmt_energy(perturbative.get('corrected_total_energy'), units)}",
                f"- verification_status: `{perturbative.get('verification_status')}`",
                f"- provenance: `{perturbative.get('provenance', {})}`",
                f"- notes: `{perturbative.get('notes', [])}`",
                "",
            ]
        )

    if embedding is not None:
        lines.extend(
            [
                "## Embedding Audit",
                "",
                f"- enabled: `{embedding.get('enabled')}`",
                f"- method: `{embedding.get('method')}`",
                f"- solver_plugin: `{embedding.get('solver_plugin')}`",
                f"- bath_threshold: `{embedding.get('bath_threshold')}`",
                f"- verification_status: `{embedding.get('verification_status')}`",
                f"- environment_metadata: `{embedding.get('environment_metadata', {})}`",
                f"- notes: `{embedding.get('notes', [])}`",
                "",
            ]
        )
        for fragment in embedding.get("fragments", []):
            lines.append(
                f"- fragment_name=`{fragment.get('name')}` atom_indices=`{fragment.get('atom_indices')}` "
                f"ao_count=`{fragment.get('ao_count')}` recommended_active_space=`{fragment.get('recommended_active_space')}`"
            )
        lines.append("")

    if tc_qsci is not None:
        lines.extend(
            [
                "## TC-Kicked QSCI",
                "",
                f"- algorithm_name: `{tc_qsci.get('algorithm_name')}`",
                f"- verification_status: `{tc_qsci.get('verification_status')}`",
                f"- resource_estimation_only: `{tc_qsci.get('resource_estimation_only')}`",
                f"- solver_energy: {_fmt_energy(tc_qsci.get('solver_energy'), units)}",
                f"- electronic_energy: {_fmt_energy(tc_qsci.get('electronic_energy'), units)}",
                f"- total_energy: {_fmt_energy(tc_qsci.get('total_energy'), units)}",
                f"- subspace_dimension: `{tc_qsci.get('subspace_dimension')}`",
                f"- selected_probability_mass: `{tc_qsci.get('selected_probability_mass')}`",
                f"- initial_state: `{tc_qsci.get('initial_state')}`",
                f"- kick: `{tc_qsci.get('kick')}`",
                f"- notes: `{tc_qsci.get('notes', [])}`",
                "",
                "## Determinant Selection",
                "",
                f"- determinant_selection: `{determinant_selection}`",
                f"- symmetry_sector: `{symmetry_sector}`",
                "",
                "## CAST-QC Hamiltonian",
                "",
                f"- cast_hamiltonian: `{cast_hamiltonian}`",
                "",
                "## TC-QSCI Resource Estimates",
                "",
                f"- low_rank_resource_estimate: `{low_rank_resource}`",
                f"- qpe_resource_estimate: `{qpe_resource}`",
                "",
                "## TC-QSCI Error Budget",
                "",
                f"- error_budget: `{error_budget}`",
                "",
            ]
        )

    if variational is not None:
        lr_ace = (variational.get("ansatz") or {}).get("lr_ace") if isinstance(variational.get("ansatz"), dict) else None
        lines.extend(
            [
                "## Variational Result",
                "",
                f"- available: `{variational['available']}`",
                f"- solver_kind: `{variational['solver_kind']}`",
                f"- optimizer: `{variational['optimizer']}`",
                f"- ansatz: `{variational['ansatz']}`",
                f"- initial_point_strategy: `{variational['initial_point_strategy']}`",
                f"- parameter_count: `{variational['parameter_count']}`",
                f"- converged: `{variational['converged']}`",
                f"- iterations: `{variational['iterations']}`",
                f"- evaluations: `{variational['evaluations']}`",
                f"- final_objective_energy: {_fmt_energy(variational.get('final_objective_energy'), units)}",
                f"- optimizer_message: `{variational.get('optimizer_message')}`",
                "",
            ]
        )
        if isinstance(lr_ace, dict):
            lines.extend(
                [
                    "## LR-ACE Exploratory Algorithm",
                    "",
                    f"- algorithm_name: `{lr_ace.get('algorithm_name')}`",
                    f"- low_rank_method: `{lr_ace.get('low_rank_method')}`",
                    f"- factor_rank: `{lr_ace.get('factor_rank')}`",
                    f"- selected_factor_count: `{lr_ace.get('selected_factor_count')}`",
                    f"- local_accuracy_gate: `{lr_ace.get('local_accuracy_gate')}`",
                    f"- selected_generators: `{lr_ace.get('selected_generators')}`",
                    "",
                ]
            )

    if sampled is not None:
        lines.extend(
            [
                "## Sampled Result",
                "",
                f"- available: `{sampled['available']}`",
                f"- backend_kind: `{sampled['backend_kind']}`",
                f"- shots: `{sampled['shots']}`",
                f"- num_repeats: `{sampled['num_repeats']}`",
                f"- seed: `{sampled.get('seed')}`",
                f"- repeat_seeds: `{sampled.get('repeat_seeds')}`",
                f"- sampled_solver_energy_mean: {_fmt_energy(sampled.get('sampled_solver_energy_mean'), units)}",
                f"- sampled_solver_energy_std: {_fmt_energy(sampled.get('sampled_solver_energy_std'), units)}",
                f"- sampled_electronic_energy_mean: {_fmt_energy(sampled.get('sampled_electronic_energy_mean'), units)}",
                f"- sampled_total_energy_mean: {_fmt_energy(sampled.get('sampled_total_energy_mean'), units)}",
                f"- standard_error: {_fmt_energy(sampled.get('standard_error'), units)}",
                f"- confidence_interval_low: {_fmt_energy(sampled.get('confidence_interval_low'), units)}",
                f"- confidence_interval_high: {_fmt_energy(sampled.get('confidence_interval_high'), units)}",
                "",
            ]
        )

    if excited is not None:
        lines.extend(
            [
                "## Excited-state Result",
                "",
                f"- method: `{excited['method']}`",
                f"- verification_status: `{excited['verification_status']}`",
                f"- notes: `{excited.get('notes', [])}`",
                "",
            ]
        )
        for state in excited.get("states", []):
            lines.append(
                f"- state_index=`{state['state_index']}` "
                f"excitation_energy={_fmt_energy(state.get('excitation_energy'), units)} "
                f"verification_status=`{state.get('verification_status')}`"
            )
        lines.append("")

    if properties is not None:
        lines.extend(
            [
                "## Property Result",
                "",
                f"- verification_status: `{properties['verification_status']}`",
                "",
            ]
        )
        for item in properties.get("properties", []):
            lines.append(
                f"- property_name=`{item['property_name']}` method=`{item['method']}` "
                f"implementation_status=`{item['implementation_status']}` value=`{item.get('value')}` "
                f"components=`{item.get('components', {})}` provenance=`{item.get('provenance', {})}`"
            )
        lines.append("")

    lines.extend(
        [
            "## Mitigation",
            "",
            f"- symmetry_check: `{mitigation.get('symmetry_check')}`",
            f"- readout_mitigation: `{mitigation.get('readout_mitigation')}`",
            f"- zne: `{mitigation.get('zne')}`",
            f"- pec: `{mitigation.get('pec')}`",
            f"- applied_methods: `{mitigation.get('applied_methods', [])}`",
            "",
            "## Provenance",
            "",
            f"- Schema version: `{data['schema_version']}`",
            f"- Timestamp: `{provenance['timestamp']}`",
            f"- Wall time (s): `{provenance['wall_time_seconds']}`",
            f"- Git commit: `{provenance['git_commit']}`",
            f"- Git commit short: `{provenance.get('git_commit_short')}`",
            f"- Git branch: `{provenance.get('git_branch')}`",
            f"- Git describe: `{provenance.get('git_describe')}`",
            f"- Git remote origin: `{provenance.get('git_remote_origin')}`",
            f"- Repo root: `{provenance.get('repo_root')}`",
            f"- Workspace dirty: `{provenance['workspace_dirty']}`",
            f"- Git status summary: `{provenance.get('git_status_summary', {})}`",
            f"- Workspace fingerprint: `{provenance.get('workspace_fingerprint')}`",
            f"- Dependency versions: `{provenance['dependency_versions']}`",
            f"- Seed: `{provenance['seed']}`",
            f"- Source config: `{provenance['source_config']}`",
            "",
            "## Artifacts",
            "",
            f"- result.json: `{data['artifacts']['result_json']}`",
            f"- exact_result.json: `{data['artifacts']['exact_result_json']}`",
            f"- report.md: `{data['artifacts']['report_markdown']}`",
            f"- resolved_config.yaml: `{data['artifacts']['resolved_config']}`",
            f"- run.log: `{data['artifacts']['log_file']}`",
            f"- calibration.json: `{data['artifacts'].get('calibration_json')}`",
            f"- calibration_report.md: `{data['artifacts'].get('calibration_report_markdown')}`",
            f"- runtime_submission.json: `{data['artifacts'].get('runtime_submission_json')}`",
            f"- qcschema.json: `{data['artifacts'].get('qcschema_json')}`",
            f"- result.h5: `{data['artifacts'].get('hdf5_file')}`",
            "",
            "## Log Summary",
            "",
        ]
    )
    lines.extend(f"- {event}" for event in data["log_summary"]["events"])
    lines.append("")
    return "\n".join(lines)


def write_markdown_report(result: Any, path: Path) -> None:
    """Write the Markdown report for a QCchem result."""
    path.write_text(render_markdown_report(result), encoding="utf-8")


def render_calibration_report(result: Any) -> str:
    """Render a focused calibration report from a QCchem run result."""
    data = to_primitive(result)
    calibration = data.get("calibration") or {}
    runtime_submission = data.get("runtime_submission") or {}
    measurement = data.get("measurement") or {}
    benchmark = data.get("benchmark") or {}
    return "\n".join(
        [
            f"# QCchem Calibration Report: {data['problem']['molecule_name']}",
            "",
            "## Measurement",
            "",
            f"- strategy: `{measurement.get('strategy')}`",
            f"- group_count: `{measurement.get('group_count')}`",
            f"- estimated_measurement_cost: `{measurement.get('estimated_shot_cost')}`",
            f"- precision_target: `{measurement.get('runtime_precision_target')}`",
            "",
            "## Empirical Calibration",
            "",
            f"- measured_wall_time_seconds: `{calibration.get('measured_wall_time_seconds')}`",
            f"- measured_shot_usage: `{calibration.get('measured_shot_usage')}`",
            f"- achieved_error: `{benchmark.get('absolute_error')}`",
            f"- estimated_vs_measured_cost: `{calibration.get('estimated_vs_measured_cost')}`",
            "",
            "## Runtime Attempt",
            "",
            f"- attempted: `{runtime_submission.get('attempted')}`",
            f"- submitted: `{runtime_submission.get('submitted')}`",
            f"- failure_category: `{runtime_submission.get('failure_category')}`",
            f"- provider: `{runtime_submission.get('provider')}`",
            f"- backend_name: `{runtime_submission.get('backend_name')}`",
            "",
        ]
    )


def write_calibration_report(result: Any, path: Path) -> None:
    """Write a focused calibration report."""
    path.write_text(render_calibration_report(result), encoding="utf-8")
