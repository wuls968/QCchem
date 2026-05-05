"""Backend capability snapshots for QCchem."""

from __future__ import annotations

from qcchem.core import BackendCapabilitySummary, BackendSpec


def describe_backend_capabilities(spec: BackendSpec) -> BackendCapabilitySummary:
    """Describe the currently configured backend in QCchem-owned terms."""
    kind = spec.kind.strip().lower()
    if kind == "statevector":
        return BackendCapabilitySummary(
            backend_kind=spec.kind,
            statevector=True,
            shot_based=False,
            exact_baseline=True,
            runtime_ready=False,
            session_ready=False,
            batch_ready=False,
            mitigation_ready=False,
            noise_model_ready=False,
            supports_grouping=False,
            supports_repetitions=False,
            supports_confidence_metrics=False,
        )

    if kind in {"shot_estimator", "aer_shot_estimator"}:
        return BackendCapabilitySummary(
            backend_kind=spec.kind,
            statevector=False,
            shot_based=True,
            exact_baseline=True,
            runtime_ready=bool(spec.runtime.runtime_ready or spec.runtime.enabled),
            session_ready=bool(spec.runtime.session_ready),
            batch_ready=bool(spec.runtime.batch_ready),
            mitigation_ready=True,
            noise_model_ready=True,
            supports_grouping=bool(spec.abelian_grouping),
            supports_repetitions=True,
            supports_confidence_metrics=True,
        )

    if "runtime" in kind:
        return BackendCapabilitySummary(
            backend_kind=spec.kind,
            statevector=False,
            shot_based=True,
            exact_baseline=True,
            runtime_ready=True,
            session_ready=bool(spec.runtime.session_ready or spec.runtime.enabled),
            batch_ready=bool(spec.runtime.batch_ready),
            mitigation_ready=True,
            noise_model_ready=False,
            supports_grouping=True,
            supports_repetitions=True,
            supports_confidence_metrics=True,
        )

    return BackendCapabilitySummary(
        backend_kind=spec.kind,
        statevector=False,
        shot_based=False,
        exact_baseline=True,
        runtime_ready=False,
        session_ready=False,
        batch_ready=False,
        mitigation_ready=False,
        noise_model_ready=False,
        supports_grouping=False,
        supports_repetitions=False,
        supports_confidence_metrics=False,
    )
