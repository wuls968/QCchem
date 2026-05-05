# QCchem Agent Interface

QCchem 现在提供一层面向 AI 代理的稳定接口，目标不是替代现有 CLI，而是把 CLI、artifact 和任务协议统一成更容易被 Codex、OpenClaw 这类工具消费的形式。

## 设计原则

- 继续复用已有 `qcchem run / benchmark / study / scan / runtime collect`
- 让代理优先消费 JSON summary，而不是自己解析 Markdown
- 保持 `validated / exploratory / unstable` 边界不被代理层稀释
- 让代理通过任务文件复用稳定流程，而不是现场拼接一串命令

## Agent 命令

```bash
qcchem agent validate-task <task-file>
qcchem agent run-task <task-file>
qcchem agent summarize <artifact-or-suite>
```

### `validate-task`

只校验任务文件 schema，不执行计算。

适合：

- 代理在真正运行前做快速静态检查
- CI 或自动化脚本检查任务文件是否合格

### `run-task`

执行一个 agent task，并把结果输出为稳定 JSON。

当前支持的 task kind：

- `run_config`
- `runtime_collect`
- `benchmark_suite`
- `hardware_campaign_summary`

### `summarize`

面向硬件实验目录的直接总结入口。它会读取 `hardware_calibration_summary.json`，并产出：

- `hardware_runtime_campaign_summary.json`
- `hardware_runtime_campaign_report.md`

## Agent Task Schema

最小格式：

```yaml
agent_task:
  version: 1
  name: summarize_hardware_runtime_campaign
  kind: hardware_campaign_summary
  description: Build an AI-friendly summary for the current hardware runtime campaign.
  inputs:
    target: ../../artifacts/hardware_calibration_suite_v1
  outputs:
    summary_json: ../../artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_summary.json
    report_markdown: ../../artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_report.md
```

### `kind = run_config`

- required:
  - `inputs.config`
- optional:
  - `inputs.output_dir`
  - `outputs.summary_json`

### `kind = runtime_collect`

- required:
  - `inputs.artifact_root`
- optional:
  - `outputs.summary_json`

### `kind = benchmark_suite`

- required:
  - `inputs.config`
- optional:
  - `inputs.output_dir`
  - `outputs.summary_json`

### `kind = hardware_campaign_summary`

- required:
  - `inputs.target`
- optional:
  - `outputs.summary_json`
  - `outputs.report_markdown`

## 推荐给 AI 的使用顺序

### 1. 先验证任务文件

```bash
qcchem agent validate-task examples/agents/hardware_campaign_summary.yaml
```

### 2. 再执行任务

```bash
qcchem agent run-task examples/agents/hardware_campaign_summary.yaml
```

### 3. 优先读取结构化结果

推荐读取顺序：

1. `summary_json`
2. `result.json`
3. `runtime_submission.json`
4. `report.md`

这样 token 成本最低，也最不容易误读边界。

## 针对 Codex / OpenClaw 的实践建议

- 如果目标是“补回真实 IBM 结果”，优先用 `runtime_collect`，不要直接重跑
- 如果目标是“总结一轮硬件实验”，优先用 `hardware_campaign_summary`
- 如果目标是“跑一个标准验证集合”，优先用 `benchmark_suite`
- 只有在明确需要新计算时，才走 `run_config`

## 边界说明

- agent interface 是 QCchem 主干 CLI 的上层任务协议，不是一套独立执行引擎
- 它不会把 exploratory 模块自动提升成 validated
- `hardware_verified` 仍然只表示真实 runtime 结果已取回，不表示 chemistry 精度已经达到 publication-grade
- 如果一个结果没有达到 chemical accuracy，agent summary 会保留这个事实，而不会自动粉饰
