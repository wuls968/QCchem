"""Classical plugin helpers for perturbative correction and embedding skeletons."""

from __future__ import annotations

from typing import Any

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
    """Build a PySCF RHF reference for plugin-based workflows."""
    mol = gto.M(
        atom=molecule.geometry_string(),
        basis=molecule.basis,
        charge=molecule.charge,
        spin=molecule.spin,
        unit=_pyscf_unit(molecule.unit),
        verbose=0,
    )
    mf = scf.RHF(mol).run(verbose=0)
    return mol, mf


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
    dm = mf.make_rdm1()
    ao_slices = mol.aoslice_by_atom()
    ao_labels = mol.ao_labels()
    fragments: list[dict[str, Any]] = []
    fragment_energies: list[float] = []
    for fragment in spec.fragments:
        ao_indices: list[int] = []
        for atom_index in fragment.atom_indices:
            _, _, start, stop = ao_slices[atom_index]
            ao_indices.extend(range(start, stop))
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
                fragment_atoms = [
                    molecule.geometry[index]
                    for index in fragment.atom_indices
                    if 0 <= index < len(molecule.geometry)
                ]
                if not fragment_atoms:
                    raise ValueError("fragment has no valid atoms")
                fragment_molecule = MoleculeSpec(
                    name=f"{molecule.name}:{fragment.name}",
                    geometry=fragment_atoms,
                    charge=0,
                    multiplicity=1,
                    basis=molecule.basis,
                    unit=molecule.unit,
                )
                _frag_mol, frag_mf = build_pyscf_mean_field(fragment_molecule)
                fragment_energies.append(float(frag_mf.e_tot))
                execution_result = {
                    "plugin": spec.execution.plugin,
                    "method": "pyscf_rhf",
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
    execution_validated = execution_enabled and len(fragment_energies) == len(spec.fragments) and bool(spec.fragments)

    return EmbeddingResultSummary(
        enabled=True,
        method=spec.method,
        solver_plugin=spec.solver_plugin,
        bath_threshold=spec.bath_threshold,
        fragments=fragments,
        environment_metadata={
            "environment_model": "rhf_density_matrix",
            "mean_field_energy": float(mf.e_tot),
            "num_fragments": len(fragments),
            "fragment_execution": assembled,
        },
        verification_status="validated" if execution_validated else "exploratory",
        notes=[
            "Current embedding path is a DMET-style skeleton built from PySCF mean-field density information.",
            "Fragment execution is validated only for PySCF RHF small-fragment reference runs; assembled embedding energy is a diagnostic, not a replacement for the full-system benchmark.",
        ],
    )
