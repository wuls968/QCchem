from __future__ import annotations

import pytest

from qiskit.quantum_info import SparsePauliOp

from qcchem.backends import BackendEstimate
from qcchem.core import AnsatzSpec, ContinuitySpec, InitialPointCandidate, OptimizerSpec
from qcchem.core import SolverSpec
from qcchem.solvers.vqe import VQESolver
from qcchem.workflow.continuity import ContinuityRecord, build_initial_point_candidate


class _Backend:
    pass


def test_vqe_reuses_matching_previous_optimal_candidate() -> None:
    spec = SolverSpec(
        initial_point="zeros",
        initial_point_candidate=InitialPointCandidate(
            values=[0.1, -0.2],
            source="point_00_0.500",
            source_run_id="point_00_0.500",
            source_parameter_count=2,
        ),
    )
    solver = VQESolver(spec, backend=_Backend(), seed=7)

    initial_point, provenance = solver._initial_point(2)

    assert initial_point.tolist() == pytest.approx([0.1, -0.2])
    assert provenance["reused"] is True
    assert provenance["effective_strategy"] == "previous_optimal"
    assert provenance["candidate_source"] == "point_00_0.500"
    assert provenance["fallback_reason"] is None


def test_vqe_falls_back_when_candidate_parameter_count_mismatches() -> None:
    spec = SolverSpec(
        initial_point="zeros",
        initial_point_candidate=InitialPointCandidate(
            values=[0.1],
            source="first_run",
            source_parameter_count=1,
        ),
    )
    solver = VQESolver(spec, backend=_Backend(), seed=7)

    initial_point, provenance = solver._initial_point(2)

    assert initial_point.tolist() == pytest.approx([0.0, 0.0])
    assert provenance["reused"] is False
    assert provenance["effective_strategy"] == "zeros"
    assert "does not match" in str(provenance["fallback_reason"])


def test_vqe_rejects_custom_initial_point_length_mismatch() -> None:
    spec = SolverSpec(initial_point=[0.1])
    solver = VQESolver(spec, backend=_Backend(), seed=7)

    with pytest.raises(ValueError, match="initial_point length"):
        solver._initial_point(2)


def _record(source: str, parameter_value: float, values: list[float]) -> ContinuityRecord:
    return ContinuityRecord(
        values=values,
        source=source,
        source_run_id=source,
        source_artifact_root=f"/tmp/{source}",
        source_parameter_count=len(values),
        parameter_value=parameter_value,
    )


def test_linear_predictor_candidate_on_equal_spacing() -> None:
    candidate = build_initial_point_candidate(
        [
            _record("p0", 0.5, [0.10, -0.20]),
            _record("p1", 0.7, [0.20, -0.10]),
        ],
        ContinuitySpec(enabled=True, mode="linear_predictor"),
        target_parameter_value=0.9,
    )

    assert candidate is not None
    assert candidate.mode == "linear_predictor"
    assert candidate.values == pytest.approx([0.30, 0.0])
    assert candidate.history_sources == ["p0", "p1"]


def test_linear_predictor_candidate_on_unequal_spacing() -> None:
    candidate = build_initial_point_candidate(
        [
            _record("p0", 0.5, [0.10, -0.20]),
            _record("p1", 0.8, [0.25, -0.05]),
        ],
        ContinuitySpec(enabled=True, mode="linear_predictor"),
        target_parameter_value=0.9,
    )

    assert candidate is not None
    assert candidate.values == pytest.approx([0.30, 0.0])


def test_linear_predictor_degrades_to_previous_for_second_point() -> None:
    candidate = build_initial_point_candidate(
        [_record("p0", 0.5, [0.10, -0.20])],
        ContinuitySpec(enabled=True, mode="linear_predictor"),
        target_parameter_value=0.7,
    )

    assert candidate is not None
    assert candidate.mode == "previous_optimal"
    assert candidate.values == pytest.approx([0.10, -0.20])
    assert candidate.history_sources == ["p0"]


def test_linear_predictor_repeated_coordinate_falls_back() -> None:
    candidate = build_initial_point_candidate(
        [
            _record("p0", 0.5, [0.10, -0.20]),
            _record("p1", 0.5, [0.20, -0.10]),
        ],
        ContinuitySpec(enabled=True, mode="linear_predictor"),
        target_parameter_value=0.7,
    )

    assert candidate is not None
    assert candidate.values == []
    assert "distinct previous scan parameter values" in str(candidate.fallback_reason)


def test_linear_predictor_history_parameter_mismatch_falls_back() -> None:
    candidate = build_initial_point_candidate(
        [
            _record("p0", 0.5, [0.10]),
            _record("p1", 0.7, [0.20, -0.10]),
        ],
        ContinuitySpec(enabled=True, mode="linear_predictor"),
        target_parameter_value=0.9,
    )

    assert candidate is not None
    assert candidate.values == []
    assert "history parameter counts" in str(candidate.fallback_reason)


def test_linear_predictor_non_finite_prediction_falls_back() -> None:
    candidate = build_initial_point_candidate(
        [
            _record("p0", 0.5, [0.10, -0.20]),
            _record("p1", 0.7, [float("inf"), -0.10]),
        ],
        ContinuitySpec(enabled=True, mode="linear_predictor"),
        target_parameter_value=0.9,
    )

    assert candidate is not None
    assert candidate.values == []
    assert "non-finite" in str(candidate.fallback_reason)


def test_vqe_records_predictor_fallback_reason() -> None:
    spec = SolverSpec(
        initial_point="zeros",
        initial_point_candidate=InitialPointCandidate(
            values=[],
            source="point_01",
            mode="linear_predictor",
            fallback_reason="linear_predictor produced non-finite parameter values",
            history_sources=["point_00", "point_01"],
        ),
    )
    solver = VQESolver(spec, backend=_Backend(), seed=7)

    initial_point, provenance = solver._initial_point(2)

    assert initial_point.tolist() == pytest.approx([0.0, 0.0])
    assert provenance["reused"] is False
    assert provenance["effective_strategy"] == "zeros"
    assert provenance["history_sources"] == ["point_00", "point_01"]
    assert "non-finite" in str(provenance["fallback_reason"])


def test_vqe_preserves_backend_evidence_for_each_evaluation() -> None:
    class _EvidenceBackend:
        def __init__(self) -> None:
            self.estimate_expectation_calls = 0
            self.evaluate_calls = 0

        def estimate_expectation(self, circuit, operator, parameter_values) -> float:
            self.estimate_expectation_calls += 1
            raise AssertionError("VQESolver should preserve BackendEstimate evidence via evaluate().")

        def evaluate(self, circuit, operator, parameter_values) -> BackendEstimate:
            self.evaluate_calls += 1
            values = [float(value) for value in parameter_values]
            energy = sum(value * value for value in values) + 0.01 * self.evaluate_calls
            return BackendEstimate(
                value=energy,
                reported_std=0.001 * self.evaluate_calls,
                metadata={"backend_call": self.evaluate_calls, "precision": 0.25},
                seed=700 + self.evaluate_calls,
                shots=1024,
            )

    backend = _EvidenceBackend()
    spec = SolverSpec(
        optimizer=OptimizerSpec(kind="COBYLA", maxiter=2),
        ansatz=AnsatzSpec(rotation_blocks=["ry"], reps=1, skip_final_rotation_layer=True),
        initial_point="zeros",
    )
    solver = VQESolver(spec, backend=backend, seed=7)

    outcome = solver.solve(SparsePauliOp.from_list([("I", 1.0)]))

    trajectory = outcome.metadata["evaluation_trajectory"]
    assert backend.estimate_expectation_calls == 0
    assert backend.evaluate_calls == outcome.evaluations == len(trajectory)
    assert trajectory[0] == {
        "evaluation_index": 1,
        "parameters": [0.0],
        "energy": pytest.approx(0.01),
        "reported_std": pytest.approx(0.001),
        "seed": 701,
        "shots": 1024,
        "backend_metadata": {"backend_call": 1, "precision": 0.25},
    }
    assert outcome.metadata["initial_point_strategy"] == "zeros"
    assert "optimizer_message" in outcome.metadata
