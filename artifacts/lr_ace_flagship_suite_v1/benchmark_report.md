# Benchmark Suite Report: lr_ace_flagship_suite_v1

> Validated-like and exploratory cases are separated below to avoid mixing benchmark scopes.

## Best Evidence

- primary_scientific_claim: `Benchmark suite lr_ace_flagship_suite_v1 currently defends a validated scope across 5 cases.`
- trust_tier: `validated`
- recommended_action: `promote_validated_result`

## Report Cover

- total_cases: `5`
- validated_like_cases: `5`
- exploratory_cases: `0`
- chemical_accuracy_target_hartree: `0.0016`
- dashboard_summary: `{'compressed_cases': ['h2o_active_lr_ace_adaptive', 'h3plus_lr_ace_adaptive', 'h4_chain_lr_ace_adaptive'], 'runtime_cases': [], 'estimated_vs_measured_cost_ratios': {}, 'precision_targets': {'h2_lr_ace_flagship': 0.01, 'lih_active_lr_ace_flagship': 0.01, 'h2o_active_lr_ace_adaptive': 0.01, 'h3plus_lr_ace_adaptive': 0.01, 'h4_chain_lr_ace_adaptive': 0.01}, 'grouping_policies': {}, 'resilience_levels': {}, 'achieved_errors': {'h2_lr_ace_flagship': 1.3086143280105489e-08, 'lih_active_lr_ace_flagship': 9.83466863502258e-10, 'h2o_active_lr_ace_adaptive': 7.580214354163672e-05, 'h3plus_lr_ace_adaptive': 1.1941071340615395e-06, 'h4_chain_lr_ace_adaptive': 1.7242036323139587e-06}, 'hardware_verified_cases': [], 'cases': [{'name': 'h2_lr_ace_flagship', 'estimated_measurement_cost': 20000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 0.009407709003426135, 'achieved_error': 1.3086143280105489e-08, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'lih_active_lr_ace_flagship', 'estimated_measurement_cost': 40000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 0.0392963329795748, 'achieved_error': 9.83466863502258e-10, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'h2o_active_lr_ace_adaptive', 'estimated_measurement_cost': 70000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 35.263980165997054, 'achieved_error': 7.580214354163672e-05, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'h3plus_lr_ace_adaptive', 'estimated_measurement_cost': 70000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 0.398849000048358, 'achieved_error': 1.1941071340615395e-06, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'h4_chain_lr_ace_adaptive', 'estimated_measurement_cost': 110000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 27.82985383301275, 'achieved_error': 1.7242036323139587e-06, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}], 'field_model_campaign': {'schema_version': 'qcchem.field_model_campaign.v0.1-alpha', 'case_count': 0, 'by_model': {}, 'hardware_candidates': [], 'cutoff_sensitive_cases': [], 'trotter_limited_cases': [], 'ansatz_limited_cases': [], 'recommended_trotter_step': None, 'hardware_gate_note': 'Real quantum hardware is not submitted by this local campaign; candidates only mean a preview passed local exact/cutoff/leakage/resource gates.'}}`

## Best Case

- case: `lih_active_lr_ace_flagship`
- status: `validated`
- absolute_error: `9.83466863502258e-10`
- distance_to_chemical_accuracy: `0.0`

## Benchmark Suite Summary

- total_cases: `5`
- status_counts: `{'validated': 5}`
- calibration_summary: `{'cases_with_measured_cost': 0, 'cases_with_estimated_cost': 5, 'mean_estimated_cost': 62000.0, 'mean_measured_cost': None, 'mean_achieved_error': 1.5746904783631167e-05, 'field_model_campaign': {'schema_version': 'qcchem.field_model_campaign.v0.1-alpha', 'case_count': 0, 'by_model': {}, 'hardware_candidates': [], 'cutoff_sensitive_cases': [], 'trotter_limited_cases': [], 'ansatz_limited_cases': [], 'recommended_trotter_step': None, 'hardware_gate_note': 'Real quantum hardware is not submitted by this local campaign; candidates only mean a preview passed local exact/cutoff/leakage/resource gates.'}}`
- dashboard_summary: `{'compressed_cases': ['h2o_active_lr_ace_adaptive', 'h3plus_lr_ace_adaptive', 'h4_chain_lr_ace_adaptive'], 'runtime_cases': [], 'estimated_vs_measured_cost_ratios': {}, 'precision_targets': {'h2_lr_ace_flagship': 0.01, 'lih_active_lr_ace_flagship': 0.01, 'h2o_active_lr_ace_adaptive': 0.01, 'h3plus_lr_ace_adaptive': 0.01, 'h4_chain_lr_ace_adaptive': 0.01}, 'grouping_policies': {}, 'resilience_levels': {}, 'achieved_errors': {'h2_lr_ace_flagship': 1.3086143280105489e-08, 'lih_active_lr_ace_flagship': 9.83466863502258e-10, 'h2o_active_lr_ace_adaptive': 7.580214354163672e-05, 'h3plus_lr_ace_adaptive': 1.1941071340615395e-06, 'h4_chain_lr_ace_adaptive': 1.7242036323139587e-06}, 'hardware_verified_cases': [], 'cases': [{'name': 'h2_lr_ace_flagship', 'estimated_measurement_cost': 20000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 0.009407709003426135, 'achieved_error': 1.3086143280105489e-08, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'lih_active_lr_ace_flagship', 'estimated_measurement_cost': 40000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 0.0392963329795748, 'achieved_error': 9.83466863502258e-10, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'h2o_active_lr_ace_adaptive', 'estimated_measurement_cost': 70000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 35.263980165997054, 'achieved_error': 7.580214354163672e-05, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'h3plus_lr_ace_adaptive', 'estimated_measurement_cost': 70000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 0.398849000048358, 'achieved_error': 1.1941071340615395e-06, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}, {'name': 'h4_chain_lr_ace_adaptive', 'estimated_measurement_cost': 110000.0, 'measured_shot_usage': None, 'measured_wall_time_seconds': 27.82985383301275, 'achieved_error': 1.7242036323139587e-06, 'hardware_verified': False, 'hardware_evidence_tier': None, 'runtime_evidence_status': 'none'}], 'field_model_campaign': {'schema_version': 'qcchem.field_model_campaign.v0.1-alpha', 'case_count': 0, 'by_model': {}, 'hardware_candidates': [], 'cutoff_sensitive_cases': [], 'trotter_limited_cases': [], 'ansatz_limited_cases': [], 'recommended_trotter_step': None, 'hardware_gate_note': 'Real quantum hardware is not submitted by this local campaign; candidates only mean a preview passed local exact/cutoff/leakage/resource gates.'}}`
- validated_like_cases: `5`
- exploratory_cases: `0`

## Field-Model Campaign

- schema_version: `qcchem.field_model_campaign.v0.1-alpha`
- case_count: `0`
- hardware_candidates: `[]`
- cutoff_sensitive_cases: `[]`
- trotter_limited_cases: `[]`
- ansatz_limited_cases: `[]`
- recommended_trotter_step: `None`
- hardware_gate_note: `Real quantum hardware is not submitted by this local campaign; candidates only mean a preview passed local exact/cutoff/leakage/resource gates.`

## Validated-Like Cases

- `h2_lr_ace_flagship` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.13002020795829594`
  measurement groups=`2` estimated_cost=`20000.0` measured_cost=`None` achieved_error=`1.3086143280105489e-08` hardware_verified=`False` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
- `lih_active_lr_ace_flagship` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.17597612499957904`
  measurement groups=`4` estimated_cost=`40000.0` measured_cost=`None` achieved_error=`9.83466863502258e-10` hardware_verified=`False` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
- `h2o_active_lr_ace_adaptive` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`67.47925066697644`
  compression=`modified_cholesky` execution_enabled=`True` rank=`10` terms=`95`->`95` compression_status=`validated`
  measurement groups=`7` estimated_cost=`70000.0` measured_cost=`None` achieved_error=`7.580214354163672e-05` hardware_verified=`False` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
  compressed_vs_uncompressed abs_error=`7.580214354163672e-05` relative_error=`1.011097354824259e-06` compressed_solve_s=`35.263980165997054` uncompressed_solve_s=`31.965455540979747`
- `h3plus_lr_ace_adaptive` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`0.9209322920069098`
  compression=`modified_cholesky` execution_enabled=`True` rank=`6` terms=`52`->`52` compression_status=`validated`
  measurement groups=`7` estimated_cost=`70000.0` measured_cost=`None` achieved_error=`1.1941071340615395e-06` hardware_verified=`False` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
  compressed_vs_uncompressed abs_error=`1.1941071340615395e-06` relative_error=`9.420334359450455e-07` compressed_solve_s=`0.398849000048358` uncompressed_solve_s=`0.34311766701284796`
- `h4_chain_lr_ace_adaptive` | kind=`run` | status=`validated` | expected=`validated` | wall_time=`62.53281237499323`
  compression=`modified_cholesky` execution_enabled=`True` rank=`10` terms=`165`->`165` compression_status=`validated`
  measurement groups=`11` estimated_cost=`110000.0` measured_cost=`None` achieved_error=`1.7242036323139587e-06` hardware_verified=`False` runtime_service=`None` grouping_policy=`None` resilience_level=`None`
  compressed_vs_uncompressed abs_error=`1.7242036323139587e-06` relative_error=`7.910805413117001e-07` compressed_solve_s=`27.82985383301275` uncompressed_solve_s=`34.37912945798598`
