# QCchem Report: LiH-active-vqe-statevector

## Verification

- verification_status: `validated`

## Energy Summary

- electronic_energy: `-8.854336092497` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.862128822022` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058116523720` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000264052213` Hartree
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
- comparison_target: `variational_result`
- exact_electronic_energy: `-8.854336103914` Hartree
- exact_total_energy: `-7.862128833439` Hartree
- absolute_error: `0.000000011416` Hartree
- relative_error: `1.0789427198944505e-08`
- statistical_error: `None`
- absolute_error_threshold: `0.001`
- relative_error_threshold: `0.001`
- within_uncertainty: `None`
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
- Qubit Hamiltonian terms: `27`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `None`
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

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `27`
- group_count: `9`
- estimated_shot_cost: `90000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `9`
- uncompressed_estimated_shot_cost: `90000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Empirical Calibration

- available: `True`
- measured_wall_time_seconds: `0.3767470829998274`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000011416` Hartree
- estimated_measurement_cost: `90000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `variational_result`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 120, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `41`
- evaluations: `41`
- final_objective_energy: `-1.058116523720` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-04-12T00:38:40.323340+00:00`
- Wall time (s): `0.5103214169994317`
- Git commit: `None`
- Git commit short: `None`
- Git branch: `None`
- Git describe: `None`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 0, 'untracked': 11}`
- Workspace fingerprint: `1ec5934cfc7cb708d481d52768106479e488db21df98a653631cb14b77ae2cb6`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `73`
- Source config: `/Users/a0000/QCchem/configs/lih_active_vqe_statevector.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_active_vqe_statevector.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=9, cost=90000
- Preparing backend: statevector
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/exact_result.json
- Computed empirical calibration: wall_time=0.377s, measured_cost=None
- Writing JSON result to /Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_vqe_ideal_uncompressed/report.md
- Run completed
