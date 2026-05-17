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

## License

待定（见下面的"需要你确认"）。

## 需要你确认

如果要把这个仓库正式推到 GitHub 上做 public，我需要你告诉我：

1. **License**：MIT / Apache-2.0 / 其它？public 研究类项目通常 MIT 或 Apache-2.0。
2. **GitHub 远程地址**：仓库名就用 `LogicAgent` 吗？我可以用 `gh repo create` 帮你建，但需要确认你已经登录 `gh`。
3. **技术栈**：主语言是 Python 吗？需要我加 `.gitignore`（Python/Node/通用）？
4. **首批内容**：要不要我搭一个最小骨架（`agents/`、`evals/`、`docs/`、一个 hello-world agent demo），还是你想完全自己来？
5. **你的 GitHub 用户名**：git 里看到的是 `Neilander`，README 里要不要写联系方式或者作者署名？
