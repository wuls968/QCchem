# QCchem Report: H2-method-evidence-smoke

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-method-evidence-smoke`
- basis: `sto3g`
- method: `shot_estimator`
- mapping_kind: `jordan_wigner`
- num_qubits: `4`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `shot_estimator`

## Hero

- headline_total_energy: `-1.137306035753` Hartree
- headline_correlation_energy: `-0.020307038999` Hartree
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `exact_baseline`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_method_evidence_smoke', 'molecule_name': 'H2-method-evidence-smoke', 'basis': 'sto3g', 'backend_kind': 'shot_estimator', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `H2-method-evidence-smoke stays within chemical accuracy against exact_baseline for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 1.9984014443252818e-15, 'units': 'Hartree', 'threshold': 1e-08, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-method-evidence-smoke stays within chemical accuracy against exact_baseline for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `qsci_tcc` / delta=`0.000000000000` Hartree
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 1.9984014443252818e-15, 'relative_error': 1.0759857381529137e-15, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.04419429100016714, 'shots': 256, 'measurement_strategy': 'default', 'measurement_group_count': 5, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': [], 'scientific_risk_notes': [], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:43.675606+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke`

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

- Module Origin: `core`
- Capability Tier: `exploratory`
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
- relative_error: `1.0759857381529137e-15`
- statistical_error: `None`
- absolute_error_threshold: `1e-08`
- relative_error_threshold: `1e-08`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/quantum_evidence.json`
- sidecar_sha256: `d99c80d39b649122f86c42b5cf64b9ab0bd147d08dd367d5d21047de111e5a83`
- pauli_terms_available: `True`
- pauli_unavailable_reason: `None`
- pauli_term_count: `15`
- measurement_group_count: `5`
- energy_contribution_sum: `-1.857275030202` Hartree
- coefficient_l1_norm: `2.7050411297549823`
- projected_matrix_dimension: `None`
- projected_hamiltonian_nnz: `None`
- physical_sector_dimension: `None`
- basis_hash: `None`
- projected_matrix_sha256: `None`
- groups_sha256: `f637ff948988d77a7adcfb87f1cec0b573a6fd28be5e8bba06c33886fc5073f4`
- measurement_group_count_scope: `pauli_grouping`
- estimated_measurement_cost_scope: `pauli_grouping`
- estimated_measurement_cost_is_hardware_cost: `None`
- sparse_exploratory_estimated_measurement_cost: `None`
- counts_available: `True`
- counts_source: `statevector_sampler_from_final_state`
- counts_sha256: `7a886b322aae84faa688d7e07aaf351e716ed1bf8aee0a339b5cea462cda4747`
- shots_per_group: `256`
- hamiltonian_variance: `4.440892098500626e-16`
- ground_state_overlap: `0.9999999999999998`
- dominant_configurations: `[{'bitstring': '0101', 'probability': 0.9875597343674857}, {'bitstring': '1010', 'probability': 0.012440265632514214}, {'bitstring': '0011', 'probability': 9.684118727256242e-31}, {'bitstring': '1101', 'probability': 6.432992020535064e-31}, {'bitstring': '0111', 'probability': 5.4671440153048155e-31}, {'bitstring': '1111', 'probability': 4.442915448714402e-31}, {'bitstring': '0001', 'probability': 3.153747026396602e-31}, {'bitstring': '1100', 'probability': 2.602710877514126e-31}]`
- z2_check: `{'status': 'disabled', 'z2_symmetry_count': 0, 'z2_tapering_values': None, 'validation': {}, 'notes': ['Z2 tapering disabled by mapping.symmetry_reduction.z2.', 'Z2 tapering skipped for QSCI++ because determinant sampling v1 assumes untapered spin-orbital bitstrings.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 4, 'raw_num_qubits': 4, 'qubit_term_count': 15, 'raw_qubit_term_count': 15, 'circuit_depth': None, 'two_qubit_gate_count': None, 'operation_counts': {}}`
- error_budget: `{'ansatz_error': {'available': False, 'absolute_error_hartree': 1.9984014443252818e-15, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
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
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/method_evidence.json`
- sidecar_sha256: `25e109ae8d7a02eb1dbb1e5e71516e624aae345e56ef472eba6bbddfccbf2c82`
- methods: `{'qsci_plus_result': {'available': True, 'trust_tier': 'exploratory'}, 'post_correlation': {'available': True, 'trust_tier': 'unsupported_for_claim'}, 'q_sc_eom': {'available': True, 'trust_tier': 'exploratory'}, 'ft_qpe_resource_estimate': {'available': True, 'trust_tier': 'exploratory'}, 'trust_qem': {'available': True, 'trust_tier': 'unsupported_for_claim'}, 'shadow_lr': {'available': True, 'trust_tier': 'exploratory'}}`
- promotion_gate_audit: `{'schema': 'qcchem.method_promotion_gate_audit.v1', 'primary_solver_kind': 'exact', 'primary_energy_policy': 'raw_solver_energy_remains_primary', 'sidecar_energy_replacement_allowed_methods': [], 'accuracy_claim_allowed_methods': [], 'hardware_claim_allowed_methods': [], 'planning_metric_methods': ['ft_qpe_resource_estimate', 'shadow_lr'], 'resource_model_only_methods': ['ft_qpe_resource_estimate'], 'unsupported_for_claim_methods': ['post_correlation', 'trust_qem'], 'method_records': {'ft_qpe_resource_estimate': {'method': 'ft_qpe_resource_estimate', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': True, 'resource_model_claim_allowed': True, 'claim_status': 'resource_model_only', 'evidence_role': 'fault_tolerant_resource_model', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['encoding_scale_assumptions_not_derived_from_integral_factorization', 'no_compiled_fault_tolerant_circuit', 'surface_code_distance_not_estimated', 'logical_error_budget_not_allocated', 'hardware_architecture_cycle_model_not_calibrated'], 'validated_resource_advantage_claim_allowed': False, 'promotion_readiness_status': 'blocked_missing_compiled_fault_tolerant_evidence', 'readiness_level': 'resource_model_only_not_compiled', 'resource_formula_scope': 'coarse_pauli_l1_phase_estimation_scaling', 'reference_encoding': 'double_factorization', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 2, 'logical_error_budget_available': False, 'required_promotion_evidence_count': 5, 'required_promotion_evidence': ['executable_integral_factorization_for_each_encoding', 'compiled_fault_tolerant_phase_estimation_circuit', 'surface_code_distance_and_physical_qubit_layout', 'logical_error_budget_allocation', 'hardware_architecture_specific_cycle_model'], 'promotion_blocker_count': 5}, 'post_correlation': {'method': 'post_correlation', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'unsupported_for_claim', 'evidence_role': 'correction_eligibility_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['cluster-amplitude contraction equations', 'double-counting correction model', 'double_counting_not_evaluated', 'executable QSCI-to-TCC amplitude backend', 'external orbital-space partition', 'external_correlation_energy_not_emitted', 'qcchem_qsci_correction_backend_missing'], 'correction_eligibility_status': 'tcc_amplitude_mapping_audit_only', 'eligible_coefficient_count': 4, 'amplitude_mapping_status': 'constructed_for_audit_only', 'mapped_single_count': 0, 'mapped_double_count': 1, 'backend_executable': False, 'correction_energy_emitted': False, 'energy_replaces_primary': False, 'required_input_missing_count': 4}, 'q_sc_eom': {'method': 'q_sc_eom', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'conditioning_reference_audit', 'evidence_role': 'excited_state_conditioning_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['exact_root_audit_not_general_eom_solver', 'excited_state_benchmark_gate_required'], 'conditioning_status': 'well_conditioned_reference_roots', 'overlap_condition_number': 1.0, 'transition_property_status': 'transition_properties_missing', 'validated_transition_property_count': 0, 'transition_property_names': []}, 'qsci_plus_result': {'method': 'qsci_plus_result', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'selected_ci_subspace_audit', 'evidence_role': 'selected_ci_variational_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['selected_subspace_benchmark_gate_required', 'primary_energy_replacement_disallowed']}, 'shadow_lr': {'method': 'shadow_lr', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': True, 'resource_model_claim_allowed': False, 'claim_status': 'planning_metric_only', 'evidence_role': 'measurement_planning_cost_model', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['not_hardware_calibrated', 'accuracy_claim_not_supported_by_measurement_plan_alone'], 'estimated_cost_claim_status': 'planning_metric_only', 'hardware_cost_claim_allowed': False, 'allocated_shots': 256, 'grouped_precision_baseline_shots': 1280.0, 'basis_l1_coverage_fraction': 1.0, 'unselected_basis_count': 0, 'max_allocated_shot_fraction': 0.921875, 'allocation_entropy': 0.23764207327154327, 'grouped_precision_variance_proxy': 0.005716599620051651, 'variance_inflation_vs_grouped_precision_proxy': 5.0, 'plan_digest': '4998f6d69b2762abdfa0438834e37c2c489f2e003caf1ebaf9530202e4049b94'}, 'trust_qem': {'method': 'trust_qem', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'unsupported_for_claim', 'evidence_role': 'mitigation_provenance_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['no_mitigation_component_allowed_for_energy_claim'], 'mitigation_claim_allowed_methods': [], 'mitigation_claim_disallowed_methods': ['symmetry_check', 'readout_mitigation'], 'pec_status': 'not_requested', 'pec_executable_calibration_model': False, 'pec_calibrated_operation_count': 0, 'pec_quasi_probability_entry_count': 0, 'pec_max_operation_l1_overhead': None, 'pec_sampling_overhead': 0.0}}, 'overall_claim_status': 'promotion_required', 'promotion_required_for_validated_claims': True, 'notes': ['Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.', 'Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.']}`
- trust_tier: `exploratory`
- notes: `['Method evidence is reported alongside the primary solver result.', 'Exploratory method sections do not promote chemical-accuracy claims by themselves.']`

## QSCI++

- sampler: `local_energy_proxy`
- raw_bitstrings: `{'1010': 3, '1011': 5, '0101': 17, '0001': 13, '1110': 9, '0011': 8, '1100': 10, '0110': 11, '0111': 10, '0100': 9, '1001': 12, '1101': 12, '0010': 2, '1111': 2, '1000': 4, '0000': 1}`
- repaired_determinants: `[{'index': 5, 'bitstring': '0101', 'occupied_spin_orbitals': [0, 2], 'probability': 0.15103890665495304, 'selection_origin': 'sampled', 'selection_origins': ['hartree_fock_reference', 'sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}, {'index': 9, 'bitstring': '1001', 'occupied_spin_orbitals': [0, 3], 'probability': 0.06970156859192993, 'selection_origin': 'sampled', 'selection_origins': ['sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}, {'index': 6, 'bitstring': '0110', 'occupied_spin_orbitals': [1, 2], 'probability': 0.0697015685919299, 'selection_origin': 'sampled', 'selection_origins': ['sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}, {'index': 10, 'bitstring': '1010', 'occupied_spin_orbitals': [1, 3], 'probability': 0.030746856587182885, 'selection_origin': 'sampled', 'selection_origins': ['sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}]`
- selected_subspace_size: `4`
- ci_energy: `-1.857275030202` Hartree
- variance_estimate: `0.0`
- excited_state_energies: `[]`
- selection_bias_audit: `{'selected_probability_mass': 0.32118890042599574, 'raw_unique_determinants': 16, 'pre_repair_ranked_count': 16, 'sector_rejected_count': 12, 'hamming_expansion_radius': 1, 'hamming_seed_count': 4, 'initial_selected_subspace_size': 8, 'max_selected_subspace_size': 8, 'residual_expansion': {'enabled': False, 'scorer': 'external_residual_coupling', 'target_residual_norm': 1e-06, 'max_iterations': 0, 'batch_size': 8, 'max_additional_determinants': 0, 'iteration_count': 0, 'added_determinant_count': 0, 'history': []}, 'selected_origin_counts': {'sampled': 4}, 'selected_multi_origin_counts': {'hartree_fock_reference': 1, 'sampled': 4, 'sector_repaired': 4}, 'hartree_fock_determinant': 5, 'hartree_fock_selected': True, 'ci_coefficients_digest': '17d2350cc0a4b7cb1a5215e37255e93461297d956ff0041a218409094d2d76aa', 'classical_diagonalizer': 'dense_exact', 'leading_coefficients': [{'determinant': 5, 'coefficient_real': -0.993760400885186, 'coefficient_imag': 0.0}, {'determinant': 9, 'coefficient_real': 0.0, 'coefficient_imag': 0.0}, {'determinant': 6, 'coefficient_real': 0.0, 'coefficient_imag': 0.0}, {'determinant': 10, 'coefficient_real': 0.1115359387485228, 'coefficient_imag': 0.0}]}`
- subspace_audit: `{'variance_method': 'embedded_ritz_vector_sparse_hamiltonian', 'ground_state_variance': 0.0, 'ground_state_residual_norm': 6.684427777288335e-16, 'ground_state_external_coupling_residual_norm': 0.0, 'energy_error_to_exact_hartree': -1.1102230246251565e-15, 'variational_upper_bound_margin_hartree': -1.1102230246251565e-15, 'variational_upper_bound_passed': True, 'selected_determinant_count': 4, 'sector_determinant_count': 4, 'selected_sector_coverage_fraction': 1.0, 'selected_bitstrings': ['0101', '1001', '0110', '1010'], 'root_residuals': [{'root_index': 0, 'energy': -1.8572750302023802, 'projected_subspace_energy': -1.8572750302023795, 'hamiltonian_variance': 0.0, 'residual_norm': 6.684427777288335e-16, 'projected_residual_norm': 6.684427777288335e-16, 'external_coupling_residual_norm': 0.0}, {'root_index': 1, 'energy': -1.2445845498133274, 'projected_subspace_energy': -1.244584549813327, 'hamiltonian_variance': 0.0, 'residual_norm': 4.577566798522237e-16, 'projected_residual_norm': 4.577566798522237e-16, 'external_coupling_residual_norm': 0.0}, {'root_index': 2, 'energy': -0.8827221502448642, 'projected_subspace_energy': -0.8827221502448641, 'hamiltonian_variance': 0.0, 'residual_norm': 1.1102230246251565e-16, 'projected_residual_norm': 1.1102230246251565e-16, 'external_coupling_residual_norm': 0.0}, {'root_index': 3, 'energy': -0.2249112528308701, 'projected_subspace_energy': -0.22491125283087, 'hamiltonian_variance': 0.0, 'residual_norm': 5.551115123125783e-17, 'projected_residual_norm': 5.551115123125783e-17, 'external_coupling_residual_norm': 0.0}]}`
- variational_upper_bound: `True`
- notes: `['QSCI++ v1 selects a determinant subspace with local sampling proxies and diagonalizes the physical Hamiltonian.', 'Variance and residual diagnostics are computed from the embedded Ritz vector in the physical qubit Hamiltonian.', 'The selected CI energy is reported as method evidence and does not replace the primary run energy.']`

## QSCI Post-Correlation

- method: `qsci_tcc`
- source_wavefunction: `qsci_plus`
- active_ci_coefficients_digest: `17d2350cc0a4b7cb1a5215e37255e93461297d956ff0041a218409094d2d76aa`
- correction_eligibility_audit: `{'schema': 'qcchem.qsci_post_correlation_eligibility.v1', 'status': 'tcc_amplitude_mapping_audit_only', 'method': 'qsci_tcc', 'source_wavefunction': 'qsci_plus', 'selected_subspace_size': 4, 'eligible_coefficient_count': 4, 'ci_coefficients_digest': '17d2350cc0a4b7cb1a5215e37255e93461297d956ff0041a218409094d2d76aa', 'ci_energy_hartree': -1.8572750302023795, 'variance_estimate': 0.0, 'amplitude_mapping_status': 'constructed_for_audit_only', 'backend_executable': False, 'correction_energy_emitted': False, 'total_corrected_energy_emitted': False, 'energy_replaces_primary': False, 'required_inputs_missing': ['external orbital-space partition', 'executable QSCI-to-TCC amplitude backend', 'cluster-amplitude contraction equations', 'double-counting correction model'], 'required_input_missing_count': 4, 'promotion_blockers': ['external_correlation_energy_not_emitted', 'double_counting_not_evaluated', 'qcchem_qsci_correction_backend_missing', 'external orbital-space partition', 'executable QSCI-to-TCC amplitude backend', 'cluster-amplitude contraction equations', 'double-counting correction model']}`
- amplitude_mapping_audit: `{'schema': 'qcchem.qsci_tcc_amplitude_mapping_audit.v1', 'status': 'constructed_for_audit_only', 'reference_policy': 'largest_abs_selected_ci_coefficient', 'reference_determinant': 5, 'reference_coefficient_abs': 0.993760400885186, 'coefficient_count': 4, 'coefficient_norm': 0.9999999999999999, 'mapped_single_count': 0, 'mapped_double_count': 1, 'unsupported_excitation_count': 0, 'negligible_coefficient_count': 2, 'max_mapped_amplitude_abs': 0.1122362479418307, 'singles': [], 'doubles': [{'determinant': 10, 'reference_determinant': 5, 'hamming_distance': 4, 'excitation_rank': 2, 'coefficient_abs': 0.1115359387485228, 'amplitude_real': -0.1122362479418307, 'amplitude_imag': -0.0, 'amplitude_abs': 0.1122362479418307}], 'unsupported_excitations': [], 'negligible_coefficients': [{'determinant': 9, 'reference_determinant': 5, 'hamming_distance': 2, 'excitation_rank': 1, 'coefficient_abs': 0.0, 'amplitude_real': -0.0, 'amplitude_imag': -0.0, 'amplitude_abs': 0.0}, {'determinant': 6, 'reference_determinant': 5, 'hamming_distance': 2, 'excitation_rank': 1, 'coefficient_abs': 0.0, 'amplitude_real': -0.0, 'amplitude_imag': -0.0, 'amplitude_abs': 0.0}], 'energy_correction_backend_executable': False, 'energy_replaces_primary': False, 'notes': ['Selected-CI coefficients are mapped to relative single/double amplitudes for audit only.', 'No QSCI-derived TCC energy is emitted without an executable external-correlation backend.']}`
- tailored_amplitudes: `{'status': 'constructed_for_audit_only', 'source': 'selected_ci_coefficients_digest', 'eligible_coefficient_count': 4, 'selected_subspace_size': 4, 'mapped_single_count': 0, 'mapped_double_count': 1, 'required_inputs_missing': ['external orbital-space partition', 'executable QSCI-to-TCC amplitude backend', 'cluster-amplitude contraction equations', 'double-counting correction model']}`
- external_correlation_energy: `None`
- total_corrected_energy: `None`
- double_counting_audit: `{'status': 'not_evaluated', 'active_space_energy_available': True, 'active_space_ci_energy_hartree': -1.8572750302023795, 'dynamic_correlation_energy_emitted': False, 'energy_replaces_primary': False, 'backend_executable': False, 'required_input_missing_count': 4, 'reason': 'No executable QSCI-derived TCC/NEVPT2 correction model is available in v1.'}`
- classical_solver: `None`
- trust_gate: `unsupported_for_claim`
- notes: `['QSCI post-correlation v1 records coefficient provenance and correction eligibility only.', 'No external-correlation or corrected-total energy is emitted without an executable QSCI-derived TCC/NEVPT2 backend.', 'Use the validated classical NEVPT2 perturbative-correction task for PySCF-backed NEVPT2 corrections.']`

## Trust-QEM

- requested_methods: `['symmetry_check', 'readout_mitigation']`
- applied_methods: `['symmetry_check', 'readout_mitigation']`
- claim_allowed_methods: `[]`
- claim_disallowed_methods: `['symmetry_check', 'readout_mitigation']`
- claim_status: `unsupported_for_claim`
- trust_gate: `unsupported_for_claim`
- energy_replaces_primary: `False`
- symmetry_check: `{'requested': True, 'effective_requested': True, 'performed': True, 'status': 'passed', 'strategy': 'postselect', 'requested_checks': {'particle_number': True, 'spin_parity': False, 'z2_sector': False}, 'postselection_rate': 1.0, 'allowed_for_claim': False, 'claim_status': 'diagnostic_only', 'energy_replaces_primary': False}`
- readout_mitigation: `{'requested': True, 'performed': True, 'status': 'passed', 'method': 'local_assignment', 'calibration_shots': 64, 'calibration_digest': 'local-readout-local_assignment-64', 'allowed_for_claim': False, 'claim_status': 'calibration_record_only', 'energy_replaces_primary': False}`
- zne: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'folding': 'global', 'scale_factors': [1.0, 1.5, 2.0, 3.0], 'extrapolator': 'linear', 'zne_curve': [], 'variance_inflation': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- pec: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'calibration_model': None, 'calibration_model_audit': {'provided': False, 'exists': False, 'executable': False, 'status': 'missing_calibration_model', 'digest': None, 'schema': None, 'calibrated_operation_count': 0, 'quasi_probability_entry_count': 0, 'max_operation_l1_overhead': None}, 'executable_calibration_model': False, 'sampling_overhead': 0.0, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'claim_scope': None, 'energy_replaces_primary': False}`

## FT-QPE Planner

- encodings_compared: `['double_factorization', 'tensor_hypercontraction']`
- lambda_norms: `{'double_factorization': 2.705041129754983, 'tensor_hypercontraction': 1.7582767343407388}`
- toffoli_counts: `{'double_factorization': 10820.16451901993, 'tensor_hypercontraction': 7033.106937362955}`
- logical_qubits: `{'double_factorization': 23, 'tensor_hypercontraction': 23}`
- physical_qubits: `{'double_factorization': 23000, 'tensor_hypercontraction': 23000}`
- runtime_estimates: `{'double_factorization': 0.01082016451901993, 'tensor_hypercontraction': 0.007033106937362955}`
- dominant_cost_terms: `{'pauli_term_count': 15, 'qubit_count': 4, 'precision_hartree': 0.001, 'coefficient_l1_norm': 2.705041129754983, 'phase_estimation_steps': {'double_factorization': 2706, 'tensor_hypercontraction': 1759}, 'surface_code_overhead_factor': 1000}`
- recommended_encoding: `tensor_hypercontraction`
- resource_formula_audit: `{'schema': 'qcchem.ft_qpe_resource_formula_audit.v1', 'scope': 'coarse_pauli_l1_phase_estimation_scaling', 'input_terms': {'coefficient_l1_norm': 2.705041129754983, 'num_qubits': 4, 'pauli_term_count': 15, 'precision_hartree': 0.001, 'cycle_time_ns': 1000.0, 'physical_error_rate': 0.001, 'surface_code_overhead_factor': 1000}, 'formulae': {'lambda_norm': 'coefficient_l1_norm * encoding_scale_assumption', 'phase_estimation_steps': 'ceil(lambda_norm / precision_hartree)', 'toffoli_count': 'lambda_norm / precision_hartree * max(num_qubits, 1)', 'logical_qubits': 'num_qubits + 4 + pauli_term_count', 'physical_qubits': 'logical_qubits * surface_code_overhead_factor', 'runtime_seconds': 'toffoli_count * cycle_time_ns * 1e-9', 'surface_code_overhead_factor': 'round(1 / physical_error_rate)'}, 'encoding_scale_assumptions': {'double_factorization': 1.0, 'symmetry_compressed_double_factorization': 0.75, 'tensor_hypercontraction': 0.65, 'first_quantization_active_basis': 0.85}, 'encoding_formula_components': {'double_factorization': {'encoding_scale_assumption': 1.0, 'lambda_norm': 2.705041129754983, 'phase_estimation_steps': 2706, 'toffoli_count': 10820.16451901993, 'logical_qubits': 23, 'physical_qubits': 23000, 'runtime_seconds': 0.01082016451901993}, 'tensor_hypercontraction': {'encoding_scale_assumption': 0.65, 'lambda_norm': 1.7582767343407388, 'phase_estimation_steps': 1759, 'toffoli_count': 7033.106937362955, 'logical_qubits': 23, 'physical_qubits': 23000, 'runtime_seconds': 0.007033106937362955}}, 'reference_encoding': 'double_factorization', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 2}`
- resource_model_audit: `{'model_scope': 'coarse_pauli_l1_phase_estimation_scaling', 'resource_claim_status': 'resource_model_only', 'promotion_readiness_status': 'blocked_missing_compiled_fault_tolerant_evidence', 'readiness_level': 'resource_model_only_not_compiled', 'compiled_fault_tolerant_circuit_available': False, 'surface_code_distance_available': False, 'logical_error_budget_available': False, 'validated_resource_advantage_claim_allowed': False, 'reference_encoding': 'double_factorization', 'recommended_encoding': 'tensor_hypercontraction', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 2, 'best_to_reference_toffoli_ratio': 0.65, 'toffoli_reduction_vs_reference': 0.35, 'lambda_reduction_vs_reference': 0.35, 'phase_estimation_steps': {'double_factorization': 2706, 'tensor_hypercontraction': 1759}, 'encoding_scale_assumptions': {'double_factorization': 1.0, 'symmetry_compressed_double_factorization': 0.75, 'tensor_hypercontraction': 0.65, 'first_quantization_active_basis': 0.85}, 'surface_code_overhead_model': 'logical_qubits * round(1 / physical_error_rate)', 'surface_code_overhead_factor': 1000, 'cycle_time_ns': 1000.0, 'physical_error_rate': 0.001, 'required_promotion_evidence': ['executable_integral_factorization_for_each_encoding', 'compiled_fault_tolerant_phase_estimation_circuit', 'surface_code_distance_and_physical_qubit_layout', 'logical_error_budget_allocation', 'hardware_architecture_specific_cycle_model'], 'required_promotion_evidence_count': 5, 'promotion_blockers': ['encoding_scale_assumptions_not_derived_from_integral_factorization', 'no_compiled_fault_tolerant_circuit', 'surface_code_distance_not_estimated', 'logical_error_budget_not_allocated', 'hardware_architecture_cycle_model_not_calibrated'], 'promotion_blocker_count': 5}`
- promotion_readiness_audit: `{'schema': 'qcchem.ft_qpe_promotion_readiness.v1', 'status': 'blocked_missing_compiled_fault_tolerant_evidence', 'readiness_level': 'resource_model_only_not_compiled', 'resource_model_claim_allowed': True, 'validated_resource_advantage_claim_allowed': False, 'compiled_fault_tolerant_circuit_available': False, 'surface_code_distance_available': False, 'logical_error_budget_available': False, 'executable_factorization_available': False, 'reference_encoding': 'double_factorization', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 2, 'best_to_reference_toffoli_ratio': 0.65, 'toffoli_reduction_vs_reference': 0.35, 'lambda_reduction_vs_reference': 0.35, 'promotion_blockers': ['encoding_scale_assumptions_not_derived_from_integral_factorization', 'no_compiled_fault_tolerant_circuit', 'surface_code_distance_not_estimated', 'logical_error_budget_not_allocated', 'hardware_architecture_cycle_model_not_calibrated'], 'promotion_blocker_count': 5, 'required_promotion_evidence': ['executable_integral_factorization_for_each_encoding', 'compiled_fault_tolerant_phase_estimation_circuit', 'surface_code_distance_and_physical_qubit_layout', 'logical_error_budget_allocation', 'hardware_architecture_specific_cycle_model'], 'required_promotion_evidence_count': 5}`
- notes: `['FT-QPE planner is a coarse resource estimator, not a compiled fault-tolerant circuit.', 'Encoding reductions are model assumptions until backed by executable factorization and logical-resource gates.']`

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
- Qubit count: `4`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `15`
- Raw qubit count: `4`
- Raw qubit Hamiltonian terms: `15`
- Symmetry tapered qubits: `0`
- Z2 symmetry count: `0`
- Z2 tapering values: `None`
- Symmetry reduction status: `disabled`
- Symmetry reduction validation: `{}`
- Symmetry reduction notes: `['Z2 tapering disabled by mapping.symmetry_reduction.z2.', 'Z2 tapering skipped for QSCI++ because determinant sampling v1 assumes untapered spin-orbital bitstrings.']`

## Backend

- Backend kind: `shot_estimator`
- Precision: `None`
- Shots: `256`
- Seed: `47`
- Repetitions: `5`
- Abelian grouping: `True`
- Noise enabled: `False`
- Runtime enabled: `False`

## Backend Capability

- backend_kind: `shot_estimator`
- statevector: `False`
- shot_based: `True`
- exact_baseline: `True`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- mitigation_ready: `True`
- noise_model_ready: `True`
- supports_grouping: `True`
- supports_repetitions: `True`
- supports_confidence_metrics: `True`

## Execution Policy

- name: `benchmark`
- default_shots: `4096`
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
- absolute_error_kcal_mol: `1.393350932410442e-12`
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
- term_count: `15`
- group_count: `5`
- estimated_shot_cost: `256.0`
- runtime_precision_target: `0.0625`
- uncompressed_group_count: `5`
- uncompressed_estimated_shot_cost: `1280.0`
- cost_reduction_ratio: `0.2`
- planner: `shadow_lr`
- shadow_bases: `[{'basis_id': 0, 'basis': 'ZZZZ', 'weight': 2.5241099299707512, 'allocation_fraction': 0.933113327633351, 'allocated_shot_fraction': 0.921875}, {'basis_id': 1, 'basis': 'YYYY', 'weight': 0.04523279994605786, 'allocation_fraction': 0.016721668091662235, 'allocated_shot_fraction': 0.01953125}, {'basis_id': 2, 'basis': 'XXYY', 'weight': 0.04523279994605786, 'allocation_fraction': 0.016721668091662235, 'allocated_shot_fraction': 0.01953125}, {'basis_id': 3, 'basis': 'YYXX', 'weight': 0.04523279994605786, 'allocation_fraction': 0.016721668091662235, 'allocated_shot_fraction': 0.01953125}, {'basis_id': 4, 'basis': 'XXXX', 'weight': 0.04523279994605786, 'allocation_fraction': 0.016721668091662235, 'allocated_shot_fraction': 0.01953125}]`
- shot_allocation: `[{'basis_id': 0, 'shots': 236, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 1, 'shots': 5, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 2, 'shots': 5, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 3, 'shots': 5, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 4, 'shots': 5, 'allocation_policy': 'coefficient_l1_covariance_proxy'}]`
- predicted_variance: `0.028582998100258255`
- measurement_cost_model: `{'planner': 'shadow_lr', 'term_l1_norm': 2.705041129754983, 'selected_basis_l1_norm': 2.705041129754983, 'basis_l1_coverage_fraction': 1.0, 'basis_count': 5, 'selected_basis_count': 5, 'unselected_basis_count': 0, 'budgeted_shots': 256, 'allocated_shots': 256, 'max_allocated_shot_fraction': 0.921875, 'allocation_entropy': 0.23764207327154327, 'grouped_precision_baseline_shots': 1280.0, 'predicted_variance': 0.028582998100258255, 'grouped_precision_variance_proxy': 0.005716599620051651, 'variance_inflation_vs_grouped_precision_proxy': 5.0, 'plan_digest': '4998f6d69b2762abdfa0438834e37c2c489f2e003caf1ebaf9530202e4049b94', 'max_circuits': 8, 'strategies': [], 'objective': 'minimize_energy_variance'}`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.0625.', 'Measurement planning reflects the uncompressed execution path.', 'Shadow-LR planner generated locally biased shadow bases and shot allocation.', 'Shadow-LR estimated shot cost uses allocated shadow shots; grouped precision cost is retained in measurement_cost_model.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.00038745799975004047`
- measured_shot_usage: `None`
- precision_target: `0.0625`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `256.0`
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

## Perturbative Correction

- enabled: `True`
- method: `qsci_tcc`
- plugin: `pyscf`
- active_space_energy: `0.000000000000` Hartree
- reduced_active_space_energy: `-1.137306035753` Hartree
- compressed_active_space_energy: `None`
- perturbative_correction: `0.000000000000` Hartree
- corrected_total_energy: `0.000000000000` Hartree
- verification_status: `exploratory`
- provenance: `{'source': 'placeholder', 'reason': 'active_space_required'}`
- notes: `['NEVPT2 correction requires an active-space specification.']`

## Excited-state Result

- method: `q_sc_eom`
- verification_status: `exploratory`
- notes: `['q-sc-EOM v1 uses exact-spectrum roots as a conditioning/reference audit.', 'Transition properties should be requested through tasks.properties; this section records root and overlap diagnostics.']`

- state_index=`1` excitation_energy=`0.600935957199` Hartree verification_status=`exploratory` solver_metadata=`{'requested_method': 'q_sc_eom', 'method': 'q_sc_eom', 'overlap_condition_number': 1.0, 'regularization_actions': [], 'root_residual_audit': {'root_index': 1, 'residual_norm': 5.782754506464139e-16, 'previous_root_gap_hartree': 0.6009359571991284, 'next_root_gap_hartree': None, 'min_neighbor_gap_hartree': 0.6009359571991284, 'degenerate_neighbor_indices': [], 'root_tracking_status': 'energy_order_stable'}, 'root_tracking': {'reference_state_index': 0, 'requested_state_index': 1, 'ordering': 'exact_spectrum_energy_order', 'status': 'energy_order_stable'}, 'transition_properties': {'available': False, 'reason': 'property operators are reported through tasks.properties; q_sc_eom v1 stores conditioning metadata here.'}}`

## Mitigation

- symmetry_check: `{'requested': True, 'effective_requested': True, 'performed': True, 'status': 'passed', 'strategy': 'postselect', 'requested_checks': {'particle_number': True, 'spin_parity': False, 'z2_sector': False}, 'postselection_rate': 1.0, 'allowed_for_claim': False, 'claim_status': 'diagnostic_only', 'energy_replaces_primary': False}`
- readout_mitigation: `{'requested': True, 'performed': True, 'status': 'passed', 'method': 'local_assignment', 'calibration_shots': 64, 'calibration_digest': 'local-readout-local_assignment-64', 'allowed_for_claim': False, 'claim_status': 'calibration_record_only', 'energy_replaces_primary': False}`
- zne: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'folding': 'global', 'scale_factors': [1.0, 1.5, 2.0, 3.0], 'extrapolator': 'linear', 'zne_curve': [], 'variance_inflation': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- pec: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'calibration_model': None, 'calibration_model_audit': {'provided': False, 'exists': False, 'executable': False, 'status': 'missing_calibration_model', 'digest': None, 'schema': None, 'calibrated_operation_count': 0, 'quasi_probability_entry_count': 0, 'max_operation_l1_overhead': None}, 'executable_calibration_model': False, 'sampling_overhead': 0.0, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'claim_scope': None, 'energy_replaces_primary': False}`
- requested_methods: `['symmetry_check', 'readout_mitigation']`
- applied_methods: `['symmetry_check', 'readout_mitigation']`
- claim_allowed_methods: `[]`
- claim_status: `unsupported_for_claim`
- energy_replaces_primary: `False`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`f17f21bd4c0255c706d3cf8377ac9a5f1dcfa6c8cd1dc5a67bdb5d0cf7596534`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-07-08T04:20:43.675606+00:00`
- Wall time (s): `0.04419429100016714`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `b2284c48d57f32f1bf970108686b3644518dd0e6c97cc4208e923e830ad02be4`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `47`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_method_evidence_smoke.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/quantum_evidence.json`
- qcschema.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/qcschema.json`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_method_evidence_smoke.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=f17f21bd4c02
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Z2 tapering skipped for QSCI++ because determinant sampling v1 assumes untapered spin-orbital bitstrings.
- Prepared measurement plan: groups=5, cost=256
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 2 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/exact_result.json
- Computed empirical calibration: wall_time=0.000s, measured_cost=None
- Computed perturbative correction: qsci_tcc
- Computed QSCI++ selected-subspace workflow: determinants=4
- Wrote integrated method evidence sidecar
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_method_evidence_smoke/report.md
- Run completed
