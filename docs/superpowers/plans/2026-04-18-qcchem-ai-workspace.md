# QCchem AI Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a task-centric AI workspace for QCchem with an OpenAI-compatible provider layer, formal task tickets and deliveries, a floating workbench copilot, and a secondary AI workspace page that routes execution through the existing QCchem workflow and agent protocol.

**Architecture:** Add a small AI workspace domain layer (`provider/session/ticket/delivery/binding`) owned by QCchem, then build a provider adapter and task orchestrator on top of it. Reuse existing `qcchem agent` and workflow entry points for execution, and surface the new system through both a CLI control plane and a Dash workbench UI that keeps “plan first, then execute” as the default contract.

**Tech Stack:** Python dataclasses, YAML/JSON config loading, existing QCchem workflow/agent modules, OpenAI Python SDK with OpenAI-compatible `base_url`, Dash workbench UI, client-side workbench asset JS/CSS, pytest.

---

## File Structure

### New files

- `qcchem/core/ai_workspace.py`
  - Own the formal domain model: provider, session, task ticket, agent binding, delivery record.
- `qcchem/io/ai_workspace_config.py`
  - Load and validate AI provider config files and AI workspace task payloads.
- `qcchem/workflow/ai_store.py`
  - Read/write workspace JSON state for sessions, tickets, deliveries, bindings.
- `qcchem/workflow/ai_assistant.py`
  - OpenAI-compatible provider adapter and prompt-to-structured-output helpers.
- `qcchem/workflow/ai_workspace.py`
  - Draft tickets, accept tickets, dispatch execution, write delivery records, answer analysis questions.
- `qcchem/workbench/components/assistant.py`
  - Floating assistant window, task ticket preview, provider drawer shell, status chips.
- `qcchem/workbench/pages/ai_workspace.py`
  - Secondary AI workspace page with inbox/running/submitted/completed/returned sections.
- `qcchem/workbench/assets/assistant-window.js`
  - Client-side drag/resize/minimize behavior for the floating window.
- `tests/unit/test_ai_workspace_domain_v15.py`
  - Domain/config parsing tests.
- `tests/unit/test_ai_assistant_v15.py`
  - Provider adapter and structured ticket drafting tests.
- `tests/integration/test_ai_workspace_cli_v15.py`
  - CLI and orchestration integration tests.
- `tests/integration/test_workbench_ai_workspace_v15.py`
  - Workbench shell, floating window, and AI workspace page tests.
- `docs/ai_workspace.md`
  - User-facing docs for provider setup, task flows, and boundaries.
- `examples/ai_workspace/provider.openai-compatible.yaml`
  - Safe example provider config using `api_key_ref`.
- `examples/ai_workspace/tickets/`
  - Seed examples for execution, analysis, and delivery tasks.

### Modified files

- `pyproject.toml`
  - Add optional dependency group and base dependency for OpenAI-compatible provider calls.
- `qcchem/cli/main.py`
  - Add `qcchem ai ...` command group.
- `qcchem/workflow/agent.py`
  - Expose small helper entry points reusable by the AI workspace dispatcher.
- `qcchem/workbench/app.py`
  - Register stores/callbacks for AI workspace UI.
- `qcchem/workbench/components/layout.py`
  - Mount floating assistant shell into the existing workbench layout.
- `qcchem/workbench/pages/_registry.py`
  - Register the AI workspace page.
- `qcchem/workbench/assets/theme.css`
  - Style the floating assistant, drawer, workspace board, and task states.
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/handoff.md`
- `docs/verified_scope.md`

### State storage location

- Persist AI workspace state under:
  - `artifacts/ai_workspace/sessions/`
  - `artifacts/ai_workspace/tickets/`
  - `artifacts/ai_workspace/deliveries/`
  - `artifacts/ai_workspace/providers/`
  - `artifacts/ai_workspace/bindings/`

This keeps the AI layer near the existing artifact model without pretending chat transcripts are scientific results.

---

### Task 1: Define the AI workspace domain model and persistence shape

**Files:**
- Create: `/Users/a0000/QCchem/qcchem/core/ai_workspace.py`
- Create: `/Users/a0000/QCchem/qcchem/io/ai_workspace_config.py`
- Create: `/Users/a0000/QCchem/qcchem/workflow/ai_store.py`
- Test: `/Users/a0000/QCchem/tests/unit/test_ai_workspace_domain_v15.py`

- [ ] **Step 1: Write the failing domain/config tests**

```python
from pathlib import Path

import pytest

from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.workflow.ai_store import workspace_root, write_ticket_record, read_ticket_record


def test_load_ai_provider_spec_openai_compatible(tmp_path: Path) -> None:
    config = tmp_path / "provider.yaml"
    config.write_text(
        """
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
  timeout_seconds: 60
  default_temperature: 0.1
  default_max_tokens: 2000
  enabled: true
""".strip(),
        encoding="utf-8",
    )

    spec = load_ai_provider_spec(config)

    assert spec.provider_kind == "openai_compatible"
    assert spec.base_url == "https://api.example.com/v1"
    assert spec.api_key_ref == "OPENAI_API_KEY"


def test_write_and_read_ticket_record_roundtrip(tmp_path: Path) -> None:
    root = workspace_root(tmp_path)
    record = {
        "task_id": "ticket-001",
        "task_type": "analysis",
        "title": "Compare H2 hardware probes",
        "status": "needs_confirmation",
    }

    path = write_ticket_record(root, record)
    loaded = read_ticket_record(path)

    assert path.name == "ticket-001.json"
    assert loaded["title"] == "Compare H2 hardware probes"


def test_load_ai_provider_spec_rejects_unknown_provider_kind(tmp_path: Path) -> None:
    config = tmp_path / "provider.yaml"
    config.write_text(
        """
ai_provider:
  provider_name: invalid
  provider_kind: unsupported
  base_url: https://api.example.com/v1
  api_key_ref: BAD_KEY
  model: bad-model
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="provider_kind"):
        load_ai_provider_spec(config)
```

- [ ] **Step 2: Run the unit test file and confirm it fails**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/unit/test_ai_workspace_domain_v15.py -q
```

Expected: FAIL with `ModuleNotFoundError` or missing symbol errors for `qcchem.core.ai_workspace`, `load_ai_provider_spec`, and store helpers.

- [ ] **Step 3: Implement the minimal domain model and JSON store**

```python
# /Users/a0000/QCchem/qcchem/core/ai_workspace.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AIProviderSpec:
    provider_name: str
    provider_kind: str = "openai_compatible"
    base_url: str = ""
    api_key_ref: str = ""
    model: str = ""
    timeout_seconds: int = 60
    default_temperature: float = 0.1
    default_max_tokens: int = 2000
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass(slots=True)
class AITaskTicket:
    task_id: str
    task_type: str
    title: str
    request_text: str
    plan_summary: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_outputs: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    boundary_notes: list[str] = field(default_factory=list)
    confirmation_required: bool = True
    execution_target: str = "analysis_only_assistant"
    linked_artifacts: list[str] = field(default_factory=list)
    linked_session_id: str | None = None
    status: str = "draft"

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


# /Users/a0000/QCchem/qcchem/io/ai_workspace_config.py
from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.core.ai_workspace import AIProviderSpec

SUPPORTED_PROVIDER_KINDS = {"openai_compatible", "anthropic", "gemini", "local_compatible"}


def load_ai_provider_spec(path: Path) -> AIProviderSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("ai_provider"), dict):
        raise ValueError("Expected top-level ai_provider mapping.")
    payload = raw["ai_provider"]
    provider_kind = str(payload.get("provider_kind", "")).strip()
    if provider_kind not in SUPPORTED_PROVIDER_KINDS:
        raise ValueError(f"provider_kind must be one of {sorted(SUPPORTED_PROVIDER_KINDS)}")
    return AIProviderSpec(
        provider_name=str(payload.get("provider_name", "")).strip(),
        provider_kind=provider_kind,
        base_url=str(payload.get("base_url", "")).strip(),
        api_key_ref=str(payload.get("api_key_ref", "")).strip(),
        model=str(payload.get("model", "")).strip(),
        timeout_seconds=int(payload.get("timeout_seconds", 60)),
        default_temperature=float(payload.get("default_temperature", 0.1)),
        default_max_tokens=int(payload.get("default_max_tokens", 2000)),
        capabilities=list(payload.get("capabilities", [])),
        enabled=bool(payload.get("enabled", True)),
    )


# /Users/a0000/QCchem/qcchem/workflow/ai_store.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def workspace_root(base: Path | None = None) -> Path:
    root = (base or Path.cwd()) / "artifacts" / "ai_workspace"
    for name in ("sessions", "tickets", "deliveries", "providers", "bindings"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def write_ticket_record(root: Path, record: dict[str, Any]) -> Path:
    path = root / "tickets" / f"{record['task_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path


def read_ticket_record(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run the unit tests again**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/unit/test_ai_workspace_domain_v15.py -q
```

Expected: PASS for all domain/config/store round-trip tests.

- [ ] **Step 5: Commit the domain layer**

```bash
cd /Users/a0000/QCchem
git add \
  qcchem/core/ai_workspace.py \
  qcchem/io/ai_workspace_config.py \
  qcchem/workflow/ai_store.py \
  tests/unit/test_ai_workspace_domain_v15.py
git commit -m "feat: add AI workspace domain model"
```

---

### Task 2: Add the OpenAI-compatible provider adapter and structured ticket drafting

**Files:**
- Modify: `/Users/a0000/QCchem/pyproject.toml`
- Create: `/Users/a0000/QCchem/qcchem/workflow/ai_assistant.py`
- Test: `/Users/a0000/QCchem/tests/unit/test_ai_assistant_v15.py`

- [ ] **Step 1: Write failing provider adapter tests**

```python
from qcchem.core.ai_workspace import AIProviderSpec
from qcchem.workflow.ai_assistant import build_openai_client_kwargs, draft_analysis_ticket


def test_build_openai_client_kwargs_uses_base_url_and_key_ref(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret-token")
    spec = AIProviderSpec(
        provider_name="research-openai",
        provider_kind="openai_compatible",
        base_url="https://api.example.com/v1",
        api_key_ref="OPENAI_API_KEY",
        model="gpt-5.4-mini",
    )

    kwargs = build_openai_client_kwargs(spec)

    assert kwargs["base_url"] == "https://api.example.com/v1"
    assert kwargs["api_key"] == "secret-token"


def test_draft_analysis_ticket_returns_structured_ticket() -> None:
    payload = {
        "title": "Summarize H2 campaign",
        "plan_summary": "Compare runtime artifacts and produce a next-step recommendation.",
        "expected_outputs": ["summary.json", "markdown note"],
        "risk_notes": ["Do not overstate chemical accuracy."],
    }

    ticket = draft_analysis_ticket(
        request_text="Summarize the recent H2 campaign.",
        structured_payload=payload,
        linked_artifacts=["artifacts/hardware_calibration_suite_v1"],
    )

    assert ticket.task_type == "analysis"
    assert ticket.status == "needs_confirmation"
    assert "summary.json" in ticket.expected_outputs
```

- [ ] **Step 2: Run the provider adapter tests and confirm failure**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/unit/test_ai_assistant_v15.py -q
```

Expected: FAIL because `ai_assistant.py` and helper functions do not exist.

- [ ] **Step 3: Implement the provider adapter and ticket drafting helpers**

```python
# /Users/a0000/QCchem/qcchem/workflow/ai_assistant.py
from __future__ import annotations

import os
import uuid
from typing import Any

from qcchem.core.ai_workspace import AIProviderSpec, AITaskTicket


def build_openai_client_kwargs(spec: AIProviderSpec) -> dict[str, Any]:
    api_key = os.environ.get(spec.api_key_ref, "")
    if not api_key:
        raise ValueError(f"Missing API key environment variable: {spec.api_key_ref}")
    return {
        "api_key": api_key,
        "base_url": spec.base_url,
        "timeout": spec.timeout_seconds,
    }


def draft_analysis_ticket(
    *,
    request_text: str,
    structured_payload: dict[str, Any],
    linked_artifacts: list[str],
) -> AITaskTicket:
    return AITaskTicket(
        task_id=f"analysis-{uuid.uuid4().hex[:10]}",
        task_type="analysis",
        title=str(structured_payload.get("title", "Research Analysis")).strip(),
        request_text=request_text,
        plan_summary=str(structured_payload.get("plan_summary", "")).strip(),
        expected_outputs=list(structured_payload.get("expected_outputs", [])),
        risk_notes=list(structured_payload.get("risk_notes", [])),
        linked_artifacts=linked_artifacts,
        status="needs_confirmation",
        execution_target="analysis_only_assistant",
    )
```

```toml
# /Users/a0000/QCchem/pyproject.toml
[project.optional-dependencies]
ui = ["dash>=2.18", "plotly>=5.24", "pandas>=2.2"]
ai = ["openai>=1.76.0"]
```

- [ ] **Step 4: Run the new unit tests**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/unit/test_ai_assistant_v15.py -q
```

Expected: PASS, with no network calls required.

- [ ] **Step 5: Commit the provider adapter**

```bash
cd /Users/a0000/QCchem
git add \
  pyproject.toml \
  qcchem/workflow/ai_assistant.py \
  tests/unit/test_ai_assistant_v15.py
git commit -m "feat: add OpenAI-compatible AI provider adapter"
```

---

### Task 3: Build the AI workspace orchestrator and CLI control plane

**Files:**
- Create: `/Users/a0000/QCchem/qcchem/workflow/ai_workspace.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/agent.py`
- Modify: `/Users/a0000/QCchem/qcchem/cli/main.py`
- Test: `/Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py`

- [ ] **Step 1: Write the failing orchestration and CLI tests**

```python
from pathlib import Path

from qcchem.cli.main import main


def test_ai_draft_ticket_command_writes_ticket(tmp_path: Path) -> None:
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

    exit_code = main(
        [
            "ai",
            "draft-ticket",
            "--provider-config",
            str(provider),
            "--task-type",
            "analysis",
            "--request",
            "Compare the recent H2 hardware campaign artifacts.",
            "--artifact",
            "artifacts/hardware_calibration_suite_v1",
        ]
    )

    assert exit_code == 0


def test_ai_run_ticket_command_executes_existing_agent_task(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret-token")
    ticket_path = tmp_path / "ticket.json"
    ticket_path.write_text(
        """
{
  "task_id": "analysis-001",
  "task_type": "analysis",
  "title": "Compare hardware campaign",
  "request_text": "Compare hardware campaign results",
  "plan_summary": "Summarize suite status and best case.",
  "expected_outputs": ["summary"],
  "risk_notes": ["Do not overstate validated status."],
  "linked_artifacts": ["artifacts/hardware_calibration_suite_v1"],
  "status": "accepted",
  "execution_target": "analysis_only_assistant"
}
""".strip(),
        encoding="utf-8",
    )

    exit_code = main(["ai", "run-ticket", str(ticket_path)])

    assert exit_code == 0
```

- [ ] **Step 2: Run the CLI integration tests and confirm failure**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py -q
```

Expected: FAIL because `qcchem ai` commands and orchestration logic do not exist.

- [ ] **Step 3: Implement the orchestrator and CLI commands**

```python
# /Users/a0000/QCchem/qcchem/workflow/ai_workspace.py
from __future__ import annotations

import json
from pathlib import Path

from qcchem.core.ai_workspace import AITaskTicket
from qcchem.io.ai_workspace_config import load_ai_provider_spec
from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary
from qcchem.workflow.ai_assistant import draft_analysis_ticket
from qcchem.workflow.ai_store import workspace_root, write_ticket_record
from qcchem.workflow.agent import summarize_agent_target


def draft_ticket_from_request(
    *,
    provider_config: Path,
    task_type: str,
    request_text: str,
    linked_artifacts: list[str],
) -> Path:
    _provider = load_ai_provider_spec(provider_config)
    if task_type != "analysis":
        raise ValueError("First iteration only drafts analysis tickets from free-form requests.")
    ticket = draft_analysis_ticket(
        request_text=request_text,
        structured_payload={
            "title": "Research Analysis Ticket",
            "plan_summary": "Read the linked QCchem artifacts, summarize the main findings, and produce a recommendation.",
            "expected_outputs": ["analysis summary", "follow-up recommendation"],
            "risk_notes": ["Respect validated/exploratory/unstable boundaries."],
        },
        linked_artifacts=linked_artifacts,
    )
    return write_ticket_record(workspace_root(Path.cwd()), ticket.to_record())


def run_ticket(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ticket = AITaskTicket(**payload)
    if ticket.task_type == "analysis" and ticket.linked_artifacts:
        summary = summarize_agent_target(Path(ticket.linked_artifacts[0]))
        return {
            "task_id": ticket.task_id,
            "status": "completed",
            "delivery_kind": "analysis_note",
            "summary": build_hardware_campaign_summary(summary),
        }
    raise ValueError(f"Unsupported ticket execution path: {ticket.task_type}")
```

```python
# /Users/a0000/QCchem/qcchem/cli/main.py
ai_parser = subparsers.add_parser("ai", help="AI workspace commands.")
ai_subparsers = ai_parser.add_subparsers(dest="ai_command", required=True)

ai_draft = ai_subparsers.add_parser("draft-ticket", help="Draft an AI workspace task ticket.")
ai_draft.add_argument("--provider-config", type=Path, required=True)
ai_draft.add_argument("--task-type", choices=["analysis", "execution", "delivery"], required=True)
ai_draft.add_argument("--request", required=True)
ai_draft.add_argument("--artifact", action="append", default=[])

ai_run = ai_subparsers.add_parser("run-ticket", help="Run an accepted AI task ticket.")
ai_run.add_argument("ticket", type=Path)
```

```python
if args.command == "ai":
    from qcchem.workflow.ai_workspace import draft_ticket_from_request, run_ticket

    if args.ai_command == "draft-ticket":
        path = draft_ticket_from_request(
            provider_config=args.provider_config,
            task_type=args.task_type,
            request_text=args.request,
            linked_artifacts=args.artifact,
        )
        print(f"AI ticket drafted: {path}")
        return 0
    if args.ai_command == "run-ticket":
        result = run_ticket(args.ticket)
        print(json.dumps(to_primitive(result), indent=2, sort_keys=True))
        return 0
```

- [ ] **Step 4: Re-run the CLI integration tests**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py -q
```

Expected: PASS for drafting and running analysis tickets through the CLI.

- [ ] **Step 5: Commit the orchestration layer**

```bash
cd /Users/a0000/QCchem
git add \
  qcchem/workflow/ai_workspace.py \
  qcchem/workflow/agent.py \
  qcchem/cli/main.py \
  tests/integration/test_ai_workspace_cli_v15.py
git commit -m "feat: add AI workspace ticket orchestration"
```

---

### Task 4: Persist deliveries and support the three task categories in the workspace backend

**Files:**
- Modify: `/Users/a0000/QCchem/qcchem/core/ai_workspace.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/ai_store.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/ai_workspace.py`
- Test: `/Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py`

- [ ] **Step 1: Expand the integration tests to cover execution, analysis, and delivery records**

```python
from pathlib import Path
import json

from qcchem.workflow.ai_store import workspace_root


def test_run_ticket_writes_delivery_record(tmp_path: Path) -> None:
    ticket_path = tmp_path / "ticket.json"
    ticket_path.write_text(
        json.dumps(
            {
                "task_id": "delivery-001",
                "task_type": "delivery",
                "title": "Submit campaign summary",
                "request_text": "Submit the latest hardware campaign summary.",
                "plan_summary": "Create a delivery record for the linked report.",
                "expected_outputs": ["delivery record"],
                "risk_notes": [],
                "linked_artifacts": ["artifacts/hardware_calibration_suite_v1"],
                "status": "accepted",
                "execution_target": "analysis_only_assistant",
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["ai", "run-ticket", str(ticket_path)])

    assert exit_code == 0
    deliveries = list((workspace_root(Path.cwd()) / "deliveries").glob("*.json"))
    assert deliveries
```

- [ ] **Step 2: Run the integration tests and confirm the new delivery assertion fails**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py -q
```

Expected: FAIL because delivery records are not written yet and task-type routing is incomplete.

- [ ] **Step 3: Add delivery records and category-aware ticket handling**

```python
# /Users/a0000/QCchem/qcchem/core/ai_workspace.py
@dataclass(slots=True)
class AIDeliveryRecord:
    delivery_id: str
    task_id: str
    delivery_kind: str
    summary: str
    linked_outputs: list[str] = field(default_factory=list)
    submitted_by: str = "assistant"
    submitted_to: str = "user"
    review_status: str = "submitted"
    return_notes: str = ""

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
```

```python
# /Users/a0000/QCchem/qcchem/workflow/ai_store.py
def write_delivery_record(root: Path, record: dict[str, Any]) -> Path:
    path = root / "deliveries" / f"{record['delivery_id']}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path
```

```python
# /Users/a0000/QCchem/qcchem/workflow/ai_workspace.py
from qcchem.core.ai_workspace import AIDeliveryRecord
from qcchem.workflow.ai_store import write_delivery_record
import uuid


def _write_delivery(ticket: AITaskTicket, *, summary: str, outputs: list[str]) -> dict[str, object]:
    root = workspace_root(Path.cwd())
    delivery = AIDeliveryRecord(
        delivery_id=f"delivery-{uuid.uuid4().hex[:10]}",
        task_id=ticket.task_id,
        delivery_kind="analysis_note" if ticket.task_type == "analysis" else "artifact_bundle",
        summary=summary,
        linked_outputs=outputs,
    )
    path = write_delivery_record(root, delivery.to_record())
    return {"delivery_record": str(path), "review_status": delivery.review_status}


def run_ticket(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ticket = AITaskTicket(**payload)
    if ticket.task_type == "analysis" and ticket.linked_artifacts:
        summary = summarize_agent_target(Path(ticket.linked_artifacts[0]))
        delivery = _write_delivery(
            ticket,
            summary="Hardware campaign summary completed.",
            outputs=[summary["summary_json"], summary["report_markdown"]],
        )
        return {"task_id": ticket.task_id, "status": "completed", **delivery}
    if ticket.task_type == "delivery":
        delivery = _write_delivery(
            ticket,
            summary="Delivery ticket submitted.",
            outputs=ticket.linked_artifacts,
        )
        return {"task_id": ticket.task_id, "status": "submitted", **delivery}
    raise ValueError(f"Unsupported ticket execution path: {ticket.task_type}")
```

- [ ] **Step 4: Re-run the integration tests**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py -q
```

Expected: PASS, with delivery records written to `artifacts/ai_workspace/deliveries/`.

- [ ] **Step 5: Commit the delivery pipeline**

```bash
cd /Users/a0000/QCchem
git add \
  qcchem/core/ai_workspace.py \
  qcchem/workflow/ai_store.py \
  qcchem/workflow/ai_workspace.py \
  tests/integration/test_ai_workspace_cli_v15.py
git commit -m "feat: add AI workspace delivery records"
```

---

### Task 5: Add the floating assistant UI shell and the dedicated AI workspace page

**Files:**
- Create: `/Users/a0000/QCchem/qcchem/workbench/components/assistant.py`
- Create: `/Users/a0000/QCchem/qcchem/workbench/pages/ai_workspace.py`
- Create: `/Users/a0000/QCchem/qcchem/workbench/assets/assistant-window.js`
- Modify: `/Users/a0000/QCchem/qcchem/workbench/components/layout.py`
- Modify: `/Users/a0000/QCchem/qcchem/workbench/app.py`
- Modify: `/Users/a0000/QCchem/qcchem/workbench/pages/_registry.py`
- Modify: `/Users/a0000/QCchem/qcchem/workbench/assets/theme.css`
- Test: `/Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py`

- [ ] **Step 1: Write failing workbench UI tests**

```python
from qcchem.workbench.app import create_app


def test_workbench_registers_ai_workspace_page() -> None:
    app = create_app()
    paths = {page["path"] for page in app.page_registry.values()}
    assert "/ai-workspace" in paths


def test_workbench_shell_contains_floating_assistant_ids() -> None:
    app = create_app()
    layout = app.layout()
    rendered = str(layout)
    assert "qcchem-ai-assistant-window" in rendered
    assert "qcchem-ai-provider-drawer" in rendered
```

- [ ] **Step 2: Run the UI tests and confirm failure**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py -q
```

Expected: FAIL because the AI page, floating assistant component, and drawer IDs do not exist.

- [ ] **Step 3: Implement the floating window, page, and shell registration**

```python
# /Users/a0000/QCchem/qcchem/workbench/components/assistant.py
from dash import dcc, html


def build_floating_assistant() -> html.Div:
    return html.Div(
        id="qcchem-ai-assistant-window",
        className="qcchem-ai-assistant-window",
        children=[
            html.Div(
                className="qcchem-ai-assistant-window__header",
                children=[
                    html.Div("Research Copilot", className="qcchem-ai-assistant-window__title"),
                    html.Button("–", id="qcchem-ai-assistant-minimize", className="qcchem-ai-assistant-window__control"),
                ],
            ),
            html.Div(
                id="qcchem-ai-assistant-body",
                className="qcchem-ai-assistant-window__body",
                children=[
                    dcc.Textarea(
                        id="qcchem-ai-request-input",
                        className="qcchem-ai-assistant-window__input",
                        placeholder="Ask a research question or draft a task ticket…",
                    ),
                    html.Div(id="qcchem-ai-current-ticket-preview"),
                    html.Button("Draft Ticket", id="qcchem-ai-draft-ticket", className="qcchem-ai-assistant-window__action"),
                ],
            ),
            html.Div(
                id="qcchem-ai-provider-drawer",
                className="qcchem-ai-provider-drawer",
                children=[
                    html.Div("Provider Settings", className="qcchem-ai-provider-drawer__title"),
                    dcc.Input(id="qcchem-ai-provider-base-url", placeholder="base_url"),
                    dcc.Input(id="qcchem-ai-provider-model", placeholder="model"),
                    dcc.Input(id="qcchem-ai-provider-key-ref", placeholder="api_key_ref"),
                ],
            ),
        ],
    )
```

```python
# /Users/a0000/QCchem/qcchem/workbench/pages/ai_workspace.py
import dash
from dash import html


dash.register_page(__name__, path="/ai-workspace", name="AI Workspace", order=11)


def layout() -> html.Div:
    return html.Div(
        className="qcchem-ai-workspace-page",
        children=[
            html.H1("AI Workspace"),
            html.Div(id="qcchem-ai-task-inbox"),
            html.Div(id="qcchem-ai-task-running"),
            html.Div(id="qcchem-ai-task-submitted"),
            html.Div(id="qcchem-ai-agent-bindings"),
        ],
    )
```

```python
# /Users/a0000/QCchem/qcchem/workbench/components/layout.py
from qcchem.workbench.components.assistant import build_floating_assistant

# add build_floating_assistant() near the end of build_shell()
```

```javascript
// /Users/a0000/QCchem/qcchem/workbench/assets/assistant-window.js
document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("qcchem-ai-assistant-window");
  if (!root) return;
  root.dataset.minimized = "false";
});
```

- [ ] **Step 4: Run the workbench AI UI tests**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py -q
```

Expected: PASS, proving that the page and floating shell elements are registered.

- [ ] **Step 5: Commit the UI shell**

```bash
cd /Users/a0000/QCchem
git add \
  qcchem/workbench/components/assistant.py \
  qcchem/workbench/pages/ai_workspace.py \
  qcchem/workbench/assets/assistant-window.js \
  qcchem/workbench/components/layout.py \
  qcchem/workbench/app.py \
  qcchem/workbench/pages/_registry.py \
  qcchem/workbench/assets/theme.css \
  tests/integration/test_workbench_ai_workspace_v15.py
git commit -m "feat: add AI workspace workbench surfaces"
```

---

### Task 6: Bind the floating UI to real workspace state and task flows

**Files:**
- Modify: `/Users/a0000/QCchem/qcchem/workflow/ai_store.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/ai_workspace.py`
- Modify: `/Users/a0000/QCchem/qcchem/workbench/app.py`
- Modify: `/Users/a0000/QCchem/qcchem/workbench/pages/ai_workspace.py`
- Test: `/Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py`

- [ ] **Step 1: Expand the workbench tests to require persisted task visibility**

```python
from pathlib import Path

from qcchem.workflow.ai_store import workspace_root, write_ticket_record


def test_ai_workspace_page_reads_ticket_inbox(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = workspace_root(tmp_path)
    write_ticket_record(
        root,
        {
            "task_id": "ticket-inbox-001",
            "task_type": "analysis",
            "title": "Explain H2 runtime gap",
            "request_text": "Explain the recent runtime gap",
            "status": "needs_confirmation",
        },
    )

    app = create_app()
    layout = str(app.validation_layout)

    assert "ticket-inbox-001" in layout or "Explain H2 runtime gap" in layout
```

- [ ] **Step 2: Run the workbench tests and confirm failure**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py -q
```

Expected: FAIL because the UI does not yet read persisted AI workspace state.

- [ ] **Step 3: Implement workspace state readers and Dash callbacks**

```python
# /Users/a0000/QCchem/qcchem/workflow/ai_store.py
def list_ticket_records(root: Path, *, status: str | None = None) -> list[dict[str, Any]]:
    tickets = []
    for path in sorted((root / "tickets").glob("*.json")):
        payload = read_ticket_record(path)
        if status is None or payload.get("status") == status:
            tickets.append(payload)
    return tickets
```

```python
# /Users/a0000/QCchem/qcchem/workbench/pages/ai_workspace.py
from qcchem.workflow.ai_store import list_ticket_records, workspace_root


def _ticket_card(record: dict[str, object]) -> html.Div:
    return html.Div(
        className="qcchem-ai-workspace-page__ticket",
        children=[
            html.Strong(str(record.get("title", "Untitled Task"))),
            html.Div(str(record.get("task_type", "unknown"))),
            html.Div(str(record.get("status", "draft"))),
        ],
    )


def layout() -> html.Div:
    root = workspace_root(Path.cwd())
    inbox = list_ticket_records(root, status="needs_confirmation")
    running = list_ticket_records(root, status="running")
    submitted = list_ticket_records(root, status="submitted")
    return html.Div(
        className="qcchem-ai-workspace-page",
        children=[
            html.H1("AI Workspace"),
            html.Div([_ticket_card(item) for item in inbox], id="qcchem-ai-task-inbox"),
            html.Div([_ticket_card(item) for item in running], id="qcchem-ai-task-running"),
            html.Div([_ticket_card(item) for item in submitted], id="qcchem-ai-task-submitted"),
        ],
    )
```

```python
# /Users/a0000/QCchem/qcchem/workbench/app.py
@app.callback(
    Output("qcchem-ai-current-ticket-preview", "children"),
    Input("qcchem-ai-request-input", "value"),
)
def _preview_ticket(value: str | None):
    if not value:
        return "Draft a task ticket to continue."
    return f"Draft task preview: {value[:120]}"
```

- [ ] **Step 4: Re-run the workbench AI tests**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py -q
```

Expected: PASS, proving the page and floating assistant can read/write AI workspace state.

- [ ] **Step 5: Commit the connected workspace UI**

```bash
cd /Users/a0000/QCchem
git add \
  qcchem/workflow/ai_store.py \
  qcchem/workflow/ai_workspace.py \
  qcchem/workbench/app.py \
  qcchem/workbench/pages/ai_workspace.py \
  tests/integration/test_workbench_ai_workspace_v15.py
git commit -m "feat: connect AI workspace UI to persisted task state"
```

---

### Task 7: Document the AI workspace and verify the full stack

**Files:**
- Create: `/Users/a0000/QCchem/docs/ai_workspace.md`
- Create: `/Users/a0000/QCchem/examples/ai_workspace/provider.openai-compatible.yaml`
- Create: `/Users/a0000/QCchem/examples/ai_workspace/tickets/analysis_h2_campaign.json`
- Modify: `/Users/a0000/QCchem/README.md`
- Modify: `/Users/a0000/QCchem/docs/architecture.md`
- Modify: `/Users/a0000/QCchem/docs/roadmap.md`
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

- [ ] **Step 1: Write a documentation regression test that checks the new examples exist**

```python
from pathlib import Path


def test_ai_workspace_examples_exist() -> None:
    root = Path("/Users/a0000/QCchem")
    assert (root / "docs" / "ai_workspace.md").exists()
    assert (root / "examples" / "ai_workspace" / "provider.openai-compatible.yaml").exists()
    assert (root / "examples" / "ai_workspace" / "tickets" / "analysis_h2_campaign.json").exists()
```

- [ ] **Step 2: Run the documentation regression and confirm failure**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest /Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py -q
```

Expected: FAIL because the docs and examples do not exist yet.

- [ ] **Step 3: Write the docs and examples**

```markdown
# /Users/a0000/QCchem/docs/ai_workspace.md
# QCchem AI Workspace

## What it is

QCchem AI Workspace adds a floating research copilot and a secondary task hub page to the existing workbench.

## Core rule

Execution does not happen directly from free-form chat. QCchem drafts a task ticket first, then waits for confirmation.

## Provider setup

Use an OpenAI-compatible provider config:

```yaml
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
```
```

```yaml
# /Users/a0000/QCchem/examples/ai_workspace/provider.openai-compatible.yaml
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
  timeout_seconds: 60
  default_temperature: 0.1
  default_max_tokens: 2000
  capabilities:
    - research_qa
    - task_drafting
    - analysis
  enabled: true
```

```json
// /Users/a0000/QCchem/examples/ai_workspace/tickets/analysis_h2_campaign.json
{
  "task_id": "analysis-h2-campaign-demo",
  "task_type": "analysis",
  "title": "Summarize the H2 hardware campaign",
  "request_text": "Compare the recent H2 hardware probes and recommend the next best convergence step.",
  "plan_summary": "Read the hardware calibration suite, compare ideal/sampled/runtime evidence, and return a constrained recommendation.",
  "expected_outputs": [
    "analysis summary",
    "recommendation"
  ],
  "risk_notes": [
    "Do not overstate chemical accuracy.",
    "Respect validated/exploratory/unstable boundaries."
  ],
  "linked_artifacts": [
    "artifacts/hardware_calibration_suite_v1"
  ],
  "status": "accepted",
  "execution_target": "analysis_only_assistant"
}
```

- [ ] **Step 4: Run targeted and full verification**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest \
  /Users/a0000/QCchem/tests/unit/test_ai_workspace_domain_v15.py \
  /Users/a0000/QCchem/tests/unit/test_ai_assistant_v15.py \
  /Users/a0000/QCchem/tests/integration/test_ai_workspace_cli_v15.py \
  /Users/a0000/QCchem/tests/integration/test_workbench_ai_workspace_v15.py -q

PYTHONPATH=/Users/a0000/QCchem pytest -q
```

Expected:

- targeted AI workspace suite passes
- full QCchem suite still passes

- [ ] **Step 5: Commit docs and verification updates**

```bash
cd /Users/a0000/QCchem
git add \
  docs/ai_workspace.md \
  examples/ai_workspace/provider.openai-compatible.yaml \
  examples/ai_workspace/tickets/analysis_h2_campaign.json \
  README.md \
  docs/architecture.md \
  docs/roadmap.md \
  docs/handoff.md \
  docs/verified_scope.md \
  tests/integration/test_ai_workspace_cli_v15.py
git commit -m "docs: add AI workspace guides and examples"
```

---

## Self-Review

### Spec coverage

- Floating window as primary surface: covered by Task 5 and Task 6.
- Dedicated AI workspace page as secondary surface: covered by Task 5 and Task 6.
- OpenAI-compatible provider entry with reserved future kinds: covered by Task 1 and Task 2.
- Plan-first task ticket flow: covered by Task 2 and Task 3.
- Three task categories: covered by Task 4.
- Delivery / receive / return / history shape: covered by Task 4 and Task 6.
- Agent binding and reuse of current QCchem agent protocol: covered by Task 3 and Task 4.
- Docs/examples/boundary language: covered by Task 7.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” placeholders remain.
- Each coding step includes explicit file paths and code snippets.
- Each test step includes an exact command and expected result.

### Type consistency

- Domain types introduced in Task 1 are reused consistently in Tasks 2–6.
- `AIProviderSpec`, `AITaskTicket`, and `AIDeliveryRecord` names remain stable across tasks.
- CLI command names remain stable: `qcchem ai draft-ticket`, `qcchem ai run-ticket`.
