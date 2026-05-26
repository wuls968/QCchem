"""Variational ground-state solver using primitives V2."""

from __future__ import annotations

import warnings

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import n_local
from qiskit_nature.second_q.circuit.library import HartreeFock, PUCCD, PUCCSD, SUCCD, UCCSD
from scipy.sparse import SparseEfficiencyWarning
from scipy.optimize import minimize

from qcchem.backends import BackendAdapter
from qcchem.core import ProblemSummary, SolverSpec
from qcchem.solvers.base import BaseSolver, SolverOutcome
from qcchem.solvers.exact import ExactDiagonalizationSolver


class VQESolver(BaseSolver):
    """A thin QCchem-owned VQE implementation."""

    def __init__(
        self,
        spec: SolverSpec,
        backend: BackendAdapter,
        seed: int,
        problem_summary: ProblemSummary | None = None,
        mapper: object | None = None,
        field_model_context: dict[str, object] | None = None,
    ) -> None:
        self.spec = spec
        self.backend = backend
        self.rng = np.random.default_rng(seed)
        self.problem_summary = problem_summary
        self.mapper = mapper
        self.field_model_context = field_model_context or {}

    def _hardware_efficient_layer(self, num_qubits: int):
        entanglement_blocks = self.spec.ansatz.entanglement_blocks
        entanglement = self.spec.ansatz.entanglement
        if num_qubits < 2:
            entanglement_blocks = []
            entanglement = []
        return n_local(
            num_qubits,
            rotation_blocks=self.spec.ansatz.rotation_blocks,
            entanglement_blocks=entanglement_blocks,
            entanglement=entanglement,
            reps=self.spec.ansatz.reps,
            skip_final_rotation_layer=self.spec.ansatz.skip_final_rotation_layer,
        )

    def _build_cavity_twolocal(self, num_qubits: int):
        cavity = self.field_model_context.get("cavity_qed")
        if not isinstance(cavity, dict):
            raise ValueError("cavity_twolocal ansatz requires cavity-QED field-model context.")
        photon_mode_qubits = [int(value) for value in cavity.get("photon_mode_qubits", [])]
        electronic_qubits = int(cavity.get("electronic_qubits", 0))
        photon_qubits = int(sum(photon_mode_qubits))
        if photon_qubits <= 0 or electronic_qubits <= 0 or photon_qubits + electronic_qubits != num_qubits:
            raise ValueError("cavity_twolocal ansatz received inconsistent electron/photon qubit metadata.")
        initial = QuantumCircuit(num_qubits, name="cavity_hf_photon_vacuum")
        mode_offset = 0
        for mode_qubit_count in photon_mode_qubits:
            initial.x(mode_offset)
            mode_offset += int(mode_qubit_count)
        if self.problem_summary is not None and self.mapper is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SparseEfficiencyWarning)
                hf = HartreeFock(
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                )
            initial.compose(
                hf,
                qubits=list(range(photon_qubits, photon_qubits + electronic_qubits)),
                inplace=True,
            )
        ansatz = initial.compose(self._hardware_efficient_layer(num_qubits))
        ansatz.name = "cavity_twolocal"
        return ansatz

    def _build_ansatz(self, num_qubits: int):
        kind = self.spec.ansatz.kind.strip().lower()
        chemistry_ansatzes = {
            "uccsd": UCCSD,
            "puccd": PUCCD,
            "puccsd": PUCCSD,
            "succd": SUCCD,
        }
        if kind in chemistry_ansatzes:
            if self.problem_summary is None or self.mapper is None:
                raise ValueError(f"{self.spec.ansatz.kind} ansatz requires problem summary and qubit mapper context.")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SparseEfficiencyWarning)
                initial_state = HartreeFock(
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                )
                return chemistry_ansatzes[kind](
                    self.problem_summary.num_spatial_orbitals,
                    self.problem_summary.num_particles,
                    self.mapper,
                    reps=self.spec.ansatz.reps,
                    initial_state=initial_state,
                )
        if kind in {"cavity_twolocal", "electron_photon_twolocal"}:
            return self._build_cavity_twolocal(num_qubits)
        return self._hardware_efficient_layer(num_qubits)

    def _base_initial_point(self, num_parameters: int) -> tuple[np.ndarray, str]:
        if isinstance(self.spec.initial_point, list):
            values = np.asarray(self.spec.initial_point, dtype=float)
            if len(values) != num_parameters:
                raise ValueError(
                    f"VQE initial_point length {len(values)} does not match parameter count {num_parameters}."
                )
            return values, "custom"
        strategy = str(self.spec.initial_point).strip().lower()
        if strategy == "zeros":
            return np.zeros(num_parameters, dtype=float), "zeros"
        if strategy == "random":
            return self.rng.uniform(-0.1, 0.1, size=num_parameters), "random"
        raise ValueError(f"Unsupported initial point strategy: {self.spec.initial_point}")

    def _initial_point(self, num_parameters: int) -> tuple[np.ndarray, dict[str, object]]:
        candidate = self.spec.initial_point_candidate
        fallback_strategy = "custom" if isinstance(self.spec.initial_point, list) else str(self.spec.initial_point)
        provenance: dict[str, object] = {
            "mode": None,
            "candidate_source": None,
            "candidate_source_run_id": None,
            "candidate_source_artifact_root": None,
            "candidate_parameter_count": None,
            "history_sources": [],
            "history_parameter_values": [],
            "target_parameter_value": None,
            "current_parameter_count": int(num_parameters),
            "reused": False,
            "fallback_reason": None,
            "fallback_strategy": fallback_strategy,
            "effective_strategy": fallback_strategy,
        }
        if candidate is not None:
            candidate_values = np.asarray(candidate.values, dtype=float)
            provenance.update(
                {
                    "mode": candidate.mode,
                    "candidate_source": candidate.source,
                    "candidate_source_run_id": candidate.source_run_id,
                    "candidate_source_artifact_root": candidate.source_artifact_root,
                    "candidate_parameter_count": (
                        candidate.source_parameter_count
                        if candidate.source_parameter_count is not None
                        else int(len(candidate_values))
                    ),
                    "history_sources": list(candidate.history_sources),
                    "history_parameter_values": list(candidate.history_parameter_values),
                    "target_parameter_value": candidate.target_parameter_value,
                }
            )
            if candidate.fallback_reason:
                provenance["fallback_reason"] = candidate.fallback_reason
                initial_point, strategy = self._base_initial_point(num_parameters)
                provenance["effective_strategy"] = strategy
                provenance["fallback_strategy"] = strategy
                return initial_point, provenance
            if len(candidate_values) == num_parameters:
                provenance.update(
                    {
                        "reused": True,
                        "fallback_strategy": None,
                        "effective_strategy": candidate.mode,
                    }
                )
                return candidate_values, provenance
            reason = (
                f"candidate_parameter_count={len(candidate_values)} does not match "
                f"current_parameter_count={num_parameters}"
            )
            if str(candidate.on_parameter_mismatch).strip().lower() != "fallback":
                raise ValueError(f"Cannot reuse VQE initial-point candidate: {reason}.")
            provenance["fallback_reason"] = reason

        initial_point, strategy = self._base_initial_point(num_parameters)
        provenance["effective_strategy"] = strategy
        provenance["fallback_strategy"] = strategy
        return initial_point, provenance

    def solve(self, operator) -> SolverOutcome:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SparseEfficiencyWarning)
            ansatz = self._build_ansatz(operator.num_qubits)
            initial_point, initial_point_provenance = self._initial_point(ansatz.num_parameters)
            evaluations = 0
            evaluation_trajectory: list[dict[str, object]] = []

            def objective(point: np.ndarray) -> float:
                nonlocal evaluations
                evaluations += 1
                estimate = self.backend.evaluate(ansatz, operator, point)
                energy = float(estimate.value)
                evaluation_trajectory.append(
                    {
                        "evaluation_index": int(evaluations),
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
                method=self.spec.optimizer.kind,
                tol=self.spec.optimizer.tol,
                options={"maxiter": self.spec.optimizer.maxiter},
            )
        return SolverOutcome(
            total_energy=float(result.fun),
            converged=bool(result.success),
            iterations=int(getattr(result, "nit", evaluations)),
            evaluations=evaluations,
            optimal_parameters=[float(value) for value in np.asarray(result.x)],
            metadata={
                "ansatz_circuit": ansatz,
                "ansatz_num_parameters": ansatz.num_parameters,
                "initial_point_strategy": initial_point_provenance["effective_strategy"],
                "initial_point_provenance": initial_point_provenance,
                "optimizer_message": str(result.message),
                "evaluation_trajectory": evaluation_trajectory,
            },
        )


def build_solver(
    spec: SolverSpec,
    backend: BackendAdapter | None,
    seed: int,
    problem_summary: ProblemSummary | None = None,
    mapper: object | None = None,
    field_model_context: dict[str, object] | None = None,
) -> BaseSolver:
    """Build the solver declared by the config."""
    normalized = spec.kind.strip().lower()
    if normalized == "vqe":
        if backend is None:
            raise ValueError("VQE requires an execution backend.")
        return VQESolver(
            spec,
            backend,
            seed,
            problem_summary=problem_summary,
            mapper=mapper,
            field_model_context=field_model_context,
        )
    if normalized == "lr_ace":
        from qcchem.solvers.lr_ace import build_solver as build_lr_ace_solver

        return build_lr_ace_solver(
            spec,
            backend,
            seed,
            problem_summary=problem_summary,
            mapper=mapper,
        )
    if normalized in {"exact", "reference"}:
        return ExactDiagonalizationSolver()
    raise ValueError(f"Unsupported solver kind: {spec.kind}")
