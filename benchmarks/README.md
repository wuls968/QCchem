# QCchem Benchmarks

- `benchmark_suite_v1.yaml`: 当前正式 benchmark suite
- `qmmm_environment_embedding_suite_v1.yaml`: 非共价 electrostatic embedding 主线验证 suite，运行 smoke/full QMMM validation profiles
- `field_model_qft_smoke_v2.yaml`: QFT/lattice-QED CI 级 smoke suite，覆盖 sparse projected exact、sector audit、dynamics 和 runtime-preview disabled path
- `field_model_qft_cutoff_grid_convergence_v1.yaml`: finite-cutoff/grid/softening convergence suite，用来报告模型截断和网格敏感性，不声称 continuum chemistry accuracy
- `field_model_qft_dynamics_resource_v1.yaml`: QFT dynamics/resource suite，覆盖 Trotter step、2D Wilson smoke、incremental dynamics 和 runtime preview resource gates
- `field_model_qft_hardware_micro_v1.yaml`: QFT Runtime micro preview suite，默认 `submit_real_job: false`
- `field_model_qft_hardware_micro_real_v1.yaml`: QFT Runtime real micro template，只有明确 runtime-budget confirmation 后才能提交真实后端
- `mini_suite.yaml`: 轻量回归 suite，用于测试与快速检查

QFT suites are exploratory. Sparse exact cases validate the configured
finite-cutoff lattice-QED Hamiltonian and physical-sector evidence only:
`continuum_chemistry_accuracy` stays `not_claimed`, `hardware_accuracy` stays
`unavailable` without a collected Runtime/shot-based result, and
`pauli_materialization=skipped` must not be converted into a fake Pauli
Hamiltonian.
