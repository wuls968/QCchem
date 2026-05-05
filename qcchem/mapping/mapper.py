"""Mapping utilities for fermionic and qubit operators."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.mappers import BravyiKitaevMapper, JordanWignerMapper, ParityMapper
from qiskit_nature.second_q.operators import FermionicOp

from qcchem.core import MappingSummary


@dataclass(slots=True)
class MappedHamiltonian:
    """Mapped qubit Hamiltonian and its summary."""

    fermionic_hamiltonian: FermionicOp
    qubit_hamiltonian: SparsePauliOp
    mapper: object
    summary: MappingSummary


def _ensure_numpy_compat() -> None:
    """Patch NumPy compatibility expected by the current Qiskit Nature release."""
    if not hasattr(np, "in1d"):
        np.in1d = np.isin  # type: ignore[attr-defined]


def _build_mapper(kind: str, *, num_particles: tuple[int, int] | None = None):
    _ensure_numpy_compat()
    normalized = kind.strip().lower()
    if normalized == "jordan_wigner":
        return JordanWignerMapper()
    if normalized == "bravyi_kitaev":
        return BravyiKitaevMapper()
    if normalized == "parity_two_qubit_reduction":
        if num_particles is None:
            raise ValueError("parity_two_qubit_reduction requires num_particles.")
        return ParityMapper(num_particles=num_particles)
    raise ValueError(f"Unsupported mapping kind: {kind}")


def map_fermionic_hamiltonian(
    fermionic_hamiltonian: FermionicOp,
    mapping_kind: str,
    *,
    num_particles: tuple[int, int] | None = None,
) -> MappedHamiltonian:
    """Map a fermionic Hamiltonian into a qubit Hamiltonian."""
    mapper = _build_mapper(mapping_kind, num_particles=num_particles)
    qubit_hamiltonian = mapper.map(fermionic_hamiltonian)
    return MappedHamiltonian(
        fermionic_hamiltonian=fermionic_hamiltonian,
        qubit_hamiltonian=qubit_hamiltonian,
        mapper=mapper,
        summary=MappingSummary(
            kind=mapping_kind,
            num_qubits=int(qubit_hamiltonian.num_qubits),
            fermionic_term_count=len(fermionic_hamiltonian),
            qubit_term_count=len(qubit_hamiltonian),
        ),
    )
