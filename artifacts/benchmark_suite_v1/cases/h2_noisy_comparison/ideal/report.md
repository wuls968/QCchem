# QCchem Report: H2-noisy

## Verification

- verification_status: `unstable`

## Energy Summary

- electronic_energy: `-1.858123213164` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_energy: `-1.138154218715` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.858123213164` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.021155221961` Hartree
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
- solver_hamiltonian_energy: `-1.857275030202` Hartree
- electronic_energy: `-1.857275030202` Hartree
- total_energy: `-1.137306035753` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `sampled_result`
- exact_electronic_energy: `-1.857275030202` Hartree
- exact_total_energy: `-1.137306035753` Hartree
- absolute_error: `0.006976892181` Hartree
- relative_error: `0.0037565207453886225`
- statistical_error: `0.002059519643` Hartree
- absolute_error_threshold: `0.5`
- relative_error_threshold: `0.5`
- within_uncertainty: `False`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.7199689944489797}`
- Electronic constant correction: `0.000000000000` Hartree

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `15`

## Backend

- Backend kind: `shot_estimator`
- Precision: `None`
- Shots: `2048`
- Seed: `515`
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

- name: `hardware_ready`
- default_shots: `16384`
- default_repetitions: `7`
- exact_baseline_required: `True`
- confidence_rule: `exact baseline preferred and repeated sampling mandatory`
- mitigation_posture: `symmetry-check and readout-mitigation placeholders enabled`
- runtime_ready_expected: `True`
- session_ready_expected: `True`
- batch_ready_expected: `True`
- noise_ready_expected: `True`

## Reduction Audit

- original_num_particles: `(1, 1)`
- original_num_spatial_orbitals: `2`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `[]`
- active_space_metadata: `None`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.7199689944489797}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_constant_correction: `0.719968994449` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 40, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `36`
- evaluations: `36`
- final_objective_energy: `-1.858123213164` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `2049`
- num_repeats: `5`
- seed: `515`
- repeat_seeds: `[100515, 100516, 100517, 100518, 100519]`
- sampled_solver_energy_mean: `-1.850298138022` Hartree
- sampled_solver_energy_std: `0.004605225922` Hartree
- sampled_electronic_energy_mean: `-1.850298138022` Hartree
- sampled_total_energy_mean: `-1.130329143573` Hartree
- standard_error: `0.002059519643` Hartree
- confidence_interval_low: `-1.854334796521` Hartree
- confidence_interval_high: `-1.846261479522` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': True, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.4-alpha`
- Timestamp: `2026-04-11T06:58:32.357655+00:00`
- Wall time (s): `1.6697241250003572`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `515`
- Source config: `/Users/a0000/QCchem/configs/h2_noisy.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/run.log`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/h2_noisy.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/exact_result.json
- Collected repeated shot-based sampling statistics
- Writing JSON result to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_noisy_comparison/ideal/report.md
- Run completed
