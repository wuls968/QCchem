# QCchem Report: LiH-active-runtime-hardware-probe-v2

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Verification

- verification_status: `exploratory`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `exploratory`
- Verification Notes: `[]`
- Scientific Risk Notes: `['Runtime-derived hardware energy does not meet chemical accuracy, even though the local solver path may.']`

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
- Active space metadata: `{'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2], 'num_electrons': 2, 'num_spatial_orbitals': 2}`
- Transformers applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- Hamiltonian constants: `{'ActiveSpaceTransformer': 0.0, 'FreezeCoreTransformer': -7.796219568777051, 'nuclear_repulsion_energy': 0.992207270475}`
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

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000294345572` Hartree
- absolute_error_kcal_mol: `0.18470463498507664`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.002255638119` Hartree
- notes: `['Meets chemical accuracy threshold.', 'Observed error lies within 95% statistical uncertainty.']`

## Chemical Accuracy (Runtime-Derived)

- available: `True`
- assessment_target: `runtime_derived`
- status: `exploratory`
- meets_chemical_accuracy: `False`
- absolute_error_hartree: `0.388794195022` Hartree
- absolute_error_kcal_mol: `243.97204081226127`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.041369338380` Hartree
- notes: `['Does not meet chemical accuracy threshold.', 'Observed error exceeds 95% statistical uncertainty.']`

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
- compressed_solve_wall_time_seconds: `0.9938129170004686`
- uncompressed_solve_wall_time_seconds: `1.370027792003384`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `True`
- session_ready: `True`
- batch_ready: `True`
- precision_target: `0.15`
- max_budgeted_shots: `None`
- max_execution_seconds: `None`
- calibration_strategy: `None`
- resilience_level: `0`
- grouping_policy: `commuting_low_rank`
- session_recommendation: `optional`
- batch_recommendation: `optional`
- low_rank_workload: `True`
- measurement_group_count: `2`
- estimated_shot_cost: `90.0`
- options: `{'backend_name': 'ibm_fez', 'optimization_level': 1, 'submit_real_job': True, 'wait_for_result': True}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'batch_mode_requested': True, 'compression_method': 'modified_cholesky', 'low_rank_policy_applied': True, 'remote_execution_configured': False, 'session_mode_requested': True}`

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
- provenance: `{'policy_name': 'publication', 'source': 'qcchem.chem.reduction_planner'}`

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

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.9938129170004686`
- measured_shot_usage: `2048.0`
- precision_target: `0.15`
- achieved_error: `0.002536465252` Hartree
- estimated_measurement_cost: `90.0`
- estimated_vs_measured_cost: `0.0439453125`
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
- batch_requested: `True`
- backend_name: `ibm_fez`
- provider: `QiskitRuntimeService`
- job_id: `d7gr4jc93s0c738rtv10`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `84.30369187500037`
- usage_estimation: `{}`
- job_metrics: `{}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'backend_name': 'ibm_fez', 'grouping_policy': 'commuting_low_rank', 'optimization_level': 1, 'precision_target': 0.15, 'resilience_level': 0, 'submit_real_job': True, 'wait_for_result': True}`
- returned_job_metadata: `{'evs': [-0.6703321256739458], 'metadata': {'circuit_metadata': {}, 'num_randomizations': 1, 'shots': 44, 'target_precision': 0.15}, 'stds': [0.04136933838034907]}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'backend_name': 'ibm_fez', 'circuit_qubits': 4, 'operator_qubits': 4, 'parameter_count': 3, 'runtime_package_version': '0.46.1'}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'uccsd', 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
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

- symmetry_check: `{'performed': False, 'requested': True, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- zne: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- pec: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-04-17T04:08:52.940347+00:00`
- Wall time (s): `86.88391525000043`
- Git commit: `ef1a7c5ddffd7726de2fa577b9f947307018afc6`
- Git commit short: `ef1a7c5ddffd`
- Git branch: `codex/qwen-integration`
- Git describe: `ef1a7c5-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 3, 'untracked': 96}`
- Workspace fingerprint: `3f139b68e6e4d1576d085f5d4bb10981e709fa4de43eec23ebd6c83b643e576f`
- Dependency versions: `{'numpy': '2.4.1', 'pyscf': '2.12.1', 'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_aer': '0.17.2', 'qiskit_nature': '0.7.2', 'scipy': '1.17.0'}`
- Seed: `111`
- Source config: `/Users/a0000/QCchem/configs/lih_active_runtime_hardware_probe_v2.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_active_runtime_hardware_probe_v2.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=2, cost=90
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/exact_result.json
- Collected repeated shot-based sampling statistics
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=0.994s, measured_cost=2048.0
- Runtime submission attempt recorded: submitted
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/report.md
- Run completed
