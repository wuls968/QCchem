# QCchem Promotion Gate

The Promotion Gate is a read-only review for exploratory artifacts. It does not
change artifact trust tiers and it never promotes QFT, LR-ACE, or TC-QSCI by
documentation alone.

## Command

```bash
qcchem promote exploratory \
  --artifact artifacts/h2_lr_ace/result.json \
  --target validated_algorithm_candidate \
  -o artifacts/promotion/h2_lr_ace
```

Outputs:

- `promotion_review.json`
- `promotion_review.md`

## Rules

QFT / lattice-QED:

- may enter `finite_cutoff_algorithm_candidate`
- must not become continuum chemistry validated
- requires finite cutoff audit, Gauss law / physical sector audit, grid/cutoff
  convergence, and comparison against molecular references where meaningful

LR-ACE:

- may enter `validated_algorithm_candidate`
- must not become a publication-grade general method by default
- requires exact baseline, multiple molecules, active-space coverage,
  compression-vs-uncompressed comparison, ansatz limitation analysis, and
  failure cases

TC-QSCI:

- may enter `exploratory_algorithm_candidate`
- requires determinant selection audit, symmetry sector audit, physical
  Hamiltonian final diagonalization, CAST provenance, ablation against non-TC
  selection, and exact baseline where feasible

## Boundary

The promotion gate preserves the exploratory boundary. It can allow a candidate
path only when required studies are present; otherwise the recommended next
action is to collect stronger baselines, run ablation studies, or compare
against best evidence.
