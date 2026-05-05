# QCchem Report: LiH-active-vqe

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `LiH-active-vqe`
- basis: `sto3g`
- method: `vqe / {'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- mapping_kind: `jordan_wigner`
- num_qubits: `4`
- verification_status: `unstable`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.001935905334` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `shot_estimator`

## Hero

- headline_total_energy: `-7.861060248769` Hartree
- headline_correlation_energy: `0.000804521040` Hartree
- headline_absolute_error: `0.001935905334` Hartree
- comparison_target: `sampled_result`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'lih_active_vqe', 'molecule_name': 'LiH-active-vqe', 'basis': 'sto3g', 'backend_kind': 'shot_estimator', 'mapping_kind': 'jordan_wigner'}`
- primary_scientific_claim: `LiH-active-vqe stays within chemical accuracy against sampled_result for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 0.001935905334354393, 'units': 'Hartree', 'threshold': 0.025, 'comparison_target': 'sampled_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `unstable`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `LiH-active-vqe stays within chemical accuracy against sampled_result for the defended local execution path.`
- trust_tier: `unstable`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `manual` / transformers=`['ActiveSpaceTransformer']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'sampled_result', 'absolute_error': 0.001935905334354393, 'relative_error': 0.0018295766771139045, 'statistical_error': 9.224491196077601e-05, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 3.9928697089781053, 'shots': 8192, 'measurement_strategy': 'default', 'measurement_group_count': 9, 'measured_shot_usage': 368685.0, 'runtime_backend': None, 'runtime_job_id': None}`
- trust_judgment: `{'verification_status': 'unstable', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': [], 'scientific_risk_notes': []}`
- provenance_timestamp: `2026-05-05T16:52:38.203584+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/QCchem/artifacts/lih_active_vqe`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.001068584670` Hartree
- threshold_hartree: `0.0016`
- distance_to_chemical_accuracy: `0.0`
- statistical_error: `0.000092244912` Hartree
- notes: `['Meets chemical accuracy threshold.', 'Observed error exceeds 95% statistical uncertainty.']`

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

- verification_status: `unstable`

## Validation Boundary

- Module Origin: `core`
- Capability Tier: `unstable`
- Verification Notes: `[]`
- Scientific Risk Notes: `[]`

## Energy Summary

- electronic_energy: `-8.853267519244` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.861060248769` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.057047950467` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `0.000804521040` Hartree
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
- comparison_target: `sampled_result`
- exact_electronic_energy: `-8.854336103914` Hartree
- exact_total_energy: `-7.862128833439` Hartree
- absolute_error: `0.001935905334` Hartree
- relative_error: `0.0018295766771139045`
- statistical_error: `0.000092244912` Hartree
- absolute_error_threshold: `0.025`
- relative_error_threshold: `0.025`
- within_uncertainty: `False`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- Transformers applied: `['ActiveSpaceTransformer']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475, 'ActiveSpaceTransformer': -7.796219568777052}`
- Electronic constant correction: `-7.796219568777` Hartree

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `72`
- Qubit Hamiltonian terms: `27`

## Backend

- Backend kind: `shot_estimator`
- Precision: `None`
- Shots: `8192`
- Seed: `211`
- Repetitions: `5`
- Abelian grouping: `False`
- Noise enabled: `False`
- Runtime enabled: `False`

## Backend Capability

- backend_kind: `shot_estimator`
- statevector: `False`
- shot_based: `True`
- exact_baseline: `True`
- runtime_ready: `False`
- session_ready: `False`
- batch_ready: `False`
- mitigation_ready: `True`
- noise_model_ready: `True`
- supports_grouping: `False`
- supports_repetitions: `True`
- supports_confidence_metrics: `True`

## Execution Policy

- name: `benchmark`
- default_shots: `4096`
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
- absolute_error_hartree: `0.001068584670` Hartree
- absolute_error_kcal_mol: `0.670547004087228`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `0.000092244912` Hartree
- notes: `['Meets chemical accuracy threshold.', 'Observed error exceeds 95% statistical uncertainty.']`

## Reduction Audit

- original_num_particles: `(2, 2)`
- original_num_spatial_orbitals: `6`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['ActiveSpaceTransformer']`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [], 'active_orbitals_original': []}`
- selection_mode: `manual`
- selection_reason: `Manual active-space selection from user-provided electron/orbital counts; Qiskit Nature chooses the orbital window.`
- selected_active_orbitals: `[]`
- selected_active_orbitals_original: `[]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475, 'ActiveSpaceTransformer': -7.796219568777052}`
- constant_energy_correction: `-7.796219568777` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `-6.804012298302` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Reduction Plan

- enabled: `True`
- mode: `manual`
- strategy: `manual_active_space`
- recommended_changes: `{'active_space': {'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': None}}`
- notes: `['Manual active-space reduction is configured.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `27`
- group_count: `9`
- estimated_shot_cost: `73737.0`
- runtime_precision_target: `0.011048543456039804`
- uncompressed_group_count: `9`
- uncompressed_estimated_shot_cost: `73737.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.0110485.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `3.339940249978099`
- measured_shot_usage: `368685.0`
- precision_target: `0.011048543456039804`
- achieved_error: `0.001935905334` Hartree
- estimated_measurement_cost: `73737.0`
- estimated_vs_measured_cost: `0.2`
- reference_target: `sampled_result`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.', 'Achieved error remains outside the reported statistical uncertainty band.']`

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
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 120, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `34`
- evaluations: `34`
- final_objective_energy: `-1.057047950467` Hartree
- optimizer_message: `Optimization terminated successfully.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `8193`
- num_repeats: `5`
- seed: `211`
- repeat_seeds: `[100211, 100212, 100213, 100214, 100215]`
- sampled_solver_energy_mean: `-1.056180629802` Hartree
- sampled_solver_energy_std: `0.000206265894` Hartree
- sampled_electronic_energy_mean: `-8.852400198579` Hartree
- sampled_total_energy_mean: `-7.860192928104` Hartree
- standard_error: `0.000092244912` Hartree
- confidence_interval_low: `-1.056361429830` Hartree
- confidence_interval_high: `-1.055999829775` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'none'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-05T16:52:38.203584+00:00`
- Wall time (s): `3.9928697089781053`
- Git commit: `adb7dad10aed10ad7b2c73d1a778c9bce42840ed`
- Git commit short: `adb7dad10aed`
- Git branch: `codex/qcchem-visual-workbench`
- Git describe: `adb7dad-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 61, 'untracked': 183}`
- Workspace fingerprint: `6711d3149d80ce8114c34c8253511fd470b8604759683db5467a607033db9095`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `211`
- Source config: `/Users/a0000/QCchem/configs/lih_active_vqe.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih_active_vqe/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih_active_vqe/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih_active_vqe/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih_active_vqe/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih_active_vqe/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/lih_active_vqe/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/lih_active_vqe/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/lih_active_vqe/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_active_vqe.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=9, cost=73737
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih_active_vqe/exact_result.json
- Collected repeated shot-based sampling statistics
- Computed empirical calibration: wall_time=3.340s, measured_cost=368685.0
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih_active_vqe/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih_active_vqe/report.md
- Run completed
