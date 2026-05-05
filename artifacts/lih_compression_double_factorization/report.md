# QCchem Report: LiH-compression-double-factorization

## Verification

- verification_status: `validated`

## Energy Summary

- electronic_energy: `-8.854336103914` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_energy: `-7.862128833439` Hartree
- hf_reference_energy: `-7.861864769809` Hartree
- solver_energy: `-1.058116535137` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.058116535137` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `-0.000264063630` Hartree
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
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-8.854336103914` Hartree
- exact_total_energy: `-7.862128833439` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `2.0984891318835563e-16`
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
- Active space metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2]}`
- Transformers applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.992207270475, 'FreezeCoreTransformer': -7.796219568777051, 'ActiveSpaceTransformer': 0.0}`
- Electronic constant correction: `-7.796219568777` Hartree

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `4`
- Fermionic Hamiltonian terms: `72`
- Qubit Hamiltonian terms: `27`

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
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['FreezeCoreTransformer', 'ActiveSpaceTransformer']`
- active_space_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2, 'active_orbitals': [0, 1], 'active_orbitals_original': [1, 2]}`
- selection_mode: `manual`
- selection_reason: `Manual active-space selection from user-provided orbital list and electron counts.`
- selected_active_orbitals: `[0, 1]`
- selected_active_orbitals_original: `[1, 2]`
- frozen_core_orbitals: `[0]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.992207270475, 'FreezeCoreTransformer': -7.796219568777051, 'ActiveSpaceTransformer': 0.0}`
- constant_energy_correction: `-7.796219568777` Hartree
- nuclear_repulsion_energy: `0.992207270475` Hartree
- total_constant_correction: `-6.804012298302` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Compression Audit

- enabled: `True`
- method: `double_factorization`
- threshold: `1e-08`
- max_rank: `8`
- apply_to_solver: `False`
- original_num_qubits: `4`
- original_fermionic_term_count: `72`
- original_qubit_term_count: `27`
- compressed_term_count_estimate: `6`
- primary_rank: `3`
- secondary_rank: `6`
- reconstruction_error_frobenius: `1.2417518519112547e-16`
- verification_status: `exploratory`
- notes: `['Double-factorization audit estimated secondary rank from eigen-decomposed factor matrices.', 'Current QCchem v0.5 path is an audit/provenance route and does not yet feed a compressed Hamiltonian to the solver.']`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.5-alpha`
- Timestamp: `2026-04-11T07:45:35.447791+00:00`
- Wall time (s): `0.11025870899902657`
- Git commit: `None`
- Workspace dirty: `True`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `43`
- Source config: `/Users/a0000/QCchem/configs/lih_compression_double_factorization.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/lih_compression_double_factorization/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/lih_compression_double_factorization/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/lih_compression_double_factorization/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/lih_compression_double_factorization/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/lih_compression_double_factorization/run.log`

## Log Summary

- Loading config from /Users/a0000/QCchem/configs/lih_compression_double_factorization.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Computed compression audit: double_factorization
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/lih_compression_double_factorization/exact_result.json
- Writing JSON result to /Users/a0000/QCchem/artifacts/lih_compression_double_factorization/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/lih_compression_double_factorization/report.md
- Run completed
