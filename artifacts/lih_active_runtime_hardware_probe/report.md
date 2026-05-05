# QCchem Report: LiH-active-runtime-hardware-probe

## Verification

- verification_status: `exploratory`

## Energy Summary

- electronic_energy: `-8.855640235044` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.863432964569` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.059420666267` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.059126320696` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.001568194761` Hartree
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
- solver_hamiltonian_energy: `-1.059126320696` Hartree
- electronic_energy: `-8.855345889473` Hartree
- total_energy: `-7.863138618998` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `compressed_vs_uncompressed`
- exact_electronic_energy: `-8.855345889473` Hartree
- exact_total_energy: `-7.863138618998` Hartree
- absolute_error: `0.002536465252` Hartree
- relative_error: `0.00032246060378868225`
- statistical_error: `0.002255638119` Hartree
- absolute_error_threshold: `0.2`
- relative_error_threshold: `0.2`
- within_uncertainty: `True`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2]}`
- Transformers applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475, 'FreezeCoreTransformer': -7.796219568777051, 'ActiveSpaceTransformer': 0.0}`
- Electronic constant correction: `-7.796219568777` Hartree

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `72`
- Qubit Hamiltonian terms: `12`

## Backend

- Backend kind: `shot_estimator`
- Precision: `None`
- Shots: `1024`
- Seed: `111`
- Repetitions: `1`
- Abelian grouping: `True`
- Noise enabled: `False`
- Runtime enabled: `True`

## Backend Capability

- backend_kind: `shot_estimator`
- statevector: `False`
- shot_based: `True`
- exact_baseline: `True`
- runtime_ready: `True`
- session_ready: `True`
- batch_ready: `True`
- mitigation_ready: `True`
- noise_model_ready: `True`
- supports_grouping: `True`
- supports_repetitions: `True`
- supports_confidence_metrics: `True`

## Execution Policy

- name: `publication`
- default_shots: `8192`
- default_repetitions: `5`
- exact_baseline_required: `True`
- confidence_rule: `exact baseline and uncertainty reporting required`
- mitigation_posture: `symmetry-check required, readout placeholder allowed`
- runtime_ready_expected: `True`
- session_ready_expected: `False`
- batch_ready_expected: `False`
- noise_ready_expected: `False`

## Compressed vs Uncompressed

- available: `True`
- method: `modified_cholesky`
- rank: `2`
- threshold: `0.001`
- pre_term_count: `27`
- post_term_count: `12`
- compressed_solver_energy: `-1.059420666267` Hartree
- uncompressed_solver_energy: `-1.061957131519` Hartree
- compressed_total_energy: `-7.863432964569` Hartree
- uncompressed_total_energy: `-7.865969429821` Hartree
- absolute_error: `0.002536465252` Hartree
- relative_error: `0.00032246060378868225`
- compressed_solve_wall_time_seconds: `0.8347472080004081`
- uncompressed_solve_wall_time_seconds: `0.8496496669995395`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `True`
- session_ready: `True`
- batch_ready: `True`
- precision_target: `0.15`
- resilience_level: `0`
- grouping_policy: `commuting_low_rank`
- session_recommendation: `optional`
- batch_recommendation: `optional`
- low_rank_workload: `True`
- measurement_group_count: `2`
- estimated_shot_cost: `90.0`
- options: `{'backend_name': 'ibm_fez', 'submit_real_job': True, 'wait_for_result': True, 'optimization_level': 1}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'remote_execution_configured': False, 'session_mode_requested': True, 'batch_mode_requested': True, 'low_rank_policy_applied': True, 'compression_method': 'modified_cholesky'}`

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
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475, 'FreezeCoreTransformer': -7.796219568777051, 'ActiveSpaceTransformer': 0.0}`
- constant_energy_correction: `-7.796219568777` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `-6.804012298302` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Compression Audit

- enabled: `True`
- method: `modified_cholesky`
- rank: `2`
- threshold: `0.001`
- max_rank: `2`
- apply_to_solver: `False`
- execution_enabled: `True`
- original_num_qubits: `4`
- compressed_num_qubits: `4`
- original_fermionic_term_count: `72`
- original_qubit_term_count: `27`
- compressed_term_count_estimate: `12`
- pre_term_count: `27`
- post_term_count: `12`
- primary_rank: `2`
- secondary_rank: `None`
- reconstruction_error_frobenius: `0.008905643352596537`
- reconstruction_error: `0.008905643352596537`
- verification_status: `validated`
- notes: `['Modified-Cholesky compression reconstructed the two-electron pair matrix for execution.']`

## Measurement Plan

- strategy: `low_rank_commuting`
- grouping_policy: `commuting_low_rank`
- execution_mode: `runtime_estimator`
- low_rank_aware: `True`
- term_count: `12`
- group_count: `2`
- estimated_shot_cost: `90.0`
- runtime_precision_target: `0.15`
- uncompressed_group_count: `9`
- uncompressed_estimated_shot_cost: `405.0`
- cost_reduction_ratio: `0.2222222222222222`
- notes: `["Measurement groups estimated with strategy 'low_rank_commuting'.", 'Per-group shot estimate derived from precision target 0.15.', 'Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.']`

## Empirical Calibration

- available: `True`
- measured_wall_time_seconds: `0.8347472080004081`
- measured_shot_usage: `2048.0`
- precision_target: `0.15`
- achieved_error: `0.002536465252` Hartree
- estimated_measurement_cost: `90.0`
- estimated_vs_measured_cost: `0.0439453125`
- reference_target: `compressed_vs_uncompressed`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Runtime Submission

- attempted: `True`
- submitted: `True`
- succeeded: `True`
- service: `ibm_quantum_platform`
- mode: `backend`
- session_requested: `True`
- batch_requested: `True`
- backend_name: `ibm_fez`
- provider: `QiskitRuntimeService`
- job_id: `d7deocr0g7hs73drrrf0`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `22.443625707999672`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'precision_target': 0.15, 'resilience_level': 0, 'grouping_policy': 'commuting_low_rank', 'backend_name': 'ibm_fez', 'submit_real_job': True, 'wait_for_result': True, 'optimization_level': 1}`
- returned_job_metadata: `{'evs': [-0.6622242755762507], 'stds': [0.040638818097580645], 'metadata': {'shots': 44, 'target_precision': 0.15, 'circuit_metadata': {}, 'num_randomizations': 1}}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'runtime_package_version': '0.46.1', 'backend_name': 'ibm_fez', 'parameter_count': 3, 'operator_qubits': 4, 'circuit_qubits': 4}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `33`
- evaluations: `33`
- final_objective_energy: `-1.059420666267` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `1024`
- num_repeats: `1`
- seed: `111`
- repeat_seeds: `[100111]`
- sampled_solver_energy_mean: `-1.057753208015` Hartree
- sampled_solver_energy_std: `0.000000000000` Hartree
- sampled_electronic_energy_mean: `-8.853972776792` Hartree
- sampled_total_energy_mean: `-7.861765506317` Hartree
- standard_error: `0.002255638119` Hartree
- confidence_interval_low: `-1.062174258728` Hartree
- confidence_interval_high: `-1.053332157303` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-04-12T00:50:05.448288+00:00`
- Wall time (s): `24.320583624999927`
- Git commit: `None`
- Git commit short: `None`
- Git branch: `None`
- Git describe: `None`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 0, 'untracked': 11}`
- Workspace fingerprint: `e4094d41bd38dceefa336a78a596e9b112062c86006ed5d7cfc6ae650ac2312b`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `111`
- Source config: `configs/lih_active_runtime_hardware_probe.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/result.h5`

## Log Summary

- Loading config from configs/lih_active_runtime_hardware_probe.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=2, cost=90
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/exact_result.json
- Collected repeated shot-based sampling statistics
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=0.835s, measured_cost=2048.0
- Runtime submission attempt recorded: submitted
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe/report.md
- Run completed
