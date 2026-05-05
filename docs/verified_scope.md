# QCchem Verified Scope

## Trust-First Release 语义

当前 QCchem 的对外主语言已经统一到 `Evidence Core`。这意味着：

- 所有核心 artifact 默认先给出 `Evidence Summary`
- 默认主判断是严格 trust tier，而不是综合分数
- 当前统一使用的主术语包括：
  - `best evidence`
  - `trust tier`
  - `baseline strength`
  - `chemical accuracy status`
  - `runtime evidence status`
  - `recommended next action`
  - `hardware verification boundary`

当前 `Evidence Summary` 的 verified surface 已包括：

- `result_identity`
- `primary_scientific_claim`
- `primary_baseline`
- `primary_error_metric`
- `chemical_accuracy_status`
- `runtime_evidence_status`
- `trust_tier`
- `recommended_action`

## 已验证

- Evidence Core summary path for:
  - run artifacts
  - study aggregates
  - benchmark case / suite aggregates
  - scan point / scan aggregates
  - hardware campaign aggregates
- exploratory gating schema/config path
- `qcchem exploratory run` CLI boundary
- qwen core integration:
  - `chemical_accuracy`
  - `reduction_plan`
  - safe `policy_engine`
- H2 exact / statevector ground-state
- LiH exact
- LiH active-space VQE benchmark
- LiH freeze-core / auto-active-space reduction audit
- modified-Cholesky compression-aware execution
- compressed exact / ideal low-rank measurement planning
- empirical calibration artifact/report path
- real runtime submission probe artifact with returned job metadata
- hardware calibration dashboard artifact/report path
- budget-aware runtime calibration metadata path
- provider-usage-enriched runtime sidecar ingestion path
- immediate runtime-sidecar persistence after remote job submit
- runtime collect / rehydrate path from persisted `job_id`
- CLI-first AI agent task interface and JSON summary path
- AI workspace docs/examples and persisted ticket visibility
- workbench startup summary path:
  - page inventory
  - default route
  - artifact inventory rooted at repo `artifacts/`
- workbench page shell and report-visual language for:
  - overview
  - structure / orbitals
  - active space / compression
  - mapping / resources / circuit
  - runtime monitoring
  - result confidence
  - studies / benchmarks / scans / hardware campaign aggregate views
- PySCF NEVPT2 classical-reference correction task
- LiH active-space compression benchmark suite
- low-rank benchmark suite exact / ideal cases
- H2O active-space exact
- JW/BK consistency
- optimizer stability benchmark
- study aggregation artifact
- benchmark suite aggregate artifact
- 1D H2 bond scan workflow
- reduction audit artifact/report section
- exact-spectrum excited-state mini baseline
- dipole moment exact-expectation property path
- aggregate reports carrying explicit `Best Evidence` sections
- run reports carrying explicit `Evidence Summary / Claim / Chain / Proof` structure
- AI delivery and artifact summary path grounded in persisted artifact evidence instead of ad hoc text summarization
- Evidence Console v2 shared workbench model for best evidence, trust gap, runtime boundary, and open AI work
- runtime-monitoring decision cockpit that separates submission health from hardware-derived chemistry accuracy
- H2 runtime micro probe configuration path with explicit budget cap and action-time confirmation metadata
- H2 hardware precision optimization preview path:
  - `configs/h2_hardware_precision_push.yaml`
  - `qcchem hardware optimize --preview`
  - parity two-qubit reduction mapping for H2
  - local candidate ranking and runtime budget ledger
- H2 hardware precision optimization submit/collect mechanics:
  - two real IBM Runtime jobs were submitted and collected under `artifacts/h2_hardware_precision_push/`
  - `parity_puccd_layout`: depth `22`, 2Q gates `4`, runtime error `0.0182535 Ha`
  - `jw_puccd_layout_baseline`: depth `149`, 2Q gates `42`, runtime error `0.0477009 Ha`
  - this validates the runtime submission / sidecar / collect / budget-ledger loop, not the chemistry claim
- Runtime backend auto-selection now ranks available backends by layout-aware error score when no backend is pinned
- LR-ACE local exact-baseline gates:
  - `configs/exploratory/h2_lr_ace.yaml`: H2, 2 qubits, 1 parameter, local error `4.78e-10 Ha`
  - `configs/exploratory/lih_active_lr_ace.yaml`: LiH active-space, 2 qubits, 5 parameters, local error `6.62e-10 Ha`
  - these validate the local artifact/workflow gates, not the algorithm as a publication-grade general method

## exploratory

- explicit exploratory solver skeletons:
  - `adapt_vqe`
  - `vqd`
  - `qse`
  - `iqpe`
  - `folded_spectrum`
- exploratory mitigation metadata modules
- exploratory benchmark suite definitions
- double factorization compression-aware execution
- embedding / fragmentation schema and DMET-style skeleton
- VQD 风格 excited-state interface
- transition dipole exact-derived path
- oscillator strength exact-derived path
- campaign schema without full workflow
- runtime-ready / session-ready / batch-ready adapter layer
- low-rank runtime policy metadata layer
- real runtime submission path beyond placeholder, still limited to hardware probe scope
- H2 runtime micro probe execution itself until a confirmed real IBM Runtime submission is collected and merged
- further H2 hardware precision optimization attempts beyond the collected parity/JW probes; current recommendation is `pause_hardware_spend_and_analyze_bias`
- LR-ACE algorithmic claim beyond H2 and LiH active-space
- LR-ACE hardware chemistry claim:
  - retrieved IBM Runtime probes exist under `artifacts/h2_lr_ace_runtime_*`
  - best runtime error is `0.001699 Ha`, close to but above the `0.0016 Ha` threshold
  - current recommendation is `pause_runtime_spend_and_analyze_bias`
- AI-facing task protocol beyond the current CLI-first layer
- workbench as a full arbitrary-artifact live browser
- mitigation config and metadata layer beyond symmetry-check hook

## unstable

- H2 shot VQE
- H2 noisy local execution
- H2 noisy comparison benchmark
- H2 shot scaling benchmark
- hardware-ready shot path
- LiH low-rank runtime-ready sampled path

## failed

当前正式 suite 里没有 persistent failed case。若未来某 case 失败，它应保留在 benchmark artifact 中，而不是静默移除。

## runtime-ready / session-ready 的含义

当前 runtime/session-ready 表示：

- schema 已有正式能力位
- policy 已能表达 hardware/publication intent
- artifact 会落 capability snapshot 与 runtime options snapshot
- 低秩 workload 会落 measurement plan、grouping policy、precision target 与 session/batch recommendation
- runtime attempt 会落 options snapshot、failure category 或 returned job metadata
- backend API 设计已为未来 runtime adapter 预留接口

它不表示：

- 已系统性验证远程 runtime chemistry workflow
- 已验证真机数值可信度

## `hardware_verified` 的含义

当前 `hardware_verified` 表示：

- `runtime_submission` 显示发生了真实 runtime 提交，并且结果已成功取回
- artifact/export/dashboard 可以据此把该 case 归入 hardware-evidence 已取得的集合
- hardware calibration suite 以 `runtime_submission` 作为 authoritative runtime-evidence source
- 对于尚未回收完成的 real hardware job，QCchem 也会在提交成功后立刻写出 `runtime_submission.json` sidecar；这保证了 `job_id`、layout 和 transpilation provenance 不会因为本地等待中断而丢失
- 现在还可以对这类 in-flight artifact 执行 `qcchem runtime collect <artifact-dir>`，在 provider 可达时把真实结果补回到 `result.json` 与 `report.md`
- 即使 `hardware_verified=True`，artifact 仍会通过 `runtime_evidence_status` 与 `recommended_next_action` 表达后续判断，而不是默认为 chemistry claim 已 validated

它不表示：

- chemistry 总能量误差已经达到 publication-grade 或 chemical-accuracy 标准
- 整条远端 chemistry workflow 已经系统性验证完成
- 相同配置在别的 backend、时间点或 shot budget 下会稳定复现

当前已知边界：

- `artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json` 中，runtime-derived `achieved_error` 目前约为：
  - H2 baseline probe `0.174 Ha`
  - H2 tighter UCCSD hardware push `0.0468 Ha`
  - H2 compact `PUCCD` hardware push `0.0537 Ha`
  - H2 layout-aware `PUCCD` hardware push `0.0137 Ha`
  - H2 layout-aware `UCCSD` push `0.0404 Ha`
  - H2 layout-aware `PUCCD + DD/twirling/measure mitigation` push `0.2673 Ha`
  - H2 layout-aware `PUCCD + 8192 shots` push `0.0533 Ha`
  - LiH `0.389 Ha`
- tighter H2 hardware probes 当前能证明：
  - budget-aware runtime calibration 已显著改善 evidence quality
  - 更浅的 chemistry-informed ansatz 不一定自动带来更好的 runtime-derived total energy
  - 真实 open-instance hardware chemistry 目前仍未收敛到 chemical accuracy
  - layout-aware `PUCCD` 是当前最佳已回收 H2 结果，约 `0.0137 Ha`
  - 更激进的 mitigation 组合与更高 shot budget 并未继续改善当前最佳结果
- 因此 `hardware_verified=True` 目前只能解释为“真实 runtime result retrieved”，不能解释为“数值结果已可信到可发表 benchmark”

当前 artifact 语义也已经收紧：

- `chemical_accuracy`
  - 评估本地 solver 路径相对 exact baseline 的误差
- `runtime_chemical_accuracy`
  - 评估真实 runtime 返回值推导总能量后的误差
- 因此单个 artifact 可以同时出现：
  - `chemical_accuracy.meets_chemical_accuracy = True`
  - `runtime_chemical_accuracy.meets_chemical_accuracy = False`
  这不是矛盾，而是 QCchem 对 “local path” 与 “hardware-derived path” 的刻意分离

## AI Agent Interface 的当前边界

当前已经验证：

- `qcchem agent validate-task`
- `qcchem agent run-task`
- `qcchem agent summarize`
- task schema:
  - `run_config`
  - `runtime_collect`
  - `benchmark_suite`
  - `hardware_campaign_summary`
- `examples/agents/*` 可作为终端型 AI 代理的最小模板
- `docs/ai_workspace.md`
- `examples/ai_workspace/provider.openai-compatible.yaml`
- `examples/ai_workspace/tickets/analysis_h2_campaign.json`
- AI 默认优先解释 artifact `Evidence Summary` 与 trust tier，再起 analysis/execution ticket
- AI delivery 可以引用 artifact evidence 与 recommended next action

当前不表示：

- QCchem 已经提供 MCP server
- QCchem 已经提供长期运行的 HTTP service
- agent interface 会自动放宽 validated / exploratory / unstable 边界

## Workbench 的当前边界

当前已经验证：

- `qcchem workbench serve` 可以构建真实页面注册表并输出 startup summary
- workbench 首页默认围绕 `best evidence`、`trust map` 和 `recommended next action`
- workbench summary 会报告：
  - URL
  - pages
  - default route
  - artifact root
  - artifact inventory
- 报告视觉语言与 workbench 使用相同的结果叙事关键词：
  - `Report Cover`
  - `Hero`
  - `Evidence Summary`
  - `Claim`
  - `Chain`
  - `Proof`
  - `Chemical Accuracy Frame`
  - `Runtime Evidence`
  - benchmark / hardware campaign `Best Case`
  - aggregate-level `Best Evidence`

当前不表示：

- workbench 已经是任意 artifact 的完整动态浏览器
- 所有页面都已经直接绑定真实 artifact 查询
- workbench 页面上出现的所有内容都自动代表 validated chemistry evidence

当前最准确的说法是：

- workbench 已经是一个真实可运行的本地研究工作台预览层
- 它已经和 repo 内真实 artifact 盘面连上
- 但默认页面主体仍然以 schema-driven curated view model 为主，用来保证结构、视觉和证据语言先稳定下来

## mitigation-ready 的含义

当前 mitigation-ready 表示：

- mitigation config schema 已正式存在
- mitigation metadata schema 已正式存在
- symmetry check hook 已落位
- readout / ZNE / PEC 已有 placeholder 位置

它不表示：

- 已实现完整 mitigation 算法
- 已验证 mitigation 后的 publication-grade 结果

## noisy-ready 的含义

当前 noisy-ready 表示：

- 本地 Aer noisy execution path 已存在
- artifact 会落 noise model schema、参数与 provenance
- benchmark 可以比较 exact / ideal / noisy 三条路径

它不表示：

- 噪声模型已经代表真实硬件
- noisy 路径已经达到 publication-grade 数值可信度

## algorithm-ready 的当前边界

当前新算法层可以这样理解：

- active-space-ready
  - 已有 formal schema、auto/manual selection、freeze-core/remove-orbitals provenance
  - reduction audit 已进入 validated scope
- compression-ready
  - 已有 formal schema、artifact、report、rank/error metadata
  - `modified_cholesky` 当前属于 validated compression-aware execution
  - `double_factorization` 当前属于 exploratory compression-aware execution
- low-rank-measurement-ready
  - 已有 formal measurement schema、artifact、report、benchmark metrics
  - 当前 validated 范围限定在 compressed exact / ideal LiH active-space
  - runtime-ready sampled 路径目前仍是 unstable
- runtime-submission-ready
  - 已有 `qiskit-ibm-runtime` 接入与真实远端 job submission/result retrieval
  - 已有 provider `usage_estimation` / `job_metrics` provenance 落盘
  - 当前已验证范围限定在最小 hardware probe artifact
  - 更大 chemistry workflow 的远端执行仍不在 validated scope
- perturbative-correction-ready
  - 已有 `NEVPT2` formal task schema 与真实 artifact
  - 当前 validated 范围限定为 PySCF classical-reference plugin path
- export-ready
  - 已有 `qcschema.json` 与 `result.h5` 可选导出
  - `qcschema.json` extras 现在显式包含 `hardware_verified`、`hardware_evidence_tier`、`runtime_submission`
  - 当前定位为 interoperability / provenance helper
- artifact-index-ready
  - 已有轻量 artifact index builder 与脚本入口
  - 当前定位为 repo hygiene helper，不替代 study/benchmark registry
- embedding-ready
  - 已有 fragment schema、bath/environment metadata、formal artifact/report
  - 当前仍是 exploratory skeleton，不表示 validated DMET workflow
