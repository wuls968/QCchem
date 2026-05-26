"""PySCF PBC adapter for Gamma-only electronic-structure problems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
from pyscf import ao2mo
from pyscf.pbc import df, gto, scf
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit_nature.second_q.problems import ElectronicBasis, ElectronicStructureProblem


@dataclass(frozen=True, slots=True)
class GammaCellInput:
    """Input needed to build a Gamma-only PySCF periodic cell."""

    atom: str | Sequence[tuple[str, Sequence[float]]]
    lattice_vectors: Sequence[Sequence[float]]
    basis: str = "sto-3g"
    unit: str = "Bohr"
    charge: int = 0
    spin: int = 0
    pseudo: str | None = None
    precision: float | None = None
    kpoint_mesh: Sequence[int] = (1, 1, 1)
    method: str = "rhf"
    density_fit: bool = True
    density_fitting: str = "fftdf"
    mesh: Sequence[int] | None = None
    max_cycle: int = 50


@dataclass(frozen=True, slots=True)
class GammaCellProblem:
    """Completed PySCF cell calculation and mapped Qiskit Nature problem."""

    cell: Any
    mean_field: Any
    problem: ElectronicStructureProblem
    metadata: dict[str, Any]


def _validate_gamma_mesh(kpoint_mesh: Sequence[int]) -> tuple[int, int, int]:
    mesh = tuple(int(value) for value in kpoint_mesh)
    if mesh != (1, 1, 1):
        raise ValueError(
            "PBC PySCF adapter currently supports Gamma-only cells; "
            f"kpoint_mesh={list(mesh)} is not supported."
        )
    return mesh


def build_gamma_cell(spec: GammaCellInput):
    """Build a PySCF periodic cell after enforcing Gamma-only scope."""

    _validate_gamma_mesh(spec.kpoint_mesh)
    cell = gto.Cell()
    cell.atom = spec.atom
    cell.a = np.asarray(spec.lattice_vectors, dtype=float)
    cell.basis = spec.basis
    cell.unit = spec.unit
    cell.charge = int(spec.charge)
    cell.spin = int(spec.spin)
    cell.verbose = 0
    if spec.pseudo is not None:
        cell.pseudo = spec.pseudo
    if spec.precision is not None:
        cell.precision = float(spec.precision)
    if spec.mesh is not None:
        mesh = tuple(int(value) for value in spec.mesh)
        if len(mesh) != 3 or any(value <= 0 for value in mesh):
            raise ValueError("PBC PySCF adapter mesh must contain three positive integers.")
        cell.mesh = np.asarray(mesh, dtype=int)
    cell.build()
    return cell


def _build_mean_field(
    cell: Any,
    *,
    method: str,
    density_fit: bool,
    density_fitting: str,
    max_cycle: int,
):
    normalized = method.strip().lower()
    if normalized == "rhf":
        mf = scf.RHF(cell)
    elif normalized == "uhf":
        raise ValueError("Gamma-only PBC mapped algorithms support closed-shell RHF only in v1.")
    else:
        raise ValueError(f"Unsupported Gamma-only PBC SCF method: {method}")
    if density_fit:
        df_kind = density_fitting.strip().lower()
        backends = {
            "fftdf": df.FFTDF,
            "gdf": df.GDF,
            "mdf": df.MDF,
            "aftdf": df.AFTDF,
        }
        if df_kind not in backends:
            raise ValueError("PBC density_fitting must be fftdf, gdf, mdf, or aftdf.")
        mf.with_df = backends[df_kind](cell)
    mf.max_cycle = int(max_cycle)
    return mf


def _mo_coeff_array(mo_coeff: Any) -> np.ndarray:
    if isinstance(mo_coeff, tuple):
        mo_coeff = mo_coeff[0]
    coeff = np.asarray(mo_coeff)
    if np.iscomplexobj(coeff):
        imag_norm = float(np.linalg.norm(np.imag(coeff)))
        if imag_norm > 1.0e-10:
            raise ValueError(
                "Gamma-only PBC adapter only maps real MO coefficients; "
                f"imaginary_norm={imag_norm:.6e}."
            )
        coeff = np.real(coeff)
    return np.asarray(coeff, dtype=float)


def _one_body_mo(
    mean_field: Any,
    coeff: np.ndarray,
    *,
    one_body_ao_delta: np.ndarray | None = None,
) -> np.ndarray:
    hcore = np.asarray(mean_field.get_hcore())
    if one_body_ao_delta is not None:
        hcore = hcore + np.asarray(one_body_ao_delta)
    if np.iscomplexobj(hcore):
        imag_norm = float(np.linalg.norm(np.imag(hcore)))
        if imag_norm > 1.0e-10:
            raise ValueError(
                "Gamma-only PBC adapter only maps real one-body integrals; "
                f"imaginary_norm={imag_norm:.6e}."
            )
        hcore = np.real(hcore)
    return np.asarray(coeff.T @ np.asarray(hcore, dtype=float) @ coeff, dtype=float)


def _two_body_mo(mean_field: Any, coeff: np.ndarray) -> np.ndarray:
    compact = mean_field.with_df.ao2mo(coeff)
    restored = ao2mo.restore(1, compact, coeff.shape[1])
    if np.iscomplexobj(restored):
        imag_norm = float(np.linalg.norm(np.imag(restored)))
        if imag_norm > 1.0e-10:
            raise ValueError(
                "Gamma-only PBC adapter only maps real two-body integrals; "
                f"imaginary_norm={imag_norm:.6e}."
            )
        restored = np.real(restored)
    return np.asarray(restored, dtype=float)


def electronic_structure_problem_from_gamma_scf(
    mean_field: Any,
    *,
    cell: Any | None = None,
    method: str = "rhf",
    one_body_ao_delta: np.ndarray | None = None,
    constants: dict[str, float] | None = None,
) -> ElectronicStructureProblem:
    """Convert a converged Gamma-only PySCF PBC SCF object into a Qiskit problem."""

    source_cell = cell if cell is not None else mean_field.cell
    coeff = _mo_coeff_array(mean_field.mo_coeff)
    h1 = _one_body_mo(mean_field, coeff, one_body_ao_delta=one_body_ao_delta)
    h2 = _two_body_mo(mean_field, coeff)
    normalized = method.strip().lower()
    if normalized == "uhf":
        raise ValueError("Gamma-only PBC mapped algorithms support closed-shell RHF only in v1.")
    else:
        energy = ElectronicEnergy.from_raw_integrals(h1, h2, validate=False)
    energy.constants = {
        "nuclear_repulsion_energy": float(mean_field.energy_nuc()),
    }
    if constants:
        energy.constants.update({str(key): float(value) for key, value in constants.items()})
    problem = ElectronicStructureProblem(energy)
    problem.basis = ElectronicBasis.MO
    problem.num_spatial_orbitals = int(coeff.shape[1])
    nelec = getattr(source_cell, "nelec", None)
    if nelec is None or tuple(int(value) for value in nelec) == (0, 0):
        nalpha = (int(source_cell.nelectron) + int(source_cell.spin)) // 2
        nbeta = int(source_cell.nelectron) - nalpha
        nelec = (nalpha, nbeta)
    problem.num_particles = tuple(int(value) for value in nelec)
    problem.reference_energy = float(mean_field.e_tot)
    return problem


def run_gamma_cell_problem(spec: GammaCellInput) -> GammaCellProblem:
    """Run a Gamma-only PySCF PBC calculation and return a mapped problem."""

    mesh = _validate_gamma_mesh(spec.kpoint_mesh)
    cell = build_gamma_cell(spec)
    mean_field = _build_mean_field(
        cell,
        method=spec.method,
        density_fit=bool(spec.density_fit),
        density_fitting=spec.density_fitting,
        max_cycle=int(spec.max_cycle),
    )
    mean_field.kernel()
    if not bool(mean_field.converged):
        raise ValueError("Gamma-only PBC PySCF SCF did not converge.")
    problem = electronic_structure_problem_from_gamma_scf(
        mean_field,
        cell=cell,
        method=spec.method,
    )
    metadata = {
        "schema": "qcchem.pbc.pyscf_adapter.v1",
        "adapter": "qcchem.pbc.pyscf_adapter.run_gamma_cell_problem",
        "pyscf_cell": {
            "dimension": int(cell.dimension),
            "lattice_vectors_bohr": np.asarray(
                cell.lattice_vectors(),
                dtype=float,
            ).tolist(),
            "basis": spec.basis,
            "unit": spec.unit,
            "charge": int(spec.charge),
            "spin": int(spec.spin),
            "nelectron": int(cell.nelectron),
        },
        "scf": {
            "method": spec.method.strip().lower(),
            "density_fit": bool(spec.density_fit),
            "density_fitting": spec.density_fitting.strip().lower(),
            "mesh": (None if spec.mesh is None else [int(value) for value in spec.mesh]),
            "converged": bool(mean_field.converged),
            "e_tot_hartree": float(mean_field.e_tot),
            "nuclear_repulsion_energy_hartree": float(mean_field.energy_nuc()),
        },
        "mapping": {
            "target": "qiskit_nature.second_q.problems.ElectronicStructureProblem",
            "raw_integrals": "ElectronicEnergy.from_raw_integrals",
            "orbital_basis": "Gamma-point PySCF molecular orbitals",
            "num_spatial_orbitals": int(problem.num_spatial_orbitals),
            "num_particles": [int(value) for value in problem.num_particles],
        },
        "scope": {
            "kpoint_mesh": list(mesh),
            "non_gamma_policy": "rejected",
            "spin_policy": "closed_shell_rhf_only",
            "periodic_images": "PySCF PBC cell integrals at Gamma point",
        },
        "integration_recommendations": [
            "Use GammaCellProblem.problem anywhere the molecular builder expects an ElectronicStructureProblem.",
            "Keep non-Gamma k-point workflows out of the mapped quantum-algorithm path until full k-point support exists.",
            "Use qcchem.pbc.ewald for periodic QM/MM constant terms before adding them to hamiltonian.constants.",
        ],
    }
    return GammaCellProblem(
        cell=cell,
        mean_field=mean_field,
        problem=problem,
        metadata=metadata,
    )
