from __future__ import annotations

import warnings

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp
from scipy.sparse import SparseEfficiencyWarning

from qcchem.backends import StatevectorBackend
from qcchem.core import BackendSpec


def test_statevector_backend_evaluates_pauli_evolution_without_sparse_efficiency_warning() -> None:
    backend = StatevectorBackend(BackendSpec(kind="statevector", seed=123))
    theta = Parameter("theta")
    circuit = QuantumCircuit(1)
    circuit.append(PauliEvolutionGate(SparsePauliOp.from_list([("X", 1.0)]), time=theta), [0])
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    with warnings.catch_warnings():
        warnings.simplefilter("error", SparseEfficiencyWarning)
        estimate = backend.evaluate(circuit, operator, np.asarray([0.1], dtype=float))

    assert estimate.reported_std == 0.0
