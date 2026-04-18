# QCchem AI Workspace Design

## Goal

在不重写现有 QCchem 架构的前提下，为 visual workbench 增加一套正式的 AI 工作层，使研究人员能够通过一个高完成度的浮动 AI 窗口和一个辅助性的独立工作台页，低成本地完成：

- 研究问答与结果解释
- 任务计划与作业单确认
- 调用现有 QCchem workflow / agent protocol 执行任务
- 提交、接收、退回、查看历史交付物
- 在同一套 schema 和 artifact 语义下保留 provenance、可信度边界和执行证据

这轮目标不是做一个“能聊天的插件”，而是做一个 **任务中枢型 AI 协作层**。

## Scope

本轮聚焦一个子项目：

1. `AI Workspace`

它包含两层产品表面：

- `浮动 AI 窗口`：主入口
- `AI Workspace 页`：次入口，用于任务中枢、交付和历史查看

它必须覆盖三类正式作业：

1. `计算执行单`
   - run
   - benchmark
   - study
   - scan
   - runtime collect
2. `研究分析单`
   - 结果解读
   - 误差分析
   - 图表总结
   - artifact 对比
3. `协作交付单`
   - 提交报告
   - 接收任务
   - 退回修改
   - 查看历史交付物

## Explicit Non-Goals

本轮明确不做：

- MCP server
- 单独的 HTTP service 平台
- 让 AI 绕过现有 QCchem workflow 直接执行任意动作
- 先支持所有模型供应商的深度原生适配
- 完整多用户权限系统
- 让 AI 自动扩张 validated 范围

## Product Strategy

采用 **任务中枢型** 方案。

原因：

- 纯聊天外挂会让复杂研究工作消失在消息流里
- 纯全自动 agent 会让执行边界和证据链失控
- QCchem 现有最强资产是 run/study/benchmark/scan/runtime artifact 与已有的 CLI-first agent protocol

因此本轮的核心原则是：

- 问答可以轻量
- 执行必须正式
- 交付必须留痕

AI 不直接成为黑盒执行器，而是先把需求收束成 `Task Ticket`，再由用户确认并路由到现有 QCchem 执行层。

## Primary UX Shape

### 1. Floating Research Copilot

作为主入口，负责：

- 即时研究问答
- 结果解释
- 草拟任务单
- 快速查看任务状态
- 快速修改计划
- 快速把任务发送到 agent 或 QCchem workflow

交互要求：

- 可浮动
- 可调整大小
- 可最小化
- 不破坏当前结果页阅读

这个窗口应该是“研究伴随层”，不是全屏聊天页。

### 2. AI Workspace Page

作为次入口，负责：

- 集中查看任务单
- Inbox / Running / Submitted / Completed / Returned 视图
- 接收任务 / 交作业 / 退回修改
- 查看交付历史
- 查看 agent binding 和执行路由

它更像“研究任务中枢”，而不是把聊天窗口放大。

## Core Principles

### 1. Plan First, Then Execute

对执行型动作，AI 必须先生成任务计划和作业单，再等待确认。

允许直接回答的只有：

- 简单概念问题
- 简短结果解释
- 不触发执行和交付的普通问答

一旦动作涉及：

- 真机或采样执行
- 运行现有 workflow
- 批量 artifact 对比
- 结构化交付输出

就必须先进入 `Task Ticket` 流。

### 2. Artifact Is Still the Source of Truth

AI 层不能发明第二套事实来源。

任何执行、汇总、分析、交付，都应尽量回指：

- `result.json`
- `report.md`
- `runtime_submission.json`
- `calibration.json`
- benchmark / study / scan summary

### 3. AI Does Not Relax Scientific Boundaries

validated / exploratory / unstable 语义必须保持不变。

AI 可以：

- 解释边界
- 汇总边界
- 基于边界给建议

AI 不可以：

- 自动把 exploratory 说成 validated
- 自动掩盖未达 chemical accuracy 的事实
- 绕过现有 task / benchmark / policy gate

## Formal Object Model

### 1. `AIProviderSpec`

负责模型 API 配置。

第一版统一采用 `OpenAI-compatible` 作为正式入口。

建议字段：

- `provider_name`
- `provider_kind`
- `base_url`
- `api_key_ref`
- `model`
- `timeout_seconds`
- `default_temperature`
- `default_max_tokens`
- `capabilities`
- `enabled`

其中：

- `provider_kind` 首批支持 `openai_compatible`
- schema 预留：
  - `anthropic`
  - `gemini`
  - `local_compatible`

要求：

- API key 不直接写入普通 artifact
- 通过 `api_key_ref` 或等效 secret reference 保存配置关系
- provider 配置应被 workbench 浮窗的设置抽屉消费

### 2. `AIWorkspaceSession`

代表一次研究上下文，而不是简单消息列表。

建议字段：

- `session_id`
- `created_at`
- `updated_at`
- `active_provider`
- `active_model`
- `current_page`
- `context_artifacts`
- `referenced_runs`
- `referenced_studies`
- `referenced_benchmarks`
- `referenced_scans`
- `agent_mode`
- `messages`

用途：

- 把聊天和当前研究对象绑定
- 支持“从结果页直接提问”
- 支持会话级上下文延续

### 3. `AITaskTicket`

这是本轮最核心的正式对象。

建议字段：

- `task_id`
- `task_type`
- `title`
- `request_text`
- `plan_summary`
- `inputs`
- `expected_outputs`
- `risk_notes`
- `boundary_notes`
- `confirmation_required`
- `execution_target`
- `linked_artifacts`
- `linked_session_id`
- `status`
- `created_by`
- `assigned_to`
- `created_at`
- `updated_at`

首批 `task_type`：

- `execution`
- `analysis`
- `delivery`

状态流统一为：

- `draft`
- `needs_confirmation`
- `accepted`
- `running`
- `blocked`
- `submitted`
- `completed`
- `returned`

### 4. `AIAgentBinding`

负责把任务单绑定到实际执行器。

建议字段：

- `binding_id`
- `executor_kind`
- `executor_name`
- `supports_execution`
- `supports_analysis`
- `supports_delivery`
- `default_task_types`
- `fallback_mode`
- `status`
- `notes`

第一版允许的执行器：

- `qcchem_agent_protocol`
- `analysis_only_assistant`
- `external_agent_bridge`

其中：

- `qcchem_agent_protocol` 负责调用现有 `qcchem agent` / workflow
- `analysis_only_assistant` 用于只生成解释和分析，不触发执行
- `external_agent_bridge` 为未来接外部 agent 保留正式绑定位，但本轮不要求完整接通

### 5. `AIDeliveryRecord`

负责“交作业 / 收作业 / 查看历史”的正式记录。

建议字段：

- `delivery_id`
- `task_id`
- `delivery_kind`
- `summary`
- `linked_outputs`
- `submitted_by`
- `submitted_to`
- `review_status`
- `return_notes`
- `created_at`
- `updated_at`

首批 `delivery_kind`：

- `summary`
- `report`
- `artifact_bundle`
- `analysis_note`

首批 `review_status`：

- `draft`
- `submitted`
- `accepted`
- `returned`
- `closed`

## Task Categories

### 1. 计算执行单

对应现有 QCchem 主干执行能力。

第一版可路由到：

- `run_config`
- `benchmark_suite`
- `runtime_collect`
- 既有 run/study/scan/benchmark workflow 包装

这类任务必须明确：

- 会不会触发真机
- 会不会消耗预算
- 预计输出 artifact 是什么

### 2. 研究分析单

第一版重点不是“新建算法”，而是对现有 artifact 与 summary 做高质量分析。

典型内容：

- 解释某次结果为什么没达到 chemical accuracy
- 比较 ideal / sampled / runtime 路径
- 总结一个 hardware campaign
- 比较一组 benchmark 的意义和边界

默认行为：

- 可先直接给短答
- 若分析复杂，则自动建议提升为正式任务单

### 3. 协作交付单

用于把执行或分析结果正式交付出去。

典型内容：

- 提交 summary
- 提交报告草稿
- 指派给 agent
- 退回修改
- 关闭任务

## Interaction Flows

### Flow A: Research Q&A

1. 用户在浮窗提问
2. AI 判断：
   - 是否能直接答
   - 是否需要提升为分析任务
3. 若可直接答：
   - 返回简洁解释
   - 附带可继续起单的建议
4. 若需升级：
   - 生成 `AITaskTicket(draft or needs_confirmation)`
   - 等待确认

### Flow B: Execution Request

1. 用户提出执行需求
2. AI 生成执行任务单，包含：
   - 输入
   - 计划
   - 预期输出
   - 风险与边界
   - 是否触发真机或 agent
3. 用户确认
4. 任务进入：
   - `accepted -> running`
5. 由 `AIAgentBinding` 路由到现有 QCchem workflow / agent protocol
6. 执行结果回写为：
   - artifact links
   - summary
   - delivery record

### Flow C: Delivery & Review

1. 执行完成后生成 `AIDeliveryRecord`
2. 用户可以：
   - 打开
   - 接收
   - 退回
   - 继续派生后续任务
3. 历史交付物进入独立页和会话历史

### Flow D: AI Workspace Management

独立页提供：

- `Inbox`
- `Running`
- `Submitted`
- `Completed`
- `Returned`
- `Assigned to Me`
- `Submitted by Me`
- `Agent Bindings`

作用是把复杂任务从聊天流里抽出来，不让研究活动消失在消息列表里。

## UI Component Model

### Floating Window

主组件必须包含：

- 会话消息区
- 快速动作区
- 当前任务单预览
- Provider 配置抽屉入口
- 状态指示（例如正在运行、等待确认、已交付）

交互要求：

- 支持最小化
- 支持拖动 / 浮动感布局
- 支持调整大小
- 不遮挡核心 workbench 视图

### Provider Drawer

作为浮窗内或邻近浮窗的设置抽屉。

首批字段：

- `base_url`
- `model`
- `api_key_ref`
- `timeout`
- `temperature`

目标：

- 配置过程正式但不打断使用
- 不把 provider 管理混进普通聊天记录

### Task Center

独立页的中区核心组件。

负责显示：

- 任务单详情
- 计划摘要
- 输入与预期输出
- 风险和边界
- 确认 / 退回 / 执行入口

### Delivery Panel

负责：

- 交作业
- 看作业
- 退回修改
- 查看历史交付

显示内容必须包括：

- 任务关联
- 输出文件
- 审阅状态
- return notes

### Agent Binding Panel

负责：

- 当前执行器
- 是否走 QCchem 自己的 agent protocol
- 是否只做分析
- 是否预留给外部 agent

它是正式配置面板，不是隐藏逻辑。

## Integration with Existing QCchem Layers

本轮必须复用：

- `qcchem agent validate-task`
- `qcchem agent run-task`
- `qcchem agent summarize`
- 现有 run / benchmark / study / scan / runtime collect workflow
- 现有 workbench 壳层与页面上下文

这意味着：

- AI 工作台不是第二执行系统
- 它是现有执行层之上的协作编排层

## Persistence & Provenance

AI 层自身也必须留痕。

建议持久化内容：

- session metadata
- task tickets
- delivery records
- provider configuration references
- agent binding references

但边界是：

- 不把 secret 明文落到普通 artifact
- 不把聊天内容误当成科学结果
- 科学结论仍以 QCchem 主 artifact 为准

## Error Handling

### Provider Errors

例如：

- API key 无效
- base_url 不可达
- model 不存在

处理原则：

- 明确显示在 provider / session 层
- 不伪装成任务失败
- 给出可修复动作

### Execution Errors

例如：

- workflow 调用失败
- runtime collect 失败
- agent execution 返回错误

处理原则：

- 任务单进入 `blocked` 或 `returned`
- 保留错误摘要与关联 provenance
- 允许用户重新编辑后再发起

### Delivery Errors

例如：

- 输出文件缺失
- summary 无法生成

处理原则：

- delivery record 显示不完整状态
- 不把“提交成功”说成成功

## Scientific Boundary Handling

AI 工作台必须显式保留：

- `validated`
- `exploratory`
- `unstable`

同时支持展示：

- `hardware_verified`
- `chemical_accuracy_achieved`
- `distance_to_target`

这些字段只能读取、汇总和解释，不能被 AI 私自改写。

## Testing Strategy

至少需要新增以下测试层：

### Unit

- provider spec parsing
- task ticket schema parsing
- delivery record serialization
- agent binding resolution

### Integration

- 从浮窗动作到 task ticket 生成
- task ticket 到既有 QCchem agent / workflow 调用
- delivery record 写出与读取
- AI workspace 页的数据聚合

### UI / Workbench

- 浮窗主入口存在与默认状态
- 独立工作台页的任务列表 / 交付列表 / agent 绑定视图
- provider drawer 表面结构

## Deliverables

本轮设计最终应导向这些实现物：

- AI workspace schema
- provider config schema
- task ticket persistence
- delivery record persistence
- floating AI window
- AI workspace page
- provider drawer UI
- task center / delivery / agent binding panels
- 文档与 examples

## Success Criteria

如果这一轮实现成功，QCchem 应该能做到：

- 用户在 workbench 内直接发起研究问答
- AI 对简单问题可直接回答
- 对复杂问题和执行请求，AI 会先生成正式作业单
- 用户可以确认后触发 QCchem 现有 workflow / agent protocol
- 用户可以交作业、接作业、退回修改、查看历史
- 整个过程不破坏现有 artifact、schema 和 validated boundary

## Future Extensions

本轮做完之后，未来可以自然扩展：

- Anthropic / Gemini / local-compatible provider native adaptations
- 更深的 external agent binding
- MCP adapter
- 更强的多人协作权限
- 更智能的 artifact-aware analysis workflows

但这些都不属于本轮设计范围。
