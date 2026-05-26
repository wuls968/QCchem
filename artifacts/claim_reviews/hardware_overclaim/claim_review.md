# QCchem Claim Compiler Review

- support_level: `overclaimed`
- status: `failed`
- recommended_action: `rewrite_claim_with_hardware_boundary`

## Claim

hardware_verified proves publication-grade chemical accuracy

## Supported Points

- Best chemistry evidence: trust_tier=hardware_verified, chemical_accuracy_status=not_met.
- Best runtime evidence: runtime_evidence_status=retrieved_result, hardware_verified=True.

## Unsupported Points

- hardware_campaign-2165c4ec626b: chemical accuracy is not_met.

## Overclaim Findings

- `hardware-boundary-hardware_campaign-2165c4ec626b`: hardware_verified is runtime retrieval evidence, not publication-grade chemistry validation.
- `accuracy-gap-hardware_campaign-2165c4ec626b`: The claim mentions chemical accuracy, but the linked evidence does not meet it.

## Required Next Evidence

- Provide a strong exact or accepted benchmark baseline before publication-grade language.
- Show runtime-derived chemical accuracy against the stated baseline before hardware chemistry claims.
- hardware_campaign-2165c4ec626b: chemical accuracy is not_met.

## Safe Rewrite

The artifact verifies runtime submission and retrieval, but the hardware-derived chemistry estimate remains exploratory until runtime chemical accuracy is met against the stated baseline.
