import json
import types
from pathlib import Path
from types import SimpleNamespace

import h5py
import numpy as np
import pytest

from qcchem.backends.runtime_submission import attempt_runtime_submission
from qcchem.core import BackendSpec, BenchmarkCaseSpec, RuntimeOptionsSpec
from qcchem.core.results import CalibrationSummary, RunResult
from qcchem.core.results import BenchmarkSummary, MeasurementSummary, SampledResultSummary
from qcchem.io.exports import build_qcschema_payload, write_hdf5_result
from qcchem.reporting import write_result_json
from qcchem.workflow.calibration import build_calibration_summary
from qcchem.workflow.benchmark import _run_case


def test_run_result_exposes_hardware_evidence_fields() -> None:
    assert "hardware_verified" in RunResult.__dataclass_fields__
    assert "hardware_evidence_tier" in RunResult.__dataclass_fields__
    assert "runtime_chemical_accuracy" in RunResult.__dataclass_fields__


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


def test_write_result_json_handles_nested_numpy_runtime_payloads(tmp_path: Path) -> None:
    output_path = tmp_path / "runtime_payload.json"
    payload = {
        "runtime_submission": {
            "attempted": True,
            "returned_job_metadata": {
                "evs": np.array([-1.234], dtype=float),
                "stds": np.array([0.012], dtype=float),
                "metadata": {
                    "shots": np.int64(4096),
                    "zne_curve": np.array([1.0, 0.95, 0.93], dtype=float),
                },
            },
            "job_metrics": {
                "timestamps": {
                    "queue_segments": np.array([1, 2, 3], dtype=int),
                }
            },
        }
    }

    write_result_json(payload, output_path)

    decoded = json.loads(output_path.read_text(encoding="utf-8"))
    assert decoded["runtime_submission"]["returned_job_metadata"]["evs"] == [-1.234]
    assert decoded["runtime_submission"]["returned_job_metadata"]["metadata"]["shots"] == 4096
    assert decoded["runtime_submission"]["returned_job_metadata"]["metadata"]["zne_curve"] == [1.0, 0.95, 0.93]
    assert decoded["runtime_submission"]["job_metrics"]["timestamps"]["queue_segments"] == [1, 2, 3]


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


def test_runtime_submission_callback_runs_immediately_after_job_submit(monkeypatch) -> None:
    fake_runtime_module = types.ModuleType("qiskit_ibm_runtime")
    fake_runtime_module.__version__ = "test-version"

    class _FakeBackend:
        def __init__(self) -> None:
            self.name = "fake_backend"
            self.num_qubits = 2

    class _FakeService:
        def backend(self, name: str):
            assert name == "fake_backend"
            return _FakeBackend()

    class _FakeJob:
        def job_id(self) -> str:
            return "job-submitted"

    class _FakeEstimator:
        def __init__(self, mode=None, options=None) -> None:
            self.mode = mode
            self.options = options

        def run(self, pubs, **run_kwargs):
            return _FakeJob()

    fake_runtime_module.QiskitRuntimeService = _FakeService
    fake_runtime_module.Batch = object
    fake_runtime_module.Session = object
    fake_runtime_module.EstimatorV2 = _FakeEstimator
    monkeypatch.setitem(__import__("sys").modules, "qiskit_ibm_runtime", fake_runtime_module)

    class _FakePassManager:
        def run(self, circuit):
            class _FakeCircuit:
                layout = "fake-layout"

                def count_ops(self):
                    return {"cz": 3}

                def depth(self):
                    return 9

                @property
                def num_parameters(self):
                    return 0

            return _FakeCircuit()

    monkeypatch.setattr("qcchem.backends.runtime_submission.generate_preset_pass_manager", lambda **kwargs: _FakePassManager())

    submitted_summaries = []

    summary = attempt_runtime_submission(
        spec=BackendSpec(
            runtime=RuntimeOptionsSpec(
                enabled=True,
                service="ibm_runtime",
                runtime_ready=True,
                session_ready=False,
                batch_ready=False,
                precision_target=0.05,
                options={
                    "backend_name": "fake_backend",
                    "submit_real_job": True,
                    "wait_for_result": False,
                },
            )
        ),
        circuit=SimpleNamespace(num_qubits=2, num_parameters=0),
        operator=SimpleNamespace(num_qubits=2, apply_layout=lambda layout: SimpleNamespace(num_qubits=2)),
        parameter_values=[],
        submission_callback=lambda runtime_summary: submitted_summaries.append(runtime_summary.job_id),
    )

    assert summary is not None
    assert summary.submitted is True
    assert summary.succeeded is False
    assert summary.job_id == "job-submitted"
    assert summary.transpiled_depth == 9
    assert summary.transpiled_two_qubit_gate_count == 3
    assert submitted_summaries == ["job-submitted"]


def test_runtime_submission_merges_custom_estimator_options(monkeypatch) -> None:
    fake_runtime_module = types.ModuleType("qiskit_ibm_runtime")
    fake_runtime_module.__version__ = "test-version"
    captured = {}

    class _FakeBackend:
        def __init__(self) -> None:
            self.name = "fake_backend"
            self.num_qubits = 2

    class _FakeService:
        def backend(self, name: str):
            assert name == "fake_backend"
            return _FakeBackend()

    class _FakeJob:
        def job_id(self) -> str:
            return "job-options"

    class _FakeEstimator:
        def __init__(self, mode=None, options=None) -> None:
            captured["options"] = options

        def run(self, pubs, **run_kwargs):
            return _FakeJob()

    fake_runtime_module.QiskitRuntimeService = _FakeService
    fake_runtime_module.Batch = object
    fake_runtime_module.Session = object
    fake_runtime_module.EstimatorV2 = _FakeEstimator
    monkeypatch.setitem(__import__("sys").modules, "qiskit_ibm_runtime", fake_runtime_module)

    class _FakePassManager:
        def run(self, circuit):
            class _FakeCircuit:
                layout = "fake-layout"

                def count_ops(self):
                    return {"cz": 1}

                def depth(self):
                    return 4

                @property
                def num_parameters(self):
                    return 0

            return _FakeCircuit()

    monkeypatch.setattr("qcchem.backends.runtime_submission.generate_preset_pass_manager", lambda **kwargs: _FakePassManager())

    summary = attempt_runtime_submission(
        spec=BackendSpec(
            runtime=RuntimeOptionsSpec(
                enabled=True,
                service="ibm_runtime",
                runtime_ready=True,
                precision_target=0.02,
                resilience_level=1,
                options={
                    "backend_name": "fake_backend",
                    "submit_real_job": True,
                    "wait_for_result": False,
                    "estimator_options": {
                        "dynamical_decoupling": {
                            "enable": True,
                            "sequence_type": "XX",
                        },
                        "twirling": {
                            "enable_gates": True,
                            "enable_measure": True,
                        },
                        "resilience": {
                            "measure_mitigation": True,
                        },
                    },
                },
            )
        ),
        circuit=SimpleNamespace(num_qubits=2, num_parameters=0),
        operator=SimpleNamespace(num_qubits=2, apply_layout=lambda layout: SimpleNamespace(num_qubits=2)),
        parameter_values=[],
    )

    assert summary is not None
    assert summary.submitted is True
    assert captured["options"]["resilience_level"] == 1
    assert captured["options"]["dynamical_decoupling"]["enable"] is True
    assert captured["options"]["dynamical_decoupling"]["sequence_type"] == "XX"
    assert captured["options"]["twirling"]["enable_gates"] is True
    assert captured["options"]["resilience"]["measure_mitigation"] is True


def test_runtime_submission_auto_selects_lowest_layout_error_backend(monkeypatch) -> None:
    fake_runtime_module = types.ModuleType("qiskit_ibm_runtime")
    fake_runtime_module.__version__ = "test-version"
    captured = {}

    class _FakeCouplingMap:
        def __init__(self, edges):
            self._edges = edges

        def get_edges(self):
            return list(self._edges)

    class _FakeProperties:
        def __init__(self, readout_error: float, gate_error: float) -> None:
            self._readout_error = readout_error
            self._gate_error = gate_error

        def readout_error(self, index: int) -> float:
            return self._readout_error

        def gate_error(self, gate: str, qargs: list[int]) -> float:
            return self._gate_error

    class _FakeBackend:
        def __init__(self, name: str, readout_error: float, gate_error: float) -> None:
            self.name = name
            self.num_qubits = 2
            self.coupling_map = _FakeCouplingMap([(0, 1)])
            self._properties = _FakeProperties(readout_error, gate_error)

        def properties(self):
            return self._properties

    worse = _FakeBackend("worse_backend", 0.1, 0.2)
    better = _FakeBackend("better_backend", 0.001, 0.002)

    class _FakeService:
        def backends(self, **kwargs):
            return [worse, better]

        def backend(self, name: str):
            captured["backend_name"] = name
            return better if name == "better_backend" else worse

    class _FakeJob:
        def job_id(self) -> str:
            return "job-auto-backend"

    class _FakeEstimator:
        def __init__(self, mode=None, options=None) -> None:
            self.mode = mode
            self.options = options

        def run(self, pubs, **run_kwargs):
            return _FakeJob()

    fake_runtime_module.QiskitRuntimeService = _FakeService
    fake_runtime_module.Batch = object
    fake_runtime_module.Session = object
    fake_runtime_module.EstimatorV2 = _FakeEstimator
    monkeypatch.setitem(__import__("sys").modules, "qiskit_ibm_runtime", fake_runtime_module)

    class _FakePassManager:
        def run(self, circuit):
            class _FakeCircuit:
                layout = "fake-layout"

                def count_ops(self):
                    return {"cz": 1}

                def depth(self):
                    return 4

                @property
                def num_parameters(self):
                    return 0

            return _FakeCircuit()

    monkeypatch.setattr("qcchem.backends.runtime_submission.generate_preset_pass_manager", lambda **kwargs: _FakePassManager())

    summary = attempt_runtime_submission(
        spec=BackendSpec(
            runtime=RuntimeOptionsSpec(
                enabled=True,
                service="ibm_runtime",
                runtime_ready=True,
                precision_target=0.02,
                options={
                    "submit_real_job": True,
                    "wait_for_result": False,
                    "layout_strategy": "min_weighted_error",
                },
            )
        ),
        circuit=SimpleNamespace(num_qubits=2, num_parameters=0),
        operator=SimpleNamespace(num_qubits=2, apply_layout=lambda layout: SimpleNamespace(num_qubits=2)),
        parameter_values=[],
    )

    assert summary is not None
    assert summary.backend_name == "better_backend"
    assert captured["backend_name"] == "better_backend"
    assert summary.result_provenance["backend_selection_strategy"] == "min_weighted_error"


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
