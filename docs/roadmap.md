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
  - unified hardware calibration dashboard
  - exports carrying `hardware_verified` / `hardware_evidence_tier` / `runtime_submission` provenance
  - explicit docs boundary that `hardware_verified` means runtime result retrieved, not publication-grade chemistry validation
- successful remote runtime / session execution integration
- 更丰富的 noise model suite 与 mitigation experiment layer
- 更稳的 variational excited-state solver 路径
- 更多 validated property 路径
- geometry optimization workflow
- gradient / response property 路径
- 资源估计工作流
- 更完整的 campaign workflow
- 更系统的 benchmark acceptance policy

## v1.0 愿景

QCchem 成为一个面向真实研究活动的量子化学平台：

- 不只支持单点运行，也支持 benchmark、study、scan 和任务编排
- ground-state / excited-state / property / optimization workflow 共用统一 schema
- 可以在 validated 与 exploratory 边界清晰的前提下承载持续演化的研究平台能力
