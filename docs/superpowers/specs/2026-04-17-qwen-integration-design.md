# QCchem Qwen Integration Design

## Goal

把 qwen 版本中有价值的优化吸收到主项目 `/Users/a0000/QCchem`，同时保持 QCchem 已建立的 `validated / exploratory / unstable` 边界不被破坏。

这次集成不是代码搬运，而是一次研究级的平台整编：

- 成熟部分并入主干
- 探索性模块保留，但明确进入隔离层
- 数学/物理不够扎实的实现不直接并入执行主链
- 所有保留能力都必须继续服从现有 `schema / artifact / workflow / report / test` 体系

## Current Context

当前主项目已经具备以下稳定骨架：

- 统一 `RunSpec / RunResult` schema
- run/study/benchmark/scan 聚合工作流
- exact baseline、shot path、runtime submission probe、calibration artifact
- reduction audit、compression-aware execution、NEVPT2 plugin、low-rank measurement/runtime policy
- 明确的 `validated / exploratory / unstable` 边界表达

qwen 版本是在相近代码树上继续扩展，主要新增了：

- `chemical_accuracy` 工具层
- `reduction planner` 与 `policy engine`
- 更激进的 IBM backend 集成
- 多个新增 solver：`adapt_vqe / vqd / qse / iqpe / folded_spectrum / qsci / qsc_eom / wqte`
- 多个 mitigation 路径：`readout / zne / cdr / symmetry verify`
- 多个 advanced benchmark suite

问题在于，qwen 版本的新增项成熟度不一致。有些模块适合直接整合，有些只能作为 exploratory skeleton 保留，还有些实现会误导数值或物理可信度，不能直接进入主干执行链。

## Integration Principle

采用“双层集成”方案：

1. 主干层（core path）
   只承载能与现有 QCchem 可信度链路兼容的模块。

2. 探索层（exploratory path）
   保留未来可能有价值的 solver、mitigation、benchmark 与 workflow skeleton，但不默认参与主干 run/benchmark/study。

3. 重写优先于硬搬
   如果一个模块的接口方向值得保留，但数学/物理实现不够可靠，则保留 schema/入口思路，重写实现，不直接复制代码。

4. artifact-first
   所有保留能力都必须在 artifact 中清楚表达来源、边界和风险；exploratory 不是“隐藏能力”。

## Module Classification

### A 类：直接并入主干

这些模块方向成熟，且能与现有平台形成正交增强：

- `chemical_accuracy`
  - 作为统一误差口径工具并入主干
  - 与现有 `BenchmarkSummary` 对齐
  - 不再另起一套相互竞争的结果语义

- `reduction planner`
  - 并入为主干的 reduction recommendation layer
  - 强化 `ReductionPlanSpec / ReductionPlanResult`
  - 结果区分“推荐策略”与“实际采用的 reduction”

- `policy engine`
  - 并入为现有 `PolicySpec` 的解析增强层
  - 原则：显式用户配置优先，policy preset 不得偷偷覆盖用户手写值

- IBM/runtime metadata 补强
  - 吸收 backend discovery、backend info summary、session/batch/runtime metadata 捕获方式
  - 不替换现有已经跑通过的 runtime submission sidecar

### B 类：保留为 exploratory 子模块

这些模块可保留并继续完善，但不能进入 validated 主链：

- `adapt_vqe`
- `vqd`
- `qse`
- `iqpe`
- `folded_spectrum`
- `qsci`
- `qsc_eom`
- advanced solver comparison workflow
- advanced benchmark suites：
  - chemical accuracy suite definitions
  - scaling
  - spectroscopy
  - strong correlation
- mitigation 扩展方法：
  - `readout`
  - `zne`
  - `cdr`
  - `symmetry_verify`

这些模块将进入：

- `qcchem/exploratory/solvers/`
- `qcchem/exploratory/mitigation/`
- `qcchem/exploratory/benchmarks/`
- `qcchem/exploratory/workflow/`

### C 类：保留思路但重写实现

这些能力方向可留，但当前实现不直接并入：

- `chem/ansatz.py`
  - 尤其是 `k-UpCCGSD` 等实现目前更像启发式电路，不是严格的化学 ansatz 实现

- `chem/properties.py`
  - 若干性质实现是函数外形完整，但数值路径主要是 stub-only 实现或近似拼装

- `QSE` 中若干矩阵元与子空间构造
  - 当前实现存在物理含义和线性代数定义不够可靠的问题

- 一般 observable 的 readout mitigation
  - 当前对非对角 Pauli observable 采用了不够通用的近似

### D 类：不并入

- 参考值来源不清、口径混杂的 benchmark case
- 容易让用户误以为“已经 validated”的测试或说明
- 只有文件数量扩张价值、没有 artifact/workflow/schema 收益的总结文档

## Architecture Change

### New Exploratory Boundary

在现有架构上增加一个正式的探索层：

- `qcchem/exploratory/__init__.py`
- `qcchem/exploratory/solvers/`
- `qcchem/exploratory/mitigation/`
- `qcchem/exploratory/benchmarks/`
- `qcchem/exploratory/workflow/`

主干层继续保留当前职责：

- `qcchem/core/`
- `qcchem/chem/`
- `qcchem/backends/`
- `qcchem/mitigation/`
- `qcchem/solvers/`
- `qcchem/workflow/`

约束规则：

- `qcchem/solvers/` 只放 validated 或接近 validated 的主链 solver
- `qcchem/exploratory/solvers/` 承载实验性 solver
- exploratory 模块不得默认被 `run/study/benchmark` 主命令选中

## Schema Design

### Spec-side changes

在现有 schema 上增加最小边界表达：

- `SolverSpec.experimental: bool = False`
- `MitigationSpec.experimental: bool = False`
- `PolicySpec.allow_exploratory: bool = False`

新增可选 exploratory 配置块：

- `exploratory.enabled: bool`
- `exploratory.modules: list[str]`
- `exploratory.notes: list[str]`

用途：

- 明确用户是否允许本次运行走 exploratory 路径
- 明确启用了哪些探索模块
- 把探索行为从“隐式魔法”改成“显式选择”

### Result-side changes

`RunResult` 增加统一边界字段：

- `capability_tier: str`
  - `validated`
  - `exploratory`
  - `unstable`

- `module_origin: str`
  - `core`
  - `exploratory`

- `verification_notes: list[str]`
- `scientific_risk_notes: list[str]`

对 exploratory solver/property/mitigation 结果，要求额外记录：

- `implementation_status`
- `validation_scope`
- `scientific_risk_notes`

### Aggregate behavior

默认规则：

- `study`
  - 允许包含 exploratory run，但 summary 必须拆分统计
- `benchmark`
  - validated suite 默认不纳入 exploratory case
  - exploratory suite 单独生成 summary/report

## CLI Design

保留现有命令：

- `qcchem run`
- `qcchem benchmark run`
- `qcchem study run`
- `qcchem scan run`

新增独立 exploratory 命令组：

- `qcchem exploratory run`
- `qcchem exploratory benchmark`

行为约束：

- 普通 `qcchem run` 遇到 experimental solver/method 时默认拒绝
- 只有当 config 明确允许 exploratory，或调用 exploratory CLI，才进入对应模块
- CLI 输出必须明确显示：
  - `module_origin`
  - `capability_tier`
  - `validation boundary`

## Reporting Design

所有 report 增加统一 section：

- `Validation Boundary`
- `Module Origin`
- `Verification Notes`
- `Scientific Risk Notes`

若结果来自 exploratory 模块，报告顶部必须明确提示：

`This result is exploratory and is not part of the validated QCchem benchmark path.`

若 aggregate report 同时包含 validated 与 exploratory case，必须分开展示：

- validated summary
- exploratory summary
- mixed-scope caution note

## Testing Strategy

测试分三层：

### 1. `tests/unit`

覆盖：

- new schema fields
- parser / policy / registry behavior
- exploratory gating logic
- serialization / report rendering metadata

### 2. `tests/integration`

仅覆盖主干 validated workflow：

- existing run path
- benchmark path
- study path
- scan path
- runtime/calibration existing validated boundaries

### 3. `tests/exploratory`

覆盖 exploratory 模块的最小可用性：

- solver can run or fail gracefully
- artifact can be generated
- result is marked exploratory
- report includes validation boundary

这些测试不把“数值达到 chemical accuracy”作为默认目标，除非某条 exploratory 路线未来被提升到 validated。

## Implementation Phases

### Phase 1: Safe core integration

- 并入 `chemical_accuracy`
- 并入 reduction planner 的主干安全子集
- 并入 policy engine 的主干安全子集
- 补强 IBM/runtime backend metadata

### Phase 2: Exploratory scaffolding

- 建立 `qcchem/exploratory/` 目录结构
- 新增 exploratory config gate
- 新增 exploratory CLI 入口
- 新增 result/report 边界字段

### Phase 3: Exploratory migration

- 迁移 solver skeleton
- 迁移 mitigation skeleton
- 迁移 advanced benchmark suites
- 修正其 artifact/report/test 语义

### Phase 4: Documentation and scope hardening

- 更新 README、architecture、handoff、verified_scope
- 增加 exploratory usage documentation
- 明确哪些功能是 future-hardening candidates

## Out of Scope

本轮不做：

- 直接把所有 qwen solver 数值链路宣布为成熟
- 重新设计 QCchem 主架构
- 完整重写所有 advanced algorithms
- 把 exploratory benchmark 混入 validated baseline suite

## Success Criteria

本轮设计成功的标准是：

- 主项目吸收 qwen 中真正成熟的部分
- exploratory 模块被正式保留，而不是散落或删除
- validated 主链不被污染
- 用户从 config、CLI、artifact、report 都能清楚看出边界
- 后续可以在 exploratory 层持续完善 solver/mitigation，而不需要再次拆主干
