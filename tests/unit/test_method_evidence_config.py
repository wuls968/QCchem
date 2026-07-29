from pathlib import Path

from qcchem.io.config import load_run_spec
from qcchem.workflow.release_audit import classify_exploratory_config


def test_method_evidence_smoke_config_round_trip() -> None:
    spec = load_run_spec(Path("configs/exploratory/h2_method_evidence_smoke.yaml"))

    assert spec.problem.measurement.planner == "shadow_lr"
    assert spec.problem.measurement.total_shots == 256
    assert spec.mitigation.readout.method == "local_assignment"
    assert spec.mitigation.readout.calibration_shots == 64
    assert spec.mitigation.symmetry_check.particle_number is True
    assert spec.qsci.enabled is True
    assert spec.qsci.determinant_repair.hamming_expansion == 1
    assert spec.tasks.excited_state.method == "q_sc_eom"
    assert spec.tasks.perturbative_correction.method == "qsci_tcc"
    assert spec.fault_tolerant.enabled is True
    assert "tensor_hypercontraction" in spec.fault_tolerant.encodings
    assert classify_exploratory_config(Path("configs/exploratory/h2_method_evidence_smoke.yaml")) == "method_evidence"


def test_trust_qem_config_keeps_pec_calibration_explicitly_unavailable() -> None:
    spec = load_run_spec(Path("configs/exploratory/h2_trust_qem.yaml"))

    assert spec.mitigation.symmetry_check.enabled is True
    assert spec.mitigation.readout.method == "local_assignment"
    assert spec.mitigation.zne.method == "richardson"
    assert spec.mitigation.pec.enabled is True
    assert spec.mitigation.pec.calibration_model is None
    assert classify_exploratory_config(Path("configs/exploratory/h2_trust_qem.yaml")) == "method_evidence"


def test_trust_qem_calibrated_pec_config_parses() -> None:
    spec = load_run_spec(Path("configs/exploratory/h2_trust_qem_calibrated_pec.yaml"))

    assert spec.mitigation.pec.enabled is True
    assert spec.mitigation.pec.method == "local_pec"
    assert spec.mitigation.pec.calibration_model == "configs/data/h2_pec_calibration_model.json"
    assert spec.mitigation.pec.max_overhead == 25.0
    assert classify_exploratory_config(
        Path("configs/exploratory/h2_trust_qem_calibrated_pec.yaml")
    ) == "method_evidence"


def test_e_adapt_shadow_lr_and_q_embed_configs_parse() -> None:
    e_adapt = load_run_spec(Path("configs/exploratory/lih_shadow_lr_e_adapt.yaml"))
    q_embed = load_run_spec(Path("configs/exploratory/h2_q_embed.yaml"))
    oo_qcasscf = load_run_spec(Path("configs/exploratory/h2_oo_qcasscf.yaml"))

    assert e_adapt.solver.kind == "e_adapt_vqe"
    assert e_adapt.solver.experimental is True
    assert e_adapt.solver.e_adapt.max_operators == 4
    assert e_adapt.problem.measurement.planner == "shadow_lr"
    assert classify_exploratory_config(Path("configs/exploratory/lih_shadow_lr_e_adapt.yaml")) == "method_evidence"

    assert q_embed.problem.embedding.method == "q_dmet"
    assert [fragment.solver for fragment in q_embed.problem.embedding.fragments] == ["exact", "exact"]
    assert classify_exploratory_config(Path("configs/exploratory/h2_q_embed.yaml")) == "method_evidence"

    assert oo_qcasscf.solver.kind == "oo_qcasscf"
    assert oo_qcasscf.solver.experimental is True
    assert oo_qcasscf.solver.orbital_optimization.max_macro_iterations == 3
    assert classify_exploratory_config(Path("configs/exploratory/h2_oo_qcasscf.yaml")) == "method_evidence"


def test_kq_pbc_and_ft_qpe_configs_parse() -> None:
    pbc = load_run_spec(Path("configs/exploratory/pbc_h2_kq_pbc.yaml"))
    ft = load_run_spec(Path("configs/exploratory/h2_ft_qpe_planner.yaml"))

    assert pbc.problem.pbc.mode == "kq_pbc"
    assert pbc.problem.pbc.kpoint_mesh == (2, 1, 1)
    assert pbc.problem.pbc.twist_average is True
    assert pbc.problem.pbc.kpoints == ["gamma", "x_half"]
    assert classify_exploratory_config(Path("configs/exploratory/pbc_h2_kq_pbc.yaml")) == "method_evidence"

    assert ft.fault_tolerant.method == "ft_qpe_planner"
    assert ft.fault_tolerant.precision_hartree == 1.0e-3
    assert "symmetry_compressed_double_factorization" in ft.fault_tolerant.encodings
    assert classify_exploratory_config(Path("configs/exploratory/h2_ft_qpe_planner.yaml")) == "method_evidence"


def test_method_promotion_probe_qsci_residual_expansion_config_parses() -> None:
    spec = load_run_spec(Path("configs/exploratory/h4_stretched_qsci_plus.yaml"))

    assert spec.qsci.enabled is True
    assert spec.qsci.max_determinants == 16
    assert spec.qsci.classical_diagonalizer.max_subspace_size == 36
    assert spec.qsci.residual_expansion.enabled is True
    assert spec.qsci.residual_expansion.scorer == "external_residual_coupling"
    assert spec.qsci.residual_expansion.max_iterations == 3
    assert spec.qsci.residual_expansion.batch_size == 10
    assert spec.qsci.residual_expansion.max_additional_determinants == 20
    assert spec.qsci.residual_expansion.target_residual_norm == 1.0e-8
