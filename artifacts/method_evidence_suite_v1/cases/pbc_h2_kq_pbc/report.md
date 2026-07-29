# QCchem Report: H2-kq-pbc

> This result is exploratory and is not part of the validated QCchem benchmark path.

## Report Cover

> Scientific Atelier framing for export-grade review: lead with chemistry confidence, runtime evidence, and the minimum context needed to defend the result.

- molecule: `H2-kq-pbc`
- basis: `sto3g`
- method: `statevector`
- mapping_kind: `jordan_wigner`
- num_qubits: `1`
- verification_status: `exploratory`
- hardware_verified: `False`
- hardware_evidence_tier: `None`
- benchmark_absolute_error: `0.000000000000` Hartree
- best_available_assessment: `local_execution`
- backend_kind: `statevector`

## Hero

- headline_total_energy: `-0.952294069566` Hartree
- headline_correlation_energy: `0.167601715515` Hartree
- headline_absolute_error: `0.000000000000` Hartree
- comparison_target: `exact_baseline`
- active_space_metadata: `None`
- runtime_backend: `None`
- runtime_job_id: `None`

## Evidence Summary

- result_identity: `{'artifact_kind': 'run', 'artifact_name': 'pbc_h2_kq_pbc', 'molecule_name': 'H2-kq-pbc', 'basis': 'sto3g', 'backend_kind': 'statevector', 'mapping_kind': 'jordan_wigner', 'field_model_kind': None}`
- primary_scientific_claim: `H2-kq-pbc stays within chemical accuracy against exact_baseline for the defended local execution path.`
- primary_baseline: `{'baseline_kind': 'exact', 'baseline_source': 'exact_diagonalization', 'baseline_scope': 'single_run', 'baseline_strength': 'strong'}`
- primary_error_metric: `{'metric_kind': 'absolute_error_hartree', 'value': 0.0, 'units': 'Hartree', 'threshold': 1e-08, 'comparison_target': 'exact_baseline'}`
- chemical_accuracy_status: `met`
- runtime_evidence_status: `none`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Claim

- primary_scientific_claim: `H2-kq-pbc stays within chemical accuracy against exact_baseline for the defended local execution path.`
- trust_tier: `exploratory`
- recommended_action: `collect_stronger_baseline`

## Chain

- reduction: `none` / transformers=`[]`
- compression: `None` / status=`None`
- correction: `None` / delta=`None`
- comparison_evidence: `{'comparison_target': 'exact_baseline', 'absolute_error': 0.0, 'relative_error': 0.0, 'statistical_error': None, 'baseline_strength': 'strong', 'compressed_vs_uncompressed': None}`

## Proof

- execution_evidence: `{'wall_time_seconds': 2.1101574999993318, 'shots': None, 'measurement_strategy': 'default', 'measurement_group_count': 2, 'measured_shot_usage': None, 'runtime_backend': None, 'runtime_job_id': None, 'field_model_kind': None}`
- trust_judgment: `{'verification_status': 'exploratory', 'module_origin': 'core', 'hardware_verified': False, 'hardware_evidence_tier': None, 'verification_notes': ['validation_scope=pbc_gamma_supercell_v1'], 'scientific_risk_notes': ['PBC execution is Gamma-only/supercell scoped in v1.', 'Non-Gamma k-point meshes, finite-size convergence, and full periodic QM/MM dynamics are not claimed.'], 'lr_ace_trust_label': None, 'lr_ace_validation_gate': None}`
- provenance_timestamp: `2026-07-08T04:20:47.006419+00:00`
- runtime_job_id: `None`
- artifact_root: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc`

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

- Module Origin: `core`
- Capability Tier: `exploratory`
- Verification Notes: `['validation_scope=pbc_gamma_supercell_v1']`
- Scientific Risk Notes: `['PBC execution is Gamma-only/supercell scoped in v1.', 'Non-Gamma k-point meshes, finite-size convergence, and full periodic QM/MM dynamics are not claimed.']`

## Energy Summary

- electronic_energy: `-1.298088849114` Hartree
- nuclear_repulsion_energy: `0.345794779547` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_energy: `-0.952294069566` Hartree
- hf_reference_energy: `-1.119895785081` Hartree
- solver_energy: `-1.298088849114` Hartree (raw solver-Hamiltonian energy, before QCchem constant-shift correction)
- exact_ground_energy: `-1.298088849114` Hartree (raw exact baseline in the same solver-Hamiltonian convention)
- correlation_energy: `0.167601715515` Hartree
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
- solver_hamiltonian_energy: `-1.298088849114` Hartree
- electronic_energy: `-1.298088849114` Hartree
- total_energy: `-0.952294069566` Hartree

## Benchmark

- exact_available: `True`
- comparison_target: `exact_baseline`
- exact_electronic_energy: `-1.298088849114` Hartree
- exact_total_energy: `-0.952294069566` Hartree
- absolute_error: `0.000000000000` Hartree
- relative_error: `0.0`
- statistical_error: `None`
- absolute_error_threshold: `1e-08`
- relative_error_threshold: `1e-08`
- within_uncertainty: `None`
- meets_threshold: `True`

## Quantum Evidence

> Full Pauli terms, measurement groups, bitstring counts, trajectory, state, symmetry, resource, and error-budget details are persisted in the quantum evidence sidecar.

- available: `True`
- schema: `qcchem.quantum_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/quantum_evidence.json`
- sidecar_sha256: `066d596548137386e02baf843f837b855b15a6241dd0f2e7791ed811cfff3f1f`
- pauli_terms_available: `True`
- pauli_unavailable_reason: `None`
- pauli_term_count: `3`
- measurement_group_count: `2`
- energy_contribution_sum: `-1.298088849114` Hartree
- coefficient_l1_norm: `1.4578858641138446`
- projected_matrix_dimension: `None`
- projected_hamiltonian_nnz: `None`
- physical_sector_dimension: `None`
- basis_hash: `None`
- projected_matrix_sha256: `None`
- groups_sha256: `709c84fbcf66765924c44c58f1738014433d1afca44aa6ec2f81c6293e737634`
- measurement_group_count_scope: `pauli_grouping`
- estimated_measurement_cost_scope: `pauli_grouping`
- estimated_measurement_cost_is_hardware_cost: `None`
- sparse_exploratory_estimated_measurement_cost: `None`
- counts_available: `True`
- counts_source: `statevector_sampler_from_final_state`
- counts_sha256: `f60f84ec9ee0035845cc1247f185bf620d77bfa1585788d24f3d9c395a14bfda`
- shots_per_group: `4096`
- hamiltonian_variance: `6.661338147750939e-16`
- ground_state_overlap: `0.9999999999999996`
- dominant_configurations: `[{'bitstring': '0', 'probability': 0.9876944806845288}, {'bitstring': '1', 'probability': 0.012305519315471015}]`
- z2_check: `{'status': 'applied_z2', 'z2_symmetry_count': 3, 'z2_tapering_values': [-1, 1, -1], 'validation': {'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.2980888491137055, 'tapered_ground_energy': -1.2980888491137033, 'absolute_delta': 2.220446049250313e-15}, 'notes': ['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=2.22045e-15 Hartree.']}`
- particle_number_check: `{'target_num_particles': [1, 1], 'status': 'declared_from_problem_summary', 'expectation_value': None, 'deviation': None, 'notes': ['Particle-number operator expectation is not reconstructed for all mapper/tapering combinations in v1.']}`
- spin_check: `{'status': 'not_available', 'notes': ['Spin-conservation expectation requires a mapped spin operator and is not computed in v1.']}`
- qft_constraints: `None`
- resources: `{'num_qubits': 1, 'raw_num_qubits': 4, 'qubit_term_count': 3, 'raw_qubit_term_count': 15, 'circuit_depth': None, 'two_qubit_gate_count': None, 'operation_counts': {}}`
- error_budget: `{'ansatz_error': {'available': False, 'absolute_error_hartree': 0.0, 'baseline': 'exact_baseline'}, 'shot_noise': {'available': False, 'sampled_standard_error': None, 'runtime_reported_std': None, 'benchmark_statistical_error': None}, 'compression_error': {'available': False, 'reconstruction_error': None, 'compressed_vs_uncompressed': None}, 'hardware_noise': {'available': False, 'verification_status': None, 'mitigation_metadata': None}, 'field_model': {'qft_error_budget': None, 'cavity_error_budget': None, 'finite_cutoff_boundary': False}, 'qmmm_embedding': {'available': False, 'mm_environment_quantized': None, 'one_body_environment': None, 'cache_validation': None, 'boundary': None}, 'existing_error_budget': {}}`
- eigen_residual_norm: `None`
- relative_eigen_residual: `None`
- ground_state_gap: `None`
- lowest_eigenvalues: `None`
- sparse_exact_validation: `{}`
- lattice_qed_observables: `{}`
- notes: `[]`

## Method Evidence

> Exploratory method outputs are reported alongside the raw solver energy; they do not replace the primary energy or promote validation status by themselves.

- available: `True`
- schema: `qcchem.method_evidence.v1`
- sidecar_path: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/method_evidence.json`
- sidecar_sha256: `2d357b2a3d319b4d604b34f264f6acb8c25fca118e80d237c527513917a4e123`
- methods: `{'kq_pbc_result': {'available': True, 'trust_tier': 'exploratory'}}`
- promotion_gate_audit: `{'schema': 'qcchem.method_promotion_gate_audit.v1', 'primary_solver_kind': 'exact', 'primary_energy_policy': 'raw_solver_energy_remains_primary', 'sidecar_energy_replacement_allowed_methods': [], 'accuracy_claim_allowed_methods': [], 'hardware_claim_allowed_methods': [], 'planning_metric_methods': [], 'resource_model_only_methods': [], 'unsupported_for_claim_methods': [], 'method_records': {'kq_pbc_result': {'method': 'kq_pbc_result', 'primary_solver_selected': False, 'energy_replacement_allowed': False, 'accuracy_claim_allowed': False, 'hardware_claim_allowed': False, 'planning_metric_allowed': False, 'resource_model_claim_allowed': False, 'claim_status': 'audit_only', 'evidence_role': 'pbc_k_twist_audit', 'promotion_required_for_validated_claim': True, 'promotion_blockers': ['non_gamma_quantum_mapping_not_executed', 'twist_energies_not_evaluated', 'finite_size_correction_not_evaluated', 'forces_stress_cell_optimization_out_of_scope'], 'promotion_readiness_status': 'blocked_exploratory_audit_only', 'readiness_level': 'not_ready_for_validated_non_gamma_claim', 'named_kpoint_execution_coverage_fraction': 0.5, 'mesh_kpoint_execution_coverage_fraction': 0.5, 'twist_energy_coverage_fraction': 0.0, 'missing_twist_energy_fraction': 1.0, 'promotion_blocker_count': 4, 'unsupported_claim_count': 4}}, 'overall_claim_status': 'promotion_required', 'promotion_required_for_validated_claims': True, 'notes': ['Sidecar method evidence cannot promote validated accuracy, hardware, or energy-replacement claims by itself.', 'Planning/resource-model findings may be compared as local estimates but are not hardware-calibrated superiority claims.']}`
- trust_tier: `exploratory`
- notes: `['Method evidence is reported alongside the primary solver result.', 'Exploratory method sections do not promote chemical-accuracy claims by themselves.']`

## kQ-PBC

- kpoints: `['gamma', 'x_half']`
- twist_energies: `[{'kpoint': 'gamma', 'requested_twist_index': 0, 'solver_energy_hartree': None, 'energy_status': 'not_evaluated', 'execution_reference': 'gamma_reference_hamiltonian', 'mapping_status': 'audit_only', 'reason': 'kQ-PBC v1 records requested non-Gamma/twist metadata but does not execute non-Gamma quantum mappings.'}, {'kpoint': 'x_half', 'requested_twist_index': 1, 'solver_energy_hartree': None, 'energy_status': 'not_evaluated', 'execution_reference': 'gamma_reference_hamiltonian', 'mapping_status': 'audit_only', 'reason': 'kQ-PBC v1 records requested non-Gamma/twist metadata but does not execute non-Gamma quantum mappings.'}]`
- finite_size_correction: `{'status': 'not_evaluated', 'twist_average_requested': True, 'energy_correction_hartree': None, 'required_twist_energy_count': 2, 'available_twist_energy_count': 0, 'missing_twist_energy_count': 2, 'twist_energy_coverage_fraction': 0.0, 'missing_twist_energy_fraction': 1.0, 'reason': 'No non-Gamma/twist energies are available for finite-size correction in kQ-PBC v1.'}`
- band_window_metadata: `{'num_electrons': 2, 'num_spatial_orbitals': 2}`
- non_gamma_mapping_audit: `{'status': 'audit_only', 'requested_kpoint_mesh': [2, 1, 1], 'execution_kpoint_mesh': [1, 1, 1], 'requested_kpoint_count': 2, 'execution_kpoint_count': 1, 'mesh_mismatch': True, 'requested_named_kpoints': ['gamma', 'x_half'], 'executed_named_kpoints': ['gamma'], 'executed_requested_named_kpoints': ['gamma'], 'named_kpoint_execution_coverage_fraction': 0.5, 'mesh_kpoint_execution_coverage_fraction': 0.5, 'gamma_reference_energy_hartree': -1.2980888491137033, 'non_gamma_energy_available': False, 'energy_replaces_primary': False, 'runtime_submission_allowed': False, 'forces_stress_cell_optimization': 'out_of_scope', 'executable_scope': 'gamma_reference_hamiltonian_only', 'promotion_blockers': ['non_gamma_quantum_mapping_not_executed', 'twist_energies_not_evaluated', 'finite_size_correction_not_evaluated', 'forces_stress_cell_optimization_out_of_scope'], 'promotion_blocker_count': 4, 'unsupported_claims': ['non_gamma_materials_accuracy', 'twist_averaged_energy', 'finite_size_corrected_energy', 'forces_or_stress'], 'unsupported_claim_count': 4, 'coverage_audit': {'status': 'gamma_reference_only_coverage_gap', 'requested_named_kpoint_count': 2, 'executed_named_kpoint_count': 1, 'executed_requested_named_kpoint_count': 1, 'named_kpoint_execution_coverage_fraction': 0.5, 'requested_mesh_kpoint_count': 2, 'execution_mesh_kpoint_count': 1, 'mesh_kpoint_execution_coverage_fraction': 0.5, 'required_twist_energy_count': 2, 'available_twist_energy_count': 0, 'missing_twist_energy_count': 2, 'twist_energy_coverage_fraction': 0.0, 'missing_twist_energy_fraction': 1.0, 'proxy_energy_present': False}}`
- pbc_trust_tier: `exploratory`
- notes: `['kQ-PBC v1 is an exploratory audit and does not validate non-Gamma materials accuracy.', 'Requested k/twist entries do not contain proxy energies; only the Gamma reference Hamiltonian is executed.']`

## Problem Summary

- Basis: `sto3g`
- Charge: `0`
- Multiplicity: `1`
- Num particles: `(1, 1)`
- Num spatial orbitals: `2`
- Active space metadata: `None`
- Transformers applied: `[]`
- Hamiltonian constants: `{'nuclear_repulsion_energy': 0.34579477954749577}`
- Electronic constant correction: `0.000000000000` Hartree
- Point-group metadata: `{'status': 'skipped_for_pbc', 'reason': 'Molecular point-group symmetry is not reused for periodic Gamma-only cells.', 'pyscf_pbc': {'schema': 'qcchem.pbc.pyscf_adapter.v1', 'adapter': 'qcchem.pbc.pyscf_adapter.run_gamma_cell_problem', 'pyscf_cell': {'dimension': 3, 'lattice_vectors_bohr': [[15.117808996520495, 0.0, 0.0], [0.0, 15.117808996520495, 0.0], [0.0, 0.0, 15.117808996520495]], 'basis': 'sto3g', 'unit': 'Angstrom', 'charge': 0, 'spin': 0, 'nelectron': 2}, 'scf': {'method': 'rhf', 'density_fit': True, 'density_fitting': 'fftdf', 'mesh': None, 'converged': True, 'e_tot_hartree': -1.1198957850814824, 'nuclear_repulsion_energy_hartree': 0.34579477954749577}, 'mapping': {'target': 'qiskit_nature.second_q.problems.ElectronicStructureProblem', 'raw_integrals': 'ElectronicEnergy.from_raw_integrals', 'orbital_basis': 'Gamma-point PySCF molecular orbitals', 'num_spatial_orbitals': 2, 'num_particles': [1, 1]}, 'scope': {'kpoint_mesh': [1, 1, 1], 'non_gamma_policy': 'rejected', 'spin_policy': 'closed_shell_rhf_only', 'periodic_images': 'PySCF PBC cell integrals at Gamma point'}, 'integration_recommendations': ['Use GammaCellProblem.problem anywhere the molecular builder expects an ElectronicStructureProblem.', 'Keep non-Gamma k-point workflows out of the mapped quantum-algorithm path until full k-point support exists.', 'Use qcchem.pbc.ewald for periodic QM/MM constant terms before adding them to hamiltonian.constants.']}}`

## PBC / PBC-QMMM

> Periodic boundary and periodic-QM/MM execution metadata. Gamma-only supercell PBC is supported in v1; non-Gamma k-point meshes are parsed and rejected.

- pbc_enabled: `True`
- pbc_status: `executed_gamma_supercell`
- periodicity: `3d`
- boundary_conditions: `[True, True, True]`
- cell_units: `angstrom`
- cell_vectors: `[[8.0, 0.0, 0.0], [0.0, 8.0, 0.0], [0.0, 0.0, 8.0]]`
- kpoint_mode: `gamma`
- kpoint_grid: `[2, 1, 1]`
- pbc_core_runner_implemented: `True`
- pbc_qmmm_enabled: `None`
- pbc_qmmm_status: `None`
- embedding_mode: `None`
- qm_region: `{}`
- mm_region: `{}`
- boundary: `{}`
- pbc_qmmm_core_runner_implemented: `None`
- notes: `[]`

## Mapping

- Mapping kind: `jordan_wigner`
- Qubit count: `1`
- Fermionic Hamiltonian terms: `36`
- Qubit Hamiltonian terms: `3`
- Raw qubit count: `4`
- Raw qubit Hamiltonian terms: `15`
- Symmetry tapered qubits: `3`
- Z2 symmetry count: `3`
- Z2 tapering values: `[-1, 1, -1]`
- Symmetry reduction status: `applied_z2`
- Symmetry reduction validation: `{'available': True, 'method': 'exact_ground_state_delta', 'max_qubits': 12, 'raw_ground_energy': -1.2980888491137055, 'tapered_ground_energy': -1.2980888491137033, 'absolute_delta': 2.220446049250313e-15}`
- Symmetry reduction notes: `['Applied Z2 tapering in sector [-1, 1, -1]; removed 3 qubits.', 'Exact-spectrum validation passed with delta=2.22045e-15 Hartree.']`

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
- finite_model_exactness: `{}`
- continuum_chemistry_accuracy: `{}`
- hardware_accuracy: `{}`
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
- hamiltonian_constants: `{'nuclear_repulsion_energy': 0.34579477954749577}`
- constant_energy_correction: `0.000000000000` Hartree
- nuclear_repulsion_energy: `0.345794779547` Hartree
- external_point_charge_nuclear_interaction_energy: `0.000000000000` Hartree
- boundary_embedding_constant_energy: `0.000000000000` Hartree
- total_constant_correction: `0.345794779547` Hartree
- energy_formula: `total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy + external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; electronic_energy = solver_energy + constant_energy_correction`
- point_group_metadata: `{'status': 'skipped_for_pbc', 'reason': 'Molecular point-group symmetry is not reused for periodic Gamma-only cells.', 'pyscf_pbc': {'schema': 'qcchem.pbc.pyscf_adapter.v1', 'adapter': 'qcchem.pbc.pyscf_adapter.run_gamma_cell_problem', 'pyscf_cell': {'dimension': 3, 'lattice_vectors_bohr': [[15.117808996520495, 0.0, 0.0], [0.0, 15.117808996520495, 0.0], [0.0, 0.0, 15.117808996520495]], 'basis': 'sto3g', 'unit': 'Angstrom', 'charge': 0, 'spin': 0, 'nelectron': 2}, 'scf': {'method': 'rhf', 'density_fit': True, 'density_fitting': 'fftdf', 'mesh': None, 'converged': True, 'e_tot_hartree': -1.1198957850814824, 'nuclear_repulsion_energy_hartree': 0.34579477954749577}, 'mapping': {'target': 'qiskit_nature.second_q.problems.ElectronicStructureProblem', 'raw_integrals': 'ElectronicEnergy.from_raw_integrals', 'orbital_basis': 'Gamma-point PySCF molecular orbitals', 'num_spatial_orbitals': 2, 'num_particles': [1, 1]}, 'scope': {'kpoint_mesh': [1, 1, 1], 'non_gamma_policy': 'rejected', 'spin_policy': 'closed_shell_rhf_only', 'periodic_images': 'PySCF PBC cell integrals at Gamma point'}, 'integration_recommendations': ['Use GammaCellProblem.problem anywhere the molecular builder expects an ElectronicStructureProblem.', 'Keep non-Gamma k-point workflows out of the mapped quantum-algorithm path until full k-point support exists.', 'Use qcchem.pbc.ewald for periodic QM/MM constant terms before adding them to hamiltonian.constants.']}}`

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
- term_count: `3`
- group_count: `2`
- estimated_shot_cost: `20000.0`
- runtime_precision_target: `0.01`
- uncompressed_group_count: `2`
- uncompressed_estimated_shot_cost: `20000.0`
- cost_reduction_ratio: `1.0`
- planner: `default`
- shadow_bases: `[]`
- shot_allocation: `[]`
- predicted_variance: `None`
- measurement_cost_model: `{}`
- notes: `["Measurement groups estimated with strategy 'default'.", 'Per-group shot estimate derived from precision target 0.01.', 'Measurement planning reflects the uncompressed execution path.']`

## Local Calibration Summary

> This section covers executed-solver calibration only; runtime-derived hardware evidence is tracked separately below.

- available: `True`
- measured_wall_time_seconds: `0.000101041001471458`
- measured_shot_usage: `None`
- precision_target: `0.01`
- achieved_error: `0.000000000000` Hartree
- estimated_measurement_cost: `20000.0`
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

- symmetry_check: `{'requested': True, 'effective_requested': False, 'performed': False, 'status': 'no_checks_requested', 'strategy': 'parity_placeholder', 'requested_checks': {'particle_number': False, 'spin_parity': False, 'z2_sector': False}, 'postselection_rate': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- readout_mitigation: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'calibration_shots': 0, 'calibration_digest': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- zne: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'folding': 'global', 'scale_factors': [1.0, 1.5, 2.0, 3.0], 'extrapolator': 'linear', 'zne_curve': [], 'variance_inflation': None, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'energy_replaces_primary': False}`
- pec: `{'requested': False, 'performed': False, 'status': 'not_requested', 'method': 'placeholder', 'calibration_model': None, 'calibration_model_audit': {'provided': False, 'exists': False, 'executable': False, 'status': 'missing_calibration_model', 'digest': None, 'schema': None, 'calibrated_operation_count': 0, 'quasi_probability_entry_count': 0, 'max_operation_l1_overhead': None}, 'executable_calibration_model': False, 'sampling_overhead': 0.0, 'allowed_for_claim': False, 'claim_status': 'not_requested', 'claim_scope': None, 'energy_replaces_primary': False}`
- requested_methods: `[]`
- applied_methods: `[]`
- claim_allowed_methods: `[]`
- claim_status: `not_requested`
- energy_replaces_primary: `False`

## Input Provenance

- source_1: kind=`inline_geometry` format=`inline` atom_count=`2` source_path=`None` resolved_path=`None` file_sha256=`None` normalized_geometry_sha256=`033faa492d62c4db3074109099b7adf0d22c80caea37a2d7514b7ecf510f5ff3`

## Provenance

- Schema version: `qcchem.result.v0.8-alpha`
- Timestamp: `2026-07-08T04:20:47.006419+00:00`
- Wall time (s): `2.1101574999993318`
- Git commit: `47612e92da7a8141c907ae3f4caee23a6463c39c`
- Git commit short: `47612e92da7a`
- Git branch: `HEAD`
- Git describe: `47612e9-dirty`
- Git remote origin: `https://github.com/wuls968/QCchem.git`
- Repo root: `/Users/a0000/.codex/worktrees/881e/QCchem`
- Workspace dirty: `True`
- Git status summary: `{'staged': 124, 'unstaged': 164, 'untracked': 41}`
- Workspace fingerprint: `fbcfccc9d5f78b049a19f6327e8cb7c7e61ff23d0dd7c47a0a6f0d99b69ef708`
- Dependency versions: `{'python': '3.12.2', 'qiskit': '2.4.2', 'qiskit_nature': '0.7.2', 'numpy': '1.26.4', 'scipy': '1.13.1', 'pyscf': '2.8.0', 'qiskit_aer': '0.17.2'}`
- Seed: `41`
- Source config: `/Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/pbc_h2_kq_pbc.yaml`

## Artifacts

- result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/result.json`
- exact_result.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/exact_result.json`
- report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/report.md`
- resolved_config.yaml: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/resolved_config.yaml`
- run.log: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/run.log`
- calibration.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/calibration.json`
- calibration_report.md: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/calibration_report.md`
- runtime_submission.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/runtime_submission.json`
- quantum_evidence.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/quantum_evidence.json`
- qcschema.json: `/Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/qcschema.json`
- result.h5: `None`

## Log Summary

- Loading config from /Users/a0000/.codex/worktrees/881e/QCchem/configs/exploratory/pbc_h2_kq_pbc.yaml
- Resolved molecular input: kind=inline_geometry, format=inline, atoms=2, sha256=033faa492d62
- Building electronic structure problem
- Applying mapping: jordan_wigner
- Prepared measurement plan: groups=2, cost=20000
- Skipping backend construction for solver: exact
- Running solver: exact
- Computing exact spectrum for 1 states
- Writing exact baseline artifact to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/exact_result.json
- Computed empirical calibration: wall_time=0.000s, measured_cost=None
- Wrote integrated method evidence sidecar
- Writing JSON result to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/result.json
- Writing Markdown report to /Users/a0000/.codex/worktrees/881e/QCchem/artifacts/method_evidence_suite_v1/cases/pbc_h2_kq_pbc/report.md
- Run completed
