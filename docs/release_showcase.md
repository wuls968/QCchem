# QCchem Release Showcase

This document fixes a single, repeatable showcase path for the current `Trust-First Release`.

## Reading Order

1. `Overview`
2. `Result Confidence`
3. `Benchmarks`
4. `Hardware Campaign`
5. `AI Workspace`

## What each stop answers

### 1. Overview

Use `/overview` to answer:

- What is the current `best evidence`?
- Which case is currently most worth advancing?
- What is the biggest trust gap right now?

### 2. Result Confidence

Use `/result-confidence` to answer:

- What is the primary scientific claim?
- What baseline is this claim compared against?
- What is the primary error metric?
- Why is this result `validated`, `exploratory`, `unstable`, or `hardware_verified`?

### 3. Benchmarks

Use `/benchmarks` to answer:

- How does the claim sit inside the broader benchmark suite?
- Is the best local evidence strong enough to promote?
- Which benchmark path is still unstable?

### 4. Hardware Campaign

Use `/hardware-campaign` to answer:

- Has the real runtime path been verified?
- How strong is the chemistry claim on hardware?
- Is the right action `continue`, `pause`, or `not worth additional budget`?

### 5. AI Workspace

Use `/ai-workspace` to answer:

- What analysis ticket should happen next?
- What execution is worth queueing?
- What is still pending, returned, or blocked?

## Curated artifacts

The current release-grade artifact set is:

- local validated anchor:
  - `/Users/a0000/QCchem/artifacts/h2/result.json`
- active-space / compression / correction anchor:
  - `/Users/a0000/QCchem/artifacts/lih_auto_compressed_nevpt2/result.json`
  - `/Users/a0000/QCchem/artifacts/lih_active_exact_compressed_cholesky/result.json`
- benchmark aggregate:
  - `/Users/a0000/QCchem/artifacts/benchmark_suite_v1/benchmark_result.json`
- study aggregate:
  - `/Users/a0000/QCchem/artifacts/mini_comparison_study/study_result.json`
- scan aggregate:
  - `/Users/a0000/QCchem/artifacts/h2_short_scan/scan_result.json`
- hardware aggregate:
  - `/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json`
- AI analysis seed:
  - `/Users/a0000/QCchem/examples/ai_workspace/tickets/analysis_h2_campaign.json`

## Release language

Every stop in the showcase should prefer the same language:

- `best evidence`
- `trust tier`
- `baseline strength`
- `chemical accuracy status`
- `runtime evidence status`
- `recommended next action`
- `hardware verification boundary`
