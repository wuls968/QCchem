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
