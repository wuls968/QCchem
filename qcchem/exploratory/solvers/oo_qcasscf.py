"""Exploratory orbital-optimized QCASSCF wrapper."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
from pyscf import mcscf

from qcchem.chem.plugins import build_pyscf_mean_field
from qcchem.solvers import build_solver as build_core_solver
from qcchem.solvers.base import BaseSolver, SolverOutcome


class OOQCASSCFSolver(BaseSolver):
    """OO-QCASSCF v1 wrapper around the existing QCchem VQE path."""

    def __init__(self, delegate: BaseSolver, spec, problem_summary=None, run_spec=None) -> None:
        self._delegate = delegate
        self._spec = spec
        self._problem_summary = problem_summary
        self._run_spec = run_spec

    def _active_space_shape(self, mo_count: int) -> tuple[int, int | tuple[int, int]]:
        active_meta = (
            dict(getattr(self._problem_summary, "active_space_metadata", {}) or {})
            if self._problem_summary is not None
            else {}
        )
        num_spatial_orbitals = active_meta.get("num_spatial_orbitals")
        num_electrons = active_meta.get("num_electrons")
        if num_spatial_orbitals is None:
            num_spatial_orbitals = getattr(self._problem_summary, "num_spatial_orbitals", mo_count)
        if num_electrons is None:
            particles = getattr(self._problem_summary, "num_particles", None)
            if isinstance(particles, tuple) and len(particles) == 2:
                num_electrons = tuple(int(value) for value in particles)
            else:
                num_electrons = int(getattr(getattr(self._run_spec, "molecule", None), "charge", 0) or 0)
        ncas = max(1, min(int(num_spatial_orbitals), int(mo_count)))
        return ncas, num_electrons

    def _casscf_reference(self) -> dict[str, Any]:
        oo = self._spec.orbital_optimization
        if self._run_spec is None:
            return {
                "status": "unavailable",
                "reason": "full RunSpec was not provided to the exploratory solver",
                "energy_replaces_primary": False,
            }
        try:
            _mol, mf = build_pyscf_mean_field(self._run_spec.molecule)
            mo_coeff = np.asarray(mf.mo_coeff)
            ncas, nelecas = self._active_space_shape(int(mo_coeff.shape[-1]))
            mc = mcscf.CASSCF(mf, ncas, nelecas)
            mc.max_cycle_macro = max(int(oo.max_macro_iterations), 1)
            mc.conv_tol_grad = float(oo.gradient_tolerance)
            casscf_total_energy = float(mc.kernel()[0])
            optimized_mo = np.asarray(mc.mo_coeff)
            rotation_norm = float(np.linalg.norm(optimized_mo - mo_coeff))
            mean_field_total_energy = float(mf.e_tot)
            nuclear_repulsion_energy = float(mf.mol.energy_nuc())
            mean_field_electronic_energy = float(mean_field_total_energy - nuclear_repulsion_energy)
            casscf_electronic_energy = float(casscf_total_energy - nuclear_repulsion_energy)
            total_delta = float(casscf_total_energy - mean_field_total_energy)
            electronic_delta = float(casscf_electronic_energy - mean_field_electronic_energy)
            energy_lowering = max(float(-total_delta), 0.0)
            lowering_status = (
                "lowered"
                if total_delta < -1.0e-10
                else "raised"
                if total_delta > 1.0e-10
                else "unchanged_within_tolerance"
            )
            return {
                "status": "computed",
                "backend": "pyscf.mcscf.CASSCF",
                "energy_scope": "molecular_total_energy",
                "mean_field_energy_hartree": mean_field_total_energy,
                "mean_field_total_energy_hartree": mean_field_total_energy,
                "mean_field_electronic_energy_hartree": mean_field_electronic_energy,
                "casscf_reference_energy_hartree": casscf_total_energy,
                "casscf_total_energy_hartree": casscf_total_energy,
                "casscf_electronic_energy_hartree": casscf_electronic_energy,
                "energy_lowering_hartree": energy_lowering,
                "mean_field_to_casscf_total_delta_hartree": total_delta,
                "mean_field_to_casscf_electronic_delta_hartree": electronic_delta,
                "energy_lowering_status": lowering_status,
                "orbital_rotation_norm": rotation_norm,
                "converged": bool(getattr(mc, "converged", False)),
                "ncas": int(ncas),
                "nelecas": nelecas,
                "nuclear_repulsion_energy_hartree": nuclear_repulsion_energy,
                "macro_iteration_limit": int(mc.max_cycle_macro),
                "gradient_tolerance": float(oo.gradient_tolerance),
                "rdm_source": oo.rdm_source,
                "energy_replaces_primary": False,
                "active_space_changed": False,
                "active_space_resolve_status": "not_applied_to_primary_solver",
            }
        except Exception as exc:  # pragma: no cover - defensive PySCF boundary
            return {
                "status": "unavailable",
                "backend": "pyscf.mcscf.CASSCF",
                "reason": f"{type(exc).__name__}: {exc}",
                "energy_replaces_primary": False,
                "active_space_resolve_status": "not_run",
            }

    def solve(self, operator) -> SolverOutcome:
        outcome = self._delegate.solve(operator)
        oo = self._spec.orbital_optimization
        reference = self._casscf_reference()
        lowering = float(reference.get("energy_lowering_hartree") or 0.0)
        rotation_norm = float(reference.get("orbital_rotation_norm") or 0.0)
        nuclear_repulsion = reference.get("nuclear_repulsion_energy_hartree")
        electronic_constant = float(
            getattr(self._problem_summary, "electronic_constant_correction", 0.0) or 0.0
        )
        primary_hamiltonian_energy = float(outcome.total_energy)
        primary_total_estimate = None
        if nuclear_repulsion is not None:
            primary_total_estimate = float(
                primary_hamiltonian_energy + electronic_constant + float(nuclear_repulsion)
            )
        casscf_total = reference.get("casscf_total_energy_hartree")
        casscf_electronic = reference.get("casscf_electronic_energy_hartree")
        total_gap = (
            float(casscf_total) - primary_total_estimate
            if casscf_total is not None and primary_total_estimate is not None
            else None
        )
        total_abs_gap = abs(float(total_gap)) if total_gap is not None else None
        reference_lower_than_primary = bool(total_gap < 0.0) if total_gap is not None else None
        active_meta = (
            dict(getattr(self._problem_summary, "active_space_metadata", {}) or {})
            if self._problem_summary is not None
            else {}
        )
        readiness_blockers = [
            "optimized_orbitals_not_applied_to_primary_solver",
            "primary_hamiltonian_not_rebuilt_from_optimized_orbitals",
            "casscf_reference_energy_scope_differs_from_solver_energy",
            "oo_qcasscf_solver_replacement_benchmark_gate_missing",
        ]
        required_promotion_evidence = [
            "optimized-orbital one- and two-electron integral transformation",
            "QCchem Hamiltonian rebuild from optimized orbitals",
            "primary solver re-run on optimized-orbital Hamiltonian",
            "energy-scope matched benchmark against exact/reference data",
            "separate promotion gate allowing solver-energy replacement",
        ]
        energy_scope_audit = {
            "primary_solver_energy_scope": "solver_hamiltonian_energy",
            "primary_total_energy_estimate_formula": (
                "delegated_solver_hamiltonian_energy_hartree + "
                "electronic_constant_correction_hartree + nuclear_repulsion_energy_hartree"
            ),
            "casscf_reference_energy_scope": reference.get("energy_scope", "molecular_total_energy"),
            "energy_scope_consistent_for_total_gap": bool(total_gap is not None),
            "energy_replaces_primary": False,
            "solver_replacement_allowed": False,
            "reason": (
                "PySCF CASSCF e_tot is a molecular total energy; QCchem solver_energy is a solver "
                "Hamiltonian energy, so v1 records an explicit total-energy estimate before comparison."
            ),
        }
        orbital_transfer_audit = {
            "schema": "qcchem.oo_qcasscf_orbital_transfer_audit.v1",
            "status": "reference_orbitals_not_transferred_to_primary_solver",
            "optimized_orbitals_available": bool(reference.get("status") == "computed"),
            "optimized_orbitals_applied_to_primary_solver": False,
            "primary_hamiltonian_rebuilt_from_optimized_orbitals": False,
            "primary_solver_rerun_on_optimized_orbitals": False,
            "delegated_solver_kind": "vqe",
            "active_space_metadata_available": bool(active_meta),
            "rotation_blocks_requested": {
                "active_active": bool(oo.active_active),
                "inactive_active": bool(oo.inactive_active),
                "active_virtual": bool(oo.active_virtual),
            },
            "rdm_source": oo.rdm_source,
            "orbital_rotation_norm": rotation_norm,
            "missing_transfer_components": [
                "optimized-orbital integral transformation",
                "QCchem Hamiltonian rebuild from optimized orbitals",
                "primary solver re-run on optimized-orbital Hamiltonian",
            ],
            "energy_replaces_primary": False,
        }
        promotion_readiness_audit = {
            "schema": "qcchem.oo_qcasscf_promotion_readiness.v1",
            "status": "blocked_reference_diagnostic_only",
            "readiness_level": "reference_diagnostic_not_solver_replacement",
            "solver_replacement_allowed": False,
            "energy_replacement_allowed": False,
            "accuracy_claim_allowed": False,
            "optimized_orbitals_applied_to_primary_solver": False,
            "primary_hamiltonian_rebuilt_from_optimized_orbitals": False,
            "energy_scope_consistent_for_total_gap": bool(total_gap is not None),
            "promotion_blockers": readiness_blockers,
            "promotion_blocker_count": len(readiness_blockers),
            "required_promotion_evidence": required_promotion_evidence,
            "required_promotion_evidence_count": len(required_promotion_evidence),
        }
        macro_iterations = [
            {
                "macro_iteration": 1,
                "status": reference.get("status"),
                "backend": reference.get("backend"),
                "mean_field_energy_hartree": reference.get("mean_field_energy_hartree"),
                "mean_field_total_energy_hartree": reference.get("mean_field_total_energy_hartree"),
                "mean_field_electronic_energy_hartree": reference.get(
                    "mean_field_electronic_energy_hartree"
                ),
                "casscf_reference_energy_hartree": reference.get("casscf_reference_energy_hartree"),
                "casscf_total_energy_hartree": casscf_total,
                "casscf_electronic_energy_hartree": casscf_electronic,
                "energy_lowering_hartree": reference.get("energy_lowering_hartree"),
                "mean_field_to_casscf_total_delta_hartree": reference.get(
                    "mean_field_to_casscf_total_delta_hartree"
                ),
                "orbital_rotation_norm": reference.get("orbital_rotation_norm"),
                "converged": reference.get("converged"),
            }
        ]
        metadata = dict(outcome.metadata)
        metadata.update(
            {
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "oo_qcasscf_pyscf_reference_diagnostic_v1",
                "scientific_risk_notes": [
                    "OO-QCASSCF v1 records a PySCF CASSCF orbital-relaxation reference diagnostic around the delegated VQE path.",
                    "The delegated VQE solver energy remains the primary solver energy in v1.",
                ],
                "delegated_execution": "vqe",
                "orbital_optimization": {
                    "macro_iterations": macro_iterations,
                    "orbital_rotation_norm": rotation_norm,
                    "rdm_source": oo.rdm_source,
                    "energy_lowering_hartree": lowering,
                    "active_space_changed": False,
                    "active_space_metadata": active_meta,
                    "reference_diagnostics": reference,
                    "active_space_resolve": {
                        "status": reference.get("active_space_resolve_status", "not_applied_to_primary_solver"),
                        "qcchem_primary_solver_kind": "vqe",
                        "delegated_solver_energy_hartree": primary_hamiltonian_energy,
                        "delegated_solver_hamiltonian_energy_hartree": primary_hamiltonian_energy,
                        "electronic_constant_correction_hartree": electronic_constant,
                        "nuclear_repulsion_energy_hartree": nuclear_repulsion,
                        "delegated_solver_total_energy_estimate_hartree": primary_total_estimate,
                        "casscf_reference_energy_hartree": reference.get("casscf_reference_energy_hartree"),
                        "casscf_reference_total_energy_hartree": casscf_total,
                        "casscf_reference_electronic_energy_hartree": casscf_electronic,
                        "casscf_minus_primary_total_energy_hartree": total_gap,
                        "abs_casscf_primary_total_gap_hartree": total_abs_gap,
                        "casscf_reference_lower_than_primary_total": reference_lower_than_primary,
                        "energy_scope_audit": energy_scope_audit,
                        "orbital_transfer_audit": orbital_transfer_audit,
                        "promotion_readiness_audit": promotion_readiness_audit,
                        "optimized_orbitals_applied_to_primary_solver": False,
                        "primary_hamiltonian_rebuilt_from_optimized_orbitals": False,
                        "solver_replacement_allowed": False,
                        "energy_replaces_primary": False,
                    },
                    "orbital_transfer_audit": orbital_transfer_audit,
                    "energy_scope_audit": energy_scope_audit,
                    "promotion_readiness_audit": promotion_readiness_audit,
                    "energy_replaces_primary": False,
                    "trust_gate": "exploratory",
                },
            }
        )
        return SolverOutcome(
            total_energy=outcome.total_energy,
            converged=outcome.converged,
            iterations=outcome.iterations,
            evaluations=outcome.evaluations,
            optimal_parameters=outcome.optimal_parameters,
            metadata=metadata,
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None, run_spec=None) -> BaseSolver:
    delegate_spec = replace(spec, kind="vqe", experimental=False)
    delegate = build_core_solver(
        delegate_spec,
        backend=backend,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
    return OOQCASSCFSolver(delegate, spec, problem_summary=problem_summary, run_spec=run_spec)
