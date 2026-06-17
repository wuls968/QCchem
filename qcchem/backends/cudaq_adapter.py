"""CUDA-Q local simulator backend adapter."""

from __future__ import annotations

import importlib
import importlib.metadata
import math
import sys
import threading
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp

from qcchem.backends.base import BackendAdapter, BackendEstimate
from qcchem.core import BackendSpec


CUDAQ_BACKEND_KINDS = {"cudaq_statevector", "cudaq_sample"}
_TARGET_LOCK = threading.RLock()
_BASIS_GATES = [
    "id",
    "x",
    "y",
    "z",
    "h",
    "s",
    "sdg",
    "t",
    "tdg",
    "sx",
    "sxdg",
    "rx",
    "ry",
    "rz",
    "p",
    "u",
    "u3",
    "cx",
    "cz",
    "cy",
    "swap",
]
_UNSUPPORTED_CONTROL_FLOW = {"measure", "reset", "barrier", "delay"}


def _load_cudaq():
    try:
        return importlib.import_module("cudaq")
    except ModuleNotFoundError as exc:
        python_note = ""
        if sys.version_info < (3, 11):
            python_note = " CUDA-Q wheels require Python 3.11 or newer for QCchem's cudaq extra."
        raise RuntimeError(
            "CUDA-Q backend requested but the 'cudaq' package is not installed. "
            "Install it with `python -m pip install -e \".[cudaq]\"` in a Python 3.11+ environment."
            f"{python_note}"
        ) from exc


def _cudaq_version(cudaq: Any) -> str | None:
    version = getattr(cudaq, "__version__", None)
    if version is not None:
        return str(version)
    try:
        return importlib.metadata.version("cudaq")
    except importlib.metadata.PackageNotFoundError:
        return None


def _as_float(value: Any, *, gate_name: str) -> float:
    try:
        return float(value)
    except TypeError as exc:
        raise ValueError(
            f"CUDA-Q backend requires bound numeric parameters; gate '{gate_name}' still has {value!r}."
        ) from exc


def _bind_circuit(circuit: QuantumCircuit, parameter_values: np.ndarray) -> QuantumCircuit:
    values = np.asarray(parameter_values, dtype=float)
    if not circuit.num_parameters:
        return circuit
    if len(values) != circuit.num_parameters:
        raise ValueError(
            f"CUDA-Q backend received {len(values)} parameter values for "
            f"{circuit.num_parameters} circuit parameters."
        )
    return circuit.assign_parameters(dict(zip(circuit.parameters, values, strict=True)), inplace=False)


def _reject_unsupported_control_flow(circuit: QuantumCircuit) -> None:
    for instruction in circuit.data:
        name = instruction.operation.name.lower()
        if name in _UNSUPPORTED_CONTROL_FLOW:
            raise ValueError(
                f"CUDA-Q backend does not support Qiskit operation '{name}'. "
                "Remove measurements/control-flow operations or use the statevector/shot_estimator backend."
            )


def _prepare_supported_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    _reject_unsupported_control_flow(circuit)
    try:
        prepared = transpile(circuit, basis_gates=_BASIS_GATES, optimization_level=0)
    except Exception:
        prepared = circuit.decompose(reps=8)
    _reject_unsupported_control_flow(prepared)
    return prepared


def _qiskit_qubit_index(circuit: QuantumCircuit, qubit: Any) -> int:
    return int(circuit.find_bit(qubit).index)


def _call_gate(kernel: Any, names: tuple[str, ...], *args: Any) -> None:
    for name in names:
        method = getattr(kernel, name, None)
        if callable(method):
            method(*args)
            return
    raise ValueError(
        "CUDA-Q kernel builder does not expose any of these gate methods: "
        f"{', '.join(names)}."
    )


def _apply_single(kernel: Any, method: str, qubit: Any) -> None:
    _call_gate(kernel, (method,), qubit)


def _apply_phase_like(kernel: Any, angle: float, qubit: Any) -> None:
    _call_gate(kernel, ("p", "r1", "rz"), angle, qubit)


def _qiskit_circuit_to_cudaq_kernel(cudaq: Any, circuit: QuantumCircuit):
    kernel = cudaq.make_kernel()
    qreg = kernel.qalloc(circuit.num_qubits)

    for instruction in circuit.data:
        operation = instruction.operation
        name = operation.name.lower()
        qargs = instruction.qubits
        qubits = [qreg[_qiskit_qubit_index(circuit, qubit)] for qubit in qargs]
        params = [_as_float(param, gate_name=name) for param in operation.params]

        if name == "id":
            continue
        if name in {"x", "y", "z", "h"}:
            _apply_single(kernel, name, qubits[0])
        elif name == "s":
            _call_gate(kernel, ("s", "rz"), qubits[0]) if hasattr(kernel, "s") else _call_gate(kernel, ("rz",), math.pi / 2.0, qubits[0])
        elif name == "sdg":
            _call_gate(kernel, ("sdg",), qubits[0]) if hasattr(kernel, "sdg") else _call_gate(kernel, ("rz",), -math.pi / 2.0, qubits[0])
        elif name == "t":
            _call_gate(kernel, ("t",), qubits[0]) if hasattr(kernel, "t") else _call_gate(kernel, ("rz",), math.pi / 4.0, qubits[0])
        elif name == "tdg":
            _call_gate(kernel, ("tdg",), qubits[0]) if hasattr(kernel, "tdg") else _call_gate(kernel, ("rz",), -math.pi / 4.0, qubits[0])
        elif name == "sx":
            _call_gate(kernel, ("sx",), qubits[0]) if hasattr(kernel, "sx") else _call_gate(kernel, ("rx",), math.pi / 2.0, qubits[0])
        elif name == "sxdg":
            _call_gate(kernel, ("sxdg",), qubits[0]) if hasattr(kernel, "sxdg") else _call_gate(kernel, ("rx",), -math.pi / 2.0, qubits[0])
        elif name in {"rx", "ry", "rz"}:
            _call_gate(kernel, (name,), params[0], qubits[0])
        elif name == "p":
            _apply_phase_like(kernel, params[0], qubits[0])
        elif name in {"u", "u3"}:
            _call_gate(kernel, ("u3", "u"), params[0], params[1], params[2], qubits[0])
        elif name in {"cx", "cz", "cy", "swap"}:
            _call_gate(kernel, (name,), qubits[0], qubits[1])
        else:
            raise ValueError(
                f"CUDA-Q backend cannot translate Qiskit operation '{operation.name}'. "
                "Supported gates are x/y/z/h/s/sdg/t/tdg/sx/sxdg/rx/ry/rz/p/u/u3/cx/cz/cy/swap. "
                "Use statevector/shot_estimator for circuits requiring this operation."
            )
    return kernel


def _spin_factor(spin: Any, pauli: str, qubit_index: int):
    if pauli == "I":
        return spin.i(qubit_index)
    if pauli == "X":
        return spin.x(qubit_index)
    if pauli == "Y":
        return spin.y(qubit_index)
    if pauli == "Z":
        return spin.z(qubit_index)
    raise ValueError(f"Unsupported Pauli label character for CUDA-Q: {pauli!r}")


def _sparse_pauli_to_cudaq_spin(cudaq: Any, operator: SparsePauliOp):
    spin = cudaq.spin
    result = None
    for label, coeff in zip(operator.paulis.to_labels(), operator.coeffs, strict=True):
        coeff_complex = complex(coeff)
        if abs(coeff_complex.imag) > 1.0e-12:
            raise ValueError(
                "CUDA-Q backend only supports real-valued SparsePauliOp coefficients; "
                f"term {label} has coefficient {coeff_complex!r}."
            )
        coeff_real = float(coeff_complex.real)
        if abs(coeff_real) <= 1.0e-15:
            continue
        term = None
        for qubit_index, pauli in enumerate(reversed(label)):
            if pauli == "I":
                continue
            factor = _spin_factor(spin, pauli, qubit_index)
            term = factor if term is None else term * factor
        if term is None:
            term = spin.i(0)
        weighted = coeff_real * term
        result = weighted if result is None else result + weighted
    if result is None:
        return 0.0 * spin.i(0)
    return result


def _observe_expectation(observe_result: Any) -> float:
    expectation = getattr(observe_result, "expectation", None)
    if callable(expectation):
        return float(expectation())
    return float(expectation)


def _observe_std(observe_result: Any, *, shots: int | None) -> float:
    for name in ("standard_deviation", "std", "variance"):
        value = getattr(observe_result, name, None)
        if callable(value):
            value = value()
        if value is None:
            continue
        value = float(value)
        if name == "variance":
            value = math.sqrt(max(value, 0.0))
        return value
    if shots is not None and shots > 0:
        return 1.0 / math.sqrt(float(shots))
    return 0.0


class CudaQBackend(BackendAdapter):
    """Backend adapter powered by CUDA-Q local simulator targets."""

    backend_kind = "cudaq_statevector"

    def __init__(self, spec: BackendSpec) -> None:
        normalized = spec.kind.strip().lower()
        if normalized not in CUDAQ_BACKEND_KINDS:
            raise ValueError(f"Unsupported CUDA-Q backend kind: {spec.kind}")
        if normalized == "cudaq_sample" and spec.shots is None:
            raise ValueError("cudaq_sample backend requires 'shots' to be configured.")
        self.spec = spec
        self.backend_kind = normalized
        self.sample_based = normalized == "cudaq_sample"
        options = dict(spec.runtime.options or {})
        self.target = str(options.get("target", "qpp-cpu"))
        self.target_option = (
            str(options.get("target_option"))
            if options.get("target_option") is not None
            else None
        )
        self.fail_if_no_gpu = bool(options.get("fail_if_no_gpu", False))
        self.qpu_id = int(options.get("qpu_id", 0))
        self._evaluation_counter = 0
        self._sampling_offset = 100_000
        self.metadata: dict[str, object] = {
            "provider": "cudaq",
            "target": self.target,
            "target_option": self.target_option,
            "shots_count": self._shots_count,
            "qpu_id": self.qpu_id,
        }

    @property
    def _shots_count(self) -> int:
        return int(self.spec.shots) if self.sample_based else -1

    def _target_kwargs(self) -> dict[str, object]:
        if self.target_option is None or self.target_option == "":
            return {}
        return {"option": self.target_option}

    def _validate_target(self, cudaq: Any) -> int | None:
        gpu_count = None
        num_available_gpus = getattr(cudaq, "num_available_gpus", None)
        if callable(num_available_gpus):
            gpu_count = int(num_available_gpus())
        if self.fail_if_no_gpu and self.target == "nvidia" and (gpu_count is None or gpu_count < 1):
            raise RuntimeError(
                "CUDA-Q target 'nvidia' was requested with fail_if_no_gpu=true, "
                "but CUDA-Q did not report any available NVIDIA GPUs."
            )
        return gpu_count

    def _single_estimate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
        *,
        seed: int | None,
    ) -> BackendEstimate:
        cudaq = _load_cudaq()
        bound_circuit = _prepare_supported_circuit(_bind_circuit(circuit, parameter_values))
        cudaq_operator = _sparse_pauli_to_cudaq_spin(cudaq, operator)
        gpu_count = self._validate_target(cudaq)

        with _TARGET_LOCK:
            set_random_seed = getattr(cudaq, "set_random_seed", None)
            if seed is not None and callable(set_random_seed):
                set_random_seed(int(seed))
            cudaq.set_target(self.target, **self._target_kwargs())
            try:
                kernel = _qiskit_circuit_to_cudaq_kernel(cudaq, bound_circuit)
                observe_result = cudaq.observe(
                    kernel,
                    cudaq_operator,
                    shots_count=self._shots_count,
                    qpu_id=self.qpu_id,
                )
            finally:
                reset_target = getattr(cudaq, "reset_target", None)
                if callable(reset_target):
                    reset_target()

        metadata: dict[str, object] = {
            "provider": "cudaq",
            "backend_kind": self.backend_kind,
            "cudaq_version": _cudaq_version(cudaq),
            "cudaq_target": self.target,
            "cudaq_target_option": self.target_option,
            "cudaq_gpu_count": gpu_count,
            "shots_count": self._shots_count,
            "qpu_id": self.qpu_id,
            "term_count": len(operator),
            "translated_gate_counts": dict(bound_circuit.count_ops()),
            "runtime_service": self.spec.runtime.service,
            "simulator_evidence": True,
            "hardware_verified": False,
        }
        self.metadata = metadata
        shots = int(self.spec.shots) if self.sample_based and self.spec.shots is not None else None
        return BackendEstimate(
            value=float(_observe_expectation(observe_result)),
            reported_std=float(_observe_std(observe_result, shots=shots)),
            metadata=metadata,
            seed=seed,
            shots=shots,
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
        repeat_count = max(int(self.spec.repetitions), 1)
        estimates: list[BackendEstimate] = []
        for index in range(repeat_count):
            seed = None if self.spec.seed is None else self.spec.seed + self._sampling_offset + index
            estimates.append(self._single_estimate(circuit, operator, parameter_values, seed=seed))
        return estimates
