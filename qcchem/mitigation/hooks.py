"""Placeholder mitigation hooks for future execution realism work."""

from __future__ import annotations

from qcchem.core import MitigationSpec, MitigationSummary


def _symmetry_check_metadata(spec: MitigationSpec) -> dict[str, object]:
    return {
        "requested": spec.symmetry_check.enabled,
        "performed": False,
        "status": "hook_available_not_implemented",
        "strategy": spec.symmetry_check.strategy,
    }


def _readout_metadata(spec: MitigationSpec) -> dict[str, object]:
    return {
        "requested": spec.readout.enabled,
        "performed": False,
        "status": "placeholder_not_implemented",
        "method": spec.readout.method,
    }


def _zne_metadata(spec: MitigationSpec) -> dict[str, object]:
    return {
        "requested": spec.zne.enabled,
        "performed": False,
        "status": "placeholder_not_implemented",
        "method": spec.zne.method,
    }


def _pec_metadata(spec: MitigationSpec) -> dict[str, object]:
    return {
        "requested": spec.pec.enabled,
        "performed": False,
        "status": "placeholder_not_implemented",
        "method": spec.pec.method,
    }


def build_mitigation_summary(spec: MitigationSpec) -> MitigationSummary:
    """Build structured mitigation metadata even when mitigation is not yet applied."""
    return MitigationSummary(
        symmetry_check=_symmetry_check_metadata(spec),
        readout_mitigation=_readout_metadata(spec),
        zne=_zne_metadata(spec),
        pec=_pec_metadata(spec),
        applied_methods=[],
    )
