# QCchem Report: H2-hardware-ready

## Verification

- verification_status: `unstable`

## Energy Summary

- electronic_energy: `-1.856357872407` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_energy: `-1.136388877958` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.856357872407` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.019389881204` Hartree
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
- absolute_error: `0.002789501732` Hartree
- relative_error: `0.0015019325011933528`
- statistical_error: `0.000365978694` Hartree
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
- Shots: `16384`
- Seed: `303`
- Repetitions: `7`
- Abelian grouping: `False`
- Noise enabled: `False`
- Runtime enabled: `True`

## Backend Capability

- backend_kind: `shot_estimator`
- statevector: `False`
- shot_based: `True`
- exact_baseline: `True`
- runtime_ready: `True`
- session_ready: `True`
- batch_ready: `True`
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

## Runtime Options

- enabled: `True`
- service: `ibm_runtime_placeholder`
- instance: `None`
- runtime_ready: `True`
- session_ready: `True`
- batch_ready: `True`
- options: `{'optimization_level': 1, 'resilience_level': 0}`
- provenance: `{'adapter': 'runtime_ready_placeholder', 'remote_execution_configured': False, 'session_mode_requested': True, 'batch_mode_requested': True}`

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
- optimizer: `{'kind': 'COBYLA', 'maxiter': 60, 'tol': None}`
- ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- initial_point_strategy: `zeros`
- parameter_count: `3`
- converged: `True`
- iterations: `33`
- evaluations: `33`
- final_objective_energy: `-1.856357872407` Hartree
- optimizer_message: `Return from COBYLA because the trust region radius reaches its lower bound.`

## Sampled Result

- available: `True`
- backend_kind: `shot_estimator`
- shots: `16384`
- num_repeats: `7`
- seed: `303`
- repeat_seeds: `[100303, 100304, 100305, 100306, 100307, 100308, 100309]`
- sampled_solver_energy_mean: `-1.854485528471` Hartree
- sampled_solver_energy_std: `0.000968288609` Hartree
- sampled_electronic_energy_mean: `-1.854485528471` Hartree
- sampled_total_energy_mean: `-1.134516534022` Hartree
- standard_error: `0.000365978694` Hartree
- confidence_interval_low: `-1.855202846711` Hartree
- confidence_interval_high: `-1.853768210231` Hartree

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': True, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.4-alpha`
- Timestamp: `2026-04-11T06:56:55.932569+00:00`
- Wall time (s): `3.6423247499988065`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `31`
- Source config: `configs/h2_hardware_ready.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_hardware_ready/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_hardware_ready/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_hardware_ready/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_hardware_ready/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_hardware_ready/run.log`

## Log Summary

- Loading config from configs/h2_hardware_ready.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Preparing backend: shot_estimator
- Running solver: vqe
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_hardware_ready/exact_result.json
- Collected repeated shot-based sampling statistics
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_hardware_ready/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_hardware_ready/report.md
- Run completed
