from pathlib import Path
from types import SimpleNamespace

from qcchem.core import (
    MeasurementSummary,
    MitigationSpec,
    MitigationSummary,
    PECSpec,
    ReadoutMitigationSpec,
    SymmetryCheckSpec,
    ZNESpec,
)
from qcchem.mitigation import build_mitigation_summary
from qcchem.workflow.method_evidence import build_and_write_method_evidence


class _ToyOperator:
    num_qubits = 2
    coeffs = [1.0, -0.25, 0.125]

    def __len__(self) -> int:
        return len(self.coeffs)


def test_method_evidence_builder_writes_active_sections(tmp_path: Path) -> None:
    solver_outcome = SimpleNamespace(
        metadata={
            "e_adapt_result": {
                "selected_operators": [{"pauli": "XY", "gradient": 0.1}],
                "rejected_operators": [],
                "gradient_history": [{"iteration": 0, "max_gradient": 0.1}],
                "depth_growth": [{"iteration": 0, "two_qubit_increment": 2}],
                "symmetry_audit": {"particle_number": "not_checked"},
                "low_rank_priority_scores": {"XY": 0.7},
                "ansatz_trust_gate": "exploratory",
            },
            "orbital_optimization": {
                "macro_iterations": [{"iteration": 0, "energy": -1.0}],
                "orbital_rotation_norm": 0.01,
                "rdm_source": "pyscf_rhf_proxy",
                "energy_lowering_hartree": 0.0,
                "active_space_changed": False,
                "reference_diagnostics": {
                    "status": "computed",
                    "backend": "pyscf.mcscf.CASSCF",
                    "energy_replaces_primary": False,
                },
                "active_space_resolve": {
                    "status": "not_applied_to_primary_solver",
                    "delegated_solver_hamiltonian_energy_hartree": -1.9,
                    "delegated_solver_total_energy_estimate_hartree": -1.1,
                    "casscf_reference_total_energy_hartree": -1.1001,
                    "casscf_minus_primary_total_energy_hartree": -0.0001,
                    "abs_casscf_primary_total_gap_hartree": 0.0001,
                    "energy_scope_audit": {
                        "energy_scope_consistent_for_total_gap": True,
                    },
                    "energy_replaces_primary": False,
                },
                "orbital_transfer_audit": {
                    "status": "reference_orbitals_not_transferred_to_primary_solver",
                    "optimized_orbitals_applied_to_primary_solver": False,
                    "primary_hamiltonian_rebuilt_from_optimized_orbitals": False,
                },
                "energy_scope_audit": {
                    "energy_scope_consistent_for_total_gap": True,
                    "energy_replaces_primary": False,
                },
                "promotion_readiness_audit": {
                    "status": "blocked_reference_diagnostic_only",
                    "readiness_level": "reference_diagnostic_not_solver_replacement",
                    "solver_replacement_allowed": False,
                    "energy_replacement_allowed": False,
                    "required_promotion_evidence_count": 5,
                    "promotion_blocker_count": 4,
                    "promotion_blockers": [
                        "optimized_orbitals_not_applied_to_primary_solver",
                        "primary_hamiltonian_not_rebuilt_from_optimized_orbitals",
                        "casscf_reference_energy_scope_differs_from_solver_energy",
                        "oo_qcasscf_solver_replacement_benchmark_gate_missing",
                    ],
                },
                "energy_replaces_primary": False,
                "trust_gate": "exploratory",
            },
        }
    )
    spec = SimpleNamespace(
        tasks=SimpleNamespace(
            perturbative_correction=SimpleNamespace(method="qsci_tcc"),
        ),
        problem=SimpleNamespace(
            pbc=SimpleNamespace(mode="kq_pbc", kpoints=["gamma", "x_half"], twist_average=True, active_space_per_k={}),
        ),
        fault_tolerant=SimpleNamespace(
            enabled=True,
            precision_hartree=1.0e-3,
            physical_error_rate=1.0e-3,
            cycle_time_ns=1000.0,
            encodings=["double_factorization", "tensor_hypercontraction"],
        ),
    )
    mitigation = MitigationSummary(
        symmetry_check={"requested": True, "performed": True},
        readout_mitigation={"requested": True, "performed": True},
        applied_methods=["symmetry_check", "readout_mitigation"],
    )
    measurement = MeasurementSummary(
        strategy="default",
        group_count=2,
        low_rank_aware=False,
        estimated_shot_cost=256.0,
        runtime_precision_target=0.1,
        execution_mode="estimator",
        planner="shadow_lr",
        shadow_bases=[{"basis": "ZZ", "shots": 128}],
    )
    qsci_payload = {
        "sampler": "local_energy_proxy",
        "raw_bitstrings": {"0011": 12},
        "repaired_determinants": [{"index": 3, "bitstring": "0011"}, {"index": 6, "bitstring": "0110"}],
        "selected_subspace_size": 2,
        "ci_energy": -1.13,
        "variance_estimate": 0.0,
        "excited_state_energies": [-0.5],
        "selection_bias_audit": {
            "ci_coefficients_digest": "abc",
            "leading_coefficients": [
                {"determinant": 3, "coefficient_real": 0.9, "coefficient_imag": 0.0},
                {"determinant": 6, "coefficient_real": 0.1, "coefficient_imag": 0.0},
            ],
        },
        "subspace_audit": {
            "variance_method": "embedded_ritz_vector_sparse_hamiltonian",
            "ground_state_residual_norm": 0.0,
            "variational_upper_bound_margin_hartree": 0.0,
        },
        "variational_upper_bound": True,
        "notes": ["unit-test"],
    }

    summary, e_adapt, orbital, qsci, post, kq_pbc, ft_qpe = build_and_write_method_evidence(
        sidecar_path=tmp_path / "method_evidence.json",
        spec=spec,
        solver_outcome=solver_outcome,
        physical_mapping=SimpleNamespace(qubit_hamiltonian=_ToyOperator()),
        solver_energy=-1.1,
        mitigation=mitigation,
        measurement=measurement,
        qsci_payload=qsci_payload,
    )

    assert summary is not None
    assert summary.available is True
    assert (tmp_path / "method_evidence.json").exists()
    assert summary.promotion_gate_audit["overall_claim_status"] == "promotion_required"
    assert summary.promotion_gate_audit["sidecar_energy_replacement_allowed_methods"] == []
    assert summary.promotion_gate_audit["accuracy_claim_allowed_methods"] == []
    assert "shadow_lr" in summary.promotion_gate_audit["planning_metric_methods"]
    assert "ft_qpe_resource_estimate" in summary.promotion_gate_audit["resource_model_only_methods"]
    assert "post_correlation" in summary.promotion_gate_audit["unsupported_for_claim_methods"]
    sidecar = (tmp_path / "method_evidence.json").read_text(encoding="utf-8")
    assert "promotion_gate_audit" in sidecar
    assert e_adapt is not None and e_adapt.selected_operators
    assert orbital is not None and orbital.rdm_source == "pyscf_rhf_proxy"
    assert orbital.reference_diagnostics["status"] == "computed"
    assert orbital.active_space_resolve["status"] == "not_applied_to_primary_solver"
    assert orbital.energy_scope_audit["energy_scope_consistent_for_total_gap"] is True
    assert orbital.active_space_resolve["casscf_minus_primary_total_energy_hartree"] == -0.0001
    assert orbital.energy_replaces_primary is False
    assert orbital.orbital_transfer_audit["optimized_orbitals_applied_to_primary_solver"] is False
    assert orbital.promotion_readiness_audit["status"] == "blocked_reference_diagnostic_only"
    assert orbital.promotion_readiness_audit["solver_replacement_allowed"] is False
    orbital_record = summary.promotion_gate_audit["method_records"]["orbital_optimization"]
    assert orbital_record["promotion_readiness_status"] == "blocked_reference_diagnostic_only"
    assert orbital_record["solver_replacement_allowed"] is False
    assert qsci is not None and qsci.ci_energy == -1.13
    assert qsci.subspace_audit["variance_method"] == "embedded_ritz_vector_sparse_hamiltonian"
    assert post is not None and post.trust_gate == "unsupported_for_claim"
    assert post.external_correlation_energy is None
    assert post.total_corrected_energy is None
    assert post.double_counting_audit["status"] == "not_evaluated"
    assert post.correction_eligibility_audit["status"] == "tcc_amplitude_mapping_audit_only"
    assert post.correction_eligibility_audit["backend_executable"] is False
    assert post.amplitude_mapping_audit["status"] == "constructed_for_audit_only"
    assert post.amplitude_mapping_audit["mapped_single_count"] == 1
    assert post.amplitude_mapping_audit["mapped_double_count"] == 0
    assert post.tailored_amplitudes["status"] == "constructed_for_audit_only"
    post_record = summary.promotion_gate_audit["method_records"]["post_correlation"]
    assert post_record["correction_eligibility_status"] == "tcc_amplitude_mapping_audit_only"
    assert post_record["amplitude_mapping_status"] == "constructed_for_audit_only"
    assert post_record["backend_executable"] is False
    assert kq_pbc is not None and kq_pbc.pbc_trust_tier == "exploratory"
    assert kq_pbc.finite_size_correction["status"] == "not_evaluated"
    assert kq_pbc.non_gamma_mapping_audit["status"] == "audit_only"
    assert kq_pbc.non_gamma_mapping_audit["execution_kpoint_mesh"] == [1, 1, 1]
    assert kq_pbc.twist_energies
    assert all(item["energy_status"] == "not_evaluated" for item in kq_pbc.twist_energies)
    assert all("solver_energy_proxy_hartree" not in item for item in kq_pbc.twist_energies)
    assert ft_qpe is not None and ft_qpe.recommended_encoding == "tensor_hypercontraction"
    assert ft_qpe.resource_formula_audit["scope"] == "coarse_pauli_l1_phase_estimation_scaling"
    assert ft_qpe.resource_formula_audit["input_terms"]["pauli_term_count"] == 3
    assert ft_qpe.resource_formula_audit["reference_encoding"] == "double_factorization"
    assert ft_qpe.resource_formula_audit["best_encoding"] == "tensor_hypercontraction"
    assert ft_qpe.resource_model_audit["resource_claim_status"] == "resource_model_only"
    assert ft_qpe.resource_model_audit["compiled_fault_tolerant_circuit_available"] is False
    assert abs(ft_qpe.resource_model_audit["best_to_reference_toffoli_ratio"] - 0.65) < 1.0e-12
    assert ft_qpe.promotion_readiness_audit["status"] == (
        "blocked_missing_compiled_fault_tolerant_evidence"
    )
    assert ft_qpe.promotion_readiness_audit["readiness_level"] == (
        "resource_model_only_not_compiled"
    )
    assert ft_qpe.promotion_readiness_audit["validated_resource_advantage_claim_allowed"] is False
    assert ft_qpe.promotion_readiness_audit["required_promotion_evidence_count"] == 5
    ft_record = summary.promotion_gate_audit["method_records"]["ft_qpe_resource_estimate"]
    assert ft_record["promotion_readiness_status"] == (
        "blocked_missing_compiled_fault_tolerant_evidence"
    )
    assert ft_record["readiness_level"] == "resource_model_only_not_compiled"
    assert ft_record["resource_formula_scope"] == "coarse_pauli_l1_phase_estimation_scaling"
    assert ft_record["validated_resource_advantage_claim_allowed"] is False
    assert set(summary.methods) >= {
        "e_adapt_result",
        "orbital_optimization",
        "qsci_plus_result",
        "post_correlation",
        "kq_pbc_result",
        "ft_qpe_resource_estimate",
        "trust_qem",
        "shadow_lr",
    }


def test_trust_qem_claim_gate_rejects_non_executable_pec_model(tmp_path: Path) -> None:
    non_executable_model = tmp_path / "pec_model.xyzq"
    non_executable_model.write_text("# not a PEC calibration model\n", encoding="utf-8")
    summary = build_mitigation_summary(
        MitigationSpec(
            symmetry_check=SymmetryCheckSpec(
                enabled=True,
                strategy="postselect",
                particle_number=True,
            ),
            readout=ReadoutMitigationSpec(
                enabled=True,
                method="local_assignment",
                calibration_shots=32,
            ),
            zne=ZNESpec(
                enabled=True,
                method="richardson",
                scale_factors=[1.0, 1.5, 2.0],
            ),
            pec=PECSpec(
                enabled=True,
                method="local_pec",
                calibration_model=str(non_executable_model),
                max_overhead=12.0,
            ),
            experimental=True,
        )
    )

    assert summary.requested_methods == [
        "symmetry_check",
        "readout_mitigation",
        "zne",
        "pec",
    ]
    assert summary.applied_methods == ["symmetry_check", "readout_mitigation", "zne"]
    assert summary.claim_allowed_methods == []
    assert summary.claim_status == "unsupported_for_claim"
    assert summary.energy_replaces_primary is False
    assert summary.pec["executable_calibration_model"] is False
    assert summary.pec["status"] == "unsupported_calibration_model_format"
    assert summary.pec["allowed_for_claim"] is False


def test_trust_qem_claim_gate_accepts_executable_pec_calibration_scope(tmp_path: Path) -> None:
    executable_model = tmp_path / "pec_model.json"
    executable_model.write_text(
        (
            '{"schema":"qcchem.pec_calibration_model.v1",'
            '"executable":true,'
            '"quasi_probabilities":{"x":[1.0]}}'
        ),
        encoding="utf-8",
    )
    summary = build_mitigation_summary(
        MitigationSpec(
            pec=PECSpec(
                enabled=True,
                method="local_pec",
                calibration_model=str(executable_model),
                max_overhead=3.0,
            ),
            experimental=True,
        )
    )

    assert summary.requested_methods == ["pec"]
    assert summary.applied_methods == ["pec"]
    assert summary.claim_allowed_methods == ["pec"]
    assert summary.claim_disallowed_methods == []
    assert summary.claim_status == "claim_limited"
    assert summary.energy_replaces_primary is False
    assert summary.pec["executable_calibration_model"] is True
    assert summary.pec["claim_scope"] == "calibration_overhead_only"
