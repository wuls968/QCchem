"""Physical-sector constraints for molecular exact diagonalization."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.properties import AngularMomentum


@dataclass(frozen=True, slots=True)
class MolecularSector:
    num_particles: tuple[int, int]
    multiplicity: int
    number_operators: tuple[SparsePauliOp, SparsePauliOp]
    spin_squared: SparsePauliOp

    def metadata(self) -> dict[str, object]:
        spin = (self.multiplicity - 1) / 2
        return {
            "kind": "molecular_particle_and_spin",
            "num_particles": list(self.num_particles),
            "multiplicity": self.multiplicity,
            "spin_squared": spin * (spin + 1),
        }


def molecular_sector(problem_summary, mapper) -> MolecularSector | None:
    """Map electron constraints with the Hamiltonian's particle/Z2 reduction."""
    if problem_summary is None or mapper is None or problem_summary.basis == "real_space_lattice":
        return None
    orbitals = int(problem_summary.num_spatial_orbitals)
    if orbitals <= 0:
        return None
    operators = []
    for offset in (0, orbitals):
        number = FermionicOp(
            {f"+_{index} -_{index}": 1.0 for index in range(offset, offset + orbitals)},
            num_spin_orbitals=2 * orbitals,
        )
        mapped = mapper.map(number)
        if mapped is None:
            raise ValueError("The mapping cannot represent molecular particle constraints.")
        operators.append(mapped)
    overlap = getattr(problem_summary, "spin_orbital_overlap", None)
    angular_momentum = AngularMomentum(orbitals, overlap=np.asarray(overlap) if overlap is not None else None)
    spin_squared = mapper.map(angular_momentum.second_q_ops()["AngularMomentum"])
    if spin_squared is None:
        raise ValueError("The mapping cannot represent the requested total-spin sector.")
    return MolecularSector(
        tuple(problem_summary.num_particles), problem_summary.multiplicity,
        (operators[0], operators[1]), spin_squared,
    )
