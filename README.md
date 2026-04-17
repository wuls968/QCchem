# QCchem

QCchem 是一个面向计算化学研究流程的量子化学平台雏形。它基于 Qiskit、Qiskit Nature 与 primitives V2，目标不是“再做一个单点 VQE demo”，而是把 `run -> benchmark -> study -> scan -> task` 统一到可复现、可审计、可比较的 artifact 工作流里。

## 项目简介

- QCchem 自己掌握 schema、artifact、workflow 和 validated/exploratory/unstable 边界。
- 当前平台重点是数值口径、执行真实性和研究活动组织能力，而不是算法数量。
- 每次运行都会落 `result.json`、`report.md`、`resolved_config.yaml`、`run.log`，并记录依赖版本、随机种子、时间戳和 capability snapshot。

## 设计目标

- 先把最小闭环和可信口径做扎实，再向更复杂的化学任务扩展。
- 让 ground-state、benchmark、study、scan、excited-state、property 共用统一结果模型。
- 面向化学研究者表达问题，而不是只暴露量子算法内部细节。
- 为 noisy execution、runtime、mitigation、激发态、性质、几何扫描保留正式接口。

## 当前支持的 Task

- `ground_state`
  - validated: H2 exact/statevector、LiH exact、H2O(active-space) exact、LiH active-space VQE
  - validated: LiH freeze-core / active-space auto reduction audit、modified-Cholesky compression-aware execution、PySCF NEVPT2 classical-reference correction
  - validated: compressed exact / ideal LiH active-space low-rank measurement planning
  - exploratory: double factorization compression-aware execution、DMET-style embedding skeleton、remote runtime submission path with real attempt provenance
  - unstable: H2 shot、H2 noisy、hardware-ready shot path、LiH low-rank runtime-ready sampled path
- `excited_state`
  - validated: small exact-spectrum baseline artifact
  - exploratory: VQD 风格接口仍使用 exact-spectrum proxy
- `property`
  - validated: dipole moment exact-expectation path
  - exploratory: transition dipole、oscillator strength 的 exact-derived path
  - placeholder only: 其他未实现 property 名称
- `study`
  - validated workflow: 多 run 聚合、registry、Markdown/JSON 汇总
- `benchmark`
  - validated workflow: Benchmark Suite v1 registry、aggregate report、case status
- `scan`
  - validated workflow: 1D bond-distance PES scan、point artifact、scan table

## 当前能力

- Qiskit Nature 电子结构 problem 构建与 active-space 支持
- ActiveSpace / FreezeCore / remove-virtual unified schema
- active-space auto recommendation 与 reduction audit provenance
- Jordan-Wigner / Bravyi-Kitaev 映射
- compression-aware execution：
  - modified Cholesky compressed solve
  - double factorization compressed solve
  - compressed vs uncompressed benchmark comparison
  - low-rank-aware measurement planning
  - estimated measurement-cost comparison
- NEVPT2 perturbative correction task
- embedding / fragmentation schema 与 DMET-style skeleton workflow
- `VQE` 与 `exact/reference` ground-state workflow
- statevector、shot-based、local noisy shot backend
- exact baseline、sampled result、variational result 三条结果口径
- backend capability snapshot 与 execution policy layer
- runtime-ready / session-ready / batch-ready metadata snapshot
- low-rank runtime policy snapshot：
  - precision target
  - resilience level
  - grouping policy
  - session / batch recommendation
- empirical calibration：
  - measured wall time
  - measured shot usage
  - achieved error
  - estimated vs measured cost
- runtime submission attempt artifact：
  - service init / auth boundary
  - options snapshot
  - returned job metadata or failure provenance
- mitigation metadata、symmetry check hook、readout/ZNE/PEC placeholder
- reduction audit：
  - reduction 前后系统规模
  - active-space metadata
  - active-space selection mode / reason
  - selected / frozen / removed orbitals
  - transformer 列表
  - constant energy correction 与 energy formula
- Benchmark Suite v1
- Low-rank Benchmark Suite v1
- Study / Registry / Campaign 风格 schema
- 1D PES scan workflow
- excited-state mini artifact
- property validation artifact
- CLI：
  - `qcchem run`
  - `qcchem report`
  - `qcchem inspect`
  - `qcchem study run`
  - `qcchem study report`
  - `qcchem benchmark run`
  - `qcchem benchmark report`
  - `qcchem scan run`
- `qcchem scan report`
- `qcchem exploratory run`

## Validated 与 Exploratory 边界

- 默认 `qcchem run` 只面向主干 validated / stable workflow。
- 如果配置显式声明了实验路径，普通 `run` 会拒绝执行，必须使用 `qcchem exploratory run` 或在 policy 中显式允许。
- exploratory 结果会继续落完整 artifact，但报告顶部会明确标注它不属于 validated QCchem benchmark path。

## 当前限制

- `qiskit-ibm-runtime` 已接入并完成一次真实远程 job submission/result retrieval；当前验证仍限于最小 hardware probe，不代表整条 runtime workflow 已 fully validated。
- `hardware_verified` 的含义很窄：它只表示 QCchem 从真实 runtime job 拿回了结果，并且 `runtime_submission` 记录显示提交/取回链路成功；它不表示该 chemistry 数值结果已经过 publication-grade 精度验证。
- 当前 hardware calibration suite 以 `runtime_submission` 作为 authoritative runtime-evidence source；dashboard 是否把一个 case 记为 `hardware_verified=True`，首先取决于是否存在真实提交并成功取回结果，而不是取决于误差是否足够小。
- 当前 `artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json` 里，runtime-derived `achieved_error` 仍然偏大：H2 约 `0.245 Ha`，LiH 约 `0.389 Ha`。这说明当前 scope 是“真实 runtime 结果已取回并被平台记录”，不是“真机 chemistry 精度已达可发表标准”。
- noisy execution 目前是本地 Aer noise model，不是真机噪声表征。
- mitigation 目前只有 schema、metadata 和 hook，没有完整 readout / ZNE / PEC 算法。
- `modified_cholesky` 已进入 compression-aware execution 与 low-rank measurement planning，但还不是完整 low-rank measurement theory/runtime platform。
- `double_factorization` 当前是 exploratory compression-aware execution，不应当视为已验证的低秩执行路径。
- embedding / fragmentation 当前是 formal skeleton；fragment solver 仍是 plugin interface，不是 validated DMET platform。
- NEVPT2 当前走 PySCF classical plugin path，适合作为 active-space 外修正的 reference augmentation，不等同于量子-经典统一求解已验证完成。
- excited-state 的 validated 范围目前只覆盖 small exact-spectrum baseline，不包含 validated VQD/qEOM。
- transition dipole 和 oscillator strength 目前属于 exploratory exact-derived 路径，不应当视为 publication-grade property benchmark。
- 仓库尚无提交，因此 `git_commit` 仍可能为 `null`；当前会同时记录 `git_describe`、`git_branch`、`git_status_summary` 和 `workspace_fingerprint`。

## 安装方法

推荐直接复用已有 conda 环境 `qiskit`：

```bash
conda activate qiskit
pip install -e ".[dev]"
pip install -e ".[runtime]"
```

## 使用方法

单次 run：

```bash
qcchem run -c configs/h2.yaml
qcchem run -c configs/h2_noisy.yaml
qcchem run -c configs/lih_active_space_auto.yaml
qcchem run -c configs/lih_compression_cholesky.yaml
qcchem run -c configs/lih_compression_double_factorization.yaml
qcchem run -c configs/lih_nevpt2.yaml
qcchem run -c configs/lih_embedding.yaml
qcchem run -c configs/lih_active_shot_runtime_ready_compressed.yaml
qcchem run -c configs/lih_active_runtime_hardware_probe.yaml
qcchem run -c configs/h2_property_validation.yaml
qcchem run -c configs/h2_excited_mini.yaml
qcchem run -c configs/h2_hardware_ready.yaml
```

study：

```bash
qcchem study run -c configs/studies/mini_comparison.yaml
qcchem study report artifacts/mini_comparison_study/study_result.json
```

benchmark：

```bash
qcchem benchmark run -c benchmarks/benchmark_suite_v1.yaml
qcchem benchmark report artifacts/benchmark_suite_v1/benchmark_result.json
qcchem benchmark run -c benchmarks/low_rank_suite_v1.yaml
qcchem benchmark report artifacts/low_rank_suite_v1/benchmark_result.json
```

scan：

```bash
qcchem scan run -c configs/scans/h2_short_scan.yaml
qcchem scan report artifacts/h2_short_scan/scan_result.json
```

配置检查：

```bash
qcchem inspect -c configs/h2_noisy.yaml
qcchem exploratory run -c configs/exploratory/h2_vqd.yaml
```

## 输出说明

Run artifact 至少包含：

- `resolved_config.yaml`
- `result.json`
- `exact_result.json`
- `report.md`
- `run.log`

Run `result.json` 当前关键 section 包括：

- `energy`
- `exact_baseline`
- `sampled_result`
- `variational_result`
- `benchmark`
- `backend_capability`
- `execution_policy`
- `noise_model`
- `runtime_options`
- `runtime_submission`
- `hardware_verified`
- `hardware_evidence_tier`
- `measurement`
- `calibration`
- `reduction_audit`
- `compression_result`
- `perturbative_correction_result`
- `embedding_result`
- optional `qcschema.json`
- optional `result.h5`
- `excited_state_result`
- `property_result`
- `mitigation`
- `provenance`

导出边界：

- `qcschema.json` 的 `extras` 现在会显式带出 `hardware_verified`、`hardware_evidence_tier` 与 `runtime_submission`，用于跨工具保留 hardware execution provenance。
- `result.h5` 继续按完整 QCchem result 结构落盘，因此同样保留 top-level `hardware_verified` / `hardware_evidence_tier` 和 `runtime_submission` group。

Benchmark artifact 至少包含：

- `benchmark_result.json`
- `benchmark_report.md`
- `registry.json`
- `cases/*`

Study artifact 至少包含：

- `study_result.json`
- `study_report.md`
- `registry.json`
- `runs/*`

Scan artifact 至少包含：

- `scan_result.json`
- `scan_report.md`
- `scan_table.csv`
- `registry.json`
- `points/*`

## Benchmark Suite v1

当前 suite 包含 10 个正式 case：

- H2 exact
- H2 statevector VQE
- H2 shot VQE
- H2 noisy comparison
- LiH exact
- LiH active-space VQE
- H2O active-space exact
- JW/BK consistency
- shot scaling benchmark
- optimizer stability benchmark

当前真实 suite artifact：

- artifact: `/Users/a0000/QCchem/artifacts/benchmark_suite_v1`
- status counts: `validated=6`, `unstable=4`

`h2_noisy_comparison` 会明确给出：

- `exact_total_energy`
- `ideal_total_energy`
- `noisy_total_energy`
- `ideal_absolute_error`
- `noisy_absolute_error`
- `noisy_minus_ideal`

## Low-rank Benchmark Suite v1

当前 low-rank suite 聚焦 LiH active-space 的 low-rank execution / measurement / runtime path：

- exact uncompressed
- exact compressed
- ideal VQE uncompressed
- ideal VQE compressed
- sampled runtime-ready compressed

真实 suite artifact：

- artifact: `/Users/a0000/QCchem/artifacts/low_rank_suite_v1`
- status counts: `validated=4`, `unstable=1`

它会显式比较：

- `compression_pre_term_count` / `compression_post_term_count`
- `compression_rank`
- `measurement_group_count`
- `estimated_measurement_cost`
- `measured_shot_usage`
- `estimated_vs_measured_cost`
- `precision_target`
- `achieved_error`
- `runtime_submission_status`
- `runtime_service`
- `wall_time_seconds`
- `absolute_error`

## 如何判断一个结果是否可信

- 先看 `verification_status`
- 再看 `benchmark` 和 `exact_baseline`
- shot/noisy 结果要结合：
  - `sampled_result.standard_error`
  - `sampled_result.confidence_interval_*`
  - `benchmark.within_uncertainty`
- active-space 或 transformer 结果要看：
  - `reduction_audit`
  - `energy.energy_formula`
  - `energy.constant_energy_correction`
- excited-state 和 property 结果必须单独看：
  - `excited_state_result.verification_status`
  - `property_result.verification_status`
  - `property_result.properties[*].implementation_status`

## Validated / Exploratory / Unstable 边界

Validated：

- exact/reference 小体系 ground-state
- H2 statevector VQE
- LiH active-space VQE
- reduction audit artifact/reporting path
- freeze-core / auto-active-space audit path
- modified-Cholesky compression-aware execution
- compressed exact / ideal low-rank measurement planning
- empirical calibration artifact/report path
- PySCF NEVPT2 classical-reference correction task
- LiH active-space compression benchmark suite
- low-rank benchmark suite exact / ideal cases
- real runtime submission probe artifact with returned job metadata
- exact-spectrum excited-state mini baseline
- dipole moment exact-expectation path
- study / benchmark / scan aggregate workflow

Exploratory：

- double factorization compression-aware execution
- DMET-style embedding / fragmentation skeleton
- VQD 风格 excited-state interface
- transition dipole exact-derived path
- oscillator strength exact-derived path
- runtime/session-ready adapter layer
- low-rank runtime policy metadata layer
- real runtime submission path beyond placeholder, still limited to hardware probe scope
- 完整 mitigation algorithm integration

Unstable：

- H2 shot VQE
- H2 noisy local execution
- H2 noisy comparison benchmark
- hardware-ready shot path
- shot scaling benchmark
- LiH low-rank runtime-ready sampled path

## 路线图

- `v0.1`: 最小闭环、统一结果对象、CLI、exact baseline
- `v0.2`: shot-based backend、sampled/variational/exact 口径、mitigation hook
- `v0.3`: benchmark suite、study/registry、scan workflow、task model、capability/policy
- `v0.4`: noise-aware chemistry platform，包含 local noisy execution、reduction audit、property validation、runtime/session-ready metadata、excited-state mini suite
- `v0.5`: active-space algorithm layer、Hamiltonian compression audit、NEVPT2 correction task、embedding/fragmentation skeleton
- `v0.6`: compression-aware execution、compression benchmark suite、active-space+compression+NEVPT2 chain、QCSchema/HDF5 provenance export
- `v0.7`: low-rank measurement planning、compression-aware runtime policy、Low-rank Benchmark Suite v1、强化 git/runtime provenance
- `v0.8`: empirical calibration、real runtime submission attempt path、low-rank execution dashboard
- `v0.9`: 成功的远程 runtime job submission、更多 validated excited-state/property 路径、geometry optimization、更系统 mitigation
- `v1.0`: 面向真实研究活动的噪声感知量子化学工作台

详细文档：

- [docs/architecture.md](docs/architecture.md)
- [docs/benchmark_suite.md](docs/benchmark_suite.md)
- [docs/study_registry.md](docs/study_registry.md)
- [docs/task_model.md](docs/task_model.md)
- [docs/verified_scope.md](docs/verified_scope.md)
- [docs/roadmap.md](docs/roadmap.md)
