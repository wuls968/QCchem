# QCchem Report: H2-runtime-hardware-probe-ca

## Verification

- verification_status: `validated`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `validated`
- Verification Notes: `[]`
- Scientific Risk Notes: `['Runtime-derived hardware energy does not meet chemical accuracy, even though the local solver path may.']`

## Energy Summary

- electronic_energy: `-1.852388159814` Hartree
- nuclear_repulsion_energy: `0.715104339081` Hartree
- total_energy: `-1.137283820733` Hartree
- hf_reference_energy: `-1.116759307396` Hartree
- solver_energy: `-1.852388159814` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.852388173570` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020524513337` Hartree
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
- comparison_target: `variational_result`
- exact_electronic_energy: `-1.852388173570` Hartree
- exact_total_energy: `-1.137283834489` Hartree
- absolute_error: `0.000000013755` Hartree
- relative_error: `7.425616361096701e-09`
- statistical_error: `None`
- absolute_error_threshold: `0.2`
- relative_error_threshold: `0.2`
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

- Mapping kind: `jordan_wigner`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `15`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `707`
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

- name: `publication`
- default_shots: `None`
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
- absolute_error_hartree: `0.000000013755` Hartree
- absolute_error_kcal_mol: `8.631470581341205e-06`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Chemical Accuracy (Runtime-Derived)

- available: `True`
- assessment_target: `runtime_derived`
- status: `exploratory`
- meets_chemical_accuracy: `False`
- absolute_error_hartree: `0.046849070102` Hartree
- absolute_error_kcal_mol: `29.39823533693178`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.019618258754` Hartree
- notes: `['Does not meet chemical accuracy threshold.', 'Observed error exceeds 95% statistical uncertainty.']`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- precision_target: `0.02`
- max_budgeted_shots: `4096`
- max_execution_seconds: `300.0`
- calibration_strategy: `chemical_accuracy_push`
- resilience_level: `2`
- grouping_policy: `default`
- session_recommendation: `optional`
- batch_recommendation: `optional`
- low_rank_workload: `False`
- measurement_group_count: `5`
- estimated_shot_cost: `12500.0`
- options: `{'backend_name': 'ibm_kingston', 'optimization_level': 3, 'submit_real_job': True, 'wait_for_result': True}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'batch_mode_requested': False, 'compression_method': None, 'low_rank_policy_applied': False, 'remote_execution_configured': False, 'session_mode_requested': True}`

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
- provenance: `{'policy_name': 'publication', 'source': 'qcchem.chem.reduction_planner'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `runtime_estimator`
- low_rank_aware: `False`
- term_count: `15`
- group_count: `5`
- estimated_shot_cost: `12500.0`
- runtime_precision_target: `0.02`
- uncompressed_group_count: `5`
- uncompressed_estimated_shot_cost: `12500.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.02.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.7276935830013826`
- measured_shot_usage: `None`
- precision_target: `0.02`
- achieved_error: `0.000000013755` Hartree
- estimated_measurement_cost: `12500.0`
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
- job_id: `d7gtv5493s0c738s29r0`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `56.549181249996764`
- usage_estimation: `{'quantum_seconds': 35.014459732}`
- job_metrics: `{'bss': {'seconds': 28}, 'caller': 'qiskit_ibm_runtime~estimator.py', 'qiskit_version': 'qiskit_ibm_runtime-0.46.1,qiskit-2.3.0*,qiskit_aer-0.17.2*,qiskit_nature-0.7.2*', 'timestamps': {'created': '2026-04-17T07:21:56.113348Z', 'finished': '2026-04-17T07:22:33.779685Z', 'running': '2026-04-17T07:21:57.317526Z'}, 'usage': {'quantum_seconds': 28, 'seconds': 28}}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'backend_name': 'ibm_kingston', 'budget_strategy': 'chemical_accuracy_push', 'grouping_policy': 'default', 'max_budgeted_shots': 4096, 'max_execution_seconds': 300.0, 'optimization_level': 3, 'precision_target': 0.02, 'resilience_level': 2, 'submit_real_job': True, 'wait_for_result': True}`
- returned_job_metadata: `{'evs': [-1.8055391034678427], 'metadata': {'circuit_metadata': {}, 'num_randomizations': 32, 'resilience': {'zne': {'extrapolator': ['multiple']}}, 'shots': 4096, 'target_precision': 0.015625}, 'stds': [0.019618258753612238]}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'backend_name': 'ibm_kingston', 'circuit_qubits': 4, 'operator_qubits': 4, 'parameter_count': 3, 'runtime_package_version': '0.46.1'}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'uccsd', 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `False`
- iterations: `40`
- evaluations: `40`
- final_objective_energy: `-1.852388159814` Hartree
- optimizer_message: `Return from COBYLA because the objective function has been evaluated MAXFUN times.`

## Mitigation

- symmetry_check: `{'performed': False, 'requested': True, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'method': 'none', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- zne: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- pec: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-04-17T07:22:35.349008+00:00`
- Wall time (s): `57.53300904200296`
- Git commit: `316becdb4f870ebb1fa1a1446c4f22d8c2aabd2d`
- Git commit short: `316becdb4f87`
- Git branch: `master`
- Git describe: `316becd-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 6, 'untracked': 134}`
- Workspace fingerprint: `b60982b5175acb91fde5abbe4982848c12a7684a868d3afb53f1b2d8a8427de4`
- Dependency versions: `{'numpy': '2.4.1', 'pyscf': '2.12.1', 'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_aer': '0.17.2', 'qiskit_nature': '0.7.2', 'scipy': '1.17.0'}`
- Seed: `707`
- Source config: `configs/h2_runtime_hardware_probe_ca.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from configs/h2_runtime_hardware_probe_ca.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=5, cost=12500
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/exact_result.json
- Computed empirical calibration: wall_time=0.728s, measured_cost=None
- Runtime submission attempt recorded: submitted
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_ca/report.md
- Run completed
