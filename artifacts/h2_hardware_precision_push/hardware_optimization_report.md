# QCchem Hardware Optimization Report

## Optimization Trial

- profile: `h2_precision_push`
- mode: `collect`
- stop_reason: `pause_after_diverse_strategy_probe`
- recommended_action: `pause_hardware_spend_and_analyze_bias`
- best_existing_reference: `artifacts/h2_runtime_hardware_probe_puccd_layout`

## Hardware Evidence Snapshot

- empirical_best_attempt: `parity_puccd_layout` error=`0.018253500584027416` Ha meets_chemical_accuracy=`False`
- best_existing_reference_summary: `h2_runtime_hardware_probe_puccd_layout` error=`0.013673650274335092` Ha depth=`146` 2Q=`42`
- runtime_accuracy_delta_vs_best_existing: `0.004579850309692324` Ha (negative means the optimization trial improved the prior hardware reference)
- chemical_accuracy_target: `0.0016` Ha
- empirical_gap_to_chemical_accuracy: `0.016653500584027415` Ha
- prior_reference_gap_to_chemical_accuracy: `0.012073650274335091` Ha

Interpretation: local algorithmic accuracy is validated for the selected H2 workloads, but the retrieved hardware-derived chemistry estimates remain exploratory until the runtime error reaches the chemical-accuracy threshold.

## Runtime Budget Ledger

- real_jobs_submitted: `2`
- max_real_jobs: `3`
- total_budgeted_shots: `16384`
- max_total_budgeted_shots: `40960`
- total_estimated_quantum_seconds: `71.259544237`
- max_total_estimated_quantum_seconds: `600.0`
- can_submit_more: `True`

## Ranked Candidates

| Candidate | Mapping | Ansatz | Local pass | Qubits | Terms | 2Q Gates | Depth | Local error | Runtime eligible |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| parity_puccd_layout | parity_two_qubit_reduction | puccd | True | 2 | 5 | 9 | 37 | 4.77500483597737e-10 | True |
| parity_succd_layout | parity_two_qubit_reduction | succd | True | 2 | 5 | 9 | 37 | 4.77500483597737e-10 | True |
| parity_uccsd_layout | parity_two_qubit_reduction | uccsd | True | 2 | 5 | 17 | 61 | 1.3755125038983351e-08 | True |
| jw_puccd_layout_baseline | jordan_wigner | puccd | True | 4 | 15 | 23 | 89 | 4.775011497315518e-10 | True |

## Submitted Attempts

- `parity_puccd_layout` shots=`8192` submitted=`True` succeeded=`True` runtime_error=`0.018253500584027416` artifact=`/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_01_parity_puccd_layout_8192`
- `jw_puccd_layout_baseline` shots=`8192` submitted=`True` succeeded=`True` runtime_error=`0.04770089847504311` artifact=`/Users/a0000/QCchem/artifacts/h2_hardware_precision_push/runtime_jobs/job_02_jw_puccd_layout_baseline_8192`
