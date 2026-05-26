# QCchem Claim Compiler

The Claim Compiler compares a scientific statement against linked QCchem
artifacts and returns a conservative support level.

## Command

```bash
qcchem claim check \
  --claim-file examples/claims/hardware_overclaim.txt \
  --target artifacts/hardware_calibration_suite_v1 \
  -o artifacts/claim_reviews/hardware_overclaim
```

Outputs:

- `claim_review.json`
- `claim_review.md`

## Support Levels

- `supported`: linked best evidence supports the statement within the trust
  tier and baseline strength.
- `partially_supported`: some evidence exists, but gaps remain.
- `unsupported`: linked artifacts do not support the statement.
- `overclaimed`: the statement uses validated, publication-grade, chemical
  accuracy, or hardware proof language that exceeds current evidence.

The compiler separates local `chemical accuracy status`, `runtime evidence status`,
and hardware verification boundary. A retrieved runtime result is not
the same thing as hardware-derived chemistry accuracy.

## Safe Rewrite

Every failed or overclaimed review includes a `safe_rewrite`: a more conservative
statement aligned to best evidence, trust tier, baseline strength, and
recommended next action.
