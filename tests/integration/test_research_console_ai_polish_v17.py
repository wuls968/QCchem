from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from qcchem.core.ai_workspace import AI_WORKSPACE_TICKET_STATUS_ACCEPTED, AI_WORKSPACE_TICKET_STATUS_RETURNED
from qcchem.workflow.ai_store import workspace_root, write_delivery_record, write_ticket_record


def _resolve_layout(layout: object) -> object:
    return layout() if callable(layout) else layout


def _walk_components(component: object) -> Iterable[object]:
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from _walk_components(child)
    else:
        yield from _walk_components(children)


def _collect_text(component: object) -> str:
    parts: list[str] = []
    for item in _walk_components(component):
        if isinstance(item, str):
            parts.append(item)
    return " ".join(parts)


@pytest.mark.integration
def test_overview_page_surfaces_best_evidence_decision_desk() -> None:
    from qcchem.workbench.pages.overview import build_overview_page, build_sample_view_model

    page = build_overview_page(build_sample_view_model())
    page_text = _collect_text(page)

    assert "Best Evidence Desk" in page_text
    assert "Recommended next action" in page_text
    assert "Pending analysis" in page_text
    assert "Trust gap to close" in page_text


@pytest.mark.integration
def test_evidence_console_model_unifies_best_evidence_and_workspace_state(tmp_path: Path) -> None:
    from qcchem.workbench.evidence_console import build_evidence_console_model
    from qcchem.workbench.pages.overview import build_sample_view_model

    root = workspace_root(tmp_path)
    write_ticket_record(
        root,
        {
            "task_id": "analysis-accepted",
            "task_type": "analysis",
            "title": "Review runtime gap",
            "request_text": "Explain the hardware-derived gap.",
            "status": AI_WORKSPACE_TICKET_STATUS_ACCEPTED,
        },
    )
    write_ticket_record(
        root,
        {
            "task_id": "analysis-returned",
            "task_type": "analysis",
            "title": "Returned review",
            "request_text": "Needs sharper limitation notes.",
            "status": AI_WORKSPACE_TICKET_STATUS_RETURNED,
        },
    )

    console = build_evidence_console_model(build_sample_view_model(), workspace_base=tmp_path)

    assert console["best_evidence"]["trust_tier"] == "validated"
    assert console["best_evidence"]["recommended_action"] == "review_runtime_gap"
    assert console["trust_gap"]["chemical_accuracy_gap_hartree"] > 0
    assert console["runtime_boundary"]["submission_health"] == "succeeded"
    assert console["open_tasks"]["pending_analysis"] == 1
    assert console["open_tasks"]["returned"] == 1


@pytest.mark.integration
def test_evidence_console_v2_pages_surface_decision_language() -> None:
    from qcchem.workbench.pages.hardware_campaign import build_hardware_campaign_page, sample_hardware_campaign_model
    from qcchem.workbench.pages.overview import build_overview_page, build_sample_view_model
    from qcchem.workbench.pages.runtime_monitoring import build_runtime_monitoring_page

    model = build_sample_view_model()
    overview_text = _collect_text(build_overview_page(model))
    runtime_text = _collect_text(build_runtime_monitoring_page(model))
    hardware_text = _collect_text(build_hardware_campaign_page(sample_hardware_campaign_model()))

    assert "Evidence Console" in overview_text
    assert "Chemical accuracy gap" in overview_text
    assert "Runtime boundary" in overview_text
    assert "Open AI work" in overview_text

    assert "Runtime Decision" in runtime_text
    assert "Submission health" in runtime_text
    assert "Hardware-derived accuracy" in runtime_text
    assert "Budget / shot usage" in runtime_text
    assert "Action gate" in runtime_text

    assert "Budget Decision" in hardware_text
    assert "Best Retrieved Evidence" in hardware_text
    assert "worth one more controlled attempt" in hardware_text.lower()


@pytest.mark.integration
def test_ai_workspace_page_reads_delivery_history_and_review_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = workspace_root(tmp_path)
    deliveries_dir = root / "deliveries"
    deliveries_dir.mkdir(parents=True, exist_ok=True)
    (deliveries_dir / "delivery-001.json").write_text(
        json.dumps(
            {
                "delivery_id": "delivery-001",
                "task_id": "analysis-001",
                "delivery_kind": "analysis_note",
                "summary": "Hardware campaign summary drafted.",
                "linked_outputs": ["artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_report.md"],
                "review_status": "pending_review",
                "evidence_summary": {
                    "trust_tier": "hardware_verified",
                    "recommended_action": "worth_one_more_controlled_attempt",
                },
            }
        ),
        encoding="utf-8",
    )

    from qcchem.workbench.pages.ai_workspace import layout

    page = _resolve_layout(layout)
    page_text = _collect_text(page)

    assert "Delivery History" in page_text
    assert "Hardware campaign summary drafted." in page_text
    assert "pending_review" in page_text
    assert "worth_one_more_controlled_attempt" in page_text


@pytest.mark.integration
def test_ai_workspace_delivery_history_surfaces_evidence_scope_and_limitations(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = workspace_root(tmp_path)
    write_delivery_record(
        root,
        {
            "delivery_id": "delivery-evidence-001",
            "task_id": "analysis-evidence-001",
            "delivery_kind": "analysis_note",
            "summary": "Runtime evidence interpretation delivered.",
            "review_status": "pending_review",
            "evidence_scope": "H2 hardware campaign only.",
            "limitation_notes": ["Hardware verified is not publication-grade chemistry validation."],
            "recommended_action": "worth one more controlled attempt",
            "linked_evidence_summary": {
                "primary_scientific_claim": "H2 PUCCD layout is the best retrieved runtime anchor.",
                "trust_tier": "hardware_verified",
            },
        },
    )

    from qcchem.workbench.pages.ai_workspace import layout

    page_text = _collect_text(_resolve_layout(layout))

    assert "Evidence scope" in page_text
    assert "H2 hardware campaign only." in page_text
    assert "Limitation notes" in page_text
    assert "publication-grade chemistry validation" in page_text
    assert "worth one more controlled attempt" in page_text


@pytest.mark.integration
def test_floating_assistant_preview_surfaces_evidence_first_context(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "h2_probe"
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "result.json").write_text(
        json.dumps(
            {
                "problem": {"molecule_name": "H2"},
                "evidence_summary": {
                    "primary_scientific_claim": "H2 layout-aware PUCCD remains the leading retrieved hardware case.",
                    "trust_tier": "hardware_verified",
                    "recommended_action": "worth_one_more_controlled_attempt",
                    "runtime_evidence_status": "retrieved_result",
                },
            }
        ),
        encoding="utf-8",
    )

    from qcchem.workbench.components.assistant import build_ticket_preview_content

    preview = build_ticket_preview_content(
        current_ticket_record=None,
        task_type="analysis",
        title="Review hardware probe",
        request_text="Explain whether the current hardware probe is worth another controlled attempt.",
        linked_artifacts_text=str(artifact_root),
        plan_summary="Summarize the evidence and recommend the next action.",
        expected_outputs_text="analysis note",
        risk_notes_text="Do not overstate validated status.",
        workspace_base=tmp_path,
        current_route="/hardware-campaign",
    )
    preview_text = _collect_text(preview)

    assert "Evidence-first context" in preview_text
    assert "H2 layout-aware PUCCD remains the leading retrieved hardware case." in preview_text
    assert "hardware_verified" in preview_text
    assert "worth_one_more_controlled_attempt" in preview_text
    assert "Hardware Campaign" in preview_text


@pytest.mark.integration
def test_floating_assistant_preview_includes_evidence_scope_limitations_and_action(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "h2_probe"
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "result.json").write_text(
        json.dumps(
            {
                "problem": {"molecule_name": "H2"},
                "evidence_summary": {
                    "primary_scientific_claim": "H2 PUCCD layout is the best retrieved runtime anchor.",
                    "trust_tier": "hardware_verified",
                    "recommended_action": "worth_one_more_controlled_attempt",
                    "runtime_evidence_status": "retrieved_result",
                },
            }
        ),
        encoding="utf-8",
    )

    from qcchem.workbench.components.assistant import build_ticket_preview_content

    preview = build_ticket_preview_content(
        current_ticket_record=None,
        task_type="analysis",
        title="Review micro probe",
        request_text="Explain whether another micro probe is justified.",
        linked_artifacts_text=str(artifact_root),
        plan_summary="Compare runtime evidence with chemical accuracy boundary.",
        expected_outputs_text="evidence memo",
        risk_notes_text="Do not overstate hardware_verified.",
        workspace_base=tmp_path,
        current_route="/runtime-monitoring",
    )
    preview_text = _collect_text(preview)

    assert "Evidence Scope" in preview_text
    assert "Limitation Notes" in preview_text
    assert "Recommended Action" in preview_text
    assert "worth_one_more_controlled_attempt" in preview_text


@pytest.mark.integration
def test_floating_assistant_preview_links_returned_delivery_notes(tmp_path: Path) -> None:
    root = workspace_root(tmp_path)
    write_delivery_record(
        root,
        {
            "delivery_id": "delivery-returned-preview",
            "task_id": "ticket-returned-preview",
            "delivery_kind": "analysis_note",
            "summary": "Returned preview handoff.",
            "linked_outputs": ["artifacts/ai_workspace/reviews/preview.md"],
            "review_status": "returned",
            "return_notes": "Add exact artifact paths before retrying this review.",
            "evidence_summary": {"recommended_action": "review_evidence_boundary"},
        },
    )

    from qcchem.workbench.components.assistant import build_ticket_preview_content

    preview = build_ticket_preview_content(
        current_ticket_record={
            "task_id": "ticket-returned-preview",
            "task_type": "analysis",
            "title": "Returned preview",
            "request_text": "Revise the returned handoff.",
            "status": AI_WORKSPACE_TICKET_STATUS_RETURNED,
        },
        task_type="analysis",
        title="Returned preview",
        request_text="Revise the returned handoff.",
        linked_artifacts_text="",
        plan_summary="Address returned scope notes.",
        expected_outputs_text="review memo",
        risk_notes_text="",
        workspace_base=tmp_path,
        current_route="/ai-workspace",
    )
    preview_text = _collect_text(preview)

    assert "Return handoff" in preview_text
    assert "delivery-returned-preview - Returned preview handoff." in preview_text
    assert "address return notes" in preview_text
    assert "Add exact artifact paths before retrying this review." in preview_text


@pytest.mark.integration
def test_theme_css_preserves_hidden_state_for_assistant_surfaces() -> None:
    css = (Path(__file__).resolve().parents[2] / "qcchem" / "workbench" / "assets" / "theme.css").read_text(encoding="utf-8")

    assert "qcchem-ai-provider-drawer[hidden]" in css
    assert "qcchem-ai-assistant-window__body[hidden]" in css
    assert "qcchem-ai-assistant-window__run-guard[hidden]" in css


@pytest.mark.integration
def test_floating_assistant_exposes_position_recovery_controls() -> None:
    from qcchem.workbench.components.assistant import build_floating_assistant

    assistant = build_floating_assistant()
    rendered = str(assistant)
    script = (Path(__file__).resolve().parents[2] / "qcchem" / "workbench" / "assets" / "assistant-window.js").read_text(encoding="utf-8")

    assert "qcchem-ai-assistant-reset-position" in rendered
    assert "Move the assistant back to a safe bottom-right position" in rendered
    assert "resetToDefaultState" in script
    assert "safeViewportTop" in script
