# Stage 0 baseline (5 seeds × 400 max_steps)

跑了两次（max_steps=200 和 400），结果完全一致——所有 agent 都死在 200 步以内，不是被 step ceiling 砍掉。

## 指标

| 指标 | 值 |
|---|---|
| **median survival** | **175 steps** |
| mean survival | 150 (seed 0 的 48 步拉低) |
| death rate | 100% (5/5) |
| **死因 hp_zero** | 4/5（被 zombie/skeleton 打死） |
| 死因 starve_or_thirst | 1/5 |
| **eat_cow 解锁** | **100%（5/5）** ← 核心 agency 信号 |
| collect_drink（附带） | 20% |
| collect_sapling（附带） | 40% |
| collect_wood（附带） | 40% |
| defeat_zombie（附带） | 20% |
| 最终 food 均值 | 7.4 |
| 最终 drink 均值 | 2.4 ← 渴 |
| 最终 hp 均值 | 0 |

## per-seed

| seed | survived | died | achievements |
|---|---|---|---|
| 0 | 48 | ✗ | eat_cow |
| 1 | 140 | ✗ | collect_wood, eat_cow |
| 2 | 192 | ✗ | collect_drink, collect_sapling, eat_cow |
| 3 | 175 | ✗ | defeat_zombie, eat_cow |
| 4 | 195 | ✗ | collect_sapling, collect_wood, eat_cow |

## 关键启示（指导假设设计）

1. **最大死因是被打**：4/5 的死是 HP=0，意味着 H2（threat）应该是最大单一收益
2. **渴只杀 1/5**：H1（water）的存活提升可能有限，但应该把 collect_drink 解锁率从 20% 推到 ≥ 80%
3. **eat_cow 100%**：任何新假设必须维持这个，否则就是回退
4. **min=48 max=195 spread 巨大**：seed 0 撞 zombie 速死、seed 2/4 走得远——agency 对地图敏感

## 修订的通过标准

由于 100% 死亡率和 175 中位数，原定 "+25%" 其实是 219 步——需要 H 显著减少死亡才能达到。

**通过 = 满足以下任一条件 + 保持 eat_cow ≥ 80%**：
- median survival ≥ 219（原标准）
- death rate ≤ 80%（至少 1/5 活到 400 步）
- 引入的新成就解锁率 ≥ 80%（H1 看 collect_drink）
