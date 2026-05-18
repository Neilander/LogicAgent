# H3: water + threat dual-kernel — ABANDONED

## 假设

把 H1 的 water_recognizer + need-based priority 和 H2 的 threat_recognizer + safe_path 合并，组合 planner `safe_need_path`。
**预期**：H1 trade-off（被打）和 H2 trade-off（饿/渴）相互补偿。

## 结果（5 seeds × 400 max_steps）

| Metric | Stage 0 | H2 (threat-only) | **H3 (water+threat)** |
|---|---|---|---|
| median | 175 | 182-206 | **178** ↓ vs H2 |
| mean | 150 | 186-200 | 184.8 |
| **hp_zero deaths** | 4/5 | **2/5** | **4/5** ↑ 回退 |
| starve/thirst deaths | 1/5 | 3/5 | 1/5 ↓ |
| **eat_cow** | **100%** | 80% | **60%** ❌ |
| collect_drink | 20% | 20% | 40% ↑ |

## 为什么 abandoned

- **eat_cow 跌破 80% 守护线**（60%）
- hp_zero deaths 从 H2 的 2/5 回退到 4/5（threat avoidance 失效）
- median 比 H2 还低
- 唯一改进是 collect_drink（+20pp），但不足以补偿其他回退

## 失败分析

**两个 kernel 互相干扰**而不是协同：

1. need-based 选择会让 agent 在 food 和 water 之间频繁切换目标，移动路径变得不稳定
2. 不稳定的移动让 agent 更可能跨过中距威胁（mid threat 没被 flee_from 触发，但下一步可能变成 close threat → 此时已经吃了攻击）
3. H2 单一 food 目标时移动是单向的，agent 经过的 tile 集合更小、更可预测，反而更安全
4. 加 water 后，水域往往在开阔区域，靠近水域 = 靠近怪物刷新点

## 启示

- **+1 kernel ≠ +1 capability**：H1 失败给的教训在 H3 又重演了一次
- planner 的目标切换成本是真实的——切换时 agent 可能放弃了"过去"的安全路径
- 解决方向：H4 需要一个能"承诺"目标的 planner，不能每帧重新选

## 留下的代码

完整代码在本文件夹保留。water.py 已经多次使用，可以视为通过验证的"模块"。
失败的不是 water 这个 recognizer 本身，是 planner 的组合策略。
