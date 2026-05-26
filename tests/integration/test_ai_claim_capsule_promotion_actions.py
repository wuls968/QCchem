from __future__ import annotations

import json
from pathlib import Path

from qcchem.cli.main import main
from qcchem.workflow.ai_store import workspace_root, write_ticket_record
from tests.unit.test_claim_compiler import _write_hardware_artifact
from tests.unit.test_evidence_capsule import _write_run
from tests.unit.test_promotion_gate import _write_lr_ace


def _ticket(workspace: Path, *, task_id: str, action_kind: str, linked_artifacts: list[str], inputs: dict[str, object]) -> Path:
    root = workspace_root(workspace)
    return write_ticket_record(
        root,
        {
            "task_id": task_id,
            "task_type": "analysis",
            "title": action_kind,
            "request_text": "Run local Trust-First review.",
            "status": "accepted",
            "execution_target": "analysis_only_assistant",
            "linked_artifacts": linked_artifacts,
            "action_plan": {
                "action_id": f"action-{task_id}",
                "action_kind": action_kind,
                "title": action_kind,
                "rationale": "test",
                "inputs": inputs,
                "outputs": {},
                "requires_confirmation": True,
                "risk_tier": "standard",
                "allowed": True,
                "blocked_reason": "",
                "route": "analysis_only_assistant",
            },
        },
    )


def test_ai_run_ticket_executes_new_local_review_actions(tmp_path: Path, monkeypatch, capsys) -> None:
    workspace = tmp_path / "workspace"
    hardware = _write_hardware_artifact(workspace / "artifacts" / "hardware")
    run_root = workspace / "artifacts" / "h2"
    _write_run(run_root)
    lr_ace = _write_lr_ace(workspace / "artifacts" / "lr_ace")
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)

    claim_ticket = _ticket(
        workspace,
        task_id="claim-001",
        action_kind="claim_check",
        linked_artifacts=[str(hardware)],
        inputs={"targets": [str(hardware)], "claim_text": "hardware_verified proves publication-grade chemical accuracy"},
    )
    assert main(["ai", "run-ticket", str(claim_ticket)]) == 0
    claim_payload = json.loads(capsys.readouterr().out)
    assert claim_payload["claim_review"]["support_level"] == "overclaimed"

    capsule_ticket = _ticket(
        workspace,
        task_id="capsule-001",
        action_kind="capsule_validate",
        linked_artifacts=[str(run_root)],
        inputs={"artifact_root": str(run_root)},
    )
    assert main(["ai", "run-ticket", str(capsule_ticket)]) == 0
    capsule_payload = json.loads(capsys.readouterr().out)
    assert capsule_payload["evidence_capsule"]["capsule_status"] == "complete"

    promotion_ticket = _ticket(
        workspace,
        task_id="promotion-001",
        action_kind="promotion_review",
        linked_artifacts=[str(lr_ace)],
        inputs={"artifact": str(lr_ace), "target": "validated_algorithm_candidate"},
    )
    assert main(["ai", "run-ticket", str(promotion_ticket)]) == 0
    promotion_payload = json.loads(capsys.readouterr().out)
    assert promotion_payload["promotion_review"]["status"] == "blocked"
