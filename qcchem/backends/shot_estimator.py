"""Shot-based backend using BackendEstimatorV2 over AerSimulator."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from qiskit import transpile
from qiskit.circuit import QuantumCircuit
from qiskit.primitives import BackendEstimatorV2
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator

from qcchem.backends.base import BackendAdapter, BackendEstimate
from qcchem.backends.noise import build_local_noise_model, effective_basis_gates
from qcchem.core import BackendSpec


class ShotEstimatorBackend(BackendAdapter):
    """Shot-based estimator backend backed by AerSimulator."""

    backend_kind = "shot_estimator"

    def __init__(self, spec: BackendSpec) -> None:
        if spec.shots is None:
            raise ValueError("shot_estimator backend requires 'shots' to be configured.")
        self.spec = spec
        self._noise_model = build_local_noise_model(spec.noise)
        self._noise_basis_gates = effective_basis_gates(spec.noise)
        simulator_kwargs = {}
        if self._noise_model is not None:
            simulator_kwargs["noise_model"] = self._noise_model
        self._backend = AerSimulator(**simulator_kwargs)
        self._evaluation_counter = 0
        self._sampling_offset = 100_000
        self._transpiled_cache: dict[int, QuantumCircuit] = {}

    @property
    def precision(self) -> float:
        return 1.0 / math.sqrt(float(self.spec.shots))

    def _build_estimator(self, seed: int | None) -> BackendEstimatorV2:
        return BackendEstimatorV2(
            backend=self._backend,
            options={
                "default_precision": self.precision,
                "abelian_grouping": self.spec.abelian_grouping,
                "seed_simulator": seed,
            },
        )

    def _prepare_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        cache_key = id(circuit)
        prepared = self._transpiled_cache.get(cache_key)
        if prepared is None:
            if self._noise_basis_gates:
                transpile_kwargs: dict[str, object] = {
                    "basis_gates": self._noise_basis_gates,
                    "optimization_level": 0,
                }
            else:
                transpile_kwargs = {"backend": self._backend, "optimization_level": 0}
            prepared = transpile(circuit, **transpile_kwargs)
            self._transpiled_cache[cache_key] = prepared
        return prepared

    def _single_estimate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
        *,
        seed: int | None,
    ) -> BackendEstimate:
        estimator = self._build_estimator(seed)
        prepared_circuit = self._prepare_circuit(circuit)
        result = estimator.run(
            [(prepared_circuit, operator, [np.asarray(parameter_values, dtype=float)])]
        ).result()[0]
        metadata: dict[str, Any] = dict(result.metadata)
        metadata.setdefault("shots", self.spec.shots)
        metadata["precision"] = self.precision
        metadata["abelian_grouping"] = self.spec.abelian_grouping
        metadata["noise_enabled"] = bool(self.spec.noise.enabled)
        metadata["noise_profile"] = self.spec.noise.profile
        metadata["runtime_service"] = self.spec.runtime.service
        return BackendEstimate(
            value=float(np.real(result.data.evs[0])),
            reported_std=float(np.real(result.data.stds[0])),
            metadata=metadata,
            seed=seed,
            shots=int(metadata.get("shots", self.spec.shots)),
        )

    def evaluate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> BackendEstimate:
        seed = None if self.spec.seed is None else self.spec.seed + self._evaluation_counter
        self._evaluation_counter += 1
        return self._single_estimate(circuit, operator, parameter_values, seed=seed)

    def sample_repeated(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> list[BackendEstimate]:
        estimates: list[BackendEstimate] = []
        repeat_count = max(int(self.spec.repetitions), 1)
        for index in range(repeat_count):
            seed = None if self.spec.seed is None else self.spec.seed + self._sampling_offset + index
            estimates.append(
                self._single_estimate(circuit, operator, parameter_values, seed=seed)
            )
        return estimates
