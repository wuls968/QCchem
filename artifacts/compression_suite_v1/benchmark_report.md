# Benchmark Suite Report: compression_suite_v1

## Benchmark Suite Summary

- total_cases: `4`
- status_counts: `{'validated': 4}`

## Cases

- `lih_active_exact_uncompressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.14186420799524058`
- `lih_active_exact_compressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.126223207989824`
  compression=`modified_cholesky` execution_enabled=`True` rank=`2` terms=`27`->`12` compression_status=`validated`
  compressed_vs_uncompressed abs_error=`0.0010097855590132099` relative_error=`0.00012843665887519792` compressed_solve_s=`0.0007334580004680902` uncompressed_solve_s=`0.00045900000259280205`
- `lih_active_vqe_uncompressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.4303446249978151`
- `lih_active_vqe_compressed` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.857692917008535`
  compression=`modified_cholesky` execution_enabled=`True` rank=`2` terms=`27`->`12` compression_status=`validated`
  compressed_vs_uncompressed abs_error=`0.0010097910917998831` relative_error=`0.00012843736278797923` compressed_solve_s=`0.42662604099314194` uncompressed_solve_s=`0.31115820800187066`
