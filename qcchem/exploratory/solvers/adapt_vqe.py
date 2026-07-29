"""Exploratory evidence-gated ADAPT-VQE implementation."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize

from qcchem.backends import BackendAdapter
from qcchem.solvers import build_solver as build_core_solver
from qcchem.solvers.base import BaseSolver, SolverOutcome


class ExploratoryADAPTVQESolver(BaseSolver):
    """Evidence-gated ADAPT-VQE wrapper using QCchem VQE execution.

    The implementation keeps the existing QCchem VQE path as the trusted
    fallback, then runs a finite-difference qubit-Pauli ADAPT growth pass. The
    adaptive energy replaces the delegated VQE energy only when it is explicitly
    lower, because this solver remains exploratory until benchmark gates promote
    it.
    """

    def __init__(self, delegate: BaseSolver, spec, backend: BackendAdapter) -> None:
        self._delegate = delegate
        self._spec = spec
        self._backend = backend

    @staticmethod
    def _public_entry(entry: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in entry.items() if not str(key).startswith("_")}

    def _ansatz_operator_candidates(
        self,
        base_ansatz: QuantumCircuit | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if base_ansatz is None or not hasattr(base_ansatz, "operators"):
            return [], []
        try:
            operators = list(getattr(base_ansatz, "operators") or [])
        except Exception:
            return [], []
        if not operators:
            return [], []
        try:
            excitation_list = list(getattr(base_ansatz, "excitation_list") or [])
        except Exception:
            excitation_list = []
        candidates: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for index, excitation_operator in enumerate(operators):
            if not isinstance(excitation_operator, SparsePauliOp):
                continue
            simplified = excitation_operator.simplify(atol=1.0e-12)
            labels = list(simplified.paulis.to_labels())
            coeff_l1 = float(sum(abs(complex(coeff)) for coeff in simplified.coeffs))
            if not labels or coeff_l1 == 0.0:
                continue
            max_weight = max(sum(1 for char in label if char != "I") for label in labels)
            two_qubit_increment = max(max_weight - 1, 0) * 2
            priority = coeff_l1 / max(two_qubit_increment, 1)
            entry = {
                "operator_id": f"excitation_{index}",
                "pauli": labels[0] if len(labels) == 1 else "multi_pauli",
                "pauli_terms": labels,
                "coefficient_l1": coeff_l1,
                "coefficient_abs": coeff_l1,
                "gradient_proxy": coeff_l1 * float(self._spec.e_adapt.finite_difference_step),
                "finite_difference_step": float(self._spec.e_adapt.finite_difference_step),
                "two_qubit_increment": two_qubit_increment,
                "low_rank_priority_score": priority,
                "pool_origin": "ansatz_excitation_operators",
                "excitation": str(excitation_list[index]) if index < len(excitation_list) else None,
                "_qubit_operator": simplified,
            }
            if two_qubit_increment > int(self._spec.e_adapt.reject_if_two_qubit_increment_gt):
                rejected.append({**entry, "reason": "two_qubit_increment_gate"})
                continue
            candidates.append(entry)
        candidates.sort(key=lambda item: (-float(item["coefficient_abs"]), -float(item["low_rank_priority_score"])))
        return candidates, rejected

    def _operator_candidates(
        self,
        operator,
        base_ansatz: QuantumCircuit | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        ansatz_candidates, ansatz_rejected = self._ansatz_operator_candidates(base_ansatz)
        if ansatz_candidates:
            return ansatz_candidates, ansatz_rejected

        labels = list(operator.paulis.to_labels())
        coeffs = [float(abs(complex(coeff))) for coeff in operator.coeffs]
        candidates: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for index, (label, coeff) in enumerate(zip(labels, coeffs, strict=True)):
            if label.count("I") == len(label):
                continue
            two_qubit_increment = max(sum(1 for char in label if char != "I") - 1, 0) * 2
            priority = coeff / max(two_qubit_increment, 1)
            gradient_proxy = coeff * float(self._spec.e_adapt.finite_difference_step)
            entry = {
                "operator_id": f"pauli_{index}",
                "pauli": label,
                "coefficient_abs": coeff,
                "gradient_proxy": gradient_proxy,
                "finite_difference_step": float(self._spec.e_adapt.finite_difference_step),
                "two_qubit_increment": two_qubit_increment,
                "low_rank_priority_score": priority,
                "pool_origin": "hamiltonian_pauli_terms",
                "_qubit_operator": SparsePauliOp.from_list([(label, 1.0)]),
            }
            if two_qubit_increment > int(self._spec.e_adapt.reject_if_two_qubit_increment_gt):
                rejected.append({**entry, "reason": "two_qubit_increment_gate"})
                continue
            candidates.append(entry)
        candidates.sort(key=lambda item: (-float(item["coefficient_abs"]), -float(item["low_rank_priority_score"])))
        return candidates, rejected

    def _adaptive_ansatz(
        self,
        base_ansatz: QuantumCircuit,
        selected: list[dict[str, Any]],
    ) -> tuple[QuantumCircuit, list[Any]]:
        circuit = QuantumCircuit(base_ansatz.num_qubits)
        circuit.compose(base_ansatz, inplace=True)
        adaptive_parameters = list(ParameterVector("eadapt", len(selected)))
        for parameter, entry in zip(adaptive_parameters, selected, strict=True):
            candidate_operator = entry.get("_qubit_operator")
            if not isinstance(candidate_operator, SparsePauliOp):
                candidate_operator = SparsePauliOp.from_list([(str(entry["pauli"]), 1.0)])
            pauli = candidate_operator
            circuit.append(PauliEvolutionGate(pauli, time=parameter), range(base_ansatz.num_qubits))
        circuit.name = "e_adapt_vqe"
        return circuit, adaptive_parameters

    @staticmethod
    def _parameter_vector(
        circuit: QuantumCircuit,
        base_ansatz: QuantumCircuit,
        base_values: np.ndarray,
        adaptive_parameters: list[Any],
        adaptive_values: list[float],
    ) -> np.ndarray:
        base_parameter_values = {
            parameter: float(value)
            for parameter, value in zip(list(base_ansatz.parameters), base_values, strict=True)
        }
        adaptive_parameter_values = {
            parameter: float(value)
            for parameter, value in zip(adaptive_parameters, adaptive_values, strict=True)
        }
        values = []
        for parameter in circuit.parameters:
            if parameter in base_parameter_values:
                values.append(base_parameter_values[parameter])
            elif parameter in adaptive_parameter_values:
                values.append(adaptive_parameter_values[parameter])
            else:
                values.append(0.0)
        return np.asarray(values, dtype=float)

    @staticmethod
    def _trajectory_parameters(outcome: SolverOutcome, fallback: list[float]) -> np.ndarray:
        trajectory = outcome.metadata.get("evaluation_trajectory")
        if isinstance(trajectory, list) and trajectory:
            first = trajectory[0]
            if isinstance(first, dict) and isinstance(first.get("parameters"), list):
                return np.asarray(first["parameters"], dtype=float)
        return np.asarray(fallback, dtype=float)

    def _finite_difference_gradient(
        self,
        operator,
        base_ansatz: QuantumCircuit,
        selected: list[dict[str, Any]],
        current_values: np.ndarray,
        current_energy: float,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        step = max(float(self._spec.e_adapt.finite_difference_step), 1.0e-8)
        trial_selected = [*selected, candidate]
        trial_circuit, adaptive_parameters = self._adaptive_ansatz(base_ansatz, trial_selected)
        selected_values = [float(entry.get("optimized_parameter", 0.0)) for entry in selected]
        plus_values = self._parameter_vector(
            trial_circuit,
            base_ansatz,
            current_values,
            adaptive_parameters,
            [*selected_values, step],
        )
        minus_values = self._parameter_vector(
            trial_circuit,
            base_ansatz,
            current_values,
            adaptive_parameters,
            [*selected_values, -step],
        )
        plus_energy = float(self._backend.evaluate(trial_circuit, operator, plus_values).value)
        minus_energy = float(self._backend.evaluate(trial_circuit, operator, minus_values).value)
        scan_angles = sorted({-25.0 * step, -10.0 * step, -5.0 * step, -step, step, 5.0 * step, 10.0 * step, 25.0 * step})
        scan_records = []
        for angle in scan_angles:
            values = self._parameter_vector(
                trial_circuit,
                base_ansatz,
                current_values,
                adaptive_parameters,
                [*selected_values, angle],
            )
            energy = float(self._backend.evaluate(trial_circuit, operator, values).value)
            scan_records.append({"angle": float(angle), "energy": energy})
        best_scan = min(scan_records, key=lambda item: float(item["energy"])) if scan_records else None
        energy_lowering_scan = (
            max(0.0, float(current_energy) - float(best_scan["energy"]))
            if best_scan is not None
            else 0.0
        )
        gradient = (plus_energy - minus_energy) / (2.0 * step)
        return {
            **candidate,
            "finite_difference_plus_energy": plus_energy,
            "finite_difference_minus_energy": minus_energy,
            "gradient": float(gradient),
            "gradient_abs": float(abs(gradient)),
            "energy_lowering_scan_hartree": float(energy_lowering_scan),
            "best_scan_angle": float(best_scan["angle"]) if best_scan is not None else None,
            "best_scan_energy": float(best_scan["energy"]) if best_scan is not None else None,
            "angle_scan": scan_records,
            "gradient_evaluation_status": "finite_difference",
        }

    def _optimize_adaptive_ansatz(
        self,
        operator,
        base_ansatz: QuantumCircuit,
        selected: list[dict[str, Any]],
        initial_base_values: np.ndarray,
        initial_adaptive_values: list[float],
    ) -> tuple[float, np.ndarray, QuantumCircuit, int, int, list[dict[str, Any]], str]:
        circuit, adaptive_parameters = self._adaptive_ansatz(base_ansatz, selected)
        initial_point = self._parameter_vector(
            circuit,
            base_ansatz,
            initial_base_values,
            adaptive_parameters,
            initial_adaptive_values,
        )
        evaluations = 0
        trajectory: list[dict[str, Any]] = []

        def objective(point: np.ndarray) -> float:
            nonlocal evaluations
            evaluations += 1
            estimate = self._backend.evaluate(circuit, operator, point)
            energy = float(estimate.value)
            trajectory.append(
                {
                    "evaluation_index": evaluations,
                    "parameters": [float(value) for value in np.asarray(point, dtype=float)],
                    "energy": energy,
                    "reported_std": float(estimate.reported_std),
                    "seed": estimate.seed,
                    "shots": estimate.shots,
                    "backend_metadata": dict(estimate.metadata),
                }
            )
            return energy

        result = minimize(
            objective,
            x0=initial_point,
            method=self._spec.optimizer.kind,
            tol=self._spec.optimizer.tol,
            options={"maxiter": self._spec.optimizer.maxiter},
        )
        best_energy = float(result.fun)
        best_parameters = np.asarray(result.x, dtype=float)
        if trajectory:
            best_record = min(trajectory, key=lambda item: float(item["energy"]))
            best_energy = float(best_record["energy"])
            best_parameters = np.asarray(best_record["parameters"], dtype=float)
        return (
            best_energy,
            best_parameters,
            circuit,
            int(getattr(result, "nit", evaluations)),
            int(evaluations),
            trajectory,
            str(result.message),
        )

    def _run_adaptive_growth(
        self,
        operator,
        base_ansatz: QuantumCircuit,
        delegate_outcome: SolverOutcome,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        base_parameter_count = len(list(base_ansatz.parameters))
        delegate_parameters = np.asarray(delegate_outcome.optimal_parameters, dtype=float)
        if len(delegate_parameters) != base_parameter_count:
            return [], [], {
                "status": "skipped",
                "reason": "delegate_parameter_count_mismatch",
                "delegate_parameter_count": int(len(delegate_parameters)),
                "base_ansatz_parameter_count": int(base_parameter_count),
            }

        current_base_values = self._trajectory_parameters(delegate_outcome, delegate_outcome.optimal_parameters)
        if len(current_base_values) != base_parameter_count:
            current_base_values = delegate_parameters
        current_adaptive_values: list[float] = []
        current_energy = float(self._backend.evaluate(base_ansatz, operator, current_base_values).value)
        candidates, rejected = self._operator_candidates(operator, base_ansatz)
        selected: list[dict[str, Any]] = []
        gradient_history: list[dict[str, Any]] = []
        optimization_history: list[dict[str, Any]] = []
        max_operators = max(int(self._spec.e_adapt.max_operators), 0)
        threshold = float(self._spec.e_adapt.gradient_threshold)
        total_evaluations = 1
        total_iterations = 0
        optimizer_message = "not_run"
        final_circuit: QuantumCircuit | None = None
        adaptive_optimum: np.ndarray | None = None
        operator_acceptance_min_improvement = 0.0
        no_improvement_rejection_count = 0

        for step in range(1, max_operators + 1):
            if not candidates:
                break
            evaluated: list[dict[str, Any]] = []
            for candidate in candidates:
                try:
                    evaluated.append(
                        self._finite_difference_gradient(
                            operator,
                            base_ansatz,
                            selected,
                            current_base_values,
                            current_energy,
                            candidate,
                        )
                    )
                    total_evaluations += 10
                except Exception as exc:  # pragma: no cover - defensive fallback for backend-specific circuits.
                    evaluated.append(
                        {
                            **candidate,
                            "gradient": None,
                            "gradient_abs": float(candidate["gradient_proxy"]),
                            "energy_lowering_scan_hartree": 0.0,
                            "gradient_evaluation_status": "failed",
                            "gradient_evaluation_error": str(exc),
                        }
                    )
            evaluated.sort(
                key=lambda item: (
                    -max(
                        float(item.get("gradient_abs", 0.0)),
                        float(item.get("energy_lowering_scan_hartree", 0.0)) / max(float(item["finite_difference_step"]), 1.0e-8),
                    ),
                    -float(item.get("energy_lowering_scan_hartree", 0.0)),
                    -float(item["low_rank_priority_score"]) if self._spec.e_adapt.use_low_rank_priority else 0.0,
                )
            )
            best = evaluated[0]
            energy_scan_threshold = max(threshold * max(float(best["finite_difference_step"]), 1.0e-8), 1.0e-10)
            gradient_history.append(
                {
                    "step": step,
                    "operator_id": best["operator_id"],
                    "pauli": best["pauli"],
                    "gradient": best.get("gradient"),
                    "gradient_abs": best.get("gradient_abs"),
                    "gradient_proxy": best.get("gradient_proxy"),
                    "gradient_evaluation_status": best.get("gradient_evaluation_status"),
                    "energy_lowering_scan_hartree": best.get("energy_lowering_scan_hartree"),
                    "best_scan_angle": best.get("best_scan_angle"),
                    "energy_lowering_proxy_hartree": max(
                        float(best.get("gradient_abs", 0.0)) ** 2,
                        float(best.get("energy_lowering_scan_hartree", 0.0)),
                    ),
                }
            )
            if (
                float(best.get("gradient_abs", 0.0)) < threshold
                and float(best.get("energy_lowering_scan_hartree", 0.0)) < energy_scan_threshold
            ):
                rejected.extend({**entry, "reason": "gradient_threshold"} for entry in evaluated)
                candidates = []
                break

            selected_entry = {
                **best,
                "selected_step": step,
                "energy_before_optimization": current_energy,
            }
            remaining_by_id = {entry["operator_id"]: entry for entry in candidates}
            remaining_by_id.pop(str(best["operator_id"]), None)
            candidates = list(remaining_by_id.values())
            trial_selected = [*selected, selected_entry]
            try:
                (
                    energy,
                    optimum,
                    final_circuit,
                    iterations,
                    evaluations,
                    trajectory,
                    optimizer_message,
                ) = self._optimize_adaptive_ansatz(
                    operator,
                    base_ansatz,
                    trial_selected,
                    current_base_values,
                    [*current_adaptive_values, 0.0],
                )
                total_evaluations += evaluations
                total_iterations += iterations
                energy_before_optimization = float(selected_entry["energy_before_optimization"])
                energy_after_optimization = float(energy)
                energy_lowering = energy_before_optimization - energy_after_optimization
                trial_circuit, adaptive_parameters = self._adaptive_ansatz(base_ansatz, trial_selected)
                base_parameter_values = dict(zip(list(trial_circuit.parameters), optimum, strict=True))
                trial_base_values = np.asarray(
                    [float(base_parameter_values[parameter]) for parameter in base_ansatz.parameters],
                    dtype=float,
                )
                trial_adaptive_values = [
                    float(base_parameter_values[parameter]) for parameter in adaptive_parameters
                ]
                accepted_operator = energy_lowering > operator_acceptance_min_improvement
                selected_entry["energy_after_optimization"] = energy_after_optimization
                selected_entry["energy_lowering_hartree"] = energy_lowering
                selected_entry["optimized_parameter"] = trial_adaptive_values[-1]
                selected_entry["operator_acceptance_min_improvement_hartree"] = (
                    operator_acceptance_min_improvement
                )
                selected_entry["optimization_status"] = (
                    "accepted" if accepted_operator else "rejected_no_improvement"
                )
                selected_entry["selection_status"] = (
                    "accepted_after_optimization"
                    if accepted_operator
                    else "rejected_after_optimization"
                )
                optimization_history.append(
                    {
                        "step": step,
                        "operator_id": selected_entry["operator_id"],
                        "energy": energy_after_optimization,
                        "energy_before_optimization": energy_before_optimization,
                        "energy_lowering_hartree": energy_lowering,
                        "accepted": accepted_operator,
                        "operator_acceptance_min_improvement_hartree": (
                            operator_acceptance_min_improvement
                        ),
                        "iterations": iterations,
                        "evaluations": evaluations,
                        "optimizer_message": optimizer_message,
                        "trajectory": trajectory,
                    }
                )
                if not accepted_operator:
                    no_improvement_rejection_count += 1
                    selected_entry["optimizer_message"] = optimizer_message
                    rejected.append(
                        {
                            **selected_entry,
                            "reason": "adaptive_optimization_no_improvement",
                        }
                    )
                    break
                current_energy = energy_after_optimization
                adaptive_optimum = optimum
                current_base_values = trial_base_values
                current_adaptive_values = trial_adaptive_values
            except Exception as exc:  # pragma: no cover - defensive fallback for backend-specific circuits.
                selected_entry["optimization_status"] = "failed"
                selected_entry["optimization_error"] = str(exc)
                rejected.append({**selected_entry, "reason": "adaptive_optimization_failed"})
                break
            selected.append(selected_entry)

        if selected:
            try:
                (
                    polish_energy,
                    polish_optimum,
                    polish_circuit,
                    polish_iterations,
                    polish_evaluations,
                    polish_trajectory,
                    polish_message,
                ) = self._optimize_adaptive_ansatz(
                    operator,
                    base_ansatz,
                    selected,
                    delegate_parameters,
                    [0.0] * len(selected),
                )
                total_evaluations += polish_evaluations
                total_iterations += polish_iterations
                optimizer_message = polish_message
                accepted_polish = polish_energy <= current_energy
                optimization_history.append(
                    {
                        "stage": "delegate_warm_start_polish",
                        "energy": polish_energy,
                        "accepted": accepted_polish,
                        "iterations": polish_iterations,
                        "evaluations": polish_evaluations,
                        "optimizer_message": polish_message,
                        "trajectory": polish_trajectory,
                    }
                )
                if accepted_polish:
                    current_energy = polish_energy
                    adaptive_optimum = polish_optimum
                    final_circuit = polish_circuit
                    polish_circuit_for_map, adaptive_parameters = self._adaptive_ansatz(base_ansatz, selected)
                    parameter_values = dict(zip(list(polish_circuit_for_map.parameters), polish_optimum, strict=True))
                    current_base_values = np.asarray(
                        [float(parameter_values[parameter]) for parameter in base_ansatz.parameters],
                        dtype=float,
                    )
                    current_adaptive_values = [
                        float(parameter_values[parameter]) for parameter in adaptive_parameters
                    ]
                    for entry, value in zip(selected, current_adaptive_values, strict=True):
                        entry["optimized_parameter"] = float(value)
                    selected[-1]["energy_after_optimization"] = current_energy
                    selected[-1]["energy_lowering_hartree"] = (
                        float(selected[-1]["energy_before_optimization"]) - current_energy
                    )
            except Exception as exc:  # pragma: no cover - defensive fallback for backend-specific circuits.
                optimization_history.append(
                    {
                        "stage": "delegate_warm_start_polish",
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        for entry in candidates:
            rejected.append({**entry, "reason": "max_operators_gate"})

        depth_growth = [
            {
                "step": step,
                "operator_id": entry["operator_id"],
                "two_qubit_increment": entry["two_qubit_increment"],
                "cumulative_two_qubit_increment": sum(
                    int(item["two_qubit_increment"]) for item in selected[:step]
                ),
            }
            for step, entry in enumerate(selected, start=1)
        ]
        return selected, rejected, {
            "status": "completed" if selected else "no_operator_selected",
            "gradient_history": gradient_history,
            "depth_growth": depth_growth,
            "optimization_history": optimization_history,
            "adaptive_energy": current_energy if selected else None,
            "adaptive_iterations": total_iterations,
            "adaptive_evaluations": total_evaluations,
            "adaptive_optimizer_message": optimizer_message,
            "operator_acceptance_policy": "optimized_energy_must_improve_current_energy",
            "operator_acceptance_min_improvement_hartree": operator_acceptance_min_improvement,
            "no_improvement_rejection_count": no_improvement_rejection_count,
            "base_reference_energy": float(delegate_outcome.total_energy),
            "gradient_reference": "delegate_initial_point_or_fallback",
            "ansatz_parameter_count": base_parameter_count + len(selected),
            "ansatz_circuit": final_circuit,
            "adaptive_optimal_parameters": (
                [float(value) for value in adaptive_optimum]
                if adaptive_optimum is not None
                else []
            ),
        }

    def solve(self, operator) -> SolverOutcome:
        outcome = self._delegate.solve(operator)
        base_ansatz = outcome.metadata.get("ansatz_circuit")
        if not isinstance(base_ansatz, QuantumCircuit):
            candidates, rejected = self._operator_candidates(operator, None)
            selected = []
            rejected.extend({**entry, "reason": "delegate_ansatz_unavailable"} for entry in candidates)
            growth = {
                "status": "skipped",
                "reason": "delegate_ansatz_unavailable",
                "gradient_history": [],
                "depth_growth": [],
                "adaptive_energy": None,
                "adaptive_iterations": 0,
                "adaptive_evaluations": 0,
                "adaptive_optimizer_message": "not_run",
                "ansatz_parameter_count": None,
                "ansatz_circuit": None,
            }
        else:
            selected, rejected, growth = self._run_adaptive_growth(operator, base_ansatz, outcome)
        adaptive_energy = growth.get("adaptive_energy")
        replacement_min_improvement = max(
            1.0e-10,
            float(self._spec.e_adapt.gradient_threshold) * float(self._spec.e_adapt.finite_difference_step),
        )
        adaptive_energy_improvement = (
            float(outcome.total_energy) - float(adaptive_energy)
            if adaptive_energy is not None
            else None
        )
        adaptive_replaces_delegate = (
            adaptive_energy_improvement is not None
            and adaptive_energy_improvement > replacement_min_improvement
        )
        total_energy = float(adaptive_energy) if adaptive_replaces_delegate else outcome.total_energy
        optimal_parameters = outcome.optimal_parameters
        if adaptive_replaces_delegate and growth.get("adaptive_optimal_parameters"):
            optimal_parameters = list(growth["adaptive_optimal_parameters"])
        metadata = dict(outcome.metadata)
        if adaptive_replaces_delegate and isinstance(growth.get("ansatz_circuit"), QuantumCircuit):
            metadata["ansatz_circuit"] = growth["ansatz_circuit"]
            metadata["ansatz_num_parameters"] = int(growth.get("ansatz_parameter_count", 0) or 0)
            metadata["optimizer_message"] = str(growth.get("adaptive_optimizer_message"))
        trust_gate = "passed" if selected else "exploratory"
        public_selected = [self._public_entry(entry) for entry in selected]
        public_rejected = [self._public_entry(entry) for entry in rejected]
        selected_lowerings = [
            float(entry["energy_lowering_hartree"])
            for entry in public_selected
            if entry.get("energy_lowering_hartree") is not None
        ]
        depth_growth = list(growth.get("depth_growth", []))
        final_depth_growth = depth_growth[-1] if depth_growth else {}
        if adaptive_energy_improvement is None:
            adaptive_improvement_status = "not_evaluated"
        elif adaptive_replaces_delegate:
            adaptive_improvement_status = "replaces_delegate"
        elif adaptive_energy_improvement > 0.0:
            adaptive_improvement_status = "positive_below_replacement_threshold"
        elif adaptive_energy_improvement == 0.0:
            adaptive_improvement_status = "no_delegate_improvement"
        else:
            adaptive_improvement_status = "adaptive_energy_above_delegate"
        replacement_threshold_ratio = (
            float(adaptive_energy_improvement) / replacement_min_improvement
            if adaptive_energy_improvement is not None and replacement_min_improvement > 0.0
            else None
        )
        optimization_signal_present = bool(
            selected
            and adaptive_energy_improvement is not None
            and adaptive_energy_improvement > 0.0
        )
        metadata.update(
            {
                "module_origin": "exploratory",
                "capability_tier": "exploratory",
                "validation_scope": "evidence_gated_adapt_vqe_v1",
                "scientific_risk_notes": [
                    "E-ADAPT v1 grows a finite-difference qubit-Pauli adaptive ansatz but remains exploratory until benchmark gates promote it.",
                    "Selected operators are PauliEvolutionGate directions from the mapped qubit Hamiltonian, not a chemically complete fermionic excitation pool.",
                ],
                "delegated_execution": "vqe",
                "e_adapt_result": {
                    "selected_operators": public_selected,
                    "rejected_operators": public_rejected,
                    "gradient_history": list(growth.get("gradient_history", [])),
                    "depth_growth": depth_growth,
                    "adaptive_optimization": {
                        "status": growth.get("status"),
                        "energy_replaces_delegate": adaptive_replaces_delegate,
                        "delegate_energy": float(outcome.total_energy),
                        "adaptive_energy": adaptive_energy,
                        "delegate_energy_improvement_hartree": adaptive_energy_improvement,
                        "replacement_min_improvement_hartree": replacement_min_improvement,
                        "delegate_improvement_to_replacement_threshold_ratio": (
                            replacement_threshold_ratio
                        ),
                        "adaptive_improvement_status": adaptive_improvement_status,
                        "optimization_signal_present": optimization_signal_present,
                        "selected_operator_count": len(public_selected),
                        "cumulative_selected_energy_lowering_hartree": (
                            float(sum(selected_lowerings)) if selected_lowerings else 0.0
                        ),
                        "max_selected_energy_lowering_hartree": (
                            float(max(selected_lowerings)) if selected_lowerings else None
                        ),
                        "min_selected_energy_lowering_hartree": (
                            float(min(selected_lowerings)) if selected_lowerings else None
                        ),
                        "final_cumulative_two_qubit_increment": (
                            final_depth_growth.get("cumulative_two_qubit_increment")
                        ),
                        "operator_acceptance_policy": growth.get("operator_acceptance_policy"),
                        "operator_acceptance_min_improvement_hartree": growth.get(
                            "operator_acceptance_min_improvement_hartree"
                        ),
                        "no_improvement_rejection_count": int(
                            growth.get("no_improvement_rejection_count", 0)
                        ),
                        "adaptive_iterations": int(growth.get("adaptive_iterations", 0)),
                        "adaptive_evaluations": int(growth.get("adaptive_evaluations", 0)),
                        "adaptive_evaluations_per_selected_operator": (
                            float(growth.get("adaptive_evaluations", 0)) / len(public_selected)
                            if public_selected
                            else None
                        ),
                        "optimizer_message": growth.get("adaptive_optimizer_message"),
                        "optimization_history": list(growth.get("optimization_history", [])),
                        "ansatz_parameter_count": growth.get("ansatz_parameter_count"),
                        "adaptive_optimal_parameters": list(growth.get("adaptive_optimal_parameters", [])),
                        "gradient_reference": growth.get("gradient_reference"),
                    },
                    "symmetry_audit": {
                        "z2_tapering_requested": bool(self._spec.e_adapt.use_z2_tapering),
                        "point_group_filter_requested": bool(self._spec.e_adapt.use_point_group_filter),
                        "status": "metadata_gated",
                    },
                    "low_rank_priority_scores": {
                        str(entry["operator_id"]): float(entry["low_rank_priority_score"])
                        for entry in selected
                    },
                    "ansatz_trust_gate": trust_gate,
                },
            }
        )
        return SolverOutcome(
            total_energy=total_energy,
            converged=outcome.converged,
            iterations=outcome.iterations + int(growth.get("adaptive_iterations", 0)),
            evaluations=outcome.evaluations + int(growth.get("adaptive_evaluations", 0)),
            optimal_parameters=[float(value) for value in optimal_parameters],
            metadata=metadata,
        )


def build_solver(spec, backend, seed, problem_summary=None, mapper=None) -> BaseSolver:
    delegate_spec = replace(spec, kind="vqe", experimental=False)
    delegate = build_core_solver(
        delegate_spec,
        backend=backend,
        seed=seed,
        problem_summary=problem_summary,
        mapper=mapper,
    )
    return ExploratoryADAPTVQESolver(delegate, spec, backend)
