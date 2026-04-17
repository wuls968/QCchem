from __future__ import annotations

from pathlib import Path

from qcchem.io.config import load_run_spec


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_h2_hardware_probe_config_has_runtime_submission_enabled() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2_runtime_hardware_probe.yaml")
    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.service == "ibm_quantum_platform"
    assert spec.backend.runtime.batch_ready is False
    assert spec.problem.measurement.execution_mode == "runtime_estimator"
    assert spec.solver.kind == "vqe"
    assert spec.backend.runtime.options["backend_name"] == "ibm_marrakesh"
    assert spec.backend.runtime.options["submit_real_job"] is True


def test_lih_hardware_probe_v2_config_uses_compression() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "lih_active_runtime_hardware_probe_v2.yaml")
    assert spec.problem.compression.enabled is True
    assert spec.problem.measurement.strategy == "low_rank_commuting"
