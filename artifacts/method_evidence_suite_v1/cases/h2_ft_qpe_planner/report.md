# QCchem Report: H2-ft-qpe-planner

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-ft-qpe-planner`
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

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_ft_qpe_planner', 'molecule_name': 'H2-ft-qpe-planner', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `H2-ft-qpe-planner stays within chemical accuracy against exact_baseline for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 0.0, 'units': 'Hartree', 'threshold': 1e-08, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `H2-ft-qpe-planner stays within chemical accuracy against exact_baseline for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 0.0, 'relative_error': 0.0, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.05694129200128373, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': [], 'scientific_risk_notes': [], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:43.622494+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner`

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
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/quantum_evidence.json`
- sidecar_sha256: `77cd0c8545472ee0be140802a96abf442e4b7433f44a112d5c99b944c45c5c2d`
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
- counts_sha256: `649137009f1fd99a17c86096b555e3a29f10ec71c9dc37467f3bc758582e4892`
- shots_per_group: `4096`
- hamiltonian_variance: `4.440892098500626e-16`
- ground_state_overlap: `0.9999999999999998`
- dominant_configurations: `[{'bitstring': '0', 'probability': 0.9875597343674857}, {'bitstring': '1', 'probability': 0.01244026563251424}]`
- z2_check: `{'status': 'applied_z2', 'z2_symmetry_count': 3, 'z2_tapering_values': [-1, 1, -1], 'validation': {'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.857275030202381, 'tapered_ground_energy': -1.8572750302023788, 'absolute_delta': 2.220446049250313e-15}, 'notes': ['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=2.22045e-15 Hartree.']}`
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
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/method_evidence.json`
- sidecar_sha256: `cd957ac07d423ae0aa4648dce2e29aa87b0725a98e342119477d7b9a5ccf7973`
- methods: `{'ft_qpe_resource_estimate': {'available': True, 'trust_tier': 'exploratory'}}`
- promotion_gate_audit: `{'schema': 'qcchem.method_promotion_gate_audit.v1', 'primary_solver_kind': 'exact', 'primary_energy_policy': 'raw_solver_energy_remains_primary', 'sidecar_energy_replacement_allowed_methods': [], 'accuracy_claim_allowed_methods': [], 'hardware_claim_allowed_methods': [], 'planning_metric_methods': ['ft_qpe_resource_estimate'], 'resource_model_only_methods': ['ft_qpe_resource_estimate'], 'unsupported_for_claim_methods': [], 'method_records': {'ft_qpe_resource_estimate': {'method': 'ft_qpe_resource_estimate', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': True, 'resource_model_claim_allowed': True, 'claim_status': 'resource_model_only', 'evidence_role': 'fault_tolerant_resource_model', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['encoding_scale_assumptions_not_derived_from_integral_factorization', 'no_compiled_fault_tolerant_circuit', 'surface_code_distance_not_estimated', 'logical_error_budget_not_allocated', 'hardware_architecture_cycle_model_not_calibrated'], 'validated_resource_advantage_claim_allowed': False, 'promotion_readiness_status': 'blocked_missing_compiled_fault_tolerant_evidence', 'readiness_level': 'resource_model_only_not_compiled', 'resource_formula_scope': 'coarse_pauli_l1_phase_estimation_scaling', 'reference_encoding': 'double_factorization', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 3, 'logical_error_budget_available': False, 'required_promotion_evidence_count': 5, 'required_promotion_evidence': ['executable_integral_factorization_for_each_encoding', 'compiled_fault_tolerant_phase_estimation_circuit', 'surface_code_distance_and_physical_qubit_layout', 'logical_error_budget_allocation', 'hardware_architecture_specific_cycle_model'], 'promotion_blocker_count': 5}}, 'overall_claim_status': 'promotion_required', 'promotion_required_for_validated_claims': True, 'notes': ['Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.', 'Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.']}`
- trust_tier: `exploratory`
- notes: `['Method evidence is reported alongside the primary solver result.', 'Exploratory method sections do not promote chemical-accuracy claims by themselves.']`

## FT-QPE Planner

- encodings_compared: `['double_factorization', 'symmetry_compressed_double_factorization', 'tensor_hypercontraction']`
- lambda_norms: `{'double_factorization': 2.0178991909872144, 'symmetry_compressed_double_factorization': 1.5134243932404108, 'tensor_hypercontraction': 1.3116344741416894}`
- toffoli_counts: `{'double_factorization': 2017.8991909872143, 'symmetry_compressed_double_factorization': 1513.4243932404108, 'tensor_hypercontraction': 1311.6344741416895}`
- logical_qubits: `{'double_factorization': 8, 'symmetry_compressed_double_factorization': 8, 'tensor_hypercontraction': 8}`
- physical_qubits: `{'double_factorization': 8000, 'symmetry_compressed_double_factorization': 8000, 'tensor_hypercontraction': 8000}`
- runtime_estimates: `{'double_factorization': 0.0020178991909872144, 'symmetry_compressed_double_factorization': 0.001513424393240411, 'tensor_hypercontraction': 0.0013116344741416896}`
- dominant_cost_terms: `{'pauli_term_count': 3, 'qubit_count': 1, 'precision_hartree': 0.001, 'coefficient_l1_norm': 2.0178991909872144, 'phase_estimation_steps': {'double_factorization': 2018, 'symmetry_compressed_double_factorization': 1514, 'tensor_hypercontraction': 1312}, 'surface_code_overhead_factor': 1000}`
- recommended_encoding: `tensor_hypercontraction`
- resource_formula_audit: `{'schema': 'qcchem.ft_qpe_resource_formula_audit.v1', 'scope': 'coarse_pauli_l1_phase_estimation_scaling', 'input_terms': {'coefficient_l1_norm': 2.0178991909872144, 'num_qubits': 1, 'pauli_term_count': 3, 'precision_hartree': 0.001, 'cycle_time_ns': 1000.0, 'physical_error_rate': 0.001, 'surface_code_overhead_factor': 1000}, 'formulae': {'lambda_norm': 'coefficient_l1_norm * encoding_scale_assumption', 'phase_estimation_steps': 'ceil(lambda_norm / precision_hartree)', 'toffoli_count': 'lambda_norm / precision_hartree * max(num_qubits, 1)', 'logical_qubits': 'num_qubits + 4 + pauli_term_count', 'physical_qubits': 'logical_qubits * surface_code_overhead_factor', 'runtime_seconds': 'toffoli_count * cycle_time_ns * 1e-9', 'surface_code_overhead_factor': 'round(1 / physical_error_rate)'}, 'encoding_scale_assumptions': {'double_factorization': 1.0, 'symmetry_compressed_double_factorization': 0.75, 'tensor_hypercontraction': 0.65, 'first_quantization_active_basis': 0.85}, 'encoding_formula_components': {'double_factorization': {'encoding_scale_assumption': 1.0, 'lambda_norm': 2.0178991909872144, 'phase_estimation_steps': 2018, 'toffoli_count': 2017.8991909872143, 'logical_qubits': 8, 'physical_qubits': 8000, 'runtime_seconds': 0.0020178991909872144}, 'symmetry_compressed_double_factorization': {'encoding_scale_assumption': 0.75, 'lambda_norm': 1.5134243932404108, 'phase_estimation_steps': 1514, 'toffoli_count': 1513.4243932404108, 'logical_qubits': 8, 'physical_qubits': 8000, 'runtime_seconds': 0.001513424393240411}, 'tensor_hypercontraction': {'encoding_scale_assumption': 0.65, 'lambda_norm': 1.3116344741416894, 'phase_estimation_steps': 1312, 'toffoli_count': 1311.6344741416895, 'logical_qubits': 8, 'physical_qubits': 8000, 'runtime_seconds': 0.0013116344741416896}}, 'reference_encoding': 'double_factorization', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 3}`
- resource_model_audit: `{'model_scope': 'coarse_pauli_l1_phase_estimation_scaling', 'resource_claim_status': 'resource_model_only', 'promotion_readiness_status': 'blocked_missing_compiled_fault_tolerant_evidence', 'readiness_level': 'resource_model_only_not_compiled', 'compiled_fault_tolerant_circuit_available': False, 'surface_code_distance_available': False, 'logical_error_budget_available': False, 'validated_resource_advantage_claim_allowed': False, 'reference_encoding': 'double_factorization', 'recommended_encoding': 'tensor_hypercontraction', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 3, 'best_to_reference_toffoli_ratio': 0.6500000000000001, 'toffoli_reduction_vs_reference': 0.34999999999999987, 'lambda_reduction_vs_reference': 0.35, 'phase_estimation_steps': {'double_factorization': 2018, 'symmetry_compressed_double_factorization': 1514, 'tensor_hypercontraction': 1312}, 'encoding_scale_assumptions': {'double_factorization': 1.0, 'symmetry_compressed_double_factorization': 0.75, 'tensor_hypercontraction': 0.65, 'first_quantization_active_basis': 0.85}, 'surface_code_overhead_model': 'logical_qubits * round(1 / physical_error_rate)', 'surface_code_overhead_factor': 1000, 'cycle_time_ns': 1000.0, 'physical_error_rate': 0.001, 'required_promotion_evidence': ['executable_integral_factorization_for_each_encoding', 'compiled_fault_tolerant_phase_estimation_circuit', 'surface_code_distance_and_physical_qubit_layout', 'logical_error_budget_allocation', 'hardware_architecture_specific_cycle_model'], 'required_promotion_evidence_count': 5, 'promotion_blockers': ['encoding_scale_assumptions_not_derived_from_integral_factorization', 'no_compiled_fault_tolerant_circuit', 'surface_code_distance_not_estimated', 'logical_error_budget_not_allocated', 'hardware_architecture_cycle_model_not_calibrated'], 'promotion_blocker_count': 5}`
- promotion_readiness_audit: `{'schema': 'qcchem.ft_qpe_promotion_readiness.v1', 'status': 'blocked_missing_compiled_fault_tolerant_evidence', 'readiness_level': 'resource_model_only_not_compiled', 'resource_model_claim_allowed': True, 'validated_resource_advantage_claim_allowed': False, 'compiled_fault_tolerant_circuit_available': False, 'surface_code_distance_available': False, 'logical_error_budget_available': False, 'executable_factorization_available': False, 'reference_encoding': 'double_factorization', 'best_encoding': 'tensor_hypercontraction', 'encoding_comparison_count': 3, 'best_to_reference_toffoli_ratio': 0.6500000000000001, 'toffoli_reduction_vs_reference': 0.34999999999999987, 'lambda_reduction_vs_reference': 0.35, 'promotion_blockers': ['encoding_scale_assumptions_not_derived_from_integral_factorization', 'no_compiled_fault_tolerant_circuit', 'surface_code_distance_not_estimated', 'logical_error_budget_not_allocated', 'hardware_architecture_cycle_model_not_calibrated'], 'promotion_blocker_count': 5, 'required_promotion_evidence': ['executable_integral_factorization_for_each_encoding', 'compiled_fault_tolerant_phase_estimation_circuit', 'surface_code_distance_and_physical_qubit_layout', 'logical_error_budget_allocation', 'hardware_architecture_specific_cycle_model'], 'required_promotion_evidence_count': 5}`
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
- Qubit count: `1`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `3`
- Raw qubit count: `4`
- Raw qubit Hamiltonian terms: `15`
- Symmetry tapered qubits: `3`
- Z2 symmetry count: `3`
- Z2 tapering values: `[-1, 1, -1]`
- Symmetry reduction status: `applied_z2`
- Symmetry reduction validation: `{'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.857275030202381, 'tapered_ground_energy': -1.8572750302023788, 'absolute_delta': 2.220446049250313e-15}`
- Symmetry reduction notes: `['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=2.22045e-15 Hartree.']`

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
- measured_wall_time_seconds: `9.879099889076315e-05`
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
- Timestamp: `2026-07-08T04:20:43.622494+00:00`
- Wall time (s): `0.05694129200128373`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `d425aedd6e440310317eeb851e3658e3ced5a12051f5bf4773f8bc0f425daf1e`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `43`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_ft_qpe_planner.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/quantum_evidence.json`
- qcschema.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/qcschema.json`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/h2_ft_qpe_planner.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=f17f21bd4c02
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=2, cost=20000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/exact_result.json
- Computed empirical calibration: wall_time=0.000s, measured_cost=None
- Wrote integrated method evidence sidecar
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/h2_ft_qpe_planner/report.md
- Run completed
