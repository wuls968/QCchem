"""CAST-QC transcorrelated Hamiltonian plugin interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit_nature.second_q.operators.symmetric_two_body import unfold

from qcchem.chem.compression import _extract_raw_integrals
from qcchem.mapping import map_fermionic_hamiltonian


@dataclass(slots=True)
class CastHamiltonianBuild:
    """Hermitian CAST Hamiltonian used for quantum kicking."""

    operator: SparsePauliOp
    audit: dict[str, Any]


def _operator_frobenius_norm(operator: SparsePauliOp) -> float:
    if operator.num_qubits <= 12:
        return float(np.linalg.norm(np.asarray(operator.to_matrix(), dtype=complex)))
    return float(np.linalg.norm(np.asarray(operator.coeffs, dtype=complex)))


def hermitian_project_operator(operator: SparsePauliOp, *, atol: float = 1.0e-12) -> tuple[SparsePauliOp, dict[str, Any]]:
    """Project a possibly non-Hermitian Pauli operator onto its Hermitian part."""
    anti_hermitian = ((operator - operator.adjoint()) * 0.5).simplify(atol=atol)
    projected = ((operator + operator.adjoint()) * 0.5).simplify(atol=atol)
    norm = _operator_frobenius_norm(anti_hermitian)
    return projected, {
        "hermitian_projection_applied": bool(norm > atol),
        "anti_hermitian_norm": norm,
        "pre_projection_pauli_terms": len(operator),
        "post_projection_pauli_terms": len(projected),
    }


def _add_if_present(base: np.ndarray | None, data: Any, key: str) -> np.ndarray | None:
    if base is None:
        return None
    if key not in data:
        return base
    return np.asarray(base, dtype=float) + np.asarray(data[key], dtype=float)


def _as_four_index(two_body: np.ndarray) -> np.ndarray:
    if two_body.ndim == 4:
        return np.asarray(two_body, dtype=float)
    return np.asarray(unfold(two_body, validate=False), dtype=float)


def build_cast_hamiltonian(
    *,
    cast_spec,
    chemistry,
    physical_operator: SparsePauliOp,
    mapping_kind: str,
) -> CastHamiltonianBuild:
    """Build the CAST/TC Hamiltonian used only for determinant-sampling kicks."""
    kind = cast_spec.kind.strip().lower()
    if kind == "identity":
        projected, projection_audit = hermitian_project_operator(physical_operator)
        audit = {
            "kind": "identity",
            "plugin": "builtin_identity",
            "description": "No-op CAST model; physical active-space Hamiltonian is used for kicking.",
            "verification_status": "exploratory",
            "notes": [
                "CAST-QC math is pluggable in QCchem v1.",
                "The identity model is intended as a baseline and provenance anchor.",
            ],
            **projection_audit,
        }
        return CastHamiltonianBuild(operator=projected, audit=audit)

    if kind != "npz_delta":
        raise ValueError(f"Unsupported CAST-QC model kind: {cast_spec.kind}")
    if cast_spec.npz_path is None:
        raise ValueError("CAST-QC npz_delta model requires tc_qsci.cast_model.npz_path.")

    raw_integrals = _extract_raw_integrals(chemistry.problem)
    if raw_integrals is None:
        raise ValueError("CAST-QC npz_delta model requires raw one-/two-body integrals.")
    h1_a, h2_aa, h1_b, h2_bb, h2_ba = raw_integrals
    h2_aa = _as_four_index(h2_aa)
    h2_bb = _as_four_index(h2_bb) if h2_bb is not None else None
    h2_ba = _as_four_index(h2_ba) if h2_ba is not None else None
    path = Path(cast_spec.npz_path).expanduser()
    data = np.load(path)
    h1_a = _add_if_present(h1_a, data, "h1_alpha_delta")
    h2_aa = _add_if_present(h2_aa, data, "h2_alpha_delta")
    h1_b = _add_if_present(h1_b, data, "h1_beta_delta")
    h2_bb = _add_if_present(h2_bb, data, "h2_beta_delta")
    h2_ba = _add_if_present(h2_ba, data, "h2_beta_alpha_delta")
    energy = ElectronicEnergy.from_raw_integrals(
        h1_a,
        h2_aa,
        h1_b,
        h2_bb,
        h2_ba,
        validate=False,
    )
    energy.constants = dict(chemistry.problem.hamiltonian.constants)
    mapped = map_fermionic_hamiltonian(
        energy.second_q_op(),
        mapping_kind,
        num_particles=chemistry.summary.num_particles,
    )
    projected, projection_audit = hermitian_project_operator(mapped.qubit_hamiltonian)
    audit = {
        "kind": "npz_delta",
        "plugin": "builtin_npz_delta",
        "npz_path": str(path),
        "verification_status": "exploratory",
        "notes": [
            "Applied user-supplied one-/two-body tensor deltas before mapping.",
            "Hermitian projection is used for quantum kicking; anti-Hermitian norm is retained as risk evidence.",
        ],
        **projection_audit,
    }
    return CastHamiltonianBuild(operator=projected, audit=audit)
