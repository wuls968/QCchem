# QCchem Hardware Runtime Campaign Report

## 目标

这轮工作的目标不是“证明真机已经达到 chemical accuracy”，而是把 QCchem 的真实 IBM runtime 化学实验整理成一套可复盘、可比较、可被 AI 代理直接消费的 campaign 证据。

## 当前覆盖

当前 campaign 汇总来自：

- `/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json`
- `/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_calibration_report.md`

当前共有 8 个真实 hardware cases，全部都已经完成真实 runtime 提交并成功取回结果。

## 当前最佳结果

当前最佳真实 H2 chemistry result 是：

- case: `h2_runtime_hardware_probe_puccd_layout`
- backend: `ibm_kingston`
- strategy: `layout-aware PUCCD`
- runtime-derived absolute error: `0.013673650274335092 Ha`

这已经显著优于早期 H2 baseline probe 的 `0.1740707404306301 Ha`，但仍然没有达到 chemical accuracy 目标 `0.0016 Ha`。

## 关键对比

### H2 baseline probe

- case: `h2_runtime_hardware_probe`
- backend: `ibm_marrakesh`
- shots: `1024`
- error: `0.1740707404306301 Ha`

### tighter UCCSD push

- case: `h2_runtime_hardware_probe_ca`
- backend: `ibm_kingston`
- shots: `4096`
- error: `0.046849070101739665 Ha`

### compact PUCCD push

- case: `h2_runtime_hardware_probe_puccd`
- backend: `ibm_kingston`
- shots: `4096`
- error: `0.05367855085690487 Ha`

### layout-aware UCCSD push

- case: `h2_runtime_hardware_probe_ca_layout`
- selected layout: `[44, 45, 46, 47]`
- transpiled depth: `158`
- 2Q gate count: `49`
- error: `0.040409655531094435 Ha`

### layout-aware PUCCD push

- case: `h2_runtime_hardware_probe_puccd_layout`
- selected layout: `[44, 45, 46, 47]`
- transpiled depth: `146`
- 2Q gate count: `42`
- error: `0.013673650274335092 Ha`

### 更激进的 mitigation 组合

- case: `h2_runtime_hardware_probe_puccd_layout_mitigated`
- strategy: `layout-aware PUCCD + 8192 shots + DD + twirling + measure mitigation`
- error: `0.26726073507437587 Ha`

### 更高 shot budget

- case: `h2_runtime_hardware_probe_puccd_layout_highshots`
- strategy: `layout-aware PUCCD + 8192 shots`
- error: `0.05332134520924514 Ha`

### LiH active-space compressed hardware probe

- case: `lih_active_runtime_hardware_probe_v2`
- backend: `ibm_fez`
- error: `0.38879419502160584 Ha`

## 当前最可靠的结论

### 已经被真实数据支持的结论

- QCchem 已经具备真实 IBM runtime chemistry 提交、回收和 artifact 合并能力
- `runtime_submission.json` 和 `qcchem runtime collect` 让长队列 job 不再丢证据
- layout-aware transpilation 对 H2 结果有明显帮助
- 当前最好的 H2 runtime case 是 `layout-aware PUCCD`

### 被真实数据否定或尚未支持的假设

- 更高 shots 并没有自动把 H2 推到 chemical accuracy
- 更激进的 `DD + twirling + measure mitigation` 组合在当前 open-instance 条件下并没有改善 H2，反而更差
- 更浅的 ansatz 并不保证更好的 runtime-derived chemistry result，效果仍取决于整体噪声和执行链

## 边界说明

- 这些 case 都属于 `hardware_verified`，因为它们确实有真实 runtime result retrieved
- 但它们**不属于**“已达到 chemical accuracy 的硬件化学 benchmark”
- 当前最好的真实 H2 结果 `0.0137 Ha` 仍然比 chemical accuracy `0.0016 Ha` 高约 8.5 倍

## 对后续 AI/自动化最有价值的用法

- 如果要继续复盘或自动总结，优先读取：
  - `hardware_calibration_summary.json`
  - `hardware_runtime_campaign_summary.json`
  - 对应 case 的 `runtime_submission.json`
- 如果一个硬件 case 还在排队或已提交未回收，优先执行：

```bash
qcchem runtime collect <artifact-dir>
```

而不是重新发一个 job。

## 推荐下一步

- 继续把 H2 作为唯一 chemical-accuracy 冲刺目标，不扩大体系
- 优先搜索 layout / observable planning / resilience 组合，而不是再机械增加 shots
- 对 AI 代理，优先使用 `qcchem agent run-task examples/agents/hardware_campaign_summary.yaml` 进行 campaign 总结
