from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.io.config import load_run_spec
from qcchem.reporting.aggregate import write_hardware_calibration_report
from qcchem.reporting.markdown import render_markdown_report
from qcchem.io.serialization import to_primitive
from qcchem.workflow.benchmark import build_hardware_calibration_suite, run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config, run_spec

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_hardware_run_report_mentions_hardware_sections(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "lih_active_shot_runtime_ready_compressed.yaml",
        output_dir=tmp_path / "lih_runtime_preview",
    )

    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Hardware Execution" in report_text
    assert "Local Calibration Summary" in report_text
    assert "executed-solver calibration only" in report_text


@pytest.mark.integration
def test_h2_puccd_preview_keeps_chemical_accuracy_with_fewer_parameters(tmp_path: Path) -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2_runtime_hardware_probe_ca.yaml")
    spec.backend.runtime.enabled = False
    spec.backend.runtime.options["submit_real_job"] = False
    spec.solver.ansatz.kind = "puccd"
    spec.run.output_dir = tmp_path / "h2_puccd_preview"

    result = run_spec(
        spec,
        source_config=str(REPO_ROOT / "configs" / "h2_runtime_hardware_probe_ca.yaml"),
        output_dir=tmp_path / "h2_puccd_preview",
    )

    assert result.variational_result is not None
    assert result.variational_result.parameter_count == 1
    assert result.chemical_accuracy is not None
    assert result.chemical_accuracy.meets_chemical_accuracy is True
    assert result.energy.total_energy == pytest.approx(result.exact_baseline.total_energy, abs=1.0e-6)


@pytest.mark.integration
def test_hardware_run_report_keeps_hardware_sections_when_data_is_unavailable(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_exact_preview",
    )
    assert result.hardware_verified is False
    assert result.hardware_evidence_tier is None

    payload = to_primitive(result)
    payload["calibration"] = None
    payload["runtime_submission"] = None
    payload["hardware_verified"] = False
    payload["hardware_evidence_tier"] = None
    report_text = render_markdown_report(payload)

    assert "Local Calibration Summary" in report_text
    assert "runtime-derived hardware evidence" in report_text
    assert "- available: `False`" in report_text
    assert "Hardware Execution" in report_text
    assert "- hardware_verified: `False`" in report_text
    assert "- attempted: `None`" in report_text


@pytest.mark.integration
def test_render_markdown_report_distinguishes_local_and_runtime_chemical_accuracy(tmp_path: Path) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_exact_preview_for_accuracy_sections",
    )
    payload = to_primitive(result)
    payload["chemical_accuracy"]["assessment_target"] = "local_execution"
    payload["runtime_chemical_accuracy"] = {
        "available": True,
        "assessment_target": "runtime_derived",
        "status": "exploratory",
        "meets_chemical_accuracy": False,
        "absolute_error_hartree": 0.05,
        "absolute_error_kcal_mol": 31.3754737,
        "threshold_hartree": 0.0016,
        "threshold_kcal_mol": 1.0040151584,
        "statistical_error": 0.02,
        "reference_energy": payload["exact_baseline"]["total_energy"],
        "computed_energy": payload["exact_baseline"]["total_energy"] + 0.05,
        "notes": ["Runtime-derived chemistry estimate does not meet chemical accuracy."],
    }

    report_text = render_markdown_report(payload)

    assert "## Chemical Accuracy (Local Execution)" in report_text
    assert "## Chemical Accuracy (Runtime-Derived)" in report_text
    assert "assessment_target: `runtime_derived`" in report_text
    assert "Runtime-derived chemistry estimate does not meet chemical accuracy." in report_text


@pytest.mark.integration
def test_hardware_dashboard_serializes_summary(tmp_path: Path) -> None:
    dashboard = {
        "summary": {
            "total_cases": 2,
            "runtime_evidence_status_counts": {"retrieved_result": 1, "none": 1},
            "hardware_verified_cases": ["h2_runtime_probe"],
        },
        "cases": [
            {
                "name": "h2_runtime_probe",
                "backend_name": "ibm_marrakesh",
                "layout_strategy": "min_weighted_error",
                "selected_layout": [12, 15, 18, 19],
                "transpiled_two_qubit_gate_count": 42,
                "transpiled_depth": 138,
                "runtime_submission_status": "succeeded",
                "runtime_submission_wall_time_seconds": 15.0,
                "runtime_shots": 44,
                "runtime_usage_seconds": 1,
                "runtime_usage_quantum_seconds": 1,
                "requested_precision_target": 0.05,
                "requested_budget_strategy": "shot_budget",
                "achieved_error": 0.03,
                "achieved_error_status": "derived_from_runtime_result",
                "chemical_accuracy_target_hartree": 0.0016,
                "meets_chemical_accuracy": False,
                "distance_to_chemical_accuracy": 0.0284,
                "hardware_verified": True,
                "runtime_evidence_tier": "retrieved_result",
                "runtime_evidence_status": "retrieved_result",
            },
            {
                "name": "h2_local_reference",
                "backend_name": None,
                "runtime_submission_status": None,
                "runtime_submission_wall_time_seconds": None,
                "runtime_shots": None,
                "achieved_error": None,
                "achieved_error_status": "no_runtime_submission",
                "hardware_verified": False,
                "runtime_evidence_tier": None,
                "runtime_evidence_status": "none",
            },
        ]
    }

    output = tmp_path / "hardware_dashboard.md"
    write_hardware_calibration_report(dashboard, output)
    text = output.read_text(encoding="utf-8")
    assert "runtime submission evidence" in text.lower()
    assert "h2_runtime_probe" in text
    assert "retrieved_result" in text
    assert "h2_local_reference" in text
    assert "Achieved Error Status" in text
    assert "derived_from_runtime_result" in text
    assert "no_runtime_submission" in text
    assert "Runtime Usage (s)" in text
    assert "Requested Precision" in text
    assert "Meets Chem Acc" in text
    assert "Layout Strategy" in text
    assert "2Q Gates" in text
    assert "12,15,18,19" in text


@pytest.mark.integration
def test_hardware_suite_builder_uses_runtime_submission_evidence(tmp_path: Path) -> None:
    h2_result = {
        "run_id": "h2_runtime_probe",
        "hardware_verified": False,
        "hardware_evidence_tier": None,
        "energy": {
            "constant_energy_correction": 1.25,
            "nuclear_repulsion_energy": 0.5,
        },
        "exact_baseline": {
            "available": True,
            "total_energy": 3.6,
        },
        "calibration": {
            "measured_wall_time_seconds": 1.5,
            "measured_shot_usage": 9999,
            "achieved_error": 9.9,
        },
        "benchmark": {"absolute_error": 9.9},
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": True,
            "submission_wall_time_seconds": 388.7,
            "job_id": "job-h2",
            "backend_name": "ibm_marrakesh",
            "usage_estimation": {"quantum_seconds": 10.99999997},
            "job_metrics": {"usage": {"seconds": 1, "quantum_seconds": 1}},
            "options_snapshot": {
                "precision_target": 0.05,
                "budget_strategy": "shot_budget",
                "max_budgeted_shots": 1024,
            },
            "returned_job_metadata": {
                "evs": [2.0],
                "metadata": {"shots": 44},
            },
        },
    }
    lih_result = {
        "run_id": "lih_runtime_probe",
        "hardware_verified": True,
        "hardware_evidence_tier": "retrieved_result",
        "energy": {
            "constant_energy_correction": -4.0,
            "nuclear_repulsion_energy": 1.0,
        },
        "exact_baseline": {
            "available": True,
            "total_energy": -2.75,
        },
        "calibration": {
            "measured_wall_time_seconds": 2.5,
            "measured_shot_usage": 8888,
            "achieved_error": 8.8,
        },
        "benchmark": {"absolute_error": 0.0025},
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": False,
            "submission_wall_time_seconds": 22.4,
            "job_id": "job-lih",
            "backend_name": "ibm_fez",
            "failure_category": "job_result_failed",
        },
    }

    h2_path = tmp_path / "h2_runtime_probe" / "result.json"
    h2_path.parent.mkdir(parents=True, exist_ok=True)
    h2_path.write_text(json.dumps(h2_result), encoding="utf-8")
    lih_path = tmp_path / "lih_runtime_probe" / "result.json"
    lih_path.parent.mkdir(parents=True, exist_ok=True)
    lih_path.write_text(json.dumps(lih_result), encoding="utf-8")

    summary = build_hardware_calibration_suite(
        [h2_path, lih_path],
        output_root=tmp_path / "hardware_calibration_suite_v1",
    )

    summary_path = tmp_path / "hardware_calibration_suite_v1" / "hardware_calibration_summary.json"
    report_path = tmp_path / "hardware_calibration_suite_v1" / "hardware_calibration_report.md"
    assert summary_path.exists()
    assert report_path.exists()

    cases_by_name = {case["name"]: case for case in summary["cases"]}
    assert cases_by_name["h2_runtime_probe"]["runtime_evidence_status"] == "retrieved_result"
    assert cases_by_name["h2_runtime_probe"]["runtime_evidence_tier"] == "retrieved_result"
    assert cases_by_name["h2_runtime_probe"]["hardware_verified"] is True
    assert cases_by_name["h2_runtime_probe"]["runtime_submission_wall_time_seconds"] == pytest.approx(388.7)
    assert cases_by_name["h2_runtime_probe"]["runtime_shots"] == 44
    assert cases_by_name["h2_runtime_probe"]["runtime_usage_seconds"] == 1
    assert cases_by_name["h2_runtime_probe"]["runtime_usage_quantum_seconds"] == 1
    assert cases_by_name["h2_runtime_probe"]["requested_precision_target"] == pytest.approx(0.05)
    assert cases_by_name["h2_runtime_probe"]["requested_budget_strategy"] == "shot_budget"
    assert cases_by_name["h2_runtime_probe"]["achieved_error"] == pytest.approx(0.15)
    assert cases_by_name["h2_runtime_probe"]["achieved_error_status"] == "derived_from_runtime_result"
    assert cases_by_name["h2_runtime_probe"]["chemical_accuracy_target_hartree"] == pytest.approx(0.0016)
    assert cases_by_name["h2_runtime_probe"]["meets_chemical_accuracy"] is False
    assert cases_by_name["h2_runtime_probe"]["distance_to_chemical_accuracy"] == pytest.approx(0.1484)
    assert cases_by_name["lih_runtime_probe"]["runtime_evidence_status"] == "submitted"
    assert cases_by_name["lih_runtime_probe"]["runtime_evidence_tier"] == "submitted"
    assert cases_by_name["lih_runtime_probe"]["hardware_verified"] is False
    assert cases_by_name["lih_runtime_probe"]["runtime_submission_status"] == "job_result_failed"
    assert cases_by_name["lih_runtime_probe"]["runtime_submission_wall_time_seconds"] == pytest.approx(22.4)
    assert cases_by_name["lih_runtime_probe"]["runtime_shots"] is None
    assert cases_by_name["lih_runtime_probe"]["achieved_error"] is None
    assert cases_by_name["lih_runtime_probe"]["achieved_error_status"] == "runtime_result_not_retrieved"

    report_text = report_path.read_text(encoding="utf-8")
    assert "Runtime Evidence Status" in report_text
    assert "Achieved Error Status" in report_text
    assert "h2_runtime_probe" in report_text
    assert "lih_runtime_probe" in report_text


@pytest.mark.integration
def test_hardware_calibration_suite_yaml_runs_through_benchmark_entrypoint(tmp_path: Path) -> None:
    result_one = {
        "run_id": "h2_runtime_probe",
        "energy": {
            "constant_energy_correction": 1.25,
            "nuclear_repulsion_energy": 0.5,
        },
        "exact_baseline": {
            "available": True,
            "total_energy": 3.6,
        },
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": True,
            "submission_wall_time_seconds": 18.0,
            "job_id": "job-h2",
            "backend_name": "ibm_marrakesh",
            "returned_job_metadata": {
                "evs": [2.0],
                "metadata": {"shots": 44},
            },
        },
    }
    result_two = {
        "run_id": "lih_runtime_probe",
        "energy": {
            "constant_energy_correction": -4.0,
            "nuclear_repulsion_energy": 1.0,
        },
        "exact_baseline": {
            "available": True,
            "total_energy": -2.75,
        },
        "runtime_submission": {
            "attempted": True,
            "submitted": False,
            "succeeded": False,
            "failure_category": "runtime_not_submitted",
        },
    }

    first_result_path = tmp_path / "h2_runtime_probe" / "result.json"
    first_result_path.parent.mkdir(parents=True, exist_ok=True)
    first_result_path.write_text(json.dumps(result_one), encoding="utf-8")
    second_result_path = tmp_path / "lih_runtime_probe" / "result.json"
    second_result_path.parent.mkdir(parents=True, exist_ok=True)
    second_result_path.write_text(json.dumps(result_two), encoding="utf-8")

    config_path = tmp_path / "hardware_calibration_suite.yaml"
    config_path.write_text(
        "\n".join(
            [
                "hardware_calibration_suite:",
                "  name: hardware_calibration_suite_test",
                "  description: Synthetic dashboard config for benchmark dispatch coverage.",
                "  output_root: artifacts/should_be_overridden",
                "  cases:",
                "    - name: h2_runtime_probe",
                f"      result_json: {first_result_path}",
                "    - name: lih_runtime_probe",
                f"      result_json: {second_result_path}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "hardware_suite_output"
    summary = run_benchmark_suite_from_config(config_path, output_dir=output_dir)

    assert summary["suite_name"] == "hardware_suite_output"
    assert summary["summary"]["total_cases"] == 2
    assert (output_dir / "hardware_calibration_summary.json").exists()
    assert (output_dir / "hardware_calibration_report.md").exists()


@pytest.mark.integration
def test_hardware_suite_prefers_runtime_submission_sidecar_when_present(tmp_path: Path) -> None:
    result_payload = {
        "run_id": "lih_runtime_probe",
        "energy": {
            "constant_energy_correction": -4.0,
            "nuclear_repulsion_energy": 1.0,
        },
        "exact_baseline": {
            "available": True,
            "total_energy": -2.75,
        },
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": True,
            "backend_name": "ibm_fez",
            "returned_job_metadata": {
                "evs": [0.0],
                "metadata": {"shots": 44},
            },
        },
    }
    sidecar_payload = {
        "attempted": True,
        "submitted": True,
        "succeeded": True,
        "backend_name": "ibm_fez",
        "job_id": "job-lih-sidecar",
        "usage_estimation": {"quantum_seconds": 12.5},
        "job_metrics": {"usage": {"seconds": 2, "quantum_seconds": 2}},
        "options_snapshot": {
            "precision_target": 0.05,
            "budget_strategy": "shot_budget",
            "max_budgeted_shots": 1024,
        },
        "returned_job_metadata": {
            "evs": [0.0],
            "metadata": {"shots": 44},
        },
    }

    result_dir = tmp_path / "lih_runtime_probe"
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / "result.json"
    result_path.write_text(json.dumps(result_payload), encoding="utf-8")
    (result_dir / "runtime_submission.json").write_text(json.dumps(sidecar_payload), encoding="utf-8")

    summary = build_hardware_calibration_suite(
        [result_path],
        output_root=tmp_path / "hardware_suite",
    )

    case = summary["cases"][0]
    assert case["job_id"] == "job-lih-sidecar"
    assert case["runtime_usage_seconds"] == 2
    assert case["runtime_usage_quantum_seconds"] == 2
    assert case["requested_budget_strategy"] == "shot_budget"
    assert case["meets_chemical_accuracy"] is False
