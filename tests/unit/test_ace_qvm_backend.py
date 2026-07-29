from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Gate, Parameter
from qiskit.quantum_info import SparsePauliOp, Statevector

from qcchem.backends import ACEQVMBackend, build_backend
from qcchem.backends.capabilities import describe_backend_capabilities
from qcchem.core import BackendSpec
from qcchem.io.config import load_run_spec


def _estimate(circuit: QuantumCircuit, operator: SparsePauliOp, spec: BackendSpec | None = None, values=None):
    backend = ACEQVMBackend(spec or BackendSpec(kind="ace_qvm"))
    return backend.evaluate(circuit, operator, np.asarray(values or [], dtype=float))


def _exact(circuit: QuantumCircuit, operator: SparsePauliOp) -> float:
    state = Statevector.from_instruction(circuit)
    return float(np.real(state.expectation_value(operator)))


def test_load_run_spec_parses_ace_qvm_backend_config() -> None:
    spec = load_run_spec(Path("configs/exploratory/h2_ace_qvm_lr_ace.yaml"))

    assert spec.backend.kind == "ace_qvm"
    assert spec.backend.ace_qvm.memory_budget_gib == 1
    assert spec.backend.ace_qvm.block_qubits == 2
    assert spec.backend.ace_qvm.max_bond_dim == 16
    assert spec.backend.ace_qvm.truncation_eps == pytest.approx(1.0e-10)
    assert spec.backend.ace_qvm.max_branch_rank == 8
    assert spec.backend.ace_qvm.cross_block_policy == "auto"
    assert spec.backend.ace_qvm.routing == "swap_network"
    assert spec.backend.ace_qvm.observable_mode == "pauli_expectation"
    assert spec.backend.ace_qvm.debug_dense_state_qubit_limit == 10
    assert spec.policy.allow_exploratory is True


def test_build_backend_and_capabilities_accept_ace_qvm() -> None:
    backend = build_backend(BackendSpec(kind="ace_qvm"))
    capability = describe_backend_capabilities(BackendSpec(kind="ace_qvm"))

    assert isinstance(backend, ACEQVMBackend)
    assert capability.backend_kind == "ace_qvm"
    assert capability.statevector is False
    assert capability.runtime_ready is False


def test_ace_qvm_bell_expectations_match_statevector() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    operator = SparsePauliOp.from_list([("ZZ", 0.5), ("XX", 0.5)])

    estimate = _estimate(circuit, operator)

    assert estimate.value == pytest.approx(_exact(circuit, operator), abs=1.0e-10)
    ledger = estimate.metadata["ace_qvm"]["ledger"]
    memory_report = estimate.metadata["ace_qvm"]["memory_report"]
    assert ledger["max_observed_bond_dim"] == 2
    assert ledger["capacity_status"] == "within_budget"
    assert memory_report["memory_budget_bytes"] > 0
    assert memory_report["max_observed_memory_bytes"] == ledger["max_observed_memory_bytes"]
    assert memory_report["within_memory_budget"] is True


def test_ace_qvm_non_adjacent_routing_matches_statevector() -> None:
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 2)
    circuit.cz(2, 1)
    operator = SparsePauliOp.from_list([("ZIZ", 1.0), ("XXX", 0.25)])

    estimate = _estimate(circuit, operator)

    assert estimate.value == pytest.approx(_exact(circuit, operator), abs=1.0e-10)
    ledger = estimate.metadata["ace_qvm"]["ledger"]
    assert ledger["routed_swap_count"] >= 2


def test_ace_qvm_parameterized_circuit_matches_statevector() -> None:
    theta = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.ry(theta, 0)
    circuit.cx(0, 1)
    operator = SparsePauliOp.from_list([("ZI", 0.7), ("IZ", -0.2), ("XX", 0.3)])
    value = [0.37]
    exact_circuit = circuit.assign_parameters({theta: value[0]}, inplace=False)

    estimate = _estimate(circuit, operator, values=value)

    assert estimate.value == pytest.approx(_exact(exact_circuit, operator), abs=1.0e-10)


def test_ace_qvm_operator_schmidt_cut_matches_statevector_when_branch_budget_suffices() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    operator = SparsePauliOp.from_list([("ZZ", 0.5), ("XX", 0.5)])
    spec = BackendSpec(kind="ace_qvm")
    spec.ace_qvm.block_qubits = 1
    spec.ace_qvm.cross_block_policy = "cut"
    spec.ace_qvm.max_branch_rank = 8

    estimate = _estimate(circuit, operator, spec)

    assert estimate.value == pytest.approx(_exact(circuit, operator), abs=1.0e-10)
    ledger = estimate.metadata["ace_qvm"]["ledger"]
    assert ledger["cut_gate_count"] == 1
    assert ledger["max_observed_branch_rank"] > 1


def test_ace_qvm_branch_truncation_is_recorded() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    operator = SparsePauliOp.from_list([("XX", 1.0)])
    spec = BackendSpec(kind="ace_qvm")
    spec.ace_qvm.block_qubits = 1
    spec.ace_qvm.cross_block_policy = "cut"
    spec.ace_qvm.max_branch_rank = 1

    estimate = _estimate(circuit, operator, spec)

    ledger = estimate.metadata["ace_qvm"]["ledger"]
    assert ledger["branch_prune_events"] >= 1
    assert ledger["capacity_status"] == "approximate_branch_truncated"
    assert ledger["total_pruned_branch_weight"] > 0.0


def test_ace_qvm_svd_truncation_is_recorded() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    operator = SparsePauliOp.from_list([("ZZ", 1.0)])
    spec = BackendSpec(kind="ace_qvm")
    spec.ace_qvm.block_qubits = 2
    spec.ace_qvm.max_bond_dim = 1
    spec.ace_qvm.truncation_eps = 0.0

    estimate = _estimate(circuit, operator, spec)

    ledger = estimate.metadata["ace_qvm"]["ledger"]
    assert ledger["svd_truncation_events"] >= 1
    assert ledger["capacity_status"] == "approximate_svd_truncated"
    assert ledger["total_discarded_svd_weight"] > 0.0


def test_ace_qvm_memory_budget_exceeded_raises_capacity_error() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    operator = SparsePauliOp.from_list([("ZI", 1.0)])
    spec = BackendSpec(kind="ace_qvm")
    spec.ace_qvm.memory_budget_gib = 1.0e-12

    with pytest.raises(RuntimeError, match="ace_qvm_capacity_exceeded"):
        _estimate(circuit, operator, spec)


def test_ace_qvm_rejects_measurements() -> None:
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    with pytest.raises(ValueError, match="measure"):
        _estimate(circuit, operator)


def test_ace_qvm_rejects_control_flow() -> None:
    circuit = QuantumCircuit(1, 1)
    with circuit.if_test((circuit.clbits[0], True)):
        circuit.x(0)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    with pytest.raises(ValueError, match="if_else"):
        _estimate(circuit, operator)


def test_ace_qvm_rejects_unsupported_three_qubit_gate() -> None:
    circuit = QuantumCircuit(3)
    circuit.append(Gate("opaque_three_qubit", 3, []), [0, 1, 2])
    operator = SparsePauliOp.from_list([("ZII", 1.0)])

    with pytest.raises(ValueError, match="one- and two-qubit operations"):
        _estimate(circuit, operator)
