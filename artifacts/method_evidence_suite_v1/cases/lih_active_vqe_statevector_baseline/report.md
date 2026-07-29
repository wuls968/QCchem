# QCchem Report: LiH-active-vqe

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `LiH-active-vqe`
- basis: `sto3g`
- method: `vqe / {'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- mapping_kind: `jordan_wigner`
- num_qubits: `2`
- verification_status: `validated`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000004028` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-7.862128829411` Hartree
- headline_correlation_energy: `-0.000264059602` Hartree
- headline_absolute_error: `0.000000004028` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'lih_active_vqe_statevector_baseline', 'molecule_name': 'LiH-active-vqe', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `LiH-active-vqe stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 4.0279586333014095e-09, 'units': 'Hartree', 'threshold': 0.025, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `LiH-active-vqe stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `manual` / transformers=`['ActiveSpaceTransformer']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 4.0279586333014095e-09, 'relative_error': 3.8067249679465956e-09, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.19961145900015254, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 4, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': [], 'scientific_risk_notes': [], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:43.892443+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000004028` Hartree
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

- electronic_energy: `-8.854336099886` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-7.862128829411` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058116531109` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000264059602` Hartree
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
- absolute_error: `0.000000004028` Hartree
- relative_error: `3.8067249679465956e-09`
- statistical_error: `None`
- absolute_error_threshold: `0.025`
- relative_error_threshold: `0.025`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/quantum_evidence.json`
- sidecar_sha256: `7a0b4534b4f7da923547de6b35ae1cdf52340d86e414710c391a36b6d76027c0`
- pauli_terms_available: `True`
- pauli_unavailable_reason: `None`
- pauli_term_count: `9`
- measurement_group_count: `4`
- energy_contribution_sum: `-1.058116531109` Hartree
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
- counts_sha256: `9987cb7ebc3bed36bb3f7779e78c72919739fc5be704768a16dc6d7728f884f4`
- shots_per_group: `4096`
- hamiltonian_variance: `2.3485164923897628e-09`
- ground_state_overlap: `0.9999999897679654`
- dominant_configurations: `[{'bitstring': '00', 'probability': 0.9994975881329758}, {'bitstring': '11', 'probability': 0.00041075852785003197}, {'bitstring': '10', 'probability': 4.633306348170417e-05}, {'bitstring': '01', 'probability': 4.5320275692540574e-05}]`
- z2_check: `{'status': 'applied_z2', 'z2_symmetry_count': 2, 'z2_tapering_values': [-1, -1], 'validation': {'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.0581165351365382, 'tapered_ground_energy': -1.0581165351365405, 'absolute_delta': 2.220446049250313e-15}, 'notes': ['Applied Z2 tapering in sector [-1, -1]; removed 2 qubits.', 'Exact-spectrum validation passed with delta=2.22045e-15 Hartree.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 2, 'raw_num_qubits': 4, 'qubit_term_count': 9, 'raw_qubit_term_count': 27, 'circuit_depth': 17, 'circuit_size': 24, 'two_qubit_gate_count': 4, 'operation_counts': {'u': 12, 'p': 8, 'cx': 4}}`
- error_budget: `{'ansatz_error': {'available': True, 'absolute_error_hartree': 4.0279586333014095e-09, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
- eigen_residual_norm: `None`
- relative_eigen_residual: `None`
- ground_state_gap: `None`
- lowest_eigenvalues: `None`
- sparse_exact_validation: `{}`
- lattice_qed_observables: `{}`
- notes: `[]`

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
- Symmetry reduction validation: `{'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.0581165351365382, 'tapered_ground_energy': -1.0581165351365405, 'absolute_delta': 2.220446049250313e-15}`
- Symmetry reduction notes: `['Applied Z2 tapering in sector [-1, -1]; removed 2 qubits.', 'Exact-spectrum validation passed with delta=2.22045e-15 Hartree.']`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `211`
- Repetitions: `1`
- Abelian grouping: `False`
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
- absolute_error_hartree: `0.000000004028` Hartree
- absolute_error_kcal_mol: `2.527582063941633e-06`
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
- estimated_shot_cost: `40000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `4`
- uncompressed_estimated_shot_cost: `40000.0`
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
- measured_wall_time_seconds: `0.10998954200113076`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000004028` Hartree
- estimated_measurement_cost: `40000.0`
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

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 120, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- initial_point_reused: `False`
- initial_point_source: `None`
- initial_point_fallback_reason: `None`
- initial_point_provenance: `{'mode': None, 'candidate_source': None, 'candidate_source_run_id': None, 'candidate_source_artifact_root': None, 'candidate_parameter_count': None, 'history_sources': [], 'history_parameter_values': [], 'target_parameter_value': None, 'current_parameter_count': 3, 'reused': False, 'fallback_reason': None, 'fallback_strategy': 'zeros', 'effective_strategy': 'zeros'}`
- parameter_count: `3`
- converged: `True`
- iterations: `48`
- evaluations: `48`
- final_objective_energy: `-1.058116531109` Hartree
- optimizer_message: `Optimization terminated successfully.`

## Mitigation

- symmetry_check: `{'requested': True, 'effective_requested': False, 'performed': False, 'status': 'no_checks_requested', 'strategy': 'parity_placeholder', 'requested_checks': {'particle_number': False, 'spin_parity': False, 'z2_sector': False}, 'postselection_rate': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'none', 'calibration_shots': 0, 'calibration_digest': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
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
- Timestamp: `2026-07-08T04:20:43.892443+00:00`
- Wall time (s): `0.19961145900015254`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `2772c0a8ca17071924168066462d720de823cb51a61e9f6e1bca67521c4ee759`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `211`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/lih_active_vqe.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/quantum_evidence.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/lih_active_vqe.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=7185ad62f88d
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=4, cost=40000
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/exact_result.json
- Computed empirical calibration: wall_time=0.110s, measured_cost=None
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/lih_active_vqe_statevector_baseline/report.md
- Run completed
