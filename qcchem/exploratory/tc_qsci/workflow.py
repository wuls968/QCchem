"""TC-kicked QSCI exploratory workflow."""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
from scipy.linalg import expm

from qcchem.exploratory.tc_qsci.cast import build_cast_hamiltonian
from qcchem.exploratory.tc_qsci.determinants import (
    InitialState,
    build_initial_state,
    build_selected_subspace_matrix,
    determinant_sector,
    filter_determinants_by_sector,
    hartree_fock_determinant,
)
from qcchem.exploratory.tc_qsci.resources import (
    estimate_low_rank_resources,
    estimate_qpe_resources,
    lcu_lambda,
)


def _truncate_operator(operator, max_terms: int | None):
    if max_terms is None or len(operator) <= max_terms:
        return operator.simplify(atol=1.0e-12)
    weights = np.abs(np.asarray(operator.coeffs, dtype=complex))
    keep = np.argsort(weights)[-max(int(max_terms), 1):]
    return operator[keep].simplify(atol=1.0e-12)


def _evolve_kicked_state(initial: InitialState, operator, *, time: float, num_kicks: int, pauli_term_budget: int | None) -> np.ndarray:
    truncated = _truncate_operator(operator, pauli_term_budget)
    matrix = np.asarray(truncated.to_matrix(), dtype=complex)
    unitary = expm(-1.0j * float(time) * matrix)
    state = np.asarray(initial.vector, dtype=complex)
    for _ in range(max(int(num_kicks), 0)):
        state = unitary @ state
    norm = np.linalg.norm(state)
    if norm <= 0.0:
        raise ValueError("TC-QSCI kicked state has zero norm.")
    return state / norm


def _sample_determinants(probabilities: np.ndarray, *, shots: int, seed: int) -> Counter[int]:
    rng = np.random.default_rng(seed)
    normalized = probabilities / float(np.sum(probabilities))
    samples = rng.choice(len(normalized), size=max(int(shots), 1), p=normalized)
    return Counter(int(item) for item in samples)


def _determinant_payload(
    determinant: int,
    *,
    count: int,
    probability: float,
    num_spatial_orbitals: int,
) -> dict[str, Any]:
    sector = determinant_sector(determinant, num_spatial_orbitals=num_spatial_orbitals)
    return {
        "index": int(determinant),
        "bitstring": sector.bitstring,
        "occupied_spin_orbitals": sector.occupied_spin_orbitals,
        "count": int(count),
        "probability": float(probability),
        "alpha_electrons": sector.alpha_electrons,
        "beta_electrons": sector.beta_electrons,
        "total_electrons": sector.total_electrons,
        "spin_projection": sector.spin_projection,
        "point_group_label": sector.point_group_label,
    }


def _select_determinants(
    counts: Counter[int],
    probabilities: np.ndarray,
    *,
    spec,
    num_spatial_orbitals: int,
    num_particles: tuple[int, int],
    initial_determinants: list[int],
) -> tuple[list[int], dict[str, Any], dict[str, Any]]:
    raw_unique = len(counts)
    working_counts = dict(counts)
    if spec.selection.symmetry_postselect:
        allowed = set(filter_determinants_by_sector(
            list(working_counts),
            num_spatial_orbitals=num_spatial_orbitals,
            num_particles=num_particles,
        ))
        working_counts = {
            determinant: count
            for determinant, count in working_counts.items()
            if determinant in allowed
        }
    min_count = max(int(spec.selection.min_count), 1)
    ranked = [
        determinant
        for determinant, count in sorted(working_counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= min_count
    ]
    for determinant in initial_determinants:
        if determinant not in ranked:
            ranked.append(int(determinant))
    if not ranked:
        ranked = [hartree_fock_determinant(num_spatial_orbitals, num_particles)]
    selected = ranked[: max(int(spec.selection.max_determinants), 1)]
    selected = filter_determinants_by_sector(
        selected,
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
    )
    if not selected:
        selected = [hartree_fock_determinant(num_spatial_orbitals, num_particles)]

    selected_payload = [
        _determinant_payload(
            determinant,
            count=working_counts.get(determinant, 0),
            probability=float(probabilities[determinant]),
            num_spatial_orbitals=num_spatial_orbitals,
        )
        for determinant in selected
    ]
    selection_payload = {
        "shots": int(spec.kick.shots),
        "raw_unique_determinants": int(raw_unique),
        "postselected_unique_determinants": int(len(working_counts)),
        "selected_determinant_count": int(len(selected)),
        "max_determinants": int(spec.selection.max_determinants),
        "min_count": int(spec.selection.min_count),
        "symmetry_postselect": bool(spec.selection.symmetry_postselect),
        "selected_determinants": selected_payload,
    }
    alpha, beta = int(num_particles[0]), int(num_particles[1])
    symmetry_payload = {
        "target_alpha_electrons": alpha,
        "target_beta_electrons": beta,
        "target_total_electrons": int(alpha + beta),
        "target_spin_projection": float((alpha - beta) / 2.0),
        "particle_number_conserved": all(
            item["alpha_electrons"] == alpha and item["beta_electrons"] == beta
            for item in selected_payload
        ),
        "point_group_label": None,
        "point_group_available": False,
    }
    return selected, selection_payload, symmetry_payload


def _initial_payload(initial: InitialState, *, num_spatial_orbitals: int) -> dict[str, Any]:
    return {
        "kind": initial.kind,
        "determinant_count": len(initial.determinants),
        "determinants": [
            _determinant_payload(
                determinant,
                count=0,
                probability=abs(initial.coefficients[determinant]) ** 2,
                num_spatial_orbitals=num_spatial_orbitals,
            )
            for determinant in initial.determinants
        ],
    }


def run_tc_qsci(
    *,
    spec,
    chemistry,
    physical_mapping,
    exact_solver_energy: float | None,
) -> dict[str, Any] | None:
    """Run TC-kicked QSCI if requested by the config."""
    tc_spec = getattr(spec, "tc_qsci", None)
    if tc_spec is None or not tc_spec.enabled:
        return None

    if spec.mapping.kind.strip().lower() != "jordan_wigner" and not tc_spec.resource_estimation_only:
        raise ValueError("TC-QSCI determinant sampling v1 requires jordan_wigner mapping; use resource_estimation_only for other mappings.")

    physical_operator = physical_mapping.qubit_hamiltonian.simplify(atol=1.0e-12)
    num_qubits = int(physical_operator.num_qubits)
    num_spatial_orbitals = int(chemistry.summary.num_spatial_orbitals)
    num_particles = tuple(int(value) for value in chemistry.summary.num_particles)
    cast_build = build_cast_hamiltonian(
        cast_spec=tc_spec.cast_model,
        chemistry=chemistry,
        physical_operator=physical_operator,
        mapping_kind=spec.mapping.kind,
    )
    cast_operator = cast_build.operator.simplify(atol=1.0e-12)
    low_rank_estimate = estimate_low_rank_resources(
        physical_operator,
        selected_determinant_count=0,
        pauli_term_budget=tc_spec.kick.pauli_term_budget,
    )
    qpe_estimate = None
    if tc_spec.resource_estimation.enabled:
        qpe_estimate = estimate_qpe_resources(
            physical_operator,
            selected_determinant_count=0,
            target_precision=tc_spec.resource_estimation.target_precision,
            trotter_time=tc_spec.kick.time,
            num_kicks=tc_spec.kick.num_kicks,
        )

    if tc_spec.resource_estimation_only:
        cast_payload = {
            **cast_build.audit,
            "qubit_count": num_qubits,
            "pauli_term_count": len(cast_operator),
            "lcu_lambda": lcu_lambda(cast_operator),
        }
        return {
            "tc_qsci_result": {
                "algorithm_name": "TC-kicked QSCI",
                "verification_status": "exploratory",
                "resource_estimation_only": True,
                "notes": ["Determinant sampling skipped by configuration."],
            },
            "determinant_selection": None,
            "symmetry_sector": None,
            "cast_hamiltonian": cast_payload,
            "low_rank_resource_estimate": low_rank_estimate,
            "qpe_resource_estimate": qpe_estimate,
            "error_budget": {
                "available": False,
                "reason": "resource_estimation_only",
            },
        }

    initial = build_initial_state(
        kind=tc_spec.initial_state.kind,
        num_qubits=num_qubits,
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
        entries=tc_spec.initial_state.determinants,
        operator=physical_operator,
        max_determinants=tc_spec.initial_state.max_determinants,
    )
    kicked_state = _evolve_kicked_state(
        initial,
        cast_operator,
        time=tc_spec.kick.time,
        num_kicks=tc_spec.kick.num_kicks,
        pauli_term_budget=tc_spec.kick.pauli_term_budget,
    )
    probabilities = np.abs(kicked_state) ** 2
    counts = _sample_determinants(probabilities, shots=tc_spec.kick.shots, seed=spec.run.seed)
    selected, determinant_selection, symmetry_sector = _select_determinants(
        counts,
        probabilities,
        spec=tc_spec,
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
        initial_determinants=initial.determinants,
    )
    subspace_matrix = build_selected_subspace_matrix(physical_operator, selected)
    eigenvalues, eigenvectors = np.linalg.eigh(subspace_matrix)
    selected_solver_energy = float(np.real(eigenvalues[0]))
    leading_vector = np.asarray(eigenvectors[:, 0], dtype=complex)
    amplitudes = [
        {
            "index": int(determinant),
            "coefficient_real": float(np.real(leading_vector[index])),
            "coefficient_imag": float(np.imag(leading_vector[index])),
            "weight": float(abs(leading_vector[index]) ** 2),
        }
        for index, determinant in enumerate(selected)
    ]
    electronic_energy = float(selected_solver_energy + chemistry.electronic_constant_correction)
    total_energy = float(selected_solver_energy + chemistry.total_constant_correction)
    selected_probability_mass = float(np.sum(probabilities[selected]))
    low_rank_estimate = estimate_low_rank_resources(
        physical_operator,
        selected_determinant_count=len(selected),
        pauli_term_budget=tc_spec.kick.pauli_term_budget,
    )
    if qpe_estimate is not None:
        qpe_estimate = estimate_qpe_resources(
            physical_operator,
            selected_determinant_count=len(selected),
            target_precision=tc_spec.resource_estimation.target_precision,
            trotter_time=tc_spec.kick.time,
            num_kicks=tc_spec.kick.num_kicks,
        )
    solver_error = None
    if exact_solver_energy is not None:
        solver_error = float(abs(selected_solver_energy - float(exact_solver_energy)))

    cast_payload = {
        **cast_build.audit,
        "qubit_count": num_qubits,
        "pauli_term_count": len(cast_operator),
        "lcu_lambda": lcu_lambda(cast_operator),
    }
    error_budget = {
        "available": True,
        "selected_vs_exact_solver_error": solver_error,
        "sampling_missing_probability": float(max(0.0, 1.0 - selected_probability_mass)),
        "cast_anti_hermitian_norm": cast_payload.get("anti_hermitian_norm"),
        "discarded_pauli_l1_norm": low_rank_estimate.get("discarded_l1_norm"),
        "notes": [
            "Final diagonalization uses the physical active-space Hamiltonian.",
            "CAST/TC Hamiltonian affects determinant sampling only.",
            "Errors are budget components, not a rigorous bound.",
        ],
    }
    tc_result = {
        "algorithm_name": "TC-kicked QSCI",
        "verification_status": "exploratory",
        "resource_estimation_only": False,
        "solver_energy": selected_solver_energy,
        "electronic_energy": electronic_energy,
        "total_energy": total_energy,
        "energy_units": "Hartree",
        "subspace_dimension": int(len(selected)),
        "selected_probability_mass": selected_probability_mass,
        "initial_state": _initial_payload(initial, num_spatial_orbitals=num_spatial_orbitals),
        "kick": {
            "time": float(tc_spec.kick.time),
            "num_kicks": int(tc_spec.kick.num_kicks),
            "pauli_term_budget": tc_spec.kick.pauli_term_budget,
            "shots": int(tc_spec.kick.shots),
            "sampler": "local_statevector_trotter_proxy",
        },
        "subspace_eigenvector": amplitudes,
        "notes": [
            "TC-kicked QSCI is implemented as an exploratory local sampling workflow.",
            "The selected determinant subspace is classically diagonalized.",
        ],
    }
    return {
        "tc_qsci_result": tc_result,
        "determinant_selection": determinant_selection,
        "symmetry_sector": symmetry_sector,
        "cast_hamiltonian": cast_payload,
        "low_rank_resource_estimate": low_rank_estimate,
        "qpe_resource_estimate": qpe_estimate,
        "error_budget": error_budget,
    }
