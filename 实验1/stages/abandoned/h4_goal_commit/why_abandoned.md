# H4: goal-commit planner — ABANDONED

## 假设

H3 失败原因诊断：每帧重新选 primary kind 导致 agent 在 food/water 间震荡。
H4 加入 commitment 机制：一旦选定一个类目（food 或 water），坚持 COMMIT_STEPS=12 步再换。
威胁来了会打断 commitment（这是合理的 interrupt）。

## 结果（5 seeds × 400）

| Metric | Stage 0 | **H2 (current best)** | H3 | **H4** |
|---|---|---|---|---|
| median | 175 | 182-206 | 178 | **196** |
| mean | 150 | 186-200 | 184.8 | 196.6 |
| hp_zero | 4/5 | 2/5 | 4/5 | **3/5** |
| starve/thirst | 1/5 | 3/5 | 1/5 | 2/5 |
| **eat_cow** | 100% | 80% | 60% | **60%** |
| collect_drink | 20% | 20% | 40% | 40% |

## 为什么 abandoned

- **eat_cow 60% < 80% 守护线**（同 H3）
- 没能超过 H2 的中位数（196 vs 206）
- hp_zero 比 H2 多（3 vs 2）

## 但 H4 证明了什么

vs H3：commit 机制是有效的（median +10%, hp_zero ↓ 1/5）
**所以"commit 机制本身"是一个 reusable 的发现，只是放在 water+threat 组合里仍然不够好。**

## 越来越清晰的 pattern

H1（water-only）、H3（water+threat）、H4（water+threat+commit）**都**因为加 water 而让 eat_cow 跌破 80%。

回看 baseline：1/5 死于渴。**渴并不是主要瓶颈**，HP 是。
所以加 water_recognizer 的 marginal benefit 远小于它对 food acquisition 的 opportunity cost。

**强烈建议未来不要再尝试 + water 直接组合**，要么：
- 让 water 只在 drink < 3 时激活（高门槛触发，避免日常干扰）
- 或者让 water 完全在另一个子规划核里（如 emergency planner）

## 留下的代码

完整代码在本文件夹保留。**`planner.py` 里的 commitment 机制可能在未来 H 里重用**。
