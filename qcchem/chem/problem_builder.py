"""Electronic-structure problem construction using Qiskit Nature."""

from __future__ import annotations

from dataclasses import dataclass

from qiskit_nature.second_q.drivers import MethodType, PySCFDriver
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.problems import ElectronicStructureProblem
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer, FreezeCoreTransformer
from qiskit_nature.units import DistanceUnit

from qcchem.chem.active_space import (
    available_original_orbitals,
    infer_frozen_core_orbitals,
    resolve_active_space,
)
from qcchem.core import ProblemSummary, ReductionAuditSummary, RunSpec

REDUCTION_ENERGY_FORMULA = (
    "total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; "
    "electronic_energy = solver_energy + constant_energy_correction"
)


@dataclass(slots=True)
class ElectronicStructureContext:
    """Internal chemistry context used by mapping and solver layers."""

    problem: ElectronicStructureProblem
    fermionic_hamiltonian: FermionicOp
    summary: ProblemSummary
    nuclear_repulsion_energy: float
    electronic_constant_correction: float
    total_constant_correction: float
    hf_reference_energy: float | None
    reduction_audit: ReductionAuditSummary


def _distance_unit(unit: str) -> DistanceUnit:
    normalized = unit.strip().lower()
    if normalized in {"angstrom", "ang", "a"}:
        return DistanceUnit.ANGSTROM
    if normalized in {"bohr", "au"}:
        return DistanceUnit.BOHR
    raise ValueError(f"Unsupported distance unit: {unit}")


def build_electronic_structure_context(spec: RunSpec) -> ElectronicStructureContext:
    """Construct an electronic-structure problem from a QCchem spec."""
    method = MethodType.RHF if spec.molecule.spin == 0 else MethodType.UHF
    transformers_applied: list[str] = []
    driver = PySCFDriver(
        atom=spec.molecule.geometry_string(),
        unit=_distance_unit(spec.molecule.unit),
        charge=spec.molecule.charge,
        spin=spec.molecule.spin,
        basis=spec.molecule.basis,
        method=method,
    )
    original_problem = driver.run()
    problem = original_problem
    original_num_spatial_orbitals = int(original_problem.num_spatial_orbitals)
    removed_orbitals = [int(value) for value in spec.problem.remove_orbitals]
    frozen_core_orbitals: list[int] = []
    selection_mode = "none"
    selection_reason = "No active-space reduction requested."
    selected_active_orbitals: list[int] = []
    selected_active_orbitals_original: list[int] = []

    if spec.problem.freeze_core or removed_orbitals:
        freeze_transformer = FreezeCoreTransformer(
            freeze_core=spec.problem.freeze_core,
            remove_orbitals=removed_orbitals or None,
        )
        problem = freeze_transformer.transform(problem)
        transformers_applied.append("FreezeCoreTransformer")
        frozen_core_orbitals = infer_frozen_core_orbitals(
            original_num_spatial_orbitals=original_num_spatial_orbitals,
            post_freeze_num_spatial_orbitals=int(problem.num_spatial_orbitals),
            remove_orbitals=removed_orbitals,
        )

    available_original = available_original_orbitals(
        original_num_spatial_orbitals=original_num_spatial_orbitals,
        frozen_core_orbitals=frozen_core_orbitals,
        remove_orbitals=removed_orbitals,
    )
    resolved_active_space = resolve_active_space(
        spec.problem.active_space,
        num_particles=tuple(int(value) for value in problem.num_particles),
        num_spatial_orbitals=int(problem.num_spatial_orbitals),
        available_original=available_original,
    )

    if resolved_active_space is not None:
        active_orbitals_for_transformer = (
            resolved_active_space.active_orbitals_current or None
        )
        transformer = ActiveSpaceTransformer(
            num_electrons=resolved_active_space.num_electrons,
            num_spatial_orbitals=resolved_active_space.num_spatial_orbitals,
            active_orbitals=active_orbitals_for_transformer,
        )
        problem = transformer.transform(problem)
        transformers_applied.append("ActiveSpaceTransformer")
        selection_mode = resolved_active_space.selection_mode
        selection_reason = resolved_active_space.selection_reason
        selected_active_orbitals = list(resolved_active_space.active_orbitals_current)
        selected_active_orbitals_original = list(resolved_active_space.active_orbitals_original)

    fermionic_hamiltonian = problem.hamiltonian.second_q_op()
    active_space_summary = None
    if resolved_active_space is not None:
        active_space_summary = {
            "num_electrons": resolved_active_space.num_electrons,
            "num_spatial_orbitals": resolved_active_space.num_spatial_orbitals,
            "active_orbitals": resolved_active_space.active_orbitals_current,
            "active_orbitals_original": resolved_active_space.active_orbitals_original,
        }

    constants = {
        str(key): float(value)
        for key, value in getattr(problem.hamiltonian, "constants", {}).items()
    }
    nuclear_repulsion_energy = float(constants.get("nuclear_repulsion_energy", 0.0))
    total_constant_correction = float(sum(constants.values()))
    electronic_constant_correction = total_constant_correction - nuclear_repulsion_energy

    return ElectronicStructureContext(
        problem=problem,
        fermionic_hamiltonian=fermionic_hamiltonian,
        summary=ProblemSummary(
            molecule_name=spec.molecule.name,
            basis=spec.molecule.basis,
            charge=spec.molecule.charge,
            multiplicity=spec.molecule.multiplicity,
            num_particles=tuple(int(value) for value in problem.num_particles),
            num_spatial_orbitals=int(problem.num_spatial_orbitals),
            active_space_metadata=active_space_summary,
            transformers_applied=transformers_applied,
            hamiltonian_constants=constants,
            electronic_constant_correction=electronic_constant_correction,
        ),
        nuclear_repulsion_energy=nuclear_repulsion_energy,
        electronic_constant_correction=electronic_constant_correction,
        total_constant_correction=total_constant_correction,
        hf_reference_energy=float(problem.reference_energy) if problem.reference_energy is not None else None,
        reduction_audit=ReductionAuditSummary(
            original_num_particles=tuple(int(value) for value in original_problem.num_particles),
            original_num_spatial_orbitals=int(original_problem.num_spatial_orbitals),
            reduced_num_particles=tuple(int(value) for value in problem.num_particles),
            reduced_num_spatial_orbitals=int(problem.num_spatial_orbitals),
            transformers_applied=transformers_applied,
            active_space_metadata=active_space_summary,
            selection_mode=selection_mode,
            selection_reason=selection_reason,
            selected_active_orbitals=selected_active_orbitals,
            selected_active_orbitals_original=selected_active_orbitals_original,
            frozen_core_orbitals=frozen_core_orbitals,
            removed_orbitals=removed_orbitals,
            hamiltonian_constants=constants,
            constant_energy_correction=electronic_constant_correction,
            nuclear_repulsion_energy=nuclear_repulsion_energy,
            total_constant_correction=total_constant_correction,
            energy_formula=REDUCTION_ENERGY_FORMULA,
        ),
    )
