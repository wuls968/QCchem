# QCchem Report: H2-lattice-QED-dynamics

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-lattice-QED-dynamics`
- basis: `real_space_lattice`
- method: `statevector`
- mapping_kind: `lattice_qed:jordan_wigner`
- num_qubits: `6`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-8.467151406014` Hartree
- headline_correlation_energy: `None`
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `exact_baseline`
- active_space_metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2], 'matter_modes': 4, 'gauge_links': 1}`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'h2_lattice_qed_2site_dynamics', 'molecule_name': 'H2-lattice-QED-dynamics', 'basis': 'real_space_lattice', 'backend_kind': 'statevector', 'mapping_kind': 'lattice_qed:jordan_wigner', 'field_model_kind': 'lattice_qed'}`
- primary_scientific_claim: `H2-lattice-QED-dynamics lattice-QED result is gauge-audited finite-cutoff evidence compared against exact_baseline.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 1.0658141036401503e-14, 'units': 'Hartree', 'threshold': 1e-09, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-lattice-QED-dynamics lattice-QED result is gauge-audited finite-cutoff evidence compared against exact_baseline.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `qft_lattice_discretization` / transformers=`['LatticeQEDRealSpaceDiscretization']`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 1.0658141036401503e-14, 'relative_error': 1.1000527290666343e-15, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 1.454603958001826, 'shots': None, 'measurement_strategy': 'lattice_qed_dynamics', 'measurement_group_count': 25, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': 'lattice_qed'}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'exploratory', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=lattice_qed_finite_cutoff_exact_gate', 'validation_scope=lattice_qed_real_time_dynamics'], 'scientific_risk_notes': ['Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.', 'Gauge links use binary padding with encoded dimension 4.', 'Pauli decomposition was materialized for this finite Hamiltonian.', 'QFT dynamics curves are exact/Trotter trajectories of the finite lattice/cutoff Hamiltonian.', 'Trotter and runtime-batch evidence do not establish continuum-limit molecular accuracy.']}`
- provenance_timestamp: `2026-05-15T13:03:14.931945+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics`

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
- Verification Notes: `['validation_scope=lattice_qed_finite_cutoff_exact_gate', 'validation_scope=lattice_qed_real_time_dynamics']`
- Scientific Risk Notes: `['Lattice-QED execution uses a finite cutoff real-space field Hamiltonian.', 'Exact baselines compare against the discretized finite cutoff model, not continuum chemistry.', 'Continuum, gauge-cutoff, and grid-convergence claims require explicit follow-up studies.', 'Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.', 'Gauge links use binary padding with encoded dimension 4.', 'Pauli decomposition was materialized for this finite Hamiltonian.', 'QFT dynamics curves are exact/Trotter trajectories of the finite lattice/cutoff Hamiltonian.', 'Trotter and runtime-batch evidence do not establish continuum-limit molecular accuracy.']`

## Energy Summary

- electronic_energy: `-9.688754688554` Hartree
- nuclear_repulsion_energy: `1.221603282540` Hartree
- total_energy: `-8.467151406014` Hartree
- hf_reference_energy: `None`
- solver_energy: `-9.688754688554` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-9.688754688554` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
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
- solver_hamiltonian_energy: `-9.688754688554` Hartree
- electronic_energy: `-9.688754688554` Hartree
- total_energy: `-8.467151406014` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-9.688754688554` Hartree
- exact_total_energy: `-8.467151406014` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `1.1000527290666343e-15`
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
- Num spatial orbitals: `2`
- Active space metadata: `{'field_model': 'lattice_qed_minimal_coupling', 'grid_shape': [2], 'matter_modes': 4, 'gauge_links': 1}`
- Transformers applied: `['LatticeQEDRealSpaceDiscretization']`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 1.221603282540386}`
- Electronic constant correction: `0.000000000000` Hartree

## Mapping

- Mapping kind: `lattice_qed:jordan_wigner`
- Qubit count: `6`
- Fermionic Hamiltonian terms: `4`
- Qubit Hamiltonian terms: `54`

## Backend

- Backend kind: `statevector`
- Precision: `None`
- Shots: `None`
- Seed: `2031`
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
- gauge_electric_cutoff: `1`
- gauge_coupling: `1.0`
- total_qubits: `6`
- target_electrons: `2`
- term_counts_by_sector: `{'onsite': 5, 'hopping': 32, 'density_coulomb': 0, 'electric': 2, 'magnetic_plaquette': 0, 'gauss_law_penalty': 12, 'particle_number_penalty': 7, 'padding_penalty': 4}`
- constraints: `{'gauss_law_penalty': 10.0, 'particle_number_penalty': 10.0, 'padding_penalty': 50.0, 'enforce_physical_sector': True, 'target_charge_sector': 'neutral', 'gauss_law_tolerance': 1e-08, 'max_sector_enumeration_qubits': 8}`
- engine: `{'requested_representation': 'auto', 'actual_representation': 'dense_full', 'operator_representation': 'dense_full', 'auto_project_physical_sector': True, 'projected_dimension': None, 'full_dimension': 64, 'max_projected_dimension': 4096, 'max_full_qubits_for_dense': 10, 'materialize_pauli': 'auto', 'pauli_materialization': 'materialized', 'dense_full_matrix_materialized': True, 'store_basis_indices': 'preview', 'projector_tolerance': 1e-08, 'full_hamiltonian_nnz': 96, 'sector_nnz': {'onsite': 60, 'hopping': 32, 'density_coulomb': 0, 'electric': 32, 'magnetic_plaquette': 0, 'gauss_law_penalty': 54, 'particle_number_penalty': 40, 'padding_penalty': 16}, 'projection_skipped_reason': 'dense_full_representation'}`
- nuclear_charge_by_site: `[1.0, 1.0]`
- notes: `['Exploratory finite-cutoff compact-U(1) lattice-QED Hamiltonian.', 'Exact baselines compare against this discretized Hamiltonian, not continuum chemistry.', 'Gauge links use binary padding with encoded dimension 4.', 'Pauli decomposition was materialized for this finite Hamiltonian.']`

## Gauge Constraint Audit

> finite-cutoff QFT correctness means the configured lattice/cutoff Hamiltonian is internally audited; gauge-constraint consistency means Gauss-law generators and physical-sector checks are tracked; continuum chemistry accuracy is not claimed here.

- gauss_law_generators: `[{'pauli_term_count': 4, 'pauli_materialized': True, 'frobenius_norm': 8.0, 'hermitian': True, 'site_index': 0, 'target_charge': 0.0, 'diagonal_min': -2.0, 'diagonal_max': 2.0}, {'pauli_term_count': 4, 'pauli_materialized': True, 'frobenius_norm': 8.0, 'hermitian': True, 'site_index': 1, 'target_charge': 0.0, 'diagonal_min': -2.0, 'diagonal_max': 2.0}]`
- hamiltonian_gauge_commutator_norms: `[{'site_index': 0, 'frobenius_norm': 0.0, 'within_tolerance': True, 'skipped_reason': None}, {'site_index': 1, 'frobenius_norm': 0.0, 'within_tolerance': True, 'skipped_reason': None}]`
- physical_sector: `{'enumerated': True, 'physical_sector_dimension': 6, 'target_charge_sector': 'neutral', 'max_sector_enumeration_qubits': 8, 'basis_indices_preview': [14, 21, 25, 37, 41, 48], 'reference_basis_index': 14, 'basis_index_count': 6, 'basis_hash': '2b09b0092e7aa557f0dc1571f81bba9b786e3eb7921d0c0b64b905064d0ddf31', 'basis_indices': [14, 21, 25, 37, 41, 48], 'padding_state_rejection_count': 16, 'tolerance': 1e-08, 'estimated_full_dimension': 64, 'skipped_reason': None}`
- gauge_invariant_ansatz: `{'kind': 'gauss_law_preserving', 'generator_policy': 'gauge_invariant_hopping', 'selected_generator_count': 1, 'selected_generators': [{'sector': 'hopping', 'selected': True, 'commutes_with_all_gauss_law_generators': True, 'max_commutator_norm': 0.0, 'commutator_norms': [0.0, 0.0], 'pauli_term_count': 32, 'pauli_materialized': True, 'skipped_reason': None}], 'commutator_checks': [{'sector': 'hopping', 'selected': True, 'commutes_with_all_gauss_law_generators': True, 'max_commutator_norm': 0.0, 'commutator_norms': [0.0, 0.0], 'pauli_term_count': 32, 'pauli_materialized': True, 'skipped_reason': None}]}`
- constraint_expectations: `{'available': True, 'gauss_law_tolerance': 1e-08, 'target_charge_sector': 'neutral', 'reference_basis_index': 14, 'reference_state_gauss_law_residuals': [0.0, 0.0], 'reference_state_max_abs_gauss_law': 0.0}`
- finite_cutoff_qft_correctness: `audited against the persisted finite Hamiltonian`
- gauge_constraint_consistency: `Gauss-law residuals and commutators are finite-cutoff checks`
- continuum_chemistry_accuracy: `not asserted by this exploratory artifact`

## QFT Physical-Sector Engine Audit

> This section separates sparse/projection correctness from hardware full-register circuits and from continuum chemistry accuracy.

- requested_representation: `auto`
- actual_representation: `dense_full`
- projected_dimension: `None`
- full_dimension: `64`
- pauli_materialization: `materialized`
- dense_full_matrix_materialized: `True`
- basis_hash: `2b09b0092e7aa557f0dc1571f81bba9b786e3eb7921d0c0b64b905064d0ddf31`
- basis_index_count: `6`
- sparse_projection_correctness: `projected operators are finite-cutoff indexed submatrices when projection is active`
- runtime_circuit_boundary: `Runtime previews still target the full qubit register unless separately transformed`
- continuum_chemistry_accuracy: `not asserted by this exploratory engine audit`

## QFT Real-Time Dynamics

> This section reports exploratory finite-cutoff real-time lattice-QED dynamics; Trotter and runtime evidence are approximation/execution evidence, not continuum chemistry accuracy.

- enabled: `True`
- method: `real_time_quench`
- quench: `{'kind': 'local_hopping_pulse', 'base': 'physical_reference', 'reference_basis_index': 14, 'evolution_reference_index': 14, 'link_index': 0, 'pulse_time': 0.05, 'pulse_strength': 1.0, 'post_pulse_state_norm': 1.0}`
- time_grid: `{'start': 0.0, 'stop': 2.0, 'num_points': 41}`
- observable_summary: `{'site_density_count': 2, 'link_electric_flux_count': 1, 'link_electric_energy_count': 1, 'gauss_residual_count': 2, 'plaquette_wilson_count': 0, 'aggregate_observables': ['particle_number', 'total_electric_energy', 'total_gauss_violation', 'total_wilson']}`
- exact_available: `True`
- exact_time_point_count: `41`
- exact_skipped_reason: `None`
- trotter_available: `True`
- trotter_circuit_resources: `{'time_point_count': 41, 'max_depth': 242, 'max_operation_count': 244, 'max_two_qubit_gate_count': 0, 'per_time_point': [{'time': 0.0, 'depth': 2, 'operation_count': 4, 'two_qubit_gate_count': 0}, {'time': 0.05, 'depth': 8, 'operation_count': 10, 'two_qubit_gate_count': 0}, {'time': 0.1, 'depth': 14, 'operation_count': 16, 'two_qubit_gate_count': 0}, {'time': 0.15000000000000002, 'depth': 26, 'operation_count': 28, 'two_qubit_gate_count': 0}, {'time': 0.2, 'depth': 26, 'operation_count': 28, 'two_qubit_gate_count': 0}, {'time': 0.25, 'depth': 32, 'operation_count': 34, 'two_qubit_gate_count': 0}, {'time': 0.30000000000000004, 'depth': 44, 'operation_count': 46, 'two_qubit_gate_count': 0}, {'time': 0.35000000000000003, 'depth': 44, 'operation_count': 46, 'two_qubit_gate_count': 0}, {'time': 0.4, 'depth': 50, 'operation_count': 52, 'two_qubit_gate_count': 0}, {'time': 0.45, 'depth': 56, 'operation_count': 58, 'two_qubit_gate_count': 0}, {'time': 0.5, 'depth': 62, 'operation_count': 64, 'two_qubit_gate_count': 0}, {'time': 0.55, 'depth': 68, 'operation_count': 70, 'two_qubit_gate_count': 0}, {'time': 0.6000000000000001, 'depth': 80, 'operation_count': 82, 'two_qubit_gate_count': 0}, {'time': 0.65, 'depth': 80, 'operation_count': 82, 'two_qubit_gate_count': 0}, {'time': 0.7000000000000001, 'depth': 86, 'operation_count': 88, 'two_qubit_gate_count': 0}, {'time': 0.75, 'depth': 92, 'operation_count': 94, 'two_qubit_gate_count': 0}, {'time': 0.8, 'depth': 98, 'operation_count': 100, 'two_qubit_gate_count': 0}, {'time': 0.8500000000000001, 'depth': 104, 'operation_count': 106, 'two_qubit_gate_count': 0}, {'time': 0.9, 'depth': 110, 'operation_count': 112, 'two_qubit_gate_count': 0}, {'time': 0.9500000000000001, 'depth': 116, 'operation_count': 118, 'two_qubit_gate_count': 0}, {'time': 1.0, 'depth': 122, 'operation_count': 124, 'two_qubit_gate_count': 0}, {'time': 1.05, 'depth': 128, 'operation_count': 130, 'two_qubit_gate_count': 0}, {'time': 1.1, 'depth': 134, 'operation_count': 136, 'two_qubit_gate_count': 0}, {'time': 1.1500000000000001, 'depth': 140, 'operation_count': 142, 'two_qubit_gate_count': 0}, {'time': 1.2000000000000002, 'depth': 152, 'operation_count': 154, 'two_qubit_gate_count': 0}, {'time': 1.25, 'depth': 152, 'operation_count': 154, 'two_qubit_gate_count': 0}, {'time': 1.3, 'depth': 158, 'operation_count': 160, 'two_qubit_gate_count': 0}, {'time': 1.35, 'depth': 164, 'operation_count': 166, 'two_qubit_gate_count': 0}, {'time': 1.4000000000000001, 'depth': 170, 'operation_count': 172, 'two_qubit_gate_count': 0}, {'time': 1.4500000000000002, 'depth': 182, 'operation_count': 184, 'two_qubit_gate_count': 0}, {'time': 1.5, 'depth': 182, 'operation_count': 184, 'two_qubit_gate_count': 0}, {'time': 1.55, 'depth': 188, 'operation_count': 190, 'two_qubit_gate_count': 0}, {'time': 1.6, 'depth': 194, 'operation_count': 196, 'two_qubit_gate_count': 0}, {'time': 1.6500000000000001, 'depth': 200, 'operation_count': 202, 'two_qubit_gate_count': 0}, {'time': 1.7000000000000002, 'depth': 206, 'operation_count': 208, 'two_qubit_gate_count': 0}, {'time': 1.75, 'depth': 212, 'operation_count': 214, 'two_qubit_gate_count': 0}, {'time': 1.8, 'depth': 218, 'operation_count': 220, 'two_qubit_gate_count': 0}, {'time': 1.85, 'depth': 224, 'operation_count': 226, 'two_qubit_gate_count': 0}, {'time': 1.9000000000000001, 'depth': 230, 'operation_count': 232, 'two_qubit_gate_count': 0}, {'time': 1.9500000000000002, 'depth': 236, 'operation_count': 238, 'two_qubit_gate_count': 0}, {'time': 2.0, 'depth': 242, 'operation_count': 244, 'two_qubit_gate_count': 0}], 'trotter_step': 0.05, 'trotter_order': 1}`
- trotter_error_summary: `{'available': True, 'max_loschmidt_abs_error': 0.0004552133187693541, 'max_particle_number_abs_error': 1.9984014443252818e-15, 'max_total_gauss_violation_abs_error': 0.0}`
- runtime_batch: `{}`
- finite_cutoff_dynamics: `exact/statevector curves are for the persisted finite Hamiltonian`
- trotter_approximation: `reported against finite-cutoff exact dynamics when available`
- continuum_chemistry_accuracy: `not asserted by this exploratory dynamics artifact`

## Chemical Accuracy (Local Execution)

- available: `True`
- assessment_target: `local_execution`
- status: `validated`
- meets_chemical_accuracy: `True`
- absolute_error_hartree: `0.000000000000` Hartree
- absolute_error_kcal_mol: `6.688084475570121e-12`
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

- strategy: `lattice_qed_dynamics`
- grouping_policy: `finite_cutoff_field_terms`
- execution_mode: `estimator`
- low_rank_aware: `False`
- term_count: `54`
- group_count: `25`
- estimated_shot_cost: `250000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `25`
- uncompressed_estimated_shot_cost: `250000.0`
- cost_reduction_ratio: `1.0`
- notes: `["Measurement groups estimated with strategy 'lattice_qed_dynamics'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.003561166988220066`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `250000.0`
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

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-05-15T13:03:14.931945+00:00`
- Wall time (s): `1.454603958001826`
- Git commit: `164b7ff23843a5187d6aeba0c0bbd1bc2e3f287b`
- Git commit short: `164b7ff23843`
- Git branch: `HEAD`
- Git describe: `164b7ff-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/c397/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 0, 'unstaged': 15, 'untracked': 14}`
- Workspace fingerprint: `356ecaf4bd5b3876018df7f3eee1c41a81d8502280d478cea366e4fb6c3cbd6c`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '1.4.0', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.16.1'}`
- Seed: `2031`
- Source config: `/Users/a0000/.codex/worktrees/c397/QCchem/configs/exploratory/h2_lattice_qed_dynamics.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/runtime_submission.json`
- qcschema.json: `None`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/c397/QCchem/configs/exploratory/h2_lattice_qed_dynamics.yaml
- Building exploratory lattice-QED field Hamiltonian
- Constructed lattice-QED Hamiltonian: sites=2, links=1, qubits=6
- Prepared measurement plan: groups=25, cost=250000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/exact_result.json
- Computed empirical calibration: wall_time=0.004s, measured_cost=None
- Building lattice-QED real-time dynamics artifact
- Computed lattice-QED dynamics: exact_skipped_reason=None, trotter_skipped_reason=None
- Writing JSON result to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/c397/QCchem/artifacts/field_model_qft_local_campaign_v1/cases/h2_lattice_qed_2site_dynamics/report.md
- Run completed
