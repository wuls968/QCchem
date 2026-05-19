from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_h2_workflow_generates_benchmarkable_artifacts(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2.yaml"), output_dir=tmp_path / "h2-run")

    assert result.energy.energy_units == "Hartree"
    assert result.schema_version == "qcchem.result.v0.8-alpha"
    assert result.execution_policy.name == "benchmark"
    assert result.backend_capability.statevector is True
    assert "constant_energy_correction" in result.energy.energy_formula
    assert result.reduction_audit is not None
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy,
        abs=1e-10,
    )
    assert result.energy.hf_reference_energy == pytest.approx(-1.1169989967540044, abs=1e-10)
    assert result.energy.exact_ground_energy == pytest.approx(-1.8572750302023824, abs=1e-8)
    assert result.benchmark.absolute_error < 1e-6
    assert result.benchmark.meets_threshold is True
    assert result.problem.transformers_applied == []
    assert result.problem.active_space_metadata is None
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    assert result.artifacts.resolved_config.exists()
    assert result.artifacts.log_file.exists()
    assert result.artifacts.exact_result_json.exists()
    assert result.artifacts.quantum_evidence_json is not None
    assert result.artifacts.quantum_evidence_json.exists()
    assert result.quantum_evidence is not None
    assert result.quantum_evidence.available is True
    assert result.quantum_evidence.hamiltonian["pauli_term_count"] == result.mapping.qubit_term_count
    assert result.quantum_evidence.sampling["available"] is True

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["quantum_evidence"]["sidecar_sha256"]
    quantum_evidence = json.loads(result.artifacts.quantum_evidence_json.read_text(encoding="utf-8"))
    assert quantum_evidence["schema"] == "qcchem.quantum_evidence.v1"
    assert quantum_evidence["hamiltonian"]["pauli_terms"]
    assert quantum_evidence["sampling"]["group_counts"]
    assert quantum_evidence["optimization"]["trajectory"]
    regenerated_report = render_markdown_report(payload)
    assert "Field Definitions" in regenerated_report
    assert "exact_ground_energy" in regenerated_report
    assert "Exact Baseline" in regenerated_report
    assert "Quantum Evidence" in regenerated_report


@pytest.mark.integration
def test_h2_structure_file_provenance_reaches_artifacts_and_exports(tmp_path: Path) -> None:
    structure_dir = tmp_path / "structures"
    structure_dir.mkdir()
    structure_path = structure_dir / "h2.xyz"
    structure_path.write_text(
        "2\nh2 structure file\nH 0.0 0.0 0.0\nH 0.0 0.0 0.735\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "h2_from_xyz.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-from-xyz
  structure_file: structures/h2.xyz
  charge: 0
  multiplicity: 1
  basis: sto3g
solver:
  kind: exact
benchmark:
  enabled: true
  exact_baseline_qubit_limit: 12
run:
  seed: 7
  overwrite: true
  exports:
    qcschema_json: true
        """.strip(),
        encoding="utf-8",
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-from-xyz-run")

    input_source = result.provenance.input_sources[0]
    assert input_source["kind"] == "structure_file"
    assert input_source["format"] == "xyz"
    assert input_source["file_sha256"]
    assert input_source["normalized_geometry_sha256"]

    result_payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    result_source = result_payload["provenance"]["input_sources"][0]
    assert result_source["file_sha256"] == input_source["file_sha256"]
    assert result_source["normalized_geometry_sha256"] == input_source["normalized_geometry_sha256"]

    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Input Provenance" in report_text
    assert input_source["file_sha256"] in report_text

    assert result.artifacts.qcschema_json is not None
    qcschema = json.loads(result.artifacts.qcschema_json.read_text(encoding="utf-8"))
    qcschema_source = qcschema["extras"]["input_provenance"][0]
    assert qcschema_source["file_sha256"] == input_source["file_sha256"]
    assert qcschema_source["normalized_geometry_sha256"] == input_source["normalized_geometry_sha256"]
    assert qcschema["extras"]["quantum_evidence"]["available"] is True
