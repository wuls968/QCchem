# QCchem Evidence Capsule

- artifact_root: `artifacts/h2`
- artifact_kind: `run`
- capsule_status: `partial`
- trust_tier: `unknown`
- recommended_action: `review_evidence_boundary`

## Required Files

- `result.json`: `True`
- `report.md`: `True`
- `resolved_config.yaml`: `True`
- `run.log`: `True`

## Evidence Summary

- status: `missing`
- missing_fields: `['result_identity', 'primary_scientific_claim', 'primary_baseline', 'primary_error_metric', 'chemical_accuracy_status', 'runtime_evidence_status', 'trust_tier', 'recommended_action']`

## Boundary Warnings

- None

## Blocking Issues

- Missing result payload fields: evidence_summary.
- evidence_summary is missing: missing result_identity, primary_scientific_claim, primary_baseline, primary_error_metric, chemical_accuracy_status, runtime_evidence_status, trust_tier, recommended_action.
