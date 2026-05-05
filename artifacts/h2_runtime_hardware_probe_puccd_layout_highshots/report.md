# QCchem Report: H2-runtime-hardware-probe-puccd-layout-highshots

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Verification

- verification_status: `exploratory`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `exploratory`
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
- total_energy: `-1.137283834488` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `variational_result`
- exact_electronic_energy: `-1.852388173570` Hartree
- exact_total_energy: `-1.137283834488` Hartree
- absolute_error: `0.000000000477` Hartree
- relative_error: `2.5777404748688724e-10`
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
- Seed: `1031`
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
- absolute_error_hartree: `0.000000000477` Hartree
- absolute_error_kcal_mol: `2.996342659409494e-07`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Chemical Accuracy (Runtime-Derived)

- available: `True`
- assessment_target: `runtime_derived`
- status: `exploratory`
- meets_chemical_accuracy: `False`
- absolute_error_hartree: `0.053321345209` Hartree
- absolute_error_kcal_mol: `33.45964928522584`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.024100003131` Hartree
- notes: `['Does not meet chemical accuracy threshold.', 'Observed error exceeds 95% statistical uncertainty.']`

## Runtime Options

- enabled: `True`
- service: `ibm_quantum_platform`
- instance: `None`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- precision_target: `0.01`
- max_budgeted_shots: `8192`
- max_execution_seconds: `420.0`
- calibration_strategy: `chemical_accuracy_push`
- resilience_level: `2`
- grouping_policy: `default`
- session_recommendation: `recommended`
- batch_recommendation: `recommended`
- low_rank_workload: `False`
- measurement_group_count: `5`
- estimated_shot_cost: `50000.0`
- options: `{'backend_name': 'ibm_kingston', 'optimization_level': 3, 'layout_strategy': 'min_weighted_error', 'layout_method': 'sabre', 'routing_method': 'sabre', 'seed_transpiler': 1031, 'submit_real_job': False, 'wait_for_result': False}`
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
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'publication'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `runtime_estimator`
- low_rank_aware: `False`
- term_count: `15`
- group_count: `5`
- estimated_shot_cost: `50000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `5`
- uncompressed_estimated_shot_cost: `50000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.07565074999729404`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000477` Hartree
- estimated_measurement_cost: `50000.0`
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
- selected_layout: `[44, 45, 46, 47]`
- layout_score: `0.010647387528702562`
- transpiled_depth: `146`
- transpiled_two_qubit_gate_count: `42`
- transpilation_options: `{'approximation_degree': 1.0, 'initial_layout': [44, 45, 46, 47], 'layout_method': 'sabre', 'optimization_level': 3, 'routing_method': 'sabre', 'seed_transpiler': 1031}`
- job_id: `d7h01qnb91ec73au3eag`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `None`
- usage_estimation: `{'quantum_seconds': 45.164042271}`
- job_metrics: `{'caller': 'qiskit_ibm_runtime~estimator.py', 'qiskit_version': 'qiskit_ibm_runtime-0.46.1,qiskit-2.3.0*,qiskit_aer-0.17.2*,qiskit_nature-0.7.2*', 'timestamps': {'created': '2026-04-17T09:44:11.045556Z', 'finished': '2026-04-17T09:45:06.761281Z', 'running': '2026-04-17T09:44:11.960619Z'}, 'bss': {'seconds': 45}, 'usage': {'quantum_seconds': 45, 'seconds': 45}}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `exploratory`
- options_snapshot: `{'backend_name': 'ibm_kingston', 'budget_strategy': 'chemical_accuracy_push', 'grouping_policy': 'default', 'layout_method': 'sabre', 'layout_strategy': 'min_weighted_error', 'max_budgeted_shots': 8192, 'max_execution_seconds': 420.0, 'optimization_level': 3, 'precision_target': 0.01, 'resilience_level': 2, 'routing_method': 'sabre', 'seed_transpiler': 1031, 'submit_real_job': True, 'wait_for_result': True}`
- returned_job_metadata: `{'evs': [-1.799066828360334], 'stds': [0.02410000313087427], 'metadata': {'shots': 8192, 'target_precision': 0.011048543456039804, 'circuit_metadata': {}, 'resilience': {'zne': {'extrapolator': ['multiple']}}, 'num_randomizations': 32}}`
- result_provenance: `{'attempt_stage': 'result_retrieved', 'backend_name': 'ibm_kingston', 'circuit_qubits': 4, 'layout_strategy': 'min_weighted_error', 'operator_qubits': 4, 'parameter_count': 1, 'runtime_package_version': '0.46.1', 'last_polled_status': 'DONE', 'last_polled_at': '2026-04-17T09:46:57.943623+00:00'}`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'kind': 'puccd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
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
- Timestamp: `2026-04-17T09:47:01.079470+00:00`
- Wall time (s): `0.20554383299895562`
- Git commit: `316becdb4f870ebb1fa1a1446c4f22d8c2aabd2d`
- Git commit short: `316becdb4f87`
- Git branch: `master`
- Git describe: `316becd-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 23, 'untracked': 148}`
- Workspace fingerprint: `6de8b5f4576ab5d8fd53077624ea98e8d08600b85876e000e87fdd2e087079f0`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `1031`
- Source config: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/resolved_config.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/resolved_config.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=5, cost=50000
- Prepared runtime policy snapshot for service=ibm_quantum_platform
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/qcchem-runtime-collect-hj3x8rrv/exact_result.json
- Computed empirical calibration: wall_time=0.076s, measured_cost=None
- Runtime submission attempt recorded: runtime_submission_disabled
- Writing JSON result to /Users/a0000/QCchem/artifacts/qcchem-runtime-collect-hj3x8rrv/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/qcchem-runtime-collect-hj3x8rrv/report.md
- Run completed
