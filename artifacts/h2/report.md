# QCchem Report: H2

## Energy Summary

- electronic_energy: `-1.857275029080` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_energy: `-1.137306034631` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.857275029080` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020307037877` Hartree
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
- exact_electronic_energy: `-1.857275030202` Hartree
- exact_total_energy: `-1.137306035753` Hartree
- absolute_error: `0.000000001122` Hartree
- relative_error: `6.043245205382807e-10`
- absolute_error_threshold: `1e-06`
- relative_error_threshold: `1e-06`
- meets_threshold: `True`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space: `None`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.7199689944489797}`

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `15`

## Solver

- Solver kind: `vqe`
- Optimizer: `{'kind': 'COBYLA', 'maxiter': 100, 'tol': None}`
- Ansatz: `{'kind': 'uccsd', 'rotation_blocks': ['ry', 'rz'], 'entanglement_blocks': 'cz', 'entanglement': 'full', 'reps': 1}`
- Initial point: `zeros`
- Converged: `True`
- Iterations: `42`
- Evaluations: `42`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`

## Provenance

- Schema version: `qcchem.result.v0.1-alpha`
- Timestamp: `2026-04-10T14:22:13.326110+00:00`
- Wall time (s): `0.9122154590004357`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1'}`
- Seed: `7`
- Source config: `configs/h2.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2/run.log`

## Log Summary

- Loading config from configs/h2.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Preparing backend: statevector
- Running solver: vqe
- Computing exact baseline by diagonalization
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2/exact_result.json
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2/report.md
- Run completed
