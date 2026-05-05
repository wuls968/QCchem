# QCchem Report: H2-hardware-precision-push

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-hardware-precision-push`
- basis: `sto3g`
- method: `vqe / {'kind': 'succd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- mapping_kind: `parity_two_qubit_reduction`
- num_qubits: `2`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `runtime_attempt`
- benchmark_absolute_error: `0.000000000478` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-1.137283834011` Hartree
- headline_correlation_energy: `-0.020524526615` Hartree
- headline_absolute_error: `0.000000000478` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'preview', 'molecule_name': 'H2-hardware-precision-push', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'parity_two_qubit_reduction'}`
- primary_scientific_claim: `H2-hardware-precision-push stays within chemical accuracy against variational_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 4.77500483597737e-10, 'units': 'Hartree', 'threshold': 0.0016, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `runtime_attempt`
- trust_tier: `exploratory`
- recommended_action: `collect_runtime_result`

## Claim

- primary_scientific_claim: `H2-hardware-precision-push stays within chemical accuracy against variational_result for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_runtime_result`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 4.77500483597737e-10, 'relative_error': 2.577756057887078e-10, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.9819750000024214, 'shots': None, 'measurement_strategy': 'hardware_precision_push', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': 'runtime_attempt', 'verification_notes': [], 'scientific_risk_notes': []}`
- provenance_timestamp: `2026-05-02T06:37:04.707542+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview`

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
- hardware_evidence_tier: `runtime_attempt`
- service: `ibm_quantum_platform`
- provider: `None`
- backend_name: `None`
- job_id: `None`
- verification_status: `exploratory`
- layout_strategy: `None`
- selected_layout: `[]`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`

## Verification

- verification_status: `exploratory`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `exploratory`
- Verification Notes: `[]`
- Scientific Risk Notes: `[]`

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
- relative_error: `2.577756057887078e-10`
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
- options: `{'optimization_level': 3, 'layout_strategy': 'min_weighted_error', 'layout_method': 'sabre', 'routing_method': 'sabre', 'seed_transpiler': 1729, 'submit_real_job': False, 'wait_for_result': False, 'requires_action_time_confirmation': True, 'confirmation_message': 'This hardware optimization campaign can submit real IBM Runtime jobs and consume monthly quota.'}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'remote_execution_configured': False, 'session_mode_requested': True, 'batch_mode_requested': False, 'low_rank_policy_applied': False, 'compression_method': None}`

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
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'hardware_ready'}`

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
- measured_wall_time_seconds: `0.33618816701346077`
- measured_shot_usage: `None`
- precision_target: `0.015`
- achieved_error: `0.000000000478` Hartree
- estimated_measurement_cost: `8890.0`
- estimated_vs_measured_cost: `None`
- reference_target: `variational_result`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Hardware Execution

- hardware_verified: `False`
- hardware_evidence_tier: `runtime_attempt`
- attempted: `True`
- submitted: `False`
- succeeded: `False`
- service: `ibm_quantum_platform`
- mode: `session`
- session_requested: `True`
- batch_requested: `False`
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
- submission_wall_time_seconds: `3.583001671358943e-06`
- usage_estimation: `{}`
- job_metrics: `{}`
- failure_category: `runtime_submission_disabled`
- failure_message: `Runtime submission is configured for preview only; no remote IBM job was requested.`
- verification_status: `exploratory`
- options_snapshot: `{'precision_target': 0.015, 'max_budgeted_shots': 8192, 'max_execution_seconds': 420.0, 'budget_strategy': 'h2_hardware_precision_push', 'resilience_level': 2, 'grouping_policy': 'hardware_aware_grouping', 'optimization_level': 3, 'layout_strategy': 'min_weighted_error', 'layout_method': 'sabre', 'routing_method': 'sabre', 'seed_transpiler': 1729, 'submit_real_job': False, 'wait_for_result': False, 'requires_action_time_confirmation': True, 'confirmation_message': 'This hardware optimization campaign can submit real IBM Runtime jobs and consume monthly quota.'}`
- returned_job_metadata: `{}`
- result_provenance: `{'attempt_stage': 'submission_disabled_before_service_init', 'real_submission_requested': False}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'kind': 'succd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `1`
- converged: `True`
- iterations: `23`
- evaluations: `23`
- final_objective_energy: `-1.852388173092` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'none'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-02T06:37:04.707542+00:00`
- Wall time (s): `0.9819750000024214`
- Git commit: `adb7dad10aed10ad7b2c73d1a778c9bce42840ed`
- Git commit short: `adb7dad10aed`
- Git branch: `codex/qcchem-visual-workbench`
- Git describe: `adb7dad-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 60, 'untracked': 171}`
- Workspace fingerprint: `b63a70d6f1a2463d501c9e5aac212b0bcd892b7073b9573f5e248c308606bb9e`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `1729`
- Source config: `/Users/a0000/QCchem/configs/h2_hardware_precision_push.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/h2_hardware_precision_push.yaml
- Building electronic structure problem
- Applying mapping: parity_two_qubit_reduction
- Prepared measurement plan: groups=2, cost=8890
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/exact_result.json
- Computed empirical calibration: wall_time=0.336s, measured_cost=None
- Runtime submission attempt recorded: runtime_submission_disabled
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_hardware_precision_push/candidates/parity_succd_layout/preview/report.md
- Run completed
