# QCchem Handoff

## Trust-First Release 状态

当前主线已经切到 `Trust-First Release`。这一阶段的完成标准不是页面数量或算法数量，而是 `证据闭环完成`：

- `run / benchmark / study / scan / hardware / AI` 围绕同一套 `Evidence Summary` 说话
- workbench、report、CLI、AI Workspace 使用同一套核心术语：
  - `best evidence`
  - `trust tier`
  - `baseline strength`
  - `chemical accuracy status`
  - `runtime evidence status`
  - `recommended action`
  - `hardware verification boundary`
- AI 默认姿态是 `保守证据解释器`
- 真机层继续保持“小而硬”的现实验证角色

## 本轮新增

- `Evidence Summary` 已进入核心 artifact 与 aggregate：
  - run
  - benchmark case / suite
  - study / run record
  - scan / scan point
  - hardware campaign summary
- `Evidence Summary` 当前至少统一表达：
  - `result_identity`
  - `primary_scientific_claim`
  - `primary_baseline`
  - `primary_error_metric`
  - `chemical_accuracy_status`
  - `runtime_evidence_status`
  - `trust_tier`
  - `recommended_action`
- comparison 语义已统一补上 baseline descriptor：
  - `baseline_kind`
  - `baseline_source`
  - `baseline_scope`
  - `baseline_strength`
- run report 已升级为固定阅读顺序：
  - `Evidence Summary`
  - `Claim`
  - `Chain`
  - `Proof`
- aggregate report 已统一增加 `Best Evidence`
- CLI `run / study / benchmark / scan` 现在会直接打印：
  - `Best evidence`
  - `Trust tier`
  - `Recommended action`
- AI summary / delivery 已开始复用 artifact 的 `Evidence Summary`
- hardware campaign summary 现在同时显式表达：
  - `evidence_summary`
  - `decision_worthiness`
- H2 hardware precision optimization 已新增受控入口：
  - `configs/h2_hardware_precision_push.yaml`
  - `qcchem hardware optimize --preview`
  - `qcchem hardware optimize --submit --confirm-runtime-budget "I understand IBM Runtime budget"`
  - `qcchem hardware optimize --collect`
  - 输出 `hardware_optimization_plan.json`、`hardware_optimization_report.md`、候选 run artifacts 与 campaign summary

## 发布级展示路径

当前推荐固定的 release showcase path：

1. `Overview`
2. `Result Confidence`
3. `Benchmarks`
4. `Hardware Campaign`
5. `AI Workspace`

这条路径对应 QCchem 当前最完整的“最佳证据 -> 边界解释 -> 推荐动作”叙事。

固定展示顺序也已落到 [release_showcase.md](/Users/a0000/QCchem/docs/release_showcase.md)。

## 本轮已完成

- 建立 qwen integration 的正式 design/spec/implementation plan
- 并入主干安全子集：
  - `chemical_accuracy`
  - `reduction_plan`
  - safe `policy_engine`
- 建立 exploratory schema gate：
  - `SolverSpec.experimental`
  - `PolicySpec.allow_exploratory`
  - `ExploratorySpec`
- CLI 新增 `qcchem exploratory run`
- 建立 `qcchem/exploratory/` 隔离包
- exploratory solver skeleton 已接入最小可运行路径：
  - `adapt_vqe`
  - `vqd`
  - `qse`
  - `iqpe`
  - `folded_spectrum`
- exploratory mitigation / benchmark definitions 已正式落模块与测试
- 把 low-rank measurement / runtime path 推进到 empirical calibration + real runtime submission attempt
- 新增 hardware calibration phase：
  - 真实 H2 / LiH runtime probe artifact
  - 统一 hardware calibration dashboard
  - export provenance 补充 `hardware_verified` / `hardware_evidence_tier`
  - provider `usage_estimation` / `job_metrics` 进入 runtime sidecar 与 dashboard
- 新增 `calibration` 正式 schema，记录：
  - measured wall time
  - measured shot usage
  - precision target
  - achieved error
  - estimated vs measured cost
- 新增 `runtime_submission` 正式 schema，记录：
  - service / mode
  - options snapshot
  - real runtime init attempt provenance
  - job metadata 或 failure boundary
- 已安装并接入 `qiskit-ibm-runtime`
- 当前环境下 QCchem 已完成一次真实 `QiskitRuntimeService()` job submission/result retrieval
- 当前环境下 tighter H2 hardware probe 已验证 budget-aware runtime calibration：
  - requested precision `0.05`
  - requested shot budget `1024`
  - provider usage `12 quantum seconds`
- 当前环境下又新增了两条更激进的 H2 hardware chemistry push：
  - `artifacts/h2_runtime_hardware_probe_ca`
    - `ibm_kingston`
    - `4096 shots`
    - runtime-derived error 约 `0.0468 Ha`
  - `artifacts/h2_runtime_hardware_probe_puccd`
    - `ibm_kingston`
    - `PUCCD` compact ansatz
    - `4096 shots`
    - runtime-derived error 约 `0.0537 Ha`
  - `artifacts/h2_runtime_hardware_probe_puccd_layout`
    - `ibm_kingston`
    - `PUCCD` + layout-aware runtime planning
    - selected layout `[44, 45, 46, 47]`
    - transpiled depth `146`, 2Q gates `42`
    - runtime-derived error 约 `0.0137 Ha`
- runtime submission robustness 已补强：
  - remote job 一旦提交，`runtime_submission.json` 会立即写出
  - 即使本地等待被打断，也会保留 `job_id`、layout、transpilation 与 runtime options provenance
- runtime collect/rehydrate 已正式落地：
  - `qcchem runtime collect <artifact-dir>`
  - 可以轮询已有 `runtime_submission.json`
  - 若 provider 结果就绪，则自动补写 `result.json`、`report.md`、`runtime_chemical_accuracy`
- AI agent interface 已正式落地：
  - `qcchem agent validate-task`
  - `qcchem agent run-task`
  - `qcchem agent summarize`
  - `examples/agents/*` 提供了可直接给 Codex/OpenClaw 复用的任务模板
  - `docs/agent_interface.md` 说明 task schema 与推荐调用顺序
  - `docs/hardware_runtime_campaign_report.md` 汇总了真实 IBM chemistry runtime campaign
- AI workspace 文档与示例已落地：
  - `docs/ai_workspace.md`
  - `examples/ai_workspace/provider.openai-compatible.yaml`
  - `examples/ai_workspace/tickets/analysis_h2_campaign.json`
  - workbench page 读取持久化 ticket state，floating preview 只镜像当前输入的 request 草稿
- visual workbench startup contract 已落地：
  - `qcchem workbench serve`
  - Dash 驱动的多页面 workbench 壳层
  - 页面顺序以 `/overview` 为 canonical landing route
  - workbench startup summary 现在会报告真实 page inventory、default route、artifact inventory 与页面总数
  - `docs/workbench.md` 记录了 workbench 启动路径、页面顺序与当前边界
- 当前有一个额外的 in-flight control case 已成功提交但尚未回收最终结果：
  - `artifacts/h2_runtime_hardware_probe_ca_layout/runtime_submission.json`
  - backend `ibm_kingston`
  - job_id `d7guiki2khts739p1pd0`
  - 已于后续 `runtime collect` 中成功回收
  - runtime-derived error 约 `0.0404 Ha`
- 当前又新增一条更激进的 H2 chemical-accuracy push，已成功提交并保留完整 sidecar：
  - `artifacts/h2_runtime_hardware_probe_puccd_layout_mitigated/runtime_submission.json`
  - backend `ibm_kingston`
  - job_id `d7guuejjne2c7393e7d0`
  - strategy: `layout-aware PUCCD + 8192 shots + DD + twirling + measure mitigation`
  - 已于后续 `runtime collect` 中成功回收
  - runtime-derived error 约 `0.2673 Ha`
- 当前又追加了一条最克制的 H2 chemical-accuracy push：
  - `artifacts/h2_runtime_hardware_probe_puccd_layout_highshots/runtime_submission.json`
  - backend `ibm_kingston`
  - job_id `d7h01qnb91ec73au3eag`
  - strategy: `layout-aware PUCCD + 8192 shots`
  - 已于后续 `runtime collect` 中成功回收
  - runtime-derived error 约 `0.0533 Ha`
- 当前新增 H2 硬件精度优化 preview artifact：
  - `artifacts/h2_hardware_precision_push/hardware_optimization_plan.json`
  - `artifacts/h2_hardware_precision_push/hardware_optimization_report.md`
  - 当前本地排序首选 `parity_puccd_layout`
  - H2/STO-3G 从 JW `4 qubits / 15 terms` 压到 parity two-qubit reduction `2 qubits / 5 terms`
  - preview 不提交真机；真实提交仍必须显式确认并逐个 collect
- 当前新增 H2 硬件精度优化真实 Runtime 结果：
  - campaign root: `artifacts/h2_hardware_precision_push`
  - `job_01_parity_puccd_layout_8192`: IBM job `d7qph0cf3ras73b64dcg`, backend `ibm_kingston`, depth `22`, 2Q gates `4`, runtime error `0.0182535 Ha`
  - `job_02_jw_puccd_layout_baseline_8192`: IBM job `d7qpl6cf3ras73b64hsg`, backend `ibm_kingston`, depth `149`, 2Q gates `42`, runtime error `0.0477009 Ha`
  - budget ledger: 2 real jobs, 16384 budgeted shots, `71.2595` estimated quantum seconds
  - stop reason: `pause_after_diverse_strategy_probe`
  - recommendation: do not spend the third job immediately; analyze hardware bias and mitigation strategy first
- 当前新增 QCchem-native exploratory algorithm：LR-ACE
  - full name: `Low-Rank Adaptive Chemistry Eigensolver`
  - implementation: `qcchem/exploratory/solvers/lr_ace.py`
  - local configs:
    - `configs/exploratory/h2_lr_ace.yaml`
    - `configs/exploratory/lih_active_lr_ace.yaml`
  - runtime config:
    - `configs/exploratory/h2_lr_ace_runtime.yaml`
  - local artifacts:
    - `artifacts/h2_lr_ace`
    - `artifacts/lih_active_lr_ace`
  - runtime artifacts:
    - `artifacts/h2_lr_ace_runtime_real`
    - `artifacts/h2_lr_ace_runtime_highshots`
    - `artifacts/h2_lr_ace_runtime_ultra`
  - suite summary:
    - `artifacts/lr_ace_suite_v1/lr_ace_summary.json`
    - `artifacts/lr_ace_suite_v1/lr_ace_report.md`
  - best local result: H2 error `4.78e-10 Ha`; LiH active-space error `6.62e-10 Ha`
  - best hardware result: H2 LR-ACE highshots error `0.001699 Ha`, just above chemical accuracy
  - current recommendation: pause Runtime spend and analyze hardware/mitigation bias before more shots
- 真实 hardware probe artifact：
  - `artifacts/h2_runtime_hardware_probe`
  - `artifacts/h2_runtime_hardware_probe_ca`
  - `artifacts/h2_runtime_hardware_probe_puccd`
  - `artifacts/lih_active_runtime_hardware_probe_v2`
- 真实 hardware calibration suite artifact：
  - `artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json`
  - `artifacts/hardware_calibration_suite_v1/hardware_calibration_report.md`
- 新增 calibration artifact：
  - `artifacts/lih_active_shot_runtime_ready_compressed/calibration.json`
  - `artifacts/lih_active_shot_runtime_ready_compressed/calibration_report.md`
- 新增 runtime submission artifact：
  - `artifacts/lih_active_shot_runtime_ready_compressed/runtime_submission.json`
- Low-rank Benchmark Suite v1 现在新增 calibration / dashboard 汇总：
  - `artifacts/low_rank_suite_v1/calibration_summary.json`
  - `artifacts/low_rank_suite_v1/calibration_report.md`

## 当前 validated 范围

- qwen integration 后的主干 schema/config boundary
- `chemical_accuracy` / `reduction_plan` / safe `policy_engine` 元数据路径
- H2 exact / statevector ground-state
- LiH exact
- LiH active-space VQE benchmark
- H2O(active-space) exact
- JW / BK consistency benchmark
- optimizer stability benchmark
- reduction audit artifact/reporting path
- freeze-core / auto-active-space audit path
- modified-Cholesky compression-aware execution
- compressed exact / ideal low-rank measurement planning
- empirical calibration artifact/report path
- real runtime submission probe artifact with returned job metadata
- hardware calibration dashboard artifact/report path
- artifact index helper / repo hygiene path
- workbench startup summary, page inventory, and `/overview` default route
- AI workspace docs/examples and persisted ticket visibility
- PySCF NEVPT2 classical-reference correction task
- LiH active-space compression benchmark suite
- low-rank benchmark suite exact / ideal cases
- study aggregation workflow
- 1D scan workflow
- exact-spectrum excited-state mini baseline
- dipole moment exact-expectation path

## 当前 exploratory 或 unstable 范围

- exploratory CLI / solver skeleton path
- H2 shot VQE
- H2 noisy local execution
- noisy comparison benchmark
- hardware-ready shot path
- LiH low-rank runtime-ready sampled path
- double factorization compression-aware execution
- embedding / fragmentation skeleton
- VQD 风格 excited-state interface
- transition dipole exact-derived path
- oscillator strength exact-derived path
- remote runtime submission path beyond placeholder，当前仅验证到最小 hardware probe
- hardware calibration dashboard 的 runtime-evidence 归因逻辑
- runtime/session-ready integration point
- low-rank runtime policy metadata layer
- 完整 mitigation implementation

## 当前未完成

- exploratory benchmark/study 的更深集成目前仍以显式隔离为主，尚未成为独立 aggregate workflow
- 还没有把完整 low-rank benchmark suite 接到真实远程 estimator primitive result
- 还没有验证多 case chemistry workflow 的远端 runtime 稳定性
- agent interface 目前是 CLI-first 协议层，不是 MCP server 或 HTTP service
- visual workbench 当前仍是 read-only preview layer；默认页面内容以 schema-driven curated view model 为主，深层 live artifact picker 仍在推进
- AI workspace page 现在会读取 `artifacts/ai_workspace/` 中的 ticket / delivery JSON，但它仍然不是任意 artifact 的通用编辑器
- floating AI assistant 现在有 `Reset` 位置恢复、标题 grip 双击恢复和 viewport clamp，自救坏的历史 localStorage 位置
- Evidence Console v2 已把 Overview / Runtime Monitoring / Hardware Campaign / AI Workspace 统一到 `best_evidence / trust_gap / runtime_boundary / open_tasks`
- `configs/h2_runtime_micro_probe_v2.yaml` 是受控 H2 micro runtime probe；它会提交真实 IBM Runtime job，执行前必须再次确认，且默认 `wait_for_result=false`
- `hardware_verified` 目前只代表真实 runtime result 已取回，不代表 chemistry 数值已验证到 publication-grade
- 当前 hardware calibration suite 的 runtime-derived achieved error 仍较大：
  - H2 baseline probe 约 `0.174 Ha`
  - H2 tighter UCCSD push 约 `0.0468 Ha`
  - H2 compact `PUCCD` push 约 `0.0537 Ha`
  - H2 layout-aware `PUCCD` push 约 `0.0137 Ha`
  - H2 layout-aware `UCCSD` push 约 `0.0404 Ha`
  - H2 layout-aware `PUCCD + DD/twirling/measure mitigation` push 约 `0.2673 Ha`
  - H2 layout-aware `PUCCD + 8192 shots` push 约 `0.0533 Ha`
  - LiH 约 `0.389 Ha`
- 到目前为止，最佳真实 H2 结果仍然是 `layout-aware PUCCD` 的 `0.0137 Ha`。更激进的 mitigation 组合和更高 shot budget 都没有继续改善它。
- 当前主干 artifact 已把 `chemical_accuracy` 与 `runtime_chemical_accuracy` 分开：
  - 前者回答本地 solver 路径是否达到 chemical accuracy
  - 后者回答真实 runtime 返回值推导出的总能量是否达到 chemical accuracy
- provider usage 已能通过 `runtime_submission.json` sidecar 补齐并进入 dashboard，但 chemistry 数值精度仍未达到 publication-grade
- mitigation 仍以 schema + metadata + hook 为主
- embedding 还没有 fragment solver execution，只到 DMET-style recommendation skeleton
- excited-state 还没有 validated VQD / qEOM implementation
- transition dipole / oscillator strength 还没有进入 validated property 集
- scan 目前只支持 1D bond-distance 模式
- campaign 目前落在 schema 层，尚未形成独立 workflow/CLI

## 建议下一步

1. 继续强化 `Evidence Core`，让更多 legacy artifact 自动补齐 baseline descriptor 与 recommended action
2. 把 Overview / Result Confidence / Benchmarks / Hardware Campaign 的 `best evidence` 联动继续收紧成真正的 artifact-driven 主控制台
3. 把 AI Workspace 的 delivery / history / provider persistence 做成更完整的作业系统，但继续保持 ticket 门控
4. 把真实 runtime probe 从单 case 扩到小规模 chemistry benchmark，同时继续坚持“小而硬”的 hardware layer
5. 为 runtime-ready sampled 路径补更稳的 shot allocation / grouping policy / resilience benchmark
6. 在不破坏当前证据闭环的前提下，再推进 embedding / excited-state / property 的 validated 边界

## 风险提醒

- local noisy model 目前只证明 QCchem 能走 noisy execution path，不证明它代表真实硬件
- 当前真实 runtime 只验证了最小 hardware probe，不应外推成整套 remote chemistry workflow 已验证
- hardware calibration suite 现在以 `runtime_submission` 作为 authoritative runtime-evidence source；它解决的是“有没有真实 runtime 结果”而不是“结果是否已经足够精确”
- hardware calibration suite 现在还会优先读取同目录 `runtime_submission.json` sidecar，以避免 run-level `result.json` 内嵌副本比 sidecar 更旧
- `hardware_verified=True` 只能读作“真实 runtime result retrieved”，不能读作“真机 chemistry benchmark 已数值达标”
- 当前 NEVPT2 是 classical plugin reference augmentation，不应当误读为量子原生后修正已验证
- `double_factorization` 与 embedding skeleton 已正式落 artifact，但仍是 exploratory
- QCSchema/HDF5 导出当前是 interoperability helper，不是外部标准完全认证声明
- property artifact 的总验证状态可能因为 exploratory property 被拉成 exploratory，因此必须看 property-level status
- ground-state validated 不会自动推出 excited-state/property validated
- 由于仓库尚无提交，artifact 的 `git_commit` 仍不是强 provenance 证据
- 仓库层面现在有 `python scripts/artifact_index.py artifacts` 这个轻量索引入口，适合做 artifact 盘点，但还不是完整 registry replacement
