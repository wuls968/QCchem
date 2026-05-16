from __future__ import annotations

import csv
import json

import pytest

from qcchem.validation import run_qmmm_embedding_validation


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
    assert all(item["passed"] for item in payload["metrics"])
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
