from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.chem import build_electronic_structure_context
from qcchem.io.config import load_run_spec
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.reporting.markdown import write_markdown_report
from qcchem.solvers import ExactDiagonalizationSolver
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config


def _assert_artifact_bundle(result) -> None:
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    assert result.artifacts.resolved_config.exists()
    assert result.artifacts.log_file.exists()
    assert result.artifacts.exact_result_json.exists()


@pytest.mark.integration
def test_lih_workflow_runs_and_generates_complete_artifacts(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/lih.yaml"), output_dir=tmp_path / "lih-run")

    _assert_artifact_bundle(result)
    assert result.energy.energy_units == "Hartree"
    assert result.benchmark.exact_available is True
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy,
        abs=1e-10,
    )
    assert result.benchmark.comparison_target == "exact_baseline"
    assert result.energy.constant_energy_correction == pytest.approx(0.0, abs=1e-12)


@pytest.mark.integration
def test_h2o_active_space_workflow_runs_and_generates_complete_artifacts(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2o_active_space.yaml"), output_dir=tmp_path / "h2o-run")

    _assert_artifact_bundle(result)
    assert result.problem.active_space_metadata is not None
    assert "ActiveSpaceTransformer" in result.problem.transformers_applied
    assert result.benchmark.exact_available is True
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy,
        abs=1e-10,
    )
    assert result.energy.constant_energy_correction != pytest.approx(0.0, abs=1e-12)


@pytest.mark.integration
def test_jordan_wigner_and_bravyi_kitaev_match_on_h2_exact_energy() -> None:
    spec = load_run_spec(Path("configs/h2.yaml"))
    chemistry = build_electronic_structure_context(spec)
    exact = ExactDiagonalizationSolver()

    jw_mapping = map_fermionic_hamiltonian(chemistry.fermionic_hamiltonian, "jordan_wigner")
    bk_mapping = map_fermionic_hamiltonian(chemistry.fermionic_hamiltonian, "bravyi_kitaev")

    jw_energy = exact.solve(jw_mapping.qubit_hamiltonian).total_energy
    bk_energy = exact.solve(bk_mapping.qubit_hamiltonian).total_energy

    assert jw_energy == pytest.approx(bk_energy, abs=1e-10)


@pytest.mark.integration
def test_report_can_be_regenerated_from_result_json(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2.yaml"), output_dir=tmp_path / "report-run")
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))

    regenerated_path = tmp_path / "regenerated.md"
    write_markdown_report(payload, regenerated_path)

    assert regenerated_path.exists()
    report_text = regenerated_path.read_text(encoding="utf-8")
    assert "Benchmark" in report_text
    assert "energy_formula" in report_text


@pytest.mark.integration
def test_benchmark_run_exposes_environment_embedding_delta_metrics(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "environment.xyzq").write_text(
        "mm_probe 0.0 0.0 2.0 -0.5\n",
        encoding="utf-8",
    )
    cache_dir = tmp_path / "effective_cache"
    config_path = tmp_path / "h2_environment_embedding.yaml"
    config_path.write_text(
        f"""
molecule:
  name: H2-benchmark-environment-embedding
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
  unit: angstrom
problem:
  environment_embedding:
    enabled: true
    point_charges:
      enabled: true
      unit: angstrom
      source_file: data/environment.xyzq
      damping:
        kind: gaussian
        default_radius: 0.4
        radius_unit: angstrom
    cache:
      enabled: true
      directory: {cache_dir}
mapping:
  kind: jordan_wigner
backend:
  kind: statevector
solver:
  kind: exact
benchmark:
  enabled: true
  exact_baseline_qubit_limit: 12
run:
  output_dir: artifacts/h2_environment_embedding
  overwrite: true
        """.strip(),
        encoding="utf-8",
    )
    suite_path = tmp_path / "environment_suite.yaml"
    suite_path.write_text(
        f"""
benchmark_suite:
  name: environment_embedding_suite
  cases:
    - name: h2_environment_run
      kind: run
      config: {config_path}
      expected_status: validated
        """.strip(),
        encoding="utf-8",
    )

    result = run_benchmark_suite_from_config(suite_path, output_dir=tmp_path / "benchmark-env")

    case = result.cases[0]
    assert case.metrics["environment_embedding_enabled"] is True
    assert case.metrics["environment_cache_enabled"] is True
    assert case.metrics["environment_cache_hit"] is False
    assert case.metrics["environment_hcore_delta_frobenius_norm"] > 0.0
    assert case.metrics["environment_qubit_growth"] == 0
    assert case.metrics["environment_mapping_tapered_qubit_delta"] == 0


@pytest.mark.integration
def test_lr_ace_flagship_benchmark_suite_accepts_fast_gates(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/lr_ace_flagship_suite_v1.yaml"),
        output_dir=tmp_path / "lr-ace-flagship-suite",
        include_tags=["fast"],
    )

    assert result.summary.total_cases == 2
    assert result.summary.status_counts["validated"] == 2
    assert result.acceptance_summary is not None
    assert result.acceptance_summary["accepted"] is True
    assert result.calibration_summary["case_filter"]["include_tags"] == ["fast"]
    assert result.calibration_summary["case_filter"]["selected_cases"] == [
        "h2_lr_ace_flagship",
        "lih_active_lr_ace_flagship",
    ]
    assert {
        item["name"] for item in result.calibration_summary["case_filter"]["skipped_cases"]
    } == {
        "h2o_active_lr_ace_adaptive",
        "h3plus_lr_ace_adaptive",
        "h4_chain_lr_ace_adaptive",
    }
    fast_cases = [
        case
        for case in result.cases
        if case.name in {"h2_lr_ace_flagship", "lih_active_lr_ace_flagship"}
    ]
    assert {case.name for case in fast_cases} >= {
        "h2_lr_ace_flagship",
        "lih_active_lr_ace_flagship",
    }
    assert all(case.status == "validated" for case in fast_cases)


@pytest.mark.integration
def test_method_evidence_benchmark_suite_records_comparison_metrics(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/method_evidence_suite_v1.yaml"),
        output_dir=tmp_path / "method-evidence-suite",
        include_tags=["fast"],
    )

    cases = {case.name: case for case in result.cases}
    assert result.summary.total_cases == 12
    assert result.acceptance_summary is not None
    assert result.acceptance_summary["accepted"] is True
    assert result.artifacts is not None
    assert (result.artifacts.root / "method_evidence_summary.json").exists()
    assert result.artifact_index_entry is not None
    assert result.artifact_index_entry["has_method_evidence_summary"] is True
    assert result.artifact_index_entry["method_evidence_method_case_count"] == 10
    assert result.artifact_index_entry["method_evidence_ft_qpe_resource_case_count"] == 2
    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "## Method Evidence Campaign" in report_text
    assert "No method-evidence case in this stable fast gate beats" in report_text
    assert "planning_metric_cost_advantage_pairs" in report_text
    assert "promotion_gate_summary" in report_text
    assert "contract_matrix_status: `complete`" in report_text
    method_summary = result.calibration_summary["method_evidence_campaign"]
    assert method_summary["available"] is True
    assert method_summary["method_case_count"] == 10
    assert set(method_summary["method_counts"]) == {
        "e_adapt_result",
        "ft_qpe_resource_estimate",
        "kq_pbc_result",
        "orbital_optimization",
        "post_correlation",
        "q_embed",
        "q_sc_eom",
        "qsci_plus_result",
        "shadow_lr",
        "trust_qem",
    }
    contract_matrix = method_summary["contract_matrix"]
    assert contract_matrix["status"] == "complete"
    assert contract_matrix["expected_method_count"] == 10
    assert contract_matrix["covered_method_count"] == 10
    assert contract_matrix["missing_methods"] == []
    assert set(contract_matrix["methods"]) == set(method_summary["method_counts"])
    required_contract_surfaces = {
        "result_method_summary_present",
        "result_detail_present",
        "sidecar_method_present",
        "promotion_gate_record_present",
        "report_mentions_method",
        "qcschema_file_present",
        "qcschema_method_summary_present",
        "metric_keys_present",
    }
    for method_key, entry in contract_matrix["methods"].items():
        assert entry["contract_passed"] is True, method_key
        assert entry["case_count"] >= 1, method_key
        assert entry["passing_case_count"] == entry["case_count"], method_key
        for row in entry["cases"]:
            assert row["contract_passed"] is True, (method_key, row["case_name"])
            for surface in required_contract_surfaces:
                assert row[surface] is True, (method_key, row["case_name"], surface)
    assert "e_adapt_adaptive_energy_replaces_delegate" in contract_matrix["methods"][
        "e_adapt_result"
    ]["metric_keys"]
    assert "e_adapt_min_selected_energy_lowering_hartree" in contract_matrix["methods"][
        "e_adapt_result"
    ]["metric_keys"]
    assert "e_adapt_optimization_signal_present" in contract_matrix["methods"][
        "e_adapt_result"
    ]["metric_keys"]
    assert "e_adapt_delegate_improvement_to_replacement_threshold_ratio" in contract_matrix[
        "methods"
    ]["e_adapt_result"]["metric_keys"]
    assert "orbital_optimization_energy_replaces_primary" in contract_matrix["methods"][
        "orbital_optimization"
    ]["metric_keys"]
    assert "post_correlation_double_counting_status" in contract_matrix["methods"][
        "post_correlation"
    ]["metric_keys"]
    assert "qsci_selected_origin_counts" in contract_matrix["methods"][
        "qsci_plus_result"
    ]["metric_keys"]
    assert "q_embed_density_matching_performed" in contract_matrix["methods"][
        "q_embed"
    ]["metric_keys"]
    assert "kq_pbc_proxy_energy_present" in contract_matrix["methods"][
        "kq_pbc_result"
    ]["metric_keys"]
    assert "trust_qem_pec_allowed_for_claim" in contract_matrix["methods"][
        "trust_qem"
    ]["metric_keys"]
    assert "trust_qem_pec_calibrated_operation_count" in contract_matrix["methods"][
        "trust_qem"
    ]["metric_keys"]
    assert "ft_qpe_compiled_circuit_available" in contract_matrix["methods"][
        "ft_qpe_resource_estimate"
    ]["metric_keys"]
    assert result.artifact_index_entry["method_evidence_contract_matrix_status"] == "complete"
    assert result.artifact_index_entry["method_evidence_contract_covered_method_count"] == 10
    assert result.artifact_index_entry["method_evidence_contract_expected_method_count"] == 10
    assert result.artifact_index_entry["method_evidence_contract_missing_methods"] == []
    assert result.artifact_index_entry["method_evidence_superiority_audit_status"] == (
        "promotion_required"
    )
    assert result.artifact_index_entry["method_evidence_superiority_claim_allowed_methods"] == []
    assert result.artifact_index_entry["method_evidence_superiority_method_count"] == 10
    promotion_summary = method_summary["promotion_gate_summary"]
    assert promotion_summary["case_count"] == 10
    assert promotion_summary["energy_replacement_allowed_cases"] == []
    assert promotion_summary["accuracy_claim_allowed_cases"] == []
    assert promotion_summary["hardware_claim_allowed_cases"] == []
    assert promotion_summary["overall_claim_status"] == "promotion_required"
    superiority_audit = method_summary["method_superiority_audit"]
    assert superiority_audit["status"] == "promotion_required"
    assert superiority_audit["claim_allowed_methods"] == []
    assert superiority_audit["method_count"] == 10
    assert set(superiority_audit["methods"]) == set(method_summary["method_counts"])
    assert all(
        row["accuracy_claim_allowed"] is False
        and row["energy_replacement_allowed"] is False
        and row["hardware_claim_allowed"] is False
        for row in superiority_audit["methods"].values()
    )
    assert superiority_audit["methods"]["qsci_plus_result"]["superiority_conclusion"] == (
        "matches_exact_smoke_not_superior"
    )
    assert superiority_audit["methods"]["shadow_lr"]["superiority_conclusion"] == (
        "planning_cost_advantage_only"
    )
    assert superiority_audit["methods"]["ft_qpe_resource_estimate"][
        "superiority_conclusion"
    ] == "resource_model_advantage_only"
    assert superiority_audit["methods"]["e_adapt_result"][
        "planning_metric_cost_advantage_pair_names"
    ] == []
    assert superiority_audit["methods"]["e_adapt_result"][
        "method_specific_estimated_cost_advantage_pair_names"
    ] == []
    assert superiority_audit["methods"]["e_adapt_result"][
        "pair_level_only_estimated_cost_advantage_pair_names"
    ] == ["lih_shadow_lr_e_adapt_vs_lih_active_vqe_statevector_baseline"]
    assert superiority_audit["methods"]["e_adapt_result"][
        "optimization_signal_case_names"
    ] == ["lih_shadow_lr_e_adapt"]
    assert superiority_audit["methods"]["e_adapt_result"][
        "superiority_conclusion"
    ] == "optimization_signal_requires_promotion"
    assert "optimization_signal_requires_accuracy_gate" in superiority_audit["methods"][
        "e_adapt_result"
    ]["promotion_blockers"]
    assert "accuracy_claim_not_allowed" in superiority_audit["methods"]["shadow_lr"][
        "promotion_blockers"
    ]
    assert "resource_model_only_no_compiled_circuit" in superiority_audit["methods"][
        "ft_qpe_resource_estimate"
    ]["promotion_blockers"]

    ideal_baseline = cases["lih_active_vqe_statevector_baseline"]
    e_adapt = cases["lih_shadow_lr_e_adapt"]
    assert ideal_baseline.absolute_error is not None
    assert e_adapt.absolute_error is not None
    assert ideal_baseline.absolute_error <= e_adapt.absolute_error
    assert "e_adapt_result" in e_adapt.metrics["method_evidence_methods"]
    assert "shadow_lr" in e_adapt.metrics["method_evidence_methods"]
    assert e_adapt.metrics["e_adapt_selected_operator_count"] >= 1
    assert e_adapt.metrics["e_adapt_pool_origins"] == ["ansatz_excitation_operators"]
    assert e_adapt.metrics["e_adapt_adaptive_energy_replaces_delegate"] is False
    assert e_adapt.metrics["e_adapt_replacement_min_improvement_hartree"] == pytest.approx(1.0e-6)
    assert e_adapt.metrics["e_adapt_min_selected_energy_lowering_hartree"] > 0.0
    assert e_adapt.metrics["e_adapt_optimization_signal_present"] is True
    assert e_adapt.metrics["e_adapt_adaptive_improvement_status"] == (
        "positive_below_replacement_threshold"
    )
    assert 0.0 < e_adapt.metrics[
        "e_adapt_delegate_improvement_to_replacement_threshold_ratio"
    ] < 1.0
    assert e_adapt.metrics["e_adapt_cumulative_selected_energy_lowering_hartree"] >= (
        e_adapt.metrics["e_adapt_min_selected_energy_lowering_hartree"]
    )
    assert e_adapt.metrics["e_adapt_final_cumulative_two_qubit_increment"] >= 0
    assert e_adapt.metrics["e_adapt_adaptive_evaluations_per_selected_operator"] > 0.0
    assert e_adapt.metrics["e_adapt_no_improvement_rejection_count"] >= 0
    assert e_adapt.metrics["e_adapt_operator_acceptance_min_improvement_hartree"] == 0.0
    assert e_adapt.metrics["shadow_lr_basis_count"] >= 1
    assert e_adapt.metrics["shadow_lr_allocated_shots"] == 1024
    assert e_adapt.metrics["shadow_lr_grouped_precision_baseline_shots"] == 40000.0
    assert e_adapt.metrics["estimated_measurement_cost"] == 1024.0
    assert e_adapt.metrics["shadow_lr_cost_reduction_vs_grouped_precision"] == pytest.approx(
        1024.0 / 40000.0
    )
    assert 0.0 < e_adapt.metrics["shadow_lr_basis_l1_coverage_fraction"] <= 1.0
    assert e_adapt.metrics["shadow_lr_unselected_basis_count"] >= 0
    assert 0.0 <= e_adapt.metrics["shadow_lr_max_allocated_shot_fraction"] <= 1.0
    assert 0.0 <= e_adapt.metrics["shadow_lr_allocation_entropy"] <= 1.0
    assert e_adapt.metrics["shadow_lr_grouped_precision_variance_proxy"] > 0.0
    assert e_adapt.metrics[
        "shadow_lr_variance_inflation_vs_grouped_precision_proxy"
    ] == pytest.approx(40000.0 / 1024.0)
    assert len(e_adapt.metrics["shadow_lr_plan_digest"]) == 64
    e_adapt_pair = method_summary["comparison_pairs"][
        "lih_shadow_lr_e_adapt_vs_lih_active_vqe_statevector_baseline"
    ]
    assert e_adapt_pair["accuracy_outcome"] == "higher_error"
    assert e_adapt_pair["estimated_cost_ratio_method_over_baseline"] == pytest.approx(
        1024.0 / 40000.0
    )
    assert "lih_shadow_lr_e_adapt_vs_lih_active_vqe_statevector_baseline" in method_summary[
        "estimated_cost_advantage_pairs"
    ]
    assert "h2_trust_qem_vs_h2_exact_baseline" in method_summary[
        "estimated_cost_advantage_pairs"
    ]
    assert "h2_trust_qem_vs_h2_exact_baseline" not in method_summary[
        "planning_metric_cost_advantage_pairs"
    ]
    assert "lih_shadow_lr_e_adapt_vs_lih_active_vqe_statevector_baseline" in method_summary[
        "planning_metric_cost_advantage_pairs"
    ]
    assert e_adapt.metrics["method_evidence_promotion_gate_status"] == "promotion_required"
    assert e_adapt.metrics["method_evidence_sidecar_energy_replacement_allowed_methods"] == []
    assert e_adapt.metrics["method_evidence_accuracy_claim_allowed_methods"] == []
    assert "shadow_lr" in e_adapt.metrics["method_evidence_planning_metric_methods"]
    assert "lih_shadow_lr_e_adapt" in promotion_summary["planning_metric_cases"]

    oo_qcasscf = cases["h2_oo_qcasscf"]
    assert "orbital_optimization" in oo_qcasscf.metrics["method_evidence_methods"]
    assert oo_qcasscf.metrics["orbital_optimization_reference_status"] == "computed"
    assert oo_qcasscf.metrics["orbital_optimization_reference_backend"] == "pyscf.mcscf.CASSCF"
    assert oo_qcasscf.metrics["orbital_optimization_casscf_converged"] is True
    assert oo_qcasscf.metrics["orbital_optimization_energy_replaces_primary"] is False
    assert oo_qcasscf.metrics["orbital_optimization_active_space_resolve_status"] == (
        "not_applied_to_primary_solver"
    )
    assert oo_qcasscf.metrics["orbital_optimization_energy_scope_consistent"] is True
    assert oo_qcasscf.metrics["orbital_optimization_promotion_readiness_status"] == (
        "blocked_reference_diagnostic_only"
    )
    assert oo_qcasscf.metrics["orbital_optimization_readiness_level"] == (
        "reference_diagnostic_not_solver_replacement"
    )
    assert oo_qcasscf.metrics["orbital_optimization_solver_replacement_allowed"] is False
    assert oo_qcasscf.metrics["orbital_optimization_optimized_orbitals_applied"] is False
    assert oo_qcasscf.metrics["orbital_optimization_primary_hamiltonian_rebuilt"] is False
    assert oo_qcasscf.metrics["orbital_optimization_required_promotion_evidence_count"] == 5
    assert oo_qcasscf.metrics["orbital_optimization_promotion_blocker_count"] == 4
    assert oo_qcasscf.metrics["orbital_optimization_primary_total_energy_estimate"] is not None
    assert oo_qcasscf.metrics["orbital_optimization_casscf_total_energy"] is not None
    assert oo_qcasscf.metrics["orbital_optimization_abs_casscf_primary_total_gap"] == pytest.approx(
        oo_qcasscf.absolute_error,
        abs=1.0e-10,
    )

    qsci = cases["h2_qsci_plus"]
    assert "qsci_plus_result" in qsci.metrics["method_evidence_methods"]
    assert qsci.metrics["qsci_selected_subspace_size"] >= 1
    assert qsci.metrics["qsci_selected_sector_coverage_fraction"] == pytest.approx(1.0)
    assert qsci.metrics["qsci_variance_estimate"] == pytest.approx(0.0, abs=1.0e-20)
    assert qsci.metrics["qsci_ground_state_residual_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert qsci.metrics["qsci_external_coupling_residual_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert qsci.metrics["qsci_variational_upper_bound_margin_hartree"] >= -1.0e-8
    assert qsci.metrics["qsci_selected_origin_counts"] == {"sampled": 4}
    assert qsci.metrics["qsci_selected_multi_origin_counts"]["sector_repaired"] == 4
    assert qsci.metrics["qsci_hartree_fock_selected"] is True
    assert qsci.metrics["qsci_hamming_expansion_radius"] == 1
    assert qsci.metrics["post_correlation_method"] == "qsci_nevpt2"
    assert qsci.metrics["post_correlation_trust_gate"] == "unsupported_for_claim"
    assert qsci.metrics["post_correlation_double_counting_status"] == "not_evaluated"
    assert qsci.metrics["post_correlation_eligibility_status"] == "coefficient_provenance_only"
    assert qsci.metrics["post_correlation_amplitude_mapping_status"] == "not_applicable_to_nevpt2"
    assert qsci.metrics["post_correlation_backend_executable"] is False
    assert qsci.metrics["post_correlation_correction_energy_emitted"] is False
    assert qsci.metrics["post_correlation_required_input_missing_count"] == 4
    assert qsci.metrics["post_correlation_external_energy"] is None
    assert qsci.metrics["post_correlation_total_corrected_energy"] is None
    assert "post_correlation" in qsci.metrics["method_evidence_unsupported_for_claim_methods"]
    assert "h2_qsci_plus" in promotion_summary["unsupported_for_claim_cases"]
    assert method_summary["comparison_pairs"]["h2_qsci_plus_vs_h2_exact_baseline"][
        "accuracy_outcome"
    ] == "matches_exact_within_tolerance"

    smoke = cases["h2_method_evidence_smoke"]
    assert smoke.metrics["post_correlation_method"] == "qsci_tcc"
    assert smoke.metrics["post_correlation_eligibility_status"] == (
        "tcc_amplitude_mapping_audit_only"
    )
    assert smoke.metrics["post_correlation_amplitude_mapping_status"] == (
        "constructed_for_audit_only"
    )
    assert smoke.metrics["post_correlation_mapped_double_count"] >= 1
    assert smoke.metrics["post_correlation_backend_executable"] is False
    assert smoke.metrics["post_correlation_correction_energy_emitted"] is False
    assert smoke.metrics["post_correlation_energy_replaces_primary"] is False

    trust_qem = cases["h2_trust_qem"]
    assert "trust_qem" in trust_qem.metrics["method_evidence_methods"]
    assert trust_qem.metrics["trust_qem_requested_methods"] == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
        "pec",
    ]
    assert trust_qem.metrics["trust_qem_applied_methods"] == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
    ]
    assert trust_qem.metrics["trust_qem_claim_allowed_methods"] == []
    assert trust_qem.metrics["trust_qem_claim_status"] == "unsupported_for_claim"
    assert trust_qem.metrics["trust_qem_energy_replaces_primary"] is False
    assert trust_qem.metrics["trust_qem_pec_status"] == "missing_calibration_model"
    assert trust_qem.metrics["trust_qem_pec_executable_calibration_model"] is False
    assert trust_qem.metrics["trust_qem_pec_allowed_for_claim"] is False
    assert "trust_qem" in trust_qem.metrics["method_evidence_unsupported_for_claim_methods"]

    calibrated_pec = cases["h2_trust_qem_calibrated_pec"]
    assert "trust_qem" in calibrated_pec.metrics["method_evidence_methods"]
    assert calibrated_pec.metrics["trust_qem_applied_methods"] == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
        "pec",
    ]
    assert calibrated_pec.metrics["trust_qem_claim_allowed_methods"] == ["pec"]
    assert calibrated_pec.metrics["trust_qem_claim_status"] == "claim_limited"
    assert calibrated_pec.metrics["trust_qem_energy_replaces_primary"] is False
    assert calibrated_pec.metrics["trust_qem_pec_status"] == (
        "executable_calibration_model_recorded"
    )
    assert calibrated_pec.metrics["trust_qem_pec_executable_calibration_model"] is True
    assert calibrated_pec.metrics["trust_qem_pec_allowed_for_claim"] is True
    assert calibrated_pec.metrics["trust_qem_pec_calibrated_operation_count"] == 2
    assert calibrated_pec.metrics["trust_qem_pec_quasi_probability_entry_count"] == 4
    assert calibrated_pec.metrics["trust_qem_pec_max_operation_l1_overhead"] == pytest.approx(
        1.16
    )
    assert calibrated_pec.metrics["trust_qem_pec_sampling_overhead"] == 25.0
    assert len(calibrated_pec.metrics["trust_qem_pec_calibration_model_digest"]) == 64
    assert calibrated_pec.metrics["method_evidence_sidecar_energy_replacement_allowed_methods"] == []
    assert calibrated_pec.metrics["method_evidence_accuracy_claim_allowed_methods"] == []

    q_sc_eom = cases["h2_q_sc_eom"]
    assert "q_sc_eom" in q_sc_eom.metrics["method_evidence_methods"]
    assert q_sc_eom.metrics["q_sc_eom_state_count"] == 2
    assert q_sc_eom.metrics["q_sc_eom_max_root_residual_norm"] == pytest.approx(0.0, abs=1.0e-10)
    assert q_sc_eom.metrics["q_sc_eom_min_neighbor_gap_hartree"] == pytest.approx(0.0, abs=1.0e-8)
    assert q_sc_eom.metrics["q_sc_eom_conditioning_status"] == (
        "degenerate_subspace_tracking_required"
    )
    assert q_sc_eom.metrics["q_sc_eom_overlap_condition_number"] >= 1.0
    assert q_sc_eom.metrics["q_sc_eom_overlap_condition_number"] < 1.0e8
    assert q_sc_eom.metrics["q_sc_eom_regularization_actions"] == [
        "degenerate_subspace_root_tracking_required"
    ]
    assert q_sc_eom.metrics["q_sc_eom_degenerate_root_count"] == 2
    assert q_sc_eom.metrics["q_sc_eom_root_tracking_statuses"] == ["degenerate_subspace"]
    assert q_sc_eom.metrics["q_sc_eom_transition_property_status"] == (
        "validated_transition_properties_linked"
    )
    assert q_sc_eom.metrics["q_sc_eom_transition_property_count"] == 1
    assert q_sc_eom.metrics["q_sc_eom_validated_transition_property_count"] == 1
    assert q_sc_eom.metrics["q_sc_eom_transition_property_names"] == ["transition_dipole"]
    assert q_sc_eom.metrics["q_sc_eom_transition_state_pairs"] == [[0, 1]]
    assert q_sc_eom.metrics["q_sc_eom_max_transition_dipole_magnitude"] is not None

    q_embed = cases["h2_q_embed"]
    assert "q_embed" in q_embed.metrics["method_evidence_methods"]
    assert q_embed.metrics["q_embed_verification_status"] == "exploratory"
    assert q_embed.metrics["q_embed_fragment_count"] == 2
    assert q_embed.metrics["q_embed_execution_status"] == "fragment_reference_only"
    assert q_embed.metrics["q_embed_self_consistency_loop_executed"] is False
    assert q_embed.metrics["q_embed_self_consistency_iteration_count"] == 0
    assert q_embed.metrics["q_embed_density_matching_performed"] is False
    assert q_embed.metrics["q_embed_density_matching_iteration_count"] == 0
    assert q_embed.metrics["q_embed_density_mismatch_status"] == "reference_audit_only"
    assert q_embed.metrics["q_embed_density_mismatch_audit_status"] == (
        "balanced_reference_density"
    )
    assert q_embed.metrics["q_embed_fragment_population_delta_norm"] == pytest.approx(
        0.0,
        abs=1.0e-10,
    )
    assert q_embed.metrics["q_embed_density_mismatch_l1_norm"] == pytest.approx(
        0.0,
        abs=1.0e-10,
    )
    assert q_embed.metrics["q_embed_density_mismatch_signed_sum"] == pytest.approx(
        0.0,
        abs=1.0e-10,
    )
    assert q_embed.metrics["q_embed_density_mismatch_threshold"] == pytest.approx(1.0e-8)
    assert q_embed.metrics["q_embed_max_fragment_population_delta_abs"] == pytest.approx(
        0.0,
        abs=1.0e-10,
    )
    assert q_embed.metrics["q_embed_correlation_potential_parameter_count"] == 0
    assert q_embed.metrics["q_embed_fragment_ao_coverage_fraction"] == pytest.approx(1.0)
    assert q_embed.metrics["q_embed_fragment_atom_coverage_fraction"] == pytest.approx(1.0)
    assert q_embed.metrics["q_embed_fragment_coverage_status"] == (
        "complete_nonoverlapping_fragment_coverage"
    )
    assert q_embed.metrics["q_embed_fragment_energy_sum_gap_hartree"] is not None
    assert q_embed.metrics["q_embed_fragment_energy_sum_gap_abs_hartree"] == pytest.approx(
        abs(q_embed.metrics["q_embed_fragment_energy_sum_gap_hartree"])
    )
    assert q_embed.metrics["q_embed_fragment_energy_sum_gap_per_fragment_hartree"] == pytest.approx(
        q_embed.metrics["q_embed_fragment_energy_sum_gap_hartree"] / 2.0
    )
    assert q_embed.metrics["q_embed_fragment_energy_sum_replaces_primary"] is False

    ft_qpe = cases["h2_ft_qpe_planner"]
    assert ft_qpe.metrics["ft_qpe_recommended_encoding"] == "tensor_hypercontraction"
    assert ft_qpe.metrics["ft_qpe_reduction_vs_double_factorization"] > 0.0
    assert ft_qpe.metrics["ft_qpe_best_to_reference_toffoli_ratio"] == pytest.approx(0.65)
    assert ft_qpe.metrics["ft_qpe_lambda_reduction_vs_double_factorization"] == pytest.approx(0.35)
    assert ft_qpe.metrics["ft_qpe_resource_model_scope"] == "coarse_pauli_l1_phase_estimation_scaling"
    assert ft_qpe.metrics["ft_qpe_resource_formula_scope"] == (
        "coarse_pauli_l1_phase_estimation_scaling"
    )
    assert ft_qpe.metrics["ft_qpe_reference_encoding"] == "double_factorization"
    assert ft_qpe.metrics["ft_qpe_encoding_comparison_count"] == 3
    assert ft_qpe.metrics["ft_qpe_resource_claim_status"] == "resource_model_only"
    assert ft_qpe.metrics["ft_qpe_promotion_readiness_status"] == (
        "blocked_missing_compiled_fault_tolerant_evidence"
    )
    assert ft_qpe.metrics["ft_qpe_readiness_level"] == "resource_model_only_not_compiled"
    assert ft_qpe.metrics["ft_qpe_compiled_circuit_available"] is False
    assert ft_qpe.metrics["ft_qpe_surface_code_distance_available"] is False
    assert ft_qpe.metrics["ft_qpe_logical_error_budget_available"] is False
    assert ft_qpe.metrics["ft_qpe_validated_resource_advantage_claim_allowed"] is False
    assert ft_qpe.metrics["ft_qpe_required_promotion_evidence_count"] == 5
    assert ft_qpe.metrics["ft_qpe_surface_code_overhead_factor"] == 1000
    assert "no_compiled_fault_tolerant_circuit" in ft_qpe.metrics["ft_qpe_promotion_blockers"]
    assert "ft_qpe_resource_estimate" in ft_qpe.metrics[
        "method_evidence_resource_model_only_methods"
    ]
    assert "h2_ft_qpe_planner" in promotion_summary["resource_model_only_cases"]
    assert method_summary["ft_qpe_resource_findings"]["h2_ft_qpe_planner"][
        "toffoli_reduction_vs_double_factorization"
    ] > 0.0
    assert method_summary["ft_qpe_resource_findings"]["h2_ft_qpe_planner"][
        "resource_claim_status"
    ] == "resource_model_only"
    assert method_summary["ft_qpe_resource_findings"]["h2_ft_qpe_planner"][
        "promotion_readiness_status"
    ] == "blocked_missing_compiled_fault_tolerant_evidence"
    assert method_summary["ft_qpe_resource_findings"]["h2_ft_qpe_planner"][
        "readiness_level"
    ] == "resource_model_only_not_compiled"
    assert method_summary["ft_qpe_resource_findings"]["h2_ft_qpe_planner"][
        "compiled_circuit_available"
    ] is False

    kq_pbc = cases["pbc_h2_kq_pbc"]
    assert kq_pbc.metrics["kq_pbc_trust_tier"] == "exploratory"
    assert kq_pbc.metrics["kq_pbc_kpoint_count"] == 2
    assert kq_pbc.metrics["kq_pbc_twist_energy_statuses"] == ["not_evaluated"]
    assert kq_pbc.metrics["kq_pbc_non_gamma_status"] == "audit_only"
    assert kq_pbc.metrics["kq_pbc_mesh_mismatch"] is True
    assert kq_pbc.metrics["kq_pbc_named_kpoint_coverage_fraction"] == pytest.approx(0.5)
    assert kq_pbc.metrics["kq_pbc_mesh_kpoint_coverage_fraction"] == pytest.approx(0.5)
    assert kq_pbc.metrics["kq_pbc_twist_energy_coverage_fraction"] == pytest.approx(0.0)
    assert kq_pbc.metrics["kq_pbc_missing_twist_energy_fraction"] == pytest.approx(1.0)
    assert kq_pbc.metrics["kq_pbc_promotion_readiness_status"] == (
        "blocked_exploratory_audit_only"
    )
    assert kq_pbc.metrics["kq_pbc_readiness_level"] == (
        "not_ready_for_validated_non_gamma_claim"
    )
    assert kq_pbc.metrics["kq_pbc_requested_kpoint_count"] == 2
    assert kq_pbc.metrics["kq_pbc_execution_kpoint_count"] == 1
    assert kq_pbc.metrics["kq_pbc_executable_scope"] == "gamma_reference_hamiltonian_only"
    assert "non_gamma_quantum_mapping_not_executed" in kq_pbc.metrics["kq_pbc_promotion_blockers"]
    assert kq_pbc.metrics["kq_pbc_promotion_blocker_count"] == 4
    assert kq_pbc.metrics["kq_pbc_unsupported_claim_count"] == 4
    assert kq_pbc.metrics["kq_pbc_energy_replaces_primary"] is False
    assert kq_pbc.metrics["kq_pbc_runtime_submission_allowed"] is False
    assert kq_pbc.metrics["kq_pbc_finite_size_status"] == "not_evaluated"
    assert kq_pbc.metrics["kq_pbc_missing_twist_energy_count"] == 2
    assert kq_pbc.metrics["kq_pbc_proxy_energy_present"] is False


@pytest.mark.integration
def test_method_promotion_probe_uses_method_specific_qsci_accuracy(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/method_promotion_probe_v1.yaml"),
        output_dir=tmp_path / "method-promotion-probe",
        include_tags=["fast"],
    )

    assert result.summary.total_cases == 4
    assert result.summary.status_counts == {"exploratory": 2, "validated": 2}
    method_summary = result.calibration_summary["method_evidence_campaign"]
    assert method_summary["method_counts"] == {"qsci_plus_result": 2}
    assert method_summary["contract_matrix"]["status"] == "incomplete"
    assert method_summary["contract_matrix"]["methods"]["qsci_plus_result"][
        "contract_passed"
    ] is True

    h2_pair = method_summary["comparison_pairs"][
        "h2_stretched_qsci_plus_vs_h2_stretched_exact_baseline"
    ]
    h4_pair = method_summary["comparison_pairs"][
        "h4_stretched_qsci_plus_vs_h4_stretched_exact_baseline"
    ]
    assert h2_pair["method_specific_accuracy_metric"] == (
        "qsci_variational_upper_bound_margin_hartree_abs"
    )
    assert h2_pair["accuracy_outcome"] == "matches_exact_within_tolerance"
    assert h4_pair["method_specific_accuracy_metric"] == (
        "qsci_variational_upper_bound_margin_hartree_abs"
    )
    assert h4_pair["primary_case_accuracy_outcome"] == "tied_with_baseline"
    assert h4_pair["accuracy_outcome"] == "tied_with_baseline"
    assert h4_pair["method_absolute_error"] < 1.0e-8

    superiority = method_summary["method_superiority_audit"]["methods"]["qsci_plus_result"]
    assert superiority["contract_passed"] is True
    assert superiority["accuracy_outcome_counts"] == {
        "matches_exact_within_tolerance": 1,
        "tied_with_baseline": 1,
    }
    assert superiority["exact_match_pair_names"] == [
        "h2_stretched_qsci_plus_vs_h2_stretched_exact_baseline"
    ]
    assert superiority["no_accuracy_advantage_pair_names"] == [
        "h4_stretched_qsci_plus_vs_h4_stretched_exact_baseline"
    ]
    assert superiority["superiority_conclusion"] == "matches_exact_smoke_not_superior"

    probe_cases = {case.name: case for case in result.cases}
    h4_qsci = probe_cases["h4_stretched_qsci_plus"]
    assert h4_qsci.metrics["qsci_selected_subspace_size"] == 26
    assert h4_qsci.metrics["qsci_residual_expansion_enabled"] is True
    assert h4_qsci.metrics["qsci_residual_expansion_added_determinant_count"] == 10
    assert h4_qsci.metrics["qsci_external_coupling_residual_norm"] < 1.0e-8
