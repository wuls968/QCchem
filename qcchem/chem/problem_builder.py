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
from qcchem.chem.external_charges import (
    ResolvedExternalPointCharges,
    StaticPointChargePySCFDriver,
    build_pyscf_driver,
)
from qcchem.chem.effective_hamiltonian import (
    build_boundary_embedding_summary,
    build_effective_hamiltonian_summary,
    resolve_environment_inputs,
)
from qcchem.chem.point_group import (
    SymmetryAwarePySCFDriver,
    resolve_point_group_filter,
    run_point_group_pyscf,
    skipped_point_group_metadata,
)
from qcchem.core import ProblemSummary, ReductionAuditSummary, RunSpec
from qcchem.core.results import EffectiveHamiltonianSummary, ExternalPointChargeSummary

REDUCTION_ENERGY_FORMULA = (
    "total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy "
    "+ external_point_charge_nuclear_interaction_energy + boundary_embedding_constant_energy; "
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
    external_point_charges: ExternalPointChargeSummary | None
    environment_embedding: EffectiveHamiltonianSummary | None


def _distance_unit(unit: str) -> DistanceUnit:
    normalized = unit.strip().lower()
    if normalized in {"angstrom", "ang", "a"}:
        return DistanceUnit.ANGSTROM
    if normalized in {"bohr", "au"}:
        return DistanceUnit.BOHR
    raise ValueError(f"Unsupported distance unit: {unit}")


class SymmetryAwareStaticPointChargePySCFDriver(
    StaticPointChargePySCFDriver,
    SymmetryAwarePySCFDriver,
):
    """PySCF driver combining point-charge embedding with symmetry metadata."""


def _build_driver(
    spec: RunSpec,
    method: MethodType,
    point_charges: ResolvedExternalPointCharges,
    *,
    symmetry: bool,
) -> PySCFDriver:
    if not symmetry:
        return build_pyscf_driver(
            atom=spec.molecule.geometry_string(),
            unit=_distance_unit(spec.molecule.unit),
            charge=spec.molecule.charge,
            spin=spec.molecule.spin,
            basis=spec.molecule.basis,
            method=method,
            point_charges=point_charges,
        )
    driver_cls: type[PySCFDriver] = (
        SymmetryAwareStaticPointChargePySCFDriver
        if point_charges.enabled
        else SymmetryAwarePySCFDriver
    )
    subgroup = spec.problem.point_group.subgroup.strip()
    kwargs = {}
    if symmetry and subgroup and subgroup.lower() != "auto":
        kwargs["symmetry_subgroup"] = subgroup
    if point_charges.enabled:
        kwargs["point_charges"] = point_charges
    return driver_cls(
        atom=spec.molecule.geometry_string(),
        unit=_distance_unit(spec.molecule.unit),
        charge=spec.molecule.charge,
        spin=spec.molecule.spin,
        basis=spec.molecule.basis,
        method=method,
        **kwargs,
    )


def _run_problem_driver(
    spec: RunSpec,
    method: MethodType,
    point_charges: ResolvedExternalPointCharges,
):
    point_group_mode = spec.mapping.symmetry_reduction.point_group.strip().lower()
    strict = bool(spec.mapping.symmetry_reduction.strict)
    if point_group_mode == "disabled":
        if spec.problem.point_group.reduction_mode.strip().lower() == "irrep_filter":
            raise ValueError("problem.point_group.irrep_filter requires mapping.symmetry_reduction.point_group.")
        driver = _build_driver(spec, method, point_charges, symmetry=False)
        return (
            driver.run(),
            skipped_point_group_metadata("Point-group symmetry audit disabled by mapping configuration."),
            driver,
        )

    driver = _build_driver(spec, method, point_charges, symmetry=True)
    try:
        result = run_point_group_pyscf(driver)
        metadata = dict(result.metadata)
        metadata.update(
            {
                "requested_mode": point_group_mode,
                "requested_subgroup": spec.problem.point_group.subgroup,
                "reduction_mode": spec.problem.point_group.reduction_mode,
                "active_irreps": list(spec.problem.point_group.active_irreps),
                "remove_irreps": list(spec.problem.point_group.remove_irreps),
            }
        )
        return result.problem, metadata, driver
    except Exception as exc:
        if strict or point_group_mode == "enabled":
            raise
        fallback_driver = _build_driver(spec, method, point_charges, symmetry=False)
        return (
            fallback_driver.run(),
            skipped_point_group_metadata(
                f"Point-group symmetry audit fell back to non-symmetry PySCF path: {type(exc).__name__}: {exc}"
            ),
            fallback_driver,
        )


def build_electronic_structure_context(spec: RunSpec) -> ElectronicStructureContext:
    """Construct an electronic-structure problem from a QCchem spec."""
    method = MethodType.RHF if spec.molecule.spin == 0 else MethodType.UHF
    transformers_applied: list[str] = []
    environment_inputs = resolve_environment_inputs(spec)
    external_point_charges = environment_inputs.point_charges
    external_summary = external_point_charges.to_summary(
        adapter_strategy=(
            "pyscf.qmmm.mm_charge(radii=gaussian)"
            if external_point_charges.radii is not None
            else "pyscf.qmmm.mm_charge"
        )
    )
    original_problem, point_group_metadata, driver = _run_problem_driver(
        spec,
        method,
        external_point_charges,
    )
    if external_point_charges.enabled and hasattr(
        driver,
        "external_point_charge_nuclear_interaction_energy",
    ):
        external_point_charges.qm_nuclear_interaction_energy = float(
            driver.external_point_charge_nuclear_interaction_energy
        )
        if external_summary is not None:
            external_summary.qm_nuclear_interaction_energy = float(
                driver.external_point_charge_nuclear_interaction_energy
            )
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
    point_group_filter = resolve_point_group_filter(
        point_group=spec.problem.point_group,
        metadata=point_group_metadata,
        available_original_orbitals=available_original,
        molecule=spec.molecule,
    )
    point_group_filter_metadata = None
    if point_group_filter is not None:
        transformer = ActiveSpaceTransformer(
            num_electrons=point_group_filter.num_electrons,
            num_spatial_orbitals=point_group_filter.num_spatial_orbitals,
            active_orbitals=point_group_filter.active_orbitals_current,
        )
        problem = transformer.transform(problem)
        transformers_applied.append("PointGroupIrrepFilter")
        selection_mode = "point_group_irrep_filter"
        selection_reason = "Explicit point-group irrep filter selected the active orbital subspace."
        selected_active_orbitals = list(point_group_filter.active_orbitals_current)
        selected_active_orbitals_original = list(point_group_filter.active_orbitals_original)
        available_original = list(point_group_filter.active_orbitals_original)
        point_group_filter_metadata = dict(point_group_filter.metadata)
        point_group_metadata["selected_active_orbitals"] = list(point_group_filter.active_orbitals_current)
        point_group_metadata["selected_active_orbitals_original"] = list(point_group_filter.active_orbitals_original)
        point_group_metadata["filter"] = point_group_filter_metadata

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
    if point_group_filter_metadata is not None:
        active_space_summary = {
            "selection_mode": "point_group_irrep_filter",
            "point_group_filter": point_group_filter_metadata,
            "num_electrons": point_group_filter_metadata.get("num_active_electrons"),
            "num_spatial_orbitals": point_group_filter_metadata.get("num_active_orbitals"),
            "active_orbitals": point_group_filter_metadata.get("selected_active_orbitals", []),
            "active_orbitals_original": point_group_filter_metadata.get(
                "selected_active_orbitals_original",
                [],
            ),
        }
    if resolved_active_space is not None:
        active_space_summary = {
            "num_electrons": resolved_active_space.num_electrons,
            "num_spatial_orbitals": resolved_active_space.num_spatial_orbitals,
            "active_orbitals": resolved_active_space.active_orbitals_current,
            "active_orbitals_original": resolved_active_space.active_orbitals_original,
        }
        if point_group_filter_metadata is not None:
            active_space_summary["point_group_filter"] = point_group_filter_metadata

    boundary_summary, v_boundary_ao = build_boundary_embedding_summary(
        boundary_spec=spec.problem.environment_embedding.boundary,
        molecule=spec.molecule,
        pyscf_driver=driver,
        active_space_metadata=active_space_summary,
    )

    constants = {
        str(key): float(value)
        for key, value in getattr(problem.hamiltonian, "constants", {}).items()
    }
    nuclear_repulsion_energy = float(constants.get("nuclear_repulsion_energy", 0.0))
    driver_constant_sum = float(sum(constants.values()))
    external_nuclear_energy = float(
        external_point_charges.qm_nuclear_interaction_energy
        if external_point_charges.enabled
        else 0.0
    )
    if external_point_charges.enabled:
        constants["external_point_charge_nuclear_interaction_energy"] = external_nuclear_energy
    boundary_constant_energy = float(boundary_summary.constant_energy)
    if boundary_summary.enabled:
        constants["boundary_embedding_constant_energy"] = boundary_constant_energy
    electronic_constant_correction = driver_constant_sum - nuclear_repulsion_energy
    total_constant_correction = (
        electronic_constant_correction
        + nuclear_repulsion_energy
        + external_nuclear_energy
        + boundary_constant_energy
    )
    effective_hamiltonian_summary = build_effective_hamiltonian_summary(
        spec=spec,
        env_inputs=environment_inputs,
        pyscf_driver=driver,
        active_space_projection={
            "original_num_spatial_orbitals": original_num_spatial_orbitals,
            "reduced_num_spatial_orbitals": int(problem.num_spatial_orbitals),
            "num_particles": tuple(int(value) for value in problem.num_particles),
            "transformers_applied": list(transformers_applied),
            "active_space_metadata": active_space_summary,
            "environment_qubit_growth": 0,
        },
        boundary_summary=boundary_summary,
        v_boundary_ao=v_boundary_ao,
    )

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
            point_group_metadata=point_group_metadata,
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
            external_point_charge_nuclear_interaction_energy=external_nuclear_energy,
            boundary_embedding_constant_energy=boundary_constant_energy,
            total_constant_correction=total_constant_correction,
            energy_formula=REDUCTION_ENERGY_FORMULA,
            point_group_metadata=point_group_metadata,
        ),
        external_point_charges=external_summary,
        environment_embedding=effective_hamiltonian_summary,
    )
