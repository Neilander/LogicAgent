# Stage 0：最小可生存 agent

## 目标

只装备**一个识别核 + 一个规划核**，看 agent 能不能在 Crafter 里"不饿死"。

- 识别核：`food_recognizer`
- 规划核：`greedy_nearest`
- Executor：Claude Sonnet（通过 CLI）

## 成功指标

| 指标 | baseline | 目标 |
|---|---|---|
| 平均存活步数 | TBD（先测随机 agent） | > baseline 2x |
| `eat_plant` achievement 解锁率 | TBD | > 50% |
| `collect_drink` achievement 解锁率（顺带）| TBD | 不要求 |

## Pipeline（一个 step）

```
1. env.step(action) → raw observation (7×7 tiles + state)
2. food_recognizer(obs) → list of food positions
3. graph_builder(obs, recognized) → Graph (nodes with NL descriptions)
4. greedy_nearest(graph, self_state) → 选一个 target node id
5. executor(target_node, graph) → 原子动作序列
6. 执行直到完成或失败 → 回到步骤 1
```

## 节点示例（一个 Graph 序列化后给 LLM 看的样子）

```
当前节点图：
- self (我自己, HP=8, food=4, drink=6)
- food_NW_close: 近处西北方的果树（plant tile）
- food_E_mid:    中距东边的浆果丛（plant tile）
- obstacle_S:    南边的石头

规划核（greedy_nearest）建议：
→ 前往 food_NW_close
```

## 节点抽象规则

- **方向**：8 方位 + self，按 agent 朝向相对计算
- **距离**：close = 1-2 格，mid = 3-4 格，far = 5+ 格（Crafter 视野最大 9×7）
- **聚合**：相邻 tile 的同类食物合并成一个节点（"那一片果丛"，而不是 5 个独立节点）

## 不做的事（明确范围）

- 不做威胁识别（让 zombie/skeleton 来打你就接受）
- 不做资源采集
- 不做合成
- 不做学习（识别核和规划核都是写死的）
- 不做多 episode 的记忆

这些都留给 Stage 1+。

## 文件

- `types.py` — Node / Graph 数据结构
- `recognizers/food.py` — 食物识别核
- `graph.py` — raw view → Graph
- `planner.py` — greedy_nearest 规划核
- `executor.py` — Claude CLI 调用，节点 → 原子动作
- `run.py` — episode 入口
- `results/` — 每次跑完留一个 markdown 记录指标和有趣的 trace
