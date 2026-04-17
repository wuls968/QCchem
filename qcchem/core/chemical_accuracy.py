"""Chemical-accuracy helpers aligned with QCchem benchmark semantics."""

from __future__ import annotations

from qcchem.core.results import ChemicalAccuracySummary

CHEMICAL_ACCURACY_HARTREE = 1.6e-3
KCAL_PER_MOL_PER_HARTREE = 627.509474


def check_chemical_accuracy(
    computed_energy: float,
    reference_energy: float | None,
    *,
    threshold_hartree: float = CHEMICAL_ACCURACY_HARTREE,
    statistical_error: float | None = None,
) -> ChemicalAccuracySummary:
    """Return a QCchem-aligned chemical-accuracy summary."""
    if reference_energy is None:
        return ChemicalAccuracySummary(
            available=False,
            meets_chemical_accuracy=None,
            absolute_error_hartree=None,
            absolute_error_kcal_mol=None,
            relative_error=None,
            threshold_hartree=threshold_hartree,
            threshold_kcal_mol=threshold_hartree * KCAL_PER_MOL_PER_HARTREE,
            statistical_error=statistical_error,
            reference_energy=None,
            computed_energy=computed_energy,
            status="no_reference",
            notes=["No reference energy available for chemical-accuracy assessment."],
        )

    absolute_error = abs(computed_energy - reference_energy)
    absolute_error_kcal = absolute_error * KCAL_PER_MOL_PER_HARTREE
    relative_error = absolute_error / max(abs(reference_energy), 1.0e-12)
    meets = absolute_error <= threshold_hartree
    notes = [
        (
            "Meets chemical accuracy threshold."
            if meets
            else "Does not meet chemical accuracy threshold."
        )
    ]
    if statistical_error is not None:
        if absolute_error <= 1.96 * statistical_error:
            notes.append("Observed error lies within 95% statistical uncertainty.")
        else:
            notes.append("Observed error exceeds 95% statistical uncertainty.")
    return ChemicalAccuracySummary(
        available=True,
        meets_chemical_accuracy=meets,
        absolute_error_hartree=absolute_error,
        absolute_error_kcal_mol=absolute_error_kcal,
        relative_error=relative_error,
        threshold_hartree=threshold_hartree,
        threshold_kcal_mol=threshold_hartree * KCAL_PER_MOL_PER_HARTREE,
        statistical_error=statistical_error,
        reference_energy=reference_energy,
        computed_energy=computed_energy,
        status="validated" if meets else "exploratory",
        notes=notes,
    )
