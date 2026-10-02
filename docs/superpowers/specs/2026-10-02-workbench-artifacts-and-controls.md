# Workbench aggregate artifacts and workflow controls

## Goal and requirements

- Read real scan and study aggregates from the configured Workbench artifact root; retain an explicit demo choice for empty workspaces.
- Select and refresh artifacts without restarting Dash. Show source paths, incomplete scan checkpoints, missing values, and the lowest sampled energy without overstating scientific conclusions.
- Workflow Studio discovers current checkpoints under that same root, including nonstandard output layouts, and offers cooperative cancellation and reviewed resume.
- Resume lists the exact retry steps and reusable completed steps before confirmation. Existing configuration, implementation, input/output integrity, execution locks, and retry requirements remain authoritative.

## Design

- A shared, read-only aggregate catalog uses root-relative selection IDs, rejects escaping symlinks and history/preview copies, and normalizes missing finite numerical values to `None`.
- Workflow resume validation is factored into a read-only engine API used by both previews and execution. A review is bound to the checkpoint/session and exact retry IDs, expires, and can be consumed once.
- A local Workbench controller starts an owned Python subprocess with the same interpreter/package, stores request/log/receipt files outside workflow output directories, and reports dispatch failures. Dash callbacks remain responsive.
- Mutating callbacks require a loopback client, a loopback Host, and a same-origin request. Paths come only from the server's checkpoint catalog. Cancellation is bound to the selected session and never sends process signals or provider cancellation requests.
- Installed plugins and hardware/runtime workflows retain their existing engine confirmation gates; the review exposes step kinds and source configuration rather than hiding possible effects.

## Validation

- Artifact selection, configured roots, malformed and incomplete JSON/checkpoints, history exclusion, symlink escape, missing energies/errors, and demo/empty behavior.
- Resume preview is read-only and shares execution preflight; stale/changed reviews, invalid retry IDs, concurrent dispatch, corrupt inputs/outputs, and local request boundary rejection.
- Real workflow cancellation and a background resume through Dash callbacks, plus browser selection, review/confirm, polling and responsive navigation.
- Related tests first, then the normal suite, lint and diff review. Retain all scientific artifacts, checkpoints, logs and previous delivery wheels.

## Constraints

No dependency installations, commits, pushes, or cleanup. Cancellation latency depends on safe polling boundaries; provider jobs are not cancelled. Recovery still requires the original matching software. Cross-platform/GPU/provider acceptance remains separate.
