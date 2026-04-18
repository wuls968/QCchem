# QCchem Handoff

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

1. 把真实 runtime probe 从单 case 扩到小规模 chemistry benchmark
2. 为 runtime-ready sampled 路径补更稳的 shot allocation / grouping policy / resilience benchmark
3. 为 NEVPT2 增加更多体系与 active-space benchmark，确认 correction 的稳定边界
4. 给 embedding 层接入一个真实 fragment solver plugin
5. 给 excited-state 增加一个真正可跑的 variational path
6. 把 workbench 从 curated preview 推进到更完整的 artifact-driven browser

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
