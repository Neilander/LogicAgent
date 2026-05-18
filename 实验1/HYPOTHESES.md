# 假设清单

中央索引：每个加入的假设、状态、和它在仓库里的位置。

**评估方法**：5 seeds (0-4) × 200 max_steps，跑 `evals/benchmark.py <stage_module>` 得到。

**通过标准**：存活步数中位数 ≥ baseline + 25%，且 `eat_cow` 解锁率不退化。

| ID | 假设 | 状态 | 位置 | 中位数 | 关键成就 | 备注 |
|---|---|---|---|---|---|---|
| H0 | baseline: food_recognizer + greedy_nearest | ✅ baseline | `stages/stage0_food_only/` | 175 | eat_cow 100% | 4/5 死于 zombie |
| H1 | + water_recognizer + need-based priority | ⛔ abandoned | `stages/abandoned/h1_water_only/` | 164 | eat_cow **60%** ↓ | water 单加导致 wander 加剧 |
| H2 | + threat_recognizer + safe_path 规划核 | ⚠️ 保留（部分通过） | `stages/stage1_threat/` | 182–206 | eat_cow 80% (守护线) | **hp_zero 死 4→2/5**，seed 0 从 48→209 步；trade-off 是 starve/thirst 增多 |
| H3 | water + threat 双新核协同 | ⛔ abandoned | `stages/abandoned/h3_water_threat/` | 178 | eat_cow **60%** ↓ | dual-kernel 互相干扰；目标频繁切换让 agent 更易吃伤害 |
| H4 | goal-commit planner（fix H3 oscillation） | ⛔ abandoned | `stages/abandoned/h4_goal_commit/` | 196 | eat_cow **60%** ↓ | commit 机制本身有效（vs H3 +10%），但仍打不过 H2；水的"机会成本"问题继续 |
| H5 | view_radius 扫描（4/6/8） | ✅ 通过 | `stages/stage1_wider_view/` | 189 (mean 205) | eat_cow 100% | **radius=8 最佳**：mean +10% vs stage1_threat、hp_zero 减半，eat_cow 完全保住 |

## 状态约定

- ✅ baseline 或 通过保留
- ⏳ 待办 / 进行中
- ⛔ 未通过，已移到 `stages/abandoned/<name>/`，folder 里有 `why_abandoned.md`

## 流水

记录在每个 stage 自己的 `results/` 下；本文件只放摘要。

---

# 第一轮（H1-H5）总结

## 保留 vs 抛弃

| 保留（`stages/stage1_*`） | 抛弃（`stages/abandoned/`） |
|---|---|
| **stage1_threat** (H2): +threat_recognizer + safe_path | h1_water_only (H1) |
| **stage1_wider_view** (H5): stage1_threat + radius=8 | h3_water_threat (H3) |
| | h4_goal_commit (H4) |

## 最终最佳 = stage1_wider_view

| metric | Stage 0 baseline | **stage1_wider_view** | Δ |
|---|---|---|---|
| median survival | 175 | 189 | +8% |
| mean survival | 150 | 205 | **+37%** |
| eat_cow | 100% | **100%** | 保住 |
| hp_zero deaths | 4/5 | **2/5** | 减半 |
| 单 seed 最高 | 195 | **240** | +23% |

## 三条核心发现

1. **威胁识别核是主要收益来源**（H2 单一改动让 hp_zero 4/5 → 2/5，seed 0 从 48 → 209 步）
2. **加 water 是负 ROI**（H1/H3/H4 三次都因为加 water 导致 eat_cow 跌破 80%；baseline 只有 1/5 死于渴，水的边际价值低）
3. **view_radius=8 比 4 显著好**（不是越大越好，但更宽视野让 threat-aware 规划提前发挥）

## 三条架构层面学到的事

1. **"+1 kernel ≠ +1 capability"**——多次实验中加 kernel 反而降低 eat_cow，因为新 kernel 改变 agent 的移动分布
2. **goal-commit 机制本身有效**（H4 改善 H3：median +10%），但放错了组合（仍带 water）
3. **死因分布是更精确的成功信号**，比 median survival 敏感得多——能识别"威胁问题已经解决，新瓶颈是 X"

## 留给下一轮的候选

（**未执行**，等 user review 后决定是否做第二轮）

- **H6**: stage1_wider_view + goal-commit（去掉 water，把 commit 机制叠加到 winning config）
- **H7**: 只在 drink < 3 时激活 water_recognizer（紧急触发），避开 H1/H3/H4 的日常干扰
- **H8**: 把 deterministic executor 换成 Claude Sonnet executor，对比同样 node graph 下 LLM 决策质量
- **H9**: 加 cow vs plant 分别识别核（plant 静态可重复采集、cow 移动给大食量）
- **H10**: view_radius=12/16 测试是否还有 sweet spot 之外的 plateau
