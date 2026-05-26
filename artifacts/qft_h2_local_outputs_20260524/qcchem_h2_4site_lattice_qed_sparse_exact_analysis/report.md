# QCchem Report: H2-4site-lattice-QED-sparse-exact

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-4site-lattice-QED-sparse-exact`
- basis: `real_space_lattice`
- method: `statevector`
- mapping_kind: `lattice_qed:jordan_wigner`
- num_qubits: `10`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-7.484440614182` Hartree
- headline_correlation_energy: `None`
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `variational_result`
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [4], 'matter_modes': 4, 'gauge_links': 3}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'qcchem_h2_4site_lattice_qed_sparse_exact_analysis', 'molecule_name': 'H2-4site-lattice-QED-sparse-exact', 'basis': 'real_space_lattice', 'backend_kind': 'statevector', 'mapping_kind': 'lattice_qed:jordan_wigner', 'field_model_kind': 'lattice_qed'}`
- primary_scientific_claim: `H2-4site-lattice-QED-sparse-exact lattice-QED result is gauge-audited finite-cutoff evidence compared against variational_result.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 0.0, 'units': 'Hartree', 'threshold': 1e-09, 'comparison_target': 'variational_result'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-4site-lattice-QED-sparse-exact lattice-QED result is gauge-audited finite-cutoff evidence compared against variational_result.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `qft_lattice_discretization` / transformers=`['LatticeQEDRealSpaceDiscretization']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'variational_result', 'absolute_error': 0.0, 'relative_error': 0.0, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.088817541996832, 'shots': None, 'measurement_strategy': 'lattice_qed_sparse_exact', 'measurement_group_count': 1, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': 'lattice_qed'}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'exploratory', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lattice_qed_sparse_projected_exact', 'validation_scope=lattice_qed_finite_cutoff_exact_gate'], 'scientific_risk_notes': ['Sparse exact energy is exact only for the configured finite lattice/cutoff Hamiltonian.', 'Physical-sector projection is a finite-cutoff Gauss-law audit, not continuum chemistry accuracy.', 'Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Physical-sector-first builder materialized only the projected sparse operator.', 'Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.', 'Runtime circuits still act on the full qubit register unless explicitly transformed.']}`
- provenance_timestamp: `2026-05-24T02:36:54.235177+00:00`
- runtime_job_id: `None`
- artifact_root: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis`

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
- Scientific Risk Notes: `['Sparse exact energy is exact only for the configured finite lattice/cutoff Hamiltonian.', 'Physical-sector projection is a finite-cutoff Gauss-law audit, not continuum chemistry accuracy.', 'Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Physical-sector-first builder materialized only the projected sparse operator.', 'Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.', 'Runtime circuits still act on the full qubit register unless explicitly transformed.']`

## Energy Summary

- electronic_energy: `-8.706043896722` Hartree
- nuclear_repulsion_energy: `1.221603282540` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-7.484440614182` Hartree
- hf_reference_energy: `None`
- solver_energy: `-8.706043896722` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-8.706043896722` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `None`
- energy_units: `Hartree`
- constant_energy_correction: `0.000000000000` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`

## Field Definitions

- `solver_energy` is the raw energy returned by the configured solver on the mapped qubit Hamiltonian.
- `exact_ground_energy` is the raw exact-diagonalization energy of that same mapped Hamiltonian.
- `electronic_energy` is QCchem's corrected electronic energy after adding any non-nuclear Hamiltonian constants, such as active-space offsets.
- `external_point_charge_nuclear_interaction_energy` is the explicit QM nuclei/static point-charge Coulomb constant; MM-MM and non-electrostatic environment terms are not included.
- `boundary_embedding_constant_energy` is the explicit constant generated by boundary embedding; the first implementation records a zero constant unless a nonzero boundary projector is supplied.
- `total_energy` is reconstructed from the explicit `energy_formula`, so active-space and transformed problems remain auditable.
- `hf_reference_energy` is the Hartree-Fock total reference energy exposed by Qiskit Nature.
- `correlation_energy` is `total_energy - hf_reference_energy` and therefore measures post-HF improvement in the total-energy convention.

## Exact Baseline

- available: `True`
- source: `exact_diagonalization`
- solver_hamiltonian_energy: `-8.706043896722` Hartree
- electronic_energy: `-8.706043896722` Hartree
- total_energy: `-7.484440614182` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `variational_result`
- exact_electronic_energy: `-8.706043896722` Hartree
- exact_total_energy: `-7.484440614182` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `0.0`
- statistical_error: `None`
- absolute_error_threshold: `1e-09`
- relative_error_threshold: `1e-09`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/quantum_evidence.json`
- sidecar_sha256: `3956e4455c374341d4600d01d075e0893a9610a337aafda8841d72814ca63e3e`
- pauli_term_count: `1`
- measurement_group_count: `1`
- energy_contribution_sum: `None`
- coefficient_l1_norm: `0.0`
- groups_sha256: `e7ba9e993191511bad739837362a54d62105b459e9a4861ae15325b27d4ea2c7`
- counts_available: `False`
- counts_source: `None`
- counts_sha256: `None`
- shots_per_group: `None`
- hamiltonian_variance: `None`
- ground_state_overlap: `None`
- dominant_configurations: `[]`
- z2_check: `{'status': 'skipped_unsupported_field_model', 'z2_symmetry_count': 0, 'z2_tapering_values': None, 'validation': {}, 'notes': ['Molecular Z2 and point-group reduction are skipped for finite-cutoff lattice-QED field models.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `{'available': True, 'gauss_law_tolerance': 1e-08, 'target_charge_sector': 'neutral', 'reference_basis_index': 218, 'reference_state_gauss_law_residuals': [0.0, 0.0, 0.0, 0.0], 'reference_state_max_abs_gauss_law': 0.0}`
- resources: `{'num_qubits': 10, 'raw_num_qubits': 10, 'qubit_term_count': 1, 'raw_qubit_term_count': 1, 'circuit_depth': None, 'two_qubit_gate_count': None, 'operation_counts': {}}`
- error_budget: `{'ansatz_error': {'available': True, 'absolute_error_hartree': 0.0, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': True}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
- notes: `['final_state_not_available']`

## Problem Summary

- Basis: `real_space_lattice`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `4`
- Active space metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [4], 'matter_modes': 4, 'gauge_links': 3}`
- Transformers applied: `['LatticeQEDRealSpaceDiscretization']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 1.221603282540386}`
- Electronic constant correction: `0.000000000000` Hartree
- Point-group metadata: `{}`

## Mapping

- Mapping kind: `lattice_qed:jordan_wigner`
- Qubit count: `10`
- Fermionic Hamiltonian terms: `4`
- Qubit Hamiltonian terms: `1`
- Raw qubit count: `10`
- Raw qubit Hamiltonian terms: `1`
- Symmetry tapered qubits: `0`
- Z2 symmetry count: `0`
- Z2 tapering values: `None`
- Symmetry reduction status: `skipped_unsupported_field_model`
- Symmetry reduction validation: `{}`
- Symmetry reduction notes: `['Molecular Z2 and point-group reduction are skipped for finite-cutoff lattice-QED field models.']`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `2041`
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
- dimensions: `1`
- grid_shape: `[4]`
- grid_spacing: `[0.75]`
- boundary: `open`
- site_count: `4`
- link_count: `3`
- plaquette_count: `0`
- matter_mode_count: `4`
- gauge_group: `u1`
- gauge_electric_cutoff: `1`
- gauge_coupling: `1.0`
- total_qubits: `10`
- target_electrons: `2`
- term_counts_by_sector: `{'onsite': 6, 'external_point_charge': 0, 'hopping': 12, 'density_coulomb': 0, 'electric': 5, 'magnetic_plaquette': 0, 'gauss_law_penalty': 0, 'particle_number_penalty': 0, 'padding_penalty': 0}`
- constraints: `{'gauss_law_penalty': 10.0, 'particle_number_penalty': 10.0, 'padding_penalty': 50.0, 'enforce_physical_sector': True, 'target_charge_sector': 'neutral', 'gauss_law_tolerance': 1e-08, 'max_sector_enumeration_qubits': 12}`
- engine: `{'requested_representation': 'sparse_projected', 'actual_representation': 'sparse_projected', 'operator_representation': 'sparse_projected', 'auto_project_physical_sector': True, 'projected_builder': 'auto', 'build_mode': 'sector_first_projected', 'projected_dimension': 6, 'full_dimension': 1024, 'full_to_projected_reduction': 170.66666666666666, 'peak_matrix_dimension': 6, 'projected_builder_fallback_reason': None, 'max_projected_dimension': 4096, 'max_full_qubits_for_dense': 10, 'materialize_pauli': 'never', 'pauli_materialization': 'skipped', 'dense_full_matrix_materialized': False, 'store_basis_indices': 'full', 'projector_tolerance': 1e-08, 'full_hamiltonian_nnz': None, 'projected_hamiltonian_nnz': 18, 'sector_nnz': {'onsite': 6, 'external_point_charge': 0, 'hopping': 12, 'density_coulomb': 0, 'electric': 5, 'magnetic_plaquette': 0, 'gauss_law_penalty': 0, 'particle_number_penalty': 0, 'padding_penalty': 0}, 'projection_skipped_reason': None}`
- nuclear_charge_by_site: `[0.0, 1.0, 1.0, 0.0]`
- external_point_charges: `{}`
- notes: `['Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Physical-sector-first builder materialized only the projected sparse operator.', 'Sparse/projected engine is an internal finite-cutoff representation, not continuum chemistry.', 'Runtime circuits still act on the full qubit register unless explicitly transformed.']`

## Gauge Constraint Audit

> finite-cutoff QFT correctness means the configured lattice/cutoff Hamiltonian is internally audited; gauge-constraint consistency means Gauss-law generators and physical-sector checks are tracked; continuum chemistry accuracy is not claimed here.

- gauss_law_generators: `[{'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 0.0, 'hermitian': True, 'site_index': 0, 'target_charge': 0.0, 'diagonal_min': 0.0, 'diagonal_max': 0.0}, {'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 0.0, 'hermitian': True, 'site_index': 1, 'target_charge': 0.0, 'diagonal_min': 0.0, 'diagonal_max': 0.0}, {'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 0.0, 'hermitian': True, 'site_index': 2, 'target_charge': 0.0, 'diagonal_min': 0.0, 'diagonal_max': 0.0}, {'pauli_term_count': None, 'pauli_materialized': False, 'frobenius_norm': 0.0, 'hermitian': True, 'site_index': 3, 'target_charge': 0.0, 'diagonal_min': 0.0, 'diagonal_max': 0.0}]`
- hamiltonian_gauge_commutator_norms: `[{'site_index': 0, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}, {'site_index': 1, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}, {'site_index': 2, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}, {'site_index': 3, 'frobenius_norm': None, 'within_tolerance': None, 'skipped_reason': 'full_commutator_skipped_for_dynamics_resource_guard'}]`
- physical_sector: `{'enumerated': True, 'physical_sector_dimension': 6, 'basis_index_count': 6, 'basis_hash': 'c1ac3f8aba45be3c3c2dd81d9c9a506de7de893471fc782827698ecf3ce26405', 'basis_indices': [218, 342, 405, 582, 645, 769], 'basis_indices_preview': [218, 342, 405, 582, 645, 769], 'padding_state_rejection_count': 0, 'reference_basis_index': 218, 'tolerance': 1e-08, 'estimated_full_dimension': 1024, 'skipped_reason': None, 'target_charge_sector': 'neutral', 'max_sector_enumeration_qubits': 12, 'builder': 'sector_first'}`
- gauge_invariant_ansatz: `{'kind': 'gauss_law_preserving', 'generator_policy': 'gauge_invariant_hopping', 'selected_generator_count': 0, 'selected_generators': [], 'commutator_checks': [{'sector': 'hopping', 'selected': False, 'commutes_with_all_gauss_law_generators': False, 'max_commutator_norm': None, 'commutator_norms': [], 'pauli_term_count': -1, 'pauli_materialized': False, 'skipped_reason': 'ansatz_commutator_skipped_for_dynamics_resource_guard'}]}`
- constraint_expectations: `{'available': True, 'gauss_law_tolerance': 1e-08, 'target_charge_sector': 'neutral', 'reference_basis_index': 218, 'reference_state_gauss_law_residuals': [0.0, 0.0, 0.0, 0.0], 'reference_state_max_abs_gauss_law': 0.0}`
- finite_cutoff_qft_correctness: `audited against the persisted finite Hamiltonian`
- gauge_constraint_consistency: `Gauss-law residuals and commutators are finite-cutoff checks`
- continuum_chemistry_accuracy: `not asserted by this exploratory artifact`

## QFT Physical-Sector Engine Audit

> This section separates sparse/projection correctness from hardware full-register circuits and from continuum chemistry accuracy.

- requested_representation: `sparse_projected`
- actual_representation: `sparse_projected`
- projected_dimension: `6`
- full_dimension: `1024`
- pauli_materialization: `skipped`
- dense_full_matrix_materialized: `False`
- basis_hash: `c1ac3f8aba45be3c3c2dd81d9c9a506de7de893471fc782827698ecf3ce26405`
- basis_index_count: `6`
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
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [4], 'matter_modes': 4, 'gauge_links': 3}`
- selection_mode: `qft_lattice_discretization`
- selection_reason: `Molecule projected onto a finite real-space compact-U(1) lattice-QED grid.`
- selected_active_orbitals: `[0, 1, 2, 3]`
- selected_active_orbitals_original: `[0, 1, 2, 3]`
- frozen_core_orbitals: `[]`
- removed_orbitals: `[]`
- hamiltonian_constants: `{'nuclear_repulsion_energy': 1.221603282540386}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `1.221603282540` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_constant_correction: `1.221603282540` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`
- point_group_metadata: `{}`

## Reduction Plan

- enabled: `True`
- mode: `audit_only`
- strategy: `executed_transformers`
- recommended_changes: `{}`
- notes: `['Reduction audit captures executed transformers even without explicit planning metadata.']`
- provenance: `{'source': 'qcchem.chem.reduction_planner', 'policy_name': 'benchmark'}`

## Measurement Plan

- strategy: `lattice_qed_sparse_exact`
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
- notes: `["Measurement groups estimated with strategy 'lattice_qed_sparse_exact'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.0013951670116512105`
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

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`0c68621f7ed95dc12a831da68f2cf64c633e30d000afab6f1e2b6e032cf439da`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-24T02:36:54.235177+00:00`
- Wall time (s): `0.088817541996832`
- Git commit: `9a375331e05742322db6a3e8f9baed5c9c8aea56`
- Git commit short: `9a375331e057`
- Git branch: `HEAD`
- Git describe: `9a37533-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `.`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 14, 'untracked': 9}`
- Workspace fingerprint: `dfe0ef4a44754f28e703b070f179b13e00368a1accab6c65072b8754fc0918b0`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `2041`
- Source config: `configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml`

## Artifacts

- result.json: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/result.json`
- exact_result.json: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/exact_result.json`
- report.md: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/report.md`
- resolved_config.yaml: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/resolved_config.yaml`
- run.log: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/run.log`
- calibration.json: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/calibration.json`
- calibration_report.md: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/calibration_report.md`
- runtime_submission.json: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/runtime_submission.json`
- quantum_evidence.json: `/tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/quantum_evidence.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=0c68621f7ed9
- Building exploratory lattice-QED field Hamiltonian
- Constructed lattice-QED Hamiltonian: sites=4, links=3, qubits=10
- Prepared measurement plan: groups=1, cost=10000
- Skipping backend construction for solver: lattice_qed_sparse_exact
- Running solver: lattice_qed_sparse_exact
- Using sparse lattice-QED exact solver as the finite-cutoff exact baseline
- Writing exact baseline artifact to /tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/exact_result.json
- Computed empirical calibration: wall_time=0.001s, measured_cost=None
- Writing JSON result to /tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/result.json
- Writing Markdown report to /tmp/qcchem_h2_4site_lattice_qed_sparse_exact_analysis/report.md
- Run completed
