# QCchem Report: H2-cavity-PF-exact

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-cavity-PF-exact`
- basis: `sto3g`
- method: `statevector`
- mapping_kind: `pauli_fierz_cavity_qed:jordan_wigner+bosonic_linear`
- num_qubits: `6`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137776186388` Hartree
- headline_correlation_energy: `-0.021016878992` Hartree
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `exact_baseline`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_cavity_pf_exact_cutoff_1', 'molecule_name': 'H2-cavity-PF-exact', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'pauli_fierz_cavity_qed:jordan_wigner+bosonic_linear', 'field_model_kind': 'pauli_fierz_cavity_qed'}`
- primary_scientific_claim: `H2-cavity-PF-exact Pauli-Fierz cavity-QED result uses a finite photon cutoff and is compared against exact_baseline within the configured electron-photon Hamiltonian.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 2.220446049250313e-15, 'units': 'Hartree', 'threshold': 1e-09, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-cavity-PF-exact Pauli-Fierz cavity-QED result uses a finite photon cutoff and is compared against exact_baseline within the configured electron-photon Hamiltonian.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 2.220446049250313e-15, 'relative_error': 1.1983751886474872e-15, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.09386629197979346, 'shots': None, 'measurement_strategy': 'cavity_qed_exact', 'measurement_group_count': 9, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': 'pauli_fierz_cavity_qed'}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'exploratory', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=pauli_fierz_cavity_qed_finite_photon_cutoff'], 'scientific_risk_notes': ['Pauli-Fierz cavity-QED execution uses a finite photon cutoff.', 'Exact baselines compare against the configured electron-photon Hamiltonian, not an external cavity-QED benchmark.', 'Photon cutoff convergence and gauge-form comparisons require explicit follow-up studies.', 'Exploratory Pauli-Fierz cavity-QED Hamiltonian with finite photon cutoff.', 'Exact baselines are exact only for the configured electron-photon qubit Hamiltonian.']}`
- provenance_timestamp: `2026-05-15T13:03:20.976813+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- threshold_hartree: `0.0016`
- distance_to_chemical_accuracy: `0.0`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Runtime Evidence

> Runtime evidence is surfaced explicitly so exported reports separate chemistry confidence from execution provenance.

- hardware_verified: `False`
- hardware_evidence_tier: `None`
- service: `None`
- provider: `None`
- backend_name: `None`
- job_id: `None`
- verification_status: `None`
- layout_strategy: `None`
- selected_layout: `[]`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`

## Verification

- verification_status: `exploratory`

## Validation Boundary

- Module Origin: `exploratory`
- Capability Tier: `exploratory`
- Verification Notes: `['validation_scope=pauli_fierz_cavity_qed_finite_photon_cutoff']`
- Scientific Risk Notes: `['Pauli-Fierz cavity-QED execution uses a finite photon cutoff.', 'Exact baselines compare against the configured electron-photon Hamiltonian, not an external cavity-QED benchmark.', 'Photon cutoff convergence and gauge-form comparisons require explicit follow-up studies.', 'Exploratory Pauli-Fierz cavity-QED Hamiltonian with finite photon cutoff.', 'Exact baselines are exact only for the configured electron-photon qubit Hamiltonian.']`

## Energy Summary

- electronic_energy: `-1.852880525469` Hartree
- nuclear_repulsion_energy: `0.715104339081` Hartree
- total_energy: `-1.137776186388` Hartree
- hf_reference_energy: `-1.116759307396` Hartree
- solver_energy: `-1.852880525469` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.852880525469` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.021016878992` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `0.000000000000` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Field Definitions

- `solver_energy` is the raw energy returned by the configured solver on the mapped qubit Hamiltonian.
- `exact_ground_energy` is the raw exact-diagonalization energy of that same mapped Hamiltonian.
- `electronic_energy` is QCchem's corrected electronic energy after adding any non-nuclear Hamiltonian constants, such as active-space offsets.
- `total_energy` is reconstructed from the explicit `energy_formula`, so active-space and transformed problems remain auditable.
- `hf_reference_energy` is the Hartree-Fock total reference energy exposed by Qiskit Nature.
- `correlation_energy` is `total_energy - hf_reference_energy` and therefore measures post-HF improvement in the total-energy convention.

## Exact Baseline

- available: `True`
- source: `exact_diagonalization`
- solver_hamiltonian_energy: `-1.852880525469` Hartree
- electronic_energy: `-1.852880525469` Hartree
- total_energy: `-1.137776186388` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-1.852880525469` Hartree
- exact_total_energy: `-1.137776186388` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `1.1983751886474872e-15`
- statistical_error: `None`
- absolute_error_threshold: `1e-09`
- relative_error_threshold: `1e-09`
- within_uncertainty: `None`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.7151043390810812}`
- Electronic constant correction: `0.000000000000` Hartree

## Mapping

- Mapping kind: `pauli_fierz_cavity_qed:jordan_wigner+bosonic_linear`
- Qubit count: `6`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `44`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `2141`
- Repetitions: `1`
- Abelian grouping: `True`
- Noise enabled: `False`
- Runtime enabled: `False`

## Backend Capability

- backend_kind: `statevector`
- statevector: `True`
- shot_based: `False`
- exact_baseline: `True`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- mitigation_ready: `False`
- noise_model_ready: `False`
- supports_grouping: `False`
- supports_repetitions: `False`
- supports_confidence_metrics: `False`

## Execution Policy

- name: `benchmark`
- default_shots: `None`
- default_repetitions: `5`
- exact_baseline_required: `True`
- confidence_rule: `require exact baseline when available; use repeated sampling for shot backends`
- mitigation_posture: `symmetry-check preferred`
- runtime_ready_expected: `False`
- session_ready_expected: `False`
- batch_ready_expected: `False`
- noise_ready_expected: `False`

## Field Model Registry

- model_kind: `pauli_fierz_cavity_qed`
- registry_name: `molecular_pauli_fierz_cavity_qed`
- capability_tier: `exploratory`
- observables: `['photon_occupation', 'dipole_expectation', 'electron_photon_coupling_energy', 'dipole_self_energy', 'polaritonic_state_composition', 'photon_cutoff_convergence']`
- resource_estimate: `{'electronic_qubits': 4, 'photon_qubits': 2, 'total_qubits': 6, 'pauli_terms': 44, 'mode_qubits': [2]}`
- error_budget: `{'photon_cutoff': {'max_occupation_by_mode': [1], 'status': 'finite_cutoff_configured'}, 'exact_residual_norm': 5.905809130943007e-15, 'vqe_vs_exact_error': 2.220446049250313e-15, 'photon_encoding_leakage': 4.905374718084259e-32}`
- risk_notes: `['Pauli-Fierz cavity-QED evidence is exact or variational only for the configured photon cutoff.', 'External cavity-QED benchmark validation is outside this first QCchem milestone.']`

## Pauli-Fierz Cavity-QED Model

> This section reports exploratory molecular cavity-QED evidence for the configured finite photon cutoff; exact baselines are exact for this electron-photon Hamiltonian only.

- model: `pauli_fierz_cavity_qed`
- mode_count: `1`
- modes: `[{'mode_index': 0, 'frequency': 0.4, 'coupling_strength': 0.04, 'polarization': [0.0, 0.0, 1.0], 'max_occupation': 1, 'mode_qubits': 2}]`
- photon_encoding: `linear`
- include_dipole_self_energy: `True`
- photon_physical_subspace_penalty: `25.0`
- electronic_qubits: `4`
- photon_qubits: `2`
- total_qubits: `6`
- hamiltonian_formula: `H = H_e + sum_m omega_m a_m^dagger a_m + sum_m g_m (e_m dot mu)(a_m + a_m^dagger) + 1/2 sum_m g_m^2 (e_m dot mu)^2`
- term_counts_by_sector: `{'electronic': 15, 'photon': 4, 'electron_photon_coupling': 18, 'dipole_self_energy': 19, 'photon_physical_subspace_penalty': 2, 'total': 44}`
- photon occupation: `[{'mode_index': 0, 'expectation': 0.0011422899425083694}]`
- dipole_expectation: `[{'mode_index': 0, 'expectation': -2.226508017631093e-09}]`
- electron_photon_coupling_energy: `[{'mode_index': 0, 'expectation': -0.0031348885143326352}]`
- dipole_self_energy: `[{'mode_index': 0, 'expectation': 0.0010785846635300766}]`
- polaritonic_state_composition: `[{'component': 'electronic_marginal_x_photon_occupation', 'mode_index': 0, 'occupation': 0, 'max_occupation': 1, 'weight': 0.9988577100574908}, {'component': 'electronic_marginal_x_photon_occupation', 'mode_index': 0, 'occupation': 1, 'max_occupation': 1, 'weight': 0.0011422899425083694}, {'component': 'exact_ground_state_photon_marginal', 'mode_index': 0, 'mean_photon_occupation': 0.0011422899425083694}]`
- photon_physical_subspace_leakage: `4.905374718084259e-32`
- exact_residual_norm: `5.905809130943007e-15`
- vqe_vs_exact_error: `2.220446049250313e-15`
- resource_estimate: `{'electronic_qubits': 4, 'photon_qubits': 2, 'total_qubits': 6, 'pauli_terms': 44, 'mode_qubits': [2]}`
- error_budget: `{'photon_cutoff': {'max_occupation_by_mode': [1], 'status': 'finite_cutoff_configured'}, 'exact_residual_norm': 5.905809130943007e-15, 'vqe_vs_exact_error': 2.220446049250313e-15, 'photon_encoding_leakage': 4.905374718084259e-32}`
- notes: `['Exploratory Pauli-Fierz cavity-QED Hamiltonian with finite photon cutoff.', 'Exact baselines are exact only for the configured electron-photon qubit Hamiltonian.']`

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- absolute_error_kcal_mol: `1.393350932410442e-12`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Reduction Audit

- original_num_particles: `(1, 1)`
- original_num_spatial_orbitals: `2`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `[]`
- active_space_metadata: `None`
- selection_mode: `none`
- selection_reason: `No active-space reduction requested.`
- selected_active_orbitals: `[]`
- selected_active_orbitals_original: `[]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.7151043390810812}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.715104339081` Hartree
- total_constant_correction: `0.715104339081` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Reduction Plan

- enabled: `True`
- mode: `disabled`
- strategy: `none`
- recommended_changes: `{}`
- notes: `['No reduction planning inputs were requested.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `cavity_qed_exact`
- grouping_policy: `electron_photon_pauli`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `44`
- group_count: `9`
- estimated_shot_cost: `90000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `5`
- uncompressed_estimated_shot_cost: `50000.0`
- cost_reduction_ratio: `1.8`
- notes: `["Measurement groups estimated with strategy 'cavity_qed_exact'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.00116379203973338`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `90000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `exact_baseline`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Hardware Execution

- hardware_verified: `False`
- hardware_evidence_tier: `None`
- attempted: `None`
- submitted: `None`
- succeeded: `None`
- service: `None`
- mode: `None`
- session_requested: `None`
- batch_requested: `None`
- backend_name: `None`
- provider: `None`
- layout_strategy: `None`
- selected_layout: `[]`
- layout_score: `None`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`
- transpilation_options: `{}`
- job_id: `None`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `None`
- usage_estimation: `{}`
- job_metrics: `{}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `None`
- options_snapshot: `{}`
- returned_job_metadata: `{}`
- result_provenance: `{}`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-15T13:03:20.976813+00:00`
- Wall time (s): `0.09386629197979346`
- Git commit: `164b7ff23843a5187d6aeba0c0bbd1bc2e3f287b`
- Git commit short: `164b7ff23843`
- Git branch: `HEAD`
- Git describe: `164b7ff-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/c397/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 15, 'untracked': 14}`
- Workspace fingerprint: `4a9e9c26adf633bf81af34cd642f7e6faa61d3ac4e0c66bae7dd57d4e9195eea`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `2141`
- Source config: `/Users/a0000/.codex/worktrees/c397/QCchem/configs/exploratory/h2_cavity_pf_exact.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/c397/QCchem/configs/exploratory/h2_cavity_pf_exact.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Building exploratory Pauli-Fierz cavity-QED Hamiltonian
- Constructed cavity-QED Hamiltonian: modes=1, electronic_qubits=4, photon_qubits=2
- Prepared measurement plan: groups=9, cost=90000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/exact_result.json
- Computed empirical calibration: wall_time=0.001s, measured_cost=None
- Writing JSON result to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_cavity_pf_exact_cutoff_1/report.md
- Run completed
