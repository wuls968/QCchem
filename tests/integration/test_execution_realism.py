from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_h2_shot_backend_records_sampling_statistics(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2_shot.yaml"), output_dir=tmp_path / "h2-shot")

    assert result.sampled_result is not None
    assert result.sampled_result.shots == 4096
    assert result.sampled_result.num_repeats == 5
    assert len(result.sampled_result.repeat_solver_energies) == 5
    assert result.sampled_result.standard_error is not None
    assert result.sampled_result.confidence_interval_low is not None
    assert result.sampled_result.confidence_interval_high is not None
    assert result.benchmark.comparison_target == "sampled_result"
    assert result.mitigation.symmetry_check["requested"] is True
    assert result.artifacts.exact_result_json.exists()
    assert result.quantum_evidence is not None
    assert result.quantum_evidence.sampling["available"] is True
    assert result.quantum_evidence.sampling["source"] == "backend_measurement_circuits"
    assert result.quantum_evidence.sampling["shots_per_group"] == 4096
    sidecar = json.loads(result.artifacts.quantum_evidence_json.read_text(encoding="utf-8"))
    assert sidecar["sampling"]["group_counts"]
    assert sidecar["optimization"]["trajectory"]


@pytest.mark.integration
def test_lih_active_space_variational_benchmark_is_reproducible(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/lih_active_vqe.yaml"), output_dir=tmp_path / "lih-active")

    assert result.problem.active_space_metadata is not None
    assert "ActiveSpaceTransformer" in result.problem.transformers_applied
    assert result.variational_result is not None
    assert result.variational_result.parameter_count == 3
    assert result.sampled_result is not None
    assert result.benchmark.absolute_error is not None
    assert result.benchmark.absolute_error < 2.5e-2
    assert result.benchmark.meets_threshold is True


@pytest.mark.integration
def test_active_space_energy_formula_tracks_constant_correction(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2o_active_space.yaml"), output_dir=tmp_path / "h2o-active")

    assert "constant_energy_correction" in result.energy.energy_formula
    assert result.problem.active_space_metadata is not None
    assert "ActiveSpaceTransformer" in result.problem.transformers_applied
    assert result.energy.total_energy == pytest.approx(
        result.energy.solver_energy
        + result.energy.constant_energy_correction
        + result.energy.nuclear_repulsion_energy,
        abs=1e-10,
    )


@pytest.mark.integration
def test_report_regeneration_includes_sampled_and_mitigation_sections(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2_shot.yaml"), output_dir=tmp_path / "report-shot")
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))

    regenerated = render_markdown_report(payload)

    assert "Sampled Result" in regenerated
    assert "Mitigation" in regenerated
    assert "Quantum Evidence" in regenerated
    assert "energy_formula" in regenerated


@pytest.mark.integration
def test_report_regeneration_includes_active_space_recommendation(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_active_space_trusted_score.yaml"),
        output_dir=tmp_path / "report-trusted-score",
    )
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))

    regenerated = render_markdown_report(payload)

    assert "Active-Space Recommendation" in regenerated
    assert "trusted_orbital_score" in regenerated
