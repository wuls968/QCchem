from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.chem import build_electronic_structure_context
from qcchem.core import MappingSymmetryReductionSpec
from qcchem.io.config import load_run_spec
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.reporting.markdown import write_markdown_report
from qcchem.solvers.spectrum import compute_exact_spectrum
from qcchem.workflow.runner import run_from_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def _mapped_with_z2(config_name: str, mapping_kind: str = "jordan_wigner"):
    spec = load_run_spec(REPO_ROOT / "configs" / config_name)
    chemistry = build_electronic_structure_context(spec)
    mapping = map_fermionic_hamiltonian(
        chemistry.fermionic_hamiltonian,
        mapping_kind,
        num_particles=chemistry.summary.num_particles,
        problem=chemistry.problem,
        symmetry_reduction=spec.mapping.symmetry_reduction,
    )
    return chemistry, mapping


@pytest.mark.integration
def test_h2_jordan_wigner_z2_tapering_preserves_exact_energy() -> None:
    _, mapping = _mapped_with_z2("h2_exact.yaml")

    raw_energy = compute_exact_spectrum(mapping.raw_qubit_hamiltonian, num_states=1).eigenvalues[0]
    tapered_energy = compute_exact_spectrum(mapping.qubit_hamiltonian, num_states=1).eigenvalues[0]

    assert mapping.summary.raw_num_qubits == 4
    assert mapping.summary.raw_qubit_term_count == 15
    assert mapping.summary.num_qubits == 1
    assert mapping.summary.qubit_term_count == 3
    assert mapping.summary.symmetry_tapered_qubits == 3
    assert mapping.summary.z2_symmetry_count == 3
    assert mapping.summary.z2_tapering_values == [-1, 1, -1]
    assert mapping.summary.symmetry_reduction_status == "applied_z2"
    assert tapered_energy == pytest.approx(raw_energy, abs=1.0e-8)


@pytest.mark.integration
def test_lih_active_jordan_wigner_z2_tapering_preserves_exact_energy() -> None:
    _, mapping = _mapped_with_z2("lih_active_exact_uncompressed.yaml")

    raw_energy = compute_exact_spectrum(mapping.raw_qubit_hamiltonian, num_states=1).eigenvalues[0]
    tapered_energy = compute_exact_spectrum(mapping.qubit_hamiltonian, num_states=1).eigenvalues[0]

    assert mapping.summary.raw_num_qubits == 4
    assert mapping.summary.raw_qubit_term_count == 27
    assert mapping.summary.num_qubits == 2
    assert mapping.summary.qubit_term_count == 9
    assert mapping.summary.symmetry_tapered_qubits == 2
    assert mapping.summary.z2_symmetry_count == 2
    assert mapping.summary.z2_tapering_values == [-1, -1]
    assert tapered_energy == pytest.approx(raw_energy, abs=1.0e-8)


@pytest.mark.integration
def test_h2_parity_two_qubit_reduction_can_be_z2_tapered() -> None:
    _, mapping = _mapped_with_z2("h2_exact.yaml", mapping_kind="parity_two_qubit_reduction")

    raw_energy = compute_exact_spectrum(mapping.raw_qubit_hamiltonian, num_states=1).eigenvalues[0]
    tapered_energy = compute_exact_spectrum(mapping.qubit_hamiltonian, num_states=1).eigenvalues[0]

    assert mapping.summary.raw_num_qubits == 2
    assert mapping.summary.raw_qubit_term_count == 5
    assert mapping.summary.num_qubits == 1
    assert mapping.summary.qubit_term_count == 3
    assert mapping.summary.symmetry_tapered_qubits == 1
    assert mapping.summary.z2_symmetry_count == 1
    assert mapping.summary.z2_tapering_values == [-1]
    assert tapered_energy == pytest.approx(raw_energy, abs=1.0e-8)


@pytest.mark.integration
def test_strict_z2_tapering_requires_problem_context() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2_exact.yaml")
    chemistry = build_electronic_structure_context(spec)

    with pytest.raises(ValueError, match="requires an ElectronicStructureProblem"):
        map_fermionic_hamiltonian(
            chemistry.fermionic_hamiltonian,
            "jordan_wigner",
            num_particles=chemistry.summary.num_particles,
            symmetry_reduction=MappingSymmetryReductionSpec(z2="enabled", strict=True),
        )


@pytest.mark.integration
def test_h2_point_group_audit_records_orbital_irreps() -> None:
    chemistry, _ = _mapped_with_z2("h2_exact.yaml")
    metadata = chemistry.summary.point_group_metadata

    assert metadata["status"] == "available"
    assert metadata["group"] == "Dooh"
    assert metadata["orbital_irreps"] == ["A1g", "A1u"]
    assert chemistry.reduction_audit.point_group_metadata["orbital_irreps"] == ["A1g", "A1u"]


@pytest.mark.integration
def test_c2v_point_group_audit_records_stable_water_irreps() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2o_active_space.yaml")
    chemistry = build_electronic_structure_context(spec)
    metadata = chemistry.summary.point_group_metadata

    assert metadata["status"] == "available"
    assert metadata["group"] == "C2v"
    assert metadata["orbital_irreps"] == ["A1", "A1", "B2", "A1", "B1", "A1", "B2"]


@pytest.mark.integration
def test_point_group_irrep_filter_reduces_active_orbitals_and_qubits() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2_exact.yaml")
    spec.problem.point_group.reduction_mode = "irrep_filter"
    spec.problem.point_group.active_irreps = ["A1g"]
    chemistry = build_electronic_structure_context(spec)
    mapping = map_fermionic_hamiltonian(
        chemistry.fermionic_hamiltonian,
        spec.mapping.kind,
        num_particles=chemistry.summary.num_particles,
        problem=chemistry.problem,
        symmetry_reduction=spec.mapping.symmetry_reduction,
    )

    assert chemistry.summary.num_spatial_orbitals == 1
    assert chemistry.summary.active_space_metadata["point_group_filter"]["selected_active_irreps"] == ["A1g"]
    assert chemistry.reduction_audit.selection_mode == "point_group_irrep_filter"
    assert mapping.summary.raw_num_qubits == 2


@pytest.mark.integration
def test_symmetry_tapered_run_writes_artifacts_and_report(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_symmetry_tapered.yaml",
        output_dir=tmp_path / "h2-symmetry-tapered",
    )
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))

    assert payload["mapping"]["raw_num_qubits"] == 4
    assert payload["mapping"]["num_qubits"] == 1
    assert payload["mapping"]["symmetry_tapered_qubits"] == 3
    assert payload["mapping"]["symmetry_reduction_status"] == "applied_z2"
    assert payload["problem"]["point_group_metadata"]["orbital_irreps"] == ["A1g", "A1u"]

    regenerated_path = tmp_path / "symmetry-report.md"
    write_markdown_report(payload, regenerated_path)
    report_text = regenerated_path.read_text(encoding="utf-8")
    assert "Symmetry tapered qubits" in report_text
    assert "Z2 tapering values" in report_text
    assert "Point-group metadata" in report_text


@pytest.mark.integration
def test_environment_embedding_auto_z2_skips_tapering_and_keeps_qubits_stable(
    tmp_path: Path,
) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_environment_embedding_z2_auto.yaml",
        output_dir=tmp_path / "h2-env-z2-auto",
    )
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    mapping = payload["mapping"]

    assert result.environment_embedding is not None
    assert mapping["raw_num_qubits"] == 4
    assert mapping["num_qubits"] == 4
    assert mapping["symmetry_tapered_qubits"] == 0
    assert mapping["symmetry_reduction_status"] == "disabled"
    assert any(
        "environment embedding in auto mode" in note
        for note in mapping["symmetry_reduction_notes"]
    )


@pytest.mark.integration
def test_environment_embedding_explicit_z2_applies_and_reports_mapping_fields(
    tmp_path: Path,
) -> None:
    _, mapping = _mapped_with_z2("h2_environment_embedding_z2_enabled.yaml")
    raw_energy = compute_exact_spectrum(mapping.raw_qubit_hamiltonian, num_states=1).eigenvalues[0]
    tapered_energy = compute_exact_spectrum(mapping.qubit_hamiltonian, num_states=1).eigenvalues[0]
    validation = mapping.summary.symmetry_reduction_validation

    assert mapping.summary.symmetry_reduction_status == "applied_z2"
    assert mapping.summary.raw_num_qubits == 4
    assert mapping.summary.num_qubits < mapping.summary.raw_num_qubits
    assert mapping.summary.symmetry_tapered_qubits == (
        mapping.summary.raw_num_qubits - mapping.summary.num_qubits
    )
    assert abs(float(raw_energy) - float(tapered_energy)) < 1.0e-8
    assert validation["available"] is True
    assert validation["absolute_delta"] < 1.0e-8

    result = run_from_config(
        REPO_ROOT / "configs" / "h2_environment_embedding_z2_enabled.yaml",
        output_dir=tmp_path / "h2-env-z2-enabled",
    )
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    artifact_mapping = payload["mapping"]

    assert artifact_mapping["raw_num_qubits"] == 4
    assert artifact_mapping["num_qubits"] < artifact_mapping["raw_num_qubits"]
    assert artifact_mapping["raw_qubit_term_count"] > artifact_mapping["qubit_term_count"]
    assert artifact_mapping["symmetry_tapered_qubits"] == (
        artifact_mapping["raw_num_qubits"] - artifact_mapping["num_qubits"]
    )
    assert artifact_mapping["symmetry_reduction_status"] == "applied_z2"
    assert artifact_mapping["symmetry_reduction_validation"]["absolute_delta"] < 1.0e-8

    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert f"Raw qubit count: `{artifact_mapping['raw_num_qubits']}`" in report_text
    assert f"Raw qubit Hamiltonian terms: `{artifact_mapping['raw_qubit_term_count']}`" in report_text
    assert f"Qubit count: `{artifact_mapping['num_qubits']}`" in report_text
    assert f"Symmetry tapered qubits: `{artifact_mapping['symmetry_tapered_qubits']}`" in report_text
    assert "Symmetry reduction status: `applied_z2`" in report_text
