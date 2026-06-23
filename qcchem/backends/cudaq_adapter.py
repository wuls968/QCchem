"""Optional CUDA-Q backend adapter for local simulator targets."""

from __future__ import annotations

import importlib
import importlib.metadata
import math
import sys
import threading
from typing import Any

import numpy as np
from qiskit import transpile
from qiskit.circuit import QuantumCircuit
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
    "r1",
    "p",
    "phase",
    "u",
    "u1",
    "u2",
    "u3",
    "cx",
    "cy",
    "cz",
    "ch",
    "swap",
    "cs",
    "ct",
    "csdg",
    "ctdg",
    "rxx",
    "rzz",
    "ccx",
    "mcx",
    "crx",
    "cry",
    "crz",
    "cp",
    "cu1",
    "cphase",
    "cu3",
]
_UNSUPPORTED_OPERATION_NAMES = {
    "measure",
    "reset",
    "delay",
    "if_else",
    "for_loop",
    "while_loop",
    "switch_case",
}


def _load_cudaq():
    try:
        return importlib.import_module("cudaq")
    except (ModuleNotFoundError, ImportError) as exc:
        python_note = ""
        if sys.version_info < (3, 11):
            python_note = " CUDA-Q wheels require Python 3.11 or newer for QCchem's cudaq extra."
        raise RuntimeError(
            "CUDA-Q/MKL-Q backend requested but the 'cudaq' Python package is not installed "
            "or is incompatible with this interpreter. Install upstream CUDA-Q with "
            "`python -m pip install -e \".[cudaq]\"`, or run with a CUDA-Q/MKL-Q source prefix "
            "on the matching Python ABI, for example "
            "`PYTHONPATH=/Users/a0000/.cudaq-mklq /opt/anaconda3/bin/python3 -m qcchem.cli.main ...`."
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


def _reject_unsupported_operations(circuit: QuantumCircuit) -> None:
    for instruction in circuit.data:
        operation = instruction.operation
        name = operation.name.lower()
        if name in _UNSUPPORTED_OPERATION_NAMES:
            raise ValueError(
                f"CUDA-Q backend does not support Qiskit operation '{name}'. "
                "Remove measurements/control-flow operations or use the statevector/shot_estimator backend."
            )


def _prepare_supported_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    _reject_unsupported_operations(circuit)
    try:
        prepared = transpile(circuit, basis_gates=_BASIS_GATES, optimization_level=0)
    except Exception:
        prepared = circuit.decompose(reps=8)
    if prepared.num_parameters:
        names = ", ".join(str(parameter) for parameter in prepared.parameters)
        raise ValueError(f"CUDA-Q backend requires fully bound circuits; unbound parameters remain: {names}")
    _reject_unsupported_operations(prepared)
    return prepared


def _qiskit_circuit_to_cudaq_kernel(cudaq: Any, circuit: QuantumCircuit):
    contrib = getattr(cudaq, "contrib", None)
    converter = getattr(contrib, "from_qiskit", None)
    if not callable(converter):
        try:
            contrib_module = importlib.import_module("cudaq.contrib")
        except (ModuleNotFoundError, ImportError) as exc:
            raise RuntimeError(
                "CUDA-Q backend requires cudaq.contrib.from_qiskit to convert Qiskit circuits."
            ) from exc
        converter = getattr(contrib_module, "from_qiskit", None)
    if not callable(converter):
        raise RuntimeError("CUDA-Q backend requires cudaq.contrib.from_qiskit to convert Qiskit circuits.")
    return converter(circuit)


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


def _target_names(cudaq: Any) -> list[str]:
    get_targets = getattr(cudaq, "get_targets", None)
    if not callable(get_targets):
        return []
    try:
        targets = get_targets()
    except Exception:
        return []
    names: list[str] = []
    for target in targets:
        name = getattr(target, "name", target)
        if callable(name):
            name = name()
        if name is not None:
            names.append(str(name))
    return names


def _target_evidence_tier(target: str) -> str:
    if target == "mklq-cpu":
        return "mklq_cpu_stable_local_simulator"
    if target == "mklq-metal":
        return "mklq_metal_experimental_mixed_path"
    if target == "qpp-cpu":
        return "cudaq_qpp_cpu_local_simulator"
    if target == "nvidia":
        return "cudaq_nvidia_target"
    return "cudaq_local_target"


def _target_boundary(target: str) -> str:
    if target == "mklq-cpu":
        return "MKL-Q CPU-compatible local simulator target; not hardware execution."
    if target == "mklq-metal":
        return (
            "Experimental MKL-Q mixed Metal/CPU local target; records smoke evidence only, "
            "not full native Metal or hardware-verified execution."
        )
    if target == "qpp-cpu":
        return "CUDA-Q qpp CPU local simulator target; not hardware execution."
    if target == "nvidia":
        return "CUDA-Q NVIDIA target request; hardware verification requires retrieved runtime/QPU evidence."
    return "CUDA-Q target request; evidence tier depends on local target implementation."


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
    """Backend adapter powered by CUDA-Q-compatible local simulator targets."""

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
        self.target = str(options.get("target", "mklq-cpu"))
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
            "backend_kind": self.backend_kind,
            "cudaq_target": self.target,
            "cudaq_target_option": self.target_option,
            "target_evidence_tier": _target_evidence_tier(self.target),
            "target_boundary": _target_boundary(self.target),
            "hardware_verified": False,
        }
        self.provenance: dict[str, object] = {
            "adapter": "qcchem.backends.cudaq_adapter.CudaQBackend",
            "integration": "optional_cudaq_python_api",
            "qiskit_to_cudaq_converter": "cudaq.contrib.from_qiskit",
            "target_requested": self.target,
        }

    @property
    def _shots_count(self) -> int:
        return int(self.spec.shots) if self.sample_based else -1

    def _target_kwargs(self) -> dict[str, object]:
        if self.target_option is None or self.target_option == "":
            return {}
        return {"option": self.target_option}

    def _validate_target(self, cudaq: Any) -> tuple[int | None, list[str], bool | None]:
        available_targets = _target_names(cudaq)
        target_available = self.target in available_targets if available_targets else None
        if available_targets and not target_available:
            raise RuntimeError(
                f"CUDA-Q target '{self.target}' is not available. "
                f"Available targets: {', '.join(available_targets)}."
            )
        gpu_count = None
        num_available_gpus = getattr(cudaq, "num_available_gpus", None)
        if callable(num_available_gpus):
            gpu_count = int(num_available_gpus())
        if self.fail_if_no_gpu and self.target == "nvidia" and (gpu_count is None or gpu_count < 1):
            raise RuntimeError(
                "CUDA-Q target 'nvidia' was requested with fail_if_no_gpu=true, "
                "but CUDA-Q did not report any available NVIDIA GPUs."
            )
        return gpu_count, available_targets, target_available

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
        gpu_count, available_targets, target_available = self._validate_target(cudaq)

        with _TARGET_LOCK:
            set_random_seed = getattr(cudaq, "set_random_seed", None)
            if seed is not None and callable(set_random_seed):
                set_random_seed(int(seed))
            try:
                cudaq.set_target(self.target, **self._target_kwargs())
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
                clear_registries = getattr(cudaq, "__clearKernelRegistries", None)
                if callable(clear_registries):
                    clear_registries()

        module_file = getattr(cudaq, "__file__", None)
        metadata: dict[str, object] = {
            "provider": "cudaq",
            "backend_kind": self.backend_kind,
            "cudaq_version": _cudaq_version(cudaq),
            "cudaq_module_file": str(module_file) if module_file is not None else None,
            "cudaq_target": self.target,
            "cudaq_target_option": self.target_option,
            "cudaq_target_available": target_available,
            "cudaq_available_targets": available_targets,
            "num_available_gpus": gpu_count,
            "shots_count": self._shots_count,
            "qpu_id": self.qpu_id,
            "term_count": len(operator),
            "translated_gate_counts": dict(bound_circuit.count_ops()),
            "runtime_service": self.spec.runtime.service,
            "simulator_evidence": True,
            "hardware_verified": False,
            "target_evidence_tier": _target_evidence_tier(self.target),
            "target_boundary": _target_boundary(self.target),
            "mklq_target": self.target.startswith("mklq-"),
            "mklq_metal_experimental": self.target == "mklq-metal",
            "metal_full_native": False if self.target == "mklq-metal" else None,
        }
        provenance: dict[str, object] = {
            "adapter": "qcchem.backends.cudaq_adapter.CudaQBackend",
            "integration": "optional_cudaq_python_api",
            "module_file": metadata["cudaq_module_file"],
            "target_requested": self.target,
            "target_option_requested": self.target_option,
            "qiskit_to_cudaq_converter": "cudaq.contrib.from_qiskit",
        }
        self.metadata = metadata
        self.provenance = provenance
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
