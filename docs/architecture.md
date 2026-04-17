# QCchem Architecture

## 模块划分

`qcchem/core`
: QCchem 自有 schema，覆盖 run、task、study、benchmark、scan、noise、runtime、policy、capability、registry 与 aggregate result。

`qcchem/chem`
: 分子输入到 Qiskit Nature problem 的经典前处理，负责 active-space resolution、FreezeCore/remove-virtual reduction、Hamiltonian compression audit、classical plugin workflow，以及 reduction audit 所需信息。

`qcchem/mapping`
: fermion-to-qubit 映射、JW/BK 兼容层、Hamiltonian term counting。

`qcchem/solvers`
: ground-state solver 抽象与 exact spectrum utility。

`qcchem/exploratory`
: 显式隔离的实验性 solver / mitigation / benchmark 模块。它们可以落正式 artifact，但不会默认进入 validated 主链。

`qcchem/backends`
: backend adapter、measurement planner、noise model helper、runtime/session-ready snapshot、runtime submission attempt helper、capability snapshot、execution policy defaults。

`qcchem/mitigation`
: mitigation schema、metadata、symmetry check hook、readout/ZNE/PEC placeholder。

`qcchem/workflow`
: run、study、benchmark、scan、task 编排和 registry 写出。

`qcchem/reporting`
: run report 与 aggregate report 生成。

`qcchem/io`
: run/study/benchmark/scan config 解析与 serialization。

`qcchem/cli`
: 单点 run 与 aggregate workflow 的命令行入口。

## 当前数据流

### Run

1. CLI 或 workflow 读取 YAML 并解析为 `RunSpec`
2. policy defaults 合并到 backend/benchmark/mitigation 配置
3. `chem` 构建 `ElectronicStructureContext`
4. `chem` 同时生成 `reduction_audit`
5. `mapping` 生成 qubit Hamiltonian
6. `chem/compression.py` 构建 compressed fermionic Hamiltonian 与 compression audit
7. `backends` 解析 capability、measurement plan、noise snapshot、runtime snapshot
8. `solver` 生成 raw `solver_energy`
9. `workflow/runner.py` 恢复 `electronic_energy` 与 `total_energy`
10. 如适用，生成 exact baseline、sampled result、variational result
11. 可选 chemistry task / plugin section 执行：
   - perturbative correction
   - embedding / fragmentation skeleton
   - excited-state
   - property
12. 可选写出 QCSchema-style JSON / HDF5 export
13. 把 reduction/compression/measurement/plugin/noise/runtime/capability/policy/mitigation/task status 与 provenance 一并落盘
14. 如启用 runtime path，额外记录 empirical calibration 与 real runtime submission attempt

### Benchmark

1. `BenchmarkSuiteSpec` 注册 benchmark cases
2. 当前 case kind：
   - `run`
   - `consistency`
   - `shot_scaling`
   - `optimizer_stability`
   - `noise_comparison`
3. noisy comparison 会把 exact、ideal、noisy 三条路径放进同一 case metrics
4. suite summary 只聚合 case status，不重复解释 run 细节

### Study

1. `StudySpec` 组织多个 run config
2. workflow 逐个运行 run，并生成 `RunRecord`
3. 汇总 status、energy、artifact path、policy/backend/mapping 维度
4. 写 `study_result.json`、`study_report.md`、`registry.json`

### Scan

1. `ScanSpec` 定义 1D geometry parameter
2. 每个扫描点生成独立 run artifact
3. workflow 汇总 point table 和 scan summary
4. 写 `scan_table.csv`、`scan_result.json`、`scan_report.md`

## 关键抽象

`RunSpec`
: 单次计算根配置，持有 molecule/problem/mapping/backend/solver/benchmark/mitigation/policy/tasks/run。

`BackendSpec`
: 现在不只描述 `kind/shots/seed`，还持有 `noise` 与 `runtime` 子 schema。

`ReductionAuditSummary`
: 记录 reduction 前后系统规模、transformers、constant terms 与 energy formula。

`CompressionResultSummary`
: 记录 modified Cholesky / double factorization 的 method、rank、pre/post term count、reconstruction error、execution_enabled 与 verification status。

`MeasurementSummary`
: 记录 measurement strategy、group count、estimated shot cost、runtime precision target、execution mode，以及 compressed/uncompressed 的测量复杂度比较。

`CalibrationSummary`
: 记录 measured wall time、measured shot usage、achieved error，以及 estimated vs measured cost 的经验校准结果。

`RuntimeSubmissionSummary`
: 记录真实 runtime 提交尝试，包括 service、mode、options snapshot、returned job metadata 或认证/提交失败边界。

`PerturbativeCorrectionResultSummary`
: 记录 active-space energy、perturbative correction、corrected total energy 与 plugin provenance。

`EmbeddingResultSummary`
: 记录 fragments、bath/environment metadata、solver plugin interface 与 verification boundary。

`NoiseModelSummary`
: 记录 local noisy execution 的 profile、参数、basis gates 与 provenance。

`RuntimeOptionsSummary`
: 记录 runtime/session/batch-ready snapshot、low-rank workload flag、grouping policy、precision target、session/batch recommendation 和 runtime options。

`RunResult`
: 原子级 artifact；benchmark/study/scan/task 都围绕它组织。

`BackendCapabilitySummary`
: capability snapshot，回答 backend 是否 statevector、shot-based、noise-model-ready、runtime-ready、session-ready、batch-ready。

`ExecutionPolicySummary`
: policy snapshot，回答当前 run 是 benchmark / exploratory / publication / hardware_ready 哪种执行意图。

`ExcitedStateTaskResult`
: excited-state section，显式表达 task-level verification status。

`PropertyTaskResult`
: property section，显式表达 validated / exploratory / placeholder_only 的 property-level 状态。

## 为什么这样设计

- 保持 run 是平台里的原子单元，benchmark/study/scan 只做聚合，不复制业务逻辑。
- noise provenance、runtime snapshot、reduction audit 都落在 run artifact 里，避免研究活动层再发明自己的字段。
- property 和 excited-state 不是塞进 solver 里的“附加结果”，而是正式 task section；这让 ground-state validated 与 task-level exploratory 可以并存且不混淆。
- active-space / compression / perturbative / embedding 也遵循同一原则：能进入统一 schema 的能力统一落 schema，尚未 fully validated 的能力仍然落正式 artifact，但保留 exploratory 标签。
- exploratory 模块采用单独包边界，而不是直接塞进主干 solver/mitigation 目录；这样我们可以持续完善实验能力，同时保持 validated 主链稳定。
- backend capability 和 execution policy 分离：
  - capability 回答“这个 backend 能做什么”
  - policy 回答“这次 run 想按什么标准执行和解释”

## 能量口径

- `solver_energy`
  - 映射后 qubit Hamiltonian 的 raw solver energy
- `constant_energy_correction`
  - 非核常数修正，例如 active-space/inactive-space correction
- `electronic_energy`
  - `solver_energy + constant_energy_correction`
- `total_energy`
  - `solver_energy + constant_energy_correction + nuclear_repulsion_energy`
- `exact_ground_energy`
  - 同一 raw Hamiltonian 下的 exact baseline
- `energy_formula`
  - 随 artifact 一起落盘
- `reduction_audit`
  - 记录这些项来自哪类 reduction/transformer/correction

## Noise / Runtime / Policy 层

### Capability

当前 capability snapshot 至少覆盖：

- `statevector`
- `shot_based`
- `exact_baseline`
- `runtime_ready`
- `session_ready`
- `batch_ready`
- `mitigation_ready`
- `noise_model_ready`
- `supports_grouping`
- `supports_repetitions`
- `supports_confidence_metrics`

### Policy

当前 policy preset：

- `benchmark`
- `exploratory`
- `publication`
- `hardware_ready`

它们会影响：

- shot 默认值
- repetitions 默认值
- baseline expectation
- confidence interpretation
- mitigation posture
- runtime/session/batch/noise 的期望姿态

### Runtime-ready / Session-ready

当前 runtime adapter 层已经能做真实服务初始化尝试，并把结果或失败边界写入 artifact。artifact 会记录：

- `backend_capability`
- `execution_policy`
- `measurement`
- `runtime_options`
- `calibration`
- `runtime_submission`
- `mitigation`

这意味着 QCchem 已经能表达“准备好怎么接 runtime”，但还不能声称“已经验证远程执行”。

当前最新边界是：

- `qiskit-ibm-runtime` 已接入
- QCchem 会真实调用 `QiskitRuntimeService()` 并可提交最小 remote estimator job
- 若缺少账户或权限，失败会以 `RuntimeSubmissionSummary` 形式落盘
- 一旦 job 成功，returned job metadata 与 result provenance 会进入 artifact
- 当前仍只验证到最小 hardware probe，不表示完整远端 chemistry workflow 已验证

当 compression-aware execution 启用时，runtime snapshot 还会记录：

- `low_rank_workload`
- `grouping_policy`
- `precision_target`
- `measurement_group_count`
- `estimated_shot_cost`
- `session_recommendation`
- `batch_recommendation`

## Problem Reduction / Compression / Plugin 层

### Active-space and reduction

当前 reduction 路线统一由 `ProblemSpec` 驱动，支持：

- `freeze_core`
- `remove_orbitals`
- `active_space.selection_mode = manual | auto`
- `active_space.auto.strategy = frontier_orbitals`

artifact 会记录：

- reduction 前后粒子数与轨道数
- selected / frozen / removed orbitals
- selection reason
- transformers applied
- constant energy correction 与 energy formula

### Hamiltonian compression

当前 compression 层支持两条 execution-aware 路线：

- `modified_cholesky`
  - 当前可作为 validated compression-aware execution
- `double_factorization`
  - 当前保留为 exploratory compression-aware execution

这两条路径现在都会进入：

- compressed fermionic Hamiltonian reconstruction
- mapper
- qubit-operator truncation
- low-rank-aware measurement planning
- solver execution
- benchmark / report / provenance

其中 `compressed_vs_uncompressed` 会在 run artifact 中记录：

- rank
- threshold
- pre/post term count
- compressed/uncompressed energy difference
- compressed/uncompressed solve wall time

而 `measurement` section 会记录：

- group count
- estimated shot cost
- runtime precision target
- compressed/uncompressed measurement-cost ratio

### Perturbative correction

当前优先落地的是 `NEVPT2` correction task：

- plugin: `PySCF`
- 输入：active-space audit metadata
- 输出：reduced active-space energy、compressed active-space energy、perturbative correction、corrected total energy

这个路径当前被定义为：

- validated as a classical-reference correction plugin inside QCchem
- not yet a validated quantum-native post-active-space workflow

### Embedding / fragmentation

当前 embedding 层支持：

- fragment schema
- bath threshold
- environment metadata
- DMET-style recommendation skeleton

当前状态：

- schema / artifact / report: formal
- fragment solver workflow: exploratory plugin interface
- validated DMET platform: not yet

## Provenance / Export 层

当前 provenance 强化包括：

- `git_commit`
- `git_commit_short`
- `git_branch`
- `workspace_fingerprint`

当前可选导出包括：

- `qcschema.json`
- `result.h5`

这两条导出当前定位是：

- interoperability / reproducibility helper
- not a claim of full external-schema certification

## Task Model

### Excited-state

当前两条路径：

- `exact_spectrum`
  - small-system validated baseline
- `vqd`
  - exploratory skeleton
  - 当前用 exact-spectrum proxy 落 artifact，并明确标注

### Property

当前三层状态：

- `dipole_moment`
  - validated on small exact tasks
- `transition_dipole`
  - exploratory，exact-derived
- `oscillator_strength`
  - exploratory，exact-derived
- 其他未实现 property
  - placeholder_only

## Validated / Exploratory / Unstable 边界表达

QCchem 现在用正式字段表达边界：

- run 级 `verification_status`
- benchmark case `status`
- compression / perturbative / embedding section-level status
- excited-state task `verification_status`
- property entry `implementation_status`

这让 aggregate report 可以诚实地区分：

- validated
- exploratory
- unstable
- failed

## 后续扩展点

- remote runtime adapter 真正接入
- symmetry verification / readout mitigation / ZNE / PEC 的真实算法实现
- compression-aware solver execution
- validated perturbative corrections beyond the initial PySCF plugin path
- validated embedding / fragmentation workflow
- 更系统的 excited-state solver stack
- 更广的 validated property 路径
- 多参数 scan 与更完整的 campaign workflow
