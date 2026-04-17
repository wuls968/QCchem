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
- 真实 hardware probe artifact：
  - `artifacts/lih_active_runtime_hardware_probe`
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
- runtime/session-ready integration point
- low-rank runtime policy metadata layer
- 完整 mitigation implementation

## 当前未完成

- exploratory benchmark/study 的更深集成目前仍以显式隔离为主，尚未成为独立 aggregate workflow
- 还没有把完整 low-rank benchmark suite 接到真实远程 estimator primitive result
- 还没有验证多 case chemistry workflow 的远端 runtime 稳定性
- mitigation 仍以 schema + metadata + hook 为主
- embedding 还没有 fragment solver execution，只到 DMET-style recommendation skeleton
- excited-state 还没有 validated VQD / qEOM implementation
- transition dipole / oscillator strength 还没有进入 validated property 集
- scan 目前只支持 1D bond-distance 模式
- campaign 目前落在 schema 层，尚未形成独立 workflow/CLI

## 建议下一步

1. 把真实 runtime probe 从单 case 扩到小规模 chemistry benchmark
2. 为 runtime-ready sampled 路径补更稳的 shot allocation / grouping policy benchmark
3. 为 NEVPT2 增加更多体系与 active-space benchmark，确认 correction 的稳定边界
4. 给 embedding 层接入一个真实 fragment solver plugin
5. 给 excited-state 增加一个真正可跑的 variational path

## 风险提醒

- local noisy model 目前只证明 QCchem 能走 noisy execution path，不证明它代表真实硬件
- 当前真实 runtime 只验证了最小 hardware probe，不应外推成整套 remote chemistry workflow 已验证
- 当前 NEVPT2 是 classical plugin reference augmentation，不应当误读为量子原生后修正已验证
- `double_factorization` 与 embedding skeleton 已正式落 artifact，但仍是 exploratory
- QCSchema/HDF5 导出当前是 interoperability helper，不是外部标准完全认证声明
- property artifact 的总验证状态可能因为 exploratory property 被拉成 exploratory，因此必须看 property-level status
- ground-state validated 不会自动推出 excited-state/property validated
- 由于仓库尚无提交，artifact 的 `git_commit` 仍不是强 provenance 证据
