"""Shared circuit preparation helpers."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit


def bind_circuit_parameters(circuit: QuantumCircuit, parameter_values) -> QuantumCircuit:
    """Bind a circuit's parameters with QCchem's strict parameter-count contract."""
    if not circuit.num_parameters:
        return circuit
    values = np.asarray(parameter_values, dtype=float)
    if len(values) != circuit.num_parameters:
        raise ValueError(
            f"Cannot bind circuit: {len(values)} values for {circuit.num_parameters} parameters."
        )
    parameter_map = dict(zip(circuit.parameters, values, strict=True))
    return circuit.assign_parameters(parameter_map, inplace=False)


def statevector_ready_circuit(circuit: QuantumCircuit, parameter_values) -> QuantumCircuit:
    """Bind and decompose circuits before local Qiskit Statevector evaluation."""
    bound_circuit = bind_circuit_parameters(circuit, parameter_values)
    return bound_circuit.decompose(reps=4)
