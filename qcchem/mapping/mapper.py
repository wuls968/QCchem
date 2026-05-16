"""Mapping utilities for fermionic and qubit operators."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.mappers import BravyiKitaevMapper, JordanWignerMapper, ParityMapper
from qiskit_nature.second_q.operators import FermionicOp

from qcchem.core import MappingSummary, MappingSymmetryReductionSpec
from qcchem.mapping.symmetry import apply_z2_tapering


@dataclass(slots=True)
class MappedHamiltonian:
    """Mapped qubit Hamiltonian and its summary."""

    fermionic_hamiltonian: FermionicOp
    qubit_hamiltonian: SparsePauliOp
    mapper: object
    summary: MappingSummary
    raw_qubit_hamiltonian: SparsePauliOp | None = None
    base_mapper: object | None = None


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
    problem: object | None = None,
    symmetry_reduction: MappingSymmetryReductionSpec | dict[str, object] | None = None,
) -> MappedHamiltonian:
    """Map a fermionic Hamiltonian into a qubit Hamiltonian."""
    base_mapper = _build_mapper(mapping_kind, num_particles=num_particles)
    raw_qubit_hamiltonian = base_mapper.map(fermionic_hamiltonian)
    tapering = apply_z2_tapering(
        fermionic_hamiltonian=fermionic_hamiltonian,
        base_mapper=base_mapper,
        raw_qubit_hamiltonian=raw_qubit_hamiltonian,
        problem=problem,
        symmetry_reduction=symmetry_reduction,
    )
    qubit_hamiltonian = tapering.qubit_hamiltonian
    raw_num_qubits = int(raw_qubit_hamiltonian.num_qubits)
    num_qubits = int(qubit_hamiltonian.num_qubits)
    return MappedHamiltonian(
        fermionic_hamiltonian=fermionic_hamiltonian,
        qubit_hamiltonian=qubit_hamiltonian,
        mapper=tapering.mapper,
        raw_qubit_hamiltonian=raw_qubit_hamiltonian,
        base_mapper=base_mapper,
        summary=MappingSummary(
            kind=mapping_kind,
            num_qubits=num_qubits,
            fermionic_term_count=len(fermionic_hamiltonian),
            qubit_term_count=len(qubit_hamiltonian),
            raw_num_qubits=raw_num_qubits,
            raw_qubit_term_count=len(raw_qubit_hamiltonian),
            symmetry_tapered_qubits=max(raw_num_qubits - num_qubits, 0),
            z2_symmetry_count=tapering.z2_symmetry_count,
            z2_tapering_values=tapering.z2_tapering_values,
            symmetry_reduction_status=tapering.status,
            symmetry_reduction_notes=tapering.notes,
            symmetry_reduction_validation=tapering.validation,
        ),
    )
