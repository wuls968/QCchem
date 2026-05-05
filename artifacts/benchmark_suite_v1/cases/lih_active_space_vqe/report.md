# QCchem Report: LiH-active-vqe

## Verification

- verification_status: `unstable`

## Energy Summary

- electronic_energy: `-8.854347436815` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.862140166340` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058127868038` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000275396532` Hartree
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
- absolute_error: `0.001245019760` Hartree
- relative_error: `0.0011766376560209233`
- statistical_error: `0.000169049816` Hartree
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
- Active space metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': None}`
- Transformers applied: `['ActiveSpaceTransformer']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475, 'ActiveSpaceTransformer': -7.796219568777051}`
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

## Reduction Audit

- original_num_particles: `(2, 2)`
- original_num_spatial_orbitals: `6`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['ActiveSpaceTransformer']`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': None}`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475, 'ActiveSpaceTransformer': -7.796219568777051}`
- constant_energy_correction: `-7.796219568777` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `-6.804012298302` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Variational Result

- available: `True`
- solver_kind: `vqe`
- optimizer: `{'kind': 'COBYLA', 'maxiter': 120, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `36`
- evaluations: `36`
- final_objective_energy: `-1.058127868038` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `8193`
- num_repeats: `5`
- seed: `211`
- repeat_seeds: `[100211, 100212, 100213, 100214, 100215]`
- sampled_solver_energy_mean: `-1.056871515377` Hartree
- sampled_solver_energy_std: `0.000378006880` Hartree
- sampled_electronic_energy_mean: `-8.853091084154` Hartree
- sampled_total_energy_mean: `-7.860883813679` Hartree
- standard_error: `0.000169049816` Hartree
- confidence_interval_low: `-1.057202853016` Hartree
- confidence_interval_high: `-1.056540177738` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'none'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.4-alpha`
- Timestamp: `2026-04-11T06:58:37.484104+00:00`
- Wall time (s): `4.396389166002336`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `211`
- Source config: `/Users/a0000/QCchem/configs/lih_active_vqe.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/run.log`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_active_vqe.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/exact_result.json
- Collected repeated shot-based sampling statistics
- Writing JSON result to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_active_space_vqe/report.md
- Run completed
