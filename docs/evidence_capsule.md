# QCchem Evidence Capsule

An Evidence Capsule is the smallest reviewable artifact package that can support
a Trust-First decision. It checks the artifact root, not only `result.json`.

## Command

```bash
qcchem artifacts capsule artifacts/h2 -o artifacts/capsule_smoke/h2
qcchem artifacts capsule artifacts --recursive -o artifacts/capsules
```

The command writes:

- `evidence_capsule.json`
- `evidence_capsule.md`

## Checks

For run artifacts, the capsule expects:

- `result.json`
- `report.md`
- `resolved_config.yaml`
- `run.log`

It also checks optional sidecars:

- `exact_result.json`
- `quantum_evidence.json`
- `runtime_submission.json`
- `calibration.json`
- `qcschema.json`
- `result.h5`

The result payload is reviewed for `schema_version`, `evidence_summary`,
`problem`, `energy`, `benchmark`, `mapping`, `backend`, `provenance`, and
`artifacts`. The `evidence_summary` should include result identity, primary
claim, primary baseline, primary error metric, `chemical accuracy status`,
`runtime evidence status`, `trust tier`, and `recommended next action`.

## Status

- `complete`: required files and Trust-First evidence fields are present.
- `partial`: files exist but evidence, provenance, or boundary fields are weak.
- `invalid`: no supported result payload or required files are missing.

Hardware verification boundary: `hardware_verified` records runtime retrieval
evidence only. It does not imply publication-grade chemistry validation.

Exploratory boundary: QFT, LR-ACE, TC-QSCI, and other exploratory artifacts need
a promotion gate before candidate or validated language.
