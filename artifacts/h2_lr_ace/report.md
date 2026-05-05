# QCchem Report: H2-LR-ACE

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-LR-ACE`
- basis: `sto3g`
- method: `lr_ace / {'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'lr_ace', 'lr_ace': {'algorithm_name': 'LR-ACE', 'ansatz_parameter_count': 1, 'compression_reconstruction_error': 1.2412670766236366e-16, 'compression_threshold': 1e-10, 'factor_rank': 3, 'local_accuracy_gate': {'absolute_error_hartree': 4.77500483597737e-10, 'passed': True, 'threshold_hartree': 0.0016}, 'low_rank_aware': True, 'low_rank_method': 'modified_cholesky', 'optimized_parameters': [-0.11279999999999998], 'post_term_count': 5, 'pre_term_count': 5, 'selected_factor_count': 1, 'selected_generators': [{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'YX', 'source_pauli': 'XX', 'source_weight': 0.1812104620151966}], 'selection_rule': 'dominant_non_diagonal_hamiltonian_factors_with_real_mixing_companions', 'source_terms': [{'coefficient_imag': 0.0, 'coefficient_real': 0.1812104620151966, 'pauli': 'XX', 'weight': 0.1812104620151966}]}, 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137283834011` Hartree
- headline_correlation_energy: `-0.020524526615` Hartree
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `compressed_vs_uncompressed`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_lr_ace', 'backend_kind': 'statevector', 'basis': 'sto3g', 'mapping_kind': 'parity_two_qubit_reduction', 'molecule_name': 'H2-LR-ACE'}`
- primary_scientific_claim: `H2-LR-ACE stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_scope': 'single_run', 'baseline_source': 'exact_diagonalization', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'comparison_target': 'compressed_vs_uncompressed', 'metric_kind': 'absolute_error_hartree', 'threshold': 0.0016, 'units': 'Hartree', 'value': 2.220446049250313e-16}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-LR-ACE stays within chemical accuracy against compressed_vs_uncompressed for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `modified_cholesky` / status=`validated`
- correction: `None` / delta=`None`
- comparison_evidence: `{'absolute_error': 2.220446049250313e-16, 'baseline_strength': 'strong', 'comparison_target': 'compressed_vs_uncompressed', 'compressed_vs_uncompressed': {'absolute_error': 2.220446049250313e-16, 'available': True, 'compressed_solve_wall_time_seconds': 0.21463387500261888, 'compressed_solver_energy': -1.8523881730920808, 'compressed_total_energy': -1.1372838340109996, 'method': 'modified_cholesky', 'post_term_count': 5, 'pre_term_count': 5, 'rank': 3, 'relative_error': 1.9524115113983383e-16, 'threshold': 1e-10, 'uncompressed_solve_wall_time_seconds': 0.15901616599876434, 'uncompressed_solver_energy': -1.852388173092081, 'uncompressed_total_energy': -1.1372838340109999}, 'relative_error': 1.9524115113983383e-16, 'statistical_error': None}`

## Proof

- execution_evidence: `{'measured_shot_usage': None, 'measurement_group_count': 2, 'measurement_strategy': 'low_rank_lr_ace_local', 'runtime_backend': None, 'runtime_job_id': None, 'shots': None, 'wall_time_seconds': 0.7746736249828245}`
- trust_judgment: `{'hardware_evidence_tier': None, 'hardware_verified': False, 'module_origin': 'exploratory', 'scientific_risk_notes': ['LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.', 'Dominant low-rank factor selection is heuristic and not yet publication-validated.'], 'verification_notes': ['validation_scope=lr_ace local exact-baseline gate'], 'verification_status': 'exploratory'}`
- provenance_timestamp: `2026-05-02T06:59:35.890556+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/QCchem/artifacts/h2_lr_ace`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
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
- absolute_error_hartree: `0.000000000478` Hartree
- absolute_error_kcal_mol: `2.9963607729716156e-07`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

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
- compressed_solve_wall_time_seconds: `0.21463387500261888`
- uncompressed_solve_wall_time_seconds: `0.15901616599876434`

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
- provenance: `{'policy_name': 'benchmark', 'source': 'qcchem.chem.reduction_planner'}`

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

- strategy: `low_rank_lr_ace_local`
- grouping_policy: `low_rank_factor_aware`
- execution_mode: `estimator`
- low_rank_aware: `True`
- term_count: `5`
- group_count: `2`
- estimated_shot_cost: `20000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `20000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'low_rank_lr_ace_local'.", 'Per-group shot estimate derived from precision target 0.01.', 'Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.21463387500261888`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `20000.0`
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
- readout_mitigation: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- zne: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- pec: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-02T06:59:35.890556+00:00`
- Wall time (s): `0.7746736249828245`
- Git commit: `adb7dad10aed10ad7b2c73d1a778c9bce42840ed`
- Git commit short: `adb7dad10aed`
- Git branch: `codex/qcchem-visual-workbench`
- Git describe: `adb7dad-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 61, 'untracked': 179}`
- Workspace fingerprint: `f73d26e0b32a6a6b1459ece995e145ac5dbef52828afc4107989b8f92c74e0e0`
- Dependency versions: `{'numpy': '2.4.1', 'pyscf': '2.12.1', 'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_aer': '0.17.2', 'qiskit_nature': '0.7.2', 'scipy': '1.17.0'}`
- Seed: `1729`
- Source config: `/Users/a0000/QCchem/configs/exploratory/h2_lr_ace.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_lr_ace/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_lr_ace/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_lr_ace/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_lr_ace/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/h2_lr_ace/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/h2_lr_ace/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/exploratory/h2_lr_ace.yaml
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=2, cost=20000
- Preparing backend: statevector
- Running solver: lr_ace
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_lr_ace/exact_result.json
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=0.215s, measured_cost=None
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_lr_ace/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_lr_ace/report.md
- Run completed
