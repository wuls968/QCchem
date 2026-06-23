from __future__ import annotations

from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
import yaml

from qcchem.backends.capabilities import describe_backend_capabilities
from qcchem.backends.policy import resolve_execution_policy
from qcchem.core import (
    BackendSpec,
    BenchmarkSpec,
    MitigationSpec,
    NoiseModelSpec,
    PolicySpec,
    RuntimeOptionsSpec,
)
from qcchem.backends.shot_estimator import ShotEstimatorBackend
from qcchem.io.config import load_run_spec


def test_load_run_spec_parses_noise_and_runtime_sections(tmp_path: Path) -> None:
    config = {
        "molecule": {
            "name": "H2-noisy-unit",
            "geometry": [
                {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                {"symbol": "H", "coords": [0.0, 0.0, 0.735]},
            ],
            "charge": 0,
            "multiplicity": 1,
            "basis": "sto3g",
        },
        "problem": {"active_space": None},
        "mapping": {"kind": "jordan_wigner"},
        "policy": {"name": "hardware_ready"},
        "backend": {
            "kind": "shot_estimator",
            "shots": 2048,
            "seed": 77,
            "repetitions": 3,
            "abelian_grouping": False,
            "noise": {
                "enabled": True,
                "profile": "depolarizing_readout",
                "depolarizing_probability_1q": 0.001,
                "depolarizing_probability_2q": 0.01,
                "readout_error_probability": 0.02,
            },
            "runtime": {
                "enabled": True,
                "service": "local_aer",
                "runtime_ready": True,
                "session_ready": True,
                "batch_ready": True,
                "options": {"optimization_level": 1, "resilience_level": 0},
            },
        },
        "solver": {
            "kind": "vqe",
            "optimizer": {"kind": "COBYLA", "maxiter": 5},
            "ansatz": {"kind": "uccsd", "reps": 1},
            "initial_point": "zeros",
        },
        "benchmark": {"enabled": True},
        "mitigation": {"symmetry_check": {"enabled": True}},
        "run": {"seed": 77, "output_dir": str(tmp_path / "artifacts"), "overwrite": True},
    }
    config_path = tmp_path / "noise_config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    spec = load_run_spec(config_path)

    assert spec.backend.noise is not None
    assert spec.backend.noise.enabled is True
    assert spec.backend.noise.profile == "depolarizing_readout"
    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.runtime_ready is True
    assert spec.backend.runtime.session_ready is True
    assert spec.backend.runtime.batch_ready is True
    assert spec.backend.runtime.options["optimization_level"] == 1


def test_backend_capabilities_include_noise_runtime_session_and_batch_flags() -> None:
    capabilities = describe_backend_capabilities(
        BackendSpec(
            kind="shot_estimator",
            shots=2048,
            noise=NoiseModelSpec(
                enabled=True,
                profile="depolarizing_readout",
                depolarizing_probability_1q=0.001,
                depolarizing_probability_2q=0.01,
                readout_error_probability=0.02,
            ),
            runtime=RuntimeOptionsSpec(
                enabled=True,
                service="ibm_runtime_placeholder",
                runtime_ready=True,
                session_ready=True,
                batch_ready=True,
                options={"resilience_level": 1},
            ),
        )
    )

    assert capabilities.noise_model_ready is True
    assert capabilities.runtime_ready is True
    assert capabilities.session_ready is True
    assert capabilities.batch_ready is True
    assert capabilities.supports_confidence_metrics is True


def test_shot_estimator_bounds_local_aer_parallelism_by_default() -> None:
    backend = ShotEstimatorBackend(BackendSpec(kind="shot_estimator", shots=1024))

    assert backend._backend.options.max_parallel_threads == 1
    assert backend._backend.options.max_parallel_experiments == 1
    assert backend._backend.options.max_parallel_shots == 1


def test_shot_estimator_accepts_runtime_parallel_overrides() -> None:
    backend = ShotEstimatorBackend(
        BackendSpec(
            kind="shot_estimator",
            shots=1024,
            runtime=RuntimeOptionsSpec(
                options={
                    "max_parallel_threads": 2,
                    "max_parallel_experiments": 1,
                    "max_parallel_shots": 1,
                }
            ),
        )
    )

    assert backend._backend.options.max_parallel_threads == 2
    assert backend._backend.options.max_parallel_experiments == 1
    assert backend._backend.options.max_parallel_shots == 1


def test_shot_estimator_uses_python_pauli_sampler_by_default() -> None:
    backend = ShotEstimatorBackend(BackendSpec(kind="shot_estimator", shots=16))
    circuit = QuantumCircuit(1)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    estimate = backend.evaluate(circuit, operator, np.asarray([], dtype=float))

    assert backend._backend.engine == "statevector_pauli_sampler"
    assert backend._backend.native_aer is False
    assert estimate.value == 1.0
    assert estimate.reported_std == 0.0
    assert estimate.metadata["sampling_engine"] == "statevector_pauli_sampler"
    assert estimate.metadata["native_aer"] is False


def test_hardware_ready_policy_exposes_runtime_and_session_expectations() -> None:
    summary = resolve_execution_policy(
        PolicySpec(name="hardware_ready"),
        BackendSpec(
            kind="shot_estimator",
            shots=4096,
            repetitions=5,
            noise=NoiseModelSpec(enabled=True),
            runtime=RuntimeOptionsSpec(
                enabled=True,
                runtime_ready=True,
                session_ready=True,
                batch_ready=True,
            ),
        ),
        BenchmarkSpec(),
        MitigationSpec(),
    )

    assert summary.runtime_ready_expected is True
    assert summary.session_ready_expected is True
    assert summary.batch_ready_expected is True
    assert summary.noise_ready_expected is True
