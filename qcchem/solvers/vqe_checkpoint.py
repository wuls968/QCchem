"""Checked objective replay for QCchem's SciPy VQE optimizer."""

from __future__ import annotations

from importlib import metadata
import inspect
from pathlib import Path
from typing import Any, Callable

import numpy as np
from qiskit.quantum_info import SparsePauliOp

from qcchem.io.checkpoint import checkpoint_digest, read_checkpoint, write_checkpoint
from qcchem.io.serialization import to_primitive

SCHEMA = "qcchem.vqe_checkpoint.v1"
HAMILTONIAN_ROUNDOFF_LIMIT = 1.0e-12


def hamiltonian_terms(operator) -> list[list[Any]]:
    return [[label, float(value.real), float(value.imag)] for label, value in operator.to_list()]


def restore_hamiltonian(operator, source: Path) -> tuple[SparsePauliOp, float]:
    """Keep original coefficients after bounding SCF reconstruction roundoff."""
    state = read_checkpoint(source, schema=SCHEMA)
    try:
        terms = state["hamiltonian"]
        if not isinstance(terms, list) or not terms:
            raise ValueError("missing Hamiltonian terms")
        for label, real, imag in terms:
            if (not isinstance(label, str) or len(label) != operator.num_qubits or set(label) - set("IXYZ")
                    or type(real) not in {int, float} or type(imag) not in {int, float}):
                raise ValueError("invalid Hamiltonian term")
        saved = SparsePauliOp.from_list([(label, complex(real, imag)) for label, real, imag in terms])
        if (saved.num_qubits != operator.num_qubits or saved.paulis.to_labels() != operator.paulis.to_labels()
                or not np.all(np.isfinite(saved.coeffs))):
            raise ValueError("Hamiltonian Pauli basis changed")
        bound = float(np.sum(np.abs(saved.coeffs - operator.coeffs)))
        if not np.isfinite(bound) or bound > HAMILTONIAN_ROUNDOFF_LIMIT:
            raise ValueError(f"Hamiltonian changed beyond the {HAMILTONIAN_ROUNDOFF_LIMIT:g} reconstruction roundoff bound")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Cannot recover VQE Hamiltonian: {exc}") from exc
    return saved, bound


def vqe_signature(spec, backend, seed: int, operator, ansatz) -> str:
    circuit = ansatz.decompose(reps=4)
    gates = [
        {
            "name": item.operation.name,
            "parameters": [to_primitive(value) if isinstance(value, np.ndarray) else str(value) for value in item.operation.params],
            "qubits": [circuit.find_bit(bit).index for bit in item.qubits],
        }
        for item in circuit.data
    ]
    backend_source = inspect.getsourcefile(type(backend))
    sources = [Path(__file__), Path(__file__).with_name("vqe.py")]
    if backend_source:
        sources.append(Path(backend_source))
    return checkpoint_digest({
        "solver": spec, "backend": getattr(backend, "spec", None),
        "backend_class": f"{type(backend).__module__}.{type(backend).__qualname__}",
        "seed": seed, "operator": [(label, float(value.real), float(value.imag)) for label, value in operator.to_list()],
        "circuit": {"qubits": circuit.num_qubits, "parameters": [str(value) for value in ansatz.parameters],
                    "phase": str(circuit.global_phase), "gates": gates},
        "versions": {name: metadata.version(name) for name in ("numpy", "scipy", "qiskit", "qiskit-nature")},
        "source_sha256": [checkpoint_digest(path.read_text(encoding="utf-8")) for path in sources],
    })


class VQECheckpoint:
    """Record completed local evaluations and verify their replay before new work."""

    def __init__(
        self, *, path: Path | None, source: Path | None, signature: str, operator,
        initial_point: np.ndarray, provenance: dict[str, Any], backend,
        control_check: Callable[[], None] | None,
    ) -> None:
        self.path = path
        self.control_check = control_check
        self.cursor = 0
        self.restored_count = 0
        self.source = source
        if source is not None and (path is None or path.resolve() == source.resolve()):
            raise ValueError("VQE recovery requires a separate new checkpoint path.")
        self.state: dict[str, Any] = {
            "schema_version": SCHEMA, "signature": signature, "status": "running",
            "initial_point": initial_point.tolist(), "initial_point_provenance": provenance,
            "evaluation_trajectory": [], "pending_evaluation": None,
            "hamiltonian": hamiltonian_terms(operator),
        }
        if source is not None:
            state = read_checkpoint(source, schema=SCHEMA)
            if state.get("signature") != signature:
                raise ValueError("VQE checkpoint Hamiltonian, circuit, backend, seed, or optimizer changed.")
            self._validate(state, len(initial_point))
            self.state = state
            self.restored_count = len(self.trajectory)
            backend.restore_evaluation_count(self.restored_count)
        self.initial_point = np.asarray(self.state["initial_point"], dtype=float)
        self.provenance = dict(self.state["initial_point_provenance"])

    @property
    def trajectory(self) -> list[dict[str, Any]]:
        return self.state["evaluation_trajectory"]

    def _validate(self, state: dict[str, Any], count: int) -> None:
        try:
            if state["status"] not in {"running", "interrupted", "failed", "completed"}:
                raise ValueError("unknown status")
            def valid_vector(values):
                return isinstance(values, list) and len(values) == count and all(
                    type(value) in {float, int} and np.isfinite(value) for value in values)

            if not valid_vector(state["initial_point"]) or not isinstance(state["initial_point_provenance"], dict):
                raise ValueError("invalid initial point")
            for index, item in enumerate(state["evaluation_trajectory"], 1):
                if type(item["evaluation_index"]) is not int or item["evaluation_index"] != index or not valid_vector(item["parameters"]):
                    raise ValueError("invalid evaluation sequence")
                std = item["reported_std"]
                if (type(item["energy"]) not in {float, int} or not np.isfinite(item["energy"])
                        or (std is not None and (type(std) not in {float, int} or not np.isfinite(std) or std < 0))
                        or not isinstance(item["backend_metadata"], dict)):
                    raise ValueError("invalid estimate")
                if (item["seed"] is not None and type(item["seed"]) is not int) or (
                        item["shots"] is not None and (type(item["shots"]) is not int or item["shots"] <= 0)):
                    raise ValueError("invalid seed or shot count")
            pending = state.get("pending_evaluation")
            if pending is not None and (pending["evaluation_index"] != len(state["evaluation_trajectory"]) + 1 or not valid_vector(pending["parameters"])):
                raise ValueError("invalid pending evaluation")
            if state["status"] == "completed" and (pending is not None or not isinstance(state.get("outcome"), dict)):
                raise ValueError("missing completed outcome")
            if state["status"] == "completed":
                outcome = state["outcome"]
                if (not valid_vector(outcome["optimal_parameters"]) or not np.isfinite(outcome["total_energy"])
                        or type(outcome["converged"]) is not bool or type(outcome["iterations"]) is not int
                        or outcome["iterations"] < 0 or not isinstance(outcome["optimizer_message"], str)):
                    raise ValueError("invalid completed outcome")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid VQE checkpoint fields: {exc}") from exc

    def check(self) -> None:
        if self.control_check is not None:
            self.control_check()

    def save(self) -> None:
        if self.path is not None:
            write_checkpoint(self.path, self.state)

    def evaluate(self, point: np.ndarray, evaluate: Callable[[], Any]) -> float:
        self.check()
        values = np.asarray(point, dtype=float)
        if self.cursor < self.restored_count:
            item = self.trajectory[self.cursor]
            if not np.array_equal(values, np.asarray(item["parameters"], dtype=float)):
                raise ValueError(f"VQE optimizer replay diverged at evaluation {self.cursor + 1}; no new estimate was requested.")
            self.cursor += 1
            return float(item["energy"])
        pending = self.state.get("pending_evaluation")
        if pending is not None and not np.array_equal(values, np.asarray(pending["parameters"], dtype=float)):
            raise ValueError("VQE optimizer replay diverged at the pending evaluation.")
        self.state["status"] = "running"
        self.state["pending_evaluation"] = {"evaluation_index": len(self.trajectory) + 1, "parameters": values.tolist()}
        self.save()
        estimate = evaluate()
        self.trajectory.append({
            "evaluation_index": len(self.trajectory) + 1,
            "parameters": values.tolist(), "energy": float(estimate.value),
            "reported_std": float(estimate.reported_std) if estimate.reported_std is not None else None,
            "seed": estimate.seed,
            "shots": estimate.shots, "backend_metadata": dict(estimate.metadata),
        })
        self.cursor += 1
        self.state["pending_evaluation"] = None
        self.save()  # Commit returned evidence before observing cancellation.
        self.check()
        return float(estimate.value)

    def complete(self, outcome: dict[str, Any]) -> None:
        if self.cursor < self.restored_count:
            raise ValueError("VQE optimizer terminated before replaying the recorded trajectory.")
        self.state.update(status="completed", outcome=outcome, pending_evaluation=None)
        self.save()

    def stop(self, exc: BaseException) -> None:
        self.state["status"] = "failed" if isinstance(exc, Exception) else "interrupted"
        try:
            self.save()
        except (OSError, ValueError, TypeError) as failure:
            if hasattr(exc, "add_note"):
                exc.add_note(f"Could not publish the final VQE checkpoint: {failure}")

    def recovery_summary(self) -> dict[str, Any]:
        return {
            "mode": "checked_objective_replay", "source_checkpoint": str(self.source),
            "replayed_evaluations": self.restored_count,
            "new_evaluations": len(self.trajectory) - self.restored_count,
        }
