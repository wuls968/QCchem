from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_auto_active_space_and_freeze_core_are_audited(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/lih_active_space_auto.yaml"), output_dir=tmp_path / "lih-auto")

    assert result.reduction_audit is not None
    assert "FreezeCoreTransformer" in result.reduction_audit.transformers_applied
    assert result.reduction_audit.selection_mode == "auto"
    assert "frontier" in result.reduction_audit.selection_reason.lower()
    assert result.reduction_audit.original_num_spatial_orbitals > result.reduction_audit.reduced_num_spatial_orbitals
    assert result.artifacts.result_json.exists()
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Reduction Audit" in report
    assert "selection_reason" in report


@pytest.mark.integration
@pytest.mark.parametrize(
    ("config_name", "expected_method"),
    [
        ("configs/lih_compression_cholesky.yaml", "modified_cholesky"),
        ("configs/lih_compression_double_factorization.yaml", "double_factorization"),
    ],
)
def test_compression_audit_is_persisted(tmp_path: Path, config_name: str, expected_method: str) -> None:
    result = run_from_config(Path(config_name), output_dir=tmp_path / expected_method)

    assert result.compression_result is not None
    assert result.compression_result.method == expected_method
    assert result.compression_result.threshold > 0.0
    assert result.compression_result.original_qubit_term_count >= result.compression_result.compressed_term_count_estimate
    assert result.compression_result.verification_status in {"validated", "exploratory"}
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert "compression_result" in payload


@pytest.mark.integration
def test_nevpt2_correction_is_reported(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/lih_nevpt2.yaml"), output_dir=tmp_path / "lih-nevpt2")

    assert result.perturbative_correction_result is not None
    assert result.perturbative_correction_result.method == "nevpt2"
    assert result.perturbative_correction_result.plugin == "pyscf"
    assert result.perturbative_correction_result.corrected_total_energy == pytest.approx(
        result.perturbative_correction_result.active_space_energy
        + result.perturbative_correction_result.perturbative_correction,
        abs=1e-8,
    )
    regenerated = render_markdown_report(json.loads(result.artifacts.result_json.read_text(encoding="utf-8")))
    assert "Perturbative Correction" in regenerated


@pytest.mark.integration
def test_embedding_skeleton_persists_fragment_metadata(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/lih_embedding.yaml"), output_dir=tmp_path / "lih-embedding")

    assert result.embedding_result is not None
    assert result.embedding_result.method == "dmet_skeleton"
    assert result.embedding_result.verification_status == "exploratory"
    assert len(result.embedding_result.fragments) == 2
    assert all(fragment["atom_indices"] for fragment in result.embedding_result.fragments)
    regenerated = render_markdown_report(json.loads(result.artifacts.result_json.read_text(encoding="utf-8")))
    assert "Embedding Audit" in regenerated


@pytest.mark.integration
def test_trust_loop_chemistry_tasks_persist_reference_artifacts(tmp_path: Path) -> None:
    config_path = tmp_path / "h2_trust_loop_tasks.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-trust-loop-tasks
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
problem:
  embedding:
    enabled: true
    fragments:
      - name: full_h2_fragment
        atom_indices: [0, 1]
    execution:
      enabled: true
      plugin: pyscf_rhf_fragment
mapping:
  kind: jordan_wigner
backend:
  kind: statevector
solver:
  kind: exact
benchmark:
  enabled: true
tasks:
  geometry_optimization:
    enabled: true
    max_steps: 12
  gradient:
    enabled: true
  response_properties:
    enabled: true
    properties: [static_polarizability]
    finite_field_step: 0.002
run:
  output_dir: artifacts/h2_trust_loop_tasks
  overwrite: true
        """.strip(),
        encoding="utf-8",
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-trust-loop")

    assert result.geometry_optimization_result is not None
    assert result.geometry_optimization_result["verification_status"] == "validated"
    assert result.gradient_result is not None
    assert result.gradient_result["verification_status"] == "validated"
    assert result.response_property_result is not None
    assert result.response_property_result["verification_status"] == "validated"
    assert result.embedding_result is not None
    assert result.embedding_result.verification_status == "validated"
    assert result.hardware_error_diagnostic is not None
    assert result.hardware_error_diagnostic["diagnostic_label"] == "missing_runtime_result"
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert "geometry_optimization_result" in payload
    assert "gradient_result" in payload
    assert "response_property_result" in payload
    assert "hardware_error_diagnostic" in payload
    assert "artifact_index_entry" in payload


@pytest.mark.integration
def test_external_point_charges_are_persisted_and_energy_formula_closes(tmp_path: Path) -> None:
    config_path = tmp_path / "h2_external_point_charges.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-external-point-charges
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
  unit: angstrom
problem:
  external_point_charges:
    enabled: true
    unit: angstrom
    charges:
      - label: mm_probe
        coords: [0.0, 0.0, 2.0]
        charge: -0.5
mapping:
  kind: jordan_wigner
backend:
  kind: statevector
solver:
  kind: exact
benchmark:
  enabled: true
  exact_baseline_qubit_limit: 12
  absolute_error_threshold: 1.0e-10
  relative_error_threshold: 1.0e-10
run:
  output_dir: artifacts/h2_external_point_charges
  overwrite: true
  exports:
    qcschema_json: true
        """.strip(),
        encoding="utf-8",
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-external")

    assert result.external_point_charges is not None
    assert result.external_point_charges.charge_count == 1
    assert result.external_point_charges.includes_mm_self_energy is False
    assert result.energy.external_point_charge_nuclear_interaction_energy != 0.0
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy
        + result.energy.external_point_charge_nuclear_interaction_energy
        + result.energy.boundary_embedding_constant_energy
    )

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["external_point_charges"]["adapter_strategy"] == "pyscf.qmmm.mm_charge"
    assert payload["energy"]["external_point_charge_nuclear_interaction_energy"] == pytest.approx(
        result.energy.external_point_charge_nuclear_interaction_energy
    )
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "External Point Charges" in report
    assert "MM-MM" in report
    qcschema = json.loads(result.artifacts.qcschema_json.read_text(encoding="utf-8"))
    assert qcschema["extras"]["external_point_charges"]["charge_count"] == 1
    assert qcschema["extras"]["environment_embedding"]["provenance"]["compatibility_notes"]


@pytest.mark.integration
def test_environment_embedding_damped_charges_cache_and_report(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "environment.xyzq").write_text(
        "mm_probe 0.0 0.0 2.0 -0.5\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "h2_environment_embedding.yaml"
    cache_dir = tmp_path / "effective_cache"
    config_path.write_text(
        f"""
molecule:
  name: H2-environment-embedding
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
    boundary:
      enabled: true
      cut_bonds:
        - label: H0-MM
          qm_atom: 0
          mm_atom: 10
      leakage_threshold: 1.0
      strict: false
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
  exports:
    qcschema_json: true
        """.strip(),
        encoding="utf-8",
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-env")

    assert result.environment_embedding is not None
    assert result.environment_embedding.cache_enabled is True
    assert result.environment_embedding.cache_hit is False
    assert result.environment_embedding.cache_fingerprint
    assert result.environment_embedding.one_body_environment["frobenius_norm"] > 0.0
    assert result.environment_embedding.active_space_projection["environment_qubit_growth"] == 0
    assert result.environment_embedding.boundary is not None
    assert result.environment_embedding.boundary.max_boundary_leakage is not None
    assert result.external_point_charges is not None
    assert result.external_point_charges.provenance["damping_model"]["kind"] == "gaussian"
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy
        + result.energy.external_point_charge_nuclear_interaction_energy
        + result.energy.boundary_embedding_constant_energy
    )
    assert len(list(cache_dir.glob("*.json"))) == 1
    assert len(list(cache_dir.glob("*.npz"))) == 1

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["environment_embedding"]["one_body_environment"]["available"] is True
    assert payload["energy"]["boundary_embedding_constant_energy"] == 0.0
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Environment Effective Hamiltonian" in report
    assert "boundary_max_leakage" in report
    qcschema = json.loads(result.artifacts.qcschema_json.read_text(encoding="utf-8"))
    assert qcschema["extras"]["environment_embedding"]["cache_fingerprint"]
