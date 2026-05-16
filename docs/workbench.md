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

The canonical landing route is `/overview`. The `/` route is kept as an alias for compatibility, but the startup summary and page ordering are anchored to `/overview`.

## Page Order

1. `/overview` - Campaign Overview
2. `/structure-orbitals` - Structure and Orbitals
3. `/active-space-compression` - Active Space and Compression
4. `/mapping-resources` - Mapping, Resources, and Circuit
5. `/runtime-monitoring` - Runtime Monitoring
6. `/result-confidence` - Result Confidence Report
7. `/studies` - Studies
8. `/benchmarks` - Benchmarks
9. `/scans` - Scans
10. `/hardware-campaign` - Hardware Campaign
11. `/ai-workspace` - AI Workspace

## Artifact Story

The workbench is intentionally read-only. It does not create new chemistry results; it summarizes what already exists in `artifacts/` and helps you navigate toward the highest-signal evidence.

At startup, the server summary reads the repo's artifact inventory and reports:

- how many artifact roots are indexed
- how many already have report markdown
- how many carry `runtime_submission.json` sidecars
- a few featured evidence roots such as `h2_runtime_hardware_probe`, `h2_runtime_hardware_probe_puccd_layout`, `lih_active_runtime_hardware_probe_v2`, and `hardware_calibration_suite_v1`

That makes the workbench a navigation layer over QCchem's existing evidence, not a second source of truth.

The artifact inventory is now generated from the same normalized index used by
the CLI:

```bash
qcchem artifacts index artifacts
```

Overview, Result Confidence, Benchmarks, and Hardware Campaign prefer real
indexed artifacts when they exist. The built-in sample models remain only as
empty-workspace fallbacks.

## Showcase Path

The recommended release-grade reading path is:

1. `/overview`
2. `/result-confidence`
3. `/benchmarks`
4. `/hardware-campaign`
5. `/ai-workspace`

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

## Browser Smoke Checklist

Before a release candidate, run the local server and open the five showcase
routes in a real browser:

```bash
qcchem workbench serve --host 127.0.0.1 --port 8065
```

Check each route directly, not only through in-app navigation:

| Route | Active route label | Route-specific text to confirm |
| --- | --- | --- |
| `/overview` | Overview | Current defended claim |
| `/result-confidence` | Result Confidence | Result Confidence Report |
| `/benchmarks` | Benchmarks | Benchmark credibility bands |
| `/hardware-campaign` | Hardware Campaign | Hardware Campaign |
| `/ai-workspace` | AI Workspace | AI Workspace |

For every route, confirm:

- the page loads without a blank shell
- the shell `Active route` label matches the route above
- route-specific content appears in the main page area
- the browser console has no errors after the page settles

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
- `/runtime-monitoring` is the runtime decision cockpit: submission health, hardware-derived accuracy, simulator-vs-hardware gap, and budget/shot usage are separated before telemetry.
- `/hardware-campaign` is the budget decision surface: best retrieved evidence is shown alongside whether another controlled runtime probe is worth the budget.
- `/hardware-campaign` also surfaces `Optimization Trial` when a hardware optimization artifact is present, including selected candidate, compiled burden, budget ledger, and stop reason.
- `/ai-workspace` is the evidence-first task hub: delivery/history entries carry evidence scope, limitations, review state, and recommended action.

## Evidence Language

Workbench pages are expected to surface the same Evidence Core vocabulary as CLI and reports:

- `best evidence`
- `trust tier`
- `baseline strength`
- `chemical accuracy status`
- `runtime evidence status`
- `recommended next action`
- `hardware verification boundary`

## Boundaries

- Validated: startup summary, page registry ordering, and the `/overview` landing route.
- Preview: live artifact picker controls. The pages now choose indexed repo artifacts by default, but the selector UI is still read-only and conservative.
- Not in scope: starting a background web server inside tests. The integration tests build the app and summary without launching a browser server.
