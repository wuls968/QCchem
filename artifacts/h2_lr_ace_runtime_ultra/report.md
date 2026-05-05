# QCchem Report: H2-LR-ACE-runtime-probe

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-LR-ACE-runtime-probe`
- basis: `sto3g`
- method: `lr_ace / {'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'lr_ace', 'lr_ace': {'algorithm_name': 'LR-ACE', 'ansatz_parameter_count': 1, 'compression_reconstruction_error': 1.2412670766236366e-16, 'compression_threshold': 1e-10, 'factor_rank': 3, 'local_accuracy_gate': {'absolute_error_hartree': 4.77500483597737e-10, 'passed': True, 'threshold_hartree': 0.0016}, 'low_rank_aware': True, 'low_rank_method': 'modified_cholesky', 'optimized_parameters': [-0.11279999999999998], 'post_term_count': 5, 'pre_term_count': 5, 'selected_factor_count': 1, 'selected_generators': [{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.1812104620151966}], 'selection_rule': 'dominant_non_diagonal_hamiltonian_factors_with_real_mixing_companions', 'source_terms': [{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'XX', 'weight': 0.1812104620151966}]}, 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `exploratory`
- hardware_verified: `True`
- hardware_evidence_tier: `retrieved_result`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137283834011` Hartree
- headline_correlation_energy: `-0.020524526615` Hartree
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `compressed_vs_uncompressed`
- active_space_metadata: `None`
- runtime_backend: `ibm_marrakesh`
- runtime_job_id: `d7qq5hfljm6s73b9ig40`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_lr_ace_runtime_ultra', 'backend_kind': 'statevector', 'basis': 'sto3g', 'mapping_kind': 'parity_two_qubit_reduction', 'molecule_name': 'H2-LR-ACE-runtime-probe'}`
- primary_scientific_claim: `H2-LR-ACE-runtime-probe stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_scope': 'single_run', 'baseline_source': 'exact_diagonalization', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'comparison_target': 'compressed_vs_uncompressed', 'metric_kind': 'absolute_error_hartree', 'threshold': 0.0016, 'units': 'Hartree', 'value': 2.220446049250313e-16}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `retrieved_result`
- trust_tier: `exploratory`
- recommended_action: `review_runtime_gap`

## Claim

- primary_scientific_claim: `H2-LR-ACE-runtime-probe stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `review_runtime_gap`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `modified_cholesky` / status=`validated`
- correction: `None` / delta=`None`
- comparison_evidence: `{'absolute_error': 2.220446049250313e-16, 'baseline_strength': 'strong', 'comparison_target': 'compressed_vs_uncompressed', 'compressed_vs_uncompressed': {'absolute_error': 2.220446049250313e-16, 'available': True, 'compressed_solve_wall_time_seconds': 0.22650179199990816, 'compressed_solver_energy': -1.8523881730920808, 'compressed_total_energy': -1.1372838340109996, 'method': 'modified_cholesky', 'post_term_count': 5, 'pre_term_count': 5, 'rank': 3, 'relative_error': 1.9524115113983383e-16, 'threshold': 1e-10, 'uncompressed_solve_wall_time_seconds': 0.19271454101544805, 'uncompressed_solver_energy': -1.852388173092081, 'uncompressed_total_energy': -1.1372838340109999}, 'relative_error': 1.9524115113983383e-16, 'statistical_error': None}`

## Proof

- execution_evidence: `{'measured_shot_usage': None, 'measurement_group_count': 2, 'measurement_strategy': 'low_rank_lr_ace_runtime', 'runtime_backend': 'ibm_marrakesh', 'runtime_job_id': 'd7qq5hfljm6s73b9ig40', 'shots': None, 'wall_time_seconds': 24.952562541991938}`
- trust_judgment: `{'hardware_evidence_tier': 'retrieved_result', 'hardware_verified': True, 'module_origin': 'exploratory', 'scientific_risk_notes': ['LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.', 'Dominant low-rank factor selection is heuristic and not yet publication-validated.', 'Runtime-derived chemistry estimate still does not meet chemical accuracy.'], 'verification_notes': ['validation_scope=lr_ace local exact-baseline gate', 'Real runtime result retrieved and merged into the run artifact.'], 'verification_status': 'exploratory'}`
- provenance_timestamp: `2026-05-02T07:07:49.012344+00:00`
- runtime_job_id: `d7qq5hfljm6s73b9ig40`
- artifact_root: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra`

## Chemical Accuracy Frame

- available_assessments: `['local_execution', 'runtime_derived']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000478` Hartree
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
- backend_name: `ibm_marrakesh`
- job_id: `d7qq5hfljm6s73b9ig40`
- verification_status: `exploratory`
- layout_strategy: `min_weighted_error`
- selected_layout: `[2, 1]`
- transpiled_depth: `12`
- transpiled_two_qubit_gate_count: `2`

## Verification

- verification_status: `exploratory`

## Validation Boundary

- Module Origin: `exploratory`
- Capability Tier: `exploratory`
- Verification Notes: `['validation_scope=lr_ace local exact-baseline gate', 'Real runtime result retrieved and merged into the run artifact.']`
- Scientific Risk Notes: `['LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.', 'Dominant low-rank factor selection is heuristic and not yet publication-validated.', 'Runtime-derived chemistry estimate still does not meet chemical accuracy.']`

## Energy Summary

- electronic_energy: `-1.852388173092` Hartree
- nuclear_repulsion_energy: `0.715104339081` Hartree
- total_energy: `-1.137283834011` Hartree
- hf_reference_energy: `-1.116759307396` Hartree
- solver_energy: `-1.852388173092` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.852388173570` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020524526615` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `0.000000000000` Hartree
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
- solver_hamiltonian_energy: `-1.852388173570` Hartree
- electronic_energy: `-1.852388173570` Hartree
- total_energy: `-1.137283834489` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `compressed_vs_uncompressed`
- exact_electronic_energy: `-1.852388173570` Hartree
- exact_total_energy: `-1.137283834489` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `1.9524115113983383e-16`
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

## Mapping

- Mapping kind: `parity_two_qubit_reduction`
- Qubit count: `2`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `5`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `1729`
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
- absolute_error_hartree: `0.000000000478` Hartree
- absolute_error_kcal_mol: `2.9963607729716156e-07`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Chemical Accuracy (Runtime-Derived)

- available: `True`
- assessment_target: `runtime_derived`
- status: `exploratory`
- meets_chemical_accuracy: `False`
- absolute_error_hartree: `0.002578316180` Hartree
- absolute_error_kcal_mol: `1.6179178296298569`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.001421873364` Hartree
- notes: `['Does not meet chemical accuracy threshold.', 'Observed error lies within 95% statistical uncertainty.']`

## Compressed vs Uncompressed

- available: `True`
- method: `modified_cholesky`
- rank: `3`
- threshold: `1e-10`
- pre_term_count: `5`
- post_term_count: `5`
- compressed_solver_energy: `-1.852388173092` Hartree
- uncompressed_solver_energy: `-1.852388173092` Hartree
- compressed_total_energy: `-1.137283834011` Hartree
- uncompressed_total_energy: `-1.137283834011` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `1.9524115113983383e-16`
- compressed_solve_wall_time_seconds: `0.22650179199990816`
- uncompressed_solve_wall_time_seconds: `0.19271454101544805`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- precision_target: `0.003`
- max_budgeted_shots: `131072`
- max_execution_seconds: `300.0`
- calibration_strategy: `lr_ace_h2_ultra_refinement`
- resilience_level: `2`
- grouping_policy: `low_rank_factor_aware`
- session_recommendation: `optional`
- batch_recommendation: `optional`
- low_rank_workload: `True`
- measurement_group_count: `2`
- estimated_shot_cost: `8890.0`
- options: `{'confirmation_message': 'LR-ACE exploratory Runtime probe may consume IBM quota.', 'default_shots': 131072, 'layout_method': 'sabre', 'layout_strategy': 'min_weighted_error', 'optimization_level': 3, 'precision_target': 0.003, 'requires_action_time_confirmation': True, 'routing_method': 'sabre', 'seed_transpiler': 1729, 'submit_real_job': True, 'wait_for_result': False}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'batch_mode_requested': False, 'compression_method': 'modified_cholesky', 'low_rank_policy_applied': True, 'remote_execution_configured': False, 'session_mode_requested': True}`

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
- total_constant_correction: `0.715104339081` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Reduction Plan

- enabled: `True`
- mode: `disabled`
- strategy: `none`
- recommended_changes: `{}`
- notes: `['No reduction planning inputs were requested.']`
- provenance: `{'policy_name': 'hardware_ready', 'source': 'qcchem.chem.reduction_planner'}`

## Compression Audit

- enabled: `True`
- method: `modified_cholesky`
- rank: `3`
- threshold: `1e-10`
- max_rank: `4`
- apply_to_solver: `True`
- execution_enabled: `True`
- original_num_qubits: `2`
- compressed_num_qubits: `2`
- original_fermionic_term_count: `36`
- original_qubit_term_count: `5`
- compressed_term_count_estimate: `5`
- pre_term_count: `5`
- post_term_count: `5`
- primary_rank: `3`
- secondary_rank: `None`
- reconstruction_error_frobenius: `1.2412670766236366e-16`
- reconstruction_error: `1.2412670766236366e-16`
- verification_status: `validated`
- notes: `['Modified-Cholesky compression reconstructed the two-electron pair matrix for execution.']`

## Measurement Plan

- strategy: `low_rank_lr_ace_runtime`
- grouping_policy: `low_rank_factor_aware`
- execution_mode: `runtime_estimator`
- low_rank_aware: `True`
- term_count: `5`
- group_count: `2`
- estimated_shot_cost: `8890.0`
- runtime_precision_target: `0.015`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `8890.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'low_rank_lr_ace_runtime'.", 'Per-group shot estimate derived from precision target 0.015.', 'Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.22650179199990816`
- measured_shot_usage: `None`
- precision_target: `0.015`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `8890.0`
- estimated_vs_measured_cost: `None`
- reference_target: `compressed_vs_uncompressed`
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
- backend_name: `ibm_marrakesh`
- provider: `QiskitRuntimeService`
- layout_strategy: `min_weighted_error`
- selected_layout: `[2, 1]`
- layout_score: `0.004504149246380901`
- transpiled_depth: `12`
- transpiled_two_qubit_gate_count: `2`
- transpilation_options: `{'approximation_degree': 1.0, 'initial_layout': [2, 1], 'layout_method': 'sabre', 'optimization_level': 3, 'routing_method': 'sabre', 'seed_transpiler': 1729}`
- job_id: `d7qq5hfljm6s73b9ig40`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `24.17161933297757`
- usage_estimation: `{'quantum_seconds': 290.813745573}`
- job_metrics: `{'bss': {'seconds': 217}, 'caller': 'qiskit_ibm_runtime~estimator.py', 'qiskit_version': 'qiskit_ibm_runtime-0.46.1,qiskit-2.3.0*,qiskit_aer-0.17.2*,qiskit_nature-0.7.2*', 'timestamps': {'created': '2026-05-02T07:07:49.270263Z', 'finished': '2026-05-02T07:11:47.262488Z', 'running': '2026-05-02T07:07:49.945391Z'}, 'usage': {'quantum_seconds': 217, 'seconds': 217}}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'budget_strategy': 'lr_ace_h2_ultra_refinement', 'confirmation_message': 'LR-ACE exploratory Runtime probe may consume IBM quota.', 'default_shots': 131072, 'grouping_policy': 'low_rank_factor_aware', 'layout_method': 'sabre', 'layout_strategy': 'min_weighted_error', 'max_budgeted_shots': 131072, 'max_execution_seconds': 300.0, 'optimization_level': 3, 'precision_target': 0.003, 'requires_action_time_confirmation': True, 'resilience_level': 2, 'routing_method': 'sabre', 'seed_transpiler': 1729, 'submit_real_job': True, 'wait_for_result': False}`
- returned_job_metadata: `{'evs': [-1.8498098573900397], 'metadata': {'circuit_metadata': {}, 'num_randomizations': 32, 'resilience': {'zne': {'extrapolator': ['multiple']}}, 'shots': 131072, 'target_precision': 0.002762135864009951}, 'stds': [0.0014218733640510401]}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'backend_name': 'ibm_marrakesh', 'backend_selection_strategy': 'min_weighted_error', 'candidates': [{'backend_name': 'ibm_marrakesh', 'entangling_score': 0.0010251453401309008, 'layout_score': 0.004504149246380901, 'pending_jobs': 0, 'readout_score': 0.0069580078125, 'selected_layout': [2, 1]}, {'backend_name': 'ibm_kingston', 'entangling_score': 0.0011204659863697508, 'layout_score': 0.005148786298869751, 'pending_jobs': 0, 'readout_score': 0.008056640625, 'selected_layout': [90, 89]}, {'backend_name': 'ibm_fez', 'entangling_score': 0.001510689689632888, 'layout_score': 0.006759713127132888, 'pending_jobs': 0, 'readout_score': 0.010498046875, 'selected_layout': [23, 22]}], 'circuit_qubits': 2, 'last_polled_at': '2026-05-02T07:14:51.031832+00:00', 'last_polled_status': 'DONE', 'layout_strategy': 'min_weighted_error', 'operator_qubits': 2, 'parameter_count': 1, 'runtime_package_version': '0.46.1', 'selected_backend': 'ibm_marrakesh'}`

## Variational Result

- available: `True`
- solver_kind: `lr_ace`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 220, 'tol': None}`
- ansatz: `{'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'lr_ace', 'lr_ace': {'algorithm_name': 'LR-ACE', 'ansatz_parameter_count': 1, 'compression_reconstruction_error': 1.2412670766236366e-16, 'compression_threshold': 1e-10, 'factor_rank': 3, 'local_accuracy_gate': {'absolute_error_hartree': 4.77500483597737e-10, 'passed': True, 'threshold_hartree': 0.0016}, 'low_rank_aware': True, 'low_rank_method': 'modified_cholesky', 'optimized_parameters': [-0.11279999999999998], 'post_term_count': 5, 'pre_term_count': 5, 'selected_factor_count': 1, 'selected_generators': [{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.1812104620151966}], 'selection_rule': 'dominant_non_diagonal_hamiltonian_factors_with_real_mixing_companions', 'source_terms': [{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'XX', 'weight': 0.1812104620151966}]}, 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
- initial_point_strategy: `zeros`
- parameter_count: `1`
- converged: `True`
- iterations: `23`
- evaluations: `23`
- final_objective_energy: `-1.852388173092` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## LR-ACE Exploratory Algorithm

- algorithm_name: `LR-ACE`
- low_rank_method: `modified_cholesky`
- factor_rank: `3`
- selected_factor_count: `1`
- local_accuracy_gate: `{'absolute_error_hartree': 4.77500483597737e-10, 'passed': True, 'threshold_hartree': 0.0016}`
- selected_generators: `[{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.1812104620151966}]`

## Mitigation

- symmetry_check: `{'performed': False, 'requested': True, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'method': 'none', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- zne: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- pec: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-02T07:07:49.012344+00:00`
- Wall time (s): `24.952562541991938`
- Git commit: `adb7dad10aed10ad7b2c73d1a778c9bce42840ed`
- Git commit short: `adb7dad10aed`
- Git branch: `codex/qcchem-visual-workbench`
- Git describe: `adb7dad-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 61, 'untracked': 182}`
- Workspace fingerprint: `7077c2565f6813d46f8f7937a3d1b6e3aee4eebcbf8ab20ea9bf0aa0f4b14b80`
- Dependency versions: `{'numpy': '2.4.1', 'pyscf': '2.12.1', 'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_aer': '0.17.2', 'qiskit_nature': '0.7.2', 'scipy': '1.17.0'}`
- Seed: `1729`
- Source config: `/Users/a0000/QCchem/configs/exploratory/h2_lr_ace_runtime.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/exploratory/h2_lr_ace_runtime.yaml
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=2, cost=8890
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: statevector
- Running solver: lr_ace
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/exact_result.json
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=0.227s, measured_cost=None
- Persisted runtime submission sidecar after job submit: d7qq5hfljm6s73b9ig40
- Runtime submission attempt recorded: submitted
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_lr_ace_runtime_ultra/report.md
- Run completed
