from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.reporting.aggregate import (
    render_benchmark_report,
    render_scan_report,
    render_study_report,
)
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.study import run_study_from_config
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_study_workflow_aggregates_runs_and_writes_registry(tmp_path: Path) -> None:
    result = run_study_from_config(
        Path("configs/studies/mini_comparison.yaml"),
        output_dir=tmp_path / "study-mini",
    )

    assert result.run_records
    assert len(result.run_records) == 2
    assert result.summary.total_runs == 2
    assert result.artifacts.study_result_json.exists()
    assert result.artifacts.study_report_markdown.exists()
    assert result.artifacts.registry_json.exists()
    regenerated = render_study_report(json.loads(result.artifacts.study_result_json.read_text()))
    assert "Study Summary" in regenerated


@pytest.mark.integration
def test_benchmark_suite_runs_and_generates_aggregate_report(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/mini_suite.yaml"),
        output_dir=tmp_path / "bench-mini",
    )

    assert result.cases
    assert result.summary.total_cases >= 3
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    regenerated = render_benchmark_report(json.loads(result.artifacts.result_json.read_text()))
    assert "Benchmark Suite Summary" in regenerated


@pytest.mark.integration
def test_scan_workflow_generates_point_runs_and_scan_table(tmp_path: Path) -> None:
    result = run_scan_from_config(
        Path("configs/scans/h2_short_scan.yaml"),
        output_dir=tmp_path / "scan-mini",
    )

    assert len(result.points) == 3
    assert result.artifacts.scan_table_csv.exists()
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    assert all(point.run_artifact_root.exists() for point in result.points)
    regenerated = render_scan_report(json.loads(result.artifacts.result_json.read_text()))
    assert "Scan Summary" in regenerated


def test_aggregate_workflows_reject_existing_output_without_overwrite(tmp_path: Path) -> None:
    benchmark_config = tmp_path / "benchmark.yaml"
    benchmark_config.write_text(
        """
benchmark_suite:
  name: reject_existing_benchmark
  cases:
    - name: h2
      kind: run
      config: configs/h2.yaml
        """.strip(),
        encoding="utf-8",
    )
    study_config = tmp_path / "study.yaml"
    study_config.write_text(
        """
study:
  name: reject_existing_study
  runs:
    - name: h2
      config: configs/h2.yaml
        """.strip(),
        encoding="utf-8",
    )
    scan_config = tmp_path / "scan.yaml"
    scan_config.write_text(
        """
scan:
  name: reject_existing_scan
  base_config: configs/h2.yaml
  parameter:
    name: bond_length
    kind: bond_distance
    values: [0.735]
        """.strip(),
        encoding="utf-8",
    )

    cases = [
        (
            lambda output_dir: run_benchmark_suite_from_config(
                benchmark_config,
                output_dir=output_dir,
                overwrite=False,
            ),
            "benchmark",
        ),
        (
            lambda output_dir: run_study_from_config(
                study_config,
                output_dir=output_dir,
                overwrite=False,
            ),
            "study",
        ),
        (
            lambda output_dir: run_scan_from_config(
                scan_config,
                output_dir=output_dir,
                overwrite=False,
            ),
            "scan",
        ),
    ]
    for runner, label in cases:
        output_dir = tmp_path / f"{label}-existing"
        output_dir.mkdir()
        sentinel = output_dir / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")

        with pytest.raises(FileExistsError, match="already exists and is not empty"):
            runner(output_dir)

        assert sentinel.read_text(encoding="utf-8") == "keep"


@pytest.mark.integration
def test_vqe_scan_uses_linear_predictor_after_previous_point(tmp_path: Path) -> None:
    scan_config = tmp_path / "h2_vqe_scan.yaml"
    scan_config.write_text(
        """
scan:
  name: h2_vqe_continuity_scan
  base_config: configs/h2.yaml
  parameter:
    name: bond_length
    kind: bond_distance
    atom_indices: [0, 1]
    axis: [0.0, 0.0, 1.0]
    values: [0.5, 0.735, 1.0]
        """.strip(),
        encoding="utf-8",
    )

    result = run_scan_from_config(scan_config, output_dir=tmp_path / "scan-vqe")

    assert len(result.points) == 3
    assert result.points[0].initial_point_reused is False
    assert result.points[1].initial_point_reused is True
    assert result.points[1].initial_point_source == result.points[0].point_label
    assert result.points[1].initial_point_strategy == "previous_optimal"
    assert result.points[2].initial_point_reused is True
    assert result.points[2].initial_point_source == result.points[1].point_label
    assert result.points[2].initial_point_strategy == "linear_predictor"
    assert result.points[2].history_sources == [
        result.points[0].point_label,
        result.points[1].point_label,
    ]
    table = result.artifacts.scan_table_csv.read_text(encoding="utf-8")
    assert "initial_point_reused" in table
    assert "initial_point_strategy" in table
    assert "effective_strategy" in table
    assert "candidate_source" in table
    assert "history_sources" in table
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["points"][1]["initial_point_reused"] is True
    point_payload = json.loads((result.points[1].run_artifact_root / "result.json").read_text(encoding="utf-8"))
    assert point_payload["variational_result"]["initial_point_strategy"] == "previous_optimal"
    assert point_payload["variational_result"]["initial_point_provenance"]["candidate_source"] == result.points[0].point_label
    predictor_payload = json.loads((result.points[2].run_artifact_root / "result.json").read_text(encoding="utf-8"))
    assert predictor_payload["variational_result"]["initial_point_strategy"] == "linear_predictor"
    assert predictor_payload["variational_result"]["initial_point_provenance"]["history_sources"] == [
        result.points[0].point_label,
        result.points[1].point_label,
    ]


@pytest.mark.integration
def test_lih_active_statevector_scan_records_predictor_provenance(tmp_path: Path) -> None:
    scan_config = tmp_path / "lih_vqe_scan.yaml"
    scan_config.write_text(
        """
scan:
  name: lih_vqe_continuity_scan
  base_config: configs/lih_active_vqe_statevector.yaml
  parameter:
    name: bond_length
    kind: bond_distance
    atom_indices: [0, 1]
    axis: [0.0, 0.0, 1.0]
    values: [1.2, 1.6, 2.0]
        """.strip(),
        encoding="utf-8",
    )

    result = run_scan_from_config(scan_config, output_dir=tmp_path / "lih-scan-vqe")

    assert len(result.points) == 3
    assert result.points[1].initial_point_strategy == "previous_optimal"
    assert result.points[2].initial_point_strategy == "linear_predictor"
    assert result.points[2].history_sources == [
        result.points[0].point_label,
        result.points[1].point_label,
    ]
    assert result.points[2].evaluations is not None
    assert result.points[2].parameter_count is not None


@pytest.mark.integration
def test_study_continuity_is_opt_in(tmp_path: Path) -> None:
    study_config = tmp_path / "h2_study_default.yaml"
    study_config.write_text(
        """
study:
  name: h2_study_default
  runs:
    - name: h2_first
      config: configs/h2.yaml
    - name: h2_second
      config: configs/h2.yaml
        """.strip(),
        encoding="utf-8",
    )

    result = run_study_from_config(study_config, output_dir=tmp_path / "study-default")

    assert len(result.run_records) == 2
    assert result.run_records[0].initial_point_reused is False
    assert result.run_records[1].initial_point_reused is False


@pytest.mark.integration
def test_study_continuity_reuses_previous_run_when_enabled(tmp_path: Path) -> None:
    study_config = tmp_path / "h2_study_continuity.yaml"
    study_config.write_text(
        """
study:
  name: h2_study_continuity
  continuity:
    enabled: true
  runs:
    - name: h2_first
      config: configs/h2.yaml
    - name: h2_second
      config: configs/h2.yaml
        """.strip(),
        encoding="utf-8",
    )

    result = run_study_from_config(study_config, output_dir=tmp_path / "study-continuity")

    assert len(result.run_records) == 2
    assert result.run_records[0].initial_point_reused is False
    assert result.run_records[1].initial_point_reused is True
    assert result.run_records[1].initial_point_source == "h2_first"
    second_payload = json.loads((result.run_records[1].artifact_root / "result.json").read_text(encoding="utf-8"))
    assert second_payload["variational_result"]["initial_point_strategy"] == "previous_optimal"
    assert second_payload["variational_result"]["initial_point_provenance"]["candidate_source"] == "h2_first"


@pytest.mark.integration
def test_study_continuity_reuses_lr_ace_previous_run_when_enabled(tmp_path: Path) -> None:
    study_config = tmp_path / "h2_lr_ace_study_continuity.yaml"
    study_config.write_text(
        """
study:
  name: h2_lr_ace_study_continuity
  continuity:
    enabled: true
  runs:
    - name: h2_lr_ace_first
      config: configs/lr_ace/h2_flagship.yaml
    - name: h2_lr_ace_second
      config: configs/lr_ace/h2_flagship.yaml
        """.strip(),
        encoding="utf-8",
    )

    result = run_study_from_config(study_config, output_dir=tmp_path / "study-lr-ace-continuity")

    assert len(result.run_records) == 2
    assert result.run_records[0].initial_point_reused is False
    assert result.run_records[1].initial_point_reused is True
    assert result.run_records[1].initial_point_source == "h2_lr_ace_first"
    second_payload = json.loads((result.run_records[1].artifact_root / "result.json").read_text(encoding="utf-8"))
    assert second_payload["variational_result"]["initial_point_strategy"] == "previous_optimal"
    assert second_payload["variational_result"]["initial_point_provenance"]["candidate_source"] == "h2_lr_ace_first"


@pytest.mark.integration
def test_study_continuity_falls_back_on_parameter_count_mismatch(tmp_path: Path) -> None:
    study_config = tmp_path / "h2_study_continuity_mismatch.yaml"
    study_config.write_text(
        """
study:
  name: h2_study_continuity_mismatch
  continuity:
    enabled: true
  runs:
    - name: h2_first
      config: configs/h2.yaml
    - name: h2_twolocal
      config: configs/h2.yaml
      overrides:
        solver.ansatz.kind: twolocal
        solver.ansatz.reps: 1
        solver.optimizer.maxiter: 5
        benchmark.absolute_error_threshold: 100.0
        benchmark.relative_error_threshold: 100.0
        """.strip(),
        encoding="utf-8",
    )

    result = run_study_from_config(study_config, output_dir=tmp_path / "study-mismatch")

    assert len(result.run_records) == 2
    assert result.run_records[1].initial_point_reused is False
    assert "does not match" in str(result.run_records[1].fallback_reason)
    second_payload = json.loads((result.run_records[1].artifact_root / "result.json").read_text(encoding="utf-8"))
    provenance = second_payload["variational_result"]["initial_point_provenance"]
    assert provenance["reused"] is False
    assert "does not match" in provenance["fallback_reason"]


@pytest.mark.integration
def test_excited_state_and_property_tasks_persist_in_run_artifact(tmp_path: Path) -> None:
    result = run_from_config(Path("configs/h2_multitask.yaml"), output_dir=tmp_path / "h2-multitask")

    assert result.excited_state_result is not None
    assert result.excited_state_result.states
    assert result.excited_state_result.verification_status in {"validated", "exploratory"}
    assert result.property_result is not None
    assert any(item.property_name == "dipole_moment" for item in result.property_result.properties)
    assert result.backend_capability.runtime_ready is True
    assert result.execution_policy.name == "publication"
    assert result.mitigation.symmetry_check["requested"] is True
    assert result.artifacts.result_json.exists()
    payload = json.loads(result.artifacts.result_json.read_text())
    assert "excited_state_result" in payload
    assert "property_result" in payload
