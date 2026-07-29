"""Generic QSCI++ selected-subspace workflow."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from qcchem.exploratory.tc_qsci.determinants import (
    build_selected_subspace_matrix,
    determinant_sector,
    determinants_in_sector,
    filter_determinants_by_sector,
    hartree_fock_determinant,
)
from qcchem.io.exports import workspace_fingerprint


def _determinant_payload(
    determinant: int,
    *,
    origin: str,
    origins: list[str] | None = None,
    probability: float,
    num_spatial_orbitals: int,
) -> dict[str, Any]:
    sector = determinant_sector(determinant, num_spatial_orbitals=num_spatial_orbitals)
    return {
        "index": int(determinant),
        "bitstring": sector.bitstring,
        "occupied_spin_orbitals": sector.occupied_spin_orbitals,
        "probability": float(probability),
        "selection_origin": origin,
        "selection_origins": list(origins or [origin]),
        "alpha_electrons": sector.alpha_electrons,
        "beta_electrons": sector.beta_electrons,
        "total_electrons": sector.total_electrons,
        "spin_projection": sector.spin_projection,
    }


def _candidate_probabilities(operator) -> np.ndarray:
    matrix = np.asarray(operator.to_matrix(), dtype=complex)
    diagonal = np.real(np.diag(matrix))
    shifted = diagonal - float(np.min(diagonal))
    weights = np.exp(-shifted)
    return weights / float(np.sum(weights))


def _hamming_neighbors(seed: int, *, num_qubits: int, radius: int) -> list[int]:
    if radius <= 0:
        return []
    neighbors: set[int] = set()
    for bit in range(num_qubits):
        neighbors.add(seed ^ (1 << bit))
    if radius >= 2:
        for first in range(num_qubits):
            for second in range(first + 1, num_qubits):
                neighbors.add(seed ^ (1 << first) ^ (1 << second))
    return sorted(neighbors)


def _primary_selection_origin(origins: list[str]) -> str:
    priority = (
        "sampled",
        "residual_expanded",
        "hartree_fock_reference",
        "hamming_expanded",
        "sector_repaired",
    )
    origin_set = set(origins)
    for candidate in priority:
        if candidate in origin_set:
            return candidate
    return origins[0] if origins else "unknown"


def _sector_determinant_indices(
    *,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
) -> list[int]:
    return [
        int(item.index)
        for item in determinants_in_sector(
            num_spatial_orbitals=num_spatial_orbitals,
            num_particles=num_particles,
        )
    ]


def _external_residual_scores(
    operator,
    selected: list[int],
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    *,
    sector_determinants: list[int],
) -> list[dict[str, Any]]:
    if not selected or not len(eigenvalues):
        return []
    sparse_matrix = operator.to_matrix(sparse=True).tocsr()
    dim = int(sparse_matrix.shape[0])
    selected_indices = [int(item) for item in selected]
    selected_set = set(selected_indices)
    coefficients = np.asarray(eigenvectors[:, 0], dtype=complex)
    embedded = np.zeros(dim, dtype=complex)
    for determinant, coefficient in zip(selected_indices, coefficients, strict=True):
        embedded[determinant] = coefficient
    norm = float(np.linalg.norm(embedded))
    if norm > 0.0:
        embedded = embedded / norm
    energy = float(np.real(eigenvalues[0]))
    residual = np.asarray(sparse_matrix @ embedded - energy * embedded, dtype=complex)
    scores = [
        {
            "determinant": int(determinant),
            "bitstring": format(int(determinant), f"0{operator.num_qubits}b"),
            "external_residual_coupling_abs": float(abs(residual[int(determinant)])),
        }
        for determinant in sector_determinants
        if int(determinant) not in selected_set
    ]
    scores.sort(key=lambda item: (-float(item["external_residual_coupling_abs"]), int(item["determinant"])))
    return scores


def _embedded_ritz_audit(
    operator,
    selected: list[int],
    eigenvalues: np.ndarray,
    eigenvectors: np.ndarray,
    *,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
    exact_solver_energy: float | None,
) -> dict[str, Any]:
    sparse_matrix = operator.to_matrix(sparse=True).tocsr()
    dim = int(sparse_matrix.shape[0])
    selected_indices = [int(item) for item in selected]
    selected_set = set(selected_indices)
    sector_determinants = _sector_determinant_indices(
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
    )
    root_audits: list[dict[str, Any]] = []
    for root_index, eigenvalue in enumerate(eigenvalues):
        coefficients = np.asarray(eigenvectors[:, root_index], dtype=complex)
        embedded = np.zeros(dim, dtype=complex)
        for determinant, coefficient in zip(selected_indices, coefficients, strict=True):
            embedded[determinant] = coefficient
        norm = float(np.linalg.norm(embedded))
        if norm > 0.0:
            embedded = embedded / norm
        h_vector = sparse_matrix @ embedded
        energy = float(np.real(np.vdot(embedded, h_vector)))
        h2 = float(np.real(np.vdot(h_vector, h_vector)))
        variance = float(max(h2 - energy**2, 0.0))
        residual = np.asarray(h_vector - energy * embedded, dtype=complex)
        selected_residual = residual[selected_indices] if selected_indices else np.asarray([], dtype=complex)
        outside_residual = residual.copy()
        for determinant in selected_indices:
            outside_residual[determinant] = 0.0
        root_audits.append(
            {
                "root_index": int(root_index),
                "energy": energy,
                "projected_subspace_energy": float(np.real(eigenvalue)),
                "hamiltonian_variance": variance,
                "residual_norm": float(np.linalg.norm(residual)),
                "projected_residual_norm": float(np.linalg.norm(selected_residual)),
                "external_coupling_residual_norm": float(np.linalg.norm(outside_residual)),
            }
        )
    ground = root_audits[0] if root_audits else {}
    exact_gap = (
        float(ground["energy"]) - float(exact_solver_energy)
        if ground and exact_solver_energy is not None
        else None
    )
    return {
        "variance_method": "embedded_ritz_vector_sparse_hamiltonian",
        "ground_state_variance": ground.get("hamiltonian_variance"),
        "ground_state_residual_norm": ground.get("residual_norm"),
        "ground_state_external_coupling_residual_norm": ground.get("external_coupling_residual_norm"),
        "energy_error_to_exact_hartree": exact_gap,
        "variational_upper_bound_margin_hartree": exact_gap,
        "variational_upper_bound_passed": (
            bool(exact_gap >= -1.0e-8)
            if exact_gap is not None
            else None
        ),
        "selected_determinant_count": int(len(selected_indices)),
        "sector_determinant_count": int(len(sector_determinants)),
        "selected_sector_coverage_fraction": (
            float(len(selected_set.intersection(sector_determinants)) / len(sector_determinants))
            if sector_determinants
            else None
        ),
        "selected_bitstrings": [
            format(index, f"0{operator.num_qubits}b")
            for index in selected_indices
        ],
        "root_residuals": root_audits,
    }


def diagonalize_selected_subspace(
    operator,
    selected: list[int],
    *,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
    exact_solver_energy: float | None,
    excited_roots: int = 0,
) -> dict[str, Any]:
    """Diagonalize a selected determinant subspace and attach Ritz-vector audits."""
    subspace = build_selected_subspace_matrix(operator, selected)
    eigenvalues, eigenvectors = np.linalg.eigh(subspace)
    subspace_audit = _embedded_ritz_audit(
        operator,
        selected,
        eigenvalues,
        eigenvectors,
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
        exact_solver_energy=exact_solver_energy,
    )
    return {
        "eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "ground_energy": float(np.real(eigenvalues[0])),
        "excited_energies": [
            float(np.real(value)) for value in eigenvalues[1 : 1 + max(int(excited_roots), 0)]
        ],
        "subspace_audit": subspace_audit,
    }


def run_qsci_plus(
    *,
    spec,
    chemistry,
    physical_mapping,
    exact_solver_energy: float | None,
) -> dict[str, Any] | None:
    qsci_spec = getattr(spec, "qsci", None)
    if qsci_spec is None or not qsci_spec.enabled:
        return None
    if spec.mapping.kind.strip().lower() != "jordan_wigner":
        raise ValueError("QSCI++ determinant selection v1 requires jordan_wigner mapping.")

    operator = physical_mapping.qubit_hamiltonian.simplify(atol=1.0e-12)
    num_qubits = int(operator.num_qubits)
    num_spatial_orbitals = int(chemistry.summary.num_spatial_orbitals)
    num_particles = tuple(int(value) for value in chemistry.summary.num_particles)
    probabilities = _candidate_probabilities(operator)
    counts = Counter()
    rng = np.random.default_rng(spec.run.seed)
    samples = rng.choice(len(probabilities), size=max(int(qsci_spec.shots), 1), p=probabilities)
    counts.update(int(item) for item in samples)

    origin_map: dict[int, set[str]] = {
        int(determinant): {"sampled"}
        for determinant in counts
        if float(probabilities[int(determinant)]) >= float(qsci_spec.min_probability)
    }
    ranked = [
        determinant
        for determinant, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if float(probabilities[determinant]) >= float(qsci_spec.min_probability)
    ]
    pre_repair_ranked = list(ranked)
    sector_rejected_count = 0
    if qsci_spec.determinant_repair.enforce_particle_number or qsci_spec.determinant_repair.enforce_spin_sector:
        before_sector_filter = set(ranked)
        ranked = filter_determinants_by_sector(
            ranked,
            num_spatial_orbitals=num_spatial_orbitals,
            num_particles=num_particles,
        )
        after_sector_filter = set(ranked)
        sector_rejected_count = len(before_sector_filter - after_sector_filter)
        for determinant in ranked:
            origin_map.setdefault(int(determinant), set()).add("sector_repaired")
    hf = hartree_fock_determinant(num_spatial_orbitals, num_particles)
    if hf not in ranked:
        ranked.append(hf)
    origin_map.setdefault(int(hf), set()).add("hartree_fock_reference")
    expanded: list[int] = []
    hamming_seeds = list(ranked)
    for determinant in hamming_seeds:
        expanded.extend(
            _hamming_neighbors(
                determinant,
                num_qubits=num_qubits,
                radius=int(qsci_spec.determinant_repair.hamming_expansion),
            )
        )
    if expanded:
        repaired = filter_determinants_by_sector(
            expanded,
            num_spatial_orbitals=num_spatial_orbitals,
            num_particles=num_particles,
        )
        for determinant in repaired:
            origin_map.setdefault(int(determinant), set()).add("hamming_expanded")
            if determinant not in ranked:
                ranked.append(determinant)

    initial_max_size = min(
        max(int(qsci_spec.max_determinants), 1),
        max(int(qsci_spec.classical_diagonalizer.max_subspace_size), 1),
    )
    residual_spec = getattr(qsci_spec, "residual_expansion", None)
    residual_enabled = bool(getattr(residual_spec, "enabled", False))
    residual_max_additional = max(
        int(getattr(residual_spec, "max_additional_determinants", 0) or 0),
        0,
    )
    max_size = (
        min(
            initial_max_size + residual_max_additional,
            max(int(qsci_spec.classical_diagonalizer.max_subspace_size), 1),
        )
        if residual_enabled
        else initial_max_size
    )
    selected = ranked[:initial_max_size]
    diagonalization = diagonalize_selected_subspace(
        operator,
        selected,
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
        exact_solver_energy=exact_solver_energy,
        excited_roots=max(int(qsci_spec.excited_roots), 0),
    )
    residual_expansion_history: list[dict[str, Any]] = []
    if residual_enabled and max_size > len(selected):
        sector_determinants = _sector_determinant_indices(
            num_spatial_orbitals=num_spatial_orbitals,
            num_particles=num_particles,
        )
        target_residual_norm = float(getattr(residual_spec, "target_residual_norm", 1.0e-6))
        scorer = str(getattr(residual_spec, "scorer", "external_residual_coupling"))
        if scorer != "external_residual_coupling":
            raise ValueError("qsci.residual_expansion.scorer must be external_residual_coupling.")
        for iteration in range(1, max(int(getattr(residual_spec, "max_iterations", 0)), 0) + 1):
            audit = diagonalization["subspace_audit"]
            residual_norm = audit.get("ground_state_external_coupling_residual_norm")
            if residual_norm is not None and float(residual_norm) <= target_residual_norm:
                residual_expansion_history.append(
                    {
                        "iteration": iteration,
                        "status": "target_residual_reached",
                        "external_residual_norm": float(residual_norm),
                        "selected_subspace_size": int(len(selected)),
                    }
                )
                break
            scores = _external_residual_scores(
                operator,
                selected,
                diagonalization["eigenvalues"],
                diagonalization["eigenvectors"],
                sector_determinants=sector_determinants,
            )
            positive_scores = [
                row for row in scores if float(row["external_residual_coupling_abs"]) > 1.0e-12
            ]
            remaining_slots = max_size - len(selected)
            add_count = min(
                max(int(getattr(residual_spec, "batch_size", 8)), 1),
                remaining_slots,
                len(positive_scores),
            )
            added = [int(row["determinant"]) for row in positive_scores[:add_count]]
            residual_expansion_history.append(
                {
                    "iteration": iteration,
                    "status": "expanded" if added else "no_external_residual_candidates",
                    "external_residual_norm": (
                        float(residual_norm) if residual_norm is not None else None
                    ),
                    "selected_subspace_size_before": int(len(selected)),
                    "added_determinants": added,
                    "top_external_residual_candidates": positive_scores[: max(add_count, 5)],
                }
            )
            if not added:
                break
            for determinant in added:
                selected.append(determinant)
                origin_map.setdefault(int(determinant), set()).add("residual_expanded")
            diagonalization = diagonalize_selected_subspace(
                operator,
                selected,
                num_spatial_orbitals=num_spatial_orbitals,
                num_particles=num_particles,
                exact_solver_energy=exact_solver_energy,
                excited_roots=max(int(qsci_spec.excited_roots), 0),
            )
            if len(selected) >= max_size:
                break
    eigenvectors = diagonalization["eigenvectors"]
    ci_energy = float(diagonalization["ground_energy"])
    roots = list(diagonalization["excited_energies"])
    leading = np.asarray(eigenvectors[:, 0], dtype=complex)
    repaired_payload = [
        _determinant_payload(
            determinant,
            origin=_primary_selection_origin(sorted(origin_map.get(int(determinant), {"unknown"}))),
            origins=sorted(origin_map.get(int(determinant), {"unknown"})),
            probability=float(probabilities[determinant]),
            num_spatial_orbitals=num_spatial_orbitals,
        )
        for determinant in selected
    ]
    subspace_audit = diagonalization["subspace_audit"]
    variance = subspace_audit.get("ground_state_variance")
    digest = workspace_fingerprint(
        [
            str(item["index"]) + ":" + str(item["probability"])
            for item in repaired_payload
        ]
    )
    primary_origin_counts = Counter(str(item["selection_origin"]) for item in repaired_payload)
    multi_origin_counts = Counter(
        str(origin)
        for item in repaired_payload
        for origin in item.get("selection_origins", [])
    )
    return {
        "sampler": qsci_spec.sampler,
        "raw_bitstrings": {
            format(int(key), f"0{num_qubits}b"): int(value)
            for key, value in counts.items()
        },
        "repaired_determinants": repaired_payload,
        "selected_subspace_size": int(len(selected)),
        "ci_energy": ci_energy,
        "variance_estimate": variance,
        "excited_state_energies": roots,
        "selection_bias_audit": {
            "selected_probability_mass": float(sum(probabilities[item] for item in selected)),
            "raw_unique_determinants": int(len(counts)),
            "pre_repair_ranked_count": int(len(pre_repair_ranked)),
            "sector_rejected_count": int(sector_rejected_count),
            "hamming_expansion_radius": int(qsci_spec.determinant_repair.hamming_expansion),
            "hamming_seed_count": int(len(hamming_seeds)),
            "initial_selected_subspace_size": int(initial_max_size),
            "max_selected_subspace_size": int(max_size),
            "residual_expansion": {
                "enabled": residual_enabled,
                "scorer": str(getattr(residual_spec, "scorer", "external_residual_coupling")),
                "target_residual_norm": (
                    float(getattr(residual_spec, "target_residual_norm", 1.0e-6))
                    if residual_spec is not None
                    else None
                ),
                "max_iterations": (
                    int(getattr(residual_spec, "max_iterations", 0))
                    if residual_spec is not None
                    else 0
                ),
                "batch_size": (
                    int(getattr(residual_spec, "batch_size", 8))
                    if residual_spec is not None
                    else 0
                ),
                "max_additional_determinants": residual_max_additional,
                "iteration_count": len(residual_expansion_history),
                "added_determinant_count": sum(
                    len(item.get("added_determinants", []))
                    for item in residual_expansion_history
                    if isinstance(item.get("added_determinants", []), list)
                ),
                "history": residual_expansion_history,
            },
            "selected_origin_counts": dict(sorted(primary_origin_counts.items())),
            "selected_multi_origin_counts": dict(sorted(multi_origin_counts.items())),
            "hartree_fock_determinant": int(hf),
            "hartree_fock_selected": bool(hf in selected),
            "ci_coefficients_digest": digest,
            "classical_diagonalizer": qsci_spec.classical_diagonalizer.method,
            "leading_coefficients": [
                {
                    "determinant": int(det),
                    "coefficient_real": float(np.real(leading[index])),
                    "coefficient_imag": float(np.imag(leading[index])),
                }
                for index, det in enumerate(selected)
            ],
        },
        "subspace_audit": subspace_audit,
        "variational_upper_bound": bool(
            subspace_audit.get("variational_upper_bound_passed")
            if subspace_audit.get("variational_upper_bound_passed") is not None
            else True
        ),
        "notes": [
            "QSCI++ v1 selects a determinant subspace with local sampling proxies and diagonalizes the physical Hamiltonian.",
            "Variance and residual diagnostics are computed from the embedded Ritz vector in the physical qubit Hamiltonian.",
            "The selected CI energy is reported as method evidence and does not replace the primary run energy.",
        ],
    }
