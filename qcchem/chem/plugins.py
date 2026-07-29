"""Classical plugin helpers for perturbative correction and embedding skeletons."""

from __future__ import annotations

from typing import Any

import numpy as np
from pyscf import gto, mrpt, scf
from pyscf.mcscf import CASCI, addons, dmet_cas

from qcchem.core import (
    EmbeddingResultSummary,
    EmbeddingSpec,
    MoleculeSpec,
    PerturbativeCorrectionResultSummary,
    PerturbativeCorrectionTaskSpec,
    ReductionAuditSummary,
)


def _pyscf_unit(unit: str) -> str:
    normalized = unit.strip().lower()
    if normalized in {"angstrom", "ang", "a"}:
        return "Angstrom"
    if normalized in {"bohr", "au"}:
        return "Bohr"
    raise ValueError(f"Unsupported PySCF unit: {unit}")


def build_pyscf_mean_field(molecule: MoleculeSpec):
    """Build a PySCF mean-field reference for plugin-based workflows."""
    mol = gto.M(
        atom=molecule.geometry_string(),
        basis=molecule.basis,
        charge=molecule.charge,
        spin=molecule.spin,
        unit=_pyscf_unit(molecule.unit),
        verbose=0,
    )
    mf = (scf.RHF(mol) if molecule.spin == 0 else scf.UHF(mol)).run(verbose=0)
    return mol, mf


def _neutral_fragment_electron_count(atoms: list[Any]) -> int:
    return int(sum(int(gto.charge(atom.symbol)) for atom in atoms))


def _default_neutral_fragment_multiplicity(atoms: list[Any]) -> int:
    electron_count = _neutral_fragment_electron_count(atoms)
    return 2 if electron_count % 2 else 1


def _spin_summed_density_matrix(dm) -> np.ndarray:
    values = np.asarray(dm, dtype=float)
    if values.ndim == 3:
        return np.sum(values, axis=0)
    return values


def _fragment_gross_population(
    dm: np.ndarray,
    overlap: np.ndarray,
    ao_indices: list[int],
) -> float:
    if not ao_indices:
        return 0.0
    rows = np.asarray(ao_indices, dtype=int)
    columns = range(dm.shape[0])
    return float(
        np.einsum(
            "ij,ij->",
            dm[np.ix_(rows, columns)],
            overlap[np.ix_(rows, columns)],
        )
    )


def run_nevpt2_correction(
    molecule: MoleculeSpec,
    reduction_audit: ReductionAuditSummary | None,
    task: PerturbativeCorrectionTaskSpec,
    *,
    reduced_active_space_energy: float | None = None,
    compressed_active_space_energy: float | None = None,
) -> PerturbativeCorrectionResultSummary | None:
    """Run a PySCF-backed NEVPT2 correction when an active space is available."""
    if not task.enabled:
        return None
    if reduction_audit is None or reduction_audit.active_space_metadata is None:
        return PerturbativeCorrectionResultSummary(
            enabled=True,
            method=task.method,
            plugin=task.plugin,
            active_space_energy=0.0,
            perturbative_correction=0.0,
            corrected_total_energy=0.0,
            reduced_active_space_energy=reduced_active_space_energy,
            compressed_active_space_energy=compressed_active_space_energy,
            verification_status="exploratory",
            provenance={"source": "placeholder", "reason": "active_space_required"},
            notes=["NEVPT2 correction requires an active-space specification."],
        )

    if task.method.strip().lower() != "nevpt2":
        return PerturbativeCorrectionResultSummary(
            enabled=True,
            method=task.method,
            plugin=task.plugin,
            active_space_energy=0.0,
            perturbative_correction=0.0,
            corrected_total_energy=0.0,
            reduced_active_space_energy=reduced_active_space_energy,
            compressed_active_space_energy=compressed_active_space_energy,
            verification_status="exploratory",
            provenance={"source": "placeholder", "reason": "unsupported_method"},
            notes=[f"Unsupported perturbative correction method: {task.method}"],
        )

    mol, mf = build_pyscf_mean_field(molecule)
    active_meta = reduction_audit.active_space_metadata
    num_spatial_orbitals = int(active_meta["num_spatial_orbitals"])
    num_electrons = active_meta["num_electrons"]
    mc = CASCI(mf, num_spatial_orbitals, num_electrons)
    mo = mf.mo_coeff
    if reduction_audit.selected_active_orbitals_original:
        mo = addons.sort_mo(mc, mf.mo_coeff, reduction_audit.selected_active_orbitals_original, base=0)
    mc.kernel(mo)
    correction = float(mrpt.NEVPT(mc, root=task.root).kernel())
    active_space_energy = float(mc.e_tot)
    compressed_energy = compressed_active_space_energy if compressed_active_space_energy is not None else active_space_energy
    return PerturbativeCorrectionResultSummary(
        enabled=True,
        method="nevpt2",
        plugin=task.plugin,
        active_space_energy=compressed_energy,
        perturbative_correction=correction,
        corrected_total_energy=float(compressed_energy + correction),
        reduced_active_space_energy=(
            reduced_active_space_energy if reduced_active_space_energy is not None else active_space_energy
        ),
        compressed_active_space_energy=compressed_active_space_energy,
        verification_status="validated",
        provenance={
            "source": "pyscf.mrpt.nevpt2",
            "root": task.root,
            "selected_active_orbitals_original": reduction_audit.selected_active_orbitals_original,
            "reduced_active_space_energy": reduced_active_space_energy,
            "compressed_active_space_energy": compressed_active_space_energy,
        },
        notes=[
            "PySCF NEVPT2 plugin path; validated as a classical-reference correction within QCchem v0.6 scope.",
            "When compression-aware execution is enabled, the perturbative correction is sourced from the classical reduced active space and applied to the compressed active-space energy for reporting.",
        ],
    )


def build_embedding_result(
    molecule: MoleculeSpec,
    spec: EmbeddingSpec,
) -> EmbeddingResultSummary | None:
    """Build a DMET-style embedding skeleton using PySCF density information."""
    if not spec.enabled:
        return None
    mol, mf = build_pyscf_mean_field(molecule)
    dm = _spin_summed_density_matrix(mf.make_rdm1())
    overlap = np.asarray(mf.get_ovlp(), dtype=float)
    ao_slices = mol.aoslice_by_atom()
    ao_labels = mol.ao_labels()
    fragments: list[dict[str, Any]] = []
    fragment_energies: list[float] = []
    fragment_density_audits: list[dict[str, Any]] = []
    all_fragment_ao_indices: list[int] = []
    all_fragment_atom_indices: list[int] = []
    for fragment in spec.fragments:
        ao_indices: list[int] = []
        for atom_index in fragment.atom_indices:
            _, _, start, stop = ao_slices[atom_index]
            ao_indices.extend(range(start, stop))
        all_fragment_ao_indices.extend(ao_indices)
        all_fragment_atom_indices.extend(fragment.atom_indices)
        fragment_atoms = [
            molecule.geometry[index]
            for index in fragment.atom_indices
            if 0 <= index < len(molecule.geometry)
        ]
        neutral_electrons = _neutral_fragment_electron_count(fragment_atoms)
        full_population = _fragment_gross_population(dm, overlap, ao_indices)
        population_delta = float(full_population - neutral_electrons)
        fragment_density_audits.append(
            {
                "fragment": fragment.name,
                "atom_indices": list(fragment.atom_indices),
                "ao_indices": list(ao_indices),
                "full_system_gross_population": full_population,
                "neutral_fragment_electron_count": neutral_electrons,
                "population_delta": population_delta,
                "population_delta_abs": abs(population_delta),
                "status": "reference_audit_only",
                "density_matching_performed": False,
            }
        )
        try:
            ncas, nelecas, _ = dmet_cas.guess_cas(
                mf,
                dm,
                ao_indices,
                threshold=spec.bath_threshold,
                base=0,
                verbose=0,
            )
            recommendation = {
                "num_spatial_orbitals": int(ncas),
                "num_electrons": nelecas,
            }
        except Exception as exc:  # pragma: no cover - defensive plugin boundary
            recommendation = {"error": f"{type(exc).__name__}: {exc}"}
        execution_result: dict[str, Any] | None = None
        if spec.execution.enabled:
            try:
                if not fragment_atoms:
                    raise ValueError("fragment has no valid atoms")
                fragment_charge = 0
                fragment_multiplicity = _default_neutral_fragment_multiplicity(fragment_atoms)
                fragment_molecule = MoleculeSpec(
                    name=f"{molecule.name}:{fragment.name}",
                    geometry=fragment_atoms,
                    charge=fragment_charge,
                    multiplicity=fragment_multiplicity,
                    basis=molecule.basis,
                    unit=molecule.unit,
                )
                _frag_mol, frag_mf = build_pyscf_mean_field(fragment_molecule)
                fragment_energies.append(float(frag_mf.e_tot))
                execution_result = {
                    "plugin": spec.execution.plugin,
                    "method": "pyscf_rhf" if fragment_molecule.spin == 0 else "pyscf_uhf",
                    "fragment_charge": fragment_charge,
                    "fragment_multiplicity": fragment_multiplicity,
                    "fragment_spin": fragment_molecule.spin,
                    "neutral_fragment_charge_assumed": True,
                    "total_energy": float(frag_mf.e_tot),
                    "verification_status": "validated",
                }
            except Exception as exc:  # pragma: no cover - defensive plugin boundary
                execution_result = {
                    "plugin": spec.execution.plugin,
                    "verification_status": "exploratory",
                    "error": f"{type(exc).__name__}: {exc}",
                }
        fragments.append(
            {
                "name": fragment.name,
                "atom_indices": list(fragment.atom_indices),
                "solver": fragment.solver or spec.solver_plugin,
                "ao_count": len(ao_indices),
                "ao_labels": [ao_labels[index] for index in ao_indices],
                "recommended_active_space": recommendation,
                "execution_result": execution_result,
            }
        )
    execution_enabled = bool(spec.execution.enabled)
    assembled = {
        "execution_enabled": execution_enabled,
        "plugin": spec.execution.plugin,
        "fragment_energy_sum": float(sum(fragment_energies)) if fragment_energies else None,
        "full_system_mean_field_energy": float(mf.e_tot),
        "fragment_count_executed": len(fragment_energies),
        "validate_against_full_system": spec.execution.validate_against_full_system,
    }
    execution_validated = (
        execution_enabled
        and len(fragment_energies) == len(spec.fragments)
        and bool(spec.fragments)
    )
    population_deltas = [
        float(item["population_delta"]) for item in fragment_density_audits
    ]
    population_delta_abs_values = [abs(value) for value in population_deltas]
    density_population_delta_norm = (
        float(np.linalg.norm(population_deltas))
        if fragment_density_audits
        else None
    )
    density_population_delta_l1_norm = (
        float(sum(population_delta_abs_values)) if population_delta_abs_values else None
    )
    density_population_delta_signed_sum = (
        float(sum(population_deltas)) if population_deltas else None
    )
    max_fragment_population_delta_abs = (
        float(max(population_delta_abs_values)) if population_delta_abs_values else None
    )
    density_mismatch_threshold = 1.0e-8
    density_mismatch_status = (
        "balanced_reference_density"
        if density_population_delta_norm is not None
        and density_population_delta_norm <= density_mismatch_threshold
        else "mismatch_observed"
        if density_population_delta_norm is not None
        else "not_evaluated"
    )
    unique_fragment_ao_indices = sorted(set(all_fragment_ao_indices))
    unique_fragment_atom_indices = sorted(
        index
        for index in set(all_fragment_atom_indices)
        if 0 <= index < len(molecule.geometry)
    )
    total_ao_count = len(ao_labels)
    total_atom_count = len(molecule.geometry)
    fragment_coverage_audit = {
        "total_ao_count": total_ao_count,
        "covered_ao_count": len(unique_fragment_ao_indices),
        "unassigned_ao_count": max(total_ao_count - len(unique_fragment_ao_indices), 0),
        "overlapping_ao_assignment_count": max(
            len(all_fragment_ao_indices) - len(unique_fragment_ao_indices),
            0,
        ),
        "ao_coverage_fraction": (
            float(len(unique_fragment_ao_indices) / total_ao_count)
            if total_ao_count
            else None
        ),
        "total_atom_count": total_atom_count,
        "covered_atom_count": len(unique_fragment_atom_indices),
        "unassigned_atom_count": max(
            total_atom_count - len(unique_fragment_atom_indices),
            0,
        ),
        "overlapping_atom_assignment_count": max(
            len(all_fragment_atom_indices) - len(unique_fragment_atom_indices),
            0,
        ),
        "atom_coverage_fraction": (
            float(len(unique_fragment_atom_indices) / total_atom_count)
            if total_atom_count
            else None
        ),
        "status": (
            "complete_nonoverlapping_fragment_coverage"
            if total_ao_count
            and len(unique_fragment_ao_indices) == total_ao_count
            and len(all_fragment_ao_indices) == len(unique_fragment_ao_indices)
            else "partial_or_overlapping_fragment_coverage"
        ),
    }
    density_mismatch_audit = {
        "metric": "fragment_population_delta",
        "l2_norm": density_population_delta_norm,
        "l1_norm": density_population_delta_l1_norm,
        "signed_sum": density_population_delta_signed_sum,
        "max_abs": max_fragment_population_delta_abs,
        "threshold": density_mismatch_threshold,
        "status": density_mismatch_status,
        "density_matching_performed": False,
        "density_matching_iteration_count": 0,
        "self_consistency_iteration_count": 0,
    }
    fragment_energy_sum = assembled["fragment_energy_sum"]
    fragment_energy_gap = (
        float(fragment_energy_sum - float(mf.e_tot))
        if fragment_energy_sum is not None
        else None
    )
    fragment_energy_gap_abs = abs(fragment_energy_gap) if fragment_energy_gap is not None else None
    fragment_energy_gap_per_fragment = (
        float(fragment_energy_gap / len(fragments))
        if fragment_energy_gap is not None and fragments
        else None
    )
    environment_metadata = {
        "environment_model": "mean_field_density_matrix",
        "mean_field_energy": float(mf.e_tot),
        "num_fragments": len(fragments),
        "fragment_execution": assembled,
    }
    notes = [
        "Current embedding path is a DMET-style skeleton built from PySCF mean-field density information.",
        "Fragment execution is validated only for PySCF RHF/UHF small-fragment reference runs; assembled embedding energy is a diagnostic, not a replacement for the full-system benchmark.",
    ]
    if spec.method.strip().lower() == "q_dmet":
        environment_metadata.update(
            {
                "embedding_method": "q_dmet",
                "embedding_execution_status": "fragment_reference_only",
                "bath_orbitals": [
                    {
                        "fragment": item["name"],
                        "recommended_active_space": item.get("recommended_active_space"),
                    }
                    for item in fragments
                ],
                "density_mismatch_history": [
                    {
                        "macro_iteration": 0,
                        "density_mismatch_norm": density_population_delta_norm,
                        "density_mismatch_l1_norm": density_population_delta_l1_norm,
                        "density_mismatch_signed_sum": density_population_delta_signed_sum,
                        "max_fragment_population_delta_abs": max_fragment_population_delta_abs,
                        "density_mismatch_threshold": density_mismatch_threshold,
                        "metric": "fragment_population_delta_norm",
                        "status": "reference_audit_only",
                        "mismatch_status": density_mismatch_status,
                        "reason": "q-DMET self-consistency loop is not implemented in v1; this is a one-shot fragment population audit.",
                    }
                ],
                "density_mismatch_audit": density_mismatch_audit,
                "fragment_coverage_audit": fragment_coverage_audit,
                "fragment_density_audit": fragment_density_audits,
                "self_consistency_loop_executed": False,
                "self_consistency_converged": False,
                "self_consistency_iteration_count": 0,
                "density_matching_iteration_count": 0,
                "correlation_potential_parameter_count": 0,
                "embedding_boundary_audit": {
                    "fragment_count": len(fragments),
                    "bath_threshold": spec.bath_threshold,
                    "assembled_energy_replaces_primary": False,
                    "fragment_energy_sum_replaces_primary": False,
                    "fragment_reference_execution_validated": bool(execution_validated),
                    "fragment_population_delta_norm": density_population_delta_norm,
                    "fragment_population_delta_l1_norm": density_population_delta_l1_norm,
                    "fragment_population_delta_signed_sum": density_population_delta_signed_sum,
                    "max_fragment_population_delta_abs": max_fragment_population_delta_abs,
                    "density_mismatch_status": density_mismatch_status,
                    "fragment_energy_sum_gap_hartree": fragment_energy_gap,
                    "fragment_energy_sum_gap_abs_hartree": fragment_energy_gap_abs,
                    "fragment_energy_sum_gap_per_fragment_hartree": fragment_energy_gap_per_fragment,
                    "self_consistency_loop_executed": False,
                    "self_consistency_iteration_count": 0,
                    "density_matching_performed": False,
                    "density_matching_iteration_count": 0,
                    "correlation_potential_optimized": False,
                    "correlation_potential_parameter_count": 0,
                    "fragment_ao_coverage_fraction": fragment_coverage_audit[
                        "ao_coverage_fraction"
                    ],
                    "fragment_atom_coverage_fraction": fragment_coverage_audit[
                        "atom_coverage_fraction"
                    ],
                    "fragment_coverage_status": fragment_coverage_audit["status"],
                    "missing_self_consistency_components": [
                        "correlation_potential_optimizer",
                        "density_matching_loop",
                        "bath_update_loop",
                    ],
                    "trust_gate": "exploratory",
                },
                "fragment_solvers": {
                    item["name"]: item.get("solver") for item in fragments
                },
            }
        )
        notes.extend(
            [
                "Q-Embed/q-DMET v1 records fragment, bath, and optional fragment-reference diagnostics only.",
                "No q-DMET self-consistency, density matching, or correlation-potential optimization is executed in v1.",
                "Fragment reference energies are diagnostics and do not replace the primary full-system energy.",
            ]
        )

    return EmbeddingResultSummary(
        enabled=True,
        method=spec.method,
        solver_plugin=spec.solver_plugin,
        bath_threshold=spec.bath_threshold,
        fragments=fragments,
        environment_metadata=environment_metadata,
        verification_status=(
            "validated"
            if execution_validated and spec.method.strip().lower() != "q_dmet"
            else "exploratory"
        ),
        notes=notes,
    )
