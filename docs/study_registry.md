# Study / Registry Model

## Study 是什么

在 QCchem 里，study 是一组有共同研究目的的 runs。它允许我们把：

- 不同 solver
- 不同 backend
- 不同 mapping
- 不同 shots
- 不同 active space

放进一个统一 artifact 里比较。

## 当前对象

- `StudySpec`
- `StudyRunSpec`
- `RunRecord`
- `StudyResult`
- `RegistryEntry`
- `CampaignSpec`
- `CampaignEntrySpec`

## Registry 的作用

registry 不是数据库替代品，而是 artifact 层的最小索引：

- 记录对象名
- 记录对象种类
- 记录状态
- 记录 artifact path
- 记录来源配置

当前 study、benchmark、scan 都会写自己的 `registry.json`。

## 当前工作方式

1. 读入 `StudySpec`
2. 依次运行每个 `StudyRunSpec`
3. 为每个 run 生成 `RunRecord`
4. 聚合 status / comparison axes
5. 写 `study_result.json`、`study_report.md`、`registry.json`

## 当前 study 能回答的问题

- 哪个 run 用了哪个 backend / mapping / policy
- 每个 run 的 artifact 在哪里
- 每个 run 的总能和 benchmark error 是什么
- 当前 study 是否全部 validated

## 当前限制

- campaign 目前已有独立 CLI/workflow，但默认应优先使用 artifact-only 或本地 workflow；真实 runtime 仍必须显式走预算确认边界
- registry 目前是 artifact-local，不是全局查询服务
- comparison 目前以 summary 为主，不是交互式分析层

## Campaign Workflow

campaign 把 run、benchmark、study、scan、hardware calibration 或已有 artifact
收成一个更高层的证据闭环。最小示例：

```bash
qcchem campaign run -c configs/campaign/trust_loop_mini.yaml
qcchem campaign report artifacts/trust_loop_mini_campaign/campaign_result.json
qcchem campaign accept artifacts/trust_loop_mini_campaign/campaign_result.json
```

输出包括 `campaign_result.json`、`campaign_report.md`、`registry.json`、
`artifact_index.json` 和 `acceptance_summary.json`。`campaign run` 默认拒绝覆盖已有非空
campaign 输出目录；确认要替换整套 campaign bundle 时再加 `--overwrite`。
