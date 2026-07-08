# QCchem AI Workspace

QCchem AI Workspace adds a floating research copilot to the Dash workbench and a dedicated task hub at `/ai-workspace`. The flow stays plan-first: free-form requests become structured tickets, and accepted tickets are then executed through the existing QCchem workflow and agent path.

Within the current `Trust-First Release`, AI Workspace is intentionally conservative: it is an `evidence-aware`, `ticket-mediated`, `artifact-grounded` research copilot.

The evidence-grounded research agent layer adds a stricter first version of the
AI research center:

- bounded artifact ingestion for run, benchmark, study, scan, hardware campaign, and runtime sidecar artifacts
- an evidence graph with separate chemistry and runtime judgments
- local trust/risk/cost gates before any workflow route is allowed
- deterministic overclaim review for validated / exploratory / unstable and hardware boundaries
- append-only AI provenance under `artifacts/ai_workspace/provenance/`

## What lives where

- Workbench preview shell: floating assistant, draft preview, provider drawer, position recovery control
- Workspace page: inbox, running, submitted, completed, and returned lanes with
  record counts, latest-record labels, and artifact-source paths
- Example provider config: `examples/ai_workspace/provider.openai-compatible.yaml`
- Example ticket: `examples/ai_workspace/tickets/analysis_h2_campaign.json`

## Provider setup

Use an OpenAI-compatible provider config like this:

```yaml
ai_provider:
  provider_name: research-openai
  provider_kind: openai_compatible
  base_url: https://api.example.com/v1
  api_key_ref: OPENAI_API_KEY
  model: gpt-5.4
```

The example file includes the same shape plus the runtime defaults QCchem expects for the workbench flow.
The Workbench provider drawer mirrors the same `base_url`, `model`, and
`api_key_ref` fields in Dash session state and renders a compact provider
profile summary. It stores the key reference name only; real API keys stay in the
runtime environment or external secret manager.

## Ticket flow

1. Draft a ticket from the workbench or CLI.
2. Review the persisted ticket in the AI workspace page.
3. Accept the ticket.
4. Run the ticket through `qcchem ai run-ticket <ticket.json>`.
5. Review the updated lane in the workspace page and the delivery record under `artifacts/ai_workspace/deliveries/`.
6. Mark the delivery accepted or returned with `qcchem ai delivery review` or `qcchem ai delivery return`.

The floating assistant preview is no longer just a request echo. When the ticket links a QCchem artifact, the preview can now surface:

- primary scientific claim
- trust tier
- runtime evidence status
- recommended action
- evidence scope
- limitation notes

New tickets may also carry:

- `evidence_context`: the normalized evidence graph consumed by the ticket
- `action_plan`: a single `ResearchActionProposal`
- `risk_assessment`: local guardrail output
- `cost_estimate`: local budget/cost boundary
- `model_provenance`: optional LLM call or fallback record
- `execution_provenance`: workflow events written after execution

That keeps the copilot aligned with the same Evidence Core language used by reports and the Research Console.

The floating assistant is intentionally persistent, but it must never trap the user. The `Reset` control and double-clicking the title grip both restore the assistant to a safe bottom-right position. This is useful when a previous browser session saved an awkward drag/resize state in local storage.

Delivery history now mirrors that same evidence-first contract. A durable
delivery should preserve the review status, linked evidence summary, evidence
scope, limitation notes, and recommended action so later agents do not have to
reinterpret raw artifacts from scratch. The Workbench delivery panel also
summarizes the delivery record count, latest delivery, review-status counts, and
the `artifacts/ai_workspace/deliveries` source path before listing individual
delivery cards. Each card includes a review action, labeled linked output paths,
workflow result/report paths when present, evidence scope, and return notes when
a handoff is sent back for revision. The Delivery History controls can filter
those handoffs by review status and delivery kind while keeping total counts,
status counts, kind counts, and the source directory visible. Returned delivery
notes are also linked back to tickets with the same `task_id`, so the returned
lane and floating preview show the revision reason without opening the delivery
JSON first. When the Workbench `Return` action is used directly, the current
risk notes are preserved as ticket-level return notes. The same review loop is
available from the CLI: `qcchem ai delivery return <delivery.json>
--return-notes "..."` marks the delivery as returned and writes the revision
reason plus linked delivery path back to the matching ticket when both records
live under the same AI workspace.

## Default AI posture

QCchem AI does not treat chat as an execution authority. Its default behavior is:

1. explain the current artifact evidence and trust boundary
2. suggest a `recommended next action`
3. create a structured ticket when the task deserves persistence
4. execute only after ticket acceptance / confirmation

That means the AI layer is designed to be a conservative evidence interpreter first, and an execution mediator second.

## Evidence inputs

When AI summarizes or drafts work, it should preferentially ground itself in:

- current page context
- selected artifact paths
- `evidence_summary`
- `trust_tier`
- baseline metadata
- runtime / calibration / hardware campaign metadata
- linked tickets and deliveries

### AI reads these fields first

In Trust-First mode, the minimum evidence tuple AI should read before offering a recommendation is:

- `primary_scientific_claim`
- `primary_baseline`
- `primary_error_metric`
- `chemical_accuracy_status`
- `runtime_evidence_status`
- `trust_tier`
- `recommended_action`

Companion boundary language should also be preserved when present:

- `baseline strength`
- `hardware verification boundary`

This is what keeps the copilot in its intended role: interpret evidence conservatively first, then propose the next ticket-worthy action.

## Useful commands

```bash
qcchem ai draft-ticket --provider-config examples/ai_workspace/provider.openai-compatible.yaml --task-type analysis --request "Compare the H2 hardware campaign" --artifact artifacts/hardware_calibration_suite_v1
qcchem ai run-ticket examples/ai_workspace/tickets/analysis_h2_campaign.json
qcchem ai summarize-evidence --artifact artifacts/hardware_calibration_suite_v1 -o artifacts/ai_workspace/evidence/hardware_campaign.json
qcchem ai review --target artifacts/hardware_calibration_suite_v1 --claim "hardware_verified proves publication-grade chemical accuracy" -o artifacts/ai_workspace/reviews/hardware_boundary
qcchem ai delivery review artifacts/ai_workspace/deliveries/delivery-example.json --status accepted
qcchem ai delivery return artifacts/ai_workspace/deliveries/delivery-example.json --return-notes "Clarify the hardware verification boundary before acceptance."
qcchem workbench serve
```

The v1 action route allows local `run_config`, `benchmark_suite`, `study`,
`scan`, `report`, `compare_artifacts`, `review_claims`, `runtime_collect`, and
`hardware_optimize_preview`. Real hardware submission is intentionally blocked
from this route; runtime collection requires an existing `runtime_submission.json`
with `job_id` plus explicit high-risk confirmation.

The Research OS action route adds local, analysis-only actions:

- `claim_check`: runs the claim compiler and writes `claim_review.json/md`.
- `capsule_validate`: validates an evidence capsule and writes
  `evidence_capsule.json/md`.
- `promotion_review`: runs the promotion gate and writes
  `promotion_review.json/md`; the risk tier is high when validated language is
  requested.
- `objective_plan`: plans a research objective without running calculations.
- `objective_status`: summarizes objective status using linked artifacts,
  evidence capsule validation, and claim compiler output.

The custom workflow route adds:

- `workflow_validate`: validates workflow YAML, references, limits, and plugin
  metadata without running chemistry.
- `workflow_run`: runs a YAML workflow through the central workflow runner and
  writes the normal workflow artifact bundle.
- `workflow_summarize`: reads an existing `workflow_result.json` and regenerates
  an AI-friendly summary/report.

Workflow deliveries keep the parsed workflow status, acceptance summary, step
counts, result JSON, and report path in the delivery record. The `/ai-workspace`
Delivery History renders those fields directly as labeled review artifacts, so
workflow review does not depend on opening the raw JSON first.

These actions keep `best evidence`, `trust tier`, `baseline strength`,
`chemical accuracy status`, `runtime evidence status`, `recommended next
action`, `hardware verification boundary`, and `exploratory boundary` visible in
the ticket delivery. They do not submit runtime jobs or read secrets.

## Notes

- The floating preview is intentionally lightweight and mirrors the current typed request, plus linked artifact evidence when available.
- If the assistant window is in the way, use `Minimize` for a compact bar or `Reset` to recover a safe docked position.
- The workspace page reads persisted ticket state from the artifact tree; it does not invent its own copy of task data.
- Execution is guarded by ticket status, not by free-form chat alone.
