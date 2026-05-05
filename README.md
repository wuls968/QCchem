# QCchem

QCchem 是一个面向计算化学研究流程的量子化学平台雏形。它基于 Qiskit、Qiskit Nature 与 primitives V2，目标不是“再做一个单点 VQE demo”，而是把 `run -> benchmark -> study -> scan -> task` 统一到可复现、可审计、可比较的 artifact 工作流里。

当前主线已经进入 `Trust-First Release` 阶段：QCchem 不再把“更多功能”当成第一目标，而是围绕同一套 `Evidence Core` 收紧 run、benchmark、study、scan、hardware 和 AI 的结论语言。

## 项目简介

- QCchem 自己掌握 schema、artifact、workflow 和 validated/exploratory/unstable 边界。
- 当前平台重点是数值口径、执行真实性和研究活动组织能力，而不是算法数量。
- 每次运行都会落 `result.json`、`report.md`、`resolved_config.yaml`、`run.log`，并记录依赖版本、随机种子、时间戳和 capability snapshot。
- 当前所有核心 artifact 都开始围绕统一的 `Evidence Summary` 工作：先回答“结果是什么、跟谁比、差多少、为什么可信、下一步该做什么”，再下钻完整 payload。

## 设计目标

- 先把最小闭环和可信口径做扎实，再向更复杂的化学任务扩展。
- 让 ground-state、benchmark、study、scan、excited-state、property 共用统一结果模型。
- 面向化学研究者表达问题，而不是只暴露量子算法内部细节。
- 为 noisy execution、runtime、mitigation、激发态、性质、几何扫描保留正式接口。
- 把 workbench、报告、CLI 和 AI Workspace 收成同一种 evidence-driven 产品语言，而不是四套并行叙事。

## Trust-First Release

这一阶段的完成标准不是“功能更多”，而是 `证据闭环完成`。QCchem 当前以 5 条主线收口：

- `Evidence Core`
  - 所有核心 artifact 统一到 `Identity / Energy Evidence / Comparison Evidence / Execution Evidence / Trust Judgment`
  - 所有入口优先消费轻量 `Evidence Summary`
- `Research Console`
  - workbench 首页优先回答 `best evidence`、`best case`、`trust map` 和 `recommended next action`
  - `Evidence Console v2` 将 Overview、Runtime Monitoring、Hardware Campaign 和 AI Workspace 收成同一套 `best_evidence / trust_gap / runtime_boundary / open_tasks` 决策语言
- `AI Research Copilot`
  - AI 默认是 `保守证据解释器`，先解释 evidence 与边界，再起 ticket，再执行
- `Hardware Verification Layer`
  - 真机层继续保持“小而硬”的现实验证位，不扩成大而散的 benchmark 场
  - 新增 `configs/h2_runtime_micro_probe_v2.yaml` 作为极小 H2 Runtime probe 入口；它默认要求 action-time confirmation，目标是验证 submission/sidecar/collect provenance，不承诺 chemical accuracy
  - 新增 `configs/h2_hardware_precision_push.yaml` 作为 H2 硬件精度优化入口；它先通过 parity two-qubit reduction 和硬件候选排序压缩 workload，再在显式确认后最多顺序提交 3 个真实 Runtime jobs
- `Release Surface`
  - README、report、CLI、workbench、AI 和 docs 使用同一套核心术语

## Evidence Core

QCchem 当前把结果对象升级成证据对象。所有核心 artifact 都会优先给出一层统一的 `Evidence Summary`，至少包含：

- `result_identity`
- `primary_scientific_claim`
- `primary_baseline`
- `primary_error_metric`
- `chemical_accuracy_status`
- `runtime_evidence_status`
- `trust_tier`
- `recommended_action`

在 release-facing 页面和报告里，`Evidence Summary` 还会配套两类衍生 companion field：

- `baseline_strength`
  - 用来说明当前 baseline 在这个比较语境里有多强
- `hardware verification boundary`
  - 用来提醒 `hardware_verified` 只代表真实 runtime/hardware result 已取回，不自动等于 chemistry claim 已 validated

同时，trust judgment 继续坚持严格分层，而不是引入综合分数：

- `validated`
- `exploratory`
- `unstable`
- `hardware_verified`

其中：

- `chemical_accuracy_status`
  - 回答本地 solver 路径相对 baseline 的 scientific accuracy
- `runtime_evidence_status`
  - 回答真实 runtime/hardware evidence 到了哪一层
- `recommended_action`
  - 回答该结果下一步最合理的研究动作，例如：
    - `promote_validated_result`
    - `review_runtime_gap`
    - `collect_runtime_result`
    - `compare_against_best_evidence`
    - `not_worth_additional_budget`

### 术语映射

QCchem 当前对外尽量统一使用一套固定词汇；内部 schema 名称与对外语言的对应关系如下：

| 对外术语 | 主要 schema / 字段 |
| --- | --- |
| `best evidence` | `evidence_summary.primary_scientific_claim` + aggregate ranking |
| `trust tier` | `evidence_summary.trust_tier` |
| `baseline strength` | `evidence_summary.primary_baseline.strength` |
| `chemical accuracy status` | `evidence_summary.chemical_accuracy_status` |
| `runtime evidence status` | `evidence_summary.runtime_evidence_status` |
| `recommended next action` | `evidence_summary.recommended_action` |
| `hardware verification boundary` | `hardware_verified` + `hardware_evidence_tier` + `runtime_submission` provenance |

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
- H2 硬件精修用 `parity_two_qubit_reduction` 映射，可把 H2/STO-3G 从 JW 的 `4 qubits / 15 terms` 降到 `2 qubits / 5 terms`
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
- budget-aware runtime calibration：
  - precision-driven or shot-budget-driven runtime policy
  - provider-reported usage seconds / quantum seconds
  - requested precision / requested shot budget provenance
- runtime submission attempt artifact：
  - service init / auth boundary
  - options snapshot
  - returned job metadata or failure provenance
  - usage estimation / job metrics when the provider exposes them
  - immediate `runtime_submission.json` persistence right after remote job submit, so queued hardware jobs retain `job_id` / layout / transpilation provenance even if local waiting is interrupted
  - `qcchem runtime collect <artifact-dir>` rehydration path, which can poll an existing real job and merge returned metadata back into `result.json` / `report.md`
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
- `qcchem runtime collect`
- `qcchem hardware optimize`
- `qcchem workbench serve`
- `qcchem agent validate-task`
- `qcchem agent run-task`
- `qcchem agent summarize`

## Visual Workbench

The local Dash workbench turns the existing QCchem artifact tree into a browsable research atlas.

Start it with:

```bash
conda activate qiskit
pip install -e ".[ui]"
qcchem workbench serve
```

The canonical landing route is `/overview`, and the page order is:

1. Overview
2. Structure and Orbitals
3. Active Space and Compression
4. Mapping, Resources, and Circuit
5. Runtime Monitoring
6. Result Confidence Report
7. Studies
8. Benchmarks
9. Scans
10. Hardware Campaign
11. AI Workspace

The startup summary reads the repo artifact inventory and reports the page list plus a short artifact story. More detail lives in [docs/workbench.md](docs/workbench.md).

## H2 Hardware Precision Push

QCchem 现在有一条受预算门控的 H2 真机精度优化路径。它默认只做本地 preview，不会提交 IBM Runtime job：

```bash
conda activate qiskit
PYTHONPATH=/Users/a0000/QCchem qcchem hardware optimize \
  -c configs/h2_hardware_precision_push.yaml \
  --preview
```

真实提交必须显式确认：

```bash
PYTHONPATH=/Users/a0000/QCchem qcchem hardware optimize \
  -c configs/h2_hardware_precision_push.yaml \
  --submit \
  --confirm-runtime-budget "I understand IBM Runtime budget"
```

回收已提交 job：

```bash
PYTHONPATH=/Users/a0000/QCchem qcchem hardware optimize \
  -c configs/h2_hardware_precision_push.yaml \
  --collect
```

输出包括 `hardware_optimization_plan.json`、`hardware_optimization_report.md` 和候选 run artifacts。`hardware_verified` 仍只表示真实结果已取回，不自动等于 chemical accuracy validated。

当前真实 IBM Runtime 精修结果已经落在 `artifacts/h2_hardware_precision_push/`：

- `parity_puccd_layout`：2 qubits / 5 terms，transpiled depth `22`，2Q gates `4`，8192 shots，runtime error `0.0182535 Ha`
- `jw_puccd_layout_baseline`：4 qubits / 15 terms，transpiled depth `149`，2Q gates `42`，8192 shots，runtime error `0.0477009 Ha`
- 结论：压缩路径显著降低硬件负担，但本轮没有达到 `0.0016 Ha` chemical accuracy；当前推荐动作为 `pause_hardware_spend_and_analyze_bias`

## LR-ACE Exploratory Algorithm

QCchem 新增了一个原生探索性算法 `LR-ACE`：`Low-Rank Adaptive Chemistry Eigensolver`。它不是 UCCSD 换壳，而是先使用 modified Cholesky / low-rank Hamiltonian audit，再从 dominant non-diagonal Hamiltonian factors 生成 compact real-mixing Pauli-evolution ansatz。

本地入口：

```bash
PYTHONPATH=/Users/a0000/QCchem qcchem exploratory run \
  -c configs/exploratory/h2_lr_ace.yaml

PYTHONPATH=/Users/a0000/QCchem qcchem exploratory run \
  -c configs/exploratory/lih_active_lr_ace.yaml
```

当前 evidence：

- H2 local LR-ACE：2 qubits、1 parameter、local error `4.78e-10 Ha`
- LiH active-space LR-ACE：2 qubits、5 parameters、local error `6.62e-10 Ha`
- H2 LR-ACE Runtime：depth `12`、2Q gates `2`
- 最佳 retrieved hardware error：`0.001699 Ha`，非常接近但仍未达到 `0.0016 Ha` chemical accuracy

汇总 artifact：

- [LR-ACE summary](/Users/a0000/QCchem/artifacts/lr_ace_suite_v1/lr_ace_summary.json)
- [LR-ACE report](/Users/a0000/QCchem/artifacts/lr_ace_suite_v1/lr_ace_report.md)

边界：LR-ACE 目前属于 `exploratory`。本地 exact-baseline gates 已通过；真机路径已经 hardware-verified，但还不能标成 chemistry validated。

推荐的发布级展示路径已经固定为：

1. `Overview`
2. `Result Confidence`
3. `Benchmarks`
4. `Hardware Campaign`
5. `AI Workspace`

这条路径对应 QCchem 当前最完整的“最佳证据 -> 边界解释 -> 可执行下一步”叙事。

## Validated 与 Exploratory 边界

- 默认 `qcchem run` 只面向主干 validated / stable workflow。
- 如果配置显式声明了实验路径，普通 `run` 会拒绝执行，必须使用 `qcchem exploratory run` 或在 policy 中显式允许。
- exploratory 结果会继续落完整 artifact，但报告顶部会明确标注它不属于 validated QCchem benchmark path。

## 当前限制

- `qcchem workbench serve` is currently a local, read-only preview layer over the artifact tree. It is validated for startup summary and route inventory, but it is not yet a live artifact editor.
- `qiskit-ibm-runtime` 已接入并完成一次真实远程 job submission/result retrieval；当前验证仍限于最小 hardware probe，不代表整条 runtime workflow 已 fully validated。
- `hardware_verified` 的含义很窄：它只表示 QCchem 从真实 runtime job 拿回了结果，并且 `runtime_submission` 记录显示提交/取回链路成功；它不表示该 chemistry 数值结果已经过 publication-grade 精度验证。
- 当前 hardware calibration suite 以 `runtime_submission` 作为 authoritative runtime-evidence source；dashboard 是否把一个 case 记为 `hardware_verified=True`，首先取决于是否存在真实提交并成功取回结果，而不是取决于误差是否足够小。
- 当前 `result.json` 会把 `chemical_accuracy` 和 `runtime_chemical_accuracy` 分开表达：
  - `chemical_accuracy` 评估本地 solver 路径相对 exact baseline 的误差
  - `runtime_chemical_accuracy` 评估真实 runtime 返回值推导出的总能量误差
- 当前 `artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json` 里，runtime-derived `achieved_error` 仍然偏大：
  - H2 baseline runtime probe 约 `0.174 Ha`
  - H2 tighter UCCSD hardware push 约 `0.0468 Ha`
  - H2 compact `PUCCD` hardware push 约 `0.0537 Ha`
  - H2 layout-aware `PUCCD` hardware push 约 `0.0137 Ha`
  - H2 layout-aware `UCCSD` push 约 `0.0404 Ha`
  - H2 layout-aware `PUCCD + DD/twirling/measure mitigation` push 约 `0.2673 Ha`
  - H2 layout-aware `PUCCD + 8192 shots` push 约 `0.0533 Ha`
  - LiH 约 `0.389 Ha`
  这说明当前 scope 是“真实 runtime 结果已取回并被平台记录”，不是“真机 chemistry 精度已达可发表标准”。
- 当前最佳真实 H2 结果仍然是 layout-aware `PUCCD` 的 `0.0137 Ha`。后续两条更激进的 push 没有继续改善，这说明当前 open-instance 硬件上的主限制已经不只是统计误差。
- 当前已经验证：对于长队列或长等待的 real runtime job，QCchem 会在提交成功后立刻写出 `runtime_submission.json`。因此即使本地会话中断，我们也仍然能保住 `job_id`、selected layout、transpiled depth/2Q gates 和 runtime options snapshot，后续可以据此继续追踪或补回结果。
- 当前 tighter H2 hardware probe 已从 `1024 shots / requested_precision 0.05` 推进到 `4096 shots / requested_precision 0.02 / ibm_kingston`，runtime-derived 误差显著下降，但仍未达到 chemical accuracy；这说明 budget-aware runtime calibration 已经在工作，但当前 open-instance 硬件与电路深度组合仍是主要限制。
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
qcchem run -c configs/lih_active_runtime_hardware_probe_v2.yaml
qcchem run -c configs/h2_runtime_hardware_probe_ca.yaml
qcchem run -c configs/h2_runtime_hardware_probe_puccd.yaml
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
qcchem benchmark run -c benchmarks/hardware_calibration_suite_v1.yaml
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
qcchem agent validate-task examples/agents/hardware_campaign_summary.yaml
qcchem agent run-task examples/agents/hardware_campaign_summary.yaml
```

本地 workbench：

```bash
pip install -e ".[ui]"
qcchem workbench serve
```

默认会打开一个 Dash 驱动的本地研究工作台，当前覆盖：

- 总览页
- 结构 / 轨道页
- 活性空间 / 压缩页
- 映射 / 资源 / 电路页
- 运行监控页
- 结果 / 可信度页
- study / benchmark / scan / hardware campaign 聚合页
- AI Workspace 页与 floating copilot 壳层

详细说明见 [docs/workbench.md](/Users/a0000/QCchem/docs/workbench.md)。

## AI Agent Interface

QCchem 现在提供一层面向 AI 代理的轻量任务协议。它适合 Codex、OpenClaw 这类终端型代理，目标是降低调用成本，而不是重新发明一套服务端。

推荐入口：

- `qcchem agent validate-task <task-file>`
- `qcchem agent run-task <task-file>`
- `qcchem agent summarize <artifact-or-suite>`

推荐示例任务：

- [examples/agents/runtime_collect_h2.yaml](/Users/a0000/QCchem/examples/agents/runtime_collect_h2.yaml)
- [examples/agents/hardware_campaign_summary.yaml](/Users/a0000/QCchem/examples/agents/hardware_campaign_summary.yaml)
- [examples/agents/benchmark_h2_lih.yaml](/Users/a0000/QCchem/examples/agents/benchmark_h2_lih.yaml)
- [examples/ai_workspace/provider.openai-compatible.yaml](/Users/a0000/QCchem/examples/ai_workspace/provider.openai-compatible.yaml)
- [examples/ai_workspace/tickets/analysis_h2_campaign.json](/Users/a0000/QCchem/examples/ai_workspace/tickets/analysis_h2_campaign.json)

对应文档：

- [agent_interface.md](/Users/a0000/QCchem/docs/agent_interface.md)
- [hardware_runtime_campaign_report.md](/Users/a0000/QCchem/docs/hardware_runtime_campaign_report.md)
- [ai_workspace.md](/Users/a0000/QCchem/docs/ai_workspace.md)

## AI Workspace

QCchem 的 AI Workspace 把 floating copilot、task ticket 和 workbench page 连接到同一套持久化 artifact 目录。它的核心约束是先写 ticket，再执行 ticket。

在 `Trust-First Release` 里，AI 的默认姿态固定为：

- `evidence-aware`
- `ticket-mediated`
- `artifact-grounded`

也就是说，AI 先解释证据与边界，再给推荐动作，最后才在 ticket 门控下推进执行。

推荐入口：

- [docs/ai_workspace.md](/Users/a0000/QCchem/docs/ai_workspace.md)
- [examples/ai_workspace/provider.openai-compatible.yaml](/Users/a0000/QCchem/examples/ai_workspace/provider.openai-compatible.yaml)
- [examples/ai_workspace/tickets/analysis_h2_campaign.json](/Users/a0000/QCchem/examples/ai_workspace/tickets/analysis_h2_campaign.json)

## Visual Workbench

QCchem 现在还包含一个本地 visual workbench 预览层。它的定位不是替代 CLI，而是把现有 artifact、benchmark、runtime evidence 和报告语言组织成研究人员更愿意长期使用的工作台界面。

当前已经具备：

- Dash 驱动的多页面工作台
- 3Dmol.js 分子层桥接
- 与 QCchem schema 对齐的结果页面
- 启动时对真实 artifact 根目录的 inventory summary
- 与导出报告共享的可信度和 chemical-accuracy 语义

当前边界也很明确：

- workbench 已经能运行、能展示、能说明页面与 artifact 盘面
- 但目前默认页面内容仍以 schema-driven curated view model 为主
- 它还不是任意 artifact 的完整 live browser

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
- `chemical_accuracy`
- `runtime_chemical_accuracy`
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
- `evidence_summary`

其中 `evidence_summary` 是默认面向 CLI、报告、workbench 和 AI 的轻量读口；只有需要下钻时才继续读完整 payload。

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

Repo hygiene helper：

```bash
python scripts/artifact_index.py artifacts
```

## Release-grade Curated Artifacts

当前建议优先作为发布与演示入口的一组 artifact：

- 最强 local validated case
  - [artifacts/h2/result.json](/Users/a0000/QCchem/artifacts/h2/result.json)
- active-space / compression / correction 代表 case
  - [artifacts/lih_auto_compressed_nevpt2/result.json](/Users/a0000/QCchem/artifacts/lih_auto_compressed_nevpt2/result.json)
  - [artifacts/lih_active_exact_compressed_cholesky/result.json](/Users/a0000/QCchem/artifacts/lih_active_exact_compressed_cholesky/result.json)
- benchmark aggregate
  - [artifacts/benchmark_suite_v1/benchmark_result.json](/Users/a0000/QCchem/artifacts/benchmark_suite_v1/benchmark_result.json)
- study aggregate
  - [artifacts/mini_comparison_study/study_result.json](/Users/a0000/QCchem/artifacts/mini_comparison_study/study_result.json)
- scan aggregate
  - [artifacts/h2_short_scan/scan_result.json](/Users/a0000/QCchem/artifacts/h2_short_scan/scan_result.json)
- hardware campaign aggregate
  - [artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json](/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json)
- AI analysis / delivery 样板
  - [examples/ai_workspace/tickets/analysis_h2_campaign.json](/Users/a0000/QCchem/examples/ai_workspace/tickets/analysis_h2_campaign.json)
  - [docs/ai_workspace.md](/Users/a0000/QCchem/docs/ai_workspace.md)

完整展示顺序见 [docs/release_showcase.md](/Users/a0000/QCchem/docs/release_showcase.md)。

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
- `requested_precision_target`
- `requested_budget_strategy`
- `runtime_usage_seconds`
- `runtime_usage_quantum_seconds`
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
