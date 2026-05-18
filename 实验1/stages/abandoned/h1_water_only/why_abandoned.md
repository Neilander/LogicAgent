# H1: water-only — ABANDONED

## 假设

加 `water_recognizer` + `need_based_nearest` 规划核（按 food/drink 缺口选目标，加 satiation 阈值），让 agent 不渴死。

## 结果（5 seeds × 400 max_steps）

| Metric | Stage 0 baseline | H1 v1 (no satiation) | **H1 v2 (with satiation)** |
|---|---|---|---|
| median survival | **175** | 153 | 164 |
| mean survival | 150 | 146.8 | 179 |
| death rate | 100% | 100% | 100% |
| death cause hp_zero | 4/5 | 5/5 | **5/5** |
| **eat_cow** | **100%** | 80% | **60%** ❌ |
| collect_drink | 20% | 60% | **60%** ✓ |
| final drink mean | 2.4 | 7.4 | 4.2 |

## 为什么 abandoned

- **eat_cow 解锁率从 100% → 60%**——核心 agency 信号回退
- median survival 没改善（164 < 175）
- death rate 仍 100%，且 hp_zero 增加到 5/5（agent 没死于渴反而更容易死于打）

## 根因

**加 water 但不加 threat 是错误组合**。加完 water 后 agent 在地图上移动更多（追 food → 追 water → 追 food 循环），暴露在 zombie 区域时间更长。
单一识别核扩展（只加 water）改变了行为分布但没解决主要死因（被打），反而 trade 走了部分 food acquisition。

## 留下的代码

完整代码在本文件夹下保留，包括 `recognizers/water.py`、改造过的 `graph.py`、`planner.py（need_based_nearest）`。

**这些代码会在 H3（water + threat 协同）里重用——预期 H3 应该能体现 water 的价值。**

## 启示

- 不要在没有 threat 感知的情况下加任何"会让 agent 移动更多"的核
- "+1 个识别核" 不总是 +1 能力，可能是 trade-off
- pass 标准里 eat_cow 不能跌破 80% 是个有效的 guard
