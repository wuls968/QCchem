from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_h2_cudaq_statevector_matches_qiskit_statevector(tmp_path: Path) -> None:
    pytest.importorskip("cudaq")

    cudaq_result = run_from_config(
        Path("configs/h2_cudaq_statevector.yaml"),
        output_dir=tmp_path / "h2-cudaq-statevector",
    )
    qiskit_result = run_from_config(Path("configs/h2.yaml"), output_dir=tmp_path / "h2-qiskit")

    assert cudaq_result.backend.kind == "cudaq_statevector"
    assert cudaq_result.hardware_verified is False
    assert cudaq_result.backend.metadata["provider"] == "cudaq"
    assert abs(cudaq_result.energy.solver_energy - qiskit_result.energy.solver_energy) < 1.0e-8


@pytest.mark.integration
def test_h2_cudaq_sample_writes_sampling_artifacts_without_hardware_verification(tmp_path: Path) -> None:
    pytest.importorskip("cudaq")

    result = run_from_config(
        Path("configs/h2_cudaq_sample.yaml"),
        output_dir=tmp_path / "h2-cudaq-sample",
    )

    assert result.backend.kind == "cudaq_sample"
    assert result.sampled_result is not None
    assert result.sampled_result.shots == 4096
    assert result.sampled_result.backend_kind == "cudaq_sample"
    assert result.hardware_verified is False
    assert result.artifacts.report_markdown.exists()
    assert result.artifacts.quantum_evidence_json is not None
    assert result.artifacts.quantum_evidence_json.exists()

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["backend"]["metadata"]["provider"] == "cudaq"
    assert payload["hardware_verified"] is False
