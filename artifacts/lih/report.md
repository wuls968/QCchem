# QCchem Report: LiH

## Energy Summary

- electronic_energy: `-8.874531649358` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.882324378883` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-8.874531649358` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-8.874531649358` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020459609075` Hartree
- energy_units: `Hartree`
- constant_energy_correction: `0.000000000000` Hartree

## Field Definitions

- `solver_energy` is the raw energy returned by the configured solver on the mapped qubit Hamiltonian.
- `exact_ground_energy` is the raw exact-diagonalization energy of that same mapped Hamiltonian.
- `electronic_energy` is QCchem's corrected electronic energy after adding any non-nuclear Hamiltonian constants, such as active-space offsets.
- `total_energy` is the physical total energy reported by QCchem and must satisfy `electronic_energy + nuclear_repulsion_energy`.
- `hf_reference_energy` is the Hartree-Fock total reference energy exposed by Qiskit Nature.
- `correlation_energy` is `total_energy - hf_reference_energy` and therefore measures post-HF improvement in the total-energy convention.

## Benchmark

- exact_available: `True`
- exact_electronic_energy: `-8.874531649358` Hartree
- exact_total_energy: `-7.882324378883` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `0.0`
- absolute_error_threshold: `1e-10`
- relative_error_threshold: `1e-10`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(2, 2)`
- Num spatial orbitals: `6`
- Active space: `None`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475}`

## Mapping

- Mapping kind: `bravyi_kitaev`
- Qubit count: `12`
- Fermionic Hamiltonian terms: `1860`
- Qubit Hamiltonian terms: `631`

## Solver

- Solver kind: `exact`
- Optimizer: `{}`
- Ansatz: `{}`
- Initial point: `n/a`
- Converged: `True`
- Iterations: `1`
- Evaluations: `1`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`

## Provenance

- Schema version: `qcchem.result.v0.1-alpha`
- Timestamp: `2026-04-10T14:22:13.679902+00:00`
- Wall time (s): `1.261037625001336`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1'}`
- Seed: `11`
- Source config: `configs/lih.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih/run.log`

## Log Summary

- Loading config from configs/lih.yaml
- Building electronic structure problem
- Applying mapping: bravyi_kitaev
- Skipping backend construction for solver: exact
- Running solver: exact
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih/exact_result.json
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih/report.md
- Run completed
