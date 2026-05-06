"""LR-ACE: Low-Rank Adaptive Chemistry Eigensolver.

LR-ACE is an exploratory QCchem-native ansatz builder. It treats the mapped,
optionally low-rank-compressed Hamiltonian as the source of compact mixing
generators instead of starting from a full UCC excitation pool.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.circuit.library import HartreeFock
from scipy.optimize import minimize
from scipy.sparse import SparseEfficiencyWarning

from qcchem.backends import BackendAdapter
from qcchem.core import ProblemSummary
from qcchem.solvers.base import BaseSolver, SolverOutcome
from qcchem.solvers.spectrum import compute_exact_spectrum


@dataclass(slots=True)
class _LRACEGenerator:
    pauli: str
    source_pauli: str
    source_weight: float
    coefficient_real: float
    coefficient_imag: float
    adaptive_score: float
    locality: int
    reference_mixing_relevance: float


def _real_mixing_companion(pauli_label: str) -> str | None:
    """Turn an X/Y Hamiltonian factor into a real-amplitude mixing generator."""
    chars = list(pauli_label)
    for index, char in enumerate(chars):
        if char == "X":
            chars[index] = "Y"
            return "".join(chars)
        if char == "Y":
            chars[index] = "X"
            return "".join(chars)
    return None


def _mixing_companions(pauli_label: str) -> list[str]:
    """Enumerate one-site X/Y flips for residual-guided generator screening."""
    companions: list[str] = []
    seen: set[str] = set()
    for index, char in enumerate(pauli_label):
        if char not in "XY":
            continue
        chars = list(pauli_label)
        chars[index] = "Y" if char == "X" else "X"
        companion = "".join(chars)
        if companion not in seen:
            seen.add(companion)
            companions.append(companion)
    return companions


def _generator_to_metadata(item: _LRACEGenerator, *, batch_index: int | None = None) -> dict[str, Any]:
    payload = {
        "pauli": item.pauli,
        "source_pauli": item.source_pauli,
        "source_weight": item.source_weight,
        "coefficient_real": item.coefficient_real,
        "coefficient_imag": item.coefficient_imag,
        "adaptive_score": item.adaptive_score,
        "locality": item.locality,
        "reference_mixing_relevance": item.reference_mixing_relevance,
    }
    if batch_index is not None:
        payload["batch_index"] = int(batch_index)
    return payload


def _enumerate_generator_candidates(
    source_terms: list[dict[str, Any]],
) -> list[_LRACEGenerator]:
    candidates: list[_LRACEGenerator] = []
    seen: set[str] = set()
    for item in source_terms:
        source_pauli = str(item["pauli"])
        source_xy_count = sum(1 for char in source_pauli if char in "XY")
        for generator in _mixing_companions(source_pauli):
            if generator in seen:
                continue
            seen.add(generator)
            locality = sum(1 for char in generator if char != "I")
            mixing_relevance = source_xy_count / max(locality, 1)
            adaptive_score = (
                float(item["weight"])
                * (1.0 + float(mixing_relevance))
                / max(locality, 1)
            )
            candidates.append(
                _LRACEGenerator(
                    pauli=generator,
                    source_pauli=source_pauli,
                    source_weight=float(item["weight"]),
                    coefficient_real=float(item["coefficient_real"]),
                    coefficient_imag=float(item["coefficient_imag"]),
                    adaptive_score=adaptive_score,
                    locality=locality,
                    reference_mixing_relevance=float(mixing_relevance),
                )
            )
    candidates.sort(key=lambda item: (-item.adaptive_score, -item.source_weight))
    return candidates


def build_low_rank_generator_plan(
    operator: SparsePauliOp,
    *,
    max_generators: int,
    coefficient_threshold: float = 1.0e-12,
    selected_paulis: list[str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic compact generator plan from dominant Hamiltonian factors."""
    source_terms: list[dict[str, Any]] = []
    for pauli, coeff in zip(operator.paulis, operator.coeffs):
        label = pauli.to_label()
        weight = float(abs(coeff))
        if weight <= coefficient_threshold or not any(char in label for char in "XY"):
            continue
        source_terms.append(
            {
                "pauli": label,
                "weight": weight,
                "coefficient_real": float(np.real(coeff)),
                "coefficient_imag": float(np.imag(coeff)),
            }
        )
    source_terms.sort(key=lambda item: (-float(item["weight"]), str(item["pauli"])))
    candidates = _enumerate_generator_candidates(source_terms)
    candidate_by_pauli = {item.pauli: item for item in candidates}
    primary_candidates = [
        item
        for item in candidates
        if item.pauli == _real_mixing_companion(item.source_pauli)
    ]
    selected: list[_LRACEGenerator] = []
    selected_seen: set[str] = set()
    if selected_paulis is not None:
        for pauli in selected_paulis:
            item = candidate_by_pauli.get(str(pauli))
            if item is None or item.pauli in selected_seen:
                continue
            selected.append(item)
            selected_seen.add(item.pauli)
            if len(selected) >= max_generators:
                break
    for item in primary_candidates:
        if len(selected) >= max_generators:
            break
        if item.pauli in selected_seen:
            continue
        selected.append(item)
        selected_seen.add(item.pauli)
    return {
        "algorithm_name": "LR-ACE",
        "low_rank_aware": True,
        "selection_rule": "adaptive_score_weight_locality_reference_mixing",
        "source_terms": source_terms,
        "candidate_generators": [
            {
                **_generator_to_metadata(item),
                "candidate_index": index,
            }
            for index, item in enumerate(candidates)
        ],
        "selected_generators": [
            _generator_to_metadata(item, batch_index=index)
            for index, item in enumerate(selected)
        ],
        "selected_factor_count": len(selected),
    }


class LRACESolver(BaseSolver):
    """Exploratory low-rank-factor-informed variational solver."""

    def __init__(
        self,
        *,
        spec,
        backend: BackendAdapter,
        seed: int,
        problem_summary: ProblemSummary | None = None,
        mapper: object | None = None,
    ) -> None:
        self.spec = spec
        self.backend = backend
        self.rng = np.random.default_rng(seed)
        self.problem_summary = problem_summary
        self.mapper = mapper

    def _initial_state(self, num_qubits: int) -> QuantumCircuit:
        circuit = QuantumCircuit(num_qubits)
        if self.problem_summary is None or self.mapper is None:
            return circuit
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SparseEfficiencyWarning)
            try:
                hartree_fock = HartreeFock(
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                )
            except Exception:
                return circuit
        circuit.compose(hartree_fock, inplace=True)
        return circuit

    def _build_ansatz(
        self,
        operator: SparsePauliOp,
        *,
        max_generators: int | None = None,
        selected_paulis: list[str] | None = None,
    ) -> tuple[QuantumCircuit, dict[str, Any]]:
        max_generators = max(
            int(max_generators if max_generators is not None else getattr(self.spec.ansatz, "reps", 1)),
            1,
        )
        if selected_paulis:
            max_generators = max(max_generators, len(selected_paulis))
        plan = build_low_rank_generator_plan(
            operator,
            max_generators=max_generators,
            selected_paulis=selected_paulis,
        )
        circuit = self._initial_state(operator.num_qubits)
        parameters: list[Parameter] = []
        for index, generator in enumerate(plan["selected_generators"]):
            parameter = Parameter(f"theta_lr_ace_{index}")
            parameters.append(parameter)
            circuit.append(
                PauliEvolutionGate(
                    SparsePauliOp.from_list([(str(generator["pauli"]), 1.0)]),
                    time=parameter,
                ),
                range(operator.num_qubits),
            )
        plan["ansatz_parameter_count"] = len(parameters)
        return circuit, plan

    def _initial_point(self, num_parameters: int) -> np.ndarray:
        if isinstance(self.spec.initial_point, list):
            values = np.asarray(self.spec.initial_point, dtype=float)
            if len(values) != num_parameters:
                raise ValueError(
                    f"LR-ACE initial_point length {len(values)} does not match parameter count {num_parameters}."
                )
            return values
        strategy = str(self.spec.initial_point).strip().lower()
        if strategy == "zeros":
            return np.zeros(num_parameters, dtype=float)
        if strategy == "random":
            return self.rng.uniform(-0.05, 0.05, size=num_parameters)
        raise ValueError(f"Unsupported LR-ACE initial point strategy: {self.spec.initial_point}")

    def _initial_point_for_strategy(
        self,
        strategy: str,
        num_parameters: int,
        *,
        previous_best: list[float] | None = None,
    ) -> np.ndarray:
        normalized = str(strategy).strip().lower()
        if normalized == "zeros":
            values = np.zeros(num_parameters, dtype=float)
        elif normalized == "random":
            values = self.rng.uniform(-0.05, 0.05, size=num_parameters)
        else:
            return self._initial_point(num_parameters)
        if previous_best:
            prefix = np.asarray(previous_best[:num_parameters], dtype=float)
            values[: len(prefix)] = prefix
        return values

    def _optimize(
        self,
        *,
        ansatz: QuantumCircuit,
        operator: SparsePauliOp,
        initial_point: np.ndarray,
        maxiter: int,
    ) -> tuple[float, list[float], bool, str, int, int]:
        evaluations = 0

        def objective(point: np.ndarray) -> float:
            nonlocal evaluations
            evaluations += 1
            return self.backend.estimate_expectation(ansatz, operator, point)

        if ansatz.num_parameters:
            result = minimize(
                objective,
                x0=initial_point,
                method=self.spec.optimizer.kind,
                tol=self.spec.optimizer.tol,
                options={"maxiter": maxiter},
            )
            energy = float(result.fun)
            optimal = [float(value) for value in np.asarray(result.x)]
            converged = bool(result.success)
            message = str(result.message)
            iterations = int(getattr(result, "nit", evaluations))
        else:
            energy = float(objective(np.asarray([], dtype=float)))
            optimal = []
            converged = True
            message = "LR-ACE found no non-diagonal low-rank factors; evaluated reference state."
            iterations = 1
        return energy, optimal, converged, message, iterations, evaluations

    def _adaptive_enabled(self) -> bool:
        adaptive = getattr(self.spec, "lr_ace_adaptive", None)
        return bool(getattr(adaptive, "enabled", False))

    def _scan_residual_candidates(
        self,
        operator: SparsePauliOp,
        *,
        selected_paulis: list[str],
        best_parameters: list[float],
        base_energy: float,
        candidate_scan_limit: int,
        residual_batch_size: int,
        residual_scan_angles: list[float],
        min_energy_improvement_hartree: float,
        expansion_index: int,
    ) -> tuple[list[str], dict[str, Any], int]:
        plan = build_low_rank_generator_plan(
            operator,
            max_generators=max(len(selected_paulis), 1),
            selected_paulis=selected_paulis,
        )
        selected_seen = set(selected_paulis)
        pool = [
            item
            for item in plan["candidate_generators"]
            if str(item["pauli"]) not in selected_seen
        ]
        scan_limit = max(int(candidate_scan_limit), 0)
        scan_angles = [float(value) for value in residual_scan_angles]
        scan_records: list[dict[str, Any]] = []
        evaluations = 0
        for candidate in pool[:scan_limit]:
            candidate_pauli = str(candidate["pauli"])
            trial_paulis = [*selected_paulis, candidate_pauli]
            trial_ansatz, _ = self._build_ansatz(
                operator,
                max_generators=len(trial_paulis),
                selected_paulis=trial_paulis,
            )
            best_scanned_energy: float | None = None
            best_angle: float | None = None
            for angle in scan_angles:
                point = np.zeros(trial_ansatz.num_parameters, dtype=float)
                prefix = np.asarray(best_parameters[: trial_ansatz.num_parameters], dtype=float)
                point[: len(prefix)] = prefix
                if trial_ansatz.num_parameters:
                    point[-1] = float(angle)
                energy = float(self.backend.estimate_expectation(trial_ansatz, operator, point))
                evaluations += 1
                if best_scanned_energy is None or energy < best_scanned_energy:
                    best_scanned_energy = energy
                    best_angle = float(angle)
            if best_scanned_energy is None:
                continue
            estimated_drop = float(base_energy) - float(best_scanned_energy)
            scan_records.append(
                {
                    "pauli": candidate_pauli,
                    "source_pauli": candidate["source_pauli"],
                    "adaptive_score": float(candidate["adaptive_score"]),
                    "best_scan_angle": best_angle,
                    "best_scanned_energy": float(best_scanned_energy),
                    "estimated_drop_hartree": float(estimated_drop),
                }
            )
        scan_records.sort(
            key=lambda item: (
                -float(item["estimated_drop_hartree"]),
                -float(item["adaptive_score"]),
                str(item["pauli"]),
            )
        )
        selected_records = [
            item
            for item in scan_records
            if float(item["estimated_drop_hartree"]) > float(min_energy_improvement_hartree)
        ][: max(int(residual_batch_size), 0)]
        selected = [str(item["pauli"]) for item in selected_records]
        expansion = {
            "expansion_index": int(expansion_index),
            "policy": "residual_guided",
            "candidate_pool_size": int(len(pool)),
            "candidate_scan_limit": int(scan_limit),
            "scanned_count": int(len(scan_records)),
            "selected_count": int(len(selected_records)),
            "scan_angles": scan_angles,
            "min_energy_improvement_hartree": float(min_energy_improvement_hartree),
            "best_estimated_drop_hartree": (
                None
                if not scan_records
                else float(scan_records[0]["estimated_drop_hartree"])
            ),
            "selected_generators": selected_records,
        }
        return selected, expansion, evaluations

    def _solve_adaptive(self, operator: SparsePauliOp) -> SolverOutcome:
        adaptive = self.spec.lr_ace_adaptive
        schedule = [max(int(value), 1) for value in adaptive.generator_schedule] or [1]
        maxiter_schedule = [max(int(value), 1) for value in adaptive.optimizer_maxiter_schedule] or [
            max(int(self.spec.optimizer.maxiter), 1)
        ]
        strategies = [str(value) for value in adaptive.initial_point_strategies] or ["zeros"]
        candidate_pool_policy = str(
            getattr(adaptive, "candidate_pool_policy", "residual_guided")
        ).strip().lower()
        candidate_scan_limit = max(int(getattr(adaptive, "candidate_scan_limit", 64)), 0)
        residual_batch_size = max(int(getattr(adaptive, "residual_batch_size", 8)), 0)
        residual_scan_angles = [
            float(value)
            for value in getattr(adaptive, "residual_scan_angles", [-0.15, -0.05, 0.05, 0.15])
        ]
        min_energy_improvement_hartree = float(
            getattr(adaptive, "min_energy_improvement_hartree", 2.0e-4)
        )
        max_adaptive_expansions = max(int(getattr(adaptive, "max_adaptive_expansions", 3)), 0)
        exact_energy = None
        if operator.num_qubits <= int(adaptive.uncompressed_check_qubit_limit):
            exact_energy = float(compute_exact_spectrum(operator, num_states=1).eigenvalues[0])

        started = perf_counter()
        stages: list[dict[str, Any]] = []
        expansions: list[dict[str, Any]] = []
        total_evaluations = 0
        best: dict[str, Any] | None = None
        best_plan: dict[str, Any] | None = None
        best_ansatz: QuantumCircuit | None = None
        selected_paulis: list[str] = []
        scheduled_counts = list(schedule)
        original_schedule_len = len(schedule)
        previous_stage_best_energy: float | None = None

        stage_index = 0
        while stage_index < len(scheduled_counts):
            generator_count = scheduled_counts[stage_index]
            if stages and perf_counter() - started >= float(adaptive.max_wall_time_seconds):
                break
            maxiter = maxiter_schedule[min(stage_index, len(maxiter_schedule) - 1)]
            ansatz, plan = self._build_ansatz(
                operator,
                max_generators=generator_count,
                selected_paulis=selected_paulis,
            )
            current_stage_paulis = [
                str(item["pauli"]) for item in plan["selected_generators"]
            ]
            stage_best_energy: float | None = None
            for strategy in strategies:
                restart_count = (
                    max(int(adaptive.random_restarts), 1)
                    if strategy.strip().lower() == "random"
                    else 1
                )
                for restart_index in range(restart_count):
                    if stages and perf_counter() - started >= float(adaptive.max_wall_time_seconds):
                        break
                    initial_point = self._initial_point_for_strategy(
                        strategy,
                        ansatz.num_parameters,
                        previous_best=(None if best is None else best["optimal_parameters"]),
                    )
                    energy, optimal, converged, message, iterations, evaluations = self._optimize(
                        ansatz=ansatz,
                        operator=operator,
                        initial_point=initial_point,
                        maxiter=maxiter,
                    )
                    total_evaluations += evaluations
                    exact_error = (
                        None if exact_energy is None else float(abs(float(energy) - exact_energy))
                    )
                    stage = {
                        "stage_index": len(stages),
                        "schedule_index": stage_index,
                        "generator_count": int(generator_count),
                        "parameter_count": int(ansatz.num_parameters),
                        "optimizer_maxiter": int(maxiter),
                        "initial_point_strategy": strategy,
                        "restart_index": int(restart_index),
                        "energy": float(energy),
                        "exact_error_hartree": exact_error,
                        "converged": bool(converged),
                        "iterations": int(iterations),
                        "evaluations": int(evaluations),
                        "optimizer_message": message,
                    }
                    stages.append(stage)
                    if stage_best_energy is None or float(energy) < stage_best_energy:
                        stage_best_energy = float(energy)
                    if best is None or float(energy) < float(best["energy"]):
                        best = {
                            **stage,
                            "optimal_parameters": list(optimal),
                            "optimizer_message": message,
                        }
                        best_plan = dict(plan)
                        best_ansatz = ansatz
                    if exact_error is not None and exact_error <= float(adaptive.target_error_hartree):
                        break
                if (
                    best is not None
                    and best.get("exact_error_hartree") is not None
                    and float(best["exact_error_hartree"]) <= float(adaptive.target_error_hartree)
                ):
                    break
            if (
                best is not None
                and best.get("exact_error_hartree") is not None
                and float(best["exact_error_hartree"]) <= float(adaptive.target_error_hartree)
            ):
                break
            selected_paulis = current_stage_paulis
            target_passed = (
                best is not None
                and best.get("exact_error_hartree") is not None
                and float(best["exact_error_hartree"]) <= float(adaptive.target_error_hartree)
            )
            if target_passed:
                break
            stage_improvement = (
                None
                if previous_stage_best_energy is None or stage_best_energy is None
                else float(previous_stage_best_energy) - float(stage_best_energy)
            )
            previous_stage_best_energy = stage_best_energy
            schedule_exhausted = stage_index >= len(scheduled_counts) - 1
            stalled = (
                stage_improvement is not None
                and stage_improvement < min_energy_improvement_hartree
            )
            should_scan = (
                candidate_pool_policy == "residual_guided"
                and max_adaptive_expansions > len(expansions)
                and residual_batch_size > 0
                and bool(residual_scan_angles)
                and best is not None
                and best_plan is not None
                and (schedule_exhausted or stalled)
            )
            if should_scan:
                selected_from_scan, expansion, scan_evaluations = self._scan_residual_candidates(
                    operator,
                    selected_paulis=[
                        str(item["pauli"]) for item in best_plan["selected_generators"]
                    ],
                    best_parameters=list(best["optimal_parameters"]),
                    base_energy=float(best["energy"]),
                    candidate_scan_limit=candidate_scan_limit,
                    residual_batch_size=residual_batch_size,
                    residual_scan_angles=residual_scan_angles,
                    min_energy_improvement_hartree=min_energy_improvement_hartree,
                    expansion_index=len(expansions),
                )
                expansion["trigger_stage_index"] = int(stage_index)
                expansion["trigger_stage_improvement_hartree"] = stage_improvement
                total_evaluations += scan_evaluations
                expansions.append(expansion)
                if selected_from_scan:
                    selected_paulis = [
                        str(item["pauli"]) for item in best_plan["selected_generators"]
                    ]
                    selected_paulis.extend(selected_from_scan)
                    next_generator_count = max(
                        len(selected_paulis),
                        int(generator_count) + len(selected_from_scan),
                    )
                    scheduled_counts.append(next_generator_count)
            stage_index += 1

        if best is None or best_plan is None or best_ansatz is None:
            ansatz, best_plan = self._build_ansatz(operator, max_generators=schedule[0])
            initial_point = self._initial_point(ansatz.num_parameters)
            energy, optimal, converged, message, iterations, evaluations = self._optimize(
                ansatz=ansatz,
                operator=operator,
                initial_point=initial_point,
                maxiter=maxiter_schedule[0],
            )
            total_evaluations += evaluations
            best_ansatz = ansatz
            exact_error = None if exact_energy is None else float(abs(float(energy) - exact_energy))
            best = {
                "stage_index": 0,
                "energy": float(energy),
                "exact_error_hartree": exact_error,
                "converged": bool(converged),
                "iterations": int(iterations),
                "evaluations": int(evaluations),
                "optimal_parameters": list(optimal),
                "optimizer_message": message,
            }
            stages.append(dict(best))

        trust_label = "passed_compressed_with_budget"
        if exact_energy is None:
            trust_label = "passed_compressed_with_budget"
        elif best.get("exact_error_hartree") is None or float(best["exact_error_hartree"]) > float(
            adaptive.target_error_hartree
        ):
            trust_label = "ansatz_limited"
        best_plan["optimized_parameters"] = list(best["optimal_parameters"])
        best_stage_index = int(best["stage_index"])
        best_plan["adaptive"] = {
            "enabled": True,
            "target_error_hartree": float(adaptive.target_error_hartree),
            "max_wall_time_seconds": float(adaptive.max_wall_time_seconds),
            "candidate_pool_policy": candidate_pool_policy,
            "candidate_scan_limit": int(candidate_scan_limit),
            "residual_batch_size": int(residual_batch_size),
            "residual_scan_angles": residual_scan_angles,
            "min_energy_improvement_hartree": float(min_energy_improvement_hartree),
            "max_adaptive_expansions": int(max_adaptive_expansions),
            "exact_reference_available": exact_energy is not None,
            "exact_solver_energy": exact_energy,
            "stages": stages,
            "expansions": expansions,
            "scheduled_generator_counts": scheduled_counts,
            "original_generator_schedule_length": int(original_schedule_len),
            "best_stage_index": best_stage_index,
            "best_energy": float(best["energy"]),
            "best_exact_error_hartree": best.get("exact_error_hartree"),
            "trust_label": trust_label,
            "uncompressed_check_triggered": False,
        }
        return SolverOutcome(
            total_energy=float(best["energy"]),
            converged=bool(best["converged"]),
            iterations=int(best["iterations"]),
            evaluations=int(total_evaluations),
            optimal_parameters=list(best["optimal_parameters"]),
            metadata={
                "ansatz_circuit": best_ansatz,
                "ansatz_num_parameters": best_ansatz.num_parameters,
                "optimizer_message": str(best["optimizer_message"]),
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "lr_ace adaptive local exact-baseline gate",
                "scientific_risk_notes": [
                    "LR-ACE adaptive scheduling is exploratory and benchmark-local.",
                    "Adaptive generator and optimizer budgets do not imply publication-validated scaling.",
                ],
                "lr_ace": best_plan,
            },
        )

    def solve(self, operator: SparsePauliOp) -> SolverOutcome:
        if self._adaptive_enabled():
            return self._solve_adaptive(operator)
        ansatz, plan = self._build_ansatz(operator)
        initial_point = self._initial_point(ansatz.num_parameters)
        energy, optimal, converged, message, iterations, evaluations = self._optimize(
            ansatz=ansatz,
            operator=operator,
            initial_point=initial_point,
            maxiter=self.spec.optimizer.maxiter,
        )
        plan["optimized_parameters"] = optimal
        return SolverOutcome(
            total_energy=energy,
            converged=converged,
            iterations=iterations,
            evaluations=evaluations,
            optimal_parameters=optimal,
            metadata={
                "ansatz_circuit": ansatz,
                "ansatz_num_parameters": ansatz.num_parameters,
                "optimizer_message": message,
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "lr_ace local exact-baseline gate",
                "scientific_risk_notes": [
                    "LR-ACE is a QCchem-native exploratory solver; current evidence is benchmark-local only.",
                    "Dominant low-rank factor selection is heuristic and not yet publication-validated.",
                ],
                "lr_ace": plan,
            },
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None) -> BaseSolver:
    if backend is None:
        raise ValueError("LR-ACE requires an execution backend.")
    return LRACESolver(
        spec=spec,
        backend=backend,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
