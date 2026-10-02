# QCchem Custom Workflows

Custom workflows let advanced users compose QCchem runs, Research OS reviews,
reports, and installed Python step plugins from one YAML source of truth.

## Commands

```bash
qcchem workflow template -o examples/workflows/local_workflow.yaml
qcchem workflow validate -c examples/workflows/h2_trust_first_workflow.yaml
qcchem workflow run -c examples/workflows/h2_trust_first_workflow.yaml
qcchem workflow status artifacts/workflows/h2_trust_first_workflow
qcchem workflow cancel artifacts/workflows/h2_trust_first_workflow --reason "Pause for review"
qcchem workflow resume -c examples/workflows/h2_trust_first_workflow.yaml --retry-step STEP_ID
qcchem workflow report artifacts/workflows/h2_trust_first_workflow/workflow_result.json
qcchem workflow plugins
```

`workflow run` rejects an existing non-empty `workflow.output_root` by default.
`--overwrite` starts a fresh workflow and retains the previous whole bundle in
an adjacent `NAME.backup-<id>` directory. Recovery uses `workflow resume`, which
keeps the existing root and its provenance. An active execution lock rejects
both resume and overwrite from another process.

## Recovery and cancellation

New runs atomically write `workflow_checkpoint.json` before execution and at
step, loop-iteration, and retry-attempt boundaries. The checkpoint commits each
finished step together with its generated graph and file manifests. An OS-held
lock at `.NAME.workflow.lock` beside the root prevents concurrent execution;
the lock file remains on disk, while a process crash releases actual ownership.
`workflow status ROOT` probes ownership rather than guessing from a PID.
Lock metadata distinguishes recovery validation (`preparing`) from an active
execution session. Cancellation is available after that preparation finishes.

Resume with the original YAML and the same output override (`-o ROOT`, if used).
The runner verifies the normalized workflow/source path, QCchem package source,
plugin identities, Python/scientific dependency versions, and persisted file
hashes before reusing completed work. Existing path strings in resolved inputs
and known nested built-in config/file references are recorded. Plugins can
declare additional inputs with `input_paths()`. Mutable-input plugins such as
`runtime_collect` retain both the before/after input manifests and verify the
post-operation state. Hashes detect accidental changes; they do not authenticate
untrusted artifacts. Recorded paths must not contain symlinks. Input directories
must be dedicated bundles rather than the workflow root or one of its parents.
Credential fields such as `api_key`, `access_token`, or `password` are rejected
before checkpointing; keep credentials outside workflow inputs and outputs.

Pending steps that never started can resume directly. Failed, cancelled, or
uncertain interrupted steps require one `--retry-step ID` flag each. A crash
before the atomic step commit leaves that step uncertain even when output files
exist. Review those files and any external side effects before authorizing its
retry. Retrying an upstream step requeues dependency-skipped descendants;
completed dependent results are never silently discarded.

A retried step receives a fresh `step_outputs/ID/resume-<session>` context;
original partial files remain in place. Previous checkpoints and result
sidecars are copied to `execution_history/<session>/`. Explicit plugin output
destinations retain their existing plugin/runner behavior rather than being
relocated. History and backups consume disk space and are not deleted
automatically. Repeating resume on a verified finished run performs no work.
Reused file manifests are also checked after execution, so a later step cannot
silently alter cached evidence and still produce an accepted recovered run.
The executed-iteration count is retained across sessions. The cooperative
`max_wall_time_seconds` limit starts anew for each explicit resume session.

`workflow cancel ROOT` writes a request bound to the current run/session. Its
`cancel_requested` response means the request was written, not that the worker
has stopped. `workflow status` reports `cancel_requested` while the owner waits
at a plugin call; it reports `cancelled` only after the owner stops. Plugins may
poll `context.check_control()` within long operations. The runner also checks
before/after validation, execution, retries, planning, and loop iterations.
Non-cooperative calls finish before cancellation is observed. Cancellation
never sends process signals or cancels an IBM/provider job. Existing runtime
submission confirmation gates still apply to any explicitly retried step.
A request racing final completion may observe a completed run; query status for
the final outcome.

Cancelled/interrupted runs are unaccepted. CLI run/resume exit codes are `0`
for completion, `2` for rejection/failure, and `130` for cancellation/interruption.
Legacy bundles without checkpoints require a new run. Generic recovery is at whole-step
granularity: it does not resume a partial loop, trajectory, or
external program inside a step, and does not migrate across software changes.

Built-in `run_config` and `scan` steps now poll control at local VQE evaluation
and scan-point boundaries. With the default artifact directory, an explicitly
approved retry automatically reads the previous inner checkpoint and writes its
new bundle in the retry context. VQE replays recorded objective values to rebuild
SciPy progress, checking each requested parameter vector before new computation.
Completed scan points and their initial-point predictor history are reused.
See [Inner computation recovery](reliability_upgrade.md#inner-computation-recovery)
for supported backends, standalone commands, and limitations. Loop retries and
explicit output destinations retain the whole-step behavior described above.

Workbench exposes the same protocol at `/workflow-studio`. The visual graph and
inspector derive from YAML; the YAML file remains the version-controlled source
of truth. Run cards poll read-only checkpoint/lock status every two seconds,
including in-progress runs that have not written `workflow_result.json` yet.
The checkpoint chooser reads the configured Workbench artifact root, including
custom workflow directories. Local browsers can request cancellation and review
the exact retry/pending steps before confirming background recovery. Reviews are
bound to a checkpoint and known input files and expire after ten minutes. See
[Workbench workflow controls](workbench.md#workflow-controls) for the UI flow,
local request boundary, and worker log/receipt location.

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
    def input_paths(self, inputs, context) -> list[str | Path]: ...
```

`plan_next()` and `input_paths()` are optional. Set `mutates_inputs = True` only
for plugins that deliberately update their declared input files, so recovery
verifies their post-operation state. When used, generated steps are not executed directly
by the plugin. The central workflow runner validates the generated step kind,
dependencies, limits, and artifact root before adding it to the run graph.
When a workflow references an unavailable kind, validation reports the available
plugin kinds and points to `qcchem workflow plugins` for installed-plugin
metadata.

## Artifacts

A workflow run writes:

- `workflow_result.json`
- `workflow_report.md`
- `workflow_graph.json`
- `step_outputs/<step_id>/...`
- `provenance.jsonl`
- `registry.json`
- `workflow_checkpoint.json`
- `workflow_control/cancel-<session>.json` when cancellation is requested
- `execution_history/<session>/...` after recovery

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
