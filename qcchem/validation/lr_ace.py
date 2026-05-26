"""Trust-first validation helpers for LR-ACE flagship artifacts."""

from __future__ import annotations

from typing import Any


def classify_lr_ace_validation_gate(
    *,
    target_error_hartree: float,
    exact_available: bool,
    local_exact_error_hartree: float | None,
    compression_enabled: bool,
    compressed_solver_energy: float | None = None,
    uncompressed_solver_energy: float | None = None,
    uncompressed_exact_solver_energy: float | None = None,
    runtime_attempted: bool = False,
    runtime_accuracy_met: bool | None = None,
) -> dict[str, Any]:
    """Classify LR-ACE evidence without promoting weak runtime or compression evidence."""
    target = float(target_error_hartree)
    local_passed = (
        bool(exact_available)
        and local_exact_error_hartree is not None
        and float(local_exact_error_hartree) <= target
    )
    trust_label = "local_exact_validated" if local_passed else "ansatz_limited"
    blocking_reason = None if local_passed else "local_exact_error_exceeds_target_or_missing"

    if not exact_available:
        trust_label = "exact_reference_missing"
        blocking_reason = "exact_reference_missing"
    elif (
        uncompressed_exact_solver_energy is not None
        and compressed_solver_energy is not None
    ):
        combined_error = abs(float(compressed_solver_energy) - float(uncompressed_exact_solver_energy))
        uncompressed_solver_error = (
            None
            if uncompressed_solver_energy is None
            else abs(float(uncompressed_solver_energy) - float(uncompressed_exact_solver_energy))
        )
        if combined_error <= target:
            trust_label = "passed_exact_reference"
            blocking_reason = None
        elif uncompressed_solver_error is not None and uncompressed_solver_error > target:
            trust_label = "ansatz_limited"
            blocking_reason = "uncompressed_lr_ace_ansatz_error_exceeds_target"
        else:
            trust_label = "compression_limited"
            blocking_reason = "compressed_solver_energy_misses_uncompressed_exact_reference"
    elif local_passed:
        trust_label = "passed_compressed_with_budget" if compression_enabled else "passed_exact_reference"
        blocking_reason = None

    verification_status = "validated" if blocking_reason is None else "exploratory"
    if runtime_attempted and runtime_accuracy_met is False:
        trust_label = "runtime_gap"
        verification_status = "hardware_verified"
        blocking_reason = "runtime_accuracy_does_not_meet_chemical_accuracy"

    return {
        "trust_label": trust_label,
        "verification_status": verification_status,
        "validated": verification_status == "validated",
        "target_error_hartree": target,
        "exact_available": bool(exact_available),
        "local_exact_error_hartree": (
            None if local_exact_error_hartree is None else float(local_exact_error_hartree)
        ),
        "compression_enabled": bool(compression_enabled),
        "compressed_solver_energy": compressed_solver_energy,
        "uncompressed_solver_energy": uncompressed_solver_energy,
        "uncompressed_exact_solver_energy": uncompressed_exact_solver_energy,
        "runtime_attempted": bool(runtime_attempted),
        "runtime_accuracy_met": runtime_accuracy_met,
        "blocking_reason": blocking_reason,
    }
