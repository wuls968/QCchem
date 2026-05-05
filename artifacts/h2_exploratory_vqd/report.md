# QCchem Report: H2-exploratory-vqd

## Verification

- verification_status: `exploratory`

## Validation Boundary

- module_origin: `exploratory`
- capability_tier: `exploratory`
- verification_notes: `['validation_scope=vqd skeleton']`
- scientific_risk_notes: `['Current VQD path delegates to QCchem VQE and does not validate excited-state energies.']`

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
- comparison_target: `variational_result`
- exact_electronic_energy: `-1.857275030202` Hartree
- exact_total_energy: `-1.137306035753` Hartree
- absolute_error: `0.000000001122` Hartree
- relative_error: `6.043212925810682e-10`
- statistical_error: `None`
- absolute_error_threshold: `1e-06`
- relative_error_threshold: `1e-06`
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

## Chemical Accuracy

- available: `True`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000001122` Hartree
- absolute_error_kcal_mol: `7.043110293148302e-07`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Reduction Audit

- original_num_particles: `(1, 1)`
- original_num_spatial_orbitals: `2`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `[]`
- active_space_metadata: `None`
- selection_mode: `none`
- selection_reason: `No active-space reduction requested.`
- selected_active_orbitals: `[]`
- selected_active_orbitals_original: `[]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.7199689944489797}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.719968994449` Hartree
- total_constant_correction: `0.719968994449` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Reduction Plan

- enabled: `True`
- mode: `disabled`
- strategy: `none`
- recommended_changes: `{}`
- notes: `['No reduction planning inputs were requested.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `default`
- grouping_policy: `default`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `15`
- group_count: `5`
- estimated_shot_cost: `50000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `5`
- uncompressed_estimated_shot_cost: `50000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Empirical Calibration

- available: `True`
- measured_wall_time_seconds: `0.38689725000222097`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000001122` Hartree
- estimated_measurement_cost: `50000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `variational_result`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-04-17T02:30:10.159878+00:00`
- Wall time (s): `0.5332100420018833`
- Git commit: `736be793ffdf01a8720042a39ea67d564358f2fa`
- Git commit short: `736be793ffdf`
- Git branch: `codex/qwen-integration`
- Git describe: `736be79-dirty`
- Git remote origin: `None`
- Repo root: `/Users/a0000/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 1, 'untracked': 85}`
- Workspace fingerprint: `91b91b40ff1503dbee6890609f773ad0fe4f33882d32259e2b9c8cef368cea6e`
- Dependency versions: `{'python': '3.11.11', 'qiskit': '2.3.0', 'qiskit_nature': '0.7.2', 'numpy': '2.4.1', 'scipy': '1.17.0', 'pyscf': '2.12.1', 'qiskit_aer': '0.17.2'}`
- Seed: `17`
- Source config: `configs/exploratory/h2_vqd.yaml`

## Artifacts

- result.json: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/result.json`
- exact_result.json: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/exact_result.json`
- report.md: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/report.md`
- resolved_config.yaml: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/resolved_config.yaml`
- run.log: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/run.log`
- calibration.json: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/calibration.json`
- calibration_report.md: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/calibration_report.md`
- runtime_submission.json: `/Users/a0000/QCchem/artifacts/h2_exploratory_vqd/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from configs/exploratory/h2_vqd.yaml
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=5, cost=50000
- Preparing backend: statevector
- Running solver: vqd
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/QCchem/artifacts/h2_exploratory_vqd/exact_result.json
- Computed empirical calibration: wall_time=0.387s, measured_cost=None
- Writing JSON result to /Users/a0000/QCchem/artifacts/h2_exploratory_vqd/result.json
- Writing Markdown report to /Users/a0000/QCchem/artifacts/h2_exploratory_vqd/report.md
- Run completed
