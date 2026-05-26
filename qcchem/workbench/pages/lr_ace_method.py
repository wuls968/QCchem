from __future__ import annotations

from dash import html

from qcchem.workbench.components.cards import detail_card, metric_card, status_card
from qcchem.workbench.pages.overview import build_sample_view_model


def _safe_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _tone(status: object) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"validated", "passed_exact_reference", "local_exact_validated", "passed_compressed_with_budget"}:
        return "validated"
    if normalized in {"failed", "ansatz_limited", "compression_limited", "runtime_gap"}:
        return "unstable"
    if normalized:
        return "exploratory"
    return "informational"


def build_lr_ace_method_page(model: dict[str, object]) -> html.Div:
    lr_ace = _safe_dict(model.get("lr_ace"))
    gate = _safe_dict(lr_ace.get("validation_gate"))
    local_gate = _safe_dict(lr_ace.get("local_accuracy_gate"))
    adaptive = _safe_dict(lr_ace.get("adaptive"))
    expansions = adaptive.get("expansions") if isinstance(adaptive.get("expansions"), list) else []
    latest_expansion = _safe_dict(expansions[-1] if expansions else {})
    trust_label = gate.get("trust_label") or adaptive.get("trust_label") or "not_recorded"
    verification_status = gate.get("verification_status") or "not_recorded"
    selected_count = lr_ace.get("selected_factor_count") or len(lr_ace.get("selected_generators") or [])
    local_error = local_gate.get("absolute_error_hartree")
    local_threshold = local_gate.get("threshold_hartree")

    return html.Div(
        className="qcchem-page qcchem-page--lr-ace",
        children=[
            html.Section(
                className="qcchem-page__hero",
                children=[
                    html.P("Flagship Method", className="qcchem-panel__eyebrow"),
                    html.H2("LR-ACE Method", className="qcchem-page__title"),
                    html.P(
                        "Low-Rank Adaptive Chemistry Eigensolver evidence is shown through generator selection, local exact gates, compression checks, and adaptive expansion provenance.",
                        className="qcchem-page__subtitle",
                    ),
                ],
            ),
            html.Div(
                className="qcchem-metric-grid qcchem-metric-grid--four",
                children=[
                    metric_card("Role", str(lr_ace.get("method_role") or "not recorded"), "QCchem method surface", tone="compact"),
                    metric_card("Profile", str(lr_ace.get("profile") or "not recorded"), "Config default family", tone="compact"),
                    metric_card("Selected factors", str(selected_count), "Generator plan size", tone="compact"),
                    metric_card("Adaptive expansions", str(len(expansions)), "Residual-guided additions", tone="compact"),
                ],
            ),
            html.Div(
                className="qcchem-card-grid qcchem-card-grid--two",
                children=[
                    status_card(
                        "Validation gate",
                        str(trust_label),
                        f"Status {verification_status}; blocking reason {gate.get('blocking_reason') or 'none'}",
                        tone=_tone(trust_label),
                    ),
                    status_card(
                        "Local exact gate",
                        str(local_gate.get("passed")),
                        f"Error {local_error} Ha against threshold {local_threshold} Ha",
                        tone="validated" if local_gate.get("passed") is True else "exploratory",
                    ),
                ],
            ),
            detail_card(
                "Adaptive provenance",
                [
                    ("Enabled", str(adaptive.get("enabled"))),
                    ("Trust label", str(trust_label)),
                    ("Latest selected count", str(latest_expansion.get("selected_count", 0))),
                    ("Latest estimated drop", str(latest_expansion.get("best_estimated_drop_hartree"))),
                ],
                eyebrow="LR-ACE Evidence",
            ),
        ],
    )


def layout() -> html.Div:
    model = build_sample_view_model()
    model.setdefault(
        "lr_ace",
        {
            "method_role": "flagship",
            "profile": "compact",
            "selected_factor_count": 1,
            "validation_gate": {"trust_label": "local_exact_validated", "verification_status": "validated"},
            "local_accuracy_gate": {"passed": True, "absolute_error_hartree": 4.8e-10, "threshold_hartree": 1.6e-3},
            "adaptive": {"enabled": False, "expansions": []},
        },
    )
    return build_lr_ace_method_page(model)
