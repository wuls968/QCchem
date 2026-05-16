# Contributing to QCchem

QCchem is developed as a Trust-First quantum chemistry workflow project. Changes
should preserve artifact provenance, explicit evidence boundaries, and local
verification before promotion.

## Development Setup

Use Python 3.10 or newer in an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui,ai,runtime]"
```

## Local Checks

Run these before opening or updating a pull request:

```bash
python -m compileall qcchem
python -m pytest
```

For release-facing changes, also run the Trust-First release audit when the
required artifacts are present:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```

## Evidence Boundaries

- Preserve `evidence_summary`, provenance, and trust-tier fields when adding
  workflow outputs.
- Treat `hardware_verified` as runtime retrieval evidence, not chemistry
  validation.
- Keep exploratory QFT, LR-ACE, TC-QSCI, and field-model claims inside their
  explicit exploratory scope unless a separate validation gate promotes them.
- Do not make publication-grade chemistry claims from local smoke tests,
  runtime sidecars, or short exploratory campaigns.

## Pull Request Expectations

- Keep changes scoped to one workflow, interface, or evidence boundary.
- Include focused tests for new public CLI commands, config fields, reports, or
  workbench behavior.
- Update README or docs when user-facing commands, artifact shapes, or trust
  semantics change.
- Never commit API keys, runtime tokens, credentials, private job metadata, or
  local environment files.
