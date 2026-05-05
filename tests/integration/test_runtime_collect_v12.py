from __future__ import annotations

import json
import types
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_result_json
from qcchem.workflow.runner import run_from_config
from qcchem.workflow.runtime_collect import collect_runtime_artifact

REPO_ROOT = Path(__file__).resolve().parents[2]


def _install_fake_runtime_module(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: str,
    evs: list[float] | None = None,
    stds: list[float] | None = None,
    shots: int = 4096,
) -> None:
    fake_runtime_module = types.ModuleType("qiskit_ibm_runtime")
    fake_runtime_module.__version__ = "test-version"

    class _FakeJob:
        usage_estimation = {"quantum_seconds": 12}

        def status(self):
            return status

        def result(self):
            assert evs is not None
            return [
                SimpleNamespace(
                    data=SimpleNamespace(
                        evs=np.asarray(evs, dtype=float),
                        stds=np.asarray(stds or [0.0], dtype=float),
                    ),
                    metadata={"shots": shots},
                )
            ]

        def metrics(self):
            return {"usage": {"seconds": 12, "quantum_seconds": 12}}

    class _FakeService:
        def job(self, job_id: str):
            assert job_id == "job-collect"
            return _FakeJob()

    fake_runtime_module.QiskitRuntimeService = _FakeService
    monkeypatch.setitem(__import__("sys").modules, "qiskit_ibm_runtime", fake_runtime_module)


@pytest.mark.integration
def test_collect_runtime_artifact_updates_result_and_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_collect",
    )
    payload = to_primitive(result)
    payload["runtime_submission"] = {
        "attempted": True,
        "submitted": True,
        "succeeded": False,
        "service": "ibm_quantum_platform",
        "mode": "backend",
        "session_requested": True,
        "batch_requested": False,
        "options_snapshot": {"precision_target": 0.02},
        "job_id": "job-collect",
        "backend_name": "ibm_kingston",
        "provider": "QiskitRuntimeService",
        "returned_job_metadata": {},
        "usage_estimation": {},
        "job_metrics": {},
        "result_provenance": {"attempt_stage": "submitted"},
        "verification_status": "exploratory",
    }
    payload["hardware_verified"] = False
    payload["hardware_evidence_tier"] = None
    payload["runtime_chemical_accuracy"] = None

    write_result_json(payload, result.artifacts.result_json)
    write_result_json(payload["runtime_submission"], result.artifacts.runtime_submission_json)

    exact_total = float(payload["exact_baseline"]["total_energy"])
    constant = float(payload["energy"]["constant_energy_correction"])
    nuclear = float(payload["energy"]["nuclear_repulsion_energy"])
    hardware_evs = [exact_total - constant - nuclear]
    _install_fake_runtime_module(monkeypatch, status="DONE", evs=hardware_evs, stds=[1.0e-4])

    summary = collect_runtime_artifact(result.artifacts.root)

    assert summary["status"] == "DONE"
    updated_payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert updated_payload["hardware_verified"] is True
    assert updated_payload["hardware_evidence_tier"] == "retrieved_result"
    assert updated_payload["runtime_submission"]["succeeded"] is True
    assert updated_payload["runtime_submission"]["returned_job_metadata"]["metadata"]["shots"] == 4096
    assert updated_payload["runtime_chemical_accuracy"]["available"] is True
    assert updated_payload["runtime_chemical_accuracy"]["meets_chemical_accuracy"] is True
    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "## Chemical Accuracy (Runtime-Derived)" in report_text
    assert "Meets chemical accuracy threshold." in report_text


@pytest.mark.integration
def test_collect_runtime_artifact_rebuilds_missing_result_from_resolved_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = run_from_config(
        REPO_ROOT / "configs" / "h2_exact.yaml",
        output_dir=tmp_path / "h2_collect_rebuild",
    )
    payload = to_primitive(result)
    runtime_submission = {
        "attempted": True,
        "submitted": True,
        "succeeded": False,
        "service": "ibm_quantum_platform",
        "mode": "backend",
        "session_requested": True,
        "batch_requested": False,
        "options_snapshot": {"precision_target": 0.02},
        "job_id": "job-collect",
        "backend_name": "ibm_kingston",
        "provider": "QiskitRuntimeService",
        "returned_job_metadata": {},
        "usage_estimation": {},
        "job_metrics": {},
        "result_provenance": {"attempt_stage": "submitted"},
        "verification_status": "exploratory",
    }
    write_result_json(runtime_submission, result.artifacts.runtime_submission_json)

    result.artifacts.result_json.unlink()
    result.artifacts.report_markdown.unlink()

    exact_total = float(payload["exact_baseline"]["total_energy"])
    constant = float(payload["energy"]["constant_energy_correction"])
    nuclear = float(payload["energy"]["nuclear_repulsion_energy"])
    hardware_evs = [exact_total - constant - nuclear + 5.0e-4]
    _install_fake_runtime_module(monkeypatch, status="DONE", evs=hardware_evs, stds=[2.0e-4])

    summary = collect_runtime_artifact(result.artifacts.root)

    assert summary["status"] == "DONE"
    assert result.artifacts.result_json.exists()
    assert result.artifacts.report_markdown.exists()
    rebuilt_payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert rebuilt_payload["run_id"] == "h2_collect_rebuild"
    assert rebuilt_payload["runtime_submission"]["job_id"] == "job-collect"
    assert rebuilt_payload["runtime_chemical_accuracy"]["available"] is True
    assert rebuilt_payload["runtime_chemical_accuracy"]["absolute_error_hartree"] == pytest.approx(5.0e-4)


@pytest.mark.integration
def test_collect_runtime_artifact_records_polled_status_for_queued_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_root = tmp_path / "queued_artifact"
    artifact_root.mkdir(parents=True)
    sidecar = {
        "attempted": True,
        "submitted": True,
        "succeeded": False,
        "service": "ibm_quantum_platform",
        "mode": "backend",
        "session_requested": True,
        "batch_requested": False,
        "options_snapshot": {"precision_target": 0.02},
        "job_id": "job-collect",
        "backend_name": "ibm_kingston",
        "provider": "QiskitRuntimeService",
        "returned_job_metadata": {},
        "usage_estimation": {},
        "job_metrics": {},
        "result_provenance": {"attempt_stage": "submitted"},
        "verification_status": "exploratory",
    }
    write_result_json(sidecar, artifact_root / "runtime_submission.json")

    _install_fake_runtime_module(monkeypatch, status="QUEUED")
    summary = collect_runtime_artifact(artifact_root)

    assert summary["status"] == "QUEUED"
    updated_sidecar = json.loads((artifact_root / "runtime_submission.json").read_text(encoding="utf-8"))
    assert updated_sidecar["submitted"] is True
    assert updated_sidecar["succeeded"] is False
    assert updated_sidecar["result_provenance"]["last_polled_status"] == "QUEUED"
    assert not (artifact_root / "result.json").exists()
