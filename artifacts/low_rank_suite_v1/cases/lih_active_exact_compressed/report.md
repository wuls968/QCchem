# QCchem Report: LiH-active-exact-compressed-cholesky

## Verification

- verification_status: `validated`

## Energy Summary

- electronic_energy: `-8.855345889473` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.863138618998` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.059126320696` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.059126320696` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.001273849189` Hartree
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
- absolute_error: `0.001009785559` Hartree
- relative_error: `0.000128436658874633`
- statistical_error: `None`
- absolute_error_threshold: `0.005`
- relative_error_threshold: `0.005`
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
- Qubit Hamiltonian terms: `12`

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

## Compressed vs Uncompressed

- available: `True`
- method: `modified_cholesky`
- rank: `2`
- threshold: `0.001`
- pre_term_count: `27`
- post_term_count: `12`
- compressed_solver_energy: `-1.059126320696` Hartree
- uncompressed_solver_energy: `-1.058116535137` Hartree
- compressed_total_energy: `-7.863138618998` Hartree
- uncompressed_total_energy: `-7.862128833439` Hartree
- absolute_error: `0.001009785559` Hartree
- relative_error: `0.000128436658874633`
- compressed_solve_wall_time_seconds: `0.0007770419997541467`
- uncompressed_solve_wall_time_seconds: `0.00045366700032900553`

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

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `estimator`
- low_rank_aware: `True`
- term_count: `12`
- group_count: `2`
- estimated_shot_cost: `20000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `9`
- uncompressed_estimated_shot_cost: `90000.0`
- cost_reduction_ratio: `0.2222222222222222`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Compressed Hamiltonian enabled low-rank-aware grouping and cost estimation.']`

## Empirical Calibration

- available: `True`
- measured_wall_time_seconds: `0.0007770419997541467`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.001009785559` Hartree
- estimated_measurement_cost: `20000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `compressed_vs_uncompressed`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-04-12T00:38:39.802535+00:00`
- Wall time (s): `0.1496407079994242`
- Git commit: `None`
- Git commit short: `None`
- Git branch: `None`
- Git describe: `None`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 0, 'untracked': 11}`
- Workspace fingerprint: `6dbd33d98aa74c5f3ada5cb43276ff3d0d9f2823a4fb5156155fe4548935408e`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `67`
- Source config: `/Users/a0000/QCchem/configs/lih_active_exact_compressed_cholesky.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/runtime_submission.json`
- qcschema.json: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/qcschema.json`
- result.h5: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/result.h5`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_active_exact_compressed_cholesky.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Constructed compressed mapped Hamiltonian via modified_cholesky
- Computed compression audit: modified_cholesky
- Prepared measurement plan: groups=2, cost=20000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/exact_result.json
- Computed compressed-vs-uncompressed execution comparison
- Computed empirical calibration: wall_time=0.001s, measured_cost=None
- Writing JSON result to /Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/low_rank_suite_v1/cases/lih_active_exact_compressed/report.md
- Run completed
