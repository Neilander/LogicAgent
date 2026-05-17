# 实验 1：从"最小可生存 agent"出发探索宏观决策

## 这是什么

我们想验证一个假设：

> **AI 的 zero-shot 能力，来自"先把世界抽象成中层表征，再在表征上做决策"，而不是直接对原始输入反应。**

为了验证它，我们造一个最小生物：地图上有食物 + 障碍，agent 的目标只有一个——**找到食物，不饿死**。我们一层层加能力，看每加一个"卷积核"，agent 的生存表现和决策质量提升多少。

## 理论基础

这个架构本质上是 **认知地图（cognitive map）理论** 的工程化：

- Tolman (1948) 证明动物会在脑里建立环境的拓扑地图，而不是死记动作序列。
- 大脑里有 **place cells**（O'Keefe & Moser，诺奖）—— 专门识别"我在 X 类位置"的神经元。
- 决策在这张地图上发生，而不是在原始感觉输入上。

我们的 **识别核** ≈ place cells；**节点图** ≈ cognitive map；**规划核** ≈ 前额叶的路径选择。

## 4 层架构

```
┌──────────────┐
│  Raw View    │  Crafter 给的 7×7 tile + 自己状态
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│ Layer 1: 识别核                   │
│   food_recognizer  → [食物位置]   │
│   threat_recognizer→ [威胁位置]   │  ← Stage 1+
│   ...                             │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Layer 2: 节点图（认知地图）       │
│   节点：用自然语言描述的关键地点  │
│   "近处西北方的果树"              │
│   "远处东边的水源"                │
│   隐藏字段：grid_pos（只给Executor）│
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Layer 3: 规划核                   │
│   greedy_nearest  → 最近原则     │
│   safe_path       → 避险原则     │  ← Stage 1+
│   resource_chain  → 多目标排序   │  ← Stage 2+
└──────┬───────────────────────────┘
       │
       ▼
   宏观行动序列：[goto(node_id), ...]
       │
       ▼
   Executor (Claude Sonnet via CLI) → 原子动作
```

## 关键设计：节点是抽象语言，不是坐标

LLM 决策看到的是：

```
当前节点图：
- self: 我自己
- food_NW_close: 近处西北方的果树
- food_E_mid:    中距东边的浆果丛
- water_E_far:   远处东边的水源
- obstacle_S:    南边一道石墙

规划核建议：先去 food_NW_close（最近）
```

而不是 `(2, -3)` 这种坐标。这强迫决策真的发生在抽象层级，也让一个决策能在不同坐标布局下泛化。

**Executor** 拿到 `goto(food_NW_close)` 后，才会查节点的 `_grid_pos` 字段反查具体坐标，输出 Crafter 的原子动作（move_north/move_west 等）。

## 渐进式 Stage

| Stage | 加什么 | 想验证什么 |
|---|---|---|
| **0** | `food_recognizer` + `greedy_nearest` | 最低配置能不能让 agent 不饿死 |
| 1 | + `threat_recognizer` + `safe_path` | 加威胁感知后死亡率下降多少 |
| 2 | + `wood/stone_recognizer` + `resource_chain` | 能不能解锁合成链 |
| 3 | 同识别核，换不同规划核 | "性格"差异（greedy vs safe vs explorer）对通关效率的影响 |

每个 Stage 是一组独立 commit + 独立结果记录。

## 实现栈

- **环境**：[Crafter](https://github.com/danijar/crafter)（2D Minecraft 简化版）
- **Executor LLM**：Claude Sonnet，通过 `claude` CLI 调用
- **语言**：Python

## 目录

```
实验1/
├── README.md                       # 你在看的这个
├── env/crafter_wrap.py             # Crafter 包装 + 状态序列化
├── llm/claude_cli.py               # subprocess 包装 claude -p
└── stages/
    └── stage0_food_only/
        ├── README.md               # Stage 0 具体说明
        ├── types.py                # Node / Graph 数据类
        ├── recognizers/food.py     # 食物识别核
        ├── graph.py                # 7×7 → 节点图
        ├── planner.py              # 规划核（greedy_nearest）
        ├── executor.py             # 节点 ID → 原子动作（Claude CLI）
        ├── run.py                  # 入口：跑一个 episode
        └── results/                # 每次跑的日志和结论
```

## 现在的状态

骨架阶段——接口和数据结构已经定型，具体逻辑等设计 review 通过后再实现。
