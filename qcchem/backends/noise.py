"""Local Aer noise-model helpers."""

from __future__ import annotations

from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

from qcchem.core import NoiseModelSpec, NoiseModelSummary

DEFAULT_ONE_QUBIT_GATES = ["id", "rz", "ry", "rx", "x", "sx", "u", "u1", "u2", "u3"]
DEFAULT_TWO_QUBIT_GATES = ["cx", "cz", "ecr"]


def effective_basis_gates(spec: NoiseModelSpec) -> list[str]:
    """Return the basis gates relevant to a configured local noise model."""
    if spec.basis_gates:
        return list(spec.basis_gates)
    if not spec.enabled:
        return []
    return sorted(set(DEFAULT_ONE_QUBIT_GATES + DEFAULT_TWO_QUBIT_GATES))


def build_local_noise_model(spec: NoiseModelSpec) -> NoiseModel | None:
    """Build an Aer noise model from QCchem's owned schema."""
    if not spec.enabled:
        return None

    model = NoiseModel()
    if spec.basis_gates:
        configured = list(spec.basis_gates)
        one_qubit_gates = [gate for gate in configured if gate in DEFAULT_ONE_QUBIT_GATES] or DEFAULT_ONE_QUBIT_GATES
        two_qubit_gates = [gate for gate in configured if gate in DEFAULT_TWO_QUBIT_GATES] or DEFAULT_TWO_QUBIT_GATES
    else:
        one_qubit_gates = DEFAULT_ONE_QUBIT_GATES
        two_qubit_gates = DEFAULT_TWO_QUBIT_GATES

    if spec.depolarizing_probability_1q > 0.0:
        error_1q = depolarizing_error(spec.depolarizing_probability_1q, 1)
        for gate in one_qubit_gates:
            model.add_all_qubit_quantum_error(error_1q, gate)

    if spec.depolarizing_probability_2q > 0.0:
        error_2q = depolarizing_error(spec.depolarizing_probability_2q, 2)
        for gate in two_qubit_gates:
            model.add_all_qubit_quantum_error(error_2q, gate)

    if spec.readout_error_probability > 0.0:
        probability = spec.readout_error_probability
        readout = ReadoutError(
            [[1.0 - probability, probability], [probability, 1.0 - probability]]
        )
        model.add_all_qubit_readout_error(readout)

    return model


def build_noise_model_summary(spec: NoiseModelSpec) -> NoiseModelSummary | None:
    """Build a serializable noise-provenance snapshot."""
    if not spec.enabled:
        return None
    return NoiseModelSummary(
        enabled=True,
        profile=spec.profile,
        model_kind="aer_noise_model",
        local_simulation=True,
        parameters={
            "depolarizing_probability_1q": spec.depolarizing_probability_1q,
            "depolarizing_probability_2q": spec.depolarizing_probability_2q,
            "readout_error_probability": spec.readout_error_probability,
        },
        basis_gates=effective_basis_gates(spec),
        provenance={
            "source": "qcchem.local_noise_model_suite",
            "applied": True,
            "validated_scope": "exploratory_noisy_local_execution",
        },
    )
