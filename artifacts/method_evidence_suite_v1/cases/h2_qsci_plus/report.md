# QCchem Report: H2-qsci-plus

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-qsci-plus`
- basis: `sto3g`
- method: `statevector`
- mapping_kind: `jordan_wigner`
- num_qubits: `4`
- verification_status: `exploratory`
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

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_qsci_plus', 'molecule_name': 'H2-qsci-plus', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `H2-qsci-plus stays within chemical accuracy against exact_baseline for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 2.6645352591003757e-15, 'units': 'Hartree', 'threshold': 1e-08, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-qsci-plus stays within chemical accuracy against exact_baseline for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `qsci_nevpt2` / delta=`0.000000000000` Hartree
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 2.6645352591003757e-15, 'relative_error': 1.4346476508705522e-15, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.039725250000628876, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 5, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': [], 'scientific_risk_notes': [], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:43.414367+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus`

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
- relative_error: `1.4346476508705522e-15`
- statistical_error: `None`
- absolute_error_threshold: `1e-08`
- relative_error_threshold: `1e-08`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/quantum_evidence.json`
- sidecar_sha256: `54967f7fe6e184a4eb9ccdf22dd7e19bc6b20065826bb32be3bb6f77c4e2fb69`
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
- counts_sha256: `8d6d7b0fd61be6409784b57bc86d19edcc63119d791be2e4121a2c6f9a306c81`
- shots_per_group: `4096`
- hamiltonian_variance: `0.0`
- ground_state_overlap: `1.0000000000000004`
- dominant_configurations: `[{'bitstring': '0101', 'probability': 0.9875597343674861}, {'bitstring': '1010', 'probability': 0.01244026563251422}, {'bitstring': '0000', 'probability': 1.0360032077034313e-31}, {'bitstring': '1001', 'probability': 2.0629107288718356e-32}, {'bitstring': '0111', 'probability': 1.9339785935846858e-32}, {'bitstring': '0100', 'probability': 1.894718739343036e-32}, {'bitstring': '1000', 'probability': 1.6844896075302494e-32}, {'bitstring': '1101', 'probability': 7.807454740008774e-33}]`
- z2_check: `{'status': 'disabled', 'z2_symmetry_count': 0, 'z2_tapering_values': None, 'validation': {}, 'notes': ['Z2 tapering disabled by mapping.symmetry_reduction.z2.', 'Z2 tapering skipped for QSCI++ because determinant sampling v1 assumes untapered spin-orbital bitstrings.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 4, 'raw_num_qubits': 4, 'qubit_term_count': 15, 'raw_qubit_term_count': 15, 'circuit_depth': None, 'two_qubit_gate_count': None, 'operation_counts': {}}`
- error_budget: `{'ansatz_error': {'available': False, 'absolute_error_hartree': 2.6645352591003757e-15, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
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
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/method_evidence.json`
- sidecar_sha256: `04e3c4b7bd759402496bf85ca7b0fc8441c82e3b8e0eba44889589b70d781db0`
- methods: `{'qsci_plus_result': {'available': True, 'trust_tier': 'exploratory'}, 'post_correlation': {'available': True, 'trust_tier': 'unsupported_for_claim'}}`
- promotion_gate_audit: `{'schema': 'qcchem.method_promotion_gate_audit.v1', 'primary_solver_kind': 'exact', 'primary_energy_policy': 'raw_solver_energy_remains_primary', 'sidecar_energy_replacement_allowed_methods': [], 'accuracy_claim_allowed_methods': [], 'hardware_claim_allowed_methods': [], 'planning_metric_methods': [], 'resource_model_only_methods': [], 'unsupported_for_claim_methods': ['post_correlation'], 'method_records': {'post_correlation': {'method': 'post_correlation', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'unsupported_for_claim', 'evidence_role': 'correction_eligibility_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['active-space one- and two-particle density matrices', 'contracted perturber-space intermediates', 'double-counting correction model', 'double_counting_not_evaluated', 'executable QSCI-to-NEVPT2 backend', 'external_correlation_energy_not_emitted', 'qcchem_qsci_correction_backend_missing'], 'correction_eligibility_status': 'coefficient_provenance_only', 'eligible_coefficient_count': 4, 'amplitude_mapping_status': 'not_applicable_to_nevpt2', 'mapped_single_count': 0, 'mapped_double_count': 0, 'backend_executable': False, 'correction_energy_emitted': False, 'energy_replaces_primary': False, 'required_input_missing_count': 4}, 'qsci_plus_result': {'method': 'qsci_plus_result', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'selected_ci_subspace_audit', 'evidence_role': 'selected_ci_variational_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['selected_subspace_benchmark_gate_required', 'primary_energy_replacement_disallowed']}}, 'overall_claim_status': 'promotion_required', 'promotion_required_for_validated_claims': True, 'notes': ['Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.', 'Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.']}`
- trust_tier: `exploratory`
- notes: `['Method evidence is reported alongside the primary solver result.', 'Exploratory method sections do not promote chemical-accuracy claims by themselves.']`

## QSCI++

- sampler: `local_energy_proxy`
- raw_bitstrings: `{'0001': 16, '0110': 25, '0100': 27, '0010': 9, '0000': 6, '0101': 36, '1100': 17, '1000': 10, '1111': 7, '0011': 25, '1110': 7, '1101': 17, '1011': 4, '0111': 24, '1010': 7, '1001': 19}`
- repaired_determinants: `[{'index': 5, 'bitstring': '0101', 'occupied_spin_orbitals': [0, 2], 'probability': 0.15103890665495304, 'selection_origin': 'sampled', 'selection_origins': ['hartree_fock_reference', 'sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}, {'index': 6, 'bitstring': '0110', 'occupied_spin_orbitals': [1, 2], 'probability': 0.0697015685919299, 'selection_origin': 'sampled', 'selection_origins': ['sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}, {'index': 9, 'bitstring': '1001', 'occupied_spin_orbitals': [0, 3], 'probability': 0.06970156859192993, 'selection_origin': 'sampled', 'selection_origins': ['sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}, {'index': 10, 'bitstring': '1010', 'occupied_spin_orbitals': [1, 3], 'probability': 0.030746856587182885, 'selection_origin': 'sampled', 'selection_origins': ['sampled', 'sector_repaired'], 'alpha_electrons': 1, 'beta_electrons': 1, 'total_electrons': 2, 'spin_projection': 0.0}]`
- selected_subspace_size: `4`
- ci_energy: `-1.857275030202` Hartree
- variance_estimate: `0.0`
- excited_state_energies: `[-1.244584549813327]`
- selection_bias_audit: `{'selected_probability_mass': 0.3211889004259958, 'raw_unique_determinants': 16, 'pre_repair_ranked_count': 16, 'sector_rejected_count': 12, 'hamming_expansion_radius': 1, 'hamming_seed_count': 4, 'initial_selected_subspace_size': 8, 'max_selected_subspace_size': 8, 'residual_expansion': {'enabled': False, 'scorer': 'external_residual_coupling', 'target_residual_norm': 1e-06, 'max_iterations': 0, 'batch_size': 8, 'max_additional_determinants': 0, 'iteration_count': 0, 'added_determinant_count': 0, 'history': []}, 'selected_origin_counts': {'sampled': 4}, 'selected_multi_origin_counts': {'hartree_fock_reference': 1, 'sampled': 4, 'sector_repaired': 4}, 'hartree_fock_determinant': 5, 'hartree_fock_selected': True, 'ci_coefficients_digest': '2f7f51cff381a3dd15564df58ec01d4700a6aa77da2903898691182d8771caa4', 'classical_diagonalizer': 'dense_exact', 'leading_coefficients': [{'determinant': 5, 'coefficient_real': -0.993760400885186, 'coefficient_imag': 0.0}, {'determinant': 6, 'coefficient_real': 0.0, 'coefficient_imag': 0.0}, {'determinant': 9, 'coefficient_real': 0.0, 'coefficient_imag': 0.0}, {'determinant': 10, 'coefficient_real': 0.1115359387485228, 'coefficient_imag': 0.0}]}`
- subspace_audit: `{'variance_method': 'embedded_ritz_vector_sparse_hamiltonian', 'ground_state_variance': 0.0, 'ground_state_residual_norm': 6.684427777288335e-16, 'ground_state_external_coupling_residual_norm': 0.0, 'energy_error_to_exact_hartree': -1.9984014443252818e-15, 'variational_upper_bound_margin_hartree': -1.9984014443252818e-15, 'variational_upper_bound_passed': True, 'selected_determinant_count': 4, 'sector_determinant_count': 4, 'selected_sector_coverage_fraction': 1.0, 'selected_bitstrings': ['0101', '0110', '1001', '1010'], 'root_residuals': [{'root_index': 0, 'energy': -1.8572750302023802, 'projected_subspace_energy': -1.8572750302023795, 'hamiltonian_variance': 0.0, 'residual_norm': 6.684427777288335e-16, 'projected_residual_norm': 6.684427777288335e-16, 'external_coupling_residual_norm': 0.0}, {'root_index': 1, 'energy': -1.2445845498133274, 'projected_subspace_energy': -1.244584549813327, 'hamiltonian_variance': 0.0, 'residual_norm': 4.577566798522237e-16, 'projected_residual_norm': 4.577566798522237e-16, 'external_coupling_residual_norm': 0.0}, {'root_index': 2, 'energy': -0.8827221502448642, 'projected_subspace_energy': -0.8827221502448641, 'hamiltonian_variance': 0.0, 'residual_norm': 1.1102230246251565e-16, 'projected_residual_norm': 1.1102230246251565e-16, 'external_coupling_residual_norm': 0.0}, {'root_index': 3, 'energy': -0.2249112528308701, 'projected_subspace_energy': -0.22491125283087, 'hamiltonian_variance': 0.0, 'residual_norm': 5.551115123125783e-17, 'projected_residual_norm': 5.551115123125783e-17, 'external_coupling_residual_norm': 0.0}]}`
- variational_upper_bound: `True`
- notes: `['QSCI++ v1 selects a determinant subspace with local sampling proxies and diagonalizes the physical Hamiltonian.', 'Variance and residual diagnostics are computed from the embedded Ritz vector in the physical qubit Hamiltonian.', 'The selected CI energy is reported as method evidence and does not replace the primary run energy.']`

## QSCI Post-Correlation

- method: `qsci_nevpt2`
- source_wavefunction: `qsci_plus`
- active_ci_coefficients_digest: `2f7f51cff381a3dd15564df58ec01d4700a6aa77da2903898691182d8771caa4`
- correction_eligibility_audit: `{'schema': 'qcchem.qsci_post_correlation_eligibility.v1', 'status': 'coefficient_provenance_only', 'method': 'qsci_nevpt2', 'source_wavefunction': 'qsci_plus', 'selected_subspace_size': 4, 'eligible_coefficient_count': 4, 'ci_coefficients_digest': '2f7f51cff381a3dd15564df58ec01d4700a6aa77da2903898691182d8771caa4', 'ci_energy_hartree': -1.8572750302023795, 'variance_estimate': 0.0, 'amplitude_mapping_status': 'not_applicable_to_nevpt2', 'backend_executable': False, 'correction_energy_emitted': False, 'total_corrected_energy_emitted': False, 'energy_replaces_primary': False, 'required_inputs_missing': ['active-space one- and two-particle density matrices', 'contracted perturber-space intermediates', 'executable QSCI-to-NEVPT2 backend', 'double-counting correction model'], 'required_input_missing_count': 4, 'promotion_blockers': ['external_correlation_energy_not_emitted', 'double_counting_not_evaluated', 'qcchem_qsci_correction_backend_missing', 'active-space one- and two-particle density matrices', 'contracted perturber-space intermediates', 'executable QSCI-to-NEVPT2 backend', 'double-counting correction model']}`
- amplitude_mapping_audit: `{'schema': 'qcchem.qsci_tcc_amplitude_mapping_audit.v1', 'status': 'not_applicable_to_nevpt2', 'coefficient_count': 4, 'mapped_single_count': 0, 'mapped_double_count': 0, 'unsupported_excitation_count': 0, 'energy_correction_backend_executable': False, 'energy_replaces_primary': False}`
- tailored_amplitudes: `{'status': 'not_constructed', 'source': 'selected_ci_coefficients_digest', 'eligible_coefficient_count': 4, 'selected_subspace_size': 4, 'mapped_single_count': 0, 'mapped_double_count': 0, 'required_inputs_missing': ['active-space one- and two-particle density matrices', 'contracted perturber-space intermediates', 'executable QSCI-to-NEVPT2 backend', 'double-counting correction model']}`
- external_correlation_energy: `None`
- total_corrected_energy: `None`
- double_counting_audit: `{'status': 'not_evaluated', 'active_space_energy_available': True, 'active_space_ci_energy_hartree': -1.8572750302023795, 'dynamic_correlation_energy_emitted': False, 'energy_replaces_primary': False, 'backend_executable': False, 'required_input_missing_count': 4, 'reason': 'No executable QSCI-derived TCC/NEVPT2 correction model is available in v1.'}`
- classical_solver: `None`
- trust_gate: `unsupported_for_claim`
- notes: `['QSCI post-correlation v1 records coefficient provenance and correction eligibility only.', 'No external-correlation or corrected-total energy is emitted without an executable QSCI-derived TCC/NEVPT2 backend.', 'Use the validated classical NEVPT2 perturbative-correction task for PySCF-backed NEVPT2 corrections.']`

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
- absolute_error_kcal_mol: `1.6720211188925303e-12`
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
- estimated_shot_cost: `50000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `5`
- uncompressed_estimated_shot_cost: `50000.0`
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
- measured_wall_time_seconds: `0.0004007919997093268`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `50000.0`
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
- method: `qsci_nevpt2`
- plugin: `pyscf`
- active_space_energy: `0.000000000000` Hartree
- reduced_active_space_energy: `-1.137306035753` Hartree
- compressed_active_space_energy: `None`
- perturbative_correction: `0.000000000000` Hartree
- corrected_total_energy: `0.000000000000` Hartree
- verification_status: `exploratory`
- provenance: `{'source': 'placeholder', 'reason': 'active_space_required'}`
- notes: `['NEVPT2 correction requires an active-space specification.']`

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
- Timestamp: `2026-07-08T04:20:43.414367+00:00`
- Wall time (s): `0.039725250000628876`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `de25b3b45df6a9c819eefb1dca9fb9ec8c4d85f4d6b2b07e5766e656500e18e3`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `29`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_qsci_plus.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/quantum_evidence.json`
- qcschema.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/qcschema.json`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_qsci_plus.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=f17f21bd4c02
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Z2 tapering skipped for QSCI++ because determinant sampling v1 assumes untapered spin-orbital bitstrings.
- Prepared measurement plan: groups=5, cost=50000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/exact_result.json
- Computed empirical calibration: wall_time=0.000s, measured_cost=None
- Computed perturbative correction: qsci_nevpt2
- Computed QSCI++ selected-subspace workflow: determinants=4
- Wrote integrated method evidence sidecar
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_qsci_plus/report.md
- Run completed
