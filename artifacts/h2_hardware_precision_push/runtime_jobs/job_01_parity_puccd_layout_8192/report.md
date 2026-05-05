# QCchem Report: H2-hardware-precision-push

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-hardware-precision-push`
- basis: `sto3g`
- method: `vqe / {'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'puccd', 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `validated`
- hardware_verified: `True`
- hardware_evidence_tier: `retrieved_result`
- benchmark_absolute_error: `0.000000000478` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137283834011` Hartree
- headline_correlation_energy: `-0.020524526615` Hartree
- headline_absolute_error: `0.000000000478` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `None`
- runtime_backend: `ibm_kingston`
- runtime_job_id: `d7qph0cf3ras73b64dcg`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'job_01_parity_puccd_layout_8192', 'molecule_name': 'H2-hardware-precision-push', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'parity_two_qubit_reduction'}`
- primary_scientific_claim: `H2-hardware-precision-push stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 4.77500483597737e-10, 'units': 'Hartree', 'threshold': 0.0016, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `retrieved_result`
- trust_tier: `validated`
- recommended_action: `review_runtime_gap`

## Claim

- primary_scientific_claim: `H2-hardware-precision-push stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `validated`
- recommended_action: `review_runtime_gap`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 4.77500483597737e-10, 'relative_error': 2.5777560578870785e-10, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 26.53889541598619, 'shots': None, 'measurement_strategy': 'hardware_precision_push', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': 'ibm_kingston', 'runtime_job_id': 'd7qph0cf3ras73b64dcg'}`
- trust_judgment: `{'verification_status': 'validated', 'module_origin': 'core', 'hardware_verified': True, 'hardware_evidence_tier': 'retrieved_result', 'verification_notes': ['Real runtime result retrieved and merged into the run artifact.'], 'scientific_risk_notes': ['Runtime-derived chemistry estimate still does not meet chemical accuracy.']}`
- provenance_timestamp: `2026-05-02T06:24:01.807554+00:00`
- runtime_job_id: `d7qph0cf3ras73b64dcg`
- artifact_root: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192`

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
- backend_name: `ibm_kingston`
- job_id: `d7qph0cf3ras73b64dcg`
- verification_status: `exploratory`
- layout_strategy: `min_weighted_error`
- selected_layout: `[90, 89]`
- transpiled_depth: `22`
- transpiled_two_qubit_gate_count: `4`

## Verification

- verification_status: `validated`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `validated`
- Verification Notes: `['Real runtime result retrieved and merged into the run artifact.']`
- Scientific Risk Notes: `['Runtime-derived chemistry estimate still does not meet chemical accuracy.']`

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
- comparison_target: `variational_result`
- exact_electronic_energy: `-1.852388173570` Hartree
- exact_total_energy: `-1.137283834489` Hartree
- absolute_error: `0.000000000478` Hartree
- relative_error: `2.5777560578870785e-10`
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
- absolute_error_hartree: `0.018253500584` Hartree
- absolute_error_kcal_mol: `11.454244550141736`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.003520617109` Hartree
- notes: `['Does not meet chemical accuracy threshold.', 'Observed error exceeds 95% statistical uncertainty.']`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- precision_target: `0.015`
- max_budgeted_shots: `8192`
- max_execution_seconds: `420.0`
- calibration_strategy: `h2_hardware_precision_push`
- resilience_level: `2`
- grouping_policy: `hardware_aware_grouping`
- session_recommendation: `optional`
- batch_recommendation: `optional`
- low_rank_workload: `False`
- measurement_group_count: `2`
- estimated_shot_cost: `8890.0`
- options: `{'confirmation_message': 'This hardware optimization campaign can submit real IBM Runtime jobs and consume monthly quota.', 'default_shots': 8192, 'layout_method': 'sabre', 'layout_strategy': 'min_weighted_error', 'optimization_level': 3, 'requires_action_time_confirmation': True, 'routing_method': 'sabre', 'seed_transpiler': 1729, 'submit_real_job': True, 'wait_for_result': False}`
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
- provenance: `{'policy_name': 'hardware_ready', 'source': 'qcchem.chem.reduction_planner'}`

## Measurement Plan

- strategy: `hardware_precision_push`
- grouping_policy: `hardware_aware_grouping`
- execution_mode: `runtime_estimator`
- low_rank_aware: `False`
- term_count: `5`
- group_count: `2`
- estimated_shot_cost: `8890.0`
- runtime_precision_target: `0.015`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `8890.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'hardware_precision_push'.", 'Per-group shot estimate derived from precision target 0.015.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.04082204101723619`
- measured_shot_usage: `None`
- precision_target: `0.015`
- achieved_error: `0.000000000478` Hartree
- estimated_measurement_cost: `8890.0`
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
- layout_strategy: `min_weighted_error`
- selected_layout: `[90, 89]`
- layout_score: `0.005148786298869751`
- transpiled_depth: `22`
- transpiled_two_qubit_gate_count: `4`
- transpilation_options: `{'approximation_degree': 1.0, 'initial_layout': [90, 89], 'layout_method': 'sabre', 'optimization_level': 3, 'routing_method': 'sabre', 'seed_transpiler': 1729}`
- job_id: `d7qph0cf3ras73b64dcg`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `26.414305374986725`
- usage_estimation: `{'quantum_seconds': 26.095501966}`
- job_metrics: `{'caller': 'qiskit_ibm_runtime~estimator.py', 'qiskit_version': 'qiskit_ibm_runtime-0.46.1,qiskit-2.3.0*,qiskit_aer-0.17.2*,qiskit_nature-0.7.2*', 'timestamps': {'created': '2026-05-02T06:24:01.966391Z', 'finished': '2026-05-02T06:24:33.797303Z', 'running': '2026-05-02T06:24:03.037782Z'}, 'bss': {'seconds': 23}, 'usage': {'quantum_seconds': 23, 'seconds': 23}}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'budget_strategy': 'h2_hardware_precision_push', 'confirmation_message': 'This hardware optimization campaign can submit real IBM Runtime jobs and consume monthly quota.', 'default_shots': 8192, 'grouping_policy': 'hardware_aware_grouping', 'layout_method': 'sabre', 'layout_strategy': 'min_weighted_error', 'max_budgeted_shots': 8192, 'max_execution_seconds': 420.0, 'optimization_level': 3, 'precision_target': 0.015, 'requires_action_time_confirmation': True, 'resilience_level': 2, 'routing_method': 'sabre', 'seed_transpiler': 1729, 'submit_real_job': True, 'wait_for_result': False}`
- returned_job_metadata: `{'evs': [-1.834134672985554], 'stds': [0.0035206171087625226], 'metadata': {'shots': 8192, 'target_precision': 0.011048543456039804, 'circuit_metadata': {}, 'resilience': {'zne': {'extrapolator': ['multiple']}}, 'num_randomizations': 32}}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'backend_name': 'ibm_kingston', 'backend_selection_strategy': 'min_weighted_error', 'candidates': [{'backend_name': 'ibm_kingston', 'entangling_score': 0.0011204659863697508, 'layout_score': 0.005148786298869751, 'pending_jobs': 0, 'readout_score': 0.008056640625, 'selected_layout': [90, 89]}, {'backend_name': 'ibm_marrakesh', 'entangling_score': 0.0012370335354305595, 'layout_score': 0.0058757054104305595, 'pending_jobs': 0, 'readout_score': 0.00927734375, 'selected_layout': [19, 15]}, {'backend_name': 'ibm_fez', 'entangling_score': 0.001510689689632888, 'layout_score': 0.006759713127132888, 'pending_jobs': 6, 'readout_score': 0.010498046875, 'selected_layout': [23, 22]}], 'circuit_qubits': 2, 'last_polled_at': '2026-05-02T06:36:48.579782+00:00', 'last_polled_status': 'DONE', 'layout_strategy': 'min_weighted_error', 'operator_qubits': 2, 'parameter_count': 1, 'runtime_package_version': '0.46.1', 'selected_backend': 'ibm_kingston'}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'entanglement': 'full', 'entanglement_blocks': 'cz', 'kind': 'puccd', 'reps': 1, 'rotation_blocks': ['ry', 'rz']}`
- initial_point_strategy: `zeros`
- parameter_count: `1`
- converged: `True`
- iterations: `23`
- evaluations: `23`
- final_objective_energy: `-1.852388173092` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Mitigation

- symmetry_check: `{'performed': False, 'requested': True, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'method': 'none', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- zne: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- pec: `{'method': 'placeholder', 'performed': False, 'requested': False, 'status': 'placeholder_not_implemented'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-02T06:24:01.807554+00:00`
- Wall time (s): `26.53889541598619`
- Git commit: `adb7dad10aed10ad7b2c73d1a778c9bce42840ed`
- Git commit short: `adb7dad10aed`
- Git branch: `codex/qcchem-visual-workbench`
- Git describe: `adb7dad-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 60, 'untracked': 171}`
- Workspace fingerprint: `d1ce3884aafb5fa6f79330887f59649c03c25ad01d72cea9c22a7ac7a1176dba`
- Dependency versions: `{'numpy': '2.4.1', 'pyscf': '2.12.1', 'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_aer': '0.17.2', 'qiskit_nature': '0.7.2', 'scipy': '1.17.0'}`
- Seed: `1729`
- Source config: `/Users/a0000/QCchem/configs/h2_hardware_precision_push.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/h2_hardware_precision_push.yaml
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Prepared measurement plan: groups=2, cost=8890
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/exact_result.json
- Computed empirical calibration: wall_time=0.041s, measured_cost=None
- Persisted runtime submission sidecar after job submit: d7qph0cf3ras73b64dcg
- Runtime submission attempt recorded: submitted
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192/report.md
- Run completed
