# QCchem Benchmark Suite v1

## 设计目标

Benchmark Suite v1 不是一堆零散样例，而是 QCchem 的正式 benchmark registry。它回答三个问题：

1. 哪些路径已经处于 validated 范围
2. 哪些路径目前仍在 exploratory 或 unstable 范围
3. noisy execution 相对 exact / ideal 的偏移有多大

## 当前包含的 benchmark

- `h2_exact_reference`
- `h2_statevector_vqe`
- `h2_shot_vqe`
- `h2_noisy_comparison`
- `lih_exact_reference`
- `lih_active_space_vqe`
- `h2o_active_space_exact`
- `jw_bk_consistency_h2`
- `h2_shot_scaling`
- `h2_optimizer_stability`
- `qmmm_environment_embedding_smoke`
- `qmmm_environment_embedding_full`
- `pbc_qmmm_smoke`
- `pbc_qmmm_full`
- `field_model_qft_smoke_v2`
- `field_model_qft_cutoff_grid_convergence_v1`
- `field_model_qft_dynamics_resource_v1`
- `field_model_qft_hardware_micro_v1`
- `field_model_qft_hardware_micro_real_v1`
- `method_evidence_suite_v1`
- `method_promotion_probe_v1`

## case kind

- `run`
  - 普通单 run benchmark，直接复用 `RunResult`
- `consistency`
  - 比较两个等价物理路径，例如 JW / BK
- `shot_scaling`
  - 比较不同 shots 下的误差和统计量
- `optimizer_stability`
  - 比较不同优化器或设置的稳定性
- `noise_comparison`
  - 比较 exact、ideal、noisy 三条路径
- `qmmm_validation`
  - 运行 `qcchem.validation.run_qmmm_embedding_validation`，把 smoke/full 环境嵌入验证闭环映射为 benchmark case
- `pbc_qmmm_validation`
  - 运行 `qcchem.validation.run_pbc_qmmm_validation`，把 smoke/full Gamma-only PBC 与 PBC-QM/MM Ewald 验证映射为 benchmark case

## Method Evidence suite

`benchmarks/method_evidence_suite_v1.yaml` 是 Method Evidence / 10-Method v1
的快速比较 gate。它运行 H2、LiH active-space 和 PBC H2 小体系，记录
E-ADAPT、OO-QCASSCF、QSCI++、QSCI post-correlation、q-sc-EOM、Q-Embed、
kQ-PBC、Trust-QEM、Shadow-LR 和 FT-QPE Planner 的 sidecar 方法列表、
误差、shot-cost 估计、wall time，以及方法专属指标。运行完成后额外写出
`method_evidence_summary.json`，用于记录 pairwise baseline comparison、
FT-QPE resource-model finding、headline finding、10-method contract matrix
和 promotion boundary。
Artifact index 同时暴露 `has_method_evidence_summary`、
`method_evidence_method_case_count`、`method_evidence_accuracy_advantage_pairs`
`method_evidence_ft_qpe_resource_case_count`、
`method_evidence_contract_matrix_status` 和
`method_evidence_contract_missing_methods`，方便 Workbench、release audit 或
外部脚本快速筛选方法证据 benchmark。

可直接运行：

```bash
qcchem benchmark run \
  -c benchmarks/method_evidence_suite_v1.yaml \
  --include-tag fast \
  -o artifacts/method_evidence_suite_v1_local \
  --overwrite
```

默认 Trust-First release manifest 使用规范 curated root
`artifacts/method_evidence_suite_v1/benchmark_result.json`。刷新该 release
artifact 后，需要用 `qcchem release accept-artifact --name
method_evidence_suite_v1 --overwrite` 重新生成 release-bound
`acceptance_summary.json`。Manifest 中的重跑 recipe 写到
`artifacts/method_evidence_suite_v1/preview_local`，用于验证可复现性而不覆盖
curated evidence root。

该 suite 的判据是 evidence-gate，不是论文级方法胜负。它保留
`lih_active_vqe_statevector_baseline` 作为稳定的 LiH 理想基线；shot-estimator
baseline 可作为单独诊断运行，但由于统计置信门会随采样误差改变，不属于这个严格
acceptance gate。QSCI++、FT-QPE Planner、Trust-QEM、q-sc-EOM、Q-Embed 和
kQ-PBC 的结果分别代表 selected-CI 精度、资源估计、mitigation provenance、
激发态审计、嵌入审计和 PBC k/twist 审计，不自动提升 validated chemistry
claim。`method_evidence_summary.json` 中的 `accuracy_outcome` 和
`promotion_boundary` 是当前最稳妥的机器可读结论入口。
`contract_matrix` 则检查每个方法是否至少有一个 case 同时覆盖
`result.method_evidence.methods`、方法详情字段、`method_evidence.json`、
`promotion_gate_audit.method_records`、`report.md`、QCSchema extras 和
benchmark metrics。`contract_matrix.status=complete` 只说明软件 surface
贯通，不表示方法精度或硬件性能已经优越。
这些 benchmark metrics 不只是占位字段：每个方法还必须暴露关键 trust-boundary
指标，例如 E-ADAPT 是否替换 delegated energy、OO-QCASSCF 是否替换 primary
energy、Q-Embed 是否执行 density matching、kQ-PBC 是否出现 proxy energy、
Trust-QEM PEC 是否可执行校准、FT-QPE 是否有 compiled circuit/surface-code
distance。缺少这些字段会使 `contract_matrix` 变为 incomplete。
Trust-QEM fast gate 现在包含两个 H2 cases：`h2_trust_qem` 保留
`missing_calibration_model` 边界，`h2_trust_qem_calibrated_pec` 读取
`configs/data/h2_pec_calibration_model.json` 并记录 executable PEC calibration
model、operation count、quasi-probability entry count 和 sampling overhead。
即使 calibrated PEC 可执行，`energy_replaces_primary` 仍为 false，accuracy 和
hardware claim 仍需独立 promotion gate。
`estimated_cost_advantage_pairs` 单独记录 measurement-planning 成本优势；
例如 `LiH E-ADAPT + Shadow-LR` 可以把估计测量 shot cost 从 grouped-estimator
基线降到配置的 shadow allocation budget，但这仍是本地规划指标，不是硬件校准或
化学精度胜出。

每个 method-evidence run 的 `method_evidence.json` 还包含
`promotion_gate_audit`。这个 audit 把方法证据拆成 accuracy claim、energy
replacement、hardware claim、planning metric 和 resource-model claim 五类：
v1 fast gate 中 `sidecar_energy_replacement_allowed_methods`、
`accuracy_claim_allowed_methods` 和 `hardware_claim_allowed_methods` 都应为空。
`promotion_gate_summary` 会在 suite 级别聚合这些字段，防止
QSCI post-correlation、Trust-QEM、Shadow-LR 或 FT-QPE 的 side evidence 被误读成
validated improvement。`estimated_cost_advantage_pairs` 保留所有配置导致的估计成本差异；
`planning_metric_cost_advantage_pairs` 只保留带有明确 planning/resource-model 方法证据
的成本优势，例如 Shadow-LR 或 FT-QPE Planner。
`method_superiority_audit` 进一步按方法拆分当前结论：accuracy advantage、
exact-match smoke、planning-cost advantage、resource-model-only advantage 和
promotion blockers 分开记录。这个字段是“优越性审计”，不是 promotion 结果；
当 `status=promotion_required` 时，任何 method-level advantage 都只能作为下一轮
promotion benchmark 的候选信号。

E-ADAPT v1 优先从 delegated chemistry ansatz 暴露的 mapped excitation
operators 构建 qubit-pool；当 ansatz 没有 excitation operators 时才回退到
Hamiltonian Pauli-term pool。adaptive optimizer 会记录有限差分梯度、小角
energy scan、ansatz-growth history 和 delegated-VQE warm-start polish。primary
solver energy 只有在 adaptive energy 比 delegated VQE 至少低过
`max(1e-10, gradient_threshold * finite_difference_step)` Hartree 时才替换；
更小的 optimizer drift 只进入 `adaptive_optimization` evidence，不作为精度优势。
单个 candidate operator 还必须在 adaptive optimization 后产生正的
`energy_lowering_hartree` 才会进入 `selected_operators`；未降能的候选以
`adaptive_optimization_no_improvement` 写入 `rejected_operators`，并通过
`e_adapt_no_improvement_rejection_count` 暴露给 benchmark contract。benchmark
同时记录 `e_adapt_optimization_signal_present`,
`e_adapt_adaptive_improvement_status`,
`e_adapt_delegate_improvement_to_replacement_threshold_ratio`,
`e_adapt_cumulative_selected_energy_lowering_hartree` 和
`e_adapt_final_cumulative_two_qubit_increment`。当 adaptive energy 有正向改善但
低于替换阈值时，`method_superiority_audit` 把 E-ADAPT 标为
`optimization_signal_requires_promotion`，不是 accuracy superiority。若同一案例还启用
Shadow-LR，测量成本优势会保留在 pair-level comparison 中；只有
`method_specific_estimated_cost_advantage_pair_names` 才会归因到某个方法自身。

q-sc-EOM v1 仍使用 exact-spectrum roots 作为 conditioning/reference audit，
但每个 root 会记录 residual norm、neighbor gap 和 degenerate-subspace
root-tracking 状态。H2 fast gate 中的近简并激发根应显示
`degenerate_subspace`，这提醒用户该路径是 root-conditioning evidence，不是已验证的
通用 EOM 求解器。若同一 run 请求 `tasks.properties` 中的
`transition_dipole` 或 `oscillator_strength`，q-sc-EOM sidecar 会记录
`transition_property_audit`、linked property count、state pairs 和最大 transition
dipole/oscillator-strength diagnostic；这些字段链接 exact property task 输出，不代表
q-sc-EOM 已实现通用响应性质求解。

Trust-QEM 的 benchmark metrics 还会记录 `trust_qem_requested_methods`,
`trust_qem_claim_allowed_methods`, `trust_qem_claim_status`,
`trust_qem_energy_replaces_primary`, 和 `trust_qem_pec_status`。v1 fast gate
允许记录 readout/ZNE/symmetry/PEC provenance，但不把 mitigated evidence 替换成
primary solver energy；PEC 没有可执行 `qcchem.pec_calibration_model.v1` JSON 时
保持 `unsupported_for_claim` / `missing_calibration_model`。

QSCI post-correlation 在该 suite 中是接口和 eligibility 审计：它记录
selected-CI coefficient digest、缺失的外部相关输入和 double-counting 状态，
并在 `qsci_tcc` 路径记录 audit-only selected-CI-to-single/double-amplitude
mapping。benchmark metrics 包括 `post_correlation_eligibility_status`,
`post_correlation_amplitude_mapping_status`,
`post_correlation_backend_executable`,
`post_correlation_correction_energy_emitted`, 和
`post_correlation_required_input_missing_count`。它不生成 proxy correction
energy；若没有可执行的 QSCI-derived TCC/NEVPT2 backend 和 double-counting
model，`external_correlation_energy` 和 `total_corrected_energy` 保持为空，
`trust_gate` 为 `unsupported_for_claim`。
QSCI++ 的 `variance_estimate` 来自 selected-CI Ritz vector 嵌入完整 qubit
Hamiltonian 后的 `<H^2>-<H>^2` 与 residual audit；`subspace_audit` 同时记录
sector coverage、external-coupling residual 和 variational upper-bound margin。
这些指标用于判断 selected-subspace 质量，不会替代 primary solver energy。
`selection_bias_audit` 还记录 selected determinant provenance：
`selected_origin_counts` 汇总 sampled、Hartree-Fock reference fallback 和
Hamming-expanded repair 来源，`selected_multi_origin_counts` 保留同一个
determinant 同时属于多个来源时的完整审计轨迹。

OO-QCASSCF 在该 suite 中记录 PySCF CASSCF orbital-relaxation reference
diagnostic、能量下降和 active-space re-solve 边界。CASSCF reference energy
不替代 primary delegated QCchem solver energy；benchmark metrics 会记录
`orbital_optimization_energy_replaces_primary=false` 和
`active_space_resolve_status=not_applied_to_primary_solver`。由于 PySCF
`CASSCF.e_tot` 是 molecular total energy，而 QCchem `solver_energy` 是 solver
Hamiltonian energy，suite 还记录
`orbital_optimization_energy_scope_consistent=true`、
`orbital_optimization_primary_total_energy_estimate` 和
`orbital_optimization_casscf_minus_primary_total_energy`，避免把不同能量口径直接
比较成“优越性”。suite 还记录
`orbital_optimization_promotion_readiness_status`,
`orbital_optimization_solver_replacement_allowed`,
`orbital_optimization_optimized_orbitals_applied`, 和
`orbital_optimization_primary_hamiltonian_rebuilt`，明确 v1 只做 reference
diagnostic，没有把 optimized orbitals 转入 primary Hamiltonian 并重新求解。

Q-Embed/q-DMET 在该 suite 中是 fragment-reference audit：可以执行 PySCF RHF/UHF
小片段参考诊断并记录 bath 推荐，但不运行 q-DMET self-consistency、density
matching 或 correlation-potential optimization。`fragment_energy_sum` 不替代
primary full-system energy，benchmark metrics 会记录这些边界字段。v1 还记录
full-system mean-field density 上的 fragment gross population audit：
`fragment_population_delta_norm`、`density_mismatch_l1_norm`、
`max_fragment_population_delta_abs`、AO/atom coverage fraction 和
`density_mismatch_audit_status` 都是 reference-only mismatch/coverage
diagnostics，不表示已经执行 q-DMET density matching。

kQ-PBC 在该 suite 中同样是 audit gate：配置可以请求非 Gamma/twist 元数据，
但执行路径仍是 Gamma reference Hamiltonian。`twist_energies` 中的 energy
status 应保持 `not_evaluated`，finite-size correction 也保持未评估；suite
明确检查不出现 `solver_energy_proxy_hartree` 这类 proxy 能量字段。`mesh_mismatch`,
`requested_kpoint_count`, `execution_kpoint_count`, 和 `promotion_blockers` 用来明确
requested non-Gamma/twist scope 与实际 Gamma execution scope 的差距。suite 还记录
`named_kpoint_coverage_fraction`、`mesh_kpoint_coverage_fraction`,
`twist_energy_coverage_fraction`, `missing_twist_energy_fraction`,
`promotion_readiness_status`, unsupported-claim count 和 blocker count，让
non-Gamma/twist promotion gap 可以被机器审计。

FT-QPE Planner 的 `toffoli_reduction_vs_double_factorization` 是
`coarse_pauli_l1_phase_estimation_scaling` resource-model finding。suite 同时记录
`ft_qpe_resource_claim_status=resource_model_only`、
`ft_qpe_resource_formula_scope`、
`ft_qpe_promotion_readiness_status`、
`ft_qpe_readiness_level=resource_model_only_not_compiled`、
`ft_qpe_reference_encoding`、
`ft_qpe_encoding_comparison_count`、
`ft_qpe_compiled_circuit_available=false`、
`ft_qpe_surface_code_distance_available=false`、
`ft_qpe_logical_error_budget_available=false`、
`ft_qpe_required_promotion_evidence_count` 和 `ft_qpe_promotion_blockers`。这些字段
必须和 reduction 一起解读：它能说明模型估算下的资源趋势，不能说明已有 compiled
fault-tolerant circuit 或硬件级资源优势。

## Method Promotion Probe

`benchmarks/method_promotion_probe_v1.yaml` 是 Method Evidence 的 promotion-prep
探针，不属于默认 release manifest。它使用 stretched H2 和 stretched H4 chain
对比 exact baseline 与 QSCI++ selected-subspace evidence，目的是检测单点 H2 smoke
之外的 selected-subspace 稳定性。

该 probe 的 comparison pair 优先使用方法专属误差，而不是 run 的 primary solver
误差。对于 QSCI++，`method_absolute_error` 来自
`abs(qsci_variational_upper_bound_margin_hartree)`；这能避免 `solver.kind=exact`
时 primary case 看起来 exact、但 selected-CI subspace 实际残差很大的误判。
当前 H2 stretched probe 可以达到 exact-match smoke。H4 stretched probe 会显式打开
QSCI++ residual-driven determinant expansion；该路径用外部 Ritz residual coupling
补充 determinant，可把 selected-subspace residual 降到数值零附近，但仍保持
`promotion_required`，因为这只是小体系 promotion-prep 信号，不是跨体系 validated claim。

## status 语义

- `validated`
  - 当前 case 已达到本轮接受标准
- `exploratory`
  - case 有正式 schema 和 artifact，但不能声称数值已验证
- `unstable`
  - case 可运行，但当前结果或统计表现还不稳
- `failed`
  - case 没达到基础要求

## 当前真实结果摘要

当前 suite artifact：

- `artifact`: `artifacts/benchmark_suite_v1`
- `total_cases`: `10`
- `status_counts`: `{'validated': 6, 'unstable': 4}`

当前 unstable 主要来自：

- H2 shot VQE
- H2 noisy comparison
- H2 shot scaling
- hardware-style shot statistics 相关子路径

## noisy comparison 的意义

`h2_noisy_comparison` 会同时记录：

- `exact_total_energy`
- `ideal_total_energy`
- `noisy_total_energy`
- `ideal_absolute_error`
- `noisy_absolute_error`
- `noisy_minus_ideal`

它的目的是把“能不能跑 noisy”与“noisy 偏移多大”分开表达，而不是把 noisy 路径混进普通单点 benchmark。

## QMMM environment embedding suite

`benchmarks/qmmm_environment_embedding_suite_v1.yaml` 是非共价
electrostatic embedding 的主线验证 benchmark。它包含两个
`qmmm_validation` case：

- `qmmm_environment_embedding_smoke`: validated smoke gate，覆盖 damped point
  charge、localized-boundary diagnostic、legacy alias、cache reload。
- `qmmm_environment_embedding_full`: validated full gate，继续覆盖
  charge/radius scan、active-space、compression、TC-QSCI、cavity-QED、LR-ACE
  surface。

该 suite 输出 `qmmm_validation.json`、`qmmm_validation.md`、`metrics.csv`，
并在 benchmark metrics 中提升以下资源账本：raw/executed qubit counts、
raw/executed Pauli-term counts、`pauli_term_delta_raw_to_executed`、
symmetry-reduction status、cache reload error、environment qubit growth。
MM environment 不被量子化；这些指标只描述嵌入后的 QM Hamiltonian 映射与
Z2 tapering 验证。

## PBC/PBC-QMMM suite

`benchmarks/pbc_qmmm_suite_v1.yaml` 是可执行的 Gamma-only PBC/PBC-QMMM
suite manifest。它包含两个 `pbc_qmmm_validation` case：

- `pbc_qmmm_smoke`: 运行 plain Gamma-only PBC、PBC-QM/MM Ewald，以及非
  Gamma k-point rejection。
- `pbc_qmmm_full`: 在 smoke 基础上增加 VQE/twolocal、active-space、
  compression、LR-ACE 和 TC-QSCI routing。

该 suite 的核心边界是：v1 只声明 Gamma-only/supercell PBC 和固定电荷
PBC-QM/MM Ewald；非 Gamma k-point mapped algorithms、forces/stress、
cell optimization、PME dynamics、polarization 和 MM relaxation 不在当前范围内。
同时要求 closed-shell RHF、fully periodic 3D cell、molecule/cell unit 一致、
full QM/MM cell 中性，并拒绝 uniform background、open-shell/UHF、runtime
submission 和 reduced-dimensional PBC flags。
可直接运行 `qcchem validation pbc-qmmm --profile smoke|full`，也可以通过
`qcchem benchmark run -c benchmarks/pbc_qmmm_suite_v1.yaml` 进入 benchmark
acceptance。

## Tag-filtered benchmark runs

Benchmark cases can carry tags such as `fast`, `slow`, `runtime_preview`, or
`full`. Use explicit tag filters when a suite contains both quick gates and
slow diagnostic cases:

```bash
qcchem benchmark run \
  -c benchmarks/lr_ace_flagship_suite_v1.yaml \
  --include-tag fast \
  -o artifacts/lr_ace_flagship_fast
```

Repeat `--include-tag` to select cases matching any listed tag. Repeat
`--exclude-tag` to skip cases carrying any listed tag:

```bash
qcchem benchmark run \
  -c benchmarks/lr_ace_flagship_suite_v1.yaml \
  --exclude-tag slow \
  -o artifacts/lr_ace_flagship_without_slow
```

The filter changes which cases run; it does not change case configs,
acceptance rules, energies, baselines, or trust-tier language. The resulting
`benchmark_result.json` records `calibration_summary.case_filter` and
`dashboard_summary.case_filter` with selected and skipped cases.
Benchmark suite outputs refuse to replace an existing non-empty directory by
default. Add `--overwrite` only when you intentionally want to replace the
previous aggregate bundle. The output guard refuses root/home paths, the
repository root, top-level `artifacts/`, and source-tree paths outside
`artifacts/` before creating or replacing outputs. It also rejects symlinked
output paths before overwrite deletion can follow the link.

## QFT / lattice-QED benchmark suites

QFT benchmark suites are exploratory by design. They are useful for finite-model
evidence, resource boundaries, and runtime-gate checks, but they do not promote
lattice-QED artifacts to continuum chemistry accuracy.

- `benchmarks/field_model_qft_smoke_v2.yaml`: CI-sized smoke suite for 2-site
  exact/sector/dynamics, 4-site sparse projected exact, a 2D plaquette smoke
  case, and disabled runtime preview.
- `benchmarks/field_model_qft_cutoff_grid_convergence_v1.yaml`: finite
  cutoff/grid scan over electric cutoff, spacing/softening, 2/4-site geometry,
  open/periodic boundary choices, and neutral/numeric charge sectors.
- `benchmarks/field_model_qft_dynamics_resource_v1.yaml`: Trotter step and 2D
  Wilson dynamics resource suite with incremental-vs-legacy dynamics checks and
  runtime preview gates.
- `benchmarks/field_model_qft_hardware_micro_v1.yaml`: guarded hardware micro
  preview; default is `submit_real_job: false`.
- `benchmarks/field_model_qft_hardware_micro_real_v1.yaml`: real-runtime micro
  template that must remain action-time budget gated and capped to a tiny
  observable/time-point set.

Acceptance for sparse exact QFT cases must read the three-layer accuracy fields:

- `finite_model_exactness`: internal exactness for the finite
  grid/cutoff/softening Hamiltonian.
- `continuum_chemistry_accuracy`: `not_claimed` unless convergence evidence is
  present.
- `hardware_accuracy`: `unavailable` unless a real Runtime/shot-based result is
  submitted and collected.

For sparse projected cases with `pauli_materialization=skipped`,
`quantum_evidence.json` must report `pauli_terms_available: false` and must not
invent a zero-coefficient identity Pauli Hamiltonian. Measurement group counts
and shot-cost fields must be labeled as sparse/exploratory estimates unless a
materialized hardware path exists.

## 设计原则

- benchmark case 必须落 artifact
- case status 必须诚实反映当前能力
- aggregate report 必须能从 JSON 再生成
- exploratory 或 unstable case 也必须有正式 schema，而不是临时脚本输出
- field-model case 必须保留 `field_model_registry.json`、
  `field_hamiltonian.json`、`field_observables.json`、`field_dynamics.json`、
  `field_constraints.json`、`field_resources.json`、`field_error_budget.json`
  这些 sidecar 指针；aggregate metrics 可以读取 compact summary，但不能丢失
  原始场模型证据文件。

## Acceptance Policy

`benchmark_suite.acceptance` 是 benchmark 的可信闭环 gate。默认规则是：

- 每个 case 的 `status` 必须匹配 `expected_status`
- 每个 case artifact 必须有 `result.json`
- suite 和 case 必须能提供 `evidence_summary`
- `hardware_verified=true` 的 case 必须有可读取的 `runtime_submission.json`
- runtime-derived chemistry miss 不允许被误升成 `promote_validated_result`

可用命令：

```bash
qcchem benchmark accept artifacts/benchmark_suite_v1/benchmark_result.json
```

输出 `acceptance_summary.json`，其中包含 `accepted`、`blocking_failures`、
`warnings` 和 `recommended_action`。

## 后续扩展

- 更丰富的 shot/noise/runtime benchmark
- 更强的 scan / task benchmark
- 更细化的 benchmark acceptance policy
