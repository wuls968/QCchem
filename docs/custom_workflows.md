# QCchem Custom Workflows

Custom workflows let advanced users compose QCchem runs, Research OS reviews,
reports, and installed Python step plugins from one YAML source of truth.

## Commands

```bash
qcchem workflow template -o examples/workflows/local_workflow.yaml
qcchem workflow validate -c examples/workflows/h2_trust_first_workflow.yaml
qcchem workflow run -c examples/workflows/h2_trust_first_workflow.yaml
qcchem workflow report artifacts/workflows/h2_trust_first_workflow/workflow_result.json
qcchem workflow plugins
```

`workflow run` rejects an existing non-empty `workflow.output_root` by default.
Add `--overwrite` only when you intend to replace the whole workflow artifact
bundle, including `step_outputs/` and `provenance.jsonl`.

Workbench exposes the same protocol at `/workflow-studio`. The visual graph and
inspector derive from YAML; the YAML file remains the version-controlled source
of truth.

`workflow template` writes starter paths relative to the template file location.
For example, a template written under `examples/workflows/` will point back to
`../../configs/h2_exact.yaml` and `../../artifacts/workflows/...`, matching the
same path resolution used by the runner.

## YAML Shape

```yaml
workflow:
  version: "1"
  name: h2_trust_first_workflow
  output_root: artifacts/workflows/h2_trust_first_workflow
  limits:
    max_steps: 16
    max_iterations: 4
  parameters:
    claim: The H2 local run is validated against an exact baseline.
  steps:
    - id: run_h2
      kind: run_config
      inputs:
        config: configs/h2_exact.yaml
    - id: capsule_h2
      kind: capsule_validate
      inputs:
        artifact_root: ${steps.run_h2.outputs.artifact_root}
  acceptance:
    required_steps: [run_h2, capsule_h2]
```

Step inputs may reference `${parameters.<name>}` or
`${steps.<id>.outputs.<key>}`. References to step outputs create implicit
dependencies, so the graph remains auditable even when `needs` is omitted.

## Built-In Steps

The v1 registry includes:

- `run_config`
- `benchmark_suite`
- `study`
- `scan`
- `report`
- `compare_artifacts`
- `claim_check`
- `capsule_validate`
- `promotion_review`
- `objective_plan`
- `objective_status`
- `runtime_collect`
- `hardware_optimize_preview`

`runtime_collect` only collects an existing sidecar. Real runtime or hardware
submission remains governed by existing QCchem confirmation gates.

## Plugin Contract

Installable plugins register classes through the `qcchem.workflow_steps` entry
point group. A plugin implements:

```python
class MyStep(WorkflowStepPlugin):
    def describe(self) -> WorkflowPluginDescription: ...
    def validate(self, inputs, context) -> list[str]: ...
    def run(self, inputs, context) -> dict[str, object]: ...
    def plan_next(self, result, context) -> list[dict[str, object]]: ...
```

`plan_next()` is optional. When used, generated steps are not executed directly
by the plugin. The central workflow runner validates the generated step kind,
dependencies, limits, and artifact root before adding it to the run graph.

## Artifacts

A workflow run writes:

- `workflow_result.json`
- `workflow_report.md`
- `workflow_graph.json`
- `step_outputs/<step_id>/...`
- `provenance.jsonl`
- `registry.json`

These files are the shared contract for CLI, AI Workspace, Workbench, and later
release-audit integration.

## Release And Index Coverage

`qcchem artifacts index artifacts` discovers `workflow_result.json` artifacts
alongside run, benchmark, study, scan, campaign, and hardware-calibration
outputs. Workflow index rows include status, acceptance, step counts, report,
graph, provenance, and registry flags.

`qcchem release audit` checks this workflow surface without running chemistry or
installing external plugins. The audit verifies that built-in workflow examples
validate, built-in step plugins are registered, plugin examples exist, and any
persisted workflow artifacts under `artifacts/` keep their report, graph,
`provenance.jsonl`, and `registry.json` files together.
