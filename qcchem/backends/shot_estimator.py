"""Shot-based backend using a local statevector Pauli sampler."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from qcchem.backends.base import BackendAdapter, BackendEstimate
from qcchem.circuit_utils import statevector_ready_circuit
from qcchem.core import BackendSpec


def _positive_int_option(options: dict[str, Any], name: str, default: int | None) -> int | None:
    """Return a positive Aer integer option with a conservative default."""
    raw = options.get(name, default)
    if raw is None:
        return None
    value = int(raw)
    if value < 1:
        raise ValueError(f"backend.runtime.options.{name} must be positive when provided.")
    return value


@dataclass(frozen=True)
class _LocalSamplerOptions:
    max_parallel_threads: int | None = 1
    max_parallel_experiments: int | None = 1
    max_parallel_shots: int | None = 1


@dataclass(frozen=True)
class _LocalSamplerBackend:
    options: _LocalSamplerOptions
    engine: str = "statevector_pauli_sampler"
    native_aer: bool = False


def _pauli_weight(label: str) -> int:
    return sum(1 for char in label if char != "I")


def _noise_attenuation(label: str, spec: BackendSpec) -> float:
    if not spec.noise.enabled:
        return 1.0
    weight = _pauli_weight(label)
    readout_factor = (1.0 - 2.0 * spec.noise.readout_error_probability) ** weight
    one_qubit_factor = (1.0 - (4.0 * spec.noise.depolarizing_probability_1q / 3.0)) ** weight
    two_qubit_factor = (1.0 - (16.0 * spec.noise.depolarizing_probability_2q / 15.0)) ** max(weight - 1, 0)
    return float(readout_factor * one_qubit_factor * two_qubit_factor)


class ShotEstimatorBackend(BackendAdapter):
    """Shot-based estimator backend backed by Python-side Pauli sampling."""

    backend_kind = "shot_estimator"

    def __init__(self, spec: BackendSpec) -> None:
        if spec.shots is None:
            raise ValueError("shot_estimator backend requires 'shots' to be configured.")
        self.spec = spec
        runtime_options = dict(spec.runtime.options or {})
        sampler_options: dict[str, int | None] = {}
        for option_name in (
            "max_parallel_threads",
            "max_parallel_experiments",
            "max_parallel_shots",
        ):
            option_value = _positive_int_option(runtime_options, option_name, 1)
            sampler_options[option_name] = option_value
        self._backend = _LocalSamplerBackend(options=_LocalSamplerOptions(**sampler_options))
        self._evaluation_counter = 0
        self._sampling_offset = 100_000

    @property
    def precision(self) -> float:
        return 1.0 / math.sqrt(float(self.spec.shots))

    def _single_estimate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
        *,
        seed: int | None,
    ) -> BackendEstimate:
        bound_circuit = statevector_ready_circuit(circuit, parameter_values)
        state = Statevector.from_instruction(bound_circuit)
        rng = np.random.default_rng(seed)
        shots = int(self.spec.shots)
        estimate = 0.0
        variance = 0.0
        term_count = 0
        labels = operator.paulis.to_labels()
        for label, coeff in zip(labels, operator.coeffs, strict=True):
            term_count += 1
            coeff_real = float(np.real(coeff))
            pauli = SparsePauliOp.from_list([(label, 1.0)])
            exact_expectation = float(np.real(state.expectation_value(pauli)))
            attenuation = _noise_attenuation(label, self.spec)
            effective_expectation = float(np.clip(exact_expectation * attenuation, -1.0, 1.0))
            probability_one = float(np.clip((1.0 + effective_expectation) / 2.0, 0.0, 1.0))
            sampled_ones = int(rng.binomial(shots, probability_one))
            sampled_expectation = float((2.0 * sampled_ones / shots) - 1.0)
            estimate += coeff_real * sampled_expectation
            variance += (coeff_real**2) * max(1.0 - effective_expectation**2, 0.0) / shots
        reported_std = float(math.sqrt(max(variance, 0.0)))
        metadata: dict[str, Any] = {
            "shots": shots,
            "sampling_engine": self._backend.engine,
            "native_aer": self._backend.native_aer,
            "term_count": term_count,
            "sampling_variance": float(variance),
        }
        metadata.setdefault("shots", self.spec.shots)
        metadata["precision"] = self.precision
        metadata["abelian_grouping"] = self.spec.abelian_grouping
        metadata["noise_enabled"] = bool(self.spec.noise.enabled)
        metadata["noise_profile"] = self.spec.noise.profile
        metadata["noise_application"] = "pauli_expectation_attenuation" if self.spec.noise.enabled else "none"
        metadata["runtime_service"] = self.spec.runtime.service
        metadata["aer_max_parallel_threads"] = self._backend.options.max_parallel_threads
        metadata["aer_max_parallel_experiments"] = self._backend.options.max_parallel_experiments
        metadata["aer_max_parallel_shots"] = self._backend.options.max_parallel_shots
        return BackendEstimate(
            value=float(estimate),
            reported_std=reported_std,
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
