"""Optional task execution for excited states and properties."""

from __future__ import annotations

import math

import numpy as np

from qcchem.core import (
    ExcitedStateLevelResult,
    ExcitedStateTaskResult,
    PropertyTaskResult,
    PropertyValueResult,
    RunSpec,
)
from qcchem.solvers.spectrum import ExactSpectrum, compute_exact_spectrum


def required_exact_states(spec: RunSpec) -> int:
    """Return how many exact states are needed to satisfy optional tasks."""
    required = 1
    if spec.tasks.excited_state.enabled:
        required = max(
            required,
            spec.tasks.excited_state.num_states,
            max(spec.tasks.excited_state.state_indices, default=0) + 1,
        )
    for item in spec.tasks.properties:
        if item.enabled and item.state_indices:
            required = max(required, max(item.state_indices) + 1)
    return required


def ensure_exact_spectrum(operator, num_states: int) -> ExactSpectrum:
    """Compute an exact spectrum slice."""
    return compute_exact_spectrum(operator, num_states=num_states)


def _expectation(operator, statevector: np.ndarray) -> float:
    if len(operator) == 0:
        return 0.0
    matrix = operator.to_matrix(sparse=True)
    return float(np.real(np.vdot(statevector, matrix @ statevector)))


def _matrix_element(operator, bra: np.ndarray, ket: np.ndarray) -> complex:
    if len(operator) == 0:
        return 0.0 + 0.0j
    matrix = operator.to_matrix(sparse=True)
    return complex(np.vdot(bra, matrix @ ket))


def _transition_dipole_components(dipole_property, mapping, bra: np.ndarray, ket: np.ndarray) -> np.ndarray:
    fermionic_ops = dipole_property.second_q_ops()
    components: list[complex] = []
    for op_name in ("XDipole", "YDipole", "ZDipole"):
        fermionic_op = fermionic_ops[op_name]
        qubit_op = mapping.mapper.map(fermionic_op)
        components.append(_matrix_element(qubit_op, bra, ket))
    electronic = np.asarray(components, dtype=complex)
    return -electronic if getattr(dipole_property, "reverse_dipole_sign", True) else electronic


def build_excited_state_result(
    spec: RunSpec,
    spectrum: ExactSpectrum | None,
    *,
    total_constant_correction: float,
) -> ExcitedStateTaskResult | None:
    """Build the excited-state task result section."""
    task = spec.tasks.excited_state
    if not task.enabled:
        return None
    if spectrum is None:
        return ExcitedStateTaskResult(
            enabled=True,
            method=task.method,
            verification_status="exploratory",
            notes=["Exact spectrum unavailable; excited-state task left as exploratory placeholder."],
        )

    ground_total = spectrum.eigenvalues[0] + total_constant_correction
    states: list[ExcitedStateLevelResult] = []
    for state_index in sorted(set(task.state_indices)):
        if state_index >= len(spectrum.eigenvalues):
            continue
        total_energy = spectrum.eigenvalues[state_index] + total_constant_correction
        verification = "validated" if task.method == "exact_spectrum" else "exploratory"
        baseline = {"source": "exact_spectrum"}
        if task.method != "exact_spectrum":
            baseline["proxy_mode"] = "exact_spectrum_for_vqd_skeleton"
        states.append(
            ExcitedStateLevelResult(
                state_index=state_index,
                solver_energy=float(spectrum.eigenvalues[state_index]),
                total_energy=float(total_energy),
                excitation_energy=float(total_energy - ground_total),
                reference_state_index=0,
                solver_metadata={"requested_method": task.method},
                baseline=baseline,
                verification_status=verification,
            )
        )

    notes: list[str] = []
    verification_status = "validated"
    if task.method != "exact_spectrum":
        verification_status = "exploratory"
        notes.append(
            "Requested excited-state method is treated as an exploratory interface; values come from an exact-spectrum proxy."
        )
    return ExcitedStateTaskResult(
        enabled=True,
        method=task.method,
        states=states,
        verification_status=verification_status,
        notes=notes,
    )


def build_property_result(
    spec: RunSpec,
    chemistry,
    mapping,
    spectrum: ExactSpectrum | None,
) -> PropertyTaskResult | None:
    """Build the property-task result section."""
    requested = [item for item in spec.tasks.properties if item.enabled]
    if not requested:
        return None

    properties: list[PropertyValueResult] = []
    dipole_property = getattr(chemistry.problem.properties, "electronic_dipole_moment", None)

    for item in requested:
        if item.property_name == "dipole_moment" and dipole_property is not None and spectrum is not None:
            state_index = item.state_indices[0] if item.state_indices else 0
            statevector = np.asarray(spectrum.eigenvectors[:, state_index], dtype=complex)
            fermionic_ops = dipole_property.second_q_ops()
            electronic_components: dict[str, float] = {}
            for axis_name, op_name in {"x": "XDipole", "y": "YDipole", "z": "ZDipole"}.items():
                fermionic_op = fermionic_ops[op_name]
                qubit_op = mapping.mapper.map(fermionic_op)
                electronic_components[axis_name] = _expectation(qubit_op, statevector)
            nuclear = np.asarray(dipole_property.nuclear_dipole_moment, dtype=float)
            electronic = np.asarray(
                [electronic_components["x"], electronic_components["y"], electronic_components["z"]],
                dtype=float,
            )
            total = nuclear - electronic if getattr(dipole_property, "reverse_dipole_sign", True) else nuclear + electronic
            properties.append(
                PropertyValueResult(
                    property_name=item.property_name,
                    method=item.method,
                    state_indices=item.state_indices,
                    value=float(math.sqrt(float(np.dot(total, total)))),
                    units="a.u.",
                    components={"x": float(total[0]), "y": float(total[1]), "z": float(total[2])},
                    implementation_status="validated",
                    provenance={
                        "source": "exact_expectation",
                        "statevector_source": "exact_spectrum",
                        "validated_scope": "ground_state_dipole_path",
                    },
                    notes=["Computed from exact eigenstate expectation values and nuclear dipole correction."],
                )
            )
            continue

        if item.property_name == "transition_dipole" and dipole_property is not None and spectrum is not None:
            if len(item.state_indices) < 2:
                properties.append(
                    PropertyValueResult(
                        property_name=item.property_name,
                        method=item.method,
                        state_indices=item.state_indices,
                        implementation_status="placeholder_only",
                        provenance={"source": "placeholder", "reason": "transition_dipole requires two state indices"},
                        notes=["Provide two state indices to compute a transition dipole."],
                    )
                )
                continue
            bra = np.asarray(spectrum.eigenvectors[:, item.state_indices[0]], dtype=complex)
            ket = np.asarray(spectrum.eigenvectors[:, item.state_indices[1]], dtype=complex)
            transition = _transition_dipole_components(dipole_property, mapping, bra, ket)
            magnitude = float(np.sqrt(float(np.sum(np.abs(transition) ** 2))))
            properties.append(
                PropertyValueResult(
                    property_name=item.property_name,
                    method=item.method,
                    state_indices=item.state_indices,
                    value=magnitude,
                    units="a.u.",
                    components={
                        "x": float(np.real(transition[0])),
                        "y": float(np.real(transition[1])),
                        "z": float(np.real(transition[2])),
                    },
                    implementation_status="exploratory",
                    provenance={
                        "source": "exact_transition_expectation",
                        "statevector_source": "exact_spectrum",
                        "validated_scope": "exploratory_transition_property",
                    },
                    notes=[
                        "Computed from exact transition matrix elements.",
                        "QCchem currently treats transition dipole reporting as exploratory.",
                    ],
                )
            )
            continue

        if item.property_name == "oscillator_strength" and dipole_property is not None and spectrum is not None:
            if len(item.state_indices) < 2:
                properties.append(
                    PropertyValueResult(
                        property_name=item.property_name,
                        method=item.method,
                        state_indices=item.state_indices,
                        implementation_status="placeholder_only",
                        provenance={"source": "placeholder", "reason": "oscillator_strength requires two state indices"},
                        notes=["Provide two state indices to compute an oscillator strength."],
                    )
                )
                continue
            initial_index, final_index = item.state_indices[:2]
            bra = np.asarray(spectrum.eigenvectors[:, initial_index], dtype=complex)
            ket = np.asarray(spectrum.eigenvectors[:, final_index], dtype=complex)
            transition = _transition_dipole_components(dipole_property, mapping, bra, ket)
            magnitude = float(np.sqrt(float(np.sum(np.abs(transition) ** 2))))
            excitation_energy = float(spectrum.eigenvalues[final_index] - spectrum.eigenvalues[initial_index])
            oscillator_strength = float((2.0 / 3.0) * excitation_energy * (magnitude**2))
            properties.append(
                PropertyValueResult(
                    property_name=item.property_name,
                    method=item.method,
                    state_indices=item.state_indices,
                    value=oscillator_strength,
                    units="a.u.",
                    components={
                        "transition_dipole_magnitude": magnitude,
                        "excitation_energy": excitation_energy,
                    },
                    implementation_status="exploratory",
                    provenance={
                        "source": "exact_transition_derived",
                        "depends_on": ["transition_dipole", "excitation_energy"],
                        "validated_scope": "exploratory_transition_property",
                    },
                    notes=[
                        "Derived from exact-spectrum excitation energy and transition-dipole magnitude.",
                        "QCchem currently treats oscillator strength reporting as exploratory.",
                    ],
                )
            )
            continue

        properties.append(
            PropertyValueResult(
                property_name=item.property_name,
                method=item.method,
                state_indices=item.state_indices,
                implementation_status="placeholder_only",
                provenance={"source": "placeholder", "validated_scope": "not_implemented"},
                notes=["Formal schema placeholder; implementation not yet validated in QCchem v0.4."],
            )
        )

    bundle_status = "validated" if all(item.implementation_status == "validated" for item in properties) else "exploratory"
    return PropertyTaskResult(
        enabled=True,
        properties=properties,
        verification_status=bundle_status,
    )
