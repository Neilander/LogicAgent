# LogicAgent

探索"具有 agency 的逻辑 AI"——让模型可以 zero-shot，或仅用极少的步骤，独立解决一个问题。

## 这是什么

当前主流 LLM agent 的失败模式往往不是"不知道怎么做"，而是：

- **缺乏 agency**：被动等待 prompt，不会主动决定何时停止、何时换路径、何时承认无解。
- **盲目试错**：用大量 tool call 堆砌出一个看起来对的答案，而不是先想清楚再行动。
- **没有逻辑结构**：在多步推理里丢上下文、自我矛盾、绕远路。

LogicAgent 想反过来：**先把推理结构立起来，再让 agent 用最少的动作完成任务。**

## 想探索的方向

- **Zero-shot decomposition**：给定一个未见过的任务，模型能否在不调用任何工具前，先产出一个可执行的推理图。
- **Minimum-action policy**：在一个可工具化的环境里，奖励"少做"而不是"多做"——把 tool call 数量、token 消耗作为一等指标。
- **Self-termination**：让 agent 自己判断"我已经够了"或"这条路走不通"，而不是被外部 budget 砍掉。
- **Logic over heuristics**：用形式化的中间表示（约束、规则、谓词）承载推理，而不是纯自然语言滚雪球。

## 状态

早期探索阶段。仓库会同时承载：

- 实验代码（不同 agent 架构的最小 demo）
- 评测脚本（怎么衡量"少动作 + 高成功率"）
- 笔记与设计文档（在 `docs/` 下）

## Contact

violandernnn@gmail.com

## License

[Apache License 2.0](LICENSE) — Copyright 2026 Neilander.
