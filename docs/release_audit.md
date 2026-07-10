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

After an audit has written outputs, summarize the existing handoff without
rerunning the audit:

```bash
qcchem release status \
  --audit-dir artifacts/release_audit \
  --strict \
  -o artifacts/release_audit/release_status.json
```

Use `--repo-root` when auditing a copied fixture or temporary repository:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o /tmp/qcchem-release-audit \
  --repo-root /path/to/QCchem
```

If `--repo-root` is provided, relative `-c` paths are resolved against that repo
root rather than the current shell directory. When `-o` is omitted in this mode,
readiness outputs are written under `<repo-root>/artifacts/release_audit/`. This
keeps copied-repository and temporary-fixture audits usable from outside the
repository checkout and avoids accidental shadow manifests in the caller's
current directory.

To create or refresh a manifest-bound release acceptance sidecar, use the
explicit writer command rather than editing `acceptance_summary.json` by hand:

```bash
qcchem release acceptance-status \
  -c configs/release/trust_first_audit.yaml \
  --strict \
  --repair-plan
```

```bash
qcchem release accept-artifact \
  -c configs/release/trust_first_audit.yaml \
  --name h2_local_validated_anchor \
  --dry-run
```

```bash
qcchem release accept-artifact \
  -c configs/release/trust_first_audit.yaml \
  --name h2_local_validated_anchor \
  --overwrite
```

`acceptance-status` is read-only and reports missing, stale, unreadable, or
blocked sidecars; with `--strict` it exits with code `2` when any manifest
sidecar needs attention. For every non-fresh sidecar, the CLI prints a bounded
`Sidecar issue:` line with the sidecar path plus the first error or contract
failure reason when one is available. Add `--repair-plan` to print copyable
preview and refresh commands for each non-fresh sidecar; the JSON status output
also includes `schema_features`, `repair_plan`, and `repair_plan_count`. The CLI
validates that status JSON contract and semantic invariants before writing `-o`,
so CI will fail rather than upload a partial, mistyped, or internally
inconsistent sidecar-freshness report.
`accept-artifact --dry-run` builds the same manifest-bound payload and reports
the current sidecar status without writing. `accept-artifact` without
`--dry-run` writes the sibling
`acceptance_summary.json` for one manifest entry, binds it to the exact
release-audit check id, records the audited artifact hash, and reuses existing
`release_boundaries` when overwriting unless new `--boundary` notes are
supplied. It does not run chemistry or promote the artifact beyond its
`evidence_summary` trust tier. Without `--overwrite`, it refuses to replace an
existing sidecar.

## Outputs

The command writes:

- `release_readiness.json`
- `release_readiness.md`
- `release_handoff.json`
- `release_handoff.md`
- `release_diagnostics_manifest.json` in CI, written before diagnostic upload
- `release_evidence/release_evidence_summary.json` in CI, written before diagnostic upload
- `release_evidence/release_evidence_handoff.md` in CI, written before diagnostic upload

Generated readiness outputs live under `artifacts/release_audit/` by default and
are ignored by git. They are local evidence for the current checkout, not source
files for the release itself.
`release_handoff.json` and `release_handoff.md` are the compact entrypoint for
handoff: they point back to `release_readiness.*`, summarize the release status,
and, inside GitHub Actions, record the current run URL plus the diagnostic
artifact name and diagnostics manifest path. CI uploads those handoff files,
readiness files, Workbench smoke JSON, compact `release_status.json` summaries,
the `release_diagnostics_manifest.json` digest/size summary, release sidecar
freshness JSON, and the CI-side `release_evidence_summary.json` /
`release_evidence_handoff.md` plus the single-run `release_history_summary.json`
and `release_history_summary.md` as `qcchem-release-diagnostics-*` artifacts so
failed runs keep their handoff bundle without tracking generated outputs in git.
CI refreshes `artifacts/workbench_smoke.json` after writing that release history
handoff, so the uploaded smoke JSON includes its compact top-level
`release_history` summary instead of the pre-history `missing` shape.
The CLI prints both `Report: <...>/release_readiness.md` and
`Handoff: <...>/release_handoff.md`. In GitHub Actions it also prints the exact
`Diagnostic artifact:` name and the `Artifact listing:` API URL recorded in
`release_handoff.json`, plus `Diagnostics manifest:` with the expected manifest
path.
`qcchem release status` reads the existing `release_readiness.json` and
`release_handoff.json` files and prints the current status, first required
failure or warning, sidecar status, handoff path, and diagnostic artifact
pointer. With `--strict`, it exits with code `2` unless the summarized audit
status is `passed`; missing or unreadable audit outputs always exit with
code `2`. Status also fails with `schema_mismatch` when
`release_readiness.json` or `release_handoff.json` uses an unexpected
`schema_version`, so old or incompatible handoff bundles are not accepted as
current evidence. It fails with `contract_mismatch` when a current-schema bundle
is missing required status, count, sidecar, diagnostic-artifact, or diagnostics
manifest fields, when the declared diagnostics manifest schema drifts, or when
`release_handoff.json` no longer agrees with `release_readiness.json` on status,
action, counts, provenance, or sidecar state. The same shared release-status
validator also checks derived counts such as failed checks, warnings, and
sidecar repair-plan length, so automation does not silently consume partial or
internally inconsistent handoff JSON. CI runs that validator against both
source-tree and installed-wheel release bundles before writing the diagnostics
manifest and uploading diagnostics. When `-o` is supplied, it writes a compact
`qcchem.release_status.v0.1-alpha` JSON summary for automation.

Inside CI, write the pre-upload reviewer handoff after release audit, release
status, Workbench smoke, and acceptance-status have produced their JSON:

```bash
qcchem release evidence-handoff \
  --audit-dir artifacts/release_audit \
  --workbench-smoke artifacts/workbench_smoke.json \
  --acceptance-status /tmp/qcchem-release-acceptance-status.json \
  --output-dir artifacts/release_evidence
```

That command uses `collection_mode: ci_diagnostics_handoff`. It summarizes the
local CI diagnostics and marks downloaded artifact digest verification as
`not_run`, because SHA-256 verification only becomes meaningful after the
uploaded artifact has been downloaded.

After downloading CI release diagnostics, collect the offline release evidence
handoff:

```bash
qcchem release collect-evidence \
  --artifact-dir /tmp/qcchem-ci-artifacts \
  --docs docs/workbench.md
```

This command writes `release_artifact_verification.json`,
`release_matrix_summary.json`, `workbench_smoke.json`,
`release_evidence_summary.json`, and the reviewer-facing
`release_evidence_handoff.md` under the downloaded artifact directory. The
verifier recursively checks downloaded
`release_status.json`, `release_diagnostics_manifest.json`, and
`qcchem-release-acceptance-status.json` files. It revalidates the release status
contracts, confirms sidecar freshness, checks manifest counts, and recomputes
uploaded file sizes and SHA-256 digests. The Workbench smoke pass then records
the same verifier status and matrix counts in its route handoff. The
collector also preserves the downloaded CI smoke report's compact
`ai_workspace_delivery` object in `release_evidence_summary.json`. It only
reads `workbench_smoke.json` paths listed by a diagnostics manifest after size
and SHA-256 verification. Multiple matrix copies must agree; otherwise the AI
review context is marked `source_status: divergent` and `status: not_available`.
The post-download smoke generated under the evidence output root remains the
route/page verification source and does not replace the frozen CI review
context. The copied object records delivery and review counts, the latest
`delivery_reviewed` event, the append-only provenance log path, verified smoke
paths/count, and `release_gate: informational_only`; AI delivery review state
therefore remains visible to reviewers without changing release pass/fail
status. The
`release_matrix_summary.json` file is a compact baseline of the current
`qcchem-release-diagnostics-*` matrix artifacts. To compare a later run against
that baseline, pass it back to collection:

```bash
qcchem release collect-evidence \
  --artifact-dir /tmp/qcchem-ci-artifacts \
  --docs docs/workbench.md \
  --baseline-summary /tmp/previous-release/release_matrix_summary.json
```

If retained evidence is organized as one directory per CI run, point collection
at the history root instead of naming a file or manually choosing an output
directory:

```bash
qcchem release collect-evidence \
  --artifact-dir /tmp/qcchem-ci-artifacts \
  --docs docs/workbench.md \
  --history-root /tmp/qcchem-release-history \
  --history-label 28800298969
```

The collector writes into `<history-root>/<history-label>`, refuses to overwrite
a non-empty retained run directory, defaults the automatic baseline search root
to the same history root, excludes the current output directory, chooses the
newest prior `release_matrix_summary.json` by file modification time, and
records the history path plus baseline selection details in the JSON summary and
Markdown handoff. Omit `--history-label` to use a UTC timestamp. Use
`--baseline-search-root` when you already chose `--output-dir` manually. An
explicit `--baseline-summary` takes precedence over automatic search.

To download a GitHub Actions run and retain the post-CI evidence in one step,
use:

```bash
qcchem release fetch-ci-evidence \
  --run-id 28834488613 \
  --repo wuls968/QCchem \
  --history-root /tmp/qcchem-release-history
```

This wrapper calls `gh run download <run-id> --dir <download-dir>`, then runs
the same retained `collect-evidence` flow with `--history-label` defaulting to
the run id. The `gh` command is invoked with explicit argv arguments, not a
shell string. Retained summaries and handoffs preserve the release-history
handoff verifier count and per-artifact history status. If `--download-dir` is
omitted, a unique `/tmp` directory is created and left on disk for provenance
review; if supplied, it must be empty.

To review the retained history without downloading or rewriting any run
directory, summarize the history root:

```bash
qcchem release history summarize \
  --history-root /tmp/qcchem-release-history \
  -o /tmp/qcchem-release-history-summary.json \
  --strict
```

The summary JSON uses `qcchem.release_history_summary.v0.1-alpha` and lists one
direct child directory per retained run. Each run records the release evidence
status, selected baseline, matrix delta status/counts, release artifact
verifier status, release-history handoff count, Workbench smoke status, frozen
AI delivery review status/source status/review-event count/latest review
metadata/provenance-log path, and first failure. Missing, unreadable, or
non-object
`release_evidence_summary.json` files are reported as incomplete runs instead
of crashing the review. Missing or malformed AI review context is recorded as
`not_available` and does not affect history pass/fail status. `--strict` returns exit code `2` unless
the retained history summary is `passed`.

Export the same retained-history review as Markdown when handing it to a
reviewer:

```bash
qcchem release history export-markdown \
  --history-summary /tmp/qcchem-release-history-summary.json \
  -o /tmp/qcchem-release-history-summary.md \
  --strict
```

The Markdown export can also read `--history-root` directly. It lists top-level
run counts, status-count summaries including AI review/source-status maps, each
retained run, selected baseline, matrix-delta counts, verifier status, Workbench
smoke status, review provenance, and first failure. It writes only the requested Markdown path and does not mutate retained run
directories.

The Markdown
handoff summarizes the generated paths, verifier counts, per-matrix diagnostic
artifact status, digest/file counts, Workbench route/page status, first failure,
matrix artifact delta, AI delivery review provenance, and whether a real browser
checklist is still required. Its `AI Delivery Review Provenance` section shows
the review-event count, latest decision metadata, and provenance path, and
labels the context `informational_only` rather than treating an empty delivery
queue as a release failure.
Malformed, unreadable, missing, or divergent downloaded AI review context is
reported as `not_available` with its source status; it is never added to the
release failure list.
Fields outside the active collection mode are rendered as explicit
`not_applicable`, `not_available`, `not_provided`, or `none` values rather than
placeholder `None` text.
The command exits with code `2` if any expected file is missing, stale,
inconsistent, tampered with, or if the Workbench route smoke fails.
On failure, the top block of `release_evidence_handoff.md` includes
`recommended_action: inspect_release_evidence_failures` and the first failure
reason/path before the detailed verifier and Workbench sections.
Use `qcchem release verify-artifacts --artifact-dir /tmp/qcchem-ci-artifacts`
when you only need the lower-level artifact-integrity check.
The verifier also checks that each downloaded diagnostics artifact contains a
readable `release_history_summary.json`, its `release_history_summary.md`
handoff, and the copied `release_history/current/release_evidence_summary.json`
with the expected schemas and passed status.
It cross-checks the summary's `current` run against that copied evidence and,
when the summary declares AI review aggregate maps, recomputes those maps and
compares the normalized current AI snapshot. An unavailable AI snapshot remains
informational; a declared cross-artifact mismatch fails verification. Retained
summaries from before the additive AI projection remain readable.
When the output is named `release_artifact_verification.json` under an artifact
root, `qcchem artifacts index` records it as
`release_artifact_verification`, and the Workbench startup inventory reports the
count plus a featured verification report path. The Workbench Overview page also
surfaces the latest indexed release verification status, failure count, and
matrix artifact counts alongside the Research OS evidence snapshot. Workbench
smoke JSON records the same compact release-verification summary so the
component-tree route evidence and release artifact verification evidence can be
reviewed from one generated handoff file.
When `release_matrix_summary.json` is retained under that artifact root, the
index records it as `release_matrix_summary`, Workbench startup reports its
count and featured path, and Overview shows the baseline matrix count and failed
count separately from the reviewer-facing handoff delta.
When a retained-history overview is archived as `release_history_summary.json`
under the artifact root, the index records it as `release_history_summary`,
Workbench startup reports its count and featured path, and Overview shows the
retained run counts plus matrix-delta status counts separately from the per-run
handoff files.
When the reviewer-facing retained-history Markdown is kept as
`release_history_summary.md` or `release_history_handoff.md` next to that JSON,
the index records it as `release_history_handoff`, Workbench startup reports its
count and featured path, and Overview shows the Markdown path while reading
status/count fields from the sibling `release_history_summary.json`.
When `release_evidence_handoff.md` is kept next to
`release_evidence_summary.json`, the artifact index classifies it as
`release_evidence_handoff`, and Workbench Overview surfaces its status,
recommended action, first failure, matrix artifact counts, matrix delta status,
Markdown path, and frozen AI delivery review provenance. When that frozen
context is unavailable, Overview falls back to the current local AI Workspace
delivery/provenance summary.

`release_readiness.json` includes a top-level `release_acceptance_sidecars`
status report. When any manifest-bound sidecar is missing, stale, unreadable, or
blocked, `release_readiness.md` adds a `Release Sidecar Repair Plan` section
with the same preview and refresh commands printed by
`qcchem release acceptance-status --repair-plan`. The `release audit` CLI also
prints the first repair-plan item directly to stdout so CI logs include one
copyable next action without opening the generated Markdown report.

Curated and exploratory artifact payloads must parse as JSON objects. If a
configured artifact exists but is unreadable or not a JSON object, the audit
records a failed `:readable` check and still writes `release_readiness.json` and
`release_readiness.md` for handoff.

Exploratory asset configs must parse as YAML mappings before they can be
classified as QFT, LR-ACE, or TC-QSCI. Unreadable exploratory config YAML is
reported as `classified=unreadable` in the config check instead of aborting the
audit.

Required docs must be readable UTF-8 text. If a configured doc path exists but
cannot be read, for example because it points at a directory, the audit records a
failed `doc:<path>:readable` check and still writes readiness outputs.

Curated release artifacts may also carry an `acceptance_summary.json` sidecar in
the same artifact directory. That sidecar records release-boundary acceptance for
the artifact as-is; it must not promote an exploratory or hardware-plumbing
artifact beyond the trust tier declared in `evidence_summary`. For release audit
purposes, acceptance requires a strict JSON `accepted: true` value and an empty
`blocking_failures` list. Sidecar `warnings` become release-audit warnings and
are governed by the configured `warning_policy`. The sidecar must parse as a
JSON object; unreadable or non-object sidecars are reported as release-audit
failures for required artifacts. When both a result payload and a sibling
`acceptance_summary.json` provide acceptance summaries, the release audit and
artifact index treat the sibling sidecar as the release-evidence source.

Sidecars using `schema_version: qcchem.release_artifact_acceptance.v0.1-alpha`
must also bind themselves to the exact release-audit check that consumes them:

- `artifact_path` must resolve to the artifact being audited.
- `artifact_path` must be repository-relative; absolute paths, `~`, and `..`
  components are rejected even if they resolve to the same artifact on the
  current machine.
- `artifact_sha256` must match the audited artifact file bytes, so a sidecar
  becomes stale when the artifact is regenerated without refreshing acceptance.
- `release_audit_check_id` must match the check id, for example
  `curated_artifact:h2_local_validated_anchor:acceptance_summary`.
- `trust_tier` must match the artifact's release-readable evidence summary.
- `runtime_evidence_status` must match the artifact's release-readable runtime
  evidence status, including derived legacy summaries.
- `blocking_failures` and `warnings` must be JSON arrays, even when empty.
- `recommended_action` must be a non-empty string for release handoff.
- `artifact_name`, `acceptance_scope`, and `release_boundaries` should be
  present so manifest-bound sidecars provide a uniform human handoff contract.

Older benchmark acceptance sidecars remain compatible only when they declare
`schema_version: qcchem.benchmark_acceptance.v0.1-alpha`; they do not provide
this release-audit binding contract, so they cannot satisfy `required` or
`acceptance_required` manifest entries. Missing or unknown acceptance schemas
fail the release audit for required artifacts instead of being treated as
compatible.

Acceptance sidecars listed by the release manifest are release evidence, not
generated scratch files. Generated readiness outputs such as
`artifacts/release_audit/release_readiness.json` and workflow run bundles under
`artifacts/workflows/` should stay ignored, while manifest-derived sibling
`acceptance_summary.json` files should remain trackable and present in
`git ls-files`. Sidecars using
`schema_version: qcchem.release_artifact_acceptance.v0.1-alpha` must be bound to
the release manifest; CI rejects orphan release-artifact sidecars so accepted
release evidence cannot drift outside `configs/release/trust_first_audit.yaml`.
Older `qcchem.benchmark_acceptance.v0.1-alpha` sidecars can remain with
historical benchmark evidence, but they do not satisfy the release-artifact
binding contract.

## Exit Codes

- `0`: all required checks passed.
- `2`: the manifest could not be read or parsed, or at least one required
  check failed.

On failure, read `release_handoff.md` first for the run and artifact entrypoint,
then `release_readiness.md` for the full human review surface and failed check
names. The CLI also prints a bounded triage list of required failed check ids
and warning check ids, including the first nested failure or warning reason when
available, so CI logs expose the first actionable failure without opening the
readiness files.

## Manifest Shape

The default manifest is `configs/release/trust_first_audit.yaml`:

```yaml
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  warning_policy:
    max_count: 0
    allowed_ids: []
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
      terms:
        - QFT
        - LR-ACE
        - TC-QSCI
        - finite-cutoff
        - exploratory boundary
        - release audit
        - finite_model_exactness
        - continuum_chemistry_accuracy
        - hardware_accuracy
      required: true
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
    - python -m pytest tests -q -W error::scipy.sparse._base.SparseEfficiencyWarning
```

Supported exploratory asset kinds:

- `qft`
- `lr_ace`
- `tc_qsci`

Boolean manifest fields such as `required` and `acceptance_required` must use
YAML booleans (`true` or `false`), not quoted strings.
Scalar identity and path fields such as `profile`, `release_version`,
`curated_artifacts.name`, `curated_artifacts.path`, `exploratory_assets.name`,
`exploratory_assets.kind`, `exploratory_assets.config`,
`exploratory_assets.artifact`, and `required_docs.path` must be strings, not
numbers or booleans that can be coerced into ambiguous check ids or paths.
Path fields must also be repository-relative. Absolute paths, `~` home paths,
and `..` parent-directory components are rejected so the audit cannot read
machine-local files outside the release checkout.
Optional path fields such as `exploratory_assets.artifact` may be omitted, but
they must be non-empty strings when present; an empty string is rejected instead
of silently disabling artifact evidence checks.
List entries in `required_docs.terms`, `warning_policy.allowed_ids`, and
`acceptance_commands` must be non-empty strings; the loader rejects numeric,
boolean, null, or empty-string entries instead of coercing them. Surrounding
whitespace is stripped before use. Warning allow-list ids and acceptance command
recipes must also be unique so the release policy and advertised evidence
commands remain unambiguous.
The fields that generate audit check ids must be unique inside their manifest
section: `curated_artifacts.name`, `exploratory_assets.name`, and
`required_docs.path`. Duplicate entries are rejected before the audit runs so
sidecar bindings and readiness reports cannot become ambiguous.
`acceptance_commands` are recorded release-evidence recipes, not commands run by
the audit. The audit parses supported command forms (`python -m pytest ...` /
`pytest ...` and `qcchem benchmark run -c ... -o ...`) and fails if referenced
pytest targets or benchmark config files are missing or resolve outside the
audited repository root. Pytest recipes may include non-path options such as
`-W` warning filters, but they still need at least one explicit repository-local
target. Benchmark recipes must declare exactly one
`-c`/`--config` file and exactly one `-o`/`--output-dir` directory under
`artifacts/`; the output directory does not need to exist before the recipe
runs, but it must be a repository-relative artifact path. Absolute paths, `~`
home paths, and `..` parent-directory components are rejected for these
referenced targets and outputs too. Empty config or output option values are
reported as empty path values instead of being treated as the repository root.
Benchmark config targets must be files, not directories. Acceptance recipes must
be reproducible from the release checkout, not from sibling scratch files or
machine-local paths.
Benchmark acceptance recipes must not write directly to a manifest-protected
release artifact root, whether curated or exploratory, such as
`artifacts/lr_ace_flagship_suite_v1`; an interrupted run could otherwise leave
release evidence half-deleted. Use an ignored preview output such as
`artifacts/lr_ace_flagship_suite_v1/preview_local` for repeatable regeneration
checks. Add `--overwrite` to preview-output recipes when the same preview
directory should be refreshed, then refresh the curated artifact in a deliberate
release-update pass.
Python pytest recipes must use `python` or `python3` literally, not
machine-local interpreter paths such as `/usr/bin/python3` or `.venv/bin/python`.
They must name at least one concrete pytest target such as `tests/unit/...` or
`tests`, rather than relying on default test discovery. Pytest option values
that encode paths, for example `--basetemp=/tmp/...` or `--basetemp /tmp/...`,
must be non-empty and must not point at absolute, home-directory,
parent-directory, or repo-external locations.
Values consumed by pytest options, including `-m`, `-k`, `--basetemp`, and
`--junitxml`, do not count as explicit pytest targets; list the target path as a
separate argument.
They must also be single supported commands; shell control tokens such as `&&`,
`;`, pipes, and redirections are rejected instead of being treated as part of a
release recipe. Shell expansion and glob syntax such as `$VAR`, `$(...)`,
backticks, `*`, and `?` are rejected too; release recipes should name concrete
local targets. Malformed shell-style quoting is reported as a static parse
failure so the audit still writes `release_readiness.json` and
`release_readiness.md` for handoff.

## Checks

The Trust-First profile verifies:

- `pyproject.toml` version matches the manifest release version.
- Configured `acceptance_commands` reference existing local pytest targets or
  benchmark config files for supported command forms.
- When `.github/workflows/ci.yml` exists, its `Run tests` command is static and
  listed in `acceptance_commands` so CI and the release manifest cannot drift.
- The release audit statically confirms CI runs
  `qcchem release acceptance-status --strict --repair-plan` after the
  Trust-First release audit so manifest-bound sidecars must stay fresh and CI
  logs carry copyable repair commands before generated-file boundary checks
  pass.
- The release audit statically confirms CI uploads release diagnostic artifacts
  with `actions/upload-artifact` and `if: always()`, including Workbench smoke,
  release readiness, release handoff, release evidence handoff, single-run
  release history handoff, and release sidecar freshness outputs for failed-run
  handoff.
- Required curated artifacts exist.
- Configured artifacts parse as JSON objects, with unreadable payloads reported
  as failed checks instead of aborting the audit.
- Required curated artifacts either embed or sit beside an accepted
  `acceptance_summary.json` with no blocking failures.
- Curated artifacts expose the required `evidence_summary` fields, or the audit
  can derive a read-only release summary from legacy artifact payloads:
  - `primary_scientific_claim`
  - `primary_baseline`
  - `primary_error_metric`
  - `chemical_accuracy_status`
  - `runtime_evidence_status`
  - `trust_tier`
  - `recommended_action`
- Runtime preview or disabled submissions are not mislabeled as
  `hardware_verified`.
- Artifacts whose evidence summary declares `trust_tier: hardware_verified`
  also expose `runtime_evidence_status: retrieved_result`. Hardware campaigns
  must list at least one `hardware_verified_cases` entry; ordinary run artifacts
  must also carry top-level `hardware_verified: true` plus a retrieved
  `runtime_submission`.
- QFT, LR-ACE, and TC-QSCI assets remain inside the exploratory boundary.
- Exploratory asset config files parse as YAML mappings and classify as their
  manifest-declared kind; unreadable YAML becomes a failed config check.
- QFT language remains finite-cutoff lattice-QED / sparse projected
  physical-sector evidence, not continuum chemistry accuracy.
- Sparse exact QFT evidence keeps the three-layer accuracy boundary:
  `finite_model_exactness`, `continuum_chemistry_accuracy`, and
  `hardware_accuracy`.
- Sparse projected QFT artifacts do not convert `pauli_materialization=skipped`
  into fake zero-coefficient Pauli Hamiltonians. The release-facing evidence
  terms are `pauli_terms_available`, `sparse_exact_validation`,
  `projected_matrix_sha256`, `basis_hash`, and explicit sparse/exploratory
  measurement-cost scope.
- Required docs contain the release language needed for the Trust-First Release.
- Required docs that exist are readable UTF-8 text; unreadable doc paths become
  failed checks instead of aborting the audit.
- Configured warning policy bounds known release warnings by count and check id,
  so new warnings fail CI instead of silently accumulating.
- Research OS docs and examples exist for research objective, evidence capsule,
  claim compiler, and promotion gate workflows.
- Optional Research OS checks confirm new CLI workflow functions are importable
  and the promotion gate blocks direct exploratory promotion by default.

## JSON Contract

`release_readiness.json` contains:

- `schema_version`
- `schema_features`
- `profile`
- `release_version`
- `audit_provenance`
- `status`
- `required_pass_count`
- `required_fail_count`
- `warning_count`
- `failed_checks`
- `required_failed_checks`
- `warning_checks`
- `warning_policy`
- `acceptance_commands`
- `schema_features`
- `checks`
- `evidence_matrix`
- `recommended_action`

The current release-readiness schema is `1.1`. It is additive over schema `1`
and advertises added automation fields through `schema_features`, including
triage summaries, warning policy results, acceptance command recipes and
remediation hints, CI acceptance-command alignment, CI acceptance-status
freshness gate coverage, CI release diagnostic artifact upload coverage,
Evidence Matrix
claim/baseline/error fields, Evidence Matrix review warnings, acceptance
evidence bindings, acceptance status/count fields, and audit provenance.

The JSON shape is intended for automation. `audit_provenance` records the UTC
generation time, audited repository root, manifest path, and output directory so
reviewers can identify exactly which checkout and manifest produced the
readiness files. `failed_checks` and `warning_checks` are compact triage views
over the full `checks` list; `required_failed_checks` is the gating subset that
determines the release-audit exit status. Each entry preserves the stable check
id, required flag, summary, and details for CI and release tooling.
`acceptance_commands` records the static validation recipes from the manifest
for reproducible handoff; release audit validates supported local targets but
does not execute those commands. When a recipe is rejected, its failure details
include a `reason` plus a short `remediation` hint so maintainers can repair the
manifest without reverse-engineering parser internals. The Markdown companion is
intended for release review and handoff. It prints schema version, advertised
schema features, provenance including the audited repository root,
warning-policy status, warning allow-list ids, unexpected warning ids, required
failures, optional failures, and warnings before the evidence matrix so
reviewers can jump directly to the actionable issue. Failed acceptance command
recipes also get an `Acceptance Command Repairs` section with the rejected
command, reason, and remediation. Failed release-bound sidecar contracts get an
`Acceptance Contract Repairs` section with the check id, sidecar source,
field, expected value, actual value, and failure reason when one is available.
Its evidence matrix includes each artifact's runtime evidence status,
hardware-verified case count, runtime submission status, review-warning count,
review-warning details, acceptance schema version, acceptance check binding,
acceptance trust tier, acceptance runtime evidence status, acceptance status,
acceptance recommended action, acceptance blocking-failure count, acceptance
warning count, and acceptance contract-failure count so reviewers do not need to
inspect the JSON before spotting a weak runtime boundary, rejected sidecar,
warning-bearing sidecar, missing handoff action, or misbound sidecar.

Evidence Matrix `review_warnings` are human review hints for weak or missing
scientific support, such as `baseline_kind: none`, `baseline_strength: weak`,
missing primary error values, or placeholder `None` text in a claim. They do not
enter `warning_checks` and are not governed by `warning_policy`; use the formal
warning channel only for release-gating warning policy decisions.

## Operating Rules

- Do not add real runtime submission to release audit.
- Do not run QFT hardware micro real suites from release audit.
- Do not let release audit regenerate curated artifacts.
- Do not promote QFT, LR-ACE, or TC-QSCI from exploratory to validated through a
  documentation-only change.
- Do not treat an Evidence Capsule or Claim Compiler pass as a replacement for
  a validated baseline, chemical accuracy status, runtime evidence status, or
  release audit.
- Keep release terms consistent across README, user manual, verified scope,
  release showcase, release audit docs, and reports.
- Keep docs role-specific but claim-equivalent: README is the public entrypoint,
  the user manual is the task guide, verified scope is the claim-boundary
  reference, and release showcase is the demo path.
- If full pytest runs before the audit, confirm it did not rewrite tracked
  release files or leave required sidecars untracked:

```bash
git diff --name-only -- .github artifacts README.md docs configs qcchem tests pyproject.toml
git status --short --untracked-files=all -- .github artifacts README.md docs configs qcchem tests pyproject.toml
```

Both commands should print nothing in a packaged release branch, except for
ignored local outputs such as `artifacts/release_audit/`,
`artifacts/release_evidence/`, and `artifacts/workflows/`.
CI also checks release acceptance sidecar freshness with
`qcchem release acceptance-status --strict --repair-plan`, then confirms
release-audit outputs and workflow bundles match `.gitignore`, while
manifest-derived `acceptance_summary.json` sidecars do not.
