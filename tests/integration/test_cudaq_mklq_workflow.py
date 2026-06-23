from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config


def _available_cudaq_targets() -> set[str]:
    cudaq = pytest.importorskip("cudaq")
    get_targets = getattr(cudaq, "get_targets", None)
    if not callable(get_targets):
        return set()
    targets = set()
    for target in get_targets():
        name = getattr(target, "name", target)
        if callable(name):
            name = name()
        targets.add(str(name))
    return targets


def _require_cudaq_target(target: str) -> None:
    targets = _available_cudaq_targets()
    if target not in targets:
        pytest.skip(f"CUDA-Q target {target!r} is not available; available targets: {sorted(targets)}")


@pytest.mark.integration
def test_h2_mklq_cpu_statevector_matches_qiskit_statevector(tmp_path: Path) -> None:
    _require_cudaq_target("mklq-cpu")

    cudaq_result = run_from_config(
        Path("configs/h2_cudaq_mklq_cpu.yaml"),
        output_dir=tmp_path / "h2-cudaq-mklq-cpu",
    )
    qiskit_result = run_from_config(Path("configs/h2.yaml"), output_dir=tmp_path / "h2-qiskit")

    assert cudaq_result.backend.kind == "cudaq_statevector"
    assert cudaq_result.hardware_verified is False
    assert cudaq_result.backend.metadata["provider"] == "cudaq"
    assert cudaq_result.backend.metadata["cudaq_target"] == "mklq-cpu"
    assert cudaq_result.backend.metadata["target_evidence_tier"] == "mklq_cpu_stable_local_simulator"
    assert cudaq_result.backend.metadata["hardware_verified"] is False
    assert abs(cudaq_result.energy.solver_energy - qiskit_result.energy.solver_energy) < 1.0e-8


@pytest.mark.integration
def test_h2_mklq_cpu_sample_writes_sampling_artifacts_without_hardware_verification(tmp_path: Path) -> None:
    _require_cudaq_target("mklq-cpu")

    result = run_from_config(
        Path("configs/h2_cudaq_mklq_sample.yaml"),
        output_dir=tmp_path / "h2-cudaq-mklq-sample",
    )

    assert result.backend.kind == "cudaq_sample"
    assert result.sampled_result is not None
    assert result.sampled_result.shots == 4096
    assert result.sampled_result.backend_kind == "cudaq_sample"
    assert result.hardware_verified is False
    assert result.backend.metadata["cudaq_target"] == "mklq-cpu"
    assert result.backend.metadata["hardware_verified"] is False
    assert result.artifacts.report_markdown.exists()
    assert result.artifacts.quantum_evidence_json is not None
    assert result.artifacts.quantum_evidence_json.exists()

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["backend"]["metadata"]["provider"] == "cudaq"
    assert payload["backend"]["metadata"]["cudaq_target"] == "mklq-cpu"
    assert payload["hardware_verified"] is False


@pytest.mark.integration
def test_h2_mklq_metal_smoke_records_experimental_evidence_boundary(tmp_path: Path) -> None:
    _require_cudaq_target("mklq-metal")

    result = run_from_config(
        Path("configs/h2_cudaq_mklq_metal_smoke.yaml"),
        output_dir=tmp_path / "h2-cudaq-mklq-metal-smoke",
    )

    assert result.backend.kind == "cudaq_statevector"
    assert result.hardware_verified is False
    assert result.backend.metadata["cudaq_target"] == "mklq-metal"
    assert result.backend.metadata["target_evidence_tier"] == "mklq_metal_experimental_mixed_path"
    assert result.backend.metadata["mklq_metal_experimental"] is True
    assert result.backend.metadata["metal_full_native"] is False
    assert result.backend.metadata["hardware_verified"] is False
