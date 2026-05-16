# QCchem Report: H2-2D-lattice-QED-projected-exact

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-2D-lattice-QED-projected-exact`
- basis: `real_space_lattice`
- method: `statevector`
- mapping_kind: `lattice_qed:jordan_wigner`
- num_qubits: `12`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-5.385158493137` Hartree
- headline_correlation_energy: `None`
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2, 2], 'matter_modes': 4, 'gauge_links': 4}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_lattice_qed_2d_projected_exact', 'molecule_name': 'H2-2D-lattice-QED-projected-exact', 'basis': 'real_space_lattice', 'backend_kind': 'statevector', 'mapping_kind': 'lattice_qed:jordan_wigner', 'field_model_kind': 'lattice_qed'}`
- primary_scientific_claim: `H2-2D-lattice-QED-projected-exact lattice-QED result is gauge-audited finite-cutoff evidence compared against variational_result.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 0.0, 'units': 'Hartree', 'threshold': 1e-09, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-2D-lattice-QED-projected-exact lattice-QED result is gauge-audited finite-cutoff evidence compared against variational_result.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `qft_lattice_discretization` / transformers=`['LatticeQEDRealSpaceDiscretization']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 0.0, 'relative_error': 0.0, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.0977149170357734, 'shots': None, 'measurement_strategy': 'lattice_qed_2d_projected_exact', 'measurement_group_count': 1, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': 'lattice_qed'}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'exploratory', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lattice_qed_sparse_projected_exact', 'validation_scope=lattice_qed_finite_cutoff_exact_gate'], 'scientific_risk_notes': ['Sparse exact energy is exact only for the configured finite lattice/cutoff Hamiltonian.', 'Physical-sector projection is a finite-cutoff Gauss-law audit, not continuum chemistry accuracy.', 'Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.', 'Runtime circuits still act on the full qubit register unless explicitly transformed.']}`
- provenance_timestamp: `2026-05-15T13:03:17.281514+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact`

## Chemical Accuracy Frame

- available_assessments: `['local_execution']`
- best_available_assessment: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- threshold_hartree: `0.0016`
- distance_to_chemical_accuracy: `0.0`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Runtime Evidence

> Runtime evidence is surfaced explicitly so exported reports separate chemistry confidence from execution provenance.

- hardware_verified: `False`
- hardware_evidence_tier: `None`
- service: `None`
- provider: `None`
- backend_name: `None`
- job_id: `None`
- verification_status: `None`
- layout_strategy: `None`
- selected_layout: `[]`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`

## Verification

- verification_status: `exploratory`

## Validation Boundary

- Module Origin: `exploratory`
- Capability Tier: `exploratory`
- Verification Notes: `['validation_scope=lattice_qed_sparse_projected_exact', 'validation_scope=lattice_qed_finite_cutoff_exact_gate']`
- Scientific Risk Notes: `['Sparse exact energy is exact only for the configured finite lattice/cutoff Hamiltonian.', 'Physical-sector projection is a finite-cutoff Gauss-law audit, not continuum chemistry accuracy.', 'Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.', 'Runtime circuits still act on the full qubit register unless explicitly transformed.']`

## Energy Summary

- electronic_energy: `-6.606761775677` Hartree
- nuclear_repulsion_energy: `1.221603282540` Hartree
- total_energy: `-5.385158493137` Hartree
- hf_reference_energy: `None`
- solver_energy: `-6.606761775677` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-6.606761775677` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `None`
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
- solver_hamiltonian_energy: `-6.606761775677` Hartree
- electronic_energy: `-6.606761775677` Hartree
- total_energy: `-5.385158493137` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `variational_result`
- exact_electronic_energy: `-6.606761775677` Hartree
- exact_total_energy: `-5.385158493137` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `0.0`
- statistical_error: `None`
- absolute_error_threshold: `1e-09`
- relative_error_threshold: `1e-09`
- within_uncertainty: `None`
- meets_threshold: `True`

## Problem Summary

- Basis: `real_space_lattice`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `4`
- Active space metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2, 2], 'matter_modes': 4, 'gauge_links': 4}`
- Transformers applied: `['LatticeQEDRealSpaceDiscretization']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 1.221603282540386}`
- Electronic constant correction: `0.000000000000` Hartree

## Mapping

- Mapping kind: `lattice_qed:jordan_wigner`
- Qubit count: `12`
- Fermionic Hamiltonian terms: `4`
- Qubit Hamiltonian terms: `1`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `2043`
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

## Field Model Registry

- model_kind: `lattice_qed`
- registry_name: `finite_cutoff_lattice_qed`
- capability_tier: `exploratory`
- observables: `['gauss_law', 'physical_sector', 'electric_flux', 'electric_energy', 'wilson_loop', 'real_time_dynamics', 'trotter_resource_estimate', 'qpe_resource_estimate']`
- resource_estimate: `{}`
- error_budget: `{}`
- risk_notes: `['Finite-cutoff lattice-QED evidence is gauge-audited but not a continuum-limit chemistry claim.']`

## Lattice QED Field Model

> This section describes an exploratory finite-cutoff field Hamiltonian; exact baselines are for this discretized model.

- model: `lattice_qed_minimal_coupling`
- dimensions: `2`
- grid_shape: `[2, 2]`
- grid_spacing: `[0.75, 0.75]`
- boundary: `open`
- site_count: `4`
- link_count: `4`
- plaquette_count: `1`
- matter_mode_count: `4`
- gauge_group: `u1`
- gauge_electric_cutoff: `1`
- gauge_coupling: `1.0`
- total_qubits: `12`
- target_electrons: `2`
- term_counts_by_sector: `{'onsite': 3840, 'hopping': 4096, 'density_coulomb': 0, 'electric': 3840, 'magnetic_plaquette': 512, 'gauss_law_penalty': 4060, 'particle_number_penalty': 2560, 'padding_penalty': 2800}`
- constraints: `{'gauss_law_penalty': 10.0, 'particle_number_penalty': 10.0, 'padding_penalty': 50.0, 'enforce_physical_sector': True, 'target_charge_sector': 'neutral', 'gauss_law_tolerance': 1e-08, 'max_sector_enumeration_qubits': 12}`
- engine: `{'requested_representation': 'sparse_projected', 'actual_representation': 'sparse_projected', 'operator_representation': 'sparse_projected', 'auto_project_physical_sector': True, 'projected_dimension': 9, 'full_dimension': 4096, 'max_projected_dimension': 4096, 'max_full_qubits_for_dense': 10, 'materialize_pauli': 'never', 'pauli_materialization': 'skipped', 'dense_full_matrix_materialized': False, 'store_basis_indices': 'full', 'projector_tolerance': 1e-08, 'full_hamiltonian_nnz': 8704, 'sector_nnz': {'onsite': 3840, 'hopping': 4096, 'density_coulomb': 0, 'electric': 3840, 'magnetic_plaquette': 512, 'gauss_law_penalty': 4060, 'particle_number_penalty': 2560, 'padding_penalty': 2800}, 'projection_skipped_reason': None}`
- nuclear_charge_by_site: `[2.0, 0.0, 0.0, 0.0]`
- notes: `['Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.', 'Runtime circuits still act on the full qubit register unless explicitly transformed.']`

## Gauge Constraint Audit

> finite-cutoff QFT correctness means the configured lattice/cutoff Hamiltonian is internally audited; gauge-constraint consistency means Gauss-law generators and physical-sector checks are tracked; continuum chemistry accuracy is not claimed here.

- gauss_law_generators: `[{'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 119.73303637676612, 'hermitian': True, 'site_index': 0, 'target_charge': 0.0, 'diagonal_min': -4.0, 'diagonal_max': 1.0}, {'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 78.38367176906169, 'hermitian': True, 'site_index': 1, 'target_charge': 0.0, 'diagonal_min': -2.0, 'diagonal_max': 3.0}, {'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 78.38367176906169, 'hermitian': True, 'site_index': 2, 'target_charge': 0.0, 'diagonal_min': -2.0, 'diagonal_max': 3.0}, {'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 78.38367176906169, 'hermitian': True, 'site_index': 3, 'target_charge': 0.0, 'diagonal_min': -2.0, 'diagonal_max': 3.0}]`
- hamiltonian_gauge_commutator_norms: `[{'site_index': 0, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}, {'site_index': 1, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}, {'site_index': 2, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}, {'site_index': 3, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}]`
- physical_sector: `{'enumerated': True, 'physical_sector_dimension': 9, 'target_charge_sector': 'neutral', 'max_sector_enumeration_qubits': 12, 'basis_indices_preview': [937, 1446, 1701, 2409, 2454, 2664, 2709, 3173, 3218], 'reference_basis_index': 937, 'basis_index_count': 9, 'basis_hash': '2d6e8b0ed82a1f2862cc65149a6d85a7959b56c02d22bdc07c36657293dc23dd', 'basis_indices': [937, 1446, 1701, 2409, 2454, 2664, 2709, 3173, 3218], 'padding_state_rejection_count': 2800, 'tolerance': 1e-08, 'estimated_full_dimension': 4096, 'skipped_reason': None}`
- gauge_invariant_ansatz: `{'kind': 'gauss_law_preserving', 'generator_policy': 'electric_magnetic', 'selected_generator_count': 0, 'selected_generators': [], 'commutator_checks': [{'sector': 'hopping', 'selected': False, 'commutes_with_all_gauss_law_generators': False, 'max_commutator_norm': None, 'commutator_norms': [], 'pauli_term_count': -1, 'pauli_materialized': False, 'skipped_reason': 'ansatz_commutator_skipped_for_dynamics_resource_guard'}, {'sector': 'electric', 'selected': False, 'commutes_with_all_gauss_law_generators': False, 'max_commutator_norm': None, 'commutator_norms': [], 'pauli_term_count': -1, 'pauli_materialized': False, 'skipped_reason': 'ansatz_commutator_skipped_for_dynamics_resource_guard'}, {'sector': 'magnetic_plaquette', 'selected': False, 'commutes_with_all_gauss_law_generators': False, 'max_commutator_norm': None, 'commutator_norms': [], 'pauli_term_count': -1, 'pauli_materialized': False, 'skipped_reason': 'ansatz_commutator_skipped_for_dynamics_resource_guard'}]}`
- constraint_expectations: `{'available': True, 'gauss_law_tolerance': 1e-08, 'target_charge_sector': 'neutral', 'reference_basis_index': 937, 'reference_state_gauss_law_residuals': [0.0, 0.0, 0.0, 0.0], 'reference_state_max_abs_gauss_law': 0.0}`
- finite_cutoff_qft_correctness: `audited against the persisted finite Hamiltonian`
- gauge_constraint_consistency: `Gauss-law residuals and commutators are finite-cutoff checks`
- continuum_chemistry_accuracy: `not asserted by this exploratory artifact`

## QFT Physical-Sector Engine Audit

> This section separates sparse/projection correctness from hardware full-register circuits and from continuum chemistry accuracy.

- requested_representation: `sparse_projected`
- actual_representation: `sparse_projected`
- projected_dimension: `9`
- full_dimension: `4096`
- pauli_materialization: `skipped`
- dense_full_matrix_materialized: `False`
- basis_hash: `2d6e8b0ed82a1f2862cc65149a6d85a7959b56c02d22bdc07c36657293dc23dd`
- basis_index_count: `9`
- sparse_projection_correctness: `projected operators are finite-cutoff indexed submatrices when projection is active`
- runtime_circuit_boundary: `Runtime previews still target the full qubit register unless separately transformed`
- continuum_chemistry_accuracy: `not asserted by this exploratory engine audit`

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- absolute_error_kcal_mol: `0.0`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Reduction Audit

- original_num_particles: `(1, 1)`
- original_num_spatial_orbitals: `4`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `4`
- transformers_applied: `['LatticeQEDRealSpaceDiscretization']`
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2, 2], 'matter_modes': 4, 'gauge_links': 4}`
- selection_mode: `qft_lattice_discretization`
- selection_reason: `Molecule projected onto a finite real-space compact-U(1) lattice-QED grid.`
- selected_active_orbitals: `[0, 1, 2, 3]`
- selected_active_orbitals_original: `[0, 1, 2, 3]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 1.221603282540386}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `1.221603282540` Hartree
- total_constant_correction: `1.221603282540` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; electronic_energy = solver_energy + constant_energy_correction`

## Reduction Plan

- enabled: `True`
- mode: `audit_only`
- strategy: `executed_transformers`
- recommended_changes: `{}`
- notes: `['Reduction audit captures executed transformers even without explicit planning metadata.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `lattice_qed_2d_projected_exact`
- grouping_policy: `finite_cutoff_sparse_projected`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `1`
- group_count: `1`
- estimated_shot_cost: `10000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `1`
- uncompressed_estimated_shot_cost: `10000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'lattice_qed_2d_projected_exact'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.00020599999697878957`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `10000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `variational_result`
- notes: `['Measured wall time is taken from the executed solver path, not full workflow overhead.', 'Measured shot usage is derived from backend shots, repeat count, and measurement group count.']`

## Hardware Execution

- hardware_verified: `False`
- hardware_evidence_tier: `None`
- attempted: `None`
- submitted: `None`
- succeeded: `None`
- service: `None`
- mode: `None`
- session_requested: `None`
- batch_requested: `None`
- backend_name: `None`
- provider: `None`
- layout_strategy: `None`
- selected_layout: `[]`
- layout_score: `None`
- transpiled_depth: `None`
- transpiled_two_qubit_gate_count: `None`
- transpilation_options: `{}`
- job_id: `None`
- session_id: `None`
- batch_id: `None`
- submission_wall_time_seconds: `None`
- usage_estimation: `{}`
- job_metrics: `{}`
- failure_category: `None`
- failure_message: `None`
- verification_status: `None`
- options_snapshot: `{}`
- returned_job_metadata: `{}`
- result_provenance: `{}`

## Mitigation

- symmetry_check: `{'requested': True, 'performed': False, 'status': 'hook_available_not_implemented', 'strategy': 'parity_placeholder'}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- zne: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- pec: `{'requested': False, 'performed': False, 'status': 'placeholder_not_implemented', 'method': 'placeholder'}`
- applied_methods: `[]`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-15T13:03:17.281514+00:00`
- Wall time (s): `0.0977149170357734`
- Git commit: `164b7ff23843a5187d6aeba0c0bbd1bc2e3f287b`
- Git commit short: `164b7ff23843`
- Git branch: `HEAD`
- Git describe: `164b7ff-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/c397/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 15, 'untracked': 14}`
- Workspace fingerprint: `7b91cb72ce1578cb155d279fb436e6db85513f746bd82db9691aabd55faf7b4b`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `2043`
- Source config: `/Users/a0000/.codex/worktrees/c397/QCchem/configs/exploratory/h2_2d_lattice_qed_projected_exact.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/c397/QCchem/configs/exploratory/h2_2d_lattice_qed_projected_exact.yaml
- Building exploratory lattice-QED field Hamiltonian
- Constructed lattice-QED Hamiltonian: sites=4, links=4, qubits=12
- Prepared measurement plan: groups=1, cost=10000
- Skipping backend construction for solver: lattice_qed_sparse_exact
- Running solver: lattice_qed_sparse_exact
- Using sparse lattice-QED exact solver as the finite-cutoff exact baseline
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/exact_result.json
- Computed empirical calibration: wall_time=0.000s, measured_cost=None
- Writing JSON result to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2d_projected_exact/report.md
- Run completed
