# QCchem Workbench

The QCchem visual workbench is a local Dash app for exploring the repo's real run, benchmark, study, scan, and runtime artifacts.

In the current `Trust-First Release`, the workbench acts as QCchem's `Research Console`: an artifact-driven surface that prioritizes `best evidence`, `trust tier`, and `recommended next action` over raw activity feeds.

`Evidence Console v2` adds a shared workbench decision model across Overview, Runtime Monitoring, Hardware Campaign, and AI Workspace. It extracts `best_evidence`, `trust_gap`, `runtime_boundary`, and `open_tasks` from existing artifacts without changing the core `result.json` schema.

## Start

```bash
conda activate qiskit
pip install -e ".[ui]"
qcchem workbench serve
```

By default the server reads `./artifacts` from the current working directory
when that directory exists. For an installed wheel launched outside the checkout,
point it at the evidence root explicitly:

```bash
qcchem workbench serve --artifact-root /path/to/QCchem/artifacts
```

Explicit artifact roots must exist and be directories; missing paths are
rejected instead of falling back to sample data.

The canonical landing route is `/overview`. The `/` route is kept as an alias for compatibility, but the startup summary and page ordering are anchored to `/overview`.

## Page Order

1. `/overview` - Campaign Overview
2. `/structure-orbitals` - Structure and Orbitals
3. `/active-space-compression` - Active Space and Compression
4. `/mapping-resources` - Mapping, Resources, and Circuit
5. `/runtime-monitoring` - Runtime Monitoring
6. `/result-confidence` - Result Confidence Report
7. `/lr-ace-method` - LR-ACE Method
8. `/studies` - Studies
9. `/benchmarks` - Benchmarks
10. `/scans` - Scans
11. `/hardware-campaign` - Hardware Campaign
12. `/ai-workspace` - AI Workspace
13. `/workflow-studio` - Workflow Studio

## Artifact Story

The workbench is intentionally read-only. It does not create new chemistry results; it summarizes what already exists in `artifacts/` and helps you navigate toward the highest-signal evidence.

At startup, the server summary reads the repo's artifact inventory and reports:

- how many artifact roots are indexed
- how many already have report markdown
- how many carry `runtime_submission.json` sidecars
- how many generated `preview_local` result artifacts were skipped from the
  startup inventory
- a few featured evidence roots such as `h2_runtime_hardware_probe`, `h2_runtime_hardware_probe_puccd_layout`, `lih_active_runtime_hardware_probe_v2`, and `hardware_calibration_suite_v1`

That makes the workbench a navigation layer over QCchem's existing evidence, not a second source of truth.

The artifact inventory is generated from the same normalized index used by the
CLI, including run, benchmark, study, scan, hardware campaign, workflow, and
release artifact verification reports:

```bash
qcchem artifacts index artifacts
```

The default output, `artifacts/artifact_index.json`, is local generated state and
is ignored by git. Commit curated artifact payloads and release sidecars, not the
regenerated index snapshot.

Overview, Result Confidence, Benchmarks, and Hardware Campaign prefer real
indexed artifacts when they exist. The built-in sample models remain only as
empty-workspace fallbacks.

The Research OS surfaces are also read-only:

- `/overview` shows the latest Research Objective plan/status, open evidence
  gaps, Claim Compiler support level, and Promotion Gate status when the
  corresponding JSON artifacts exist.
- `/result-confidence` shows Evidence Capsule status, missing files, provenance
  status, and boundary warnings for the selected artifact.
- `/ai-workspace` shows ticket-mediated `claim_check`, `capsule_validate`,
  `promotion_review`, `objective_plan`, and `objective_status` actions and their
  delivery records.
- `/workflow-studio` shows the YAML-first custom workflow surface: built-in and
  installed plugins, derived graph, validation/export controls, and recent
  `workflow_result.json` artifacts with acceptance, graph, provenance, registry,
  and report status.

## Showcase Path

The recommended release-grade reading path is:

1. `/overview`
2. `/result-confidence`
3. `/benchmarks`
4. `/hardware-campaign`
5. `/ai-workspace`
6. `/workflow-studio`

The AI surface now includes:

- a floating ticket console that can pull `Evidence Summary` cues from linked artifacts
- evidence scope, limitation notes, and recommended action in ticket previews and delivery cards
- safe floating-window recovery through `Reset`, title-grip double click, and viewport clamping
- an AI Workspace board for inbox/running/submitted/completed/returned lanes
- a delivery history section that preserves review state and downstream outputs

This path is designed to answer, in order:

- What is the current best evidence?
- Why is a selected result trusted or bounded?
- How does it compare against benchmark evidence?
- What is the current hardware verification boundary?
- What analysis or execution task should happen next?
- Which custom workflow run produced durable artifacts, and is it accepted?

## Browser Smoke Checklist

Before a release candidate, run the local server and open the six showcase
routes in a real browser:

```bash
qcchem workbench serve --host 127.0.0.1 --port 8065
```

If the command is run outside the repository root, add
`--artifact-root /path/to/QCchem/artifacts` so the browser demo reads the release
evidence rather than an empty installed package directory.

The CI-friendly component-tree gate checks the same documented route table plus
every registered Dash page for nonblank, non-placeholder rendered content
without starting a server or browser:

```bash
qcchem workbench smoke --docs docs/workbench.md
```

When running this smoke gate outside the repository root, pass the same evidence
root used by the server:

```bash
qcchem workbench smoke --docs /path/to/QCchem/docs/workbench.md --artifact-root /path/to/QCchem/artifacts
```

The smoke gate rejects a missing explicit artifact root with exit code `2`.

Use `-o artifacts/workbench_smoke.json` when you want a machine-readable handoff.
The JSON includes a top-level `failed_checks` summary using
`route:/path:check` and `page:/path:check` ids, plus per-route and per-page
`failed_checks`, `registered_routes`, page titles, route labels, the resolved
`artifact_root`, bounded `text_excerpt` fields, and `render_error` fields for
page layout exceptions so CI logs can show whether a failure came from an
unregistered route, an active-label mismatch, rendered content drift, or a
component render failure. It also includes a compact `release_verification`
summary for the latest indexed `release_artifact_verification.json`, or
`status: missing` when that report is not present under the selected artifact
root. The same linked handoff can be generated after a CI artifact download:

```bash
qcchem release collect-evidence --artifact-dir <downloaded-artifacts> --docs docs/workbench.md
```

A missing docs file or malformed checklist is rejected with exit code `2`, not a
traceback.
When the smoke gate fails, the CLI prints the same top-level failed-check ids
before the per-route and per-page diagnostics.

Check each route directly, not only through in-app navigation:

| Route | Active route label | Route-specific text to confirm |
| --- | --- | --- |
| `/overview` | Overview | Release verification |
| `/result-confidence` | Result Confidence | Result Confidence Report |
| `/benchmarks` | Benchmarks | Benchmark credibility bands |
| `/hardware-campaign` | Hardware Campaign | Hardware Campaign |
| `/ai-workspace` | AI Workspace | AI Workspace |
| `/workflow-studio` | Workflow Studio | Workflow Studio |

Keep route paths in backticks and list each route once. The component-tree
smoke command rejects malformed or duplicate route rows instead of silently
skipping them.

For every route, confirm:

- the page loads without a blank shell
- the shell `Active route` label matches the route above
- route-specific content appears in the main page area
- the browser console has no errors after the page settles

When automating this checklist, normalize whitespace and case before comparing
visible text. Some compact labels are uppercased by CSS in the browser while the
component-tree smoke command checks the underlying source text.

### Evidence Summary first

The first reading block on the showcase path should always be the artifact's `Evidence Summary`. In practice that means Overview, Result Confidence, and the major aggregate pages should surface:

- `primary_scientific_claim`
- `primary_baseline`
- `primary_error_metric`
- `chemical_accuracy_status`
- `runtime_evidence_status`
- `trust_tier`
- `recommended_action`

The release-facing terms `baseline strength` and `hardware verification boundary` are companion interpretations layered on top of that same summary, not a separate truth source.

### Evidence Console v2 pages

- `/overview` is the best-evidence research home: chemical-accuracy gap, runtime boundary, open AI work, and next action appear before deep diagnostics.
- `/overview` also acts as the Research Objective snapshot, showing the latest
  objective status, open evidence gaps, and indexed release artifact
  verification status when those artifacts exist.
- `/runtime-monitoring` is the runtime decision cockpit: submission health, hardware-derived accuracy, simulator-vs-hardware gap, and budget/shot usage are separated before telemetry.
- `/hardware-campaign` is the budget decision surface: best retrieved evidence is shown alongside whether another controlled runtime probe is worth the budget.
- `/hardware-campaign` also surfaces `Optimization Trial` when a hardware optimization artifact is present, including selected candidate, compiled burden, budget ledger, and stop reason.
- `/ai-workspace` is the evidence-first task hub: delivery/history entries carry evidence scope, limitations, review state, and recommended action.
- `/ai-workspace` can execute local analysis-only AI tickets for claim compiler,
  evidence capsule, promotion gate, and research objective planning/status.
- `/workflow-studio` is the custom workflow hub: workflow YAML, plugin registry,
  graph, acceptance, provenance, and report paths stay visible together.

## Evidence Language

Workbench pages are expected to surface the same Evidence Core vocabulary as CLI and reports:

- `best evidence`
- `trust tier`
- `baseline strength`
- `chemical accuracy status`
- `runtime evidence status`
- `recommended next action`
- `hardware verification boundary`
- `exploratory boundary`
- `evidence capsule`
- `claim compiler`
- `promotion gate`
- `research objective`
- `workflow_result.json`
- `workflow_graph.json`
- `provenance.jsonl`

## Boundaries

- Validated: startup summary, page registry ordering, every registered page's
  nonblank/non-placeholder component tree, the `/overview` landing route, and
  the documented showcase route table through `qcchem workbench smoke`.
- Preview: live artifact picker controls. The pages now choose indexed repo artifacts by default, but the selector UI is still read-only and conservative.
- Not in scope for CI: starting a background browser server or checking browser
  console logs. The integration tests build the app and summary without launching
  a browser server; run the real browser checklist manually before release
  candidates.
