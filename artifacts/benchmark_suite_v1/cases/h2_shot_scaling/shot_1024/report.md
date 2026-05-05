# QCchem Report: H2-shot

## Verification

- verification_status: `unstable`

## Energy Summary

- electronic_energy: `-1.857736820651` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_energy: `-1.137767826202` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.857736820651` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020768829448` Hartree
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
- absolute_error: `0.007512043589` Hartree
- relative_error: `0.004044658688987192`
- statistical_error: `0.001492106067` Hartree
- absolute_error_threshold: `0.05`
- relative_error_threshold: `0.05`
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
- Shots: `1024`
- Seed: `101`
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
- optimizer: `{'kind': 'COBYLA', 'maxiter': 80, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `34`
- evaluations: `34`
- final_objective_energy: `-1.857736820651` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `1024`
- num_repeats: `5`
- seed: `101`
- repeat_seeds: `[100101, 100102, 100103, 100104, 100105]`
- sampled_solver_energy_mean: `-1.849762986614` Hartree
- sampled_solver_energy_std: `0.003336450595` Hartree
- sampled_electronic_energy_mean: `-1.849762986614` Hartree
- sampled_total_energy_mean: `-1.129793992165` Hartree
- standard_error: `0.001492106067` Hartree
- confidence_interval_low: `-1.852687514505` Hartree
- confidence_interval_high: `-1.846838458722` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'none'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.4-alpha`
- Timestamp: `2026-04-11T06:58:39.205699+00:00`
- Wall time (s): `1.5251751670002704`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `101`
- Source config: `/Users/a0000/QCchem/configs/h2_shot.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/run.log`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/h2_shot.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/exact_result.json
- Collected repeated shot-based sampling statistics
- Writing JSON result to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/h2_shot_scaling/shot_1024/report.md
- Run completed
