from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.cli.main import main
from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.workflow.ai_store import workspace_root

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_hardware_suite(suite_dir: Path, *, suite_name: str, best_case_name: str, achieved_error: float) -> None:
    suite_dir.mkdir(parents=True, exist_ok=True)
    (suite_dir / "hardware_calibration_summary.json").write_text(
        json.dumps(
            {
                "suite_name": suite_name,
                "artifact_root": str(suite_dir),
                "summary": {
                    "total_cases": 1,
                    "runtime_evidence_status_counts": {"retrieved_result": 1},
                    "hardware_verified_cases": [best_case_name],
                },
                "cases": [
                    {
                        "name": best_case_name,
                        "achieved_error": achieved_error,
                        "meets_chemical_accuracy": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_ai_workspace_docs_and_examples_exist() -> None:
    root = REPO_ROOT
    docs_path = root / "docs" / "ai_workspace.md"
    readme_path = root / "README.md"
    architecture_path = root / "docs" / "architecture.md"
    handoff_path = root / "docs" / "handoff.md"
    provider_path = root / "examples" / "ai_workspace" / "provider.openai-compatible.yaml"
    ticket_path = root / "examples" / "ai_workspace" / "tickets" / "analysis_h2_campaign.json"

    assert docs_path.exists()
    assert readme_path.exists()
    assert architecture_path.exists()
    assert handoff_path.exists()
    assert provider_path.exists()
    assert ticket_path.exists()

    provider = load_ai_provider_spec(provider_path)
    assert provider.provider_kind == "openai_compatible"
    assert provider.model == "gpt-5.4"

    ticket_payload = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert ticket_payload["task_type"] == "analysis"
    assert ticket_payload["status"] == "accepted"
    assert ticket_payload["linked_artifacts"] == ["artifacts/hardware_calibration_suite_v1"]

    docs_body = docs_path.read_text(encoding="utf-8")
    assert "examples/ai_workspace/tickets/analysis_h2_campaign.json" in docs_body
    assert "qcchem ai run-ticket examples/ai_workspace/tickets/analysis_h2_campaign.json" in docs_body
    assert "qcchem ai delivery list" in docs_body
    assert "qcchem ai delivery return" in docs_body

    readme_body = readme_path.read_text(encoding="utf-8")
    assert "## AI Workspace" in readme_body
    assert "floating research copilot shell" in readme_body

    architecture_body = architecture_path.read_text(encoding="utf-8")
    assert "## Agent Interface 层" in architecture_body
    assert "`hardware_verified=True` 只表示真实 runtime 结果已取回" in architecture_body

    handoff_body = handoff_path.read_text(encoding="utf-8")
    assert "workbench page 读取持久化 ticket state" in handoff_body
    assert "floating preview 只镜像当前输入的 request 草稿" in handoff_body


@pytest.mark.parametrize(
    ("task_type", "expected_title"),
    [
        ("analysis", "Research Analysis Ticket"),
        ("execution", "Research Execution Ticket"),
        ("delivery", "Research Delivery Ticket"),
    ],
)
def test_ai_draft_ticket_command_writes_ticket_under_current_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    task_type: str,
    expected_title: str,
) -> None:
    provider = tmp_path / "provider.yaml"
    provider.write_text(
        """
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4-mini
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "ai",
            "draft-ticket",
            "--provider-config",
            str(provider),
            "--task-type",
            task_type,
            "--request",
            "Compare the recent H2 hardware campaign artifacts.",
            "--artifact",
            "artifacts/hardware_calibration_suite_v1",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    ticket_path = Path(payload["ticket_path"])
    assert ticket_path == tmp_path / "artifacts" / "ai_workspace" / "tickets" / f"{ticket_path.stem}.json"
    written_ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert written_ticket["task_type"] == task_type
    assert written_ticket["title"] == expected_title
    assert written_ticket["status"] == "needs_confirmation"
    assert written_ticket["linked_artifacts"] == ["artifacts/hardware_calibration_suite_v1"]


def test_ai_run_ticket_command_rejects_unapproved_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    suite_dir = workspace / "artifacts" / "suite_a"
    _write_hardware_suite(
        suite_dir,
        suite_name="suite_a",
        best_case_name="case_a",
        achieved_error=0.012,
    )
    ticket_dir = workspace / "artifacts" / "ai_workspace" / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = ticket_dir / "analysis-001.json"
    ticket_path.write_text(
        json.dumps(
            {
                "task_id": "analysis-001",
                "task_type": "analysis",
                "title": "Compare hardware campaign",
                "request_text": "Compare hardware campaign results",
                "plan_summary": "Summarize suite status and best case.",
                "expected_outputs": ["summary"],
                "risk_notes": ["Do not overstate validated status."],
                "linked_artifacts": ["artifacts/suite_a"],
                "status": "needs_confirmation",
                "execution_target": "analysis_only_assistant",
            }
        ),
        encoding="utf-8",
    )
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    with pytest.raises(ValueError, match="accepted"):
        main(["ai", "run-ticket", str(ticket_path)])

    assert not (suite_dir / "hardware_runtime_campaign_summary.json").exists()


def test_ai_run_ticket_command_executes_all_linked_artifacts_relative_to_ticket_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "workspace"
    suite_a = workspace / "artifacts" / "suite_a"
    suite_b = workspace / "artifacts" / "suite_b"
    _write_hardware_suite(
        suite_a,
        suite_name="suite_a",
        best_case_name="case_a",
        achieved_error=0.012,
    )
    _write_hardware_suite(
        suite_b,
        suite_name="suite_b",
        best_case_name="case_b",
        achieved_error=0.008,
    )

    ticket_dir = workspace / "artifacts" / "ai_workspace" / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = ticket_dir / "analysis-002.json"
    ticket_path.write_text(
        json.dumps(
            {
                "task_id": "analysis-002",
                "task_type": "analysis",
                "title": "Compare two hardware campaigns",
                "request_text": "Compare both hardware campaign results",
                "plan_summary": "Summarize both suites.",
                "expected_outputs": ["summary"],
                "risk_notes": ["Do not overstate validated status."],
                "linked_artifacts": ["artifacts/suite_a", "artifacts/suite_b"],
                "status": "accepted",
                "execution_target": "analysis_only_assistant",
            }
        ),
        encoding="utf-8",
    )

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    exit_code = main(["ai", "run-ticket", str(ticket_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["task_id"] == "analysis-002"
    assert payload["status"] == "completed"
    assert [item["suite_name"] for item in payload["summaries"]] == ["suite_a", "suite_b"]
    assert payload["summaries"][0]["best_case"]["name"] == "case_a"
    assert payload["summaries"][1]["best_case"]["name"] == "case_b"
    assert (suite_a / "hardware_runtime_campaign_summary.json").exists()
    assert (suite_b / "hardware_runtime_campaign_summary.json").exists()


@pytest.mark.parametrize(
    ("task_type", "expected_status", "expected_delivery_kind", "expect_summary_outputs"),
    [
        ("analysis", "completed", "analysis_note", True),
        ("execution", "completed", "artifact_bundle", True),
        ("delivery", "submitted", "artifact_bundle", False),
    ],
)
def test_ai_run_ticket_command_writes_delivery_record_for_supported_task_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    task_type: str,
    expected_status: str,
    expected_delivery_kind: str,
    expect_summary_outputs: bool,
) -> None:
    workspace = tmp_path / "workspace"
    suite_dir = workspace / "artifacts" / "suite_a"
    _write_hardware_suite(
        suite_dir,
        suite_name="suite_a",
        best_case_name="case_a",
        achieved_error=0.012,
    )

    ticket_dir = workspace / "artifacts" / "ai_workspace" / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    ticket_path = ticket_dir / f"{task_type}-001.json"
    ticket_path.write_text(
        json.dumps(
            {
                "task_id": f"{task_type}-001",
                "task_type": task_type,
                "title": f"{task_type.title()} hardware campaign",
                "request_text": f"Handle the {task_type} hardware campaign task",
                "plan_summary": "Run the accepted task and persist a delivery record.",
                "expected_outputs": ["delivery record"],
                "risk_notes": [],
                "linked_artifacts": ["artifacts/suite_a"],
                "status": "accepted",
                "execution_target": "analysis_only_assistant",
            }
        ),
        encoding="utf-8",
    )

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    exit_code = main(["ai", "run-ticket", str(ticket_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["task_id"] == f"{task_type}-001"
    assert payload["status"] == expected_status

    delivery_record_path = Path(payload["delivery_record"])
    assert delivery_record_path.exists()
    assert delivery_record_path.parent == workspace_root(workspace) / "deliveries"

    delivery_record = json.loads(delivery_record_path.read_text(encoding="utf-8"))
    assert delivery_record["task_id"] == f"{task_type}-001"
    assert delivery_record["delivery_kind"] == expected_delivery_kind
    assert delivery_record["review_status"] == "submitted"
    assert payload["delivery_kind"] == expected_delivery_kind

    if expect_summary_outputs:
        assert payload["linked_outputs"]
        assert (suite_dir / "hardware_runtime_campaign_summary.json").exists()
        assert (suite_dir / "hardware_runtime_campaign_report.md").exists()
    else:
        expected_output = str((workspace / "artifacts" / "suite_a").resolve())
        assert payload["linked_outputs"] == [expected_output]


def test_ai_delivery_list_command_reports_reviewable_delivery_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "workspace"
    root = workspace_root(workspace)
    submitted_path = root / "deliveries" / "delivery-list-submitted.json"
    submitted_path.write_text(
        json.dumps(
            {
                "delivery_id": "delivery-list-submitted",
                "task_id": "analysis-list-001",
                "delivery_kind": "analysis_note",
                "summary": "Submitted analysis delivery.",
                "linked_outputs": [],
                "review_status": "submitted",
            }
        ),
        encoding="utf-8",
    )
    returned_path = root / "deliveries" / "manual-returned-delivery.json"
    returned_path.write_text(
        json.dumps(
            {
                "delivery_id": "delivery-list-returned",
                "task_id": "analysis-list-002",
                "delivery_kind": "artifact_bundle",
                "summary": "Returned artifact bundle.",
                "linked_outputs": ["artifacts/suite_a/report.md"],
                "review_status": "returned",
                "return_notes": "Needs a clearer boundary.",
            }
        ),
        encoding="utf-8",
    )
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    exit_code = main(
        [
            "ai",
            "delivery",
            "list",
            "--workspace-base",
            str(workspace),
            "--status",
            "returned",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["workspace_root"] == str(root.resolve())
    assert payload["filters"] == {"review_status": "returned", "delivery_kind": ""}
    assert payload["total_delivery_count"] == 2
    assert payload["filtered_delivery_count"] == 1
    assert payload["review_status_counts"] == {"returned": 1}
    assert payload["delivery_kind_counts"] == {"artifact_bundle": 1}
    assert payload["deliveries"][0]["delivery_id"] == "delivery-list-returned"
    assert payload["deliveries"][0]["delivery_record"] == str(returned_path.resolve())


def test_ai_delivery_return_command_marks_delivery_and_ticket_returned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "workspace"
    root = workspace_root(workspace)
    ticket_path = root / "tickets" / "analysis-003.json"
    ticket_path.write_text(
        json.dumps(
            {
                "task_id": "analysis-003",
                "task_type": "analysis",
                "title": "Review delivery handoff",
                "request_text": "Review the persisted delivery.",
                "plan_summary": "Keep revision reasons attached to the ticket.",
                "expected_outputs": ["review"],
                "risk_notes": ["Clarify evidence boundary."],
                "linked_artifacts": ["artifacts/suite_a"],
                "status": "completed",
                "execution_target": "analysis_only_assistant",
            }
        ),
        encoding="utf-8",
    )
    delivery_path = root / "deliveries" / "delivery-review-001.json"
    delivery_path.write_text(
        json.dumps(
            {
                "delivery_id": "delivery-review-001",
                "task_id": "analysis-003",
                "delivery_kind": "analysis_note",
                "summary": "Needs a clearer evidence boundary before acceptance.",
                "linked_outputs": ["artifacts/suite_a/hardware_runtime_campaign_report.md"],
                "review_status": "submitted",
                "return_notes": "",
            }
        ),
        encoding="utf-8",
    )
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    exit_code = main(
        [
            "ai",
            "delivery",
            "return",
            str(delivery_path),
            "--return-notes",
            "Clarify the hardware verification boundary.",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["delivery_record"] == str(delivery_path.resolve())
    assert payload["review_status"] == "returned"
    assert payload["return_notes"] == "Clarify the hardware verification boundary."
    assert payload["did_update_ticket"] is True
    assert payload["ticket_link_status"] == "updated"
    assert payload["ticket_record"] == str(ticket_path.resolve())
    assert payload["ticket_status"] == "returned"

    delivery_record = json.loads(delivery_path.read_text(encoding="utf-8"))
    assert delivery_record["review_status"] == "returned"
    assert delivery_record["return_notes"] == "Clarify the hardware verification boundary."

    ticket_record = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert ticket_record["status"] == "returned"
    assert ticket_record["return_notes"] == "Clarify the hardware verification boundary."
    assert ticket_record["linked_return_delivery_record"] == str(delivery_path.resolve())


def test_ai_delivery_review_command_accepts_delivery_without_touching_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "workspace"
    root = workspace_root(workspace)
    ticket_path = root / "tickets" / "analysis-004.json"
    ticket_path.write_text(
        json.dumps(
            {
                "task_id": "analysis-004",
                "task_type": "analysis",
                "title": "Accept delivery handoff",
                "request_text": "Accept the persisted delivery.",
                "status": "completed",
                "execution_target": "analysis_only_assistant",
            }
        ),
        encoding="utf-8",
    )
    delivery_path = root / "deliveries" / "delivery-review-002.json"
    delivery_path.write_text(
        json.dumps(
            {
                "delivery_id": "delivery-review-002",
                "task_id": "analysis-004",
                "delivery_kind": "analysis_note",
                "summary": "Evidence boundary is clear.",
                "linked_outputs": [],
                "review_status": "submitted",
                "return_notes": "Old revision note.",
            }
        ),
        encoding="utf-8",
    )
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    exit_code = main(["ai", "delivery", "review", str(delivery_path), "--status", "accepted"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["review_status"] == "accepted"
    assert payload["did_update_ticket"] is False
    assert payload["ticket_link_status"] == "not_applicable"

    delivery_record = json.loads(delivery_path.read_text(encoding="utf-8"))
    assert delivery_record["review_status"] == "accepted"
    assert delivery_record["return_notes"] == ""

    ticket_record = json.loads(ticket_path.read_text(encoding="utf-8"))
    assert ticket_record["status"] == "completed"
    assert "return_notes" not in ticket_record


def test_ai_delivery_return_command_requires_return_notes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "workspace"
    root = workspace_root(workspace)
    delivery_path = root / "deliveries" / "delivery-review-003.json"
    delivery_path.write_text(
        json.dumps(
            {
                "delivery_id": "delivery-review-003",
                "task_id": "analysis-005",
                "delivery_kind": "analysis_note",
                "summary": "Needs revision.",
                "linked_outputs": [],
                "review_status": "submitted",
                "return_notes": "",
            }
        ),
        encoding="utf-8",
    )
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)

    exit_code = main(["ai", "delivery", "return", str(delivery_path)])

    assert exit_code == 2
    assert "Return notes are required" in capsys.readouterr().out
    delivery_record = json.loads(delivery_path.read_text(encoding="utf-8"))
    assert delivery_record["review_status"] == "submitted"
    assert delivery_record["return_notes"] == ""
