from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.artifact_index import build_artifact_index_entry
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_h2_method_evidence_smoke_persists_sidecars_and_exports(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/h2_method_evidence_smoke.yaml"),
        output_dir=tmp_path / "method-evidence-smoke",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.method_evidence is not None
    assert result.artifacts.method_evidence_json is not None
    assert result.artifacts.method_evidence_json.exists()
    assert result.qsci_plus_result is not None
    assert result.post_correlation is not None
    assert result.ft_qpe_resource_estimate is not None
    assert result.measurement is not None
    assert result.measurement.planner == "shadow_lr"
    assert result.measurement.shadow_bases
    assert result.measurement.estimated_shot_cost == sum(
        int(item["shots"]) for item in result.measurement.shot_allocation
    )
    assert result.measurement.cost_reduction_ratio is not None
    assert result.measurement.cost_reduction_ratio < 1.0
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy
        + result.energy.external_point_charge_nuclear_interaction_energy
        + result.energy.boundary_embedding_constant_energy,
        abs=1.0e-10,
    )
    assert result.post_correlation.trust_gate == "unsupported_for_claim"
    assert result.post_correlation.external_correlation_energy is None
    assert result.post_correlation.total_corrected_energy is None
    assert result.post_correlation.double_counting_audit["status"] == "not_evaluated"
    assert result.post_correlation.correction_eligibility_audit["status"] == (
        "tcc_amplitude_mapping_audit_only"
    )
    assert result.post_correlation.correction_eligibility_audit["backend_executable"] is False
    assert result.post_correlation.amplitude_mapping_audit["status"] == (
        "constructed_for_audit_only"
    )
    assert result.post_correlation.amplitude_mapping_audit["mapped_double_count"] >= 1

    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    assert sidecar["schema"] == "qcchem.method_evidence.v1"
    assert set(sidecar["methods"]) >= {
        "qsci_plus_result",
        "post_correlation",
        "ft_qpe_resource_estimate",
        "trust_qem",
        "shadow_lr",
    }
    promotion_gate = sidecar["promotion_gate_audit"]
    assert promotion_gate["overall_claim_status"] == "promotion_required"
    assert promotion_gate["sidecar_energy_replacement_allowed_methods"] == []
    assert promotion_gate["accuracy_claim_allowed_methods"] == []
    assert "post_correlation" in promotion_gate["unsupported_for_claim_methods"]
    assert "shadow_lr" in promotion_gate["planning_metric_methods"]
    assert "ft_qpe_resource_estimate" in promotion_gate["resource_model_only_methods"]
    post_record = promotion_gate["method_records"]["post_correlation"]
    assert post_record["correction_eligibility_status"] == "tcc_amplitude_mapping_audit_only"
    assert post_record["amplitude_mapping_status"] == "constructed_for_audit_only"
    assert post_record["backend_executable"] is False
    ft_qpe = sidecar["methods"]["ft_qpe_resource_estimate"]
    assert ft_qpe["resource_formula_audit"]["scope"] == (
        "coarse_pauli_l1_phase_estimation_scaling"
    )
    assert ft_qpe["promotion_readiness_audit"]["status"] == (
        "blocked_missing_compiled_fault_tolerant_evidence"
    )
    assert ft_qpe["promotion_readiness_audit"]["readiness_level"] == (
        "resource_model_only_not_compiled"
    )
    assert ft_qpe["promotion_readiness_audit"][
        "validated_resource_advantage_claim_allowed"
    ] is False
    ft_qpe_record = promotion_gate["method_records"]["ft_qpe_resource_estimate"]
    assert ft_qpe_record["promotion_readiness_status"] == (
        "blocked_missing_compiled_fault_tolerant_evidence"
    )
    assert ft_qpe_record["resource_formula_scope"] == "coarse_pauli_l1_phase_estimation_scaling"
    shadow_record = promotion_gate["method_records"]["shadow_lr"]
    assert len(shadow_record["plan_digest"]) == 64
    assert 0.0 < shadow_record["basis_l1_coverage_fraction"] <= 1.0
    assert shadow_record["unselected_basis_count"] >= 0
    assert shadow_record["variance_inflation_vs_grouped_precision_proxy"] > 0.0

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["method_evidence"]["available"] is True
    assert payload["method_evidence"]["promotion_gate_audit"]["overall_claim_status"] == (
        "promotion_required"
    )
    assert payload["qsci_plus_result"]["selected_subspace_size"] >= 1
    assert payload["post_correlation"]["trust_gate"] == "unsupported_for_claim"
    assert payload["post_correlation"]["external_correlation_energy"] is None
    assert payload["post_correlation"]["total_corrected_energy"] is None
    assert payload["post_correlation"]["amplitude_mapping_audit"]["status"] == (
        "constructed_for_audit_only"
    )

    assert result.artifacts.qcschema_json is not None
    qcschema = json.loads(result.artifacts.qcschema_json.read_text(encoding="utf-8"))
    assert qcschema["extras"]["method_evidence"]["available"] is True
    assert qcschema["extras"]["method_evidence"]["promotion_gate_audit"][
        "overall_claim_status"
    ] == "promotion_required"
    assert qcschema["extras"]["qsci_plus_result"]["available"] is True

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Method Evidence" in report
    assert "QSCI++" in report
    assert "unsupported_for_claim" in report
    assert "amplitude_mapping_audit" in report
    assert "promotion_gate_audit" in report
    assert "FT-QPE Planner" in report

    index_entry = build_artifact_index_entry(result.artifacts.result_json)
    assert index_entry["has_method_evidence"] is True
    assert "qsci_plus_result" in index_entry["method_evidence_methods"]
    assert index_entry["has_method_evidence_promotion_gate_audit"] is True
    assert index_entry["method_evidence_promotion_gate_status"] == "promotion_required"
    assert index_entry["method_evidence_sidecar_energy_replacement_allowed_methods"] == []


@pytest.mark.integration
def test_trust_qem_records_claim_gate_without_replacing_primary_energy(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/h2_trust_qem.yaml"),
        output_dir=tmp_path / "trust-qem",
        exploratory_command=True,
    )

    assert result.verification_status == "validated"
    assert result.method_evidence is not None
    assert "trust_qem" in result.method_evidence.methods
    assert result.mitigation.requested_methods == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
        "pec",
    ]
    assert result.mitigation.applied_methods == ["symmetry_check", "readout_mitigation", "zne"]
    assert result.mitigation.claim_allowed_methods == []
    assert result.mitigation.claim_status == "unsupported_for_claim"
    assert result.mitigation.energy_replaces_primary is False
    assert result.mitigation.pec["status"] == "missing_calibration_model"
    assert result.mitigation.pec["allowed_for_claim"] is False
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy
        + result.energy.external_point_charge_nuclear_interaction_energy
        + result.energy.boundary_embedding_constant_energy,
        abs=1.0e-10,
    )

    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    trust_qem = sidecar["methods"]["trust_qem"]
    assert trust_qem["requested_methods"] == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
        "pec",
    ]
    assert trust_qem["claim_allowed_methods"] == []
    assert trust_qem["claim_status"] == "unsupported_for_claim"
    assert trust_qem["energy_replaces_primary"] is False
    assert trust_qem["primary_energy_policy"] == "raw_solver_energy_remains_primary"
    assert trust_qem["pec"]["status"] == "missing_calibration_model"
    gate = sidecar["promotion_gate_audit"]["method_records"]["trust_qem"]
    assert gate["claim_status"] == "unsupported_for_claim"
    assert gate["energy_replacement_allowed"] is False
    assert gate["accuracy_claim_allowed"] is False
    assert gate["hardware_claim_allowed"] is False
    assert "no_mitigation_component_allowed_for_energy_claim" in gate["promotion_blockers"]
    assert all(
        item["energy_evaluation_status"] == "not_evaluated"
        and item["energy_estimate_hartree"] is None
        and "energy_shift_proxy_hartree" not in item
        for item in trust_qem["zne"]["zne_curve"]
    )

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Trust-QEM" in report
    assert "claim_status: `unsupported_for_claim`" in report
    assert "energy_replaces_primary: `False`" in report


@pytest.mark.integration
def test_trust_qem_records_executable_pec_without_replacing_primary_energy(
    tmp_path: Path,
) -> None:
    result = run_from_config(
        Path("configs/exploratory/h2_trust_qem_calibrated_pec.yaml"),
        output_dir=tmp_path / "trust-qem-calibrated-pec",
        exploratory_command=True,
    )

    assert result.verification_status == "validated"
    assert result.method_evidence is not None
    assert result.mitigation.applied_methods == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
        "pec",
    ]
    assert result.mitigation.claim_allowed_methods == ["pec"]
    assert result.mitigation.claim_status == "claim_limited"
    assert result.mitigation.energy_replaces_primary is False
    assert result.mitigation.pec["status"] == "executable_calibration_model_recorded"
    assert result.mitigation.pec["executable_calibration_model"] is True
    assert result.mitigation.pec["allowed_for_claim"] is True
    assert result.mitigation.pec["energy_replaces_primary"] is False
    audit = result.mitigation.pec["calibration_model_audit"]
    assert audit["schema"] == "qcchem.pec_calibration_model.v1"
    assert audit["calibrated_operation_count"] == 2
    assert audit["quasi_probability_entry_count"] == 4
    assert audit["max_operation_l1_overhead"] == pytest.approx(1.16)
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy
        + result.energy.external_point_charge_nuclear_interaction_energy
        + result.energy.boundary_embedding_constant_energy,
        abs=1.0e-10,
    )

    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    trust_qem = sidecar["methods"]["trust_qem"]
    assert trust_qem["claim_allowed_methods"] == ["pec"]
    assert trust_qem["claim_status"] == "claim_limited"
    assert trust_qem["energy_replaces_primary"] is False
    assert trust_qem["pec"]["status"] == "executable_calibration_model_recorded"
    gate = sidecar["promotion_gate_audit"]["method_records"]["trust_qem"]
    assert gate["claim_status"] == "claim_limited"
    assert gate["energy_replacement_allowed"] is False
    assert gate["accuracy_claim_allowed"] is False
    assert gate["hardware_claim_allowed"] is False
    assert gate["pec_executable_calibration_model"] is True
    assert gate["pec_calibrated_operation_count"] == 2
    assert "mitigated_energy_does_not_replace_primary" in gate["promotion_blockers"]


@pytest.mark.integration
def test_q_sc_eom_links_transition_properties_and_conditioning_audit(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/h2_q_sc_eom.yaml"),
        output_dir=tmp_path / "q-sc-eom",
        exploratory_command=True,
    )

    assert result.method_evidence is not None
    assert result.excited_state_result is not None
    assert result.property_result is not None
    transition_properties = {
        item.property_name: item
        for item in result.property_result.properties
        if item.property_name in {"transition_dipole", "oscillator_strength"}
    }
    assert transition_properties["transition_dipole"].implementation_status == "validated"
    assert transition_properties["transition_dipole"].value is not None

    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    q_sc_eom = sidecar["methods"]["q_sc_eom"]
    assert q_sc_eom["energy_replaces_primary"] is False
    assert q_sc_eom["conditioning_status"] == "degenerate_subspace_tracking_required"
    assert q_sc_eom["overlap_condition_number"] >= 1.0
    assert q_sc_eom["overlap_condition_number"] < q_sc_eom["conditioning_audit"][
        "overlap_condition_threshold"
    ]
    assert q_sc_eom["max_root_residual_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert q_sc_eom["min_neighbor_gap_hartree"] == pytest.approx(0.0, abs=1.0e-8)
    assert q_sc_eom["root_tracking_statuses"] == ["degenerate_subspace"]

    conditioning = q_sc_eom["conditioning_audit"]
    assert conditioning["root_count"] == 2
    assert conditioning["degenerate_root_count"] == 2
    assert conditioning["regularization_actions"] == [
        "degenerate_subspace_root_tracking_required"
    ]
    assert conditioning["energy_replaces_primary"] is False

    transition_audit = q_sc_eom["transition_property_audit"]
    assert transition_audit["status"] == "validated_transition_properties_linked"
    assert transition_audit["requested_transition_property_count"] == 1
    assert transition_audit["validated_transition_property_count"] == 1
    assert transition_audit["property_names"] == ["transition_dipole"]
    assert transition_audit["state_pairs"] == [[0, 1]]
    assert transition_audit["max_transition_dipole_magnitude"] == pytest.approx(
        transition_properties["transition_dipole"].value
    )
    assert transition_audit["energy_replaces_primary"] is False
    assert q_sc_eom["transition_property_status"] == "validated_transition_properties_linked"
    assert q_sc_eom["validated_transition_property_count"] == 1
    assert q_sc_eom["transition_property_names"] == ["transition_dipole"]

    gate = sidecar["promotion_gate_audit"]["method_records"]["q_sc_eom"]
    assert gate["conditioning_status"] == "degenerate_subspace_tracking_required"
    assert gate["transition_property_status"] == "validated_transition_properties_linked"
    assert gate["validated_transition_property_count"] == 1
    assert gate["energy_replacement_allowed"] is False


@pytest.mark.integration
def test_q_embed_runs_as_fragment_reference_audit(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/h2_q_embed.yaml"),
        output_dir=tmp_path / "q-embed",
        exploratory_command=True,
    )

    assert result.verification_status == "validated"
    assert result.embedding_result is not None
    assert result.embedding_result.method == "q_dmet"
    assert result.embedding_result.verification_status == "exploratory"
    environment = result.embedding_result.environment_metadata
    boundary = environment["embedding_boundary_audit"]
    assert environment["embedding_execution_status"] == "fragment_reference_only"
    assert environment["self_consistency_loop_executed"] is False
    assert environment["self_consistency_converged"] is False
    assert environment["density_mismatch_history"][0]["status"] == "reference_audit_only"
    assert environment["density_mismatch_history"][0]["mismatch_status"] == (
        "balanced_reference_density"
    )
    assert environment["density_mismatch_history"][0]["density_mismatch_norm"] == pytest.approx(
        0.0,
        abs=1.0e-10,
    )
    assert environment["density_mismatch_history"][0]["density_mismatch_l1_norm"] == pytest.approx(
        0.0,
        abs=1.0e-10,
    )
    assert environment["density_mismatch_audit"]["status"] == "balanced_reference_density"
    assert environment["density_mismatch_audit"]["signed_sum"] == pytest.approx(0.0, abs=1.0e-10)
    assert environment["density_mismatch_audit"]["max_abs"] == pytest.approx(0.0, abs=1.0e-10)
    assert environment["density_mismatch_audit"]["density_matching_iteration_count"] == 0
    assert environment["fragment_coverage_audit"]["ao_coverage_fraction"] == pytest.approx(1.0)
    assert environment["fragment_coverage_audit"]["atom_coverage_fraction"] == pytest.approx(1.0)
    assert environment["fragment_coverage_audit"]["status"] == (
        "complete_nonoverlapping_fragment_coverage"
    )
    assert environment["self_consistency_iteration_count"] == 0
    assert environment["density_matching_iteration_count"] == 0
    assert environment["correlation_potential_parameter_count"] == 0
    assert environment["fragment_density_audit"]
    assert boundary["fragment_reference_execution_validated"] is True
    assert boundary["fragment_population_delta_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert boundary["fragment_population_delta_l1_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert boundary["fragment_population_delta_signed_sum"] == pytest.approx(0.0, abs=1.0e-10)
    assert boundary["density_mismatch_status"] == "balanced_reference_density"
    assert boundary["fragment_energy_sum_gap_hartree"] is not None
    assert boundary["fragment_energy_sum_gap_abs_hartree"] == pytest.approx(
        abs(boundary["fragment_energy_sum_gap_hartree"])
    )
    assert boundary["fragment_energy_sum_gap_per_fragment_hartree"] == pytest.approx(
        boundary["fragment_energy_sum_gap_hartree"] / 2.0
    )
    assert boundary["self_consistency_loop_executed"] is False
    assert boundary["self_consistency_iteration_count"] == 0
    assert boundary["density_matching_performed"] is False
    assert boundary["density_matching_iteration_count"] == 0
    assert boundary["correlation_potential_parameter_count"] == 0
    assert boundary["fragment_ao_coverage_fraction"] == pytest.approx(1.0)
    assert boundary["fragment_atom_coverage_fraction"] == pytest.approx(1.0)
    assert boundary["fragment_coverage_status"] == "complete_nonoverlapping_fragment_coverage"
    assert boundary["missing_self_consistency_components"] == [
        "correlation_potential_optimizer",
        "density_matching_loop",
        "bath_update_loop",
    ]
    assert boundary["fragment_energy_sum_replaces_primary"] is False
    assert [fragment["execution_result"]["method"] for fragment in result.embedding_result.fragments] == [
        "pyscf_uhf",
        "pyscf_uhf",
    ]
    assert [fragment["execution_result"]["fragment_spin"] for fragment in result.embedding_result.fragments] == [
        1,
        1,
    ]

    assert result.method_evidence is not None
    assert "q_embed" in result.method_evidence.methods
    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    q_embed = sidecar["methods"]["q_embed"]
    assert q_embed["embedding_execution_status"] == "fragment_reference_only"
    assert q_embed["density_mismatch_status"] == "reference_audit_only"
    assert q_embed["density_mismatch_audit_status"] == "balanced_reference_density"
    assert q_embed["fragment_population_delta_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert q_embed["fragment_population_delta_l1_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert q_embed["max_fragment_population_delta_abs"] == pytest.approx(0.0, abs=1.0e-10)
    assert q_embed["density_mismatch_threshold"] == pytest.approx(1.0e-8)
    assert q_embed["fragment_energy_sum_gap_hartree"] is not None
    assert q_embed["fragment_energy_sum_gap_abs_hartree"] == pytest.approx(
        abs(q_embed["fragment_energy_sum_gap_hartree"])
    )
    assert q_embed["self_consistency_loop_executed"] is False
    assert q_embed["self_consistency_iteration_count"] == 0
    assert q_embed["density_matching_performed"] is False
    assert q_embed["density_matching_iteration_count"] == 0
    assert q_embed["correlation_potential_parameter_count"] == 0
    assert q_embed["fragment_ao_coverage_fraction"] == pytest.approx(1.0)
    assert q_embed["fragment_atom_coverage_fraction"] == pytest.approx(1.0)
    assert q_embed["fragment_coverage_status"] == "complete_nonoverlapping_fragment_coverage"
    assert q_embed["fragment_energy_sum_replaces_primary"] is False
    assert q_embed["energy_replaces_primary"] is False
    gate = sidecar["promotion_gate_audit"]["method_records"]["q_embed"]
    assert gate["density_mismatch_audit_status"] == "balanced_reference_density"
    assert gate["fragment_coverage_status"] == "complete_nonoverlapping_fragment_coverage"
    assert gate["self_consistency_iteration_count"] == 0
    assert gate["density_matching_iteration_count"] == 0

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Embedding Audit" in report
    assert "fragment_reference_only" in report
    assert "self_consistency_loop_executed: `False`" in report


@pytest.mark.integration
def test_oo_qcasscf_records_casscf_reference_without_replacing_primary_energy(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/h2_oo_qcasscf.yaml"),
        output_dir=tmp_path / "oo-qcasscf",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.orbital_optimization is not None
    orbital = result.orbital_optimization
    assert orbital.trust_gate == "exploratory"
    assert orbital.reference_diagnostics["status"] == "computed"
    assert orbital.reference_diagnostics["backend"] == "pyscf.mcscf.CASSCF"
    assert orbital.reference_diagnostics["converged"] is True
    assert orbital.reference_diagnostics["energy_replaces_primary"] is False
    assert orbital.active_space_resolve["status"] == "not_applied_to_primary_solver"
    assert orbital.energy_scope_audit["energy_scope_consistent_for_total_gap"] is True
    assert orbital.orbital_transfer_audit["status"] == (
        "reference_orbitals_not_transferred_to_primary_solver"
    )
    assert orbital.orbital_transfer_audit["optimized_orbitals_applied_to_primary_solver"] is False
    assert orbital.orbital_transfer_audit[
        "primary_hamiltonian_rebuilt_from_optimized_orbitals"
    ] is False
    assert orbital.promotion_readiness_audit["status"] == "blocked_reference_diagnostic_only"
    assert orbital.promotion_readiness_audit["readiness_level"] == (
        "reference_diagnostic_not_solver_replacement"
    )
    assert orbital.promotion_readiness_audit["solver_replacement_allowed"] is False
    assert orbital.reference_diagnostics["energy_scope"] == "molecular_total_energy"
    assert orbital.reference_diagnostics["casscf_total_energy_hartree"] == pytest.approx(
        orbital.active_space_resolve["casscf_reference_total_energy_hartree"],
        abs=1.0e-12,
    )
    assert orbital.active_space_resolve["delegated_solver_hamiltonian_energy_hartree"] == pytest.approx(
        result.energy.solver_energy,
        abs=1.0e-12,
    )
    assert orbital.active_space_resolve["delegated_solver_total_energy_estimate_hartree"] == pytest.approx(
        result.energy.total_energy,
        abs=1.0e-12,
    )
    assert abs(orbital.active_space_resolve["casscf_minus_primary_total_energy_hartree"]) == pytest.approx(
        result.benchmark.absolute_error,
        abs=1.0e-10,
    )
    assert orbital.active_space_resolve["energy_replaces_primary"] is False
    assert orbital.energy_replaces_primary is False
    assert orbital.energy_lowering_hartree >= 0.0
    assert result.energy.solver_energy == pytest.approx(
        orbital.active_space_resolve["delegated_solver_energy_hartree"],
        abs=1.0e-12,
    )

    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    oo = sidecar["methods"]["orbital_optimization"]
    assert oo["reference_diagnostics"]["status"] == "computed"
    assert oo["active_space_resolve"]["status"] == "not_applied_to_primary_solver"
    assert oo["orbital_transfer_audit"]["optimized_orbitals_applied_to_primary_solver"] is False
    assert oo["energy_scope_audit"]["energy_scope_consistent_for_total_gap"] is True
    assert oo["promotion_readiness_audit"]["status"] == "blocked_reference_diagnostic_only"
    assert oo["energy_replaces_primary"] is False
    gate = sidecar["promotion_gate_audit"]["method_records"]["orbital_optimization"]
    assert gate["promotion_readiness_status"] == "blocked_reference_diagnostic_only"
    assert gate["solver_replacement_allowed"] is False

    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "OO-QCASSCF" in report
    assert "pyscf.mcscf.CASSCF" in report
    assert "energy_scope_audit" in report
    assert "promotion_readiness_audit" in report
    assert "energy_replaces_primary: `False`" in report


@pytest.mark.integration
def test_kq_pbc_runs_as_gamma_reference_audit(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/pbc_h2_kq_pbc.yaml"),
        output_dir=tmp_path / "kq-pbc",
        exploratory_command=True,
    )

    assert result.verification_status == "exploratory"
    assert result.kq_pbc_result is not None
    assert result.kq_pbc_result.kpoints == ["gamma", "x_half"]
    assert result.kq_pbc_result.finite_size_correction["status"] == "not_evaluated"
    assert result.kq_pbc_result.finite_size_correction["energy_correction_hartree"] is None
    assert result.kq_pbc_result.non_gamma_mapping_audit["status"] == "audit_only"
    assert result.kq_pbc_result.non_gamma_mapping_audit["execution_kpoint_mesh"] == [1, 1, 1]
    assert result.kq_pbc_result.non_gamma_mapping_audit["requested_kpoint_mesh"] == [2, 1, 1]
    assert result.kq_pbc_result.non_gamma_mapping_audit["mesh_mismatch"] is True
    assert result.kq_pbc_result.non_gamma_mapping_audit["requested_kpoint_count"] == 2
    assert result.kq_pbc_result.non_gamma_mapping_audit["execution_kpoint_count"] == 1
    assert result.kq_pbc_result.non_gamma_mapping_audit[
        "named_kpoint_execution_coverage_fraction"
    ] == pytest.approx(0.5)
    assert result.kq_pbc_result.non_gamma_mapping_audit[
        "mesh_kpoint_execution_coverage_fraction"
    ] == pytest.approx(0.5)
    assert result.kq_pbc_result.non_gamma_mapping_audit["executable_scope"] == "gamma_reference_hamiltonian_only"
    assert "non_gamma_quantum_mapping_not_executed" in result.kq_pbc_result.non_gamma_mapping_audit["promotion_blockers"]
    assert result.kq_pbc_result.non_gamma_mapping_audit["non_gamma_energy_available"] is False
    assert result.kq_pbc_result.finite_size_correction["missing_twist_energy_count"] == 2
    assert result.kq_pbc_result.finite_size_correction[
        "twist_energy_coverage_fraction"
    ] == pytest.approx(0.0)
    assert result.kq_pbc_result.finite_size_correction[
        "missing_twist_energy_fraction"
    ] == pytest.approx(1.0)
    readiness = result.kq_pbc_result.promotion_readiness_audit
    assert readiness["status"] == "blocked_exploratory_audit_only"
    assert readiness["readiness_level"] == "not_ready_for_validated_non_gamma_claim"
    assert readiness["coverage_audit"]["named_kpoint_execution_coverage_fraction"] == pytest.approx(0.5)
    assert readiness["coverage_audit"]["mesh_kpoint_execution_coverage_fraction"] == pytest.approx(0.5)
    assert readiness["coverage_audit"]["twist_energy_coverage_fraction"] == pytest.approx(0.0)
    assert readiness["coverage_audit"]["missing_twist_energy_fraction"] == pytest.approx(1.0)
    assert readiness["promotion_blocker_count"] == 4
    assert readiness["unsupported_claim_count"] == 4
    assert readiness["energy_replaces_primary"] is False
    assert readiness["runtime_submission_allowed"] is False
    assert result.kq_pbc_result.twist_energies
    assert all(item["energy_status"] == "not_evaluated" for item in result.kq_pbc_result.twist_energies)
    assert all(item["solver_energy_hartree"] is None for item in result.kq_pbc_result.twist_energies)
    assert all("solver_energy_proxy_hartree" not in item for item in result.kq_pbc_result.twist_energies)
    assert result.method_evidence is not None
    assert "kq_pbc_result" in result.method_evidence.methods
    sidecar = json.loads(result.artifacts.method_evidence_json.read_text(encoding="utf-8"))
    kq_pbc = sidecar["methods"]["kq_pbc_result"]
    assert kq_pbc["promotion_readiness_audit"]["status"] == "blocked_exploratory_audit_only"
    gate = sidecar["promotion_gate_audit"]["method_records"]["kq_pbc_result"]
    assert gate["promotion_readiness_status"] == "blocked_exploratory_audit_only"
    assert gate["named_kpoint_execution_coverage_fraction"] == pytest.approx(0.5)
    assert gate["twist_energy_coverage_fraction"] == pytest.approx(0.0)
    assert gate["missing_twist_energy_fraction"] == pytest.approx(1.0)
    assert gate["promotion_blocker_count"] == 4
    assert gate["unsupported_claim_count"] == 4
    assert gate["energy_replacement_allowed"] is False
    assert result.periodic_boundary is not None
    assert result.periodic_boundary.provenance["execution_kpoint_mesh"] == [1, 1, 1]
    assert result.periodic_boundary.provenance["requested_audit_kpoint_mesh"] == [2, 1, 1]
