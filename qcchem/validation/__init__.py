"""Validation harnesses for QCchem trust loops."""

__all__ = [
    "QMMMValidationCase",
    "classify_lr_ace_validation_gate",
    "default_qmmm_validation_cases",
    "run_qmmm_embedding_validation",
]


def __getattr__(name: str):
    if name in {"QMMMValidationCase", "default_qmmm_validation_cases", "run_qmmm_embedding_validation"}:
        from . import qmmm_embedding

        return getattr(qmmm_embedding, name)
    if name == "classify_lr_ace_validation_gate":
        from .lr_ace import classify_lr_ace_validation_gate

        return classify_lr_ace_validation_gate
    raise AttributeError(name)
