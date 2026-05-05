# QCchem Report: LiH

## Verification

- verification_status: `validated`

## Energy Summary

- electronic_energy: `-8.874531649359` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.882324378884` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-8.874531649359` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-8.874531649359` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020459609075` Hartree
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
- solver_hamiltonian_energy: `-8.874531649359` Hartree
- electronic_energy: `-8.874531649359` Hartree
- total_energy: `-7.882324378884` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-8.874531649359` Hartree
- exact_total_energy: `-7.882324378884` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `8.006537852749232e-16`
- statistical_error: `None`
- absolute_error_threshold: `1e-10`
- relative_error_threshold: `1e-10`
- within_uncertainty: `None`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(2, 2)`
- Num spatial orbitals: `6`
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475}`
- Electronic constant correction: `0.000000000000` Hartree

## Mapping

- Mapping kind: `bravyi_kitaev`
- Qubit count: `12`
- Fermionic Hamiltonian terms: `1860`
- Qubit Hamiltonian terms: `631`

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
- reduced_num_particles: `(2, 2)`
- reduced_num_spatial_orbitals: `6`
- transformers_applied: `[]`
- active_space_metadata: `None`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `0.992207270475` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.4-alpha`
- Timestamp: `2026-04-11T06:58:33.083901+00:00`
- Wall time (s): `0.7226312920029159`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `11`
- Source config: `/Users/a0000/QCchem/configs/lih.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/run.log`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih.yaml
- Building electronic structure problem
- Applying mapping: bravyi_kitaev
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/exact_result.json
- Writing JSON result to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/benchmark_suite_v1/cases/lih_exact_reference/report.md
- Run completed
