"""Environment effective-Hamiltonian audit helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from qcchem.chem.external_charges import (
    ResolvedExternalPointCharges,
    resolve_external_point_charges,
)
from qcchem.core import (
    BoundaryEmbeddingSpec,
    BoundaryEmbeddingSummary,
    EffectiveHamiltonianSummary,
    EnvironmentEmbeddingSpec,
    ExternalPointChargeSpec,
    MoleculeSpec,
    RunSpec,
)
from qcchem.io.exports import workspace_fingerprint
from qcchem.io.serialization import to_primitive


@dataclass(slots=True)
class ResolvedEnvironmentInputs:
    """Resolved environment-embedding inputs for molecular Hamiltonian construction."""

    enabled: bool
    mode: str
    point_charges: ResolvedExternalPointCharges
    compatibility_notes: list[str]
    cache_enabled: bool


def _disabled_external_spec(molecule: MoleculeSpec) -> ExternalPointChargeSpec:
    return ExternalPointChargeSpec(enabled=False, unit=molecule.unit)


def _environment_point_charge_spec(env: EnvironmentEmbeddingSpec) -> ExternalPointChargeSpec:
    point = env.point_charges
    return ExternalPointChargeSpec(
        enabled=point.enabled,
        unit=point.unit,
        source_file=point.source_file,
        charges=list(point.charges),
        min_distance_to_qm_atoms=point.min_distance_to_qm_atoms,
    )


def resolve_environment_inputs(spec: RunSpec) -> ResolvedEnvironmentInputs:
    """Resolve new environment_embedding config with legacy point-charge compatibility."""
    env = spec.problem.environment_embedding
    legacy = spec.problem.external_point_charges
    notes: list[str] = []
    if env.enabled:
        if legacy.enabled and env.point_charges.enabled:
            notes.append(
                "problem.environment_embedding.point_charges takes precedence over legacy problem.external_point_charges."
            )
        point_spec = _environment_point_charge_spec(env)
        point_charges = resolve_external_point_charges(
            spec.molecule,
            point_spec,
            damping=(env.point_charges.damping if point_spec.enabled else None),
            compatibility_mode="environment_embedding.point_charges",
        )
        return ResolvedEnvironmentInputs(
            enabled=True,
            mode=env.mode,
            point_charges=point_charges,
            compatibility_notes=notes,
            cache_enabled=bool(env.cache.enabled),
        )
    if legacy.enabled:
        point_charges = resolve_external_point_charges(
            spec.molecule,
            legacy,
            damping=None,
            compatibility_mode="external_point_charges_compatibility_alias",
        )
        notes.append(
            "Legacy problem.external_point_charges was treated as an undamped environment_embedding point-charge source."
        )
        return ResolvedEnvironmentInputs(
            enabled=True,
            mode="effective_hamiltonian",
            point_charges=point_charges,
            compatibility_notes=notes,
            cache_enabled=False,
        )
    point_charges = resolve_external_point_charges(
        spec.molecule,
        _disabled_external_spec(spec.molecule),
        damping=None,
        compatibility_mode="disabled",
    )
    return ResolvedEnvironmentInputs(
        enabled=False,
        mode=env.mode,
        point_charges=point_charges,
        compatibility_notes=[],
        cache_enabled=False,
    )


def _matrix_summary(matrix: np.ndarray | None) -> dict[str, Any]:
    if matrix is None:
        return {
            "available": False,
            "shape": [],
            "frobenius_norm": 0.0,
            "max_abs": 0.0,
            "hermitian_deviation": None,
        }
    array = np.asarray(matrix, dtype=float)
    return {
        "available": True,
        "shape": [int(value) for value in array.shape],
        "frobenius_norm": float(np.linalg.norm(array)),
        "max_abs": float(np.max(np.abs(array))) if array.size else 0.0,
        "hermitian_deviation": float(np.linalg.norm(array - array.T.conj())),
    }


def _file_digest(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache_fingerprint(
    *,
    spec: RunSpec,
    env_inputs: ResolvedEnvironmentInputs,
    active_space_projection: dict[str, Any],
    matrix_shape: list[int],
) -> str:
    env = spec.problem.environment_embedding
    charge_source = env.point_charges.source_file if env.enabled else spec.problem.external_point_charges.source_file
    payload = {
        "schema": "qcchem.environment_embedding.v1",
        "molecule": to_primitive(spec.molecule),
        "basis": spec.molecule.basis,
        "active_space": to_primitive(spec.problem.active_space),
        "freeze_core": spec.problem.freeze_core,
        "remove_orbitals": spec.problem.remove_orbitals,
        "environment_embedding": to_primitive(env),
        "legacy_external_point_charges": to_primitive(spec.problem.external_point_charges),
        "resolved_point_charge_sources": env_inputs.point_charges.sources,
        "source_file_digest": _file_digest(charge_source),
        "active_space_projection": active_space_projection,
        "matrix_shape": matrix_shape,
    }
    return workspace_fingerprint([json.dumps(payload, sort_keys=True, default=str)])


def _write_cache(
    *,
    directory: Path,
    fingerprint: str,
    metadata: dict[str, Any],
    v_env_ao: np.ndarray | None,
    v_boundary_ao: np.ndarray | None,
    refresh: bool,
) -> tuple[bool, dict[str, str], dict[str, Any]]:
    directory.mkdir(parents=True, exist_ok=True)
    metadata_path = directory / f"{fingerprint}.json"
    matrix_path = directory / f"{fingerprint}.npz"
    cache_hit = metadata_path.exists() and matrix_path.exists() and not refresh
    current_env = np.asarray(v_env_ao if v_env_ao is not None else np.zeros((0, 0)))
    current_boundary = np.asarray(
        v_boundary_ao if v_boundary_ao is not None else np.zeros((0, 0))
    )
    validation: dict[str, Any] = {
        "validated": False,
        "reload_matrix_error": None,
        "boundary_reload_matrix_error": None,
        "tolerance": 1.0e-12,
    }
    if not cache_hit:
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        np.savez_compressed(
            matrix_path,
            v_env_ao=current_env,
            v_boundary_ao=current_boundary,
        )
    else:
        with np.load(matrix_path) as cached:
            cached_env = np.asarray(cached["v_env_ao"])
            cached_boundary = np.asarray(cached["v_boundary_ao"])
        if cached_env.shape != current_env.shape:
            raise ValueError(
                "Environment effective-Hamiltonian cache shape mismatch: "
                f"cached={cached_env.shape}, current={current_env.shape}."
            )
        if cached_boundary.shape != current_boundary.shape:
            raise ValueError(
                "Boundary effective-Hamiltonian cache shape mismatch: "
                f"cached={cached_boundary.shape}, current={current_boundary.shape}."
            )
        env_error = float(np.linalg.norm(cached_env - current_env))
        boundary_error = float(np.linalg.norm(cached_boundary - current_boundary))
        validation.update(
            {
                "validated": True,
                "reload_matrix_error": env_error,
                "boundary_reload_matrix_error": boundary_error,
            }
        )
        tolerance = float(validation["tolerance"])
        if env_error > tolerance or boundary_error > tolerance:
            raise ValueError(
                "Environment effective-Hamiltonian cache validation failed: "
                f"reload_matrix_error={env_error:.6e}, "
                f"boundary_reload_matrix_error={boundary_error:.6e}, tolerance={tolerance:.6e}."
            )
    return cache_hit, {
        "metadata_json": str(metadata_path),
        "matrices_npz": str(matrix_path),
    }, validation


def _boundary_atom_indices(spec: BoundaryEmbeddingSpec, molecule: MoleculeSpec) -> list[int]:
    indices: list[int] = []
    atom_count = len(molecule.geometry)
    for bond in spec.cut_bonds:
        index = int(bond.qm_atom)
        if index < 0 or index >= atom_count:
            raise ValueError(
                "problem.environment_embedding.boundary.cut_bonds qm_atom indices are zero-based "
                f"and must be in [0, {atom_count - 1}]."
            )
        indices.append(index)
    return indices


def build_boundary_embedding_summary(
    *,
    boundary_spec: BoundaryEmbeddingSpec,
    molecule: MoleculeSpec,
    pyscf_driver: Any,
    active_space_metadata: dict[str, Any] | None,
) -> tuple[BoundaryEmbeddingSummary, np.ndarray | None]:
    """Build localized-boundary diagnostics and a first-version correction matrix."""
    if not boundary_spec.enabled:
        return (
            BoundaryEmbeddingSummary(
                enabled=False,
                method=boundary_spec.method,
                localization=boundary_spec.localization,
                leakage_threshold=boundary_spec.leakage_threshold,
                adapter_strategy="disabled",
                verification_status="not_requested",
            ),
            None,
        )
    if not boundary_spec.cut_bonds:
        raise ValueError("problem.environment_embedding.boundary.enabled=true requires cut_bonds.")
    boundary_atoms = _boundary_atom_indices(boundary_spec, molecule)
    calc = getattr(pyscf_driver, "_calc", None)
    mol = getattr(pyscf_driver, "_mol", None)
    if calc is None or mol is None:
        raise ValueError("Boundary embedding requires a completed PySCF calculation.")
    mo_coeff = getattr(calc, "mo_coeff", None)
    if isinstance(mo_coeff, tuple):
        mo_coeff = mo_coeff[0]
    if mo_coeff is None:
        raise ValueError("Boundary embedding could not access PySCF molecular orbitals.")
    coeff = np.asarray(mo_coeff, dtype=float)
    overlap = np.asarray(mol.intor_symmetric("int1e_ovlp"), dtype=float)
    boundary_mask = np.zeros(overlap.shape[0], dtype=bool)
    slices = mol.aoslice_by_atom()
    for atom_index in boundary_atoms:
        start, stop = int(slices[atom_index][2]), int(slices[atom_index][3])
        boundary_mask[start:stop] = True
    boundary_rows = overlap[boundary_mask, :]
    populations = np.abs(np.einsum("ai,ai->i", coeff[boundary_mask, :], boundary_rows @ coeff))
    selected_boundary_orbitals = [
        int(index)
        for index, value in enumerate(populations)
        if value >= boundary_spec.leakage_threshold
    ]
    active_orbitals = None
    if active_space_metadata:
        raw_active = active_space_metadata.get("active_orbitals_original") or active_space_metadata.get("active_orbitals")
        if raw_active:
            active_orbitals = [int(value) for value in raw_active]
    if active_orbitals:
        leakage_values = [
            float(populations[index])
            for index in active_orbitals
            if 0 <= index < len(populations)
        ]
    else:
        leakage_values = [float(value) for value in populations]
    max_leakage = max(leakage_values) if leakage_values else 0.0
    if boundary_spec.strict and max_leakage > boundary_spec.leakage_threshold:
        raise ValueError(
            "Boundary orbital leakage exceeds threshold: "
            f"max_boundary_leakage={max_leakage:.6f}, "
            f"threshold={boundary_spec.leakage_threshold:.6f}."
        )
    correction = np.zeros_like(overlap)
    summary = BoundaryEmbeddingSummary(
        enabled=True,
        method=boundary_spec.method,
        localization=boundary_spec.localization,
        cut_bonds=[
            {
                "label": bond.label,
                "qm_atom": bond.qm_atom,
                "mm_atom": bond.mm_atom,
            }
            for bond in boundary_spec.cut_bonds
        ],
        leakage_threshold=float(boundary_spec.leakage_threshold),
        max_boundary_leakage=float(max_leakage),
        selected_boundary_orbitals=selected_boundary_orbitals,
        correction_frobenius_norm=float(np.linalg.norm(correction)),
        constant_energy=0.0,
        adapter_strategy="localized_boundary_orbital_diagnostic_gate",
        verification_status="exploratory",
        provenance={
            "atom_indexing": "zero_based",
            "boundary_ao_count": int(np.count_nonzero(boundary_mask)),
            "population_metric": "abs_mulliken_mo_population_on_declared_qm_boundary_atoms",
            "correction_matrix": "zero_first_version",
        },
        risk_notes=[
            "Boundary embedding currently diagnoses localized boundary leakage and avoids link atoms.",
            "First implementation does not add a nonzero downfolding correction unless a future boundary projector plugin supplies one.",
        ],
    )
    return summary, correction


def build_effective_hamiltonian_summary(
    *,
    spec: RunSpec,
    env_inputs: ResolvedEnvironmentInputs,
    pyscf_driver: Any,
    active_space_projection: dict[str, Any],
    boundary_summary: BoundaryEmbeddingSummary,
    v_boundary_ao: np.ndarray | None,
) -> EffectiveHamiltonianSummary | None:
    """Build and optionally cache the environment effective-Hamiltonian audit."""
    if not env_inputs.enabled:
        return None
    v_env_ao = getattr(pyscf_driver, "external_point_charge_potential_matrix_ao", None)
    env_matrix_summary = _matrix_summary(v_env_ao)
    env = spec.problem.environment_embedding
    cache_fingerprint = _cache_fingerprint(
        spec=spec,
        env_inputs=env_inputs,
        active_space_projection=active_space_projection,
        matrix_shape=list(env_matrix_summary.get("shape") or []),
    )
    cache_hit = False
    cache_paths: dict[str, str] = {}
    cache_enabled = bool(env.enabled and env.cache.enabled)
    metadata = {
        "schema": "qcchem.environment_effective_hamiltonian.v1",
        "fingerprint": cache_fingerprint,
        "one_body_environment": env_matrix_summary,
        "boundary": to_primitive(boundary_summary),
        "active_space_projection": active_space_projection,
        "point_charge_sources": env_inputs.point_charges.sources,
        "damping_model": env_inputs.point_charges.damping_model,
    }
    if cache_enabled:
        cache_hit, cache_paths, cache_validation = _write_cache(
            directory=env.cache.directory,
            fingerprint=cache_fingerprint,
            metadata=metadata,
            v_env_ao=v_env_ao,
            v_boundary_ao=v_boundary_ao,
            refresh=env.cache.refresh,
        )
    else:
        cache_validation = {}
    return EffectiveHamiltonianSummary(
        enabled=True,
        mode=env.mode if env.enabled else env_inputs.mode,
        solver_surface="molecular_qubit_hamiltonian",
        cache_enabled=cache_enabled,
        cache_hit=cache_hit,
        cache_fingerprint=cache_fingerprint,
        cache_paths=cache_paths,
        cache_validation=cache_validation,
        one_body_environment={
            **env_matrix_summary,
            "source": "pyscf.qmmm.mm_charge hcore delta",
            "damping_model": env_inputs.point_charges.damping_model,
        },
        boundary=boundary_summary,
        active_space_projection=active_space_projection,
        provenance={
            "builder": "qcchem.chem.effective_hamiltonian",
            "compatibility_notes": list(env_inputs.compatibility_notes),
            "mm_environment_quantized": False,
            "active_space_qubit_growth_from_environment": 0,
        },
        risk_notes=[
            "The MM environment is represented as fixed classical sources compressed into the active-space Hamiltonian.",
            "MM-MM, van der Waals, explicit polarization response, and environment relaxation are not included.",
            *env_inputs.compatibility_notes,
        ],
    )
