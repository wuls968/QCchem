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
