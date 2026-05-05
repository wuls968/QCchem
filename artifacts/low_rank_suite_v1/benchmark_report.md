# Benchmark Suite Report: low_rank_suite_v1

## Benchmark Suite Summary

- total_cases: `5`
- status_counts: `{'validated': 4, 'unstable': 1}`
- calibration_summary: `{'cases_with_measured_cost': 1, 'cases_with_estimated_cost': 5, 'mean_estimated_cost': 60000.0, 'mean_measured_cost': 24576.0, 'mean_achieved_error': 0.00045919525961819475}`
- dashboard_summary: `{'compressed_cases': ['lih_active_exact_compressed', 'lih_active_vqe_ideal_compressed', 'lih_active_vqe_runtime_ready_compressed'], 'runtime_cases': ['lih_active_vqe_runtime_ready_compressed'], 'estimated_vs_measured_cost_ratios': {'lih_active_vqe_runtime_ready_compressed': 3.2552083333333335}, 'precision_targets': {'lih_active_exact_uncompressed': 0.01, 'lih_active_exact_compressed': 0.01, 'lih_active_vqe_ideal_uncompressed': 0.01, 'lih_active_vqe_ideal_compressed': 0.01, 'lih_active_vqe_runtime_ready_compressed': 0.005}, 'grouping_policies': {'lih_active_vqe_runtime_ready_compressed': 'commuting_low_rank'}, 'resilience_levels': {'lih_active_vqe_runtime_ready_compressed': 1}, 'achieved_errors': {'lih_active_exact_uncompressed': 4.440892098500626e-16, 'lih_active_exact_compressed': 0.001009785559008769, 'lih_active_vqe_ideal_uncompressed': 1.1416471323855149e-08, 'lih_active_vqe_ideal_compressed': 0.0010097910917998831, 'lih_active_vqe_runtime_ready_compressed': 0.00027638823081055364}}`

## Cases

- `lih_active_exact_uncompressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.22236562499983847`
  measurement groups=`9` estimated_cost=`90000.0` measured_cost=`None` achieved_error=`4.440892098500626e-16` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
- `lih_active_exact_compressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.1496407079994242`
  compression=`modified_cholesky` execution_enabled=`True` rank=`2` terms=`27`->`12` compression_status=`validated`
  measurement groups=`2` estimated_cost=`20000.0` measured_cost=`None` achieved_error=`0.001009785559008769` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
  compressed_vs_uncompressed abs_error=`0.001009785559008769` relative_error=`0.000128436658874633` compressed_solve_s=`0.0007770419997541467` uncompressed_solve_s=`0.00045366700032900553`
- `lih_active_vqe_ideal_uncompressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.5103214169994317`
  measurement groups=`9` estimated_cost=`90000.0` measured_cost=`None` achieved_error=`1.1416471323855149e-08` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
- `lih_active_vqe_ideal_compressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.9885190420000072`
  compression=`modified_cholesky` execution_enabled=`True` rank=`2` terms=`27`->`12` compression_status=`validated`
  measurement groups=`2` estimated_cost=`20000.0` measured_cost=`None` achieved_error=`0.0010097910917998831` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
  compressed_vs_uncompressed abs_error=`0.0010097910917998831` relative_error=`0.00012843736278797923` compressed_solve_s=`0.4813544999997248` uncompressed_solve_s=`0.34816262500044104`
- `lih_active_vqe_runtime_ready_compressed` | kind=`run` | status=`unstable` | expected=`exploratory` | wall_time=`2.3530660829992485`
  compression=`modified_cholesky` execution_enabled=`True` rank=`2` terms=`27`->`12` compression_status=`validated`
  measurement groups=`2` estimated_cost=`80000.0` measured_cost=`24576.0` achieved_error=`0.00027638823081055364` runtime_service=`ibm_quantum_platform` grouping_policy=`commuting_low_rank` resilience_level=`1`
  compressed_vs_uncompressed abs_error=`0.00027638823081055364` relative_error=`3.515040414777986e-05` compressed_solve_s=`1.0354859170001873` uncompressed_solve_s=`1.1158275000007052`
