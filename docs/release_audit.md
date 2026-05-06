# QCchem Release Audit

`qcchem release audit` is the local Trust-First Release gate for QCchem. It
checks that curated artifacts, docs, configs, and exploratory research assets
still use the same Evidence Core language before the `0.1.0a1` alpha release.

The audit is deliberately conservative. It reads local files and writes audit
outputs. It does not run chemistry workflows, submit runtime jobs, call IBM
Runtime, mutate curated artifacts, or rewrite source files.

Short rule: no runtime submission happens during release audit.

## Command

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```

Equivalent module form:

```bash
python -m qcchem.cli.main release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```

Use `--repo-root` when auditing a copied fixture or temporary repository:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o /tmp/qcchem-release-audit \
  --repo-root /path/to/QCchem
```

## Outputs

The command writes:

- `release_readiness.json`
- `release_readiness.md`

Generated readiness outputs live under `artifacts/release_audit/` by default and
are ignored by git. They are local evidence for the current checkout, not source
files for the release itself.

## Exit Codes

- `0`: all required checks passed.
- `2`: at least one required check failed.

On failure, read `release_readiness.md` first. It is the human review surface and
points at the failed check names.

## Manifest Shape

The default manifest is `configs/release/trust_first_audit.yaml`:

```yaml
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts:
    - name: h2_local_validated_anchor
      path: artifacts/h2/result.json
      required: true
  exploratory_assets:
    - name: qft_sparse_projected_engine
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      required: true
  required_docs:
    - path: README.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
      required: true
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
```

Supported exploratory asset kinds:

- `qft`
- `lr_ace`
- `tc_qsci`

## Checks

The Trust-First profile verifies:

- `pyproject.toml` version matches the manifest release version.
- Required curated artifacts exist.
- Curated artifacts expose the required `evidence_summary` fields, or the audit
  can derive a read-only release summary from legacy artifact payloads:
  - `trust_tier`
  - `primary_baseline`
  - `primary_error_metric`
  - `recommended_action`
- Runtime preview or disabled submissions are not mislabeled as
  `hardware_verified`.
- QFT, LR-ACE, and TC-QSCI assets remain inside the exploratory boundary.
- QFT language remains finite-cutoff lattice-QED / sparse projected
  physical-sector evidence, not continuum chemistry accuracy.
- Required docs contain the release language needed for the Trust-First Release.

## JSON Contract

`release_readiness.json` contains:

- `schema_version`
- `profile`
- `release_version`
- `status`
- `required_pass_count`
- `required_fail_count`
- `checks`
- `evidence_matrix`
- `recommended_action`

The JSON shape is intended for automation. The Markdown companion is intended
for release review and handoff.

## Operating Rules

- Do not add real runtime submission to release audit.
- Do not let release audit regenerate curated artifacts.
- Do not promote QFT, LR-ACE, or TC-QSCI from exploratory to validated through a
  documentation-only change.
- Keep release terms consistent across README, verified scope, release showcase,
  and reports.
- If full pytest runs before the audit, confirm it did not rewrite tracked
  artifacts:

```bash
git diff --name-only -- artifacts/lih_active_vqe
```

The command should print nothing.
