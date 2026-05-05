# QCchem Hardware Runtime Campaign Report

- suite_name: `hardware_calibration_suite_v1`
- total_cases: `8`
- chemical_accuracy_target_hartree: `0.0016`
- runtime_evidence_status_counts: `{'retrieved_result': 8}`

## Best Case

- name: `h2_runtime_hardware_probe_puccd_layout`
- achieved_error: `0.013673650274335092`
- meets_chemical_accuracy: `False`

## Worst Case

- name: `lih_active_runtime_hardware_probe_v2`
- achieved_error: `0.38879419502160584`
- meets_chemical_accuracy: `False`

## Cases

| Name | Achieved Error | Meets Chemical Accuracy |
| --- | --- | --- |
| h2_runtime_hardware_probe | 0.1740707404306301 | False |
| h2_runtime_hardware_probe_ca | 0.046849070101739665 | False |
| h2_runtime_hardware_probe_puccd | 0.05367855085690487 | False |
| h2_runtime_hardware_probe_ca_layout | 0.040409655531094435 | False |
| h2_runtime_hardware_probe_puccd_layout | 0.013673650274335092 | False |
| h2_runtime_hardware_probe_puccd_layout_mitigated | 0.26726073507437587 | False |
| h2_runtime_hardware_probe_puccd_layout_highshots | 0.05332134520924514 | False |
| lih_active_runtime_hardware_probe_v2 | 0.38879419502160584 | False |
