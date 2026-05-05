# Benchmark Suite Report: benchmark_suite_v1

> Validated-like and exploratory cases are separated below to avoid mixing benchmark scopes.

## Report Cover

- total_cases: `10`
- validated_like_cases: `10`
- exploratory_cases: `0`
- chemical_accuracy_target_hartree: `0.0016`
- dashboard_summary: `{}`

## Best Case

- case: `jw_bk_consistency_h2`
- status: `validated`
- absolute_error: `2.220446049250313e-15`
- distance_to_chemical_accuracy: `0.0`

## Benchmark Suite Summary

- total_cases: `10`
- status_counts: `{'unstable': 4, 'validated': 6}`
- calibration_summary: `{}`
- dashboard_summary: `{}`
- validated_like_cases: `10`
- exploratory_cases: `0`

## Validated-Like Cases

- `h2_exact_reference` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`None`
- `h2_statevector_vqe` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`None`
- `h2_shot_vqe` | kind=`run` | status=`unstable` | expected=`unstable` | wall_time=`None`
- `h2_noisy_comparison` | kind=`noise_comparison` | status=`unstable` | expected=`unstable` | wall_time=`None`
- `lih_exact_reference` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`None`
- `lih_active_space_vqe` | kind=`run` | status=`unstable` | expected=`validated` | wall_time=`None`
- `h2o_active_space_exact` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`None`
- `jw_bk_consistency_h2` | kind=`consistency` | status=`validated` | expected=`validated` | wall_time=`None`
- `h2_shot_scaling` | kind=`shot_scaling` | status=`unstable` | expected=`exploratory` | wall_time=`None`
- `h2_optimizer_stability` | kind=`optimizer_stability` | status=`validated` | expected=`validated` | wall_time=`None`
