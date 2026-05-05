# QCchem Architecture

## Trust-First Release 主轴

QCchem 当前阶段的主抓手是 `Evidence Core`。这意味着：

- `run / benchmark / study / scan / hardware / AI` 必须用同一套证据语义表达结论
- workbench、report、CLI、AI Workspace 不再各自发明“主结论”
- 真机层保持“小而硬”的现实验证角色
- AI 默认扮演 `保守证据解释器`，而不是无门控执行器

这一阶段的完成标志不是功能数量，而是 `证据闭环完成`。

## 模块划分

`qcchem/core`
: QCchem 自有 schema，覆盖 run、task、study、benchmark、scan、noise、runtime、policy、capability、registry、aggregate result 与统一 `Evidence Summary`。

`qcchem/chem`
: 分子输入到 Qiskit Nature problem 的经典前处理，负责 active-space resolution、FreezeCore/remove-virtual reduction、Hamiltonian compression audit、classical plugin workflow，以及 reduction audit 所需信息。

`qcchem/mapping`
: fermion-to-qubit 映射、JW/BK 兼容层、H2 hardware precision push 使用的 parity two-qubit reduction，以及 Hamiltonian term counting。

`qcchem/solvers`
: ground-state solver 抽象与 exact spectrum utility。

`qcchem/exploratory`
: 显式隔离的实验性 solver / mitigation / benchmark 模块。它们可以落正式 artifact，但不会默认进入 validated 主链。
  当前包含 LR-ACE (`Low-Rank Adaptive Chemistry Eigensolver`) 原型：它从 mapped low-rank/compressed Hamiltonian 的 dominant non-diagonal factors 生成 compact real-mixing Pauli-evolution ansatz，并通过 QCchem evidence gate 标注为 exploratory。

`qcchem/backends`
: backend adapter、measurement planner、noise model helper、runtime/session-ready snapshot、runtime submission attempt helper、capability snapshot、execution policy defaults。

`qcchem/mitigation`
: mitigation schema、metadata、symmetry check hook、readout/ZNE/PEC placeholder。

`qcchem/workflow`
: run、study、benchmark、scan、task 编排、runtime collect/rehydrate、hardware optimization candidate planning 和 registry 写出。

`qcchem/reporting`
: run report 与 aggregate report 生成。

`qcchem/io`
: run/study/benchmark/scan config 解析与 serialization。

`qcchem/cli`
: 单点 run 与 aggregate workflow 的命令行入口。

`qcchem/workbench`
: Dash 驱动的本地 visual workbench，负责多页面工作台壳层、共享视觉系统、floating AI assistant、AI workspace page、结果页/聚合页组件，以及带有 `/overview` 默认路由、page inventory 和 artifact inventory 的 startup summary。
  在当前阶段，它承担 `Research Console` 角色，并按三层组织页面：
  - `Decision Pages`: Overview / Result Confidence / Studies / Benchmarks / Hardware Campaign
  - `Mechanism Pages`: Structure-Orbitals / Active-Space-Compression / Mapping-Resources-Circuit / Runtime Monitoring
  - `Operational Pages`: AI Workspace / runtime collect entry / 后续 Compose-Run

`examples/agents`
: 面向 Codex/OpenClaw 等终端代理的最小任务模板。

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
15. 构建 `Evidence Summary`，把 scientific claim、baseline、error metric、trust tier 和 recommended action 收成统一读口
16. hardware calibration suite 以 `runtime_submission` 为 authoritative runtime-evidence source 聚合 dashboard，并把 `hardware_verified` / `hardware_evidence_tier` 一起纳入导出和汇总

### Hardware Optimization

1. `qcchem hardware optimize --preview` 读取普通 `RunSpec` 加 `HardwareOptimizationSpec`
2. workflow 固定生成 H2 候选：
   - `jw_puccd_layout_baseline`
   - `parity_puccd_layout`
   - `parity_succd_layout`
   - `parity_uccsd_layout`
3. 每个候选先跑本地 VQE/exact baseline，只有 local chemical accuracy pass 的候选才可进入 runtime 队列
4. candidate planner 按 local pass、qubit 数、estimated 2Q gates、depth、layout score 排序
5. `--submit` 必须带 `--confirm-runtime-budget`，并且 budget ledger 会限制真实 jobs 与 total budgeted shots
6. `--collect` 复用 runtime collect/rehydrate，把真实 Runtime result 合并回候选 artifact
7. `Hardware Campaign` 页面显示 `Optimization Trial`，但继续把 `hardware_verified` 与 chemistry validated 分开

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

### Workbench

1. `qcchem workbench serve` 通过 `qcchem/workbench/server.py` 创建 Dash app
2. startup summary 统计 page inventory、default route 与真实 artifact 根目录盘面
3. 页面层复用 QCchem run/study/benchmark/scan schema 对齐的 view model
4. AI workspace page 从 `artifacts/ai_workspace/` 读取 ticket / delivery 记录，floating preview 通过 Dash callback 绑定当前请求输入
5. 当前工作台既服务人类用户，也为未来 AI 代理调用提供稳定入口语义

## 关键抽象

`RunSpec`
: 单次计算根配置，持有 molecule/problem/mapping/backend/solver/benchmark/mitigation/policy/tasks/run。

`HardwareOptimizationSpec`
: H2 hardware precision push 的预算与候选策略 schema，记录 `max_real_jobs`、`max_total_budgeted_shots`、`stop_if_error_below`、`candidate_strategies` 与 `requires_confirmation`。对应 workflow 现在还会持久化 empirical best attempt、prior hardware reference、delta vs reference、chemical-accuracy gap 和下一步预算建议，避免把重复候选机械送上真机。

`BackendSpec`
: 现在不只描述 `kind/shots/seed`，还持有 `noise` 与 `runtime` 子 schema。

`ReductionAuditSummary`
: 记录 reduction 前后系统规模、transformers、constant terms 与 energy formula。

`CompressionResultSummary`
: 记录 modified Cholesky / double factorization 的 method、rank、pre/post term count、reconstruction error、execution_enabled 与 verification status。

`LR-ACE metadata`
: 作为 `variational_result.ansatz.lr_ace` 持久化，记录 `low_rank_method`、`factor_rank`、`selected_factor_count`、`selected_generators` 与 `local_accuracy_gate`。它是 algorithm provenance，不替代 compression audit。

`MeasurementSummary`
: 记录 measurement strategy、group count、estimated shot cost、runtime precision target、execution mode，以及 compressed/uncompressed 的测量复杂度比较。

`CalibrationSummary`
: 记录 measured wall time、measured shot usage、achieved error，以及 estimated vs measured cost 的经验校准结果。

`RuntimeSubmissionSummary`
: 记录真实 runtime 提交尝试，包括 service、mode、options snapshot、returned job metadata 或认证/提交失败边界。
  对于 real hardware job，QCchem 现在会在 `job_id` 产生后立刻把这一段 sidecar 落盘，因此等待过程被打断时也不会丢失 runtime provenance。
  后续 `runtime collect` 会以这个 sidecar 为入口，把 provider 返回结果再并回 run artifact。

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
  当前它会显式区分 `chemical_accuracy` 和 `runtime_chemical_accuracy`，避免把“本地 solver 达标”和“真实 runtime 推导总能量达标”混成同一个判断。

`EvidenceSummary`
: 轻量证据摘要层，当前统一至少覆盖：
  - `result_identity`
  - `primary_scientific_claim`
  - `primary_baseline`
  - `primary_error_metric`
  - `chemical_accuracy_status`
  - `runtime_evidence_status`
  - `trust_tier`
  - `recommended_action`
  release-facing 术语 `baseline strength` 与 `hardware verification boundary` 继续作为 derived companion language 出现，而不额外扩成第二套顶层 schema。

`BaselineDescriptorSummary`
: comparison 口径描述层，显式记录：
  - `baseline_kind`
  - `baseline_source`
  - `baseline_scope`
  - `baseline_strength`

`hardware_verified`
: 表示真实 runtime result 已取回并写入 artifact 的证据位；它不等于 chemistry 数值已经通过 publication-grade 精度验证。

`decision_worthiness`
: 尤其用于 hardware aggregate 的行动判断层，回答当前 evidence 更适合：
  - `continue`
  - `pause`
  - `not_worth_additional_budget`
  - `needs_better_local_baseline_first`
  - `worth_one_more_controlled_attempt`

`hardware_evidence_tier`
: 对 hardware evidence 的来源分层；当前 hardware calibration 主要使用 `retrieved_result` 这类 tier。

`hardware_optimization`
: hardware optimization artifact section，记录 `candidate_id`、`selection_score`、local accuracy gate、compiled burden、runtime budget ledger 和 stop reason。

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
- `reduction / compression / correction` 不再只是附属审计块，而是正式并入证据链；最终 scientific claim 必须清楚落在哪一层成立。
- exploratory 模块采用单独包边界，而不是直接塞进主干 solver/mitigation 目录；这样我们可以持续完善实验能力，同时保持 validated 主链稳定。
- backend capability 和 execution policy 分离：
  - capability 回答“这个 backend 能做什么”
  - policy 回答“这次 run 想按什么标准执行和解释”
- visual workbench 复用同一套 schema/artifact 语言，而不是另造一套 UI 专用数据模型；这样 CLI、报告、AI task interface 和本地工作台始终围绕同一批证据对象组织
- AI workspace ticket / delivery state 也落在 `artifacts/ai_workspace/`，page render 只读这些持久化 JSON，不自行创造独立状态源
- AI 默认先消费 `Evidence Summary`，先解释 evidence 与边界，再在 ticket 门控下推进执行；这样 artifact 主链始终是权威来源。

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
- `hardware_verified`
- `hardware_evidence_tier`
- `mitigation`

这意味着 QCchem 已经能表达“准备好怎么接 runtime”，但还不能声称“已经验证远程执行”。

当前最新边界是：

- `qiskit-ibm-runtime` 已接入
- QCchem 会真实调用 `QiskitRuntimeService()` 并可提交最小 remote estimator job
- 一旦 job 成功提交，`runtime_submission.json` 会立即写出，保留 `job_id`、layout strategy、selected layout、transpiled depth、2Q gate count 和 runtime options snapshot
- 若运行过程被打断或需要稍后补回，`qcchem runtime collect <artifact-dir>` 可以基于已落盘 `job_id` 轮询 provider，并在结果就绪后补写 `result.json` 与 `report.md`
- 若缺少账户或权限，失败会以 `RuntimeSubmissionSummary` 形式落盘
- 一旦 job 成功，returned job metadata 与 result provenance 会进入 artifact
- 当前仍只验证到最小 hardware probe，不表示完整远端 chemistry workflow 已验证
- hardware calibration/dashboard 以 `runtime_submission` 为 authoritative runtime-evidence source；一个 case 是否被视为 hardware-verified，首先取决于真实提交与结果取回是否存在
- 当前 `artifacts/hardware_calibration_suite_v1` 的 runtime-derived achieved error 仍明显偏大：
  - H2 baseline runtime probe 约 `0.174 Ha`
  - H2 tighter UCCSD hardware push 约 `0.0468 Ha`
  - H2 compact `PUCCD` hardware push 约 `0.0537 Ha`

## Agent Interface 层

QCchem 当前没有单独起一个 HTTP 服务，而是在已有 CLI 和 artifact 之上增加了一层轻量 agent protocol：

- `qcchem agent validate-task`
- `qcchem agent run-task`
- `qcchem agent summarize`

这层接口的核心目标是：

- 让 AI 优先消费结构化 JSON，而不是二次解析 Markdown
- 让任务输入固定成 task schema，而不是让代理在会话里临时拼命令
- 继续复用已有 `run / benchmark / runtime collect` workflow，而不分叉出第二套执行引擎

当前支持的 agent task kind：

- `run_config`
- `runtime_collect`
- `benchmark_suite`
- `hardware_campaign_summary`

这类 task 会把执行结果重新整理成结构化 summary，供终端型 AI 代理继续消费，而不是要求代理直接解析报告正文。

`hardware_campaign_summary` 这类聚合任务仍然必须遵守 QCchem 现有的证据边界：

- `hardware_verified=True` 只表示真实 runtime 结果已取回
- 它不能自动等价于“真机 chemistry 精度已经达到 publication 标准”

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
