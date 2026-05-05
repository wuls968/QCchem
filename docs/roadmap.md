# QCchem Roadmap

## v0.1

- 建立 Python package、CLI、统一 run schema
- 打通 molecule -> problem -> mapping -> solver -> report 的最小闭环
- 建立 exact baseline 与基础 artifact

## v0.2

- 建立 shot-based backend
- 显式拆分 exact / sampled / variational 结果口径
- 加入 mitigation hook 与统计不确定度表达
- 把 execution realism 纳入测试与 artifact

## v0.3

- 建立 Benchmark Suite v1
- 建立 Study / Registry / Campaign 风格 schema
- 实现 1D PES scan workflow
- 建立 backend capability / execution policy 层
- 建立 excited-state task skeleton
- 建立 property task skeleton
- 把 validated / exploratory / unstable / failed 边界显式写进结果和报告

## v0.4

- 建立 local noisy execution path
- 建立 noise model schema、noise provenance、noise comparison benchmark
- 建立 reduction audit
- 强化 property validation，区分 validated / exploratory / placeholder_only
- 建立 runtime-ready / session-ready / batch-ready metadata layer
- 建立 exact-spectrum excited-state mini suite

## v0.5

- 建立 active-space algorithm layer：
  - manual active space
  - auto active space recommendation
  - freeze core
  - remove-virtual schema
- 建立 reduction audit 的 orbital-level provenance
- 建立 Hamiltonian compression audit：
  - modified Cholesky
  - double factorization
- 建立 NEVPT2 perturbative correction task
- 建立 embedding / fragmentation formal skeleton

## v0.6

- compression-aware execution
- LiH active-space compression benchmark suite
- active-space + compression + NEVPT2 chained workflow
- stronger provenance with QCSchema-style / HDF5 exports

## v0.7

- low-rank measurement planning
- compression-aware runtime policy
- Low-rank Benchmark Suite v1
- stronger git/runtime provenance in artifacts and exports

## v0.8

- empirical calibration for low-rank execution
- real runtime submission attempt path
- low-rank execution dashboard / calibration report

## v0.9

- qwen integration hardening:
  - merge mature utilities into core path
  - isolate exploratory solvers/mitigation/benchmarks under explicit package boundaries
  - make exploratory CLI/reporting behavior first-class
- hardware calibration phase:
  - real H2 / LiH runtime probes
  - chemistry-informed compact hardware ansatz comparison for H2 (`UCCSD` vs `PUCCD`)
  - layout-aware hardware transpilation / qubit-selection heuristics for H2 chemistry pushes
  - unified hardware calibration dashboard
  - exports carrying `hardware_verified` / `hardware_evidence_tier` / `runtime_submission` provenance
  - separate `chemical_accuracy` vs `runtime_chemical_accuracy` semantics in run artifacts
  - immediate runtime sidecar persistence so queued remote jobs retain provenance before result retrieval
  - runtime collect / rehydrate command so submitted jobs can be merged back into artifacts later
- explicit docs boundary that `hardware_verified` means runtime result retrieved, not publication-grade chemistry validation
- CLI-first AI agent interface:
  - task schema for `run_config` / `runtime_collect` / `benchmark_suite` / `hardware_campaign_summary`
  - `qcchem agent` command group
  - agent-facing hardware runtime campaign summary/report
- AI workspace docs/examples:
  - `docs/ai_workspace.md`
  - `examples/ai_workspace/provider.openai-compatible.yaml`
  - `examples/ai_workspace/tickets/analysis_h2_campaign.json`
- successful remote runtime / session execution integration
- 更丰富的 noise model suite 与 mitigation experiment layer
- 更稳的 variational excited-state solver 路径
- 更多 validated property 路径
- geometry optimization workflow
- gradient / response property 路径
- 资源估计工作流
- 更完整的 campaign workflow
- 更系统的 benchmark acceptance policy

## v0.10

- Dash-driven local research workbench
- report-engine visual refresh
- startup artifact inventory and user-facing workbench path
- `qcchem workbench serve`
- floating AI workspace shell and task lanes
- `/overview` canonical landing route and ordered page inventory
- stronger bridge between CLI artifacts, reports, and visual analysis surfaces
- Evidence Console v2 shared decision model for Overview / Runtime Monitoring / Hardware Campaign / AI Workspace
- H2 runtime micro probe config with explicit budget cap and action-time confirmation metadata
- H2 hardware precision optimization:
  - `parity_two_qubit_reduction` mapping for two-qubit H2 workloads
  - hardware-aware candidate ranking before real runtime submission
  - budget ledger and explicit confirmation gate for IBM Runtime jobs
  - Hardware Campaign `Optimization Trial` section
  - first real optimization campaign submitted two controlled H2 probes; neither reached chemical accuracy, so the next milestone is bias-aware mitigation rather than more blind shots
- LR-ACE exploratory algorithm:
  - local exact-baseline gates now pass for H2 and LiH active-space with 2-qubit parity-reduced workloads
  - retrieved H2 hardware probes reached a best runtime error of `0.001699 Ha`, just above chemical accuracy
  - next milestone is bias-aware mitigation / calibration for LR-ACE rather than simply increasing shots
- 逐步从 curated page model 过渡到更完整的 artifact-driven browser

## v1.0 愿景

QCchem 成为一个面向真实研究活动的量子化学平台：

- 不只支持单点运行，也支持 benchmark、study、scan 和任务编排
- ground-state / excited-state / property / optimization workflow 共用统一 schema
- 可以在 validated 与 exploratory 边界清晰的前提下承载持续演化的研究平台能力

## Trust-First Release

当前主线不是继续平均扩功能，而是把 QCchem 收成发布级研究主力平台。这个阶段的完成标准是 `证据闭环完成`。

### Evidence Core

- 为 `run / benchmark / study / scan / hardware / AI` 统一 `Evidence Summary`
- 统一 `trust_tier / baseline descriptor / primary claim / primary error metric / recommended action`
- 保留严格 trust tier：
  - `validated`
  - `exploratory`
  - `unstable`
  - `hardware_verified`
- 把 `reduction / compression / correction` 正式并入证据链

### Research Console

- 把 workbench 收成 artifact-driven 主控制台
- 首页固定为“最佳证据优先”
- 固定 showcase path：
  - `Overview -> Result Confidence -> Benchmarks -> Hardware Campaign -> AI Workspace`

### AI Research Copilot

- AI 默认作为 `保守证据解释器`
- 先解释 evidence 与边界，再给 recommended actions，再在 ticket 门控下执行
- 浮动窗口负责快速提问与起单，AI Workspace 负责历史、lane、delivery 和审阅

### Hardware Verification Layer

- 继续保持“小而硬”的现实验证层
- 主输出不是更多 case，而是行动判断：
  - `continue`
  - `pause`
  - `not_worth_additional_budget`
  - `needs_better_local_baseline_first`
  - `worth_one_more_controlled_attempt`

### Release Surface

- 统一 README、report、CLI、workbench、AI、docs 的核心术语
- 明确 curated release artifacts
- 做适量清理，但不破坏真实研究痕迹
