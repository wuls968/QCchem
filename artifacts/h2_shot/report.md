# QCchem Report: H2-shot

## Energy Summary

- electronic_energy: `-1.856022641911` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_energy: `-1.136053647462` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.856022641911` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.019054650708` Hartree
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
- absolute_error: `0.008229104151` Hartree
- relative_error: `0.004430740745228576`
- statistical_error: `0.000896051906` Hartree
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
- Shots: `4096`
- Seed: `101`
- Repetitions: `5`
- Abelian grouping: `False`

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
- final_objective_energy: `-1.856022641911` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `4096`
- num_repeats: `5`
- seed: `101`
- repeat_seeds: `[100101, 100102, 100103, 100104, 100105]`
- sampled_solver_energy_mean: `-1.849045926051` Hartree
- sampled_solver_energy_std: `0.002003632973` Hartree
- sampled_electronic_energy_mean: `-1.849045926051` Hartree
- sampled_total_energy_mean: `-1.129076931602` Hartree
- standard_error: `0.000896051906` Hartree
- confidence_interval_low: `-1.850802187786` Hartree
- confidence_interval_high: `-1.847289664316` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'none'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.2-alpha`
- Timestamp: `2026-04-11T02:24:51.544928+00:00`
- Wall time (s): `2.1826615410027443`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `101`
- Source config: `configs/h2_shot.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_shot/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_shot/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_shot/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_shot/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_shot/run.log`

## Log Summary

- Loading config from configs/h2_shot.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact baseline by diagonalization
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_shot/exact_result.json
- Collected repeated shot-based sampling statistics
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_shot/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_shot/report.md
- Run completed
