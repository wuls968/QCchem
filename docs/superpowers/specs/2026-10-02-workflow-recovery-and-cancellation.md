# Workflow recovery and cancellation

## Goal and current state

Continue the correctness/reliability upgrade with durable recovery for custom
workflows. The current runner persists final step results but starts every run
from an empty directory. It has no execution lock, restart protocol, or cancel
mailbox. VQE continuity is a warm start for adjacent calculations, not recovery
after a process crash. Runtime collection already concerns existing provider
jobs; this change must not turn local cancellation into provider cancellation.

## Requirements

- Atomically checkpoint the normalized workflow, generated graph, committed
  results, execution budget, and current step/iteration/attempt.
- Expose `workflow status`, `workflow cancel`, and `workflow resume` in the CLI.
- Use an OS-held exclusive lock beside the output root. A crash releases the
  lock. Never infer ownership from a PID or signal an unrelated process.
- Reject concurrent runs, resumes, and overwrites of the same output root.
- Publish preparation/execution phases in the held lock, so status/cancel never
  mistakes a previous checkpoint session for a worker preparing a new session.
- Verify configuration, implementation/environment identity, completed step
  files, and detected file inputs before reusing results.
- Resume pending steps without rerunning committed completed steps. Require
  `--retry-step ID` for failed, cancelled, or uncertain interrupted steps.
- Preserve previous checkpoints and result sidecars in execution history.
  Retried steps use fresh subdirectories and retain original partial files.
- Invalidate dependency-skipped descendants when an upstream step is retried.
  Do not silently discard completed dependent results.
- Cancellation is a session-bound request, checked before/after plugin calls,
  retries, planning, and iterations. A plugin may poll `context.check_control()`.
  Cancelled/interrupted workflows are never accepted.

## Design

Add `workflow_control.py` for lock ownership, checkpoint validation, file
manifests, execution history, and the cancel mailbox. Keep graph execution in
`custom_workflow.py` and preserve the current step plugin interfaces. Add a
control callback to the execution context without changing existing callers.

The checkpoint is authoritative for recovery. Step results, generated steps,
and output manifests commit together after execution and dynamic graph
validation. A crash before this commit leaves an uncertain active step even if
some result files exist. Recovery does not guess whether its side effects
finished. Step-level recovery is intentionally distinct from restarting an
optimizer, a partially completed loop, or an external program inside a step.

File hashes detect accidental alteration; they do not authenticate an untrusted
artifact. Input discovery covers existing path strings in resolved inputs and
can be extended by plugins. Plugins remain trusted Python code. Resume requires
the same package source, plugin identities, Python/dependency versions, and
  normalized workflow. It does not provide migration across software upgrades.

Keep the execution count across sessions, including interrupted iterations.
The monotonic wall-time limit applies anew to each explicitly started execution
session; downtime is not computation time. A cancel request includes the run
and session identities, so an old request cannot stop a later resume.

## Validation

- Unit checks for checkpoint corruption, modified/missing artifacts and inputs,
  configuration/plugin mismatches, dependency invalidation, retry isolation,
  loop budget retention, cooperative cancellation, and terminal acceptance.
- Real subprocess checks for crash/restart, OS lock release, concurrent resume
  and overwrite rejection, cancellation from another process, and repeated
  resume without duplicate committed work.
- CLI error/status/exit-code checks and an actual H2 workflow recovery smoke.
- Relevant workflow/AI/Workbench tests, then the normal suite if core changes
  justify it; Ruff and diff checks. No new dependency installation is needed.

## Boundaries and open questions

No pending product choices are required for this increment. Forced termination,
provider job cancellation, migrations of legacy bundles without checkpoints,
mid-step scientific restart, and background scheduling remain outside this
contract. Document these limits in the workflow guide and show live recovery
status in Workflow Studio. Retain all temporary build and acceptance evidence;
cleanup remains a separate explicitly authorized action.
