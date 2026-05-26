"""Electronic-structure problem construction using Qiskit Nature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
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
    ATOMIC_NUMBERS,
    BOHR_PER_ANGSTROM,
    ResolvedExternalPointCharges,
    StaticPointChargePySCFDriver,
    build_pyscf_driver,
    convert_point_charges_unit,
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
from qcchem.core.results import (
    BoundaryEmbeddingSummary,
    EffectiveHamiltonianSummary,
    ExternalPointChargeSummary,
    PBCQMMMSummary,
    PeriodicBoundarySummary,
)
from qcchem.io.exports import workspace_fingerprint
from qcchem.io.serialization import to_primitive
from qcchem.pbc.ewald import (
    EwaldSettings,
    PeriodicPointCharge,
    periodic_qmmm_nuclear_point_charge_energy,
)
from qcchem.pbc.geometry import cell_volume, normalize_cell_unit
from qcchem.pbc.pyscf_adapter import (
    GammaCellInput,
    electronic_structure_problem_from_gamma_scf,
    run_gamma_cell_problem,
)

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


class _PBCEmbeddingAuditDriver:
    """Small adapter object consumed by effective-Hamiltonian summary code."""

    def __init__(self, v_env_ao: np.ndarray | None) -> None:
        self.external_point_charge_potential_matrix_ao = v_env_ao


def _pbc_cell_unit(unit: str) -> str:
    return "Angstrom" if normalize_cell_unit(unit) == "angstrom" else "Bohr"


def _pbc_periodic_summary(spec: RunSpec) -> PeriodicBoundarySummary | None:
    if not spec.problem.pbc.enabled and not spec.molecule.periodic.enabled:
        return None
    periodic = spec.molecule.periodic
    if not periodic.enabled or periodic.cell is None:
        raise ValueError("problem.pbc.enabled=true requires molecule.periodic.enabled=true with cell vectors.")
    if tuple(bool(value) for value in periodic.pbc) != (True, True, True):
        raise ValueError("PBC v1 supports only fully periodic pbc=[true, true, true] cells.")
    if tuple(bool(value) for value in spec.problem.pbc.pbc) != (True, True, True):
        raise ValueError("PBC v1 supports only fully periodic problem.pbc.pbc=[true, true, true] cells.")
    if normalize_cell_unit(periodic.cell.unit) != normalize_cell_unit(spec.molecule.unit):
        raise ValueError("PBC v1 requires molecule.periodic.cell.unit to match molecule.unit.")
    if spec.problem.pbc.neutralization == "uniform_background":
        raise ValueError("problem.pbc.neutralization=uniform_background is not implemented in PBC v1.")
    if spec.molecule.charge != 0:
        raise ValueError("PBC v1 requires a neutral QM molecule unless a supported neutralization model is added.")
    pbc_payload = {
        "molecule_periodic": to_primitive(periodic),
        "problem_pbc": to_primitive(spec.problem.pbc),
    }
    return PeriodicBoundarySummary(
        enabled=True,
        cell_vectors=[[float(value) for value in row] for row in periodic.cell.vectors],
        cell_unit=periodic.cell.unit,
        pbc=list(periodic.pbc),
        coordinate_mode=periodic.coordinate_mode,
        wrap_policy=periodic.wrap_policy,
        volume=cell_volume(periodic.cell.vectors),
        kpoint_mesh=[int(value) for value in spec.problem.pbc.kpoint_mesh],
        driver=spec.problem.pbc.driver,
        mode=spec.problem.pbc.mode,
        density_fitting=spec.problem.pbc.density_fitting,
        precision=spec.problem.pbc.precision,
        fingerprint=workspace_fingerprint([str(to_primitive(pbc_payload))]),
        provenance={
            "source": periodic.source or periodic.cell.source,
            "semantics": "Gamma-only periodic/supercell electronic structure in v1.",
        },
        risk_notes=[
            "PBC v1 supports Gamma-only/supercell periodic Hamiltonians; non-Gamma k-point meshes are rejected.",
            "Finite-size, k-point convergence, and pseudopotential validation require explicit follow-up studies.",
        ],
    )


def _qm_nuclear_charges(spec: RunSpec, *, unit: str) -> list[PeriodicPointCharge]:
    scale = BOHR_PER_ANGSTROM if normalize_cell_unit(spec.molecule.unit) == "angstrom" and normalize_cell_unit(unit) == "bohr" else 1.0
    if normalize_cell_unit(spec.molecule.unit) == "bohr" and normalize_cell_unit(unit) == "angstrom":
        scale = 1.0 / BOHR_PER_ANGSTROM
    charges: list[PeriodicPointCharge] = []
    for atom in spec.molecule.geometry:
        if atom.symbol not in ATOMIC_NUMBERS:
            raise ValueError(f"Unsupported atom symbol for PBC QM/MM Ewald: {atom.symbol}")
        charges.append(
            PeriodicPointCharge(
                label=atom.symbol,
                coords=tuple(float(value) * scale for value in atom.coords),
                charge=float(ATOMIC_NUMBERS[atom.symbol]),
            )
        )
    return charges


def _periodic_point_charge_potential_ao(
    *,
    cell: Any,
    point_charges: ResolvedExternalPointCharges,
) -> np.ndarray | None:
    if not point_charges.enabled:
        return None
    matrix = np.zeros((cell.nao_nr(), cell.nao_nr()), dtype=float)
    for charge in point_charges.charges:
        origin = (
            tuple(float(value) * BOHR_PER_ANGSTROM for value in charge.coords)
            if point_charges.unit == "angstrom"
            else charge.coords
        )
        with cell.with_rinv_origin(origin):
            matrix -= float(charge.charge) * np.asarray(cell.pbc_intor("int1e_rinv"), dtype=float)
    return matrix


def _build_pbc_qmmm_summary(
    *,
    spec: RunSpec,
    env_inputs,
    periodic_summary: PeriodicBoundarySummary | None,
    cell: Any,
) -> tuple[PBCQMMMSummary | None, float, dict[str, float], np.ndarray | None]:
    if not (spec.problem.pbc.enabled and env_inputs.enabled and env_inputs.point_charges.enabled):
        return None, 0.0, {}, None
    policy = spec.problem.environment_embedding.periodic_policy
    if policy.mode != "ewald":
        raise ValueError(
            "PBC environment embedding requires problem.environment_embedding.periodic_policy.mode=ewald."
        )
    if policy.neutralization == "uniform_background":
        raise ValueError(
            "problem.environment_embedding.periodic_policy.neutralization=uniform_background "
            "is not implemented in PBC-QM/MM v1."
        )
    point_charges = env_inputs.point_charges
    if normalize_cell_unit(point_charges.unit) != normalize_cell_unit(spec.molecule.unit):
        converted = convert_point_charges_unit(
            point_charges.charges,
            source_unit=point_charges.unit,
            target_unit=spec.molecule.unit,
        )
        point_charges.charges[:] = converted
        point_charges.unit = spec.molecule.unit
    total_mm_charge = float(sum(charge.charge for charge in point_charges.charges))
    qm_nuclear = _qm_nuclear_charges(spec, unit=spec.molecule.unit)
    full_cell_charge = float(spec.molecule.charge + total_mm_charge)
    if policy.require_charge_neutrality and abs(full_cell_charge) > 1.0e-10:
        raise ValueError(
            "PBC-QM/MM Ewald requires a neutral full QM/MM cell including QM electrons; "
            f"molecule_charge_plus_mm_charge={full_cell_charge:.12g}."
        )
    mm_charges = [
        PeriodicPointCharge(label=charge.label, coords=charge.coords, charge=float(charge.charge))
        for charge in point_charges.charges
    ]
    result = periodic_qmmm_nuclear_point_charge_energy(
        lattice_vectors=spec.molecule.periodic.cell.vectors if spec.molecule.periodic.cell else cell.lattice_vectors(),
        qm_nuclear_charges=qm_nuclear,
        mm_point_charges=mm_charges,
        settings=EwaldSettings(
            unit=spec.molecule.unit,
            real_space_cutoff=policy.real_space_cutoff,
            reciprocal_cutoff=policy.reciprocal_cutoff,
            neutrality_tolerance=policy.ewald_precision,
            total_cell_charge=full_cell_charge,
        ),
    )
    v_env_ao = _periodic_point_charge_potential_ao(cell=cell, point_charges=point_charges)
    one_body = {
        "available": v_env_ao is not None,
        "shape": [] if v_env_ao is None else [int(value) for value in v_env_ao.shape],
        "frobenius_norm": 0.0 if v_env_ao is None else float(np.linalg.norm(v_env_ao)),
        "source": "pbc_intor(int1e_rinv) fixed MM point-charge potential at Gamma point",
    }
    summary = PBCQMMMSummary(
        enabled=True,
        mode=policy.mode,
        neutralization=policy.neutralization,
        require_charge_neutrality=policy.require_charge_neutrality,
        ewald_precision=policy.ewald_precision,
        charge_count=len(point_charges.charges),
        total_mm_charge=total_mm_charge,
        nuclear_interaction_energy=float(result.energy_hartree),
        background_energy=0.0,
        one_body_environment=one_body,
        provenance={
            "ewald": result.payload,
            "full_cell_charge": full_cell_charge,
            "periodic_boundary_fingerprint": (
                periodic_summary.fingerprint if periodic_summary is not None else None
            ),
        },
        risk_notes=[
            "PBC-QM/MM v1 applies fixed classical MM charges through a Gamma-point one-body potential.",
            "The nuclear/MM constant uses a QCchem Ewald cross term; polarization, MM relaxation, and PME dynamics are not included.",
        ],
    )
    constants = {"pbc_qmmm_nuclear_interaction_energy": float(result.energy_hartree)}
    return summary, float(result.energy_hartree), constants, v_env_ao


def build_pbc_electronic_structure_context(spec: RunSpec) -> ElectronicStructureContext:
    """Construct a Gamma-only periodic electronic-structure context."""
    if not spec.problem.pbc.enabled:
        raise ValueError("build_pbc_electronic_structure_context requires problem.pbc.enabled=true.")
    if spec.problem.qft.enabled:
        raise ValueError("problem.pbc cannot be combined with problem.qft lattice-QED in v1.")
    if spec.problem.cavity_qed.enabled:
        raise ValueError("problem.pbc cannot be combined with problem.cavity_qed in v1.")
    if spec.molecule.spin != 0:
        raise ValueError("PBC v1 supports closed-shell RHF systems only; open-shell/UHF mapping is not implemented.")
    periodic_summary = _pbc_periodic_summary(spec)
    periodic = spec.molecule.periodic
    if periodic.cell is None:
        raise ValueError("problem.pbc.enabled=true requires molecule.periodic.cell.vectors.")
    if tuple(int(value) for value in spec.problem.pbc.kpoint_mesh) != (1, 1, 1):
        raise ValueError("PBC v1 supports only Gamma-only kpoint_mesh=[1, 1, 1].")

    method = "rhf" if spec.molecule.spin == 0 else "uhf"
    gamma = run_gamma_cell_problem(
        GammaCellInput(
            atom=spec.molecule.geometry_string(),
            lattice_vectors=periodic.cell.vectors,
            basis=spec.molecule.basis,
            unit=_pbc_cell_unit(periodic.cell.unit),
            charge=spec.molecule.charge,
            spin=spec.molecule.spin,
            precision=spec.problem.pbc.precision,
            kpoint_mesh=spec.problem.pbc.kpoint_mesh,
            method=method,
            density_fit=True,
            density_fitting=spec.problem.pbc.density_fitting,
            mesh=spec.problem.pbc.mesh,
        )
    )
    env_inputs = resolve_environment_inputs(spec)
    pbc_qmmm, external_nuclear_energy, _pbc_constants, v_env_ao = _build_pbc_qmmm_summary(
        spec=spec,
        env_inputs=env_inputs,
        periodic_summary=periodic_summary,
        cell=gamma.cell,
    )
    problem = electronic_structure_problem_from_gamma_scf(
        gamma.mean_field,
        cell=gamma.cell,
        method=method,
        one_body_ao_delta=v_env_ao,
    )
    original_problem = problem
    original_num_spatial_orbitals = int(problem.num_spatial_orbitals)
    transformers_applied: list[str] = []
    removed_orbitals = [int(value) for value in spec.problem.remove_orbitals]
    frozen_core_orbitals: list[int] = []
    selection_mode = "none"
    selection_reason = "No active-space reduction requested."
    selected_active_orbitals: list[int] = []
    selected_active_orbitals_original: list[int] = []
    if spec.problem.freeze_core or removed_orbitals:
        transformer = FreezeCoreTransformer(
            freeze_core=spec.problem.freeze_core,
            remove_orbitals=removed_orbitals or None,
        )
        problem = transformer.transform(problem)
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
    active_space_summary = None
    if resolved_active_space is not None:
        transformer = ActiveSpaceTransformer(
            num_electrons=resolved_active_space.num_electrons,
            num_spatial_orbitals=resolved_active_space.num_spatial_orbitals,
            active_orbitals=resolved_active_space.active_orbitals_current or None,
        )
        problem = transformer.transform(problem)
        transformers_applied.append("ActiveSpaceTransformer")
        selection_mode = resolved_active_space.selection_mode
        selection_reason = resolved_active_space.selection_reason
        selected_active_orbitals = list(resolved_active_space.active_orbitals_current)
        selected_active_orbitals_original = list(resolved_active_space.active_orbitals_original)
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
    driver_constant_sum = float(sum(constants.values()))
    electronic_constant_correction = driver_constant_sum - nuclear_repulsion_energy
    total_constant_correction = (
        electronic_constant_correction
        + nuclear_repulsion_energy
        + external_nuclear_energy
    )
    external_summary = env_inputs.point_charges.to_summary(adapter_strategy="qcchem.pbc.ewald")
    if external_summary is not None:
        external_summary.qm_nuclear_interaction_energy = external_nuclear_energy
        external_summary.adapter_strategy = "qcchem.pbc.ewald + pbc_intor(int1e_rinv)"
    boundary_summary = BoundaryEmbeddingSummary(
        enabled=False,
        method=spec.problem.environment_embedding.boundary.method,
        localization=spec.problem.environment_embedding.boundary.localization,
        adapter_strategy="disabled_for_pbc_v1",
        verification_status="not_requested",
        risk_notes=["Covalent boundary embedding is not enabled for PBC-QM/MM v1."],
    )
    effective_hamiltonian_summary = build_effective_hamiltonian_summary(
        spec=spec,
        env_inputs=env_inputs,
        pyscf_driver=_PBCEmbeddingAuditDriver(v_env_ao),
        active_space_projection={
            "original_num_spatial_orbitals": original_num_spatial_orbitals,
            "reduced_num_spatial_orbitals": int(problem.num_spatial_orbitals),
            "num_particles": tuple(int(value) for value in problem.num_particles),
            "transformers_applied": list(transformers_applied),
            "active_space_metadata": active_space_summary,
            "environment_qubit_growth": 0,
            "periodic_boundary": to_primitive(periodic_summary),
            "pbc_qmmm": to_primitive(pbc_qmmm),
        },
        boundary_summary=boundary_summary,
        v_boundary_ao=None,
    )
    if effective_hamiltonian_summary is not None:
        effective_hamiltonian_summary.solver_surface = "periodic_gamma_qubit_hamiltonian"
        effective_hamiltonian_summary.one_body_environment.update(
            {
                "source": "qcchem.pbc pbc_intor(int1e_rinv) Gamma-point hcore delta",
                "pbc_qmmm": to_primitive(pbc_qmmm),
            }
        )
        effective_hamiltonian_summary.provenance["periodic_boundary"] = to_primitive(periodic_summary)

    point_group_metadata = {
        "status": "skipped_for_pbc",
        "reason": "Molecular point-group symmetry is not reused for periodic Gamma-only cells.",
        "pyscf_pbc": gamma.metadata,
    }
    hf_reference_energy = (
        None
        if v_env_ao is not None
        else float(problem.reference_energy) if problem.reference_energy is not None else None
    )
    fermionic_hamiltonian = problem.hamiltonian.second_q_op()
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
            periodic_boundary=periodic_summary,
            pbc_qmmm=pbc_qmmm,
        ),
        nuclear_repulsion_energy=nuclear_repulsion_energy,
        electronic_constant_correction=electronic_constant_correction,
        total_constant_correction=total_constant_correction,
        hf_reference_energy=hf_reference_energy,
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
            boundary_embedding_constant_energy=0.0,
            total_constant_correction=total_constant_correction,
            energy_formula=REDUCTION_ENERGY_FORMULA,
            point_group_metadata=point_group_metadata,
            periodic_boundary=periodic_summary,
            pbc_qmmm=pbc_qmmm,
        ),
        external_point_charges=external_summary,
        environment_embedding=effective_hamiltonian_summary,
    )


def build_electronic_structure_context(spec: RunSpec) -> ElectronicStructureContext:
    """Construct an electronic-structure problem from a QCchem spec."""
    if spec.problem.pbc.enabled:
        return build_pbc_electronic_structure_context(spec)
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
