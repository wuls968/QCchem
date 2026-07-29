# QCchem Report: H2-q-embed

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-q-embed`
- basis: `sto3g`
- method: `statevector`
- mapping_kind: `jordan_wigner`
- num_qubits: `1`
- verification_status: `validated`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137306035753` Hartree
- headline_correlation_energy: `-0.020307038999` Hartree
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `exact_baseline`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_q_embed', 'molecule_name': 'H2-q-embed', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `H2-q-embed stays within chemical accuracy against exact_baseline for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 0.0, 'units': 'Hartree', 'threshold': 1e-08, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `H2-q-embed stays within chemical accuracy against exact_baseline for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 0.0, 'relative_error': 0.0, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.07791916700080037, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': [], 'scientific_risk_notes': [], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:43.555138+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed`

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

- verification_status: `validated`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `validated`
- Verification Notes: `[]`
- Scientific Risk Notes: `[]`

## Energy Summary

- electronic_energy: `-1.857275030202` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-1.137306035753` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.857275030202` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020307038999` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `0.000000000000` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`

## Field Definitions

- `solver_energy` is the raw energy returned by the configured solver on the mapped qubit Hamiltonian.
- `exact_ground_energy` is the raw exact-diagonalization energy of that same mapped Hamiltonian.
- `electronic_energy` is QCchem's corrected electronic energy after adding any non-nuclear Hamiltonian constants, such as active-space offsets.
- `external_point_charge_nuclear_interaction_energy` is the explicit QM nuclei/static point-charge Coulomb constant; MM-MM and non-electrostatic environment terms are not included.
- `boundary_embedding_constant_energy` is the explicit constant generated by boundary embedding; the first implementation records a zero constant unless a nonzero boundary projector is supplied.
- `total_energy` is reconstructed from the explicit `energy_formula`, so active-space and transformed problems remain auditable.
- `hf_reference_energy` is the Hartree-Fock total reference energy exposed by Qiskit Nature.
- `correlation_energy` is `total_energy - hf_reference_energy` and therefore measures post-HF improvement in the total-energy convention.

## Exact Baseline

- available: `True`
- source: `exact_diagonalization`
- solver_hamiltonian_energy: `-1.857275030202` Hartree
- electronic_energy: `-1.857275030202` Hartree
- total_energy: `-1.137306035753` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-1.857275030202` Hartree
- exact_total_energy: `-1.137306035753` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `0.0`
- statistical_error: `None`
- absolute_error_threshold: `1e-08`
- relative_error_threshold: `1e-08`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/quantum_evidence.json`
- sidecar_sha256: `01c93c711436f12c2e0359fd5dd175531694f0a79be5730dc8fa3325fb263bc9`
- pauli_terms_available: `True`
- pauli_unavailable_reason: `None`
- pauli_term_count: `3`
- measurement_group_count: `2`
- energy_contribution_sum: `-1.857275030202` Hartree
- coefficient_l1_norm: `2.0178991909872144`
- projected_matrix_dimension: `None`
- projected_hamiltonian_nnz: `None`
- physical_sector_dimension: `None`
- basis_hash: `None`
- projected_matrix_sha256: `None`
- groups_sha256: `709c84fbcf66765924c44c58f1738014433d1afca44aa6ec2f81c6293e737634`
- measurement_group_count_scope: `pauli_grouping`
- estimated_measurement_cost_scope: `pauli_grouping`
- estimated_measurement_cost_is_hardware_cost: `None`
- sparse_exploratory_estimated_measurement_cost: `None`
- counts_available: `True`
- counts_source: `statevector_sampler_from_final_state`
- counts_sha256: `b0593a03b071c1204b45ac0caffa14b6d10dbdde0c56cbdcddaed3676f47d5e6`
- shots_per_group: `4096`
- hamiltonian_variance: `4.440892098500626e-16`
- ground_state_overlap: `0.9999999999999998`
- dominant_configurations: `[{'bitstring': '0', 'probability': 0.9875597343674857}, {'bitstring': '1', 'probability': 0.01244026563251424}]`
- z2_check: `{'status': 'applied_z2', 'z2_symmetry_count': 3, 'z2_tapering_values': [-1, 1, -1], 'validation': {'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.8572750302023777, 'tapered_ground_energy': -1.8572750302023788, 'absolute_delta': 1.1102230246251565e-15}, 'notes': ['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=1.11022e-15 Hartree.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 1, 'raw_num_qubits': 4, 'qubit_term_count': 3, 'raw_qubit_term_count': 15, 'circuit_depth': None, 'two_qubit_gate_count': None, 'operation_counts': {}}`
- error_budget: `{'ansatz_error': {'available': False, 'absolute_error_hartree': 0.0, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
- eigen_residual_norm: `None`
- relative_eigen_residual: `None`
- ground_state_gap: `None`
- lowest_eigenvalues: `None`
- sparse_exact_validation: `{}`
- lattice_qed_observables: `{}`
- notes: `[]`

## Method Evidence

> Exploratory method outputs are reported alongside the raw solver energy; they do not replace the primary energy or promote validation status by themselves.

- available: `True`
- schema: `qcchem.method_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/method_evidence.json`
- sidecar_sha256: `3d66ab94eabf4dba1e89c108c2074a051a5c526dd42e412244c264915a929bd6`
- methods: `{'q_embed': {'available': True, 'trust_tier': 'exploratory'}}`
- promotion_gate_audit: `{'schema': 'qcchem.method_promotion_gate_audit.v1', 'primary_solver_kind': 'exact', 'primary_energy_policy': 'raw_solver_energy_remains_primary', 'sidecar_energy_replacement_allowed_methods': [], 'accuracy_claim_allowed_methods': [], 'hardware_claim_allowed_methods': [], 'planning_metric_methods': [], 'resource_model_only_methods': [], 'unsupported_for_claim_methods': [], 'method_records': {'q_embed': {'method': 'q_embed', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'fragment_reference_only', 'evidence_role': 'embedding_fragment_reference_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['q_dmet_self_consistency_not_executed', 'density_matching_not_performed', 'fragment_energy_sum_does_not_replace_primary'], 'density_mismatch_audit_status': 'balanced_reference_density', 'fragment_coverage_status': 'complete_nonoverlapping_fragment_coverage', 'fragment_ao_coverage_fraction': 1.0, 'fragment_atom_coverage_fraction': 1.0, 'self_consistency_iteration_count': 0, 'density_matching_iteration_count': 0, 'correlation_potential_parameter_count': 0, 'missing_self_consistency_components': ['correlation_potential_optimizer', 'density_matching_loop', 'bath_update_loop']}}, 'overall_claim_status': 'promotion_required', 'promotion_required_for_validated_claims': True, 'notes': ['Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.', 'Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.']}`
- trust_tier: `exploratory`
- notes: `['Method evidence is reported alongside the primary solver result.', 'Exploratory method sections do not promote chemical-accuracy claims by themselves.']`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.7199689944489797}`
- Electronic constant correction: `0.000000000000` Hartree
- Point-group metadata: `{'enabled': True, 'status': 'available', 'group': 'Dooh', 'topgroup': 'Dooh', 'irrep_names': ['A1g', 'A1u'], 'irrep_ids': [0, 5], 'notes': [], 'orbital_irreps': ['A1g', 'A1u'], 'orbital_occupations': [2.0, 0.0], 'orbital_energies': [-0.5806289181997333, 0.6763362534452201], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `1`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `3`
- Raw qubit count: `4`
- Raw qubit Hamiltonian terms: `15`
- Symmetry tapered qubits: `3`
- Z2 symmetry count: `3`
- Z2 tapering values: `[-1, 1, -1]`
- Symmetry reduction status: `applied_z2`
- Symmetry reduction validation: `{'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.8572750302023777, 'tapered_ground_energy': -1.8572750302023788, 'absolute_delta': 1.1102230246251565e-15}`
- Symmetry reduction notes: `['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=1.11022e-15 Hartree.']`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `None`
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

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- absolute_error_kcal_mol: `0.0`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- finite_model_exactness: `{}`
- continuum_chemistry_accuracy: `{}`
- hardware_accuracy: `{}`
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
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.7199689944489797}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_constant_correction: `0.719968994449` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`
- point_group_metadata: `{'enabled': True, 'status': 'available', 'group': 'Dooh', 'topgroup': 'Dooh', 'irrep_names': ['A1g', 'A1u'], 'irrep_ids': [0, 5], 'notes': [], 'orbital_irreps': ['A1g', 'A1u'], 'orbital_occupations': [2.0, 0.0], 'orbital_energies': [-0.5806289181997333, 0.6763362534452201], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Reduction Plan

- enabled: `True`
- mode: `disabled`
- strategy: `none`
- recommended_changes: `{}`
- notes: `['No reduction planning inputs were requested.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `3`
- group_count: `2`
- estimated_shot_cost: `20000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `20000.0`
- cost_reduction_ratio: `1.0`
- planner: `default`
- shadow_bases: `[]`
- shot_allocation: `[]`
- predicted_variance: `None`
- measurement_cost_model: `{}`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `9.683399912319146e-05`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `20000.0`
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

## Embedding Audit

- enabled: `True`
- method: `q_dmet`
- solver_plugin: `qcchem_fragment_exact`
- bath_threshold: `0.05`
- verification_status: `exploratory`
- embedding_execution_status: `fragment_reference_only`
- self_consistency_loop_executed: `False`
- density_matching_performed: `False`
- fragment_energy_sum_replaces_primary: `False`
- environment_metadata: `{'environment_model': 'mean_field_density_matrix', 'mean_field_energy': -1.1169989967540035, 'num_fragments': 2, 'fragment_execution': {'execution_enabled': True, 'plugin': 'pyscf_rhf_fragment', 'fragment_energy_sum': -0.9331636991145507, 'full_system_mean_field_energy': -1.1169989967540035, 'fragment_count_executed': 2, 'validate_against_full_system': True}, 'embedding_method': 'q_dmet', 'embedding_execution_status': 'fragment_reference_only', 'bath_orbitals': [{'fragment': 'left_h', 'recommended_active_space': {'num_spatial_orbitals': 2, 'num_electrons': 2}}, {'fragment': 'right_h', 'recommended_active_space': {'num_spatial_orbitals': 2, 'num_electrons': 2}}], 'density_mismatch_history': [{'macro_iteration': 0, 'density_mismatch_norm': 7.021666937153402e-16, 'density_mismatch_l1_norm': 8.881784197001252e-16, 'density_mismatch_signed_sum': -4.440892098500626e-16, 'max_fragment_population_delta_abs': 6.661338147750939e-16, 'density_mismatch_threshold': 1e-08, 'metric': 'fragment_population_delta_norm', 'status': 'reference_audit_only', 'mismatch_status': 'balanced_reference_density', 'reason': 'q-DMET self-consistency loop is not implemented in v1; this is a one-shot fragment population audit.'}], 'density_mismatch_audit': {'metric': 'fragment_population_delta', 'l2_norm': 7.021666937153402e-16, 'l1_norm': 8.881784197001252e-16, 'signed_sum': -4.440892098500626e-16, 'max_abs': 6.661338147750939e-16, 'threshold': 1e-08, 'status': 'balanced_reference_density', 'density_matching_performed': False, 'density_matching_iteration_count': 0, 'self_consistency_iteration_count': 0}, 'fragment_coverage_audit': {'total_ao_count': 2, 'covered_ao_count': 2, 'unassigned_ao_count': 0, 'overlapping_ao_assignment_count': 0, 'ao_coverage_fraction': 1.0, 'total_atom_count': 2, 'covered_atom_count': 2, 'unassigned_atom_count': 0, 'overlapping_atom_assignment_count': 0, 'atom_coverage_fraction': 1.0, 'status': 'complete_nonoverlapping_fragment_coverage'}, 'fragment_density_audit': [{'fragment': 'left_h', 'atom_indices': [0], 'ao_indices': [0], 'full_system_gross_population': 1.0000000000000002, 'neutral_fragment_electron_count': 1, 'population_delta': 2.220446049250313e-16, 'population_delta_abs': 2.220446049250313e-16, 'status': 'reference_audit_only', 'density_matching_performed': False}, {'fragment': 'right_h', 'atom_indices': [1], 'ao_indices': [1], 'full_system_gross_population': 0.9999999999999993, 'neutral_fragment_electron_count': 1, 'population_delta': -6.661338147750939e-16, 'population_delta_abs': 6.661338147750939e-16, 'status': 'reference_audit_only', 'density_matching_performed': False}], 'self_consistency_loop_executed': False, 'self_consistency_converged': False, 'self_consistency_iteration_count': 0, 'density_matching_iteration_count': 0, 'correlation_potential_parameter_count': 0, 'embedding_boundary_audit': {'fragment_count': 2, 'bath_threshold': 0.05, 'assembled_energy_replaces_primary': False, 'fragment_energy_sum_replaces_primary': False, 'fragment_reference_execution_validated': True, 'fragment_population_delta_norm': 7.021666937153402e-16, 'fragment_population_delta_l1_norm': 8.881784197001252e-16, 'fragment_population_delta_signed_sum': -4.440892098500626e-16, 'max_fragment_population_delta_abs': 6.661338147750939e-16, 'density_mismatch_status': 'balanced_reference_density', 'fragment_energy_sum_gap_hartree': 0.18383529763945283, 'fragment_energy_sum_gap_abs_hartree': 0.18383529763945283, 'fragment_energy_sum_gap_per_fragment_hartree': 0.09191764881972642, 'self_consistency_loop_executed': False, 'self_consistency_iteration_count': 0, 'density_matching_performed': False, 'density_matching_iteration_count': 0, 'correlation_potential_optimized': False, 'correlation_potential_parameter_count': 0, 'fragment_ao_coverage_fraction': 1.0, 'fragment_atom_coverage_fraction': 1.0, 'fragment_coverage_status': 'complete_nonoverlapping_fragment_coverage', 'missing_self_consistency_components': ['correlation_potential_optimizer', 'density_matching_loop', 'bath_update_loop'], 'trust_gate': 'exploratory'}, 'fragment_solvers': {'left_h': 'exact', 'right_h': 'exact'}}`
- notes: `['Current embedding path is a DMET-style skeleton built from PySCF mean-field density information.', 'Fragment execution is validated only for PySCF RHF/UHF small-fragment reference runs; assembled embedding energy is a diagnostic, not a replacement for the full-system benchmark.', 'Q-Embed/q-DMET v1 records fragment, bath, and optional fragment-reference diagnostics only.', 'No q-DMET self-consistency, density matching, or correlation-potential optimization is executed in v1.', 'Fragment reference energies are diagnostics and do not replace the primary full-system energy.']`

- fragment_name=`left_h` atom_indices=`[0]` ao_count=`1` recommended_active_space=`{'num_spatial_orbitals': 2, 'num_electrons': 2}`
- fragment_name=`right_h` atom_indices=`[1]` ao_count=`1` recommended_active_space=`{'num_spatial_orbitals': 2, 'num_electrons': 2}`

## Mitigation

- symmetry_check: `{'requested': True, 'effective_requested': False, 'performed': False, 'status': 'no_checks_requested', 'strategy': 'parity_placeholder', 'requested_checks': {'particle_number': False, 'spin_parity': False, 'z2_sector': False}, 'postselection_rate': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'calibration_shots': 0, 'calibration_digest': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- zne: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'folding': 'global', 'scale_factors': [1.0, 1.5, 2.0, 3.0], 'extrapolator': 'linear', 'zne_curve': [], 'variance_inflation': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- pec: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'calibration_model': None, 'calibration_model_audit': {'provided': False, 'exists': False, 'executable': False, 'status': 'missing_calibration_model', 'digest': None, 'schema': None, 'calibrated_operation_count': 0, 'quasi_probability_entry_count': 0, 'max_operation_l1_overhead': None}, 'executable_calibration_model': False, 'sampling_overhead': 0.0, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'claim_scope': None, 'energy_replaces_primary': False}`
- requested_methods: `[]`
- applied_methods: `[]`
- claim_allowed_methods: `[]`
- claim_status: `not_requested`
- energy_replaces_primary: `False`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`f17f21bd4c0255c706d3cf8377ac9a5f1dcfa6c8cd1dc5a67bdb5d0cf7596534`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-07-08T04:20:43.555138+00:00`
- Wall time (s): `0.07791916700080037`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `306d4ba17c2458f1d3916ab3745507c6bc7cf060110c55e7b52ac4ca8637dc71`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `37`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_q_embed.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/quantum_evidence.json`
- qcschema.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/qcschema.json`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_q_embed.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=f17f21bd4c02
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=2, cost=20000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/exact_result.json
- Computed empirical calibration: wall_time=0.000s, measured_cost=None
- Computed embedding audit: q_dmet
- Wrote integrated method evidence sidecar
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_q_embed/report.md
- Run completed
