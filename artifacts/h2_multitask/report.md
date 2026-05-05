# QCchem Report: H2-multitask

## Verification

- verification_status: `validated`

## Energy Summary

- electronic_energy: `-1.857275030202` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_energy: `-1.137306035753` Hartree
- hf_reference_energy: `-1.116998996754` Hartree
- solver_energy: `-1.857275030202` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.857275030202` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.020307038999` Hartree
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
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-1.857275030202` Hartree
- exact_total_energy: `-1.137306035753` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `2.8692953017411102e-15`
- statistical_error: `None`
- absolute_error_threshold: `1e-10`
- relative_error_threshold: `1e-10`
- within_uncertainty: `None`
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
- Shots: `8192`
- Seed: `909`
- Repetitions: `5`
- Abelian grouping: `False`

## Backend Capability

- backend_kind: `shot_estimator`
- statevector: `False`
- shot_based: `True`
- exact_baseline: `True`
- runtime_ready: `True`
- mitigation_ready: `True`
- noise_model_ready: `True`
- supports_grouping: `False`
- supports_repetitions: `True`
- supports_confidence_metrics: `True`

## Execution Policy

- name: `publication`
- default_shots: `8192`
- default_repetitions: `5`
- exact_baseline_required: `True`
- confidence_rule: `exact baseline and uncertainty reporting required`
- mitigation_posture: `symmetry-check required, readout placeholder allowed`
- runtime_ready_expected: `True`

## Excited-state Result

- method: `vqd`
- verification_status: `exploratory`
- notes: `['Requested excited-state method is treated as an exploratory interface; values come from an exact-spectrum proxy.']`

- state_index=`1` excitation_energy=`0.600935957199` Hartree verification_status=`exploratory`

## Property Result

- verification_status: `exploratory`

- property_name=`dipole_moment` method=`exact_expectation` implementation_status=`validated` value=`1.5553200949369739e-09` components=`{'x': 0.0, 'y': 0.0, 'z': -1.5553200949369739e-09}`
- property_name=`transition_dipole` method=`placeholder` implementation_status=`exploratory` value=`None` components=`{}`
- property_name=`oscillator_strength` method=`placeholder` implementation_status=`exploratory` value=`None` components=`{}`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.3-alpha`
- Timestamp: `2026-04-11T03:35:53.712723+00:00`
- Wall time (s): `0.1579262919985922`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `41`
- Source config: `configs/h2_multitask.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_multitask/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_multitask/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_multitask/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_multitask/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_multitask/run.log`

## Log Summary

- Loading config from configs/h2_multitask.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 2 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_multitask/exact_result.json
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_multitask/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_multitask/report.md
- Run completed
