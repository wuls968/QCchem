# QCchem Report: H2-lattice-QED-exact

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-lattice-QED-exact`
- basis: `real_space_lattice`
- method: `statevector`
- mapping_kind: `lattice_qed:jordan_wigner`
- num_qubits: `5`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-6.921881558008` Hartree
- headline_correlation_energy: `None`
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `exact_baseline`
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2], 'matter_modes': 4, 'gauge_links': 1}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_lattice_qed_cutoff_0', 'molecule_name': 'H2-lattice-QED-exact', 'basis': 'real_space_lattice', 'backend_kind': 'statevector', 'mapping_kind': 'lattice_qed:jordan_wigner', 'field_model_kind': 'lattice_qed'}`
- primary_scientific_claim: `H2-lattice-QED-exact lattice-QED result is gauge-audited finite-cutoff evidence compared against exact_baseline.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 2.4868995751603507e-14, 'units': 'Hartree', 'threshold': 1e-09, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-lattice-QED-exact lattice-QED result is gauge-audited finite-cutoff evidence compared against exact_baseline.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `qft_lattice_discretization` / transformers=`['LatticeQEDRealSpaceDiscretization']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 2.4868995751603507e-14, 'relative_error': 3.053851789319376e-15, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 0.08830762500292622, 'shots': None, 'measurement_strategy': 'lattice_qed_exact', 'measurement_group_count': 1, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': 'lattice_qed'}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'exploratory', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lattice_qed_finite_cutoff_exact_gate'], 'scientific_risk_notes': ['Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.', 'Gauge links use binary padding with encoded dimension 2.', 'Pauli decomposition was materialized for this finite Hamiltonian.']}`
- provenance_timestamp: `2026-05-24T02:37:15.189758+00:00`
- runtime_job_id: `None`
- artifact_root: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0`

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
- Verification Notes: `['validation_scope=lattice_qed_finite_cutoff_exact_gate']`
- Scientific Risk Notes: `['Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.', 'Gauge links use binary padding with encoded dimension 2.', 'Pauli decomposition was materialized for this finite Hamiltonian.']`

## Energy Summary

- electronic_energy: `-8.143484840548` Hartree
- nuclear_repulsion_energy: `1.221603282540` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-6.921881558008` Hartree
- hf_reference_energy: `None`
- solver_energy: `-8.143484840548` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-8.143484840548` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
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
- solver_hamiltonian_energy: `-8.143484840548` Hartree
- electronic_energy: `-8.143484840548` Hartree
- total_energy: `-6.921881558008` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-8.143484840548` Hartree
- exact_total_energy: `-6.921881558008` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `3.053851789319376e-15`
- statistical_error: `None`
- absolute_error_threshold: `1e-09`
- relative_error_threshold: `1e-09`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/quantum_evidence.json`
- sidecar_sha256: `5c3613da09aac74ed803d83d6908de93ed054d7b4bced5f6ce8913e4952d30e5`
- pauli_term_count: `12`
- measurement_group_count: `1`
- energy_contribution_sum: `-8.143484840548` Hartree
- coefficient_l1_norm: `110.0`
- groups_sha256: `dad36228d262682af063dc53501df4f6bdae0194e0ed401fcc467376ce99cdcc`
- counts_available: `True`
- counts_source: `statevector_sampler_from_final_state`
- counts_sha256: `df3d16a0176d9b76902adcd6ea7e121969adba2b79b5cc8b3c198f711e97a81f`
- shots_per_group: `4096`
- hamiltonian_variance: `0.0`
- ground_state_overlap: `1.0000000000000004`
- dominant_configurations: `[{'bitstring': '01100', 'probability': 0.40468931583222156}, {'bitstring': '01010', 'probability': 0.26285426029306647}, {'bitstring': '10010', 'probability': 0.24121669496363962}, {'bitstring': '10100', 'probability': 0.09123972891107242}, {'bitstring': '11111', 'probability': 2.516876465767381e-31}, {'bitstring': '11100', 'probability': 5.703876109643928e-32}, {'bitstring': '00110', 'probability': 3.8591169894080504e-32}, {'bitstring': '11010', 'probability': 3.0115551238375873e-32}]`
- z2_check: `{'status': 'skipped_unsupported_field_model', 'z2_symmetry_count': 0, 'z2_tapering_values': None, 'validation': {}, 'notes': ['Molecular Z2 and point-group reduction are skipped for finite-cutoff lattice-QED field models.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `{'available': True, 'gauss_law_tolerance': 1e-08, 'target_charge_sector': 'neutral', 'reference_basis_index': 10, 'reference_state_gauss_law_residuals': [0.0, 0.0], 'reference_state_max_abs_gauss_law': 0.0}`
- resources: `{'num_qubits': 5, 'raw_num_qubits': 5, 'qubit_term_count': 12, 'raw_qubit_term_count': 12, 'circuit_depth': None, 'two_qubit_gate_count': None, 'operation_counts': {}}`
- error_budget: `{'ansatz_error': {'available': False, 'absolute_error_hartree': 2.4868995751603507e-14, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': True}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
- notes: `[]`

## Problem Summary

- Basis: `real_space_lattice`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2], 'matter_modes': 4, 'gauge_links': 1}`
- Transformers applied: `['LatticeQEDRealSpaceDiscretization']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 1.221603282540386}`
- Electronic constant correction: `0.000000000000` Hartree
- Point-group metadata: `{}`

## Mapping

- Mapping kind: `lattice_qed:jordan_wigner`
- Qubit count: `5`
- Fermionic Hamiltonian terms: `4`
- Qubit Hamiltonian terms: `12`
- Raw qubit count: `5`
- Raw qubit Hamiltonian terms: `12`
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
- Seed: `2026`
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
- grid_shape: `[2]`
- grid_spacing: `[0.75]`
- boundary: `open`
- site_count: `2`
- link_count: `1`
- plaquette_count: `0`
- matter_mode_count: `4`
- gauge_group: `u1`
- gauge_electric_cutoff: `0`
- gauge_coupling: `1.0`
- total_qubits: `5`
- target_electrons: `2`
- term_counts_by_sector: `{'onsite': 5, 'external_point_charge': 0, 'hopping': 0, 'density_coulomb': 0, 'electric': 0, 'magnetic_plaquette': 0, 'gauss_law_penalty': 3, 'particle_number_penalty': 7, 'padding_penalty': 2}`
- constraints: `{'gauss_law_penalty': 10.0, 'particle_number_penalty': 10.0, 'padding_penalty': 50.0, 'enforce_physical_sector': False, 'target_charge_sector': 'neutral', 'gauss_law_tolerance': 1e-08, 'max_sector_enumeration_qubits': 10}`
- engine: `{'requested_representation': 'auto', 'actual_representation': 'dense_full', 'operator_representation': 'dense_full', 'auto_project_physical_sector': True, 'projected_builder': 'auto', 'build_mode': 'dense_full', 'projected_dimension': None, 'full_to_projected_reduction': None, 'peak_matrix_dimension': 32, 'projected_builder_fallback_reason': None, 'full_dimension': 32, 'max_projected_dimension': 4096, 'max_full_qubits_for_dense': 10, 'materialize_pauli': 'auto', 'pauli_materialization': 'materialized', 'dense_full_matrix_materialized': True, 'store_basis_indices': 'preview', 'projector_tolerance': 1e-08, 'full_hamiltonian_nnz': 32, 'sector_nnz': {'onsite': 30, 'external_point_charge': 0, 'hopping': 0, 'density_coulomb': 0, 'electric': 0, 'magnetic_plaquette': 0, 'gauss_law_penalty': 24, 'particle_number_penalty': 20, 'padding_penalty': 16}, 'projection_skipped_reason': 'dense_full_representation'}`
- nuclear_charge_by_site: `[1.0, 1.0]`
- external_point_charges: `{}`
- notes: `['Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.', 'Gauge links use binary padding with encoded dimension 2.', 'Pauli decomposition was materialized for this finite Hamiltonian.']`

## Gauge Constraint Audit

> finite-cutoff QFT correctness means the configured lattice/cutoff Hamiltonian is internally audited; gauge-constraint consistency means Gauss-law generators and physical-sector checks are tracked; continuum chemistry accuracy is not claimed here.

- gauss_law_generators: `[{'pauli_term_count': 2, 'pauli_materialized': True, 'frobenius_norm': 4.0, 'hermitian': True, 'site_index': 0, 'target_charge': 0.0, 'diagonal_min': -1.0, 'diagonal_max': 1.0}, {'pauli_term_count': 2, 'pauli_materialized': True, 'frobenius_norm': 4.0, 'hermitian': True, 'site_index': 1, 'target_charge': 0.0, 'diagonal_min': -1.0, 'diagonal_max': 1.0}]`
- hamiltonian_gauge_commutator_norms: `[{'site_index': 0, 'frobenius_norm': 0.0, 'within_tolerance': True, 'skipped_reason': None}, {'site_index': 1, 'frobenius_norm': 0.0, 'within_tolerance': True, 'skipped_reason': None}]`
- physical_sector: `{'enumerated': True, 'physical_sector_dimension': 4, 'target_charge_sector': 'neutral', 'max_sector_enumeration_qubits': 10, 'basis_indices_preview': [10, 12, 18, 20], 'reference_basis_index': 10, 'basis_index_count': 4, 'basis_hash': '70a34c20ecbd8be62401a2ea9dca800d2964cf9d6668e888d03b0907d202347e', 'basis_indices': [10, 12, 18, 20], 'padding_state_rejection_count': 16, 'tolerance': 1e-08, 'estimated_full_dimension': 32, 'skipped_reason': None}`
- gauge_invariant_ansatz: `{'kind': 'gauss_law_preserving', 'generator_policy': 'gauge_invariant_hopping', 'selected_generator_count': 0, 'selected_generators': [], 'commutator_checks': [{'sector': 'hopping', 'selected': False, 'reason': 'empty_sector', 'commutes_with_all_gauss_law_generators': True, 'max_commutator_norm': 0.0}]}`
- constraint_expectations: `{'available': True, 'gauss_law_tolerance': 1e-08, 'target_charge_sector': 'neutral', 'reference_basis_index': 10, 'reference_state_gauss_law_residuals': [0.0, 0.0], 'reference_state_max_abs_gauss_law': 0.0}`
- finite_cutoff_qft_correctness: `audited against the persisted finite Hamiltonian`
- gauge_constraint_consistency: `Gauss-law residuals and commutators are finite-cutoff checks`
- continuum_chemistry_accuracy: `not asserted by this exploratory artifact`

## QFT Physical-Sector Engine Audit

> This section separates sparse/projection correctness from hardware full-register circuits and from continuum chemistry accuracy.

- requested_representation: `auto`
- actual_representation: `dense_full`
- projected_dimension: `None`
- full_dimension: `32`
- pauli_materialization: `materialized`
- dense_full_matrix_materialized: `True`
- basis_hash: `70a34c20ecbd8be62401a2ea9dca800d2964cf9d6668e888d03b0907d202347e`
- basis_index_count: `4`
- sparse_projection_correctness: `projected operators are finite-cutoff indexed submatrices when projection is active`
- runtime_circuit_boundary: `Runtime previews still target the full qubit register unless separately transformed`
- continuum_chemistry_accuracy: `not asserted by this exploratory engine audit`

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- absolute_error_kcal_mol: `1.5605530442996948e-11`
- threshold_hartree: `0.0016`
- threshold_kcal_mol: `1.0040151583999999`
- statistical_error: `None`
- notes: `['Meets chemical accuracy threshold.']`

## Reduction Audit

- original_num_particles: `(1, 1)`
- original_num_spatial_orbitals: `2`
- reduced_num_particles: `(1, 1)`
- reduced_num_spatial_orbitals: `2`
- transformers_applied: `['LatticeQEDRealSpaceDiscretization']`
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2], 'matter_modes': 4, 'gauge_links': 1}`
- selection_mode: `qft_lattice_discretization`
- selection_reason: `Molecule projected onto a finite real-space compact-U(1) lattice-QED grid.`
- selected_active_orbitals: `[0, 1]`
- selected_active_orbitals_original: `[0, 1]`
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

- strategy: `lattice_qed_exact`
- grouping_policy: `finite_cutoff_field_terms`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `12`
- group_count: `1`
- estimated_shot_cost: `10000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `1`
- uncompressed_estimated_shot_cost: `10000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'lattice_qed_exact'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.005445000002509914`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `10000.0`
- estimated_vs_measured_cost: `None`
- reference_target: `exact_baseline`
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
- Timestamp: `2026-05-24T02:37:15.189758+00:00`
- Wall time (s): `0.08830762500292622`
- Git commit: `9a375331e05742322db6a3e8f9baed5c9c8aea56`
- Git commit short: `9a375331e057`
- Git branch: `HEAD`
- Git describe: `9a37533-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `.`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 14, 'untracked': 9}`
- Workspace fingerprint: `ff59bbd3ff313f363df346dc545e4d1e1014559d82e406c056d2a0a9bbc40467`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `2026`
- Source config: `./configs/exploratory/h2_lattice_qed_exact.yaml`

## Artifacts

- result.json: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/result.json`
- exact_result.json: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/exact_result.json`
- report.md: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/report.md`
- resolved_config.yaml: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/resolved_config.yaml`
- run.log: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/run.log`
- calibration.json: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/calibration.json`
- calibration_report.md: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/calibration_report.md`
- runtime_submission.json: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/runtime_submission.json`
- quantum_evidence.json: `/tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/quantum_evidence.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from ./configs/exploratory/h2_lattice_qed_exact.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=0c68621f7ed9
- Building exploratory lattice-QED field Hamiltonian
- Constructed lattice-QED Hamiltonian: sites=2, links=1, qubits=5
- Prepared measurement plan: groups=1, cost=10000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/exact_result.json
- Computed empirical calibration: wall_time=0.005s, measured_cost=None
- Writing JSON result to /tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/result.json
- Writing Markdown report to /tmp/qcchem_h2_lattice_qed_cutoff_grid_analysis/cases/h2_lattice_qed_cutoff_0/report.md
- Run completed
