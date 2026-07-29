"""Exploratory ACE-QVM backend adapter."""

from __future__ import annotations

from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from qcchem.backends.ace_qvm_tn import (
    ACEQVMCapacityError,
    ACEQVMSettings,
    simulate_circuit_expectation,
)
from qcchem.backends.base import BackendAdapter, BackendEstimate
from qcchem.circuit_utils import bind_circuit_parameters
from qcchem.core import BackendSpec


_UNSUPPORTED_OPERATION_NAMES = {
    "measure",
    "reset",
    "delay",
    "barrier",
    "if_else",
    "for_loop",
    "while_loop",
    "switch_case",
}


def _settings_from_spec(spec: BackendSpec) -> ACEQVMSettings:
    ace = spec.ace_qvm
    return ACEQVMSettings(
        memory_budget_gib=float(ace.memory_budget_gib),
        block_qubits=int(ace.block_qubits),
        max_bond_dim=int(ace.max_bond_dim),
        truncation_eps=float(ace.truncation_eps),
        max_branch_rank=int(ace.max_branch_rank),
        cross_block_policy=str(ace.cross_block_policy).strip().lower(),
        routing=str(ace.routing).strip().lower(),
        observable_mode=str(ace.observable_mode).strip().lower(),
        debug_dense_state_qubit_limit=int(ace.debug_dense_state_qubit_limit),
    )


def _operation_matrix(operation: Any) -> np.ndarray:
    try:
        return np.asarray(operation.to_matrix(), dtype=complex)
    except Exception as exc:
        raise ValueError(
            f"ACE-QVM cannot simulate operation '{operation.name}' after decomposition. "
            "Decompose the ansatz to one- and two-qubit matrix-backed gates or use the statevector backend."
        ) from exc


def prepare_ace_qvm_circuit(circuit: QuantumCircuit, parameter_values: np.ndarray) -> QuantumCircuit:
    """Bind and decompose a circuit into ACE-QVM-supported matrix operations."""
    bound = bind_circuit_parameters(circuit, parameter_values)
    prepared = bound.decompose(reps=8)
    filtered = QuantumCircuit(prepared.num_qubits, name=prepared.name or "ace_qvm_prepared")
    qubit_indices = {qubit: index for index, qubit in enumerate(prepared.qubits)}
    for instruction in prepared.data:
        operation = instruction.operation
        name = operation.name.lower()
        if name == "barrier":
            continue
        if name in _UNSUPPORTED_OPERATION_NAMES:
            raise ValueError(
                f"ACE-QVM does not support Qiskit operation '{name}'. "
                "Remove measurement/control-flow/reset operations before backend evaluation."
            )
        qargs = [qubit_indices[qubit] for qubit in instruction.qubits]
        if len(qargs) > 2:
            raise ValueError(
                f"ACE-QVM supports only one- and two-qubit operations after decomposition; "
                f"operation '{name}' still has {len(qargs)} qubits."
            )
        if qargs:
            _operation_matrix(operation)
        filtered.append(operation, qargs)
    return filtered


class ACEQVMBackend(BackendAdapter):
    """Backend adapter for the ACE-QVM compressed-entanglement simulator."""

    backend_kind = "ace_qvm"

    def __init__(self, spec: BackendSpec) -> None:
        if spec.kind.strip().lower() != "ace_qvm":
            raise ValueError(f"Unsupported ACE-QVM backend kind: {spec.kind}")
        self.spec = spec
        self.settings = _settings_from_spec(spec)
        self.metadata: dict[str, object] = {
            "provider": "qcchem",
            "backend_kind": self.backend_kind,
            "hardware_verified": False,
            "ace_qvm": {
                "algorithm_name": "ACE-QVM",
                "settings": self.settings.to_dict(),
                "capability_tier": "exploratory",
                "boundary": (
                    "Compressed-entanglement local simulator evidence only; "
                    "not hardware execution and not a blanket exact statevector claim."
                ),
            },
        }
        self.provenance: dict[str, object] = {
            "adapter": "qcchem.backends.ace_qvm.ACEQVMBackend",
            "integration": "qcchem_exploratory_numpy_mps_branch_engine",
            "full_state_reconstruction_default": False,
        }

    def evaluate(
        self,
        circuit: QuantumCircuit,
        operator: SparsePauliOp,
        parameter_values: np.ndarray,
    ) -> BackendEstimate:
        prepared = prepare_ace_qvm_circuit(circuit, np.asarray(parameter_values, dtype=float))
        try:
            value, ace_metadata = simulate_circuit_expectation(
                circuit=prepared,
                operator=operator,
                settings=self.settings,
            )
        except ACEQVMCapacityError:
            raise
        except Exception as exc:
            raise RuntimeError(f"ACE-QVM evaluation failed: {type(exc).__name__}: {exc}") from exc
        self.metadata["ace_qvm"] = ace_metadata
        return BackendEstimate(
            value=value,
            reported_std=0.0,
            metadata={"ace_qvm": ace_metadata},
            seed=self.spec.seed,
            shots=self.spec.shots,
        )
