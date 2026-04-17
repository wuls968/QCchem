import json
import types
from pathlib import Path
from types import SimpleNamespace

import h5py
import pytest

from qcchem.backends.runtime_submission import attempt_runtime_submission
from qcchem.core import BackendSpec, BenchmarkCaseSpec, RuntimeOptionsSpec
from qcchem.core.results import CalibrationSummary, RunResult
from qcchem.core.results import BenchmarkSummary, MeasurementSummary, SampledResultSummary
from qcchem.io.exports import build_qcschema_payload, write_hdf5_result
from qcchem.workflow.calibration import build_calibration_summary
from qcchem.workflow.benchmark import _run_case


def test_run_result_exposes_hardware_evidence_fields() -> None:
    assert "hardware_verified" in RunResult.__dataclass_fields__
    assert "hardware_evidence_tier" in RunResult.__dataclass_fields__


def test_calibration_summary_can_use_runtime_measured_values() -> None:
    summary = build_calibration_summary(
        measurement=None,
        sampled_result=None,
        benchmark=None,
        measured_wall_time_seconds=12.5,
        measured_shot_usage=4096,
        precision_target=0.1,
        achieved_error=0.02,
        estimated_measurement_cost=8000.0,
    )
    assert isinstance(summary, CalibrationSummary)
    assert summary.measured_wall_time_seconds == 12.5
    assert summary.measured_shot_usage == 4096
    assert summary.precision_target == 0.1
    assert summary.achieved_error == 0.02
    assert summary.estimated_measurement_cost == 8000.0


def test_calibration_summary_derives_values_from_sampled_data() -> None:
    measurement = MeasurementSummary(
        strategy="grouped",
        group_count=2,
        low_rank_aware=True,
        estimated_shot_cost=120.0,
        runtime_precision_target=0.25,
        execution_mode="local",
    )
    sampled_result = SampledResultSummary(
        available=True,
        backend_kind="statevector",
        shots=100,
        num_repeats=3,
        seed=7,
    )
    benchmark = BenchmarkSummary(
        exact_available=True,
        comparison_target="exact_baseline",
        absolute_error=0.03,
        relative_error=0.04,
        statistical_error=0.01,
        absolute_error_threshold=0.1,
        relative_error_threshold=0.2,
        within_uncertainty=True,
        meets_threshold=True,
    )

    summary = build_calibration_summary(
        measurement=measurement,
        sampled_result=sampled_result,
        benchmark=benchmark,
        measured_wall_time_seconds=5.0,
    )

    assert isinstance(summary, CalibrationSummary)
    assert summary.measured_shot_usage == 600.0
    assert summary.precision_target == 0.25
    assert summary.achieved_error == 0.03
    assert summary.estimated_vs_measured_cost == 0.2


def test_exports_include_hardware_execution_metadata(tmp_path) -> None:
    payload = {
        "schema_version": "0.10",
        "run_id": "hardware-probe",
        "verification_status": "exploratory",
        "hardware_verified": True,
        "hardware_evidence_tier": "retrieved_result",
        "solver": {"kind": "vqe"},
        "problem": {
            "basis": "sto3g",
            "molecule_name": "H2",
            "charge": 0,
            "multiplicity": 1,
        },
        "energy": {
            "total_energy": -1.05,
            "electronic_energy": -1.75,
            "nuclear_repulsion_energy": 0.7,
        },
        "provenance": {
            "git_commit": None,
            "git_branch": "main",
            "workspace_fingerprint": "abc123",
        },
        "mapping": {"kind": "jw"},
        "runtime_submission": {
            "attempted": True,
            "submitted": True,
            "succeeded": True,
            "job_id": "job-123",
            "backend_name": "ibm_marrakesh",
        },
        "measurement": None,
        "calibration": {
            "measured_wall_time_seconds": 388.7,
            "achieved_error": 0.15,
        },
        "runtime_options": None,
        "compression_result": None,
        "perturbative_correction_result": None,
        "reduction_audit": None,
    }

    qcschema = build_qcschema_payload(payload)
    assert qcschema["extras"]["hardware_verified"] is True
    assert qcschema["extras"]["hardware_evidence_tier"] == "retrieved_result"
    assert qcschema["extras"]["runtime_submission"]["job_id"] == "job-123"

    hdf5_path = tmp_path / "result.h5"
    write_hdf5_result(payload, hdf5_path)
    with h5py.File(hdf5_path, "r") as handle:
        assert json.loads(handle.attrs["hardware_verified"]) is True
        assert json.loads(handle.attrs["hardware_evidence_tier"]) == "retrieved_result"
        assert json.loads(handle["runtime_submission"].attrs["submitted"]) is True
        assert json.loads(handle["runtime_submission"].attrs["job_id"]) == "job-123"


def test_runtime_preview_skips_service_initialization_when_submission_disabled(monkeypatch) -> None:
    fake_runtime_module = types.ModuleType("qiskit_ibm_runtime")
    fake_runtime_module.__version__ = "test-version"

    class _ExplodingService:
        def __init__(self) -> None:
            raise AssertionError("QiskitRuntimeService should not be initialized for preview-only runs")

    fake_runtime_module.QiskitRuntimeService = _ExplodingService
    monkeypatch.setitem(__import__("sys").modules, "qiskit_ibm_runtime", fake_runtime_module)

    summary = attempt_runtime_submission(
        spec=BackendSpec(
            runtime=RuntimeOptionsSpec(
                enabled=True,
                service="ibm_runtime",
                runtime_ready=True,
                precision_target=0.05,
                max_budgeted_shots=1024,
                max_execution_seconds=180,
                calibration_strategy="shot_budget",
                options={"submit_real_job": False},
            )
        ),
        circuit=SimpleNamespace(num_qubits=2, num_parameters=0),
        operator=SimpleNamespace(num_qubits=2),
        parameter_values=[],
    )

    assert summary is not None
    assert summary.attempted is True
    assert summary.submitted is False
    assert summary.succeeded is False
    assert summary.failure_category == "runtime_submission_disabled"
    assert summary.provider is None
    assert summary.backend_name is None
    assert summary.options_snapshot["precision_target"] == 0.05
    assert summary.options_snapshot["max_budgeted_shots"] == 1024
    assert summary.options_snapshot["max_execution_seconds"] == 180
    assert summary.options_snapshot["budget_strategy"] == "shot_budget"


def test_benchmark_run_case_preserves_succeeded_runtime_submission_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = BenchmarkCaseSpec(
        name="runtime_case",
        kind="run",
        config=tmp_path / "runtime_case.yaml",
    )
    fake_result = SimpleNamespace(
        verification_status="unstable",
        energy=SimpleNamespace(total_energy=-7.86),
        benchmark=SimpleNamespace(
            absolute_error=0.2,
            relative_error=0.03,
            comparison_target="exact_baseline",
            within_uncertainty=False,
            compressed_vs_uncompressed=None,
        ),
        execution_policy=SimpleNamespace(name="hardware_ready"),
        compression_result=None,
        measurement=None,
        calibration=None,
        runtime_options=None,
        runtime_submission=SimpleNamespace(
            attempted=True,
            submitted=True,
            succeeded=True,
            failure_category=None,
        ),
        hardware_verified=True,
        hardware_evidence_tier="retrieved_result",
        provenance=SimpleNamespace(wall_time_seconds=12.0),
        artifacts=SimpleNamespace(root=tmp_path / "runtime_case"),
    )

    monkeypatch.setattr("qcchem.workflow.benchmark.load_run_spec", lambda path: object())
    monkeypatch.setattr("qcchem.workflow.benchmark.run_spec", lambda spec, source_config, output_dir: fake_result)

    case_result = _run_case(case, tmp_path / "runtime_case")

    assert case_result.metrics["runtime_evidence_status"] == "retrieved_result"
    assert case_result.metrics["runtime_submission_status"] == "succeeded"
