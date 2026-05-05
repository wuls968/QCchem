# QCchem Report: LiH-embedding

## Verification

- verification_status: `validated`

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
- solver_hamiltonian_energy: `-8.874531649358` Hartree
- electronic_energy: `-8.874531649358` Hartree
- total_energy: `-7.882324378883` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-8.874531649358` Hartree
- exact_total_energy: `-7.882324378883` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `2.0016344631873138e-16`
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

- Mapping kind: `jordan_wigner`
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
- selection_mode: `none`
- selection_reason: `No active-space reduction requested.`
- selected_active_orbitals: `[]`
- selected_active_orbitals_original: `[]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `0.992207270475` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Embedding Audit

- enabled: `True`
- method: `dmet_skeleton`
- solver_plugin: `placeholder_fragment_solver`
- bath_threshold: `0.05`
- verification_status: `exploratory`
- environment_metadata: `{'environment_model': 'rhf_density_matrix', 'mean_field_energy': -7.861864769808649, 'num_fragments': 2}`
- notes: `['Current embedding path is a DMET-style skeleton built from PySCF mean-field density information.', 'Fragment solver execution remains a formal plugin interface in QCchem v0.5.']`

- fragment_name=`Li_fragment` atom_indices=`[0]` ao_count=`5` recommended_active_space=`{'num_spatial_orbitals': 6, 'num_electrons': 4}`
- fragment_name=`H_fragment` atom_indices=`[1]` ao_count=`1` recommended_active_space=`{'num_spatial_orbitals': 2, 'num_electrons': 2}`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.5-alpha`
- Timestamp: `2026-04-11T07:45:36.191468+00:00`
- Wall time (s): `0.8491074999910779`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `53`
- Source config: `/Users/a0000/QCchem/configs/lih_embedding.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih_embedding/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih_embedding/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih_embedding/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih_embedding/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih_embedding/run.log`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_embedding.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih_embedding/exact_result.json
- Computed embedding audit: dmet_skeleton
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih_embedding/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih_embedding/report.md
- Run completed
