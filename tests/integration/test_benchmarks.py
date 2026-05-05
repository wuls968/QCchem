from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.chem import build_electronic_structure_context
from qcchem.io.config import load_run_spec
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.reporting.markdown import write_markdown_report
from qcchem.solvers import ExactDiagonalizationSolver
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
