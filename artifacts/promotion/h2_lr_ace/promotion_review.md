# QCchem Promotion Gate Review

- artifact: `artifacts/h2_lr_ace/result.json`
- source_trust_tier: `exploratory`
- module_origin: `lr_ace`
- target: `validated_algorithm_candidate`
- status: `blocked`
- recommended_action: `collect_stronger_baseline`

## Blocking Gaps

- Exploratory or unstable artifact cannot be directly promoted to validated.
- Missing required studies: multiple molecules, active-space coverage, ansatz limitation analysis, failure cases.

## Required Studies

- exact baseline
- multiple molecules
- active-space coverage
- compression-vs-uncompressed comparison
- ansatz limitation analysis
- failure cases

## Suggested Configs

- `configs/exploratory/h2_lr_ace.yaml`
- `configs/exploratory/lih_active_lr_ace.yaml`

## Safe Claim

lr_ace evidence may be discussed as bounded exploratory algorithm evidence; broader validated or publication-grade claims require the promotion gate studies first.
