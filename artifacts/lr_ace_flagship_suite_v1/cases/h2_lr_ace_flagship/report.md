# QCchem Report: H2-LR-ACE-flagship

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-LR-ACE-flagship`
- basis: `sto3g`
- method: `lr_ace / {'kind': 'lr_ace', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1, 'lr_ace': {'algorithm_name': 'LR-ACE', 'low_rank_aware': True, 'selection_rule': 'adaptive_score_weight_locality_reference_mixing', 'source_terms': [{'pauli': 'XX', 'weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0}], 'candidate_generators': [{'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 0}, {'pauli': 'XY', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 1}], 'selected_generators': [{'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 0}], 'selected_factor_count': 1, 'method_role': 'flagship', 'profile': 'compact', 'validation_mode': 'trust_first', 'ansatz_parameter_count': 1, 'optimized_parameters': [-0.11269296875], 'local_accuracy_gate': {'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 1.3086143280105489e-08}, 'validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 1.3086143280105489e-08, 'compression_enabled': False, 'compressed_solver_energy': -1.852388160483439, 'uncompressed_solver_energy': None, 'uncompressed_exact_solver_energy': None, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `validated`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000013086` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137283821402` Hartree
- headline_correlation_energy: `-0.020524514006` Hartree
- headline_absolute_error: `0.000000013086` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_lr_ace_flagship', 'molecule_name': 'H2-LR-ACE-flagship', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'parity_two_qubit_reduction', 'field_model_kind': None}`
- primary_scientific_claim: `H2-LR-ACE-flagship stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 1.3086143280105489e-08, 'units': 'Hartree', 'threshold': 0.0016, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Claim

- primary_scientific_claim: `H2-LR-ACE-flagship stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 1.3086143280105489e-08, 'relative_error': 7.064471403360494e-09, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.13002020795829594, 'shots': None, 'measurement_strategy': 'low_rank_lr_ace_local', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lr_ace local exact-baseline gate'], 'scientific_risk_notes': ['LR-ACE is the QCchem flagship low-rank-factor-informed solver path.', 'Dominant low-rank factor selection remains trust-gated by exact-reference artifacts.'], 'lr_ace_trust_label': 'passed_exact_reference', 'lr_ace_validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 1.3086143280105489e-08, 'compression_enabled': False, 'compressed_solver_energy': -1.852388160483439, 'uncompressed_solver_energy': None, 'uncompressed_exact_solver_energy': None, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}`
- provenance_timestamp: `2026-05-17T10:49:32.987689+00:00`
- runtime_job_id: `None`
- artifact_root: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship`

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
- relative_error: `7.064471403360494e-09`
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
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.7151043390810812}`
- Electronic constant correction: `0.000000000000` Hartree
- Point-group metadata: `{'enabled': True, 'status': 'available', 'group': 'Dooh', 'topgroup': 'Dooh', 'irrep_names': ['A1g', 'A1u'], 'irrep_ids': [0, 5], 'notes': [], 'orbital_irreps': ['A1g', 'A1u'], 'orbital_occupations': [2.0, 0.0], 'orbital_energies': [-0.5785538598315291, 0.6711434919142523], 'requested_mode': 'auto', 'requested_subgroup': 'auto', 'reduction_mode': 'audit', 'active_irreps': [], 'remove_irreps': []}`

## Mapping

- Mapping kind: `parity_two_qubit_reduction`
- Qubit count: `2`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `5`
- Raw qubit count: `2`
- Raw qubit Hamiltonian terms: `5`
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
- Seed: `1729`
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
- absolute_error_hartree: `0.000000013086` Hartree
- absolute_error_kcal_mol: `8.211678886387629e-06`
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
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `low_rank_lr_ace_local`
- grouping_policy: `low_rank_factor_aware`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `5`
- group_count: `2`
- estimated_shot_cost: `20000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `20000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'low_rank_lr_ace_local'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.009407709003426135`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000013086` Hartree
- estimated_measurement_cost: `20000.0`
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
- optimizer: `{'kind': 'COBYLA', 'maxiter': 220, 'tol': None}`
- ansatz: `{'kind': 'lr_ace', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1, 'lr_ace': {'algorithm_name': 'LR-ACE', 'low_rank_aware': True, 'selection_rule': 'adaptive_score_weight_locality_reference_mixing', 'source_terms': [{'pauli': 'XX', 'weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0}], 'candidate_generators': [{'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 0}, {'pauli': 'XY', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'candidate_index': 1}], 'selected_generators': [{'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 0}], 'selected_factor_count': 1, 'method_role': 'flagship', 'profile': 'compact', 'validation_mode': 'trust_first', 'ansatz_parameter_count': 1, 'optimized_parameters': [-0.11269296875], 'local_accuracy_gate': {'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 1.3086143280105489e-08}, 'validation_gate': {'trust_label': 'passed_exact_reference', 'verification_status': 'validated', 'validated': True, 'target_error_hartree': 0.0016, 'exact_available': True, 'local_exact_error_hartree': 1.3086143280105489e-08, 'compression_enabled': False, 'compressed_solver_energy': -1.852388160483439, 'uncompressed_solver_energy': None, 'uncompressed_exact_solver_energy': None, 'runtime_attempted': False, 'runtime_accuracy_met': None, 'blocking_reason': None}}}`
- initial_point_strategy: `zeros`
- initial_point_reused: `False`
- initial_point_source: `None`
- initial_point_fallback_reason: `None`
- initial_point_provenance: `{'requested_strategy': 'zeros', 'candidate_source': None, 'candidate_mode': None, 'candidate_parameter_count': None, 'candidate_source_run_id': None, 'candidate_source_artifact_root': None, 'history_sources': [], 'history_parameter_values': [], 'target_parameter_value': None, 'reused': False, 'fallback_reason': None, 'fallback_strategy': 'zeros', 'effective_strategy': 'zeros'}`
- parameter_count: `1`
- converged: `True`
- iterations: `22`
- evaluations: `22`
- final_objective_energy: `-1.852388160483` Hartree
- optimizer_message: `Optimization terminated successfully.`

## LR-ACE Exploratory Algorithm

- algorithm_name: `LR-ACE`
- low_rank_method: `None`
- factor_rank: `None`
- selected_factor_count: `1`
- local_accuracy_gate: `{'passed': True, 'threshold_hartree': 0.0016, 'absolute_error_hartree': 1.3086143280105489e-08}`
- selected_generators: `[{'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.18121046201519675, 'coefficient_real': 0.18121046201519675, 'coefficient_imag': 0.0, 'adaptive_score': 0.18121046201519675, 'locality': 2, 'reference_mixing_relevance': 1.0, 'batch_index': 0}]`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`0c68621f7ed95dc12a831da68f2cf64c633e30d000afab6f1e2b6e032cf439da`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-17T10:49:32.987689+00:00`
- Wall time (s): `0.13002020795829594`
- Git commit: `a7c0893f8c2b2a07e7c911c49536761ba5ebb250`
- Git commit short: `a7c0893f8c2b`
- Git branch: `codex/lr-ace-flagship`
- Git describe: `a7c0893-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `.`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 22, 'untracked': 6}`
- Workspace fingerprint: `c0363161a73053013d5eda305c18cee4b4514c05dcdb7120174d27439e834048`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `1729`
- Source config: `configs/lr_ace/h2_flagship.yaml`

## Artifacts

- result.json: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/result.json`
- exact_result.json: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/exact_result.json`
- report.md: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/report.md`
- resolved_config.yaml: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/resolved_config.yaml`
- run.log: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/run.log`
- calibration.json: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/calibration.json`
- calibration_report.md: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/calibration_report.md`
- runtime_submission.json: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/runtime_submission.json`
- qcschema.json: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/qcschema.json`
- result.h5: `artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/result.h5`

## Log Summary

- Loading config from configs/lr_ace/h2_flagship.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=0c68621f7ed9
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Z2 tapering skipped for LR-ACE in auto mode because its trust-first provenance currently targets untapered parity-reduced workloads.
- Prepared measurement plan: groups=2, cost=20000
- Preparing backend: statevector
- Running solver: lr_ace
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/exact_result.json
- Computed empirical calibration: wall_time=0.009s, measured_cost=None
- Writing JSON result to artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/result.json
- Writing Markdown report to artifacts/lr_ace_flagship_suite_v1/cases/h2_lr_ace_flagship/report.md
- Run completed
