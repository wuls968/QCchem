# QCchem Report: H2-runtime-micro-probe-v2

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-runtime-micro-probe-v2`
- basis: `sto3g`
- method: `vqe / {'kind': 'puccd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- mapping_kind: `jordan_wigner`
- num_qubits: `1`
- verification_status: `validated`
- hardware_verified: `True`
- hardware_evidence_tier: `retrieved_result`
- benchmark_absolute_error: `0.000000013086` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137283821402` Hartree
- headline_correlation_energy: `-0.020524514006` Hartree
- headline_absolute_error: `0.000000013086` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `None`
- runtime_backend: `ibm_kingston`
- runtime_job_id: `d8966his46sc73fa77fg`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'qcchem_h2_runtime_micro_real_v2', 'molecule_name': 'H2-runtime-micro-probe-v2', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `H2-runtime-micro-probe-v2 stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 1.3086143058060884e-08, 'units': 'Hartree', 'threshold': 0.2, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `retrieved_result`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `H2-runtime-micro-probe-v2 stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 1.3086143058060884e-08, 'relative_error': 7.064471283491125e-09, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 53.74384645799, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': 'ibm_kingston', 'runtime_job_id': 'd8966his46sc73fa77fg', 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': True, 'hardware_evidence_tier': 'retrieved_result', 'verification_notes': [], 'scientific_risk_notes': []}`
- provenance_timestamp: `2026-05-24T02:33:02.551796+00:00`
- runtime_job_id: `d8966his46sc73fa77fg`
- artifact_root: `/tmp/qcchem_h2_runtime_micro_real_v2`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000013086` Hartree
- threshold_hartree: `0.0016`
- distance_to_chemical_accuracy: `0.0`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Runtime Evidence

> Runtime evidence is surfaced explicitly so exported reports separate chemistry confidence from execution provenance.

- hardware_verified: `True`
- hardware_evidence_tier: `retrieved_result`
- service: `ibm_quantum_platform`
- provider: `QiskitRuntimeService`
- backend_name: `ibm_kingston`
- job_id: `d8966his46sc73fa77fg`
- verification_status: `exploratory`
- layout_strategy: `None`
- selected_layout: `[]`
- transpiled_depth: `4`
- transpiled_two_qubit_gate_count: `0`

## Verification

- verification_status: `validated`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `validated`
- Verification Notes: `[]`
- Scientific Risk Notes: `[]`

## Energy Summary

- electronic_energy: `-1.852388160483` Hartree
- nuclear_repulsion_energy: `0.715104339081` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-1.137283821402` Hartree
- hf_reference_energy: `-1.116759307396` Hartree
- solver_energy: `-1.852388160483` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.852388173570` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020524514006` Hartree
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
- solver_hamiltonian_energy: `-1.852388173570` Hartree
- electronic_energy: `-1.852388173570` Hartree
- total_energy: `-1.137283834489` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `variational_result`
- exact_electronic_energy: `-1.852388173570` Hartree
- exact_total_energy: `-1.137283834489` Hartree
- absolute_error: `0.000000013086` Hartree
- relative_error: `7.064471283491125e-09`
- statistical_error: `None`
- absolute_error_threshold: `0.2`
- relative_error_threshold: `0.2`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/tmp/qcchem_h2_runtime_micro_real_v2/quantum_evidence.json`
- sidecar_sha256: `045ef6d84981bc46d52bdf234b5854a6ac4d3d94504d1281e77431e732f6b332`
- pauli_term_count: `3`
- measurement_group_count: `2`
- energy_contribution_sum: `-1.852388160483` Hartree
- coefficient_l1_norm: `2.013074108492702`
- groups_sha256: `709c84fbcf66765924c44c58f1738014433d1afca44aa6ec2f81c6293e737634`
- counts_available: `True`
- counts_source: `statevector_sampler_from_final_state`
- counts_sha256: `85b7121ea305856b5648c28161b6c87ec5703f8a153defce3a91723d53e784d6`
- shots_per_group: `4096`
- hamiltonian_variance: `2.1205133204915683e-08`
- ground_state_overlap: `0.9999999919242597`
- dominant_configurations: `[{'bitstring': '0', 'probability': 0.9873539646813752}, {'bitstring': '1', 'probability': 0.01264603531862494}]`
- z2_check: `{'status': 'applied_z2', 'z2_symmetry_count': 3, 'z2_tapering_values': [-1, 1, -1], 'validation': {'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.8523881735695766, 'tapered_ground_energy': -1.8523881735695817, 'absolute_delta': 5.10702591327572e-15}, 'notes': ['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=5.10703e-15 Hartree.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 1, 'raw_num_qubits': 4, 'qubit_term_count': 3, 'raw_qubit_term_count': 15, 'circuit_depth': 1, 'circuit_size': 1, 'two_qubit_gate_count': 0, 'operation_counts': {'EvolvedOps': 1}, 'runtime_transpiled_depth': 4, 'runtime_transpiled_two_qubit_gate_count': 0, 'runtime_selected_layout': []}`
- error_budget: `{'ansatz_error': {'available': True, 'absolute_error_hartree': 1.3086143058060884e-08, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': True, 'verification_status': 'exploratory', 'mitigation_metadata': {'shots': 1024, 'target_precision': 0.03125, 'circuit_metadata': {}, 'resilience': {}, 'num_randomizations': 16}}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
- notes: `[]`

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
- Point-group metadata: `{'enabled': True, 'status': 'available', 'group': 'Dooh', 'topgroup': 'Dooh', 'irrep_names': ['A1g', 'A1u'], 'irrep_ids': [0, 5], 'notes': [], 'orbital_irreps': ['A1g', 'A1u'], 'orbital_occupations': [2.0, 0.0], 'orbital_energies': [-0.5785538598315291, 0.6711434919142523], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

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
- Symmetry reduction validation: `{'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.8523881735695766, 'tapered_ground_energy': -1.8523881735695817, 'absolute_delta': 5.10702591327572e-15}`
- Symmetry reduction notes: `['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=5.10703e-15 Hartree.']`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `727`
- Repetitions: `1`
- Abelian grouping: `False`
- Noise enabled: `False`
- Runtime enabled: `True`

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

- name: `hardware_ready`
- default_shots: `None`
- default_repetitions: `7`
- exact_baseline_required: `True`
- confidence_rule: `exact baseline preferred and repeated sampling mandatory`
- mitigation_posture: `symmetry-check and readout-mitigation placeholders enabled`
- runtime_ready_expected: `True`
- session_ready_expected: `True`
- batch_ready_expected: `True`
- noise_ready_expected: `True`

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000013086` Hartree
- absolute_error_kcal_mol: `8.211678747052537e-06`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- precision_target: `0.08`
- max_budgeted_shots: `1024`
- max_execution_seconds: `180.0`
- calibration_strategy: `runtime_micro_probe`
- resilience_level: `1`
- grouping_policy: `default`
- session_recommendation: `optional`
- batch_recommendation: `optional`
- low_rank_workload: `False`
- measurement_group_count: `2`
- estimated_shot_cost: `314.0`
- options: `{'backend_name': 'ibm_kingston', 'optimization_level': 1, 'layout_method': 'sabre', 'routing_method': 'sabre', 'seed_transpiler': 727, 'submit_real_job': True, 'wait_for_result': True, 'requires_action_time_confirmation': True, 'confirmation_message': 'This micro probe submits one real IBM Runtime job and may consume part of the monthly quota.', 'runtime_budget_confirmation': 'I understand IBM Runtime budget'}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'remote_execution_configured': False, 'session_mode_requested': True, 'batch_mode_requested': False, 'low_rank_policy_applied': False, 'compression_method': None}`

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
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_constant_correction: `0.715104339081` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`
- point_group_metadata: `{'enabled': True, 'status': 'available', 'group': 'Dooh', 'topgroup': 'Dooh', 'irrep_names': ['A1g', 'A1u'], 'irrep_ids': [0, 5], 'notes': [], 'orbital_irreps': ['A1g', 'A1u'], 'orbital_occupations': [2.0, 0.0], 'orbital_energies': [-0.5785538598315291, 0.6711434919142523], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Reduction Plan

- enabled: `True`
- mode: `disabled`
- strategy: `none`
- recommended_changes: `{}`
- notes: `['No reduction planning inputs were requested.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'hardware_ready'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `runtime_estimator`
- low_rank_aware: `False`
- term_count: `3`
- group_count: `2`
- estimated_shot_cost: `314.0`
- runtime_precision_target: `0.08`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `314.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.08.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.009087541999178939`
- measured_shot_usage: `None`
- precision_target: `0.08`
- achieved_error: `0.000000013086` Hartree
- estimated_measurement_cost: `314.0`
- estimated_vs_measured_cost: `None`
- reference_target: `variational_result`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Hardware Execution

- hardware_verified: `True`
- hardware_evidence_tier: `retrieved_result`
- attempted: `True`
- submitted: `True`
- succeeded: `True`
- service: `ibm_quantum_platform`
- mode: `backend`
- session_requested: `True`
- batch_requested: `False`
- backend_name: `ibm_kingston`
- provider: `QiskitRuntimeService`
- layout_strategy: `None`
- selected_layout: `[]`
- layout_score: `None`
- transpiled_depth: `4`
- transpiled_two_qubit_gate_count: `0`
- transpilation_options: `{'optimization_level': 1, 'layout_method': 'sabre', 'routing_method': 'sabre', 'approximation_degree': 1.0, 'seed_transpiler': 727}`
- job_id: `d8966his46sc73fa77fg`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `53.57426862500142`
- usage_estimation: `{'quantum_seconds': 12.384688496}`
- job_metrics: `{'caller': 'qiskit_ibm_runtime~estimator.py', 'qiskit_version': 'qiskit_ibm_runtime-0.36.1,qiskit-1.4.0*,qiskit_aer-0.16.1*,qiskit_experiments-0.8.1,qiskit_nature-0.7.2*', 'timestamps': {'created': '2026-05-24T02:32:38.833663Z', 'finished': '2026-05-24T02:32:55.599844Z', 'running': '2026-05-24T02:32:40.232221Z'}, 'bss': {'seconds': 11}, 'usage': {'quantum_seconds': 11, 'seconds': 11, 'status': 'complete'}}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'precision_target': 0.08, 'max_budgeted_shots': 1024, 'max_execution_seconds': 180.0, 'budget_strategy': 'runtime_micro_probe', 'resilience_level': 1, 'grouping_policy': 'default', 'backend_name': 'ibm_kingston', 'optimization_level': 1, 'layout_method': 'sabre', 'routing_method': 'sabre', 'seed_transpiler': 727, 'submit_real_job': True, 'wait_for_result': True, 'requires_action_time_confirmation': True, 'confirmation_message': 'This micro probe submits one real IBM Runtime job and may consume part of the monthly quota.', 'runtime_budget_confirmation': 'I understand IBM Runtime budget'}`
- returned_job_metadata: `{'evs': -1.86436913813243, 'stds': 0.007924186551404694, 'metadata': {'shots': 1024, 'target_precision': 0.03125, 'circuit_metadata': {}, 'resilience': {}, 'num_randomizations': 16}}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'runtime_package_version': '0.36.1', 'backend_name': 'ibm_kingston', 'parameter_count': 1, 'operator_qubits': 1, 'circuit_qubits': 1, 'backend_selection_strategy': 'pinned_backend', 'layout_strategy': None}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'kind': 'puccd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- initial_point_reused: `False`
- initial_point_source: `None`
- initial_point_fallback_reason: `None`
- initial_point_provenance: `{'mode': None, 'candidate_source': None, 'candidate_source_run_id': None, 'candidate_source_artifact_root': None, 'candidate_parameter_count': None, 'history_sources': [], 'history_parameter_values': [], 'target_parameter_value': None, 'current_parameter_count': 1, 'reused': False, 'fallback_reason': None, 'fallback_strategy': 'zeros', 'effective_strategy': 'zeros'}`
- parameter_count: `1`
- converged: `True`
- iterations: `22`
- evaluations: `22`
- final_objective_energy: `-1.852388160483` Hartree
- optimizer_message: `Optimization terminated successfully.`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'none'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`0c68621f7ed95dc12a831da68f2cf64c633e30d000afab6f1e2b6e032cf439da`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-24T02:33:02.551796+00:00`
- Wall time (s): `53.74384645799`
- Git commit: `9a375331e05742322db6a3e8f9baed5c9c8aea56`
- Git commit short: `9a375331e057`
- Git branch: `HEAD`
- Git describe: `9a37533-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `.`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 14, 'untracked': 9}`
- Workspace fingerprint: `52499c35abb1b9bbbd0d75eea345c6c3734768c68143fc3d7d5586b96262d726`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `727`
- Source config: `configs/h2_runtime_micro_probe_v2.yaml`

## Artifacts

- result.json: `/tmp/qcchem_h2_runtime_micro_real_v2/result.json`
- exact_result.json: `/tmp/qcchem_h2_runtime_micro_real_v2/exact_result.json`
- report.md: `/tmp/qcchem_h2_runtime_micro_real_v2/report.md`
- resolved_config.yaml: `/tmp/qcchem_h2_runtime_micro_real_v2/resolved_config.yaml`
- run.log: `/tmp/qcchem_h2_runtime_micro_real_v2/run.log`
- calibration.json: `/tmp/qcchem_h2_runtime_micro_real_v2/calibration.json`
- calibration_report.md: `/tmp/qcchem_h2_runtime_micro_real_v2/calibration_report.md`
- runtime_submission.json: `/tmp/qcchem_h2_runtime_micro_real_v2/runtime_submission.json`
- quantum_evidence.json: `/tmp/qcchem_h2_runtime_micro_real_v2/quantum_evidence.json`
- qcschema.json: `/tmp/qcchem_h2_runtime_micro_real_v2/qcschema.json`
- result.h5: `/tmp/qcchem_h2_runtime_micro_real_v2/result.h5`

## Log Summary

- Loading config from configs/h2_runtime_micro_probe_v2.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=0c68621f7ed9
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=2, cost=314
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /tmp/qcchem_h2_runtime_micro_real_v2/exact_result.json
- Computed empirical calibration: wall_time=0.009s, measured_cost=None
- Persisted runtime submission sidecar after job submit: d8966his46sc73fa77fg
- Runtime submission attempt recorded: submitted
- Writing JSON result to /tmp/qcchem_h2_runtime_micro_real_v2/result.json
- Writing Markdown report to /tmp/qcchem_h2_runtime_micro_real_v2/report.md
- Run completed
