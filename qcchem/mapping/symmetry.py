"""Symmetry-reduction helpers for mapped molecular Hamiltonians."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from qiskit.quantum_info import SparsePauliOp

from qcchem.core import MappingSymmetryReductionSpec


@dataclass(slots=True)
class Z2TaperingResult:
    """Result of applying, skipping, or failing Z2 tapering."""

    qubit_hamiltonian: SparsePauliOp
    mapper: object
    status: str
    notes: list[str] = field(default_factory=list)
    z2_symmetry_count: int = 0
    z2_tapering_values: list[int] | None = None
    validation: dict[str, Any] = field(default_factory=dict)


def _mode_and_strict(
    symmetry_reduction: MappingSymmetryReductionSpec | dict[str, Any] | None,
) -> tuple[str, bool]:
    if symmetry_reduction is None:
        return "disabled", False
    if isinstance(symmetry_reduction, dict):
        mode = str(symmetry_reduction.get("z2", "disabled")).strip().lower()
        strict = bool(symmetry_reduction.get("strict", False))
    else:
        mode = str(symmetry_reduction.z2).strip().lower()
        strict = bool(symmetry_reduction.strict)
    if mode not in {"auto", "enabled", "disabled"}:
        raise ValueError("mapping.symmetry_reduction.z2 must be one of: auto, enabled, disabled.")
    return mode, strict


def _raise_or_skip(
    *,
    strict: bool,
    qubit_hamiltonian: SparsePauliOp,
    mapper: object,
    status: str,
    note: str,
    z2_symmetry_count: int = 0,
    z2_tapering_values: list[int] | None = None,
    validation: dict[str, Any] | None = None,
) -> Z2TaperingResult:
    if strict:
        raise ValueError(note)
    return Z2TaperingResult(
        qubit_hamiltonian=qubit_hamiltonian,
        mapper=mapper,
        status=status,
        notes=[note],
        z2_symmetry_count=z2_symmetry_count,
        z2_tapering_values=z2_tapering_values,
        validation=validation or {},
    )


def _validate_tapered_spectrum(
    raw_operator: SparsePauliOp,
    tapered_operator: SparsePauliOp,
    *,
    max_qubits: int,
) -> dict[str, Any]:
    validation: dict[str, Any] = {
        "available": False,
        "method": "exact_ground_state_delta",
        "max_qubits": max_qubits,
    }
    if raw_operator.num_qubits > max_qubits or tapered_operator.num_qubits > max_qubits:
        validation["reason"] = "qubit_count_above_validation_limit"
        return validation
    from qcchem.solvers.spectrum import compute_exact_spectrum

    raw_energy = compute_exact_spectrum(raw_operator, num_states=1).eigenvalues[0]
    tapered_energy = compute_exact_spectrum(tapered_operator, num_states=1).eigenvalues[0]
    delta = abs(float(raw_energy) - float(tapered_energy))
    validation.update(
        {
            "available": True,
            "raw_ground_energy": float(raw_energy),
            "tapered_ground_energy": float(tapered_energy),
            "absolute_delta": float(delta),
        }
    )
    return validation


def apply_z2_tapering(
    *,
    fermionic_hamiltonian,
    base_mapper: object,
    raw_qubit_hamiltonian: SparsePauliOp,
    problem: object | None,
    symmetry_reduction: MappingSymmetryReductionSpec | dict[str, Any] | None,
    validation_qubit_limit: int = 12,
    validation_tolerance: float = 1.0e-8,
) -> Z2TaperingResult:
    """Apply Qiskit Nature Z2 tapering when it is safe and requested."""
    mode, strict = _mode_and_strict(symmetry_reduction)
    if mode == "disabled":
        return Z2TaperingResult(
            qubit_hamiltonian=raw_qubit_hamiltonian,
            mapper=base_mapper,
            status="disabled",
            notes=["Z2 tapering disabled by mapping.symmetry_reduction.z2."],
        )
    if problem is None:
        return _raise_or_skip(
            strict=strict,
            qubit_hamiltonian=raw_qubit_hamiltonian,
            mapper=base_mapper,
            status="skipped_no_problem_context",
            note="Z2 tapering requires an ElectronicStructureProblem context with particle counts.",
        )
    if not hasattr(problem, "get_tapered_mapper"):
        return _raise_or_skip(
            strict=strict,
            qubit_hamiltonian=raw_qubit_hamiltonian,
            mapper=base_mapper,
            status="skipped_unsupported_problem_context",
            note="Z2 tapering skipped because the problem context does not expose get_tapered_mapper().",
        )

    try:
        tapered_mapper = problem.get_tapered_mapper(base_mapper)
        z2_symmetries = tapered_mapper.z2symmetries
        z2_count = len(z2_symmetries.symmetries)
        tapering_values = (
            [int(value) for value in z2_symmetries.tapering_values]
            if z2_symmetries.tapering_values is not None
            else None
        )
        if z2_count == 0:
            return _raise_or_skip(
                strict=strict,
                qubit_hamiltonian=raw_qubit_hamiltonian,
                mapper=base_mapper,
                status="skipped_no_z2_symmetry",
                note="No Z2 Pauli symmetries were detected for this mapped Hamiltonian.",
            )
        if tapering_values is None:
            return _raise_or_skip(
                strict=strict,
                qubit_hamiltonian=raw_qubit_hamiltonian,
                mapper=base_mapper,
                status="skipped_no_z2_sector",
                note="Z2 symmetries were detected, but Qiskit Nature could not locate a tapering sector.",
                z2_symmetry_count=z2_count,
            )
        tapered_operator = tapered_mapper.map(fermionic_hamiltonian)
        if tapered_operator is None:
            return _raise_or_skip(
                strict=strict,
                qubit_hamiltonian=raw_qubit_hamiltonian,
                mapper=base_mapper,
                status="skipped_empty_tapered_operator",
                note="Z2 tapering returned no commuting tapered operator.",
                z2_symmetry_count=z2_count,
                z2_tapering_values=tapering_values,
            )
        validation = _validate_tapered_spectrum(
            raw_qubit_hamiltonian,
            tapered_operator,
            max_qubits=validation_qubit_limit,
        )
        if validation.get("available") and float(validation["absolute_delta"]) > validation_tolerance:
            return _raise_or_skip(
                strict=strict,
                qubit_hamiltonian=raw_qubit_hamiltonian,
                mapper=base_mapper,
                status="skipped_z2_validation_failed",
                note=(
                    "Z2 tapering failed exact-spectrum validation: "
                    f"delta={validation['absolute_delta']:.6g} Hartree."
                ),
                z2_symmetry_count=z2_count,
                z2_tapering_values=tapering_values,
                validation=validation,
            )
        tapered_qubits = int(raw_qubit_hamiltonian.num_qubits) - int(tapered_operator.num_qubits)
        notes = [
            f"Applied Z2 tapering in sector {tapering_values}; removed {tapered_qubits} qubits.",
        ]
        if validation.get("available"):
            notes.append(
                "Exact-spectrum validation passed with "
                f"delta={validation['absolute_delta']:.6g} Hartree."
            )
        else:
            notes.append(f"Exact-spectrum validation skipped: {validation.get('reason')}.")
        return Z2TaperingResult(
            qubit_hamiltonian=tapered_operator,
            mapper=tapered_mapper,
            status="applied_z2",
            notes=notes,
            z2_symmetry_count=z2_count,
            z2_tapering_values=tapering_values,
            validation=validation,
        )
    except ValueError as exc:
        if strict:
            raise
        return _raise_or_skip(
            strict=False,
            qubit_hamiltonian=raw_qubit_hamiltonian,
            mapper=base_mapper,
            status="skipped_z2_error",
            note=f"Z2 tapering skipped after Qiskit Nature error: {type(exc).__name__}: {exc}",
        )
    except Exception as exc:
        return _raise_or_skip(
            strict=strict,
            qubit_hamiltonian=raw_qubit_hamiltonian,
            mapper=base_mapper,
            status="skipped_z2_error",
            note=f"Z2 tapering skipped after Qiskit Nature error: {type(exc).__name__}: {exc}",
        )
