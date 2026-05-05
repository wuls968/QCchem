# QCchem Report: LiH-active-LR-ACE

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `LiH-active-LR-ACE`
- basis: `sto3g`
- method: `lr_ace / {'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'lr_ace', 'lr_ace': {'algorithm_name': 'LR-ACE', 'ansatz_parameter_count': 5, 'compression_reconstruction_error': 1.2417518519112547e-16, 'compression_threshold': 1e-10, 'factor_rank': 3, 'local_accuracy_gate': {'absolute_error_hartree': 6.617706382883171e-10, 'passed': True, 'threshold_hartree': 0.0016}, 'low_rank_aware': True, 'low_rank_method': 'modified_cholesky', 'optimized_parameters': [-0.002517398678155159, 0.0038946988975990223, -0.0030990423664654584, -0.004161664875235105, -0.02021061653252367], 'post_term_count': 9, 'pre_term_count': 9, 'selected_factor_count': 5, 'selected_generators': [{'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.028031882173134164, 'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': -0.028031882173134164, 'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': 0.01306398358080487, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.01306398358080487}], 'selection_rule': 'dominant_non_diagonal_hamiltonian_factors_with_real_mixing_companions', 'source_terms': [{'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'IX', 'weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'XI', 'weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.028031882173134164, 'pauli': 'XZ', 'weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': -0.028031882173134164, 'pauli': 'ZX', 'weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': 0.01306398358080487, 'pauli': 'XX', 'weight': 0.01306398358080487}]}, 'reps': 5, 'rotation_blocks': ['ry', 'rz']}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000411` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-7.862128832777` Hartree
- headline_correlation_energy: `-0.000264062968` Hartree
- headline_absolute_error: `0.000000000411` Hartree
- comparison_target: `compressed_vs_uncompressed`
- active_space_metadata: `{'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2], 'num_electrons': 2, 'num_spatial_orbitals': 2}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'lih_active_lr_ace', 'backend_kind': 'statevector', 'basis': 'sto3g', 'mapping_kind': 'parity_two_qubit_reduction', 'molecule_name': 'LiH-active-LR-ACE'}`
- primary_scientific_claim: `LiH-active-LR-ACE stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_scope': 'single_run', 'baseline_source': 'exact_diagonalization', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'comparison_target': 'compressed_vs_uncompressed', 'metric_kind': 'absolute_error_hartree', 'threshold': 0.0016, 'units': 'Hartree', 'value': 4.106137652115649e-10}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `LiH-active-LR-ACE stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `manual` / transformers=`['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- compression: `modified_cholesky` / status=`validated`
- correction: `None` / delta=`None`
- comparison_evidence: `{'absolute_error': 4.106137652115649e-10, 'baseline_strength': 'strong', 'comparison_target': 'compressed_vs_uncompressed', 'compressed_vs_uncompressed': {'absolute_error': 4.106137652115649e-10, 'available': True, 'compressed_solve_wall_time_seconds': 1.993790042004548, 'compressed_solver_energy': -1.0581165344747692, 'compressed_total_energy': -7.86212883277682, 'method': 'modified_cholesky', 'post_term_count': 9, 'pre_term_count': 9, 'rank': 3, 'relative_error': 5.222679174642646e-11, 'threshold': 1e-10, 'uncompressed_solve_wall_time_seconds': 1.366409084002953, 'uncompressed_solver_energy': -1.0581165340641554, 'uncompressed_total_energy': -7.862128832366206}, 'relative_error': 5.222679174642646e-11, 'statistical_error': None}`

## Proof

- execution_evidence: `{'measured_shot_usage': None, 'measurement_group_count': 4, 'measurement_strategy': 'low_rank_lr_ace_local', 'runtime_backend': None, 'runtime_job_id': None, 'shots': None, 'wall_time_seconds': 3.813802000018768}`
- trust_judgment: `{'hardware_evidence_tier': None, 'hardware_verified': False, 'module_origin': 'exploratory', 'scientific_risk_notes': ['LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.', 'Dominant low-rank factor selection is heuristic and not yet publication-validated.'], 'verification_notes': ['validation_scope=lr_ace local exact-baseline gate'], 'verification_status': 'exploratory'}`
- provenance_timestamp: `2026-05-02T06:59:42.526989+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000662` Hartree
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
- Verification Notes: `['validation_scope=lr_ace local exact-baseline gate']`
- Scientific Risk Notes: `['LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.', 'Dominant low-rank factor selection is heuristic and not yet publication-validated.']`

## Energy Summary

- electronic_energy: `-8.854336103252` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.862128832777` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058116534475` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000264062968` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `-7.796219568777` Hartree
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
- solver_hamiltonian_energy: `-1.058116535137` Hartree
- electronic_energy: `-8.854336103914` Hartree
- total_energy: `-7.862128833439` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `compressed_vs_uncompressed`
- exact_electronic_energy: `-8.854336103914` Hartree
- exact_total_energy: `-7.862128833439` Hartree
- absolute_error: `0.000000000411` Hartree
- relative_error: `5.222679174642646e-11`
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
- Active space metadata: `{'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2], 'num_electrons': 2, 'num_spatial_orbitals': 2}`
- Transformers applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- Hamiltonian constants: `{'ActiveSpaceTransformer': 0.0, 'FreezeCoreTransformer': -7.796219568777051, 'nuclear_repulsion_energy': 0.992207270475}`
- Electronic constant correction: `-7.796219568777` Hartree

## Mapping

- Mapping kind: `parity_two_qubit_reduction`
- Qubit count: `2`
- Fermionic Hamiltonian terms: `72`
- Qubit Hamiltonian terms: `9`

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
- absolute_error_hartree: `0.000000000662` Hartree
- absolute_error_kcal_mol: `4.1526706647075956e-07`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Compressed vs Uncompressed

- available: `True`
- method: `modified_cholesky`
- rank: `3`
- threshold: `1e-10`
- pre_term_count: `9`
- post_term_count: `9`
- compressed_solver_energy: `-1.058116534475` Hartree
- uncompressed_solver_energy: `-1.058116534064` Hartree
- compressed_total_energy: `-7.862128832777` Hartree
- uncompressed_total_energy: `-7.862128832366` Hartree
- absolute_error: `0.000000000411` Hartree
- relative_error: `5.222679174642646e-11`
- compressed_solve_wall_time_seconds: `1.993790042004548`
- uncompressed_solve_wall_time_seconds: `1.366409084002953`

## Reduction Audit

- original_num_particles: `(2, 2)`
- original_num_spatial_orbitals: `6`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- active_space_metadata: `{'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2], 'num_electrons': 2, 'num_spatial_orbitals': 2}`
- selection_mode: `manual`
- selection_reason: `Manual active-space selection from user-provided orbital list and electron counts.`
- selected_active_orbitals: `[0, 1]`
- selected_active_orbitals_original: `[1, 2]`
- frozen_core_orbitals: `[0]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'ActiveSpaceTransformer': 0.0, 'FreezeCoreTransformer': -7.796219568777051, 'nuclear_repulsion_energy': 0.992207270475}`
- constant_energy_correction: `-7.796219568777` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `-6.804012298302` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Reduction Plan

- enabled: `True`
- mode: `manual`
- strategy: `manual_active_space`
- recommended_changes: `{'active_space': {'active_orbitals': [1, 2], 'num_electrons': 2, 'num_spatial_orbitals': 2}, 'freeze_core': True}`
- notes: `['Freeze-core reduction is enabled.', 'Manual active-space reduction is configured.']`
- provenance: `{'policy_name': 'benchmark', 'source': 'qcchem.chem.reduction_planner'}`

## Compression Audit

- enabled: `True`
- method: `modified_cholesky`
- rank: `3`
- threshold: `1e-10`
- max_rank: `6`
- apply_to_solver: `True`
- execution_enabled: `True`
- original_num_qubits: `2`
- compressed_num_qubits: `2`
- original_fermionic_term_count: `72`
- original_qubit_term_count: `9`
- compressed_term_count_estimate: `9`
- pre_term_count: `9`
- post_term_count: `9`
- primary_rank: `3`
- secondary_rank: `None`
- reconstruction_error_frobenius: `1.2417518519112547e-16`
- reconstruction_error: `1.2417518519112547e-16`
- verification_status: `validated`
- notes: `['Modified-Cholesky compression reconstructed the two-electron pair matrix for execution.']`

## Measurement Plan

- strategy: `low_rank_lr_ace_local`
- grouping_policy: `low_rank_factor_aware`
- execution_mode: `estimator`
- low_rank_aware: `True`
- term_count: `9`
- group_count: `4`
- estimated_shot_cost: `40000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `4`
- uncompressed_estimated_shot_cost: `40000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'low_rank_lr_ace_local'.", 'Per-group shot estimate derived from precision target 0.01.', 'Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `1.993790042004548`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000411` Hartree
- estimated_measurement_cost: `40000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `compressed_vs_uncompressed`
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
- ansatz: `{'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'lr_ace', 'lr_ace': {'algorithm_name': 'LR-ACE', 'ansatz_parameter_count': 5, 'compression_reconstruction_error': 1.2417518519112547e-16, 'compression_threshold': 1e-10, 'factor_rank': 3, 'local_accuracy_gate': {'absolute_error_hartree': 6.617706382883171e-10, 'passed': True, 'threshold_hartree': 0.0016}, 'low_rank_aware': True, 'low_rank_method': 'modified_cholesky', 'optimized_parameters': [-0.002517398678155159, 0.0038946988975990223, -0.0030990423664654584, -0.004161664875235105, -0.02021061653252367], 'post_term_count': 9, 'pre_term_count': 9, 'selected_factor_count': 5, 'selected_generators': [{'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.028031882173134164, 'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': -0.028031882173134164, 'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': 0.01306398358080487, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.01306398358080487}], 'selection_rule': 'dominant_non_diagonal_hamiltonian_factors_with_real_mixing_companions', 'source_terms': [{'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'IX', 'weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'XI', 'weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.028031882173134164, 'pauli': 'XZ', 'weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': -0.028031882173134164, 'pauli': 'ZX', 'weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': 0.01306398358080487, 'pauli': 'XX', 'weight': 0.01306398358080487}]}, 'reps': 5, 'rotation_blocks': ['ry', 'rz']}`
- initial_point_strategy: `zeros`
- parameter_count: `5`
- converged: `True`
- iterations: `67`
- evaluations: `67`
- final_objective_energy: `-1.058116534475` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## LR-ACE Exploratory Algorithm

- algorithm_name: `LR-ACE`
- low_rank_method: `modified_cholesky`
- factor_rank: `3`
- selected_factor_count: `5`
- local_accuracy_gate: `{'absolute_error_hartree': 6.617706382883171e-10, 'passed': True, 'threshold_hartree': 0.0016}`
- selected_generators: `[{'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'IY', 'source_pauli': 'IX', 'source_weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.02803189488746322, 'pauli': 'YI', 'source_pauli': 'XI', 'source_weight': 0.02803189488746322}, {'coefficient_imag': 0.0, 'coefficient_real': 0.028031882173134164, 'pauli': 'YZ', 'source_pauli': 'XZ', 'source_weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': -0.028031882173134164, 'pauli': 'ZY', 'source_pauli': 'ZX', 'source_weight': 0.028031882173134164}, {'coefficient_imag': 0.0, 'coefficient_real': 0.01306398358080487, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.01306398358080487}]`

## Mitigation

- symmetry_check: `{'performed': False, 'requested': True, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- zne: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- pec: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-02T06:59:42.526989+00:00`
- Wall time (s): `3.813802000018768`
- Git commit: `adb7dad10aed10ad7b2c73d1a778c9bce42840ed`
- Git commit short: `adb7dad10aed`
- Git branch: `codex/qcchem-visual-workbench`
- Git describe: `adb7dad-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 61, 'untracked': 179}`
- Workspace fingerprint: `92700c2b4ac5a6027436da5de91198ba00eb7f48492cd3b7f0aa84fc7dd91aff`
- Dependency versions: `{'numpy': '2.4.1', 'pyscf': '2.12.1', 'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_aer': '0.17.2', 'qiskit_nature': '0.7.2', 'scipy': '1.17.0'}`
- Seed: `73`
- Source config: `/Users/a0000/QCchem/configs/exploratory/lih_active_lr_ace.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/lih_active_lr_ace/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/exploratory/lih_active_lr_ace.yaml
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=4, cost=40000
- Preparing backend: statevector
- Running solver: lr_ace
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih_active_lr_ace/exact_result.json
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=1.994s, measured_cost=None
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih_active_lr_ace/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih_active_lr_ace/report.md
- Run completed
