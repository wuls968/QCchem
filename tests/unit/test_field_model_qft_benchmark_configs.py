from __future__ import annotations

from pathlib import Path

from qcchem.io.benchmark_config import load_benchmark_suite_spec

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = REPO_ROOT / "benchmarks"


def _suite(name: str):
    return load_benchmark_suite_spec(BENCHMARKS / name)


def _cases_by_name(suite_name: str):
    return {case.name: case for case in _suite(suite_name).cases}


def test_qft_smoke_v2_covers_small_local_and_disabled_runtime_preview_cases() -> None:
    cases = _cases_by_name("field_model_qft_smoke_v2.yaml")

    assert "h2_lattice_qed_2site_exact" in cases
    assert "h2_lattice_qed_2site_sector_audit" in cases
    assert "h2_lattice_qed_2site_dynamics" in cases
    assert "h2_lattice_qed_4site_sparse_projected" in cases
    assert "h2_lattice_qed_2d_plaquette" in cases

    sparse = cases["h2_lattice_qed_4site_sparse_projected"]
    assert {"four_site", "sparse_projected"} <= set(sparse.tags)
    plaquette = cases["h2_lattice_qed_2d_plaquette"]
    assert "plaquette" in plaquette.tags

    preview_disabled = cases["h2_lattice_qed_runtime_preview_disabled"]
    assert preview_disabled.overrides["problem.qft.dynamics.runtime.enabled"] is False
    assert preview_disabled.overrides["backend.runtime.enabled"] is False
    assert preview_disabled.overrides["backend.runtime.options"]["submit_real_job"] is False
    assert preview_disabled.overrides["backend.runtime.options"]["wait_for_result"] is False


def test_qft_cutoff_grid_convergence_v1_covers_cutoff_grid_boundary_and_sector_options() -> None:
    cases = _suite("field_model_qft_cutoff_grid_convergence_v1.yaml").cases

    electric_cutoffs = {
        case.overrides.get("problem.qft.gauge.electric_cutoff")
        for case in cases
        if "electric_cutoff_scan" in case.tags
    }
    assert electric_cutoffs == {0, 1, 2}

    overrides = [case.overrides for case in cases]
    assert any(item.get("problem.qft.grid.spacing") == [0.60] for item in overrides)
    assert any(item.get("problem.qft.grid.softening") == 0.25 for item in overrides)
    assert any(item.get("problem.qft.grid.shape") == [3] for item in overrides)
    assert any(item.get("problem.qft.grid.boundary") == "open" for item in overrides)
    assert any(item.get("problem.qft.grid.boundary") == "periodic" for item in overrides)
    assert any(item.get("problem.qft.constraints.target_charge_sector") == "0" for item in overrides)


def test_qft_dynamics_resource_v1_covers_trotter_steps_and_runtime_preview() -> None:
    cases = _suite("field_model_qft_dynamics_resource_v1.yaml").cases

    trotter_steps = {
        case.overrides.get("problem.qft.dynamics.evolution.trotter_step")
        for case in cases
        if "trotter_step_scan" in case.tags
    }
    assert trotter_steps == {0.20, 0.10, 0.05}

    runtime_cases = [case for case in cases if "runtime_preview" in case.tags]
    assert len(runtime_cases) == 1
    options = runtime_cases[0].overrides["backend.runtime.options"]
    assert options["submit_real_job"] is False
    assert options["use_batch"] is True
    assert runtime_cases[0].overrides["problem.qft.dynamics.time_grid.stop"] == 1.0
    assert runtime_cases[0].overrides["problem.qft.dynamics.runtime.max_pub_count"] == 4
    assert runtime_cases[0].overrides["problem.qft.dynamics.runtime.time_point_indices"] == [0, 10]


def test_qft_hardware_micro_v1_defaults_to_preview_only_with_tiny_budget() -> None:
    cases = _cases_by_name("field_model_qft_hardware_micro_v1.yaml")
    micro = cases["h2_lattice_qed_hardware_micro_preview"]

    assert micro.overrides["backend.runtime.max_budgeted_shots"] <= 512
    options = micro.overrides["backend.runtime.options"]
    assert options["submit_real_job"] is False
    assert micro.overrides["problem.qft.dynamics.time_grid.stop"] == 1.0
    assert micro.overrides["problem.qft.dynamics.runtime.time_point_indices"] == [0, 10]
    assert micro.overrides["problem.qft.dynamics.runtime.observable_names"] == [
        "particle_number",
        "total_gauss_violation",
    ]
    assert options["default_shots"] <= 512
    assert micro.overrides["problem.qft.dynamics.runtime.max_pub_count"] == 4
    assert micro.overrides["problem.qft.dynamics.runtime.max_total_pub_shots"] <= 2048
    assert micro.overrides["problem.qft.dynamics.runtime.max_logical_depth"] <= 200
    assert options["wait_for_result"] is False
