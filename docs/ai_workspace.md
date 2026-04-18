# QCchem AI Workspace

QCchem AI Workspace adds a floating research copilot to the Dash workbench and a dedicated task hub at `/ai-workspace`. The flow stays plan-first: free-form requests become structured tickets, and accepted tickets are then executed through the existing QCchem workflow and agent path.

## What lives where

- Workbench preview shell: floating assistant, draft preview, provider drawer
- Workspace page: inbox, running, submitted, completed, and returned lanes
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

## Ticket flow

1. Draft a ticket from the workbench or CLI.
2. Review the persisted ticket in the AI workspace page.
3. Accept the ticket.
4. Run the ticket through `qcchem ai run-ticket <ticket.json>`.
5. Review the updated lane in the workspace page and the delivery record under `artifacts/ai_workspace/deliveries/`.

## Useful commands

```bash
qcchem ai draft-ticket --provider-config examples/ai_workspace/provider.openai-compatible.yaml --task-type analysis --request "Compare the H2 hardware campaign" --artifact artifacts/hardware_calibration_suite_v1
qcchem ai run-ticket examples/ai_workspace/tickets/analysis_h2_campaign.json
qcchem workbench serve
```

## Notes

- The floating preview is intentionally lightweight and mirrors the current typed request.
- The workspace page reads persisted ticket state from the artifact tree; it does not invent its own copy of task data.
- Execution is guarded by ticket status, not by free-form chat alone.
