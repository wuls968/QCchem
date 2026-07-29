# QCchem Report: LiH-shadow-lr-e-adapt

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `LiH-shadow-lr-e-adapt`
- basis: `sto3g`
- method: `statevector`
- mapping_kind: `jordan_wigner`
- num_qubits: `2`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000047172` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-7.862128786267` Hartree
- headline_correlation_energy: `-0.000264016458` Hartree
- headline_absolute_error: `0.000000047172` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'lih_shadow_lr_e_adapt', 'molecule_name': 'LiH-shadow-lr-e-adapt', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `LiH-shadow-lr-e-adapt stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 4.717189105996056e-08, 'units': 'Hartree', 'threshold': 0.001, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `LiH-shadow-lr-e-adapt stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `manual` / transformers=`['ActiveSpaceTransformer']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 4.717189105996056e-08, 'relative_error': 4.4580997927485794e-08, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.8242659999996249, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 4, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'exploratory', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=evidence_gated_adapt_vqe_v1'], 'scientific_risk_notes': ['E-ADAPT v1 grows a finite-difference qubit-Pauli adaptive ansatz but remains exploratory until benchmark gates promote it.', 'Selected operators are PauliEvolutionGate directions from the mapped qubit Hamiltonian, not a chemically complete fermionic excitation pool.'], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:44.716752+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000047172` Hartree
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
- Verification Notes: `['validation_scope=evidence_gated_adapt_vqe_v1']`
- Scientific Risk Notes: `['E-ADAPT v1 grows a finite-difference qubit-Pauli adaptive ansatz but remains exploratory until benchmark gates promote it.', 'Selected operators are PauliEvolutionGate directions from the mapped qubit Hamiltonian, not a chemically complete fermionic excitation pool.']`

## Energy Summary

- electronic_energy: `-8.854336056742` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-7.862128786267` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058116487965` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000264016458` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `-7.796219568777` Hartree
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
- solver_hamiltonian_energy: `-1.058116535137` Hartree
- electronic_energy: `-8.854336103914` Hartree
- total_energy: `-7.862128833439` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `variational_result`
- exact_electronic_energy: `-8.854336103914` Hartree
- exact_total_energy: `-7.862128833439` Hartree
- absolute_error: `0.000000047172` Hartree
- relative_error: `4.4580997927485794e-08`
- statistical_error: `None`
- absolute_error_threshold: `0.001`
- relative_error_threshold: `0.001`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/quantum_evidence.json`
- sidecar_sha256: `f0636e10f2e5978df7004abb644bbe121fa2126f2f5761f26010593ba68d1787`
- pauli_terms_available: `True`
- pauli_unavailable_reason: `None`
- pauli_term_count: `9`
- measurement_group_count: `4`
- energy_contribution_sum: `-1.058116487965` Hartree
- coefficient_l1_norm: `1.37203058352284`
- projected_matrix_dimension: `None`
- projected_hamiltonian_nnz: `None`
- physical_sector_dimension: `None`
- basis_hash: `None`
- projected_matrix_sha256: `None`
- groups_sha256: `e024ae2235e5b06b134fec5160b839ec259c052da640114ad6e3f8bf6f341f65`
- measurement_group_count_scope: `pauli_grouping`
- estimated_measurement_cost_scope: `pauli_grouping`
- estimated_measurement_cost_is_hardware_cost: `None`
- sparse_exploratory_estimated_measurement_cost: `None`
- counts_available: `True`
- counts_source: `statevector_sampler_from_final_state`
- counts_sha256: `9367402264eb17774f48a8cfee65d223fc0aa844c3d1ad49f752d7eb5a4973eb`
- shots_per_group: `4096`
- hamiltonian_variance: `1.910876812338813e-08`
- ground_state_overlap: `0.9999997915910717`
- dominant_configurations: `[{'bitstring': '00', 'probability': 0.9995043470322302}, {'bitstring': '11', 'probability': 0.0004014277936372136}, {'bitstring': '10', 'probability': 5.1168002249160604e-05}, {'bitstring': '01', 'probability': 4.30571718836012e-05}]`
- z2_check: `{'status': 'applied_z2', 'z2_symmetry_count': 2, 'z2_tapering_values': [-1, -1], 'validation': {'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.0581165351365447, 'tapered_ground_energy': -1.0581165351365405, 'absolute_delta': 4.218847493575595e-15}, 'notes': ['Applied Z2 tapering in sector [-1, -1]; removed 2 qubits.', 'Exact-spectrum validation passed with delta=4.21885e-15 Hartree.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 2, 'raw_num_qubits': 4, 'qubit_term_count': 9, 'raw_qubit_term_count': 27, 'circuit_depth': 17, 'circuit_size': 24, 'two_qubit_gate_count': 4, 'operation_counts': {'u': 12, 'p': 8, 'cx': 4}}`
- error_budget: `{'ansatz_error': {'available': True, 'absolute_error_hartree': 4.717189105996056e-08, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
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
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/method_evidence.json`
- sidecar_sha256: `c873d335740610eeb90cfd3d881addd25516edce47cd8c1dfad36b313a99c881`
- methods: `{'e_adapt_result': {'available': True, 'trust_tier': 'exploratory'}, 'shadow_lr': {'available': True, 'trust_tier': 'exploratory'}}`
- promotion_gate_audit: `{'schema': 'qcchem.method_promotion_gate_audit.v1', 'primary_solver_kind': 'e_adapt_vqe', 'primary_energy_policy': 'raw_solver_energy_remains_primary', 'sidecar_energy_replacement_allowed_methods': [], 'accuracy_claim_allowed_methods': [], 'hardware_claim_allowed_methods': [], 'planning_metric_methods': ['shadow_lr'], 'resource_model_only_methods': [], 'unsupported_for_claim_methods': [], 'method_records': {'e_adapt_result': {'method': 'e_adapt_result', 'primary_solver_selected': True, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'primary_solver_exploratory', 'evidence_role': 'adaptive_solver_trace', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['accuracy_benchmark_gate_required']}, 'shadow_lr': {'method': 'shadow_lr', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': True, 'resource_model_claim_allowed': False, 'claim_status': 'planning_metric_only', 'evidence_role': 'measurement_planning_cost_model', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['not_hardware_calibrated', 'accuracy_claim_not_supported_by_measurement_plan_alone'], 'estimated_cost_claim_status': 'planning_metric_only', 'hardware_cost_claim_allowed': False, 'allocated_shots': 1024, 'grouped_precision_baseline_shots': 40000.0, 'basis_l1_coverage_fraction': 1.0, 'unselected_basis_count': 0, 'max_allocated_shot_fraction': 0.90625, 'allocation_entropy': 0.29000643188852765, 'grouped_precision_variance_proxy': 4.7061698053050614e-05, 'variance_inflation_vs_grouped_precision_proxy': 39.0625, 'plan_digest': 'c1aa2f714eae0e4dc710965ad4baac21edec64400e2a8a07f968587a72fdb862'}}, 'overall_claim_status': 'promotion_required', 'promotion_required_for_validated_claims': True, 'notes': ['Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.', 'Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.']}`
- trust_tier: `exploratory`
- notes: `['Method evidence is reported alongside the primary solver result.', 'Exploratory method sections do not promote chemical-accuracy claims by themselves.']`

## E-ADAPT

- selected_operators: `[{'operator_id': 'excitation_2', 'pauli': 'multi_pauli', 'pauli_terms': ['XY', 'YX'], 'coefficient_l1': 0.9999999999999997, 'coefficient_abs': 0.9999999999999997, 'gradient_proxy': 0.009999999999999997, 'finite_difference_step': 0.01, 'two_qubit_increment': 2, 'low_rank_priority_score': 0.49999999999999983, 'pool_origin': 'ansatz_excitation_operators', 'excitation': '((0, 2), (1, 3))', 'finite_difference_plus_energy': -1.0575228259673213, 'finite_difference_minus_energy': -1.0580453504739613, 'gradient': 0.026126225332001596, 'gradient_abs': 0.026126225332001596, 'energy_lowering_scan_hartree': 0.0001928789673613096, 'best_scan_angle': -0.01, 'best_scan_energy': -1.0580453504739613, 'angle_scan': [{'angle': -0.25, 'energy': -1.0222577502427868}, {'angle': -0.1, 'energy': -1.0536320926540395}, {'angle': -0.05, 'energy': -1.0574484787107872}, {'angle': -0.01, 'energy': -1.0580453504739613}, {'angle': 0.01, 'energy': -1.0575228259673213}, {'angle': 0.05, 'energy': -1.0548400344790039}, {'angle': 0.1, 'energy': -1.0484412669029999}, {'angle': 0.25, 'energy': -1.0097313355136828}], 'gradient_evaluation_status': 'finite_difference', 'selected_step': 1, 'energy_before_optimization': -1.0578524715066, 'energy_after_optimization': -1.058114092582726, 'energy_lowering_hartree': 0.00026162107612592855, 'optimized_parameter': -0.0005567113633583351, 'operator_acceptance_min_improvement_hartree': 0.0, 'optimization_status': 'accepted', 'selection_status': 'accepted_after_optimization'}, {'operator_id': 'excitation_1', 'pauli': 'YI', 'pauli_terms': ['YI'], 'coefficient_l1': 0.9999999999999997, 'coefficient_abs': 0.9999999999999997, 'gradient_proxy': 0.009999999999999997, 'finite_difference_step': 0.01, 'two_qubit_increment': 0, 'low_rank_priority_score': 0.9999999999999997, 'pool_origin': 'ansatz_excitation_operators', 'excitation': '((2,), (3,))', 'finite_difference_plus_energy': -1.0580874295425737, 'finite_difference_minus_energy': -1.058109883887691, 'gradient': 0.001122717255863659, 'gradient_abs': 0.001122717255863659, 'energy_lowering_scan_hartree': 0.0, 'best_scan_angle': -0.01, 'best_scan_energy': -1.058109883887691, 'angle_scan': [{'angle': -0.25, 'energy': -1.0489348284159978}, {'angle': -0.1, 'energy': -1.0566871251526866}, {'angle': -0.05, 'energy': -1.0577845505996366}, {'angle': -0.01, 'energy': -1.058109883887691}, {'angle': 0.01, 'energy': -1.0580874295425737}, {'angle': 0.05, 'energy': -1.0576724584273922}, {'angle': 0.1, 'energy': -1.0564640607961302}, {'angle': 0.25, 'energy': -1.0483965332052696}], 'gradient_evaluation_status': 'finite_difference', 'selected_step': 2, 'energy_before_optimization': -1.058114092582726, 'energy_after_optimization': -1.058116507260394, 'energy_lowering_hartree': 2.4146776680389337e-06, 'optimized_parameter': 0.0002971878434018608, 'operator_acceptance_min_improvement_hartree': 0.0, 'optimization_status': 'accepted', 'selection_status': 'accepted_after_optimization'}]`
- rejected_operators: `[{'operator_id': 'excitation_0', 'pauli': 'IY', 'pauli_terms': ['IY'], 'coefficient_l1': 0.9999999999999997, 'coefficient_abs': 0.9999999999999997, 'gradient_proxy': 0.009999999999999997, 'finite_difference_step': 0.01, 'two_qubit_increment': 0, 'low_rank_priority_score': 0.9999999999999997, 'pool_origin': 'ansatz_excitation_operators', 'excitation': '((0,), (1,))', 'finite_difference_plus_energy': -1.058098438539585, 'finite_difference_minus_energy': -1.0580946773845972, 'gradient': -0.00018805774939512077, 'gradient_abs': 0.00018805774939512077, 'energy_lowering_scan_hartree': 0.0, 'best_scan_angle': 0.01, 'best_scan_energy': -1.058098438539585, 'angle_scan': [{'angle': -0.25, 'energy': -1.0486095150320942}, {'angle': -0.1, 'energy': -1.056553361722525}, {'angle': -0.05, 'energy': -1.0577166653696122}, {'angle': -0.01, 'energy': -1.0580946773845972}, {'angle': 0.01, 'energy': -1.058098438539585}, {'angle': 0.05, 'energy': -1.05773544106895}, {'angle': 0.1, 'energy': -1.0565907255206195}, {'angle': 0.25, 'energy': -1.0486996807308155}], 'gradient_evaluation_status': 'finite_difference', 'selected_step': 3, 'energy_before_optimization': -1.0581164758738246, 'energy_after_optimization': -1.0581164758738246, 'energy_lowering_hartree': 0.0, 'optimized_parameter': 0.0, 'operator_acceptance_min_improvement_hartree': 0.0, 'optimization_status': 'rejected_no_improvement', 'selection_status': 'rejected_after_optimization', 'optimizer_message': 'Maximum number of function evaluations has been exceeded.', 'reason': 'adaptive_optimization_no_improvement'}]`
- gradient_history: `[{'step': 1, 'operator_id': 'excitation_2', 'pauli': 'multi_pauli', 'gradient': 0.026126225332001596, 'gradient_abs': 0.026126225332001596, 'gradient_proxy': 0.009999999999999997, 'gradient_evaluation_status': 'finite_difference', 'energy_lowering_scan_hartree': 0.0001928789673613096, 'best_scan_angle': -0.01, 'energy_lowering_proxy_hartree': 0.0006825796500985219}, {'step': 2, 'operator_id': 'excitation_1', 'pauli': 'YI', 'gradient': 0.001122717255863659, 'gradient_abs': 0.001122717255863659, 'gradient_proxy': 0.009999999999999997, 'gradient_evaluation_status': 'finite_difference', 'energy_lowering_scan_hartree': 0.0, 'best_scan_angle': -0.01, 'energy_lowering_proxy_hartree': 1.2604940366140246e-06}, {'step': 3, 'operator_id': 'excitation_0', 'pauli': 'IY', 'gradient': -0.00018805774939512077, 'gradient_abs': 0.00018805774939512077, 'gradient_proxy': 0.009999999999999997, 'gradient_evaluation_status': 'finite_difference', 'energy_lowering_scan_hartree': 0.0, 'best_scan_angle': 0.01, 'energy_lowering_proxy_hartree': 3.536571710755804e-08}]`
- depth_growth: `[{'step': 1, 'operator_id': 'excitation_2', 'two_qubit_increment': 2, 'cumulative_two_qubit_increment': 2}, {'step': 2, 'operator_id': 'excitation_1', 'two_qubit_increment': 0, 'cumulative_two_qubit_increment': 2}]`
- adaptive_optimization: `{'status': 'completed', 'energy_replaces_delegate': False, 'delegate_energy': -1.0581164879646494, 'adaptive_energy': -1.058116507260394, 'delegate_energy_improvement_hartree': 1.9295744557723538e-08, 'replacement_min_improvement_hartree': 1.0000000000000002e-06, 'delegate_improvement_to_replacement_threshold_ratio': 0.019295744557723534, 'adaptive_improvement_status': 'positive_below_replacement_threshold', 'optimization_signal_present': True, 'selected_operator_count': 2, 'cumulative_selected_energy_lowering_hartree': 0.0002640357537939675, 'max_selected_energy_lowering_hartree': 0.00026162107612592855, 'min_selected_energy_lowering_hartree': 2.4146776680389337e-06, 'final_cumulative_two_qubit_increment': 2, 'operator_acceptance_policy': 'optimized_energy_must_improve_current_energy', 'operator_acceptance_min_improvement_hartree': 0.0, 'no_improvement_rejection_count': 1, 'adaptive_iterations': 160, 'adaptive_evaluations': 221, 'adaptive_evaluations_per_selected_operator': 110.5, 'optimizer_message': 'Maximum number of function evaluations has been exceeded.', 'optimization_history': [{'step': 1, 'operator_id': 'excitation_2', 'energy': -1.058114092582726, 'energy_before_optimization': -1.0578524715066, 'energy_lowering_hartree': 0.00026162107612592855, 'accepted': True, 'operator_acceptance_min_improvement_hartree': 0.0, 'iterations': 40, 'evaluations': 40, 'optimizer_message': 'Maximum number of function evaluations has been exceeded.', 'trajectory': [{'evaluation_index': 1, 'parameters': [0.0, 0.0, 0.0, 0.0], 'energy': -1.0578524715065996, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 2, 'parameters': [1.0, 0.0, 0.0, 0.0], 'energy': -0.5617534139877414, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 3, 'parameters': [0.0, 1.0, 0.0, 0.0], 'energy': -0.9495588473177456, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 4, 'parameters': [0.0, 0.0, 1.0, 0.0], 'energy': -0.9495588473177458, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 5, 'parameters': [0.0, 0.0, 0.0, 1.0], 'energy': -0.5617534139877414, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 6, 'parameters': [-0.6908388547133302, -0.1508034376875222, -0.15080343768752205, -0.6908388547133302], 'energy': -0.4628184032539231, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 7, 'parameters': [-0.3454194273566651, -0.0754017188437611, -0.07540171884376103, -0.3454194273566651], 'energy': -0.8085069691215024, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 8, 'parameters': [0.23128397478513799, -0.019795897201404594, -0.01979589720140458, -0.0906860954919248], 'energy': -1.0399733366091255, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 9, 'parameters': [-2.331903250719248e-18, 0.0883883476483184, -0.08838834764831847, 0.0], 'energy': -1.0558500459371314, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 10, 'parameters': [0.010541105370882053, 0.17402846336568423, 0.17564432395246796, -0.035384325617696576], 'energy': -1.0481649521469563, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 11, 'parameters': [0.06331019054228641, 0.005764957070024634, 0.015469863532836744, 0.2412866933043668], 'energy': -0.9895197689200801, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 12, 'parameters': [-0.07355794898228925, -0.02388711841447357, -0.01445319490873557, -0.09713258398859752], 'energy': -1.0431771180943064, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 13, 'parameters': [-0.005085918187733837, -0.008076663101945963, 0.0003166863821397088, 0.06176609635601646], 'energy': -1.0541213631815414, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 14, 'parameters': [-0.012528332681419747, 0.020215449839148945, 0.020215449839148924, 0.0015081630632582496], 'energy': -1.0578688627210073, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 15, 'parameters': [0.043680885342286216, 0.03510452496172434, 0.041081933795205194, -0.007961741818494282], 'energy': -1.0557772218744075, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 16, 'parameters': [-0.028849388911810124, 0.011960624153482896, 0.020553190823903857, -0.023828162784246164], 'energy': -1.0570580792393558, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 17, 'parameters': [-0.012206363971136886, 0.031152824061633493, 0.009769328052129572, -0.002401996252893584], 'energy': -1.0578495226999904, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 18, 'parameters': [-0.025702103764909393, 0.0200429085400354, 0.010695511144943515, 0.02819814718087216], 'energy': -1.0577014962884976, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 19, 'parameters': [0.0009844945271094002, 0.024613108252454618, 0.0241947597161859, 0.006643318291178061], 'energy': -1.057439057559829, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 20, 'parameters': [-0.01687038533108738, 0.019785662797381122, 0.017588884675044558, 0.007432534217647224], 'energy': -1.057879032227434, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 21, 'parameters': [-0.018477136225584896, 0.022290899314317384, 0.0201158279301319, 0.007556986639516283], 'energy': -1.057851628964548, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 22, 'parameters': [-0.021778310965000724, 0.01600246323772271, 0.015577575085420787, 0.0031209849545094153], 'energy': -1.0579535863301897, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 23, 'parameters': [-0.02441498718306326, 0.010277428419254175, 0.011870278570093429, 0.00037088974781783945], 'energy': -1.057985663860153, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 24, 'parameters': [-0.031267188778446954, 0.010373551243336965, 0.01397543193599812, -0.0027341995029013205], 'energy': -1.0578102894556038, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 25, 'parameters': [-0.024338243685498414, 0.007813551279344355, 0.014486847773584189, 0.0018992138433077507], 'energy': -1.0579945407737559, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 26, 'parameters': [-0.02230186007388143, 0.005753882837917055, 0.00996980546019601, 0.007577452363023788], 'energy': -1.0580408860838153, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 27, 'parameters': [-0.015444902544813118, 0.0028489230959536506, 0.00914018682918874, 0.005366065576590683], 'energy': -1.058017777110549, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 28, 'parameters': [-0.024071525479901233, 0.0038489950404321702, 0.008369925957486484, 0.010014430300765502], 'energy': -1.0580513074211406, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 29, 'parameters': [-0.023378782209736174, 0.005373383592628423, 0.008896553099984378, 0.013504100660392402], 'energy': -1.0580096641470502, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 30, 'parameters': [-0.023921774239158776, 0.004838106001753034, 0.006705727713651851, 0.009803775267752439], 'energy': -1.058055229367868, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 31, 'parameters': [-0.02640452732703673, 0.003596102052542012, 0.005329978997298189, 0.007424811664262897], 'energy': -1.0580761266208503, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 32, 'parameters': [-0.024548439454644543, 0.0008661695289605724, 0.00357886076061216, 0.0062869275707381975], 'energy': -1.058090211836618, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 33, 'parameters': [-0.026004792208402714, -0.001099617723766497, 0.0009690801138606204, 0.004717675783427484], 'energy': -1.0580986632453262, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 34, 'parameters': [-0.02295978293886334, -0.0029572839458656087, -0.0004478047592391286, 0.0054444639744242905], 'energy': -1.0581055199825864, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 35, 'parameters': [-0.02230802608579823, -0.001594242611238604, -0.0012963954538459622, 0.004543396594461731], 'energy': -1.0581057898824207, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 36, 'parameters': [-0.021176721601978032, -0.0032782173633466713, 1.2859786577821154e-05, 0.001472725824568978], 'energy': -1.0581072612841445, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 37, 'parameters': [-0.020555102553064895, -0.005550587031342962, -0.003056341168351513, 0.0009353987260902075], 'energy': -1.058114092582726, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 38, 'parameters': [-0.018450493292961726, -0.0077275146995940645, -0.005523606373094729, 0.0008806514754356402], 'energy': -1.0581113696148083, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 39, 'parameters': [-0.023660341774305167, -0.006032840542023275, -0.00450044345334786, -0.0008807176202037029], 'energy': -1.058101407421225, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 40, 'parameters': [-0.018813117095007152, -0.006113949659379487, -0.0033939420699181768, 0.0015260188325321624], 'energy': -1.0581100339784302, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}]}, {'step': 2, 'operator_id': 'excitation_1', 'energy': -1.0581164758738246, 'energy_before_optimization': -1.058114092582726, 'energy_lowering_hartree': 2.383291098695395e-06, 'accepted': True, 'operator_acceptance_min_improvement_hartree': 0.0, 'iterations': 40, 'evaluations': 40, 'optimizer_message': 'Maximum number of function evaluations has been exceeded.', 'trajectory': [{'evaluation_index': 1, 'parameters': [-0.020555102553064895, 0.0, -0.005550587031342962, -0.003056341168351513, 0.0009353987260902075], 'energy': -1.058114092582726, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 2, 'parameters': [0.9794448974469351, 0.0, -0.005550587031342962, -0.003056341168351513, 0.0009353987260902075], 'energy': -0.5730563806124586, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 3, 'parameters': [-0.020555102553064895, 1.0, -0.005550587031342962, -0.003056341168351513, 0.0009353987260902075], 'energy': -0.9483026979679658, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 4, 'parameters': [-0.020555102553064895, 0.0, 0.9944494129686571, -0.003056341168351513, 0.0009353987260902075], 'energy': -0.949194781319244, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 5, 'parameters': [-0.020555102553064895, 0.0, -0.005550587031342962, 0.9969436588316485, 0.0009353987260902075], 'energy': -0.9486727557182659, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 6, 'parameters': [-0.020555102553064895, 0.0, -0.005550587031342962, -0.003056341168351513, 1.0009353987260903], 'energy': -0.5730563806124589, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 7, 'parameters': [-0.7021404838391702, -0.15430296111372424, -0.15860002520106514, -0.15683931064682963, -0.6806499825600146], 'energy': -0.5150490896593323, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 8, 'parameters': [-0.36134779319611754, -0.07715148055686212, -0.08207530611620406, -0.07994782590759057, -0.3398572919169622], 'energy': -0.8136864789718098, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 9, 'parameters': [0.21091881818874297, -0.019915739755649295, -0.025304535745846384, -0.02290496608700786, -0.08703619285564591], 'energy': -1.0427220132036623, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 10, 'parameters': [-0.02055510255306489, 0.08802712763619593, -0.0942986844764199, -0.003056341168351513, 0.0009353987260902075], 'energy': -1.0558865265040014, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 11, 'parameters': [-0.009636812116544718, 0.17451819221201556, 0.16938499348787375, -0.011057961354824505, -0.03452878410377147], 'energy': -1.048225111370993, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 12, 'parameters': [-0.02055510255306489, 6.632869528997363e-18, -0.005550587031342953, 0.11887852563517017, -0.02657620351019231], 'energy': -1.0548025933480953, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 13, 'parameters': [0.04544641771590323, 0.004893654958220623, 0.010396782216294895, 0.038403156897276455, 0.23788822714888108], 'energy': -0.9986443655100342, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 14, 'parameters': [-0.09307311981272293, -0.027165042615257876, -0.02062922757393464, -0.03643404066379975, -0.09009625185884661], 'energy': -1.0412170334864734, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 15, 'parameters': [0.03432465159157498, -0.006998536976709211, -0.01108585099394642, -0.010778517077528535, -0.026545720561550655], 'energy': -1.0575028618924427, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 16, 'parameters': [-0.020555116154102448, -0.02118583958459975, -0.026564317566216373, -0.0010135545657415429, 0.009989284797791534], 'energy': -1.0578990653688636, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 17, 'parameters': [0.004472940708606734, 0.008353092640379242, 0.013434422687971466, -0.0025895602564553984, 0.05431539887006699], 'energy': -1.0540426387475397, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 18, 'parameters': [-0.01895405331980542, 0.00014537692192026415, -0.004319482973648429, 0.02775890502064581, -0.0038482183168874412], 'energy': -1.0579123756716136, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 19, 'parameters': [-0.021729659009944332, -0.011254948384577598, 0.00510872876715982, -0.0035969515427056046, -0.0005390184879393192], 'energy': -1.0580842370928538, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 20, 'parameters': [-0.03892661969818344, 0.0003579541019813408, -0.012042720760543375, -0.008520479982057563, -0.022874622553073314], 'energy': -1.0569651471259152, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 21, 'parameters': [-0.016877029515839394, 0.004022186456968395, -8.394971024319568e-05, -0.0037757802587036794, 0.014501264110688684], 'energy': -1.0579106295177094, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 22, 'parameters': [-0.006048547548305333, -0.0008754478945853578, -0.006025686002323994, -0.0053218439233679565, -0.004315873130568615], 'energy': -1.0580510765302067, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 23, 'parameters': [-0.024676096010079657, 0.0019084956427674557, -0.006030872812852111, -0.006303217014635462, -0.004508619676310468], 'energy': -1.0580574274624586, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 24, 'parameters': [-0.020409831453865674, 0.0018164809154163559, -0.0036502430482021897, -0.00043422139714583124, -0.0002692850935730807], 'energy': -1.0581032291146553, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 25, 'parameters': [-0.021466297394539847, -0.0038313447784698615, -0.010239647634365176, 0.0017789345677139672, 0.0005372823903759305], 'energy': -1.0581111825471006, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 26, 'parameters': [-0.020681373291117976, 0.00031455032987723846, -0.005701230139508377, -0.0028753267240932607, 0.004819783269118587], 'energy': -1.0581030460868752, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 27, 'parameters': [-0.021459471605533586, -0.0012182206879288169, -0.004327396442551237, -0.0029964728836424197, 0.0010492969703324547], 'energy': -1.058114278433452, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 28, 'parameters': [-0.01817195952342564, -0.00313901949654616, -0.0037130193048803785, -0.003481812479503576, 0.0006638472087484328], 'energy': -1.0581109950646646, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 29, 'parameters': [-0.021701064831751854, -0.0021753197521052095, -0.0054920393950661055, -0.0017931529715544542, 0.0008597729814730421], 'energy': -1.0581144140037018, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 30, 'parameters': [-0.021870784731852062, -0.0022338734310765667, -0.005576521918001597, -0.002098294454917661, -4.642364015192341e-05], 'energy': -1.0581126671444456, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 31, 'parameters': [-0.022236779767146296, -0.0024996536506017406, -0.006230146006699345, -0.00257437742449865, 0.002365562236279873], 'energy': -1.0581160035266277, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 32, 'parameters': [-0.022614061371188206, -0.001964197051511998, -0.006020194841814776, -0.0016619765945126536, 0.003949572122982695], 'energy': -1.0581138385593118, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 33, 'parameters': [-0.02143161105758663, -0.002932148074444158, -0.00609410653333786, -0.002304706953461447, 0.002530174926056789], 'energy': -1.0581151656695442, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 34, 'parameters': [-0.0224779756716612, -0.002878191106439718, -0.00663032896646434, -0.004404846937434745, 0.002685665589469389], 'energy': -1.0581163340933968, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 35, 'parameters': [-0.022941682393915117, -0.0031671430960794416, -0.007128067259687929, -0.004375743153628724, 0.0020480397579246924], 'energy': -1.0581162313415826, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 36, 'parameters': [-0.022681375615754364, -0.003145920541480057, -0.006276341093445672, -0.004401279160518187, 0.0026787483515065976], 'energy': -1.0581163756758245, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 37, 'parameters': [-0.02265376744265117, -0.0026189830597285143, -0.005821370382701906, -0.004785764299965581, 0.002112690204830014], 'energy': -1.0581162932503283, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 38, 'parameters': [-0.02305746836608161, -0.002892977716749066, -0.006298003647832926, -0.004368289326786383, 0.0028560479687586523], 'energy': -1.0581164758738246, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 39, 'parameters': [-0.02354731992332071, -0.002889625156322357, -0.00620213819288644, -0.004741771911587156, 0.0036077321457995844], 'energy': -1.0581163192038436, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 40, 'parameters': [-0.02318405685731218, -0.0026460829070659624, -0.006028098981040978, -0.0034724263298342643, 0.0028917352883786164], 'energy': -1.0581163568014613, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}]}, {'step': 3, 'operator_id': 'excitation_0', 'energy': -1.0581164758738246, 'energy_before_optimization': -1.0581164758738246, 'energy_lowering_hartree': 0.0, 'accepted': False, 'operator_acceptance_min_improvement_hartree': 0.0, 'iterations': 40, 'evaluations': 40, 'optimizer_message': 'Maximum number of function evaluations has been exceeded.', 'trajectory': [{'evaluation_index': 1, 'parameters': [-0.02305746836608161, -0.002892977716749066, 0.0, -0.006298003647832926, -0.004368289326786383, 0.0028560479687586523], 'energy': -1.0581164758738246, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 2, 'parameters': [0.9769425316339184, -0.002892977716749066, 0.0, -0.006298003647832926, -0.004368289326786383, 0.0028560479687586523], 'energy': -0.573284758570129, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 3, 'parameters': [-0.02305746836608161, 0.997107022283251, 0.0, -0.006298003647832926, -0.004368289326786383, 0.0028560479687586523], 'energy': -0.9487984583095241, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 4, 'parameters': [-0.02305746836608161, -0.002892977716749066, 1.0, -0.006298003647832926, -0.004368289326786383, 0.0028560479687586523], 'energy': -0.9486064302274568, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 5, 'parameters': [-0.02305746836608161, -0.002892977716749066, 0.0, 0.993701996352167, -0.004368289326786383, 0.0028560479687586523], 'energy': -0.9489793667560819, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 6, 'parameters': [-0.02305746836608161, -0.002892977716749066, 0.0, -0.006298003647832926, 0.9956317106732137, 0.0028560479687586523], 'energy': -0.9491806868218187, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 7, 'parameters': [-0.02305746836608161, -0.002892977716749066, 0.0, -0.006298003647832926, -0.004368289326786383, 1.0028560479687587], 'energy': -0.5732847585701292, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 8, 'parameters': [-0.6967960047654361, -0.1548049886830525, -0.1521788596776029, -0.15795861812406364, -0.15574914263724257, -0.6708824884305956], 'energy': -0.5645457446560358, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 9, 'parameters': [-0.3599267365657589, -0.07884898319990079, -0.07608942983880145, -0.08212831088594828, -0.08005871598201449, -0.33401322023091845], 'energy': -0.8296662252190714, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 10, 'parameters': [0.2073088704294282, -0.02285719761730269, -0.01999928905880303, -0.02622918511529549, -0.024262704686041768, -0.08568641954644948], 'energy': -1.0424023401378415, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 11, 'parameters': [-0.02305746836608161, 0.0855728992526374, -0.08831075026313258, -0.006298003647832926, -0.004368289326786383, 0.0028560479687586523], 'energy': -1.0560183784932324, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 12, 'parameters': [-0.012845939320854885, 0.17071992747279935, 0.17566311853882546, -0.014315093305436061, -0.012370590238105748, -0.032759146330368256], 'energy': -1.048382418824201, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 13, 'parameters': [-0.02305746836608161, -0.0028929777167490687, 3.281296241747486e-18, 0.08200870820716036, -0.09283819743886247, 0.0028560479687586523], 'energy': -1.0558858758081844, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 14, 'parameters': [-0.012292359470434075, -0.002112853541452142, 0.0026213512992226697, 0.16747925597512162, 0.17104094323765628, -0.034689890868771604], 'energy': -1.0482636200797866, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 15, 'parameters': [0.04134226572066568, 0.0017739318269228048, 0.015681618110351122, -0.0014982392768170955, 0.012103182804559829, 0.24325287391726724], 'energy': -0.9975107402313914, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 16, 'parameters': [-0.09643623516831272, -0.029097108254286685, -0.015461166502475995, -0.03232096959841439, -0.018893527681197893, -0.0889408754525663], 'energy': -1.0411239414303501, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 17, 'parameters': [0.03158196484101712, -0.009801701258796938, -0.005599326744120707, -0.013178415107491437, -0.009833544017545236, -0.024793370599270247], 'energy': -1.0574780269989434, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 18, 'parameters': [-0.02302159941772454, -0.002880429938365, 1.2569819817592863e-05, 0.014806199213460276, 0.016696983609188983, -0.006494235219128142], 'energy': -1.057868968080248, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 19, 'parameters': [0.0005750319637626011, -0.01348179663294331, -0.001100488276908745, -0.0015688467640221984, 0.01044128992261165, 0.05756191790331367], 'energy': -1.0539946401567941, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 20, 'parameters': [-0.016101946505357206, 0.039476660656117254, 0.04525454897135394, -0.009096796957623192, -0.004179318584766142, 0.0002404594566680564], 'energy': -1.0575296097653295, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 21, 'parameters': [-0.04083060629609508, -0.009894065325363837, 0.0022571084720700105, -0.018249570576582726, -0.006459580167857158, -0.018576517261007817], 'energy': -1.0571331378612727, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 22, 'parameters': [-0.023057468366081607, -0.010947910248847432, 0.008040808044831555, 0.0012648163669969478, -0.011945085900062203, 0.002856047968758661], 'energy': -1.0580456228448722, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 23, 'parameters': [-0.026100959346290777, 0.012519488460943919, -0.015118653030145484, 0.007606662268236726, -0.021559305825737635, -0.0006526693216773616], 'energy': -1.0580889970230176, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 24, 'parameters': [-0.02175170880119886, 0.0080629590234551, 0.0109724469049678, -0.007003294212465587, -0.004688976226360386, 0.0016693714530619716], 'energy': -1.0580789518552034, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 25, 'parameters': [-0.0292974006939462, -0.0022471265039635483, 0.0006643745468170183, -0.0053267835477032, -0.003380407047548102, 0.007251580198833476], 'energy': -1.058112660759559, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 26, 'parameters': [-0.014101144518072994, -0.0015543679612467795, -0.0025848268783766554, -0.006207788819690171, -0.0042320982106020906, 0.015323004105905499], 'energy': -1.0577977714120126, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 27, 'parameters': [-0.027235582172843307, -0.003616834002223007, -0.0006417282825760651, -0.010580639548191733, -0.005726526412236595, -0.0018828295272033144], 'energy': -1.0580660545001501, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 28, 'parameters': [-0.022680930949532684, -0.004754850863437881, 0.0018260311719428158, -0.007734254537228733, -0.0018846642798756473, 0.003147316213231501], 'energy': -1.0581161539486428, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 29, 'parameters': [-0.023943177567848098, -0.0022305106330481237, -0.0009781713537012392, -0.0012814819948796458, 0.000272540840037026, -0.0006299525323701007], 'energy': -1.0580917272204644, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 30, 'parameters': [-0.023304293050750973, -0.004969691676637877, 0.001967997211133039, -0.0044509791780037635, -0.006228789881673523, 0.0024830184304774003], 'energy': -1.0581111628810156, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 31, 'parameters': [-0.023023934678082933, -0.001563341578480862, 0.0013885343393337907, -0.006386569445605632, -0.004410161626495977, 0.0025273905549091967], 'energy': -1.0581157702668216, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 32, 'parameters': [-0.02061742853361242, -0.002323178701970606, -0.00014685057225522275, -0.0061738752210883955, -0.004545554815635307, 0.005841333173020818], 'energy': -1.0580962187867116, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 33, 'parameters': [-0.023876463160876146, -0.0030521093000592464, -0.00025786444513225035, -0.0077114972612584674, -0.004919838744626557, 0.0019900474472001133], 'energy': -1.058114713117868, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 34, 'parameters': [-0.022304468666173728, -0.002960168053637605, -0.00010045833672283922, -0.006322507374229815, -0.004401761894383458, 0.0022474935306286683], 'energy': -1.058116444438073, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 35, 'parameters': [-0.023795040039874506, -0.002698763448155506, -0.00041647226459682094, -0.005404682176608766, -0.003205480304028725, 0.0019024396172941248], 'energy': -1.058114057221271, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 36, 'parameters': [-0.022543677615504167, -0.002634320254478967, -0.0003115513363179317, -0.006524990375747055, -0.004286003819859495, 0.0035397376525907556], 'energy': -1.0581154311271501, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 37, 'parameters': [-0.02310631251708395, -0.0026763827064821945, -0.0002129450953944277, -0.00610484861556326, -0.004692220594149409, 0.0028168882519202616], 'energy': -1.0581164635857723, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 38, 'parameters': [-0.022970738423520782, -0.0034793237738351447, 0.0004557788389615047, -0.005903531502176025, -0.004841824925140291, 0.0029775878723154827], 'energy': -1.0581159318395892, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 39, 'parameters': [-0.023221393011966258, -0.0029705875249098662, -4.897738181394577e-05, -0.006673582564810899, -0.004564044032788017, 0.0027019512604196444], 'energy': -1.0581164301494754, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 40, 'parameters': [-0.0230281491079383, -0.0027418894319456277, 0.00017922753081606866, -0.0063394331681317995, -0.004413504403196751, 0.0028502135893523615], 'energy': -1.0581164663707634, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}]}, {'stage': 'delegate_warm_start_polish', 'energy': -1.058116507260394, 'accepted': True, 'iterations': 40, 'evaluations': 40, 'optimizer_message': 'Maximum number of function evaluations has been exceeded.', 'trajectory': [{'evaluation_index': 1, 'parameters': [0.0, 0.0, -0.006562011375445608, -0.007153396286150541, -0.020084890095887303], 'energy': -1.058116487964649, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 2, 'parameters': [1.0, 0.0, -0.006562011375445608, -0.007153396286150541, -0.020084890095887303], 'energy': -0.5728690870724329, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 3, 'parameters': [0.0, 1.0, -0.006562011375445608, -0.007153396286150541, -0.020084890095887303], 'energy': -0.9487776056809327, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 4, 'parameters': [0.0, 0.0, 0.9934379886245543, -0.007153396286150541, -0.020084890095887303], 'energy': -0.94902245231162, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 5, 'parameters': [0.0, 0.0, -0.006562011375445608, 0.9928466037138495, -0.020084890095887303], 'energy': -0.9491476728495766, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 6, 'parameters': [0.0, 0.0, -0.006562011375445608, -0.007153396286150541, 0.9799151099041127], 'energy': -0.572869087072433, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 7, 'parameters': [-0.6817177046731201, -0.1536087606547244, -0.15982679021231347, -0.16024225443275456, -0.7018025947690074], 'energy': -0.5159326740550556, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 8, 'parameters': [-0.34085885233656005, -0.0768043803273622, -0.08319440079387955, -0.08369782535945254, -0.36094374243244737], 'energy': -0.8138970527198988, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 9, 'parameters': [0.23144871168799924, -0.019842447883557244, -0.026360025326559042, -0.026928685640611273, -0.10814593536842866], 'energy': -1.0426774429955996, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 10, 'parameters': [1.7067668141064904e-19, 0.08828921558985538, -0.09504938002503331, -0.007153396286150541, -0.020084890095887303], 'energy': -1.0559670081089547, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 11, 'parameters': [0.010892091368920977, 0.1740381846071892, 0.1688603774431141, -0.015111098534770415, -0.055521214966807425], 'energy': -1.0484421396782813, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 12, 'parameters': [-4.167622351762633e-18, 2.4490721231849014e-18, -0.006562011375445618, 0.11480921589994414, -0.04747323120564185], 'energy': -1.054951363806718, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 13, 'parameters': [0.06600114163877527, 0.005274317706946148, 0.009449734556934899, 0.03456080850618661, 0.21681082532725912], 'energy': -0.9987622666231782, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 14, 'parameters': [-0.07273208075885816, -0.026677978347747936, -0.021655866603888553, -0.03994872466822055, -0.11129876990822193], 'energy': -1.0410787273630517, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 15, 'parameters': [0.001077444535450441, -0.007039349511624857, -0.005429551994466542, -0.0019739873216695833, 0.041781319827263005], 'energy': -1.0553890961457477, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 16, 'parameters': [-0.014119396867426012, 0.019676959915351754, 0.013070885190832032, -0.006684909770923999, -0.01799867980144052], 'energy': -1.0578342414845916, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 17, 'parameters': [0.05525107993099427, 0.01616609475379266, 0.014904150942060417, -0.01477709944399271, -0.028646932631980666], 'energy': -1.0566876021055895, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 18, 'parameters': [-0.013031028656445372, -0.01222195541676958, -0.007722199212867547, -0.023390319645159766, -0.039893849734418424], 'energy': -1.0573787427930046, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 19, 'parameters': [2.433703688033662e-19, -0.009129846532050916, 0.002588325847491229, 0.001411560284388943, -0.02200826602183286], 'energy': -1.058099704851772, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 20, 'parameters': [-0.0026927724402934917, 0.009645653267280365, -0.02121029030563616, 0.015542307304623675, -0.03219297881935036], 'energy': -1.0577524871814552, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 21, 'parameters': [0.013337377639448032, 0.0039324402319565, -0.002103859468013532, -0.009135270598754498, -0.02527988309916863], 'energy': -1.0580714726265188, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 22, 'parameters': [0.005468186212583203, -0.0026636235455987146, -0.0080747812271498, -0.0060675144917515505, -0.005813342798687365], 'energy': -1.0578366386673002, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 23, 'parameters': [-0.0029543537851761553, 0.00507483366409807, -0.001540841086062377, -0.0069957118709971814, -0.01893772062541437], 'energy': -1.0581038789065076, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 24, 'parameters': [-0.0003897398304239367, -0.0016159589975360317, -0.005113315184426943, -0.01036841963711602, -0.019838978233143383], 'energy': -1.0581122211599943, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 25, 'parameters': [-0.003534565813002064, 0.00013347907451037426, -0.008244628114311574, -0.0075264516237428325, -0.02683424671155126], 'energy': -1.0580486545947856, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 26, 'parameters': [0.0006734594017118316, -0.0004900226504150417, -0.0074811385134081945, -0.0066170841704953276, -0.016419826124046116], 'energy': -1.0581019943657515, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 27, 'parameters': [0.0005807851068449979, 0.0012375827295198366, -0.007436613368462006, -0.00824006265097865, -0.02008646434151066], 'energy': -1.0581160129711276, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 28, 'parameters': [0.0033610815092932683, 3.7012171028106144e-05, -0.004808514227089, -0.006663231174784759, -0.020888342747813777], 'energy': -1.0581115268560355, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 29, 'parameters': [-0.0006086099607420394, -0.00020189428069830072, -0.007315008504828921, -0.00693071309043119, -0.021754302387149288], 'energy': -1.0581136513543663, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 30, 'parameters': [-0.0008842724286428596, 0.0013078562830236787, -0.00542638763031262, -0.00697921297766465, -0.02013274785448068], 'energy': -1.058115352011773, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 31, 'parameters': [-0.0001747599801549195, -0.0003849977552071457, -0.006196511100928627, -0.007952270238262978, -0.020140746628112535], 'energy': -1.0581161505267958, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 32, 'parameters': [-0.00035693203754581484, -2.577817147156779e-05, -0.006795380980641861, -0.007186034198637623, -0.01985073847921646], 'energy': -1.0581165070026741, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 33, 'parameters': [0.00010519056974047037, -0.0002392268394639782, -0.006743477395439043, -0.006981928840325168, -0.019044386385572078], 'energy': -1.0581152672903194, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 34, 'parameters': [-0.0005567113633583351, 0.0002971878434018608, -0.006496642102688348, -0.007130349938718232, -0.019807679225709935], 'energy': -1.058116507260394, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 35, 'parameters': [-0.0006402227545714251, 0.00014166426577088482, -0.0064050799398260765, -0.00699286146673943, -0.01984168215968369], 'energy': -1.0581164643195475, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 36, 'parameters': [-0.0007013406745955963, 0.00045112109680896874, -0.006709373571977442, -0.007101988519052058, -0.020192057225570388], 'energy': -1.058116229911407, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 37, 'parameters': [-0.0006268222884015886, 0.00022190598990832957, -0.0064164574404380415, -0.007326988120872263, -0.01987033376072944], 'energy': -1.0581164576381443, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 38, 'parameters': [-0.0003473090396313435, 0.0003189479378704718, -0.006440433490302358, -0.007141165985105333, -0.019370850484391085], 'energy': -1.0581163386993617, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 39, 'parameters': [-0.0004520102014948393, 0.0003080678906361663, -0.006468537796495353, -0.007135757961911782, -0.01958926485505051], 'energy': -1.0581164932348461, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}, {'evaluation_index': 40, 'parameters': [-0.0006479923026819814, 0.00029216864722273974, -0.0065583789227727325, -0.007137553558886465, -0.019755906338190538], 'energy': -1.0581165057712456, 'reported_std': 0.0, 'seed': None, 'shots': None, 'backend_metadata': {'precision': None}}]}], 'ansatz_parameter_count': 5, 'adaptive_optimal_parameters': [-0.0005567113633583351, 0.0002971878434018608, -0.006496642102688348, -0.007130349938718232, -0.019807679225709935], 'gradient_reference': 'delegate_initial_point_or_fallback'}`
- symmetry_audit: `{'z2_tapering_requested': True, 'point_group_filter_requested': True, 'status': 'metadata_gated'}`
- ansatz_trust_gate: `passed`
- notes: `['E-ADAPT evidence is exploratory and does not promote the run by itself.']`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- Transformers applied: `['ActiveSpaceTransformer']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475, 'ActiveSpaceTransformer': -7.796219568777056}`
- Electronic constant correction: `-7.796219568777` Hartree
- Point-group metadata: `{'enabled': True, 'status': 'available', 'group': 'Coov', 'topgroup': 'Coov', 'irrep_names': ['A1', 'E1x', 'E1y'], 'irrep_ids': [0, 2, 3], 'notes': [], 'orbital_irreps': ['A1', 'A1', 'A1', 'E1x', 'E1y', 'A1'], 'orbital_occupations': [2.0, 2.0, 0.0, 0.0, 0.0, 0.0], 'orbital_energies': [-2.3487619299812823, -0.2852707712014576, 0.07821656593872457, 0.1639413456784407, 0.1639413456784407, 0.5477083855957863], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `2`
- Fermionic Hamiltonian terms: `72`
- Qubit Hamiltonian terms: `9`
- Raw qubit count: `4`
- Raw qubit Hamiltonian terms: `27`
- Symmetry tapered qubits: `2`
- Z2 symmetry count: `2`
- Z2 tapering values: `[-1, -1]`
- Symmetry reduction status: `applied_z2`
- Symmetry reduction validation: `{'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.0581165351365447, 'tapered_ground_energy': -1.0581165351365405, 'absolute_delta': 4.218847493575595e-15}`
- Symmetry reduction notes: `['Applied Z2 tapering in sector [-1, -1]; removed 2 qubits.', 'Exact-spectrum validation passed with delta=4.21885e-15 Hartree.']`

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
- absolute_error_hartree: `0.000000047172` Hartree
- absolute_error_kcal_mol: `2.9600808685956244e-05`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- finite_model_exactness: `{}`
- continuum_chemistry_accuracy: `{}`
- hardware_accuracy: `{}`
- notes: `['Meets chemical accuracy threshold.']`

## Reduction Audit

- original_num_particles: `(2, 2)`
- original_num_spatial_orbitals: `6`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['ActiveSpaceTransformer']`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- selection_mode: `manual`
- selection_reason: `Manual active-space selection from user-provided electron/orbital counts; Qiskit Nature chooses the orbital window.`
- selected_active_orbitals: `[]`
- selected_active_orbitals_original: `[]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475, 'ActiveSpaceTransformer': -7.796219568777056}`
- constant_energy_correction: `-7.796219568777` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_constant_correction: `-6.804012298302` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`
- point_group_metadata: `{'enabled': True, 'status': 'available', 'group': 'Coov', 'topgroup': 'Coov', 'irrep_names': ['A1', 'E1x', 'E1y'], 'irrep_ids': [0, 2, 3], 'notes': [], 'orbital_irreps': ['A1', 'A1', 'A1', 'E1x', 'E1y', 'A1'], 'orbital_occupations': [2.0, 2.0, 0.0, 0.0, 0.0, 0.0], 'orbital_energies': [-2.3487619299812823, -0.2852707712014576, 0.07821656593872457, 0.1639413456784407, 0.1639413456784407, 0.5477083855957863], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Reduction Plan

- enabled: `True`
- mode: `manual`
- strategy: `manual_active_space`
- recommended_changes: `{'active_space': {'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': None}}`
- notes: `['Manual active-space reduction is configured.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `9`
- group_count: `4`
- estimated_shot_cost: `1024.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `4`
- uncompressed_estimated_shot_cost: `40000.0`
- cost_reduction_ratio: `0.0256`
- planner: `shadow_lr`
- shadow_bases: `[{'basis_id': 0, 'basis': 'ZZ', 'weight': 1.2468390458206748, 'allocation_fraction': 0.9087545575108669, 'allocated_shot_fraction': 0.90625}, {'basis_id': 1, 'basis': 'XZ', 'weight': 0.05606377706067145, 'allocation_fraction': 0.04086190040802262, 'allocated_shot_fraction': 0.0419921875}, {'basis_id': 2, 'basis': 'ZX', 'weight': 0.05606377706067145, 'allocation_fraction': 0.04086190040802262, 'allocated_shot_fraction': 0.041015625}, {'basis_id': 3, 'basis': 'XX', 'weight': 0.013063983580822107, 'allocation_fraction': 0.009521641673087847, 'allocated_shot_fraction': 0.0107421875}]`
- shot_allocation: `[{'basis_id': 0, 'shots': 928, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 1, 'shots': 43, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 2, 'shots': 42, 'allocation_policy': 'coefficient_l1_covariance_proxy'}, {'basis_id': 3, 'shots': 11, 'allocation_policy': 'coefficient_l1_covariance_proxy'}]`
- predicted_variance: `0.0018383475801972897`
- measurement_cost_model: `{'planner': 'shadow_lr', 'term_l1_norm': 1.37203058352284, 'selected_basis_l1_norm': 1.37203058352284, 'basis_l1_coverage_fraction': 1.0, 'basis_count': 4, 'selected_basis_count': 4, 'unselected_basis_count': 0, 'budgeted_shots': 1024, 'allocated_shots': 1024, 'max_allocated_shot_fraction': 0.90625, 'allocation_entropy': 0.29000643188852765, 'grouped_precision_baseline_shots': 40000.0, 'predicted_variance': 0.0018383475801972897, 'grouped_precision_variance_proxy': 4.7061698053050614e-05, 'variance_inflation_vs_grouped_precision_proxy': 39.0625, 'plan_digest': 'c1aa2f714eae0e4dc710965ad4baac21edec64400e2a8a07f968587a72fdb862', 'max_circuits': 16, 'strategies': ['low_rank_grouping', 'locally_biased_shadows'], 'objective': 'minimize_energy_variance'}`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.', 'Shadow-LR planner generated locally biased shadow bases and shot allocation.', 'Shadow-LR estimated shot cost uses allocated shadow shots; grouped precision cost is retained in measurement_cost_model.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.7213522500023828`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000047172` Hartree
- estimated_measurement_cost: `1024.0`
- estimated_vs_measured_cost: `None`
- reference_target: `variational_result`
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

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`7185ad62f88d64ae61a96e03527730183ad129e59649f2b06bf0e3e569e25163`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-07-08T04:20:44.716752+00:00`
- Wall time (s): `0.8242659999996249`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `b8eb62d0a9d65cf65ff2c7c445d390ba2a57965529136f2fac18859759ba8130`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `23`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/lih_shadow_lr_e_adapt.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/quantum_evidence.json`
- qcschema.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/qcschema.json`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/lih_shadow_lr_e_adapt.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=7185ad62f88d
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=4, cost=1024
- Preparing backend: statevector
- Running solver: e_adapt_vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/exact_result.json
- Computed empirical calibration: wall_time=0.721s, measured_cost=None
- Wrote integrated method evidence sidecar
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_shadow_lr_e_adapt/report.md
- Run completed
