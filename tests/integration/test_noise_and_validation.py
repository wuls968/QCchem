from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from qcchem.reporting.markdown import render_markdown_report
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config


def _write_yaml(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


@pytest.mark.integration
def test_noisy_run_persists_noise_runtime_and_sampling_metadata(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path / "h2_noisy.yaml",
        {
            "molecule": {
                "name": "H2-noisy-test",
                "geometry": [
                    {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                    {"symbol": "H", "coords": [0.0, 0.0, 0.735]},
                ],
                "charge": 0,
                "multiplicity": 1,
                "basis": "sto3g",
            },
            "problem": {"active_space": None},
            "mapping": {"kind": "jordan_wigner"},
            "policy": {"name": "hardware_ready"},
            "backend": {
                "kind": "shot_estimator",
                "shots": 1024,
                "seed": 222,
                "repetitions": 3,
                "abelian_grouping": False,
                "noise": {
                    "enabled": True,
                    "profile": "depolarizing_readout",
                    "depolarizing_probability_1q": 0.001,
                    "depolarizing_probability_2q": 0.01,
                    "readout_error_probability": 0.02,
                },
                "runtime": {
                    "enabled": True,
                    "service": "local_aer",
                    "runtime_ready": True,
                    "session_ready": True,
                    "batch_ready": True,
                    "options": {"optimization_level": 1, "resilience_level": 0},
                },
            },
            "solver": {
                "kind": "vqe",
                "optimizer": {"kind": "COBYLA", "maxiter": 20},
                "ansatz": {"kind": "uccsd", "reps": 1},
                "initial_point": "zeros",
            },
            "benchmark": {
                "enabled": True,
                "exact_baseline_qubit_limit": 12,
                "absolute_error_threshold": 0.25,
                "relative_error_threshold": 0.25,
            },
            "mitigation": {"symmetry_check": {"enabled": True, "strategy": "parity_placeholder"}},
            "run": {"seed": 222, "output_dir": str(tmp_path / "h2-noisy"), "overwrite": True},
        },
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-noisy")

    assert result.noise_model is not None
    assert result.noise_model.enabled is True
    assert result.noise_model.profile == "depolarizing_readout"
    assert result.runtime_options is not None
    assert result.runtime_options.session_ready is True
    assert result.runtime_options.batch_ready is True
    assert result.backend_capability.noise_model_ready is True
    assert result.backend_capability.session_ready is True
    assert result.backend_capability.batch_ready is True
    assert result.sampled_result is not None
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert "noise_model" in payload
    assert "runtime_options" in payload


@pytest.mark.integration
def test_reduction_audit_is_persisted_for_active_space_runs(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2o_active_space.yaml"), output_dir=tmp_path / "h2o-audit")

    assert result.reduction_audit is not None
    assert "ActiveSpaceTransformer" in result.reduction_audit.transformers_applied
    assert (
        result.reduction_audit.original_num_spatial_orbitals
        >= result.reduction_audit.reduced_num_spatial_orbitals
    )
    assert "constant_energy_correction" in result.reduction_audit.energy_formula
    report = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Reduction Audit" in report


@pytest.mark.integration
def test_property_validation_tracks_validated_and_exploratory_entries(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path / "h2_property_validation.yaml",
        {
            "molecule": {
                "name": "H2-property-validation",
                "geometry": [
                    {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                    {"symbol": "H", "coords": [0.0, 0.0, 0.735]},
                ],
                "charge": 0,
                "multiplicity": 1,
                "basis": "sto3g",
            },
            "problem": {"active_space": None},
            "mapping": {"kind": "jordan_wigner"},
            "backend": {"kind": "statevector"},
            "solver": {"kind": "exact"},
            "benchmark": {"enabled": True},
            "tasks": {
                "excited_state": {"enabled": True, "method": "exact_spectrum", "num_states": 2, "state_indices": [1]},
                "properties": [
                    {"property_name": "dipole_moment", "method": "exact_expectation", "state_indices": [0]},
                    {"property_name": "transition_dipole", "method": "exact_transition", "state_indices": [0, 1]},
                    {"property_name": "oscillator_strength", "method": "exact_transition", "state_indices": [0, 1]},
                ],
            },
            "run": {"seed": 19, "output_dir": str(tmp_path / "h2-property"), "overwrite": True},
        },
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-property")

    assert result.property_result is not None
    properties = {item.property_name: item for item in result.property_result.properties}
    assert properties["dipole_moment"].implementation_status == "validated"
    assert properties["dipole_moment"].provenance["source"] == "exact_expectation"
    assert properties["transition_dipole"].implementation_status == "validated"
    assert properties["transition_dipole"].value is not None
    assert properties["oscillator_strength"].implementation_status == "validated"
    assert properties["oscillator_strength"].value is not None


@pytest.mark.integration
def test_exact_excited_state_mini_artifact_is_validated(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path / "h2_excited_mini.yaml",
        {
            "molecule": {
                "name": "H2-excited-mini",
                "geometry": [
                    {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                    {"symbol": "H", "coords": [0.0, 0.0, 0.735]},
                ],
                "charge": 0,
                "multiplicity": 1,
                "basis": "sto3g",
            },
            "problem": {"active_space": None},
            "mapping": {"kind": "jordan_wigner"},
            "backend": {"kind": "statevector"},
            "solver": {"kind": "exact"},
            "benchmark": {"enabled": True},
            "tasks": {
                "excited_state": {"enabled": True, "method": "exact_spectrum", "num_states": 2, "state_indices": [1]}
            },
            "run": {"seed": 23, "output_dir": str(tmp_path / "h2-excited"), "overwrite": True},
        },
    )

    result = run_from_config(config_path, output_dir=tmp_path / "h2-excited")

    assert result.excited_state_result is not None
    assert result.excited_state_result.verification_status == "validated"
    assert result.excited_state_result.states[0].baseline["source"] == "exact_spectrum"
    regenerated = render_markdown_report(json.loads(result.artifacts.result_json.read_text(encoding="utf-8")))
    assert "Excited-state Result" in regenerated


@pytest.mark.integration
def test_noise_comparison_benchmark_case_summarizes_exact_ideal_and_noisy(tmp_path: Path) -> None:
    noisy_config = _write_yaml(
        tmp_path / "h2_noise_benchmark.yaml",
        {
            "molecule": {
                "name": "H2-noise-benchmark",
                "geometry": [
                    {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                    {"symbol": "H", "coords": [0.0, 0.0, 0.735]},
                ],
                "charge": 0,
                "multiplicity": 1,
                "basis": "sto3g",
            },
            "problem": {"active_space": None},
            "mapping": {"kind": "jordan_wigner"},
            "policy": {"name": "benchmark"},
            "backend": {
                "kind": "shot_estimator",
                "shots": 1024,
                "seed": 333,
                "repetitions": 3,
                "abelian_grouping": False,
                "noise": {
                    "enabled": True,
                    "profile": "depolarizing_readout",
                    "depolarizing_probability_1q": 0.001,
                    "depolarizing_probability_2q": 0.01,
                    "readout_error_probability": 0.02,
                },
            },
            "solver": {
                "kind": "vqe",
                "optimizer": {"kind": "COBYLA", "maxiter": 20},
                "ansatz": {"kind": "uccsd", "reps": 1},
                "initial_point": "zeros",
            },
            "benchmark": {
                "enabled": True,
                "exact_baseline_qubit_limit": 12,
                "absolute_error_threshold": 0.25,
                "relative_error_threshold": 0.25,
            },
            "run": {"seed": 333, "output_dir": str(tmp_path / "h2-noise-bench"), "overwrite": True},
        },
    )
    suite_path = _write_yaml(
        tmp_path / "noise_suite.yaml",
        {
            "benchmark_suite": {
                "name": "noise_suite",
                "description": "Mini noise comparison suite.",
                "cases": [
                    {
                        "name": "h2_noise_compare",
                        "kind": "noise_comparison",
                        "config": str(noisy_config),
                        "expected_status": "unstable",
                    }
                ],
            }
        },
    )

    result = run_benchmark_suite_from_config(suite_path, output_dir=tmp_path / "noise-suite")

    assert result.summary.total_cases == 1
    case = result.cases[0]
    assert case.kind == "noise_comparison"
    assert {"exact_total_energy", "ideal_total_energy", "noisy_total_energy"}.issubset(case.metrics)
    assert case.status in {"validated", "exploratory", "unstable"}
