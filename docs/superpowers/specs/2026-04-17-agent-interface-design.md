# QCchem Agent Interface Design

## Goal

让 QCchem 在不重写现有架构的前提下，提供一个对 AI 代理友好的正式接口层，使 `Codex`、`OpenClaw` 等终端型代理可以低成本、高可靠地：

- 提交标准化任务
- 读取结构化结果
- 复用现有 artifact/workflow
- 对真实 runtime job 做补回与汇总

同时，本轮还要把最近的真实 IBM runtime 化学精度冲刺整理为正式报告。

## Scope

本轮只做两件事：

1. `hardware runtime campaign report`
2. `CLI-first agent interface`

明确不做：

- GUI
- HTTP service
- MCP server 正式实现
- 新算法扩张

## Why CLI-First

现有 QCchem 已经有较稳定的 CLI、artifact schema 与报告体系。对于 `Codex/OpenClaw` 这类代理，最低成本、最高可维护性的方式不是新增服务层，而是在现有 CLI 上增加：

- agent task schema
- agent task validation
- agent task execution
- machine-readable summary output

这样做的好处：

- 不破坏现有 validated workflow
- 代理可以继续通过 shell 调用
- artifact 仍然是唯一事实来源
- 未来若要做 MCP/HTTP adapter，可以直接复用同一套 task schema

## Deliverables

### 1. Hardware Runtime Report

新增正式报告文档：

- `docs/hardware_runtime_campaign_report.md`

内容包括：

- 本轮真实 IBM runtime 化学实验背景
- H2 / LiH 真实 case 清单
- 误差表与 chemical-accuracy 距离
- 最佳真实结果
- 失败/退化尝试的解释
- 当前 validated/exploratory 边界
- 对后续硬件实验的建议

同时输出一份机器可读汇总：

- `artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_summary.json`

### 2. Agent Task Schema

新增正式 agent task schema，支持 YAML/JSON。

建议顶层字段：

- `agent_task.version`
- `agent_task.name`
- `agent_task.kind`
- `agent_task.description`
- `agent_task.inputs`
- `agent_task.outputs`
- `agent_task.policy`

首批支持的 task kind：

- `run_config`
- `runtime_collect`
- `benchmark_suite`
- `hardware_campaign_summary`

### 3. Agent Workflow Layer

新增：

- `qcchem/io/agent_config.py`
- `qcchem/workflow/agent.py`

职责：

- 解析 agent task file
- 校验 task kind 与必需字段
- 调用现有 workflow：
  - `run_from_config`
  - `run_benchmark_suite_from_config`
  - `collect_runtime_artifact`
- 生成统一 agent result payload

### 4. Agent CLI

在现有 CLI 上新增：

- `qcchem agent validate-task <task-file>`
- `qcchem agent run-task <task-file>`
- `qcchem agent summarize <artifact-or-suite>`

要求：

- 输出既对人类可读，也对代理可解析
- 始终返回 artifact path / summary json path
- 不重复发明新的 run logic，只封装现有 workflow

### 5. Agent Examples

新增目录：

- `examples/agents/`

首批样例：

- `runtime_collect_h2.yaml`
- `hardware_campaign_summary.yaml`
- `benchmark_h2_lih.yaml`

### 6. Agent Documentation

新增：

- `docs/agent_interface.md`

说明：

- AI 代理如何最低成本调用 QCchem
- 推荐任务类型
- 推荐 artifact 读取顺序
- 何时先 `runtime collect`
- 何时读 `result.json` 而不是重跑
- validated / exploratory 边界怎么读

## Data Flow

### Agent Run

1. 代理写或选择一个 task file
2. `qcchem agent validate-task` 做静态校验
3. `qcchem agent run-task` 调用现有 workflow
4. QCchem 返回：
   - 状态
   - 结构化 summary
   - artifact 路径
5. 代理后续只消费 artifact，而不是猜 CLI 输出文本

### Hardware Campaign Summary

1. Agent task 读取 `hardware_calibration_suite_v1`
2. 汇总最佳/最差/推荐 case
3. 输出 markdown + json summary

## Boundaries

- Agent interface 不改变现有 validated/exploratory/unstable 语义
- Agent interface 不绕过现有 exploratory gate
- Agent interface 不直接提交新算法，只复用现有能力
- Agent interface 的 summary 必须明确：
  - `verification_status`
  - `hardware_verified`
  - `runtime_chemical_accuracy`

## Success Criteria

- 代理可以通过单个 task file 启动标准 QCchem 工作流
- 代理可以通过单个 task file 对 runtime sidecar 做 collect
- 代理可以低成本得到结构化 summary，而不是自己手工解析很多 artifact
- 硬件冲刺报告有正式文档和机器可读 summary
