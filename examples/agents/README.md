# QCchem Agent Examples

这些任务文件是给 Codex、OpenClaw 或其他终端型 AI 代理直接复用的最小模板。

- `runtime_collect_h2.yaml`
  - 补回一个已经提交的真实 IBM runtime job
- `hardware_campaign_summary.yaml`
  - 把当前硬件实验目录总结成 AI 友好的 JSON 和 Markdown
- `benchmark_h2_lih.yaml`
  - 运行主 benchmark suite，并生成 compact summary

推荐命令：

```bash
qcchem agent validate-task examples/agents/runtime_collect_h2.yaml
qcchem agent run-task examples/agents/runtime_collect_h2.yaml
qcchem agent run-task examples/agents/hardware_campaign_summary.yaml
```
