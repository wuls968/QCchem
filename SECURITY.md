# Security Policy

## Reporting

Report security issues privately through GitHub Security Advisories for this
repository when available. If private advisories are not enabled, open a minimal
GitHub issue that requests a secure contact path and does not include secrets,
tokens, exploit details, or private runtime metadata.

## Secrets and Runtime Credentials

Do not commit:

- OpenAI API keys or provider credentials.
- IBM Quantum or other runtime tokens.
- Private backend names, job payloads, or account identifiers that should not be
  public.
- Local `.env`, virtual environment, cache, or machine-specific configuration
  files.

QCchem CI intentionally avoids real runtime submission and does not require
hardware or AI provider secrets. Real hardware submission must remain behind
explicit user confirmation and budget controls.

## Supported Scope

The current `0.1.0a1` release line focuses on local artifact-first workflows,
guarded runtime collection, and evidence-grounded reporting. Security-sensitive
changes should preserve the boundary between local validation, runtime
provenance, and chemistry claims.
