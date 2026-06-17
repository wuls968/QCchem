"""Backend adapters for QCchem solvers."""

from .base import BackendAdapter, BackendEstimate
from .capabilities import describe_backend_capabilities
from .layout import LayoutPlan, recommend_initial_layout
from .measurement import plan_measurement as build_measurement_plan
from .noise import build_noise_model_summary
from .policy import apply_policy_defaults, resolve_execution_policy
from .policy_engine import resolve_policy
from .runtime_submission import attempt_runtime_submission
from .runtime_batch import attempt_runtime_batch_submission
from .runtime import build_runtime_options_summary
from .cudaq_adapter import CudaQBackend
from .shot_estimator import ShotEstimatorBackend
from .statevector import StatevectorBackend


def build_backend(spec):
    """Build the backend adapter declared by the config."""
    normalized = spec.kind.strip().lower()
    if normalized == "statevector":
        return StatevectorBackend(spec)
    if normalized in {"shot_estimator", "aer_shot_estimator"}:
        return ShotEstimatorBackend(spec)
    if normalized in {"cudaq_statevector", "cudaq_sample"}:
        return CudaQBackend(spec)
    raise ValueError(
        f"Unsupported backend kind '{spec.kind}'. "
        "Supported backends are 'statevector', 'shot_estimator', "
        "'cudaq_statevector', and 'cudaq_sample'."
    )


__all__ = [
    "BackendAdapter",
    "BackendEstimate",
    "CudaQBackend",
    "LayoutPlan",
    "ShotEstimatorBackend",
    "StatevectorBackend",
    "apply_policy_defaults",
    "build_measurement_plan",
    "build_noise_model_summary",
    "attempt_runtime_submission",
    "attempt_runtime_batch_submission",
    "build_runtime_options_summary",
    "build_backend",
    "describe_backend_capabilities",
    "recommend_initial_layout",
    "resolve_execution_policy",
    "resolve_policy",
]
