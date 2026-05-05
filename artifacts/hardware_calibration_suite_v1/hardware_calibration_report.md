# Hardware Calibration Dashboard

## Runtime Submission Evidence

- total_cases: `8`
- runtime_evidence_status_counts: `{'retrieved_result': 8}`
- hardware_verified_cases: `['h2_runtime_hardware_probe', 'h2_runtime_hardware_probe_ca', 'h2_runtime_hardware_probe_puccd', 'h2_runtime_hardware_probe_ca_layout', 'h2_runtime_hardware_probe_puccd_layout', 'h2_runtime_hardware_probe_puccd_layout_mitigated', 'h2_runtime_hardware_probe_puccd_layout_highshots', 'lih_active_runtime_hardware_probe_v2']`

| Case | Backend | Layout Strategy | Layout | 2Q Gates | Depth | Runtime Evidence Status | Evidence Tier | Submission Status | Submission Wall Time (s) | Runtime Shots | Runtime Usage (s) | Runtime Quantum (s) | Requested Precision | Budget Strategy | Achieved Error | Meets Chem Acc | Distance to Target | Achieved Error Status | Hardware Verified |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | --- | --- |
| h2_runtime_hardware_probe | ibm_marrakesh | None |  | None | None | retrieved_result | retrieved_result | succeeded | 59.237931750001735 | 1024 | 12 | 12 | 0.05 | shot_budget | 0.1740707404306301 | False | 0.1724707404306301 | derived_from_runtime_result | True |
| h2_runtime_hardware_probe_ca | ibm_kingston | None |  | None | None | retrieved_result | retrieved_result | succeeded | 56.549181249996764 | 4096 | 28 | 28 | 0.02 | chemical_accuracy_push | 0.046849070101739665 | False | 0.04524907010173967 | derived_from_runtime_result | True |
| h2_runtime_hardware_probe_puccd | ibm_kingston | None |  | None | None | retrieved_result | retrieved_result | succeeded | 88.31883212500543 | 4096 | 28 | 28 | 0.02 | chemical_accuracy_push | 0.05367855085690487 | False | 0.052078550856904875 | derived_from_runtime_result | True |
| h2_runtime_hardware_probe_ca_layout | ibm_kingston | min_weighted_error | 44,45,46,47 | 49 | 158 | retrieved_result | retrieved_result | succeeded | None | 4096 | 28 | 28 | 0.02 | chemical_accuracy_push | 0.040409655531094435 | False | 0.03880965553109444 | derived_from_runtime_result | True |
| h2_runtime_hardware_probe_puccd_layout | ibm_kingston | min_weighted_error | 44,45,46,47 | 42 | 146 | retrieved_result | retrieved_result | succeeded | 85.04070733400295 | 4096 | 33 | 33 | 0.02 | chemical_accuracy_push | 0.013673650274335092 | False | 0.012073650274335091 | derived_from_runtime_result | True |
| h2_runtime_hardware_probe_puccd_layout_mitigated | ibm_kingston | min_weighted_error | 44,45,46,47 | 42 | 146 | retrieved_result | retrieved_result | succeeded | None | 8192 | 28 | 28 | 0.015 | chemical_accuracy_push | 0.26726073507437587 | False | 0.2656607350743759 | derived_from_runtime_result | True |
| h2_runtime_hardware_probe_puccd_layout_highshots | ibm_kingston | min_weighted_error | 44,45,46,47 | 42 | 146 | retrieved_result | retrieved_result | succeeded | None | 8192 | 45 | 45 | 0.01 | chemical_accuracy_push | 0.05332134520924514 | False | 0.051721345209245144 | derived_from_runtime_result | True |
| lih_active_runtime_hardware_probe_v2 | ibm_fez | None |  | None | None | retrieved_result | retrieved_result | succeeded | 84.30369187500037 | 44 | 2 | 2 | 0.15 | None | 0.38879419502160584 | False | 0.38719419502160585 | derived_from_runtime_result | True |
