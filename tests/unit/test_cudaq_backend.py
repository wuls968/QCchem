from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

import qcchem.backends.cudaq_adapter as cudaq_adapter
from qcchem.backends import build_backend
from qcchem.backends.capabilities import describe_backend_capabilities
from qcchem.backends.cudaq_adapter import (
    CudaQBackend,
    _prepare_supported_circuit,
    _qiskit_circuit_to_cudaq_kernel,
    _sparse_pauli_to_cudaq_spin,
)
from qcchem.core import BackendSpec, RuntimeOptionsSpec
from qcchem.io.config import load_run_spec


class _FakeSpinTerm:
    def __init__(self, terms):
        self.terms = list(terms)

    def __mul__(self, other):
        if isinstance(other, _FakeSpinTerm):
            terms = []
            for coeff, factors in self.terms:
                for other_coeff, other_factors in other.terms:
                    terms.append((coeff * other_coeff, factors + other_factors))
            return _FakeSpinTerm(terms)
        return _FakeSpinTerm([(coeff * float(other), factors) for coeff, factors in self.terms])

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other):
        return _FakeSpinTerm(self.terms + other.terms)


class _FakeSpin:
    @staticmethod
    def i(index):
        return _FakeSpinTerm([(1.0, (("I", int(index)),))])

    @staticmethod
    def x(index):
        return _FakeSpinTerm([(1.0, (("X", int(index)),))])

    @staticmethod
    def y(index):
        return _FakeSpinTerm([(1.0, (("Y", int(index)),))])

    @staticmethod
    def z(index):
        return _FakeSpinTerm([(1.0, (("Z", int(index)),))])


class _FakeKernel:
    def __init__(self):
        self.ops = []

    def qalloc(self, count):
        self.ops.append(("qalloc", int(count)))
        return [f"q{index}" for index in range(int(count))]

    def __getattr__(self, name):
        def _record(*args):
            self.ops.append((name, args))

        return _record


class _FakeObserveResult:
    def __init__(self, value=0.25):
        self._value = value

    def expectation(self):
        return self._value

    def standard_deviation(self):
        return 0.125


class _FakeCudaQ(types.ModuleType):
    def __init__(self):
        super().__init__("cudaq")
        self.__version__ = "fake-0.14"
        self.spin = _FakeSpin()
        self.kernels = []
        self.observe_calls = []
        self.target_calls = []
        self.reset_count = 0
        self.seed_calls = []
        self.gpu_count = 0

    def make_kernel(self):
        kernel = _FakeKernel()
        self.kernels.append(kernel)
        return kernel

    def set_target(self, target, **kwargs):
        self.target_calls.append((target, kwargs))

    def reset_target(self):
        self.reset_count += 1

    def set_random_seed(self, seed):
        self.seed_calls.append(seed)

    def num_available_gpus(self):
        return self.gpu_count

    def observe(self, kernel, operator, **kwargs):
        self.observe_calls.append({"kernel": kernel, "operator": operator, "kwargs": kwargs})
        return _FakeObserveResult()


def test_load_run_spec_parses_cudaq_backend_configs() -> None:
    statevector = load_run_spec(Path("configs/h2_cudaq_statevector.yaml"))
    sampled = load_run_spec(Path("configs/h2_cudaq_sample.yaml"))

    assert statevector.backend.kind == "cudaq_statevector"
    assert statevector.backend.runtime.options["target"] == "qpp-cpu"
    assert "target_option" not in statevector.backend.runtime.options
    assert sampled.backend.kind == "cudaq_sample"
    assert sampled.backend.shots == 4096
    assert sampled.backend.runtime.options["fail_if_no_gpu"] is False


def test_cudaq_capability_summary_marks_simulator_not_runtime() -> None:
    statevector = describe_backend_capabilities(BackendSpec(kind="cudaq_statevector"))
    sampled = describe_backend_capabilities(BackendSpec(kind="cudaq_sample", shots=1024))

    assert statevector.statevector is True
    assert statevector.shot_based is False
    assert statevector.runtime_ready is False
    assert sampled.statevector is False
    assert sampled.shot_based is True
    assert sampled.runtime_ready is False
    assert sampled.supports_confidence_metrics is True


def test_build_backend_accepts_cudaq_kinds() -> None:
    assert isinstance(build_backend(BackendSpec(kind="cudaq_statevector")), CudaQBackend)
    assert isinstance(build_backend(BackendSpec(kind="cudaq_sample", shots=100)), CudaQBackend)


def test_cudaq_sample_requires_shots() -> None:
    with pytest.raises(ValueError, match="requires 'shots'"):
        CudaQBackend(BackendSpec(kind="cudaq_sample"))


def test_missing_cudaq_dependency_has_actionable_error(monkeypatch) -> None:
    def _missing_cudaq(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(cudaq_adapter.importlib, "import_module", _missing_cudaq)

    backend = CudaQBackend(BackendSpec(kind="cudaq_statevector"))
    circuit = QuantumCircuit(1)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    with pytest.raises(RuntimeError, match="pip install -e"):
        backend.evaluate(circuit, operator, np.asarray([], dtype=float))


def test_sparse_pauli_to_cudaq_spin_preserves_qiskit_qubit_order() -> None:
    fake_cudaq = _FakeCudaQ()
    operator = SparsePauliOp.from_list(
        [
            ("IZ", 1.0),
            ("ZI", 2.0),
            ("XX", 3.0),
            ("YZ", 4.0),
        ]
    )

    spin_operator = _sparse_pauli_to_cudaq_spin(fake_cudaq, operator)

    assert spin_operator.terms == [
        (1.0, (("Z", 0),)),
        (2.0, (("Z", 1),)),
        (3.0, (("X", 0), ("X", 1))),
        (4.0, (("Z", 0), ("Y", 1))),
    ]


def test_cudaq_circuit_translator_accepts_supported_gate_subset() -> None:
    fake_cudaq = _FakeCudaQ()
    circuit = QuantumCircuit(2)
    circuit.x(0)
    circuit.y(0)
    circuit.z(0)
    circuit.h(0)
    circuit.s(0)
    circuit.sdg(0)
    circuit.t(0)
    circuit.tdg(0)
    circuit.sx(0)
    circuit.sxdg(0)
    circuit.rx(0.1, 0)
    circuit.ry(0.2, 0)
    circuit.rz(0.3, 0)
    circuit.p(0.4, 0)
    circuit.u(0.5, 0.6, 0.7, 0)
    circuit.cx(0, 1)
    circuit.cz(0, 1)
    circuit.cy(0, 1)
    circuit.swap(0, 1)

    prepared = _prepare_supported_circuit(circuit)
    kernel = _qiskit_circuit_to_cudaq_kernel(fake_cudaq, prepared)
    names = [item[0] for item in kernel.ops]

    assert "qalloc" in names
    assert "x" in names
    assert "y" in names
    assert "z" in names
    assert "h" in names
    assert "cx" in names
    assert "cz" in names
    assert "cy" in names
    assert "swap" in names


def test_cudaq_circuit_translator_rejects_measurements() -> None:
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)

    with pytest.raises(ValueError, match="measure"):
        _prepare_supported_circuit(circuit)


def test_cudaq_backend_sets_target_observe_and_resets(monkeypatch) -> None:
    fake_cudaq = _FakeCudaQ()
    monkeypatch.setitem(sys.modules, "cudaq", fake_cudaq)
    backend = CudaQBackend(
        BackendSpec(
            kind="cudaq_sample",
            shots=256,
            seed=11,
            repetitions=2,
            runtime=RuntimeOptionsSpec(
                service="cudaq_local",
                options={
                    "target": "nvidia",
                    "target_option": "fp64",
                    "qpu_id": 1,
                    "fail_if_no_gpu": False,
                },
            ),
        )
    )
    circuit = QuantumCircuit(1)
    circuit.h(0)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    estimate = backend.evaluate(circuit, operator, np.asarray([], dtype=float))

    assert estimate.value == 0.25
    assert estimate.reported_std == 0.125
    assert estimate.seed == 11
    assert estimate.shots == 256
    assert fake_cudaq.target_calls == [("nvidia", {"option": "fp64"})]
    assert fake_cudaq.observe_calls[0]["kwargs"]["shots_count"] == 256
    assert fake_cudaq.observe_calls[0]["kwargs"]["qpu_id"] == 1
    assert fake_cudaq.reset_count == 1
    assert backend.metadata["cudaq_target"] == "nvidia"
    assert backend.metadata["hardware_verified"] is False


def test_cudaq_backend_gpu_gate_can_fail_fast(monkeypatch) -> None:
    fake_cudaq = _FakeCudaQ()
    monkeypatch.setitem(sys.modules, "cudaq", fake_cudaq)
    backend = CudaQBackend(
        BackendSpec(
            kind="cudaq_statevector",
            runtime=RuntimeOptionsSpec(options={"target": "nvidia", "fail_if_no_gpu": True}),
        )
    )
    circuit = QuantumCircuit(1)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    with pytest.raises(RuntimeError, match="fail_if_no_gpu"):
        backend.evaluate(circuit, operator, np.asarray([], dtype=float))
