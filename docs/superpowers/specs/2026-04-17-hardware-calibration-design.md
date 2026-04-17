# QCchem Hardware Calibration and Minimal Real Runtime Design

## Goal

在现有 `/Users/a0000/QCchem` 仓库上，把 QCchem 从“已经具备 runtime-ready 与 calibration artifact 的平台”推进到“具备少量但高价值的真实硬件验证样例的平台”。

这轮不追求铺很多新算法，也不追求大规模真机实验，而是用用户当前每月约 10 分钟的 IBM Quantum 额度，换取最值得留下的研究级证据链：

- 至少两个真实化学硬件样例
- 一条统一的 hardware calibration / dashboard 汇总链
- 一套清楚的 `validated / exploratory / unstable / hardware-verified` 边界表达

## Current Context

当前 QCchem 已经具备：

- ground-state / benchmark / study / scan 主工作流
- exact baseline、shot-based backend、runtime submission sidecar
- active-space / reduction audit / compression-aware execution
- low-rank measurement planning 与 runtime policy
- empirical calibration artifact
- exploratory 隔离层与明确的 capability tier

当前仓库里已经存在一个真实远程 runtime chemistry probe：

- `artifacts/lih_active_runtime_hardware_probe/`

这个 artifact 说明：

- IBM Runtime SDK 已经能初始化与提交最小真实 job
- QCchem 能把返回结果、job metadata 与 runtime provenance 写入 artifact

但当前仍有几个明显缺口：

1. 真实硬件样例数量太少，缺乏“可比较”的 chemistry evidence
2. 当前 calibration 更偏单点，没有形成 hardware dashboard
3. 低秩 measurement / runtime 路径虽然能估计成本，也有少量 measured data，但还没有用一组更一致的真实样例来校准
4. 文档层还没有把“hardware-verified scope”说得足够清楚

## User Constraint

用户当前给出的核心约束：

- 可以使用已经配置好的 IBM 真实量子计算资源
- 每月约有 10 分钟额度
- 不需要刻意省到过头
- 但必须确保这 10 分钟主要花在最有价值的测试上，而不是零散 demo

因此，本轮必须围绕“少量但高可信”的策略设计，而不是追求样例数量最大化。

## Design Principle

### 1. Hardware time is for evidence, not exploration

真机时间只用在能够直接强化主项目可信度的 case 上，不用在“顺便试试看”的 exploratory placeholder 上。

### 2. Use classical and ideal paths to de-risk hardware runs

每一个真机 case 在提交前，都应先有本地 exact / ideal / sampled 对照链，避免把硬件额度浪费在明显不稳的参数组合上。

### 3. Keep chemistry tasks tiny but meaningful

真机 case 只选最小但有化学意义的体系，不做大型、排队风险高、结果解释困难的任务。

### 4. Promote measured data into first-class provenance

真实 wall time、returned job metadata、shots usage、precision target 与 achieved error 必须进入统一 schema 与 dashboard，而不是只留在 log。

## Scope

本轮只做三条交付主线：

1. `H2 hardware probe`
2. `LiH active-space compressed hardware probe`
3. `hardware calibration and dashboard`

明确不优先做：

- GUI
- 更多 excited-state 名字
- 更多 placeholder property
- 大型真机扫描
- 多 backend 横向大规模跑分

## Approaches Considered

### Approach A: Single-system deep hardware campaign

只围绕 `LiH active-space compressed` 做多次重复和 policy 扫描。

优点：

- calibration 统计更扎实
- 更容易把 low-rank runtime 路径讲深

缺点：

- 样例覆盖太窄
- 用户明确希望“多做一些例子”

### Approach B: Two chemistry probes plus one calibration chain

选择两个最小化学体系：

- `H2`
- `LiH active-space compressed`

然后把它们统一纳入 hardware calibration / dashboard。

优点：

- 在预算内最均衡
- 同时强化“基础 chemistry path”和“QCchem 差异化 low-rank path”
- 对 README / verified scope / benchmark 报告最有价值

缺点：

- 统计重复度不如单一体系深挖

### Approach C: Many lightweight hardware examples

尽量多做 case，每个只跑一次。

优点：

- 表面覆盖面更广

缺点：

- 容易把预算切得太碎
- 很难形成真正有说服力的 benchmark 结论

### Recommendation

采用 `Approach B`。

它最符合用户对“深度优化项目 + 多做一些真机例子 + 精准使用 10 分钟额度”的组合目标。

## Hardware Budget Strategy

本轮按“预算上限导向”管理，而不是无限提交直到碰运气。

### Planned hardware package

1. `H2 hardware probe`
   - 目标：提供一个极小、稳定、易解释的真实 chemistry hardware evidence
   - 提交次数：1 到 2 次
   - 预算：约 2 到 3 分钟

2. `LiH active-space compressed hardware probe`
   - 目标：验证 `active-space + compression + low-rank measurement/runtime`
   - 提交次数：1 到 2 次
   - 预算：约 4 到 5 分钟

3. `calibration overhead / rerun reserve`
   - 用于一次必要的补跑或更稳的 repeated submission
   - 预算：约 2 到 3 分钟

### Stop rules

一旦满足以下条件之一，就停止进一步真机提交：

- 两个主 case 都已生成可用 artifact
- runtime queue unexpectedly grows enough to threaten the remaining budget
- 新的 submission 不再明显增加证据价值

## Architecture Changes

### New hardware experiment layer

在不重写现有架构的前提下，增加一个轻量的 hardware experiment registry 概念，仍然依附于现有 run/benchmark/report 系统：

- run 结果中保留单次 hardware probe
- benchmark 聚合中新增 hardware dashboard summary
- calibration summary 支持多 artifact 汇总

不新增一整套全新的平台层；而是在既有：

- `workflow/runner.py`
- `workflow/benchmark.py`
- `reporting/markdown.py`
- `reporting/aggregate.py`

之上做增强。

## Schema Design

### Run-level additions

在现有 result schema 基础上，补强下列 measured 字段与 runtime provenance：

- `hardware_verified: bool`
- `hardware_evidence_tier: str | null`
  - `probe`
  - `benchmark`
  - `comparison_only`

- `calibration.measured_wall_time_seconds`
- `calibration.measured_shot_usage`
- `calibration.precision_target`
- `calibration.achieved_error`
- `calibration.estimated_vs_measured_cost`

- `runtime_submission.service`
- `runtime_submission.mode`
- `runtime_submission.backend_name`
- `runtime_submission.job_id`
- `runtime_submission.session_id`
- `runtime_submission.batch_id`
- `runtime_submission.returned_job_metadata`
- `runtime_submission.result_provenance`

其中大部分字段已存在，本轮重点是：

- 统一口径
- 确保两个新 hardware artifact 都真正填满这些字段

### Benchmark-level additions

benchmark summary 增加 hardware comparison 视图：

- `comparison_kind`
  - `ideal_vs_runtime`
  - `sampled_vs_runtime`
  - `uncompressed_vs_compressed_runtime`

- `estimated_measurement_cost`
- `measured_shot_usage`
- `measured_wall_time_seconds`
- `precision_target`
- `achieved_error`
- `estimated_vs_measured_cost`
- `runtime_service`
- `hardware_verified`

## Workflow Design

### 1. H2 hardware probe workflow

路线：

`molecule -> problem -> mapper -> exact baseline -> ideal reference -> runtime submission -> calibration -> report`

设计目标：

- 保持 qubit count 和 ansatz complexity 极小
- 报告中把 H2 作为“最小 chemistry hardware verified probe”

边界：

- 如果结果能稳定回到合理误差范围，标记为 `hardware_verified benchmark`
- 如果只证明了 runtime path works，但数值误差偏大，则仍保留为 `probe` 或 `unstable`

### 2. LiH active-space compressed hardware probe workflow

路线：

`auto/manual active-space -> reduction audit -> compression -> low-rank measurement plan -> runtime submission -> calibration -> report`

设计目标：

- 让 QCchem 最有特色的一条主线真正有硬件证据
- 形成 `ideal vs sampled vs runtime` 的 compression-aware 对照

边界：

- 即使 runtime 数值不够稳，也必须保留 artifact
- 但 capability tier 要如实保留 `exploratory` 或 `unstable`

### 3. Hardware calibration dashboard workflow

基于两个 run artifact 与现有 low-rank suite，生成一个统一 dashboard：

- 每个 case 的 exact / ideal / sampled / runtime 对照
- precision target vs achieved error
- estimated cost vs measured cost
- grouping policy / resilience level
- runtime backend / job metadata summary

输出：

- `hardware_calibration_summary.json`
- `hardware_calibration_report.md`

## Reporting Design

### Run report

每个 hardware run 的 `report.md` 新增明确 section：

- `Hardware Execution`
- `Returned Runtime Metadata`
- `Calibration Summary`
- `Validation Boundary`

### Aggregate dashboard

新增一个更偏“执行面板”的汇总报告，重点回答：

1. uncompressed vs compressed 有没有真实执行收益迹象
2. ideal vs sampled vs runtime 的偏差各是多少
3. precision target 是否达成
4. estimated cost 和 measured cost 差了多少
5. 哪些结果已经可以算 `hardware-verified`

## Validation Boundary

本轮定义新的边界表达：

### `validated`

表示：

- exact / ideal / sampled 路径在现有标准下可信
- 不自动意味着已经通过真实硬件验证

### `hardware-verified`

表示：

- 有真实 IBM Runtime artifact
- 有 returned job metadata
- 有 exact / ideal 对照链
- 结果误差与不确定度至少达到本轮定义的“可接受 benchmark/probe”标准

### `exploratory`

表示：

- runtime 通路或 chemistry workflow 已经真实跑过
- 但数值质量、统计量或比较口径还不足以进入 validated hardware scope

### `unstable`

表示：

- 路径是通的
- 但当前误差、不确定度或 runtime 行为还不足以支持更强结论

## Testing Strategy

优先做轻量、平台逻辑导向的测试，不引入需要真机才能通过的 CI 依赖。

### Unit tests

覆盖：

- hardware calibration summary aggregation
- runtime submission metadata persistence
- hardware verification status derivation

### Integration tests

覆盖：

- H2 hardware config parsing and report regeneration
- LiH compressed hardware config parsing and benchmark comparison serialization
- dashboard generation from stored artifacts

### Manual real-hardware verification

真实硬件提交不纳入自动化测试，而是作为受控 manual verification：

- 运行前确认 backend availability
- 控制 submit count
- artifact 必须完整落盘

## Files To Touch

预计主要修改：

- `qcchem/core/results.py`
- `qcchem/workflow/runner.py`
- `qcchem/workflow/benchmark.py`
- `qcchem/workflow/calibration.py`
- `qcchem/reporting/markdown.py`
- `qcchem/reporting/aggregate.py`
- `qcchem/io/exports.py`
- `configs/`
- `benchmarks/`
- `tests/unit/`
- `tests/integration/`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/handoff.md`
- `docs/verified_scope.md`

## Success Criteria

本轮完成后，QCchem 应满足：

1. 有至少两个新的真实 IBM hardware chemistry artifact
2. 至少一个 H2 hardware probe 能成为稳定的最小化学真机证据
3. LiH active-space compressed 路线有真实 runtime artifact 与 calibration
4. benchmark/report 能统一比较 ideal / sampled / runtime
5. 文档清楚回答“哪些属于 hardware-verified，哪些还只是 exploratory/unstable”

## Out of Scope

- 大规模真机 benchmark 矩阵
- 多台机器 systematic comparison
- 真机上的 excited-state 平台
- 真机上的复杂 mitigation 套件评估
- 新的 GUI 或可视化前端
