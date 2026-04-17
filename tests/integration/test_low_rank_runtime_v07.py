from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_low_rank_runtime_ready_run_persists_measurement_and_runtime_policy(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_active_shot_runtime_ready_compressed.yaml"),
        output_dir=tmp_path / "lih-low-rank-runtime",
    )

    assert result.measurement is not None
    assert result.measurement.low_rank_aware is True
    assert result.measurement.group_count > 0
    assert result.measurement.estimated_shot_cost >= result.measurement.group_count
    assert result.measurement.execution_mode == "runtime_estimator"
    assert result.runtime_options is not None
    assert result.runtime_options.low_rank_workload is True
    assert result.runtime_options.grouping_policy == "commuting_low_rank"
    assert result.runtime_options.precision_target == pytest.approx(5.0e-3, abs=1e-12)
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert "measurement" in payload
    assert payload["runtime_options"]["low_rank_workload"] is True


@pytest.mark.integration
def test_low_rank_benchmark_suite_reports_measurement_costs(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/low_rank_suite_v1.yaml"),
        output_dir=tmp_path / "low-rank-suite",
    )

    assert result.summary.total_cases >= 4
    assert any(case.metrics.get("measurement_group_count") is not None for case in result.cases)
    assert any(case.metrics.get("estimated_measurement_cost") is not None for case in result.cases)
    assert any(case.metrics.get("runtime_service") is not None for case in result.cases)


@pytest.mark.integration
def test_qcschema_and_hdf5_exports_include_low_rank_sections(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_active_exact_compressed_cholesky.yaml"),
        output_dir=tmp_path / "lih-low-rank-export",
    )

    assert result.artifacts.qcschema_json is not None and result.artifacts.qcschema_json.exists()
    assert result.artifacts.hdf5_file is not None and result.artifacts.hdf5_file.exists()
    payload = json.loads(result.artifacts.qcschema_json.read_text(encoding="utf-8"))
    assert "measurement" in payload["extras"]
    assert "runtime_options" in payload["extras"]


@pytest.mark.integration
def test_runtime_ready_run_exports_hardware_metadata_in_qcschema(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_active_shot_runtime_ready_compressed.yaml"),
        output_dir=tmp_path / "lih-runtime-export",
    )

    assert result.artifacts.qcschema_json is not None and result.artifacts.qcschema_json.exists()
    assert result.runtime_submission is not None

    payload = json.loads(result.artifacts.qcschema_json.read_text(encoding="utf-8"))
    extras = payload["extras"]

    assert "hardware_verified" in extras
    assert "hardware_evidence_tier" in extras
    assert "runtime_submission" in extras
    assert extras["hardware_verified"] is result.hardware_verified
    assert extras["hardware_evidence_tier"] == result.hardware_evidence_tier
    assert extras["runtime_submission"]["attempted"] is result.runtime_submission.attempted
    assert extras["runtime_submission"]["submitted"] is result.runtime_submission.submitted
