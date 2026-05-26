# QCchem Report: LiH-active-LR-ACE-flagship

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `LiH-active-LR-ACE-flagship`
- basis: `sto3g`
- method: `lr_ace / {'kind': 'lr_ace', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 5, 'lr_ace': {'algorithm_name': 'LR-ACE', 'low_rank_aware': True, 'selection_rule': 'adaptive_score_weight_locality_reference_mixing', 'source_terms': [{'pauli': 'XI', 'weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0}, {'pauli': 'IX', 'weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0}, {'pauli': 'XZ', 'weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0}, {'pauli': 'ZX', 'weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0}, {'pauli': 'XX', 'weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0}], 'candidate_generators': [{'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0, 'adaptive_score': 0.05606378977502419, 'locality': 1, 'reference_mixing_relevance': 1.0, 'candidate_index': 0}, {'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0, 'adaptive_score': 0.056063789775024186, 'locality': 1, 'reference_mixing_relevance': 1.0, 'candidate_index': 1}, {'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'candidate_index': 2}, {'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'candidate_index': 3}, {'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 4}, {'pauli': 'XY', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 5}], 'selected_generators': [{'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0, 'adaptive_score': 0.05606378977502419, 'locality': 1, 'reference_mixing_relevance': 1.0, 'batch_index': 0}, {'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0, 'adaptive_score': 0.056063789775024186, 'locality': 1, 'reference_mixing_relevance': 1.0, 'batch_index': 1}, {'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'batch_index': 2}, {'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'batch_index': 3}, {'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 4}], 'selected_factor_count': 5, 'method_role': 'flagship', 'profile': 'compact', 'validation_mode': 'trust_first', 'ansatz_parameter_count': 5, 'optimized_parameters': [-0.012450141865208248, -0.009746716843774612, -0.019333366620825243, 0.003094599663255523, -0.019896843037543153], 'local_accuracy_gate': {'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 9.83466863502258e-10}, 'validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 9.83466863502258e-10, 'compression_enabled': False, 'compressed_solver_energy': -1.058116534153073, 'uncompressed_solver_energy': None, 'uncompressed_exact_solver_energy': None, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `validated`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000983` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-7.862128832455` Hartree
- headline_correlation_energy: `-0.000264062646` Hartree
- headline_absolute_error: `0.000000000983` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2]}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'lih_active_lr_ace_flagship', 'molecule_name': 'LiH-active-LR-ACE-flagship', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'parity_two_qubit_reduction', 'field_model_kind': None}`
- primary_scientific_claim: `LiH-active-LR-ACE-flagship stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 9.83466863502258e-10, 'units': 'Hartree', 'threshold': 0.0016, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `LiH-active-LR-ACE-flagship stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `manual` / transformers=`['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 9.83466863502258e-10, 'relative_error': 9.294504252079863e-10, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.17597612499957904, 'shots': None, 'measurement_strategy': 'low_rank_lr_ace_local', 'measurement_group_count': 4, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lr_ace local exact-baseline gate'], 'scientific_risk_notes': ['LR-ACE is the QCchem flagship low-rank-factor-informed solver path.', 'Dominant low-rank factor selection remains trust-gated by exact-reference artifacts.'], 'lr_ace_trust_label': 'passed_exact_reference', 'lr_ace_validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 9.83466863502258e-10, 'compression_enabled': False, 'compressed_solver_energy': -1.058116534153073, 'uncompressed_solver_energy': None, 'uncompressed_exact_solver_energy': None, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}`
- provenance_timestamp: `2026-05-17T10:49:33.255100+00:00`
- runtime_job_id: `None`
- artifact_root: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000983` Hartree
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
- Capability Tier: `flagship`
- Verification Notes: `['validation_scope=lr_ace local exact-baseline gate']`
- Scientific Risk Notes: `['LR-ACE is the QCchem flagship low-rank-factor-informed solver path.', 'Dominant low-rank factor selection remains trust-gated by exact-reference artifacts.']`

## Energy Summary

- electronic_energy: `-8.854336102930` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-7.862128832455` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058116534153` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000264062646` Hartree
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
- absolute_error: `0.000000000983` Hartree
- relative_error: `9.294504252079863e-10`
- statistical_error: `None`
- absolute_error_threshold: `0.0016`
- relative_error_threshold: `0.0016`
- within_uncertainty: `None`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2]}`
- Transformers applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475, 'FreezeCoreTransformer': -7.796219568777056, 'ActiveSpaceTransformer': 0.0}`
- Electronic constant correction: `-7.796219568777` Hartree
- Point-group metadata: `{'enabled': True, 'status': 'available', 'group': 'Coov', 'topgroup': 'Coov', 'irrep_names': ['A1', 'E1x', 'E1y'], 'irrep_ids': [0, 2, 3], 'notes': [], 'orbital_irreps': ['A1', 'A1', 'A1', 'E1x', 'E1y', 'A1'], 'orbital_occupations': [2.0, 2.0, 0.0, 0.0, 0.0, 0.0], 'orbital_energies': [-2.3487619299812823, -0.2852707712014576, 0.07821656593872457, 0.1639413456784407, 0.1639413456784407, 0.5477083855957863], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Mapping

- Mapping kind: `parity_two_qubit_reduction`
- Qubit count: `2`
- Fermionic Hamiltonian terms: `72`
- Qubit Hamiltonian terms: `9`
- Raw qubit count: `2`
- Raw qubit Hamiltonian terms: `9`
- Symmetry tapered qubits: `0`
- Z2 symmetry count: `0`
- Z2 tapering values: `None`
- Symmetry reduction status: `disabled`
- Symmetry reduction validation: `{}`
- Symmetry reduction notes: `['Z2 tapering disabled by mapping.symmetry_reduction.z2.', 'Z2 tapering skipped for LR-ACE in auto mode because its trust-first provenance currently targets untapered parity-reduced workloads.']`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `73`
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
- absolute_error_hartree: `0.000000000983` Hartree
- absolute_error_kcal_mol: `6.171346348776385e-07`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Reduction Audit

- original_num_particles: `(2, 2)`
- original_num_spatial_orbitals: `6`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2]}`
- selection_mode: `manual`
- selection_reason: `Manual active-space selection from user-provided orbital list and electron counts.`
- selected_active_orbitals: `[0, 1]`
- selected_active_orbitals_original: `[1, 2]`
- frozen_core_orbitals: `[0]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475, 'FreezeCoreTransformer': -7.796219568777056, 'ActiveSpaceTransformer': 0.0}`
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
- recommended_changes: `{'freeze_core': True, 'active_space': {'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [1, 2]}}`
- notes: `['Freeze-core reduction is enabled.', 'Manual active-space reduction is configured.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `low_rank_lr_ace_local`
- grouping_policy: `low_rank_factor_aware`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `9`
- group_count: `4`
- estimated_shot_cost: `40000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `4`
- uncompressed_estimated_shot_cost: `40000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'low_rank_lr_ace_local'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.0392963329795748`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000983` Hartree
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
- solver_kind: `lr_ace`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 320, 'tol': None}`
- ansatz: `{'kind': 'lr_ace', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 5, 'lr_ace': {'algorithm_name': 'LR-ACE', 'low_rank_aware': True, 'selection_rule': 'adaptive_score_weight_locality_reference_mixing', 'source_terms': [{'pauli': 'XI', 'weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0}, {'pauli': 'IX', 'weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0}, {'pauli': 'XZ', 'weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0}, {'pauli': 'ZX', 'weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0}, {'pauli': 'XX', 'weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0}], 'candidate_generators': [{'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0, 'adaptive_score': 0.05606378977502419, 'locality': 1, 'reference_mixing_relevance': 1.0, 'candidate_index': 0}, {'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0, 'adaptive_score': 0.056063789775024186, 'locality': 1, 'reference_mixing_relevance': 1.0, 'candidate_index': 1}, {'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'candidate_index': 2}, {'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'candidate_index': 3}, {'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 4}, {'pauli': 'XY', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 5}], 'selected_generators': [{'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0, 'adaptive_score': 0.05606378977502419, 'locality': 1, 'reference_mixing_relevance': 1.0, 'batch_index': 0}, {'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0, 'adaptive_score': 0.056063789775024186, 'locality': 1, 'reference_mixing_relevance': 1.0, 'batch_index': 1}, {'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'batch_index': 2}, {'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'batch_index': 3}, {'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 4}], 'selected_factor_count': 5, 'method_role': 'flagship', 'profile': 'compact', 'validation_mode': 'trust_first', 'ansatz_parameter_count': 5, 'optimized_parameters': [-0.012450141865208248, -0.009746716843774612, -0.019333366620825243, 0.003094599663255523, -0.019896843037543153], 'local_accuracy_gate': {'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 9.83466863502258e-10}, 'validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 9.83466863502258e-10, 'compression_enabled': False, 'compressed_solver_energy': -1.058116534153073, 'uncompressed_solver_energy': None, 'uncompressed_exact_solver_energy': None, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}}`
- initial_point_strategy: `zeros`
- initial_point_reused: `False`
- initial_point_source: `None`
- initial_point_fallback_reason: `None`
- initial_point_provenance: `{'requested_strategy': 'zeros', 'candidate_source': None, 'candidate_mode': None, 'candidate_parameter_count': None, 'candidate_source_run_id': None, 'candidate_source_artifact_root': None, 'history_sources': [], 'history_parameter_values': [], 'target_parameter_value': None, 'reused': False, 'fallback_reason': None, 'fallback_strategy': 'zeros', 'effective_strategy': 'zeros'}`
- parameter_count: `5`
- converged: `True`
- iterations: `59`
- evaluations: `59`
- final_objective_energy: `-1.058116534153` Hartree
- optimizer_message: `Optimization terminated successfully.`

## LR-ACE Exploratory Algorithm

- algorithm_name: `LR-ACE`
- low_rank_method: `None`
- factor_rank: `None`
- selected_factor_count: `5`
- local_accuracy_gate: `{'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 9.83466863502258e-10}`
- selected_generators: `[{'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.028031894887512097, 'coefficient_real': 0.028031894887512097, 'coefficient_imag': 0.0, 'adaptive_score': 0.05606378977502419, 'locality': 1, 'reference_mixing_relevance': 1.0, 'batch_index': 0}, {'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.028031894887512093, 'coefficient_real': 0.028031894887512093, 'coefficient_imag': 0.0, 'adaptive_score': 0.056063789775024186, 'locality': 1, 'reference_mixing_relevance': 1.0, 'batch_index': 1}, {'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173159352, 'coefficient_real': 0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'batch_index': 2}, {'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173159352, 'coefficient_real': -0.028031882173159352, 'coefficient_imag': 0.0, 'adaptive_score': 0.021023911629869513, 'locality': 2, 'reference_mixing_relevance': 0.5, 'batch_index': 3}, {'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.013063983580822107, 'coefficient_real': 0.013063983580822107, 'coefficient_imag': 0.0, 'adaptive_score': 0.013063983580822107, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 4}]`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`a2c4dddce5b1554a66112e9260ab3281774757b24fa14cf4569fbfc78d90c405`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-17T10:49:33.255100+00:00`
- Wall time (s): `0.17597612499957904`
- Git commit: `a7c0893f8c2b2a07e7c911c49536761ba5ebb250`
- Git commit short: `a7c0893f8c2b`
- Git branch: `codex/lr-ace-flagship`
- Git describe: `a7c0893-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `.`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 22, 'untracked': 6}`
- Workspace fingerprint: `c82bd905bf17c5bcf31500bc415480761726ca90a5563d9dc7ba01eb44e8dead`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `73`
- Source config: `configs/lr_ace/lih_active_flagship.yaml`

## Artifacts

- result.json: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/result.json`
- exact_result.json: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/exact_result.json`
- report.md: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/report.md`
- resolved_config.yaml: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/resolved_config.yaml`
- run.log: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/run.log`
- calibration.json: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/calibration.json`
- calibration_report.md: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/calibration_report.md`
- runtime_submission.json: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/runtime_submission.json`
- qcschema.json: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/qcschema.json`
- result.h5: `artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/result.h5`

## Log Summary

- Loading config from configs/lr_ace/lih_active_flagship.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=a2c4dddce5b1
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Z2 tapering skipped for LR-ACE in auto mode because its trust-first provenance currently targets untapered parity-reduced workloads.
- Prepared measurement plan: groups=4, cost=40000
- Preparing backend: statevector
- Running solver: lr_ace
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/exact_result.json
- Computed empirical calibration: wall_time=0.039s, measured_cost=None
- Writing JSON result to artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/result.json
- Writing Markdown report to artifacts/lr_ace_flagship_suite_v1/cases/lih_active_lr_ace_flagship/report.md
- Run completed
