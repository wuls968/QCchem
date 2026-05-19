from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from qcchem.cli.main import main
from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.validation import run_qmmm_embedding_validation
from qcchem.workflow.benchmark import run_benchmark_suite_from_config


@pytest.mark.integration
def test_qmmm_embedding_validation_harness_writes_trust_artifacts(tmp_path):
    summary = run_qmmm_embedding_validation(tmp_path / "qmmm-validation", profile="smoke")

    assert summary["overall_status"] == "passed"
    assert summary["passed_cases"] == summary["case_count"] == 3
    artifact_paths = summary["artifacts"]
    result_json = tmp_path / "qmmm-validation" / "qmmm_validation.json"
    result_md = tmp_path / "qmmm-validation" / "qmmm_validation.md"
    metrics_csv = tmp_path / "qmmm-validation" / "metrics.csv"
    assert artifact_paths["json"] == str(result_json)
    assert result_json.exists()
    assert result_md.exists()
    assert metrics_csv.exists()

    payload = json.loads(result_json.read_text(encoding="utf-8"))
    assert payload["acceptance_criteria"]["environment_qubit_growth"] == 0
    assert payload["acceptance_criteria"]["quantum_evidence_closure_hartree"] == 1.0e-8
    assert all(item["passed"] for item in payload["metrics"])
    for item in payload["metrics"]:
        assert item["raw_num_qubits"] is not None
        assert item["num_qubits"] is not None
        assert item["raw_qubit_term_count"] is not None
        assert item["qubit_term_count"] is not None
        assert (
            item["pauli_term_delta_raw_to_executed"]
            == item["raw_qubit_term_count"] - item["qubit_term_count"]
        )
        assert item["symmetry_reduction_status"]
        assert item["quantum_evidence_sidecar_exists"] is True
        assert item["quantum_evidence_energy_closure_error_hartree"] < 1.0e-8
    cache_cases = [item for item in payload["metrics"] if item["case"] != "h2_legacy_alias"]
    assert cache_cases
    assert all(item["cache_hit"] for item in cache_cases)
    assert all(item["cache_validated"] for item in cache_cases)
    assert all(item["cache_reload_matrix_error"] < 1.0e-12 for item in cache_cases)
    assert "QMMM Environment Embedding Validation" in result_md.read_text(encoding="utf-8")

    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    assert {row["case"] for row in rows} == {
        "h2_damped_exact_radius_0p40",
        "h2_boundary_diagnostic",
        "h2_legacy_alias",
    }
    assert {
        "raw_num_qubits",
        "num_qubits",
        "raw_qubit_term_count",
        "qubit_term_count",
        "pauli_term_delta_raw_to_executed",
        "symmetry_reduction_status",
        "symmetry_reduction_validation_absolute_delta",
        "quantum_evidence_sidecar_exists",
        "quantum_evidence_energy_closure_error_hartree",
    }.issubset(rows[0].keys())


@pytest.mark.integration
def test_qmmm_validation_cli_smoke_command_writes_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_dir = tmp_path / "qmmm-cli-smoke"

    exit_code = main(["validation", "qmmm", "--profile", "smoke", "-o", str(output_dir)])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "QMMM validation completed: passed" in stdout
    assert "Profile: smoke" in stdout
    assert "Cases: 3/3" in stdout
    assert (output_dir / "qmmm_validation.json").exists()
    assert (output_dir / "qmmm_validation.md").exists()
    assert (output_dir / "metrics.csv").exists()


@pytest.mark.integration
def test_qmmm_validation_benchmark_suite_runs_profiles_and_accepts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suite_path = Path("benchmarks/qmmm_environment_embedding_suite_v1.yaml")
    spec = load_benchmark_suite_spec(suite_path)
    assert {case.name: case.profile for case in spec.cases} == {
        "qmmm_environment_embedding_smoke": "smoke",
        "qmmm_environment_embedding_full": "full",
    }
    calls: list[str] = []

    def _fake_validation(output_dir: Path, *, profile: str = "smoke"):
        calls.append(profile)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        artifacts = {
            "json": str(output_dir / "qmmm_validation.json"),
            "markdown": str(output_dir / "qmmm_validation.md"),
            "csv": str(output_dir / "metrics.csv"),
        }
        summary = {
            "schema": "qcchem.qmmm_validation.v1",
            "profile": profile,
            "case_count": 1,
            "passed_cases": 1,
            "overall_status": "passed",
            "metrics": [
                {
                    "case": f"{profile}_case",
                    "passed": True,
                    "formula_closure_error_hartree": 0.0,
                    "pyscf_nuclear_delta_error_hartree": 0.0,
                    "hcore_hermiticity_deviation": 0.0,
                    "cache_reload_matrix_error": 0.0,
                    "cache_validated": True,
                    "environment_qubit_growth": 0,
                    "raw_num_qubits": 4,
                    "num_qubits": 4,
                    "raw_qubit_term_count": 15,
                    "qubit_term_count": 15,
                    "pauli_term_delta_raw_to_executed": 0,
                    "symmetry_reduction_status": "not_requested",
                    "symmetry_reduction_validation_absolute_delta": None,
                }
            ],
            "artifacts": artifacts,
        }
        Path(artifacts["json"]).write_text(json.dumps(summary), encoding="utf-8")
        Path(artifacts["markdown"]).write_text("# QMMM", encoding="utf-8")
        Path(artifacts["csv"]).write_text("case,passed\ncase,true\n", encoding="utf-8")
        return summary

    monkeypatch.setattr("qcchem.workflow.benchmark.run_qmmm_embedding_validation", _fake_validation)

    result = run_benchmark_suite_from_config(suite_path, output_dir=tmp_path / "qmmm-suite")

    assert calls == ["smoke", "full"]
    assert result.summary.total_cases == 2
    assert result.summary.status_counts == {"validated": 2}
    assert result.acceptance_summary["accepted"] is True
    assert (result.artifacts.root / "acceptance_summary.json").exists()
    by_name = {case.name: case for case in result.cases}
    assert by_name["qmmm_environment_embedding_smoke"].metrics["qmmm_validation_profile"] == "smoke"
    assert by_name["qmmm_environment_embedding_full"].metrics["qmmm_validation_profile"] == "full"
    assert by_name["qmmm_environment_embedding_smoke"].metrics["qmmm_pauli_term_delta_max"] == 0
    assert by_name["qmmm_environment_embedding_full"].metrics["qmmm_symmetry_reduction_statuses"] == [
        "not_requested"
    ]
    assert all((case.artifact_root / "result.json").exists() for case in result.cases)
