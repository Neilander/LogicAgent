# H5: view_radius 扫描结果

## 实验设置

- 基底：stage1_threat（食物+威胁识别核 + safe_path 规划核）
- 唯一变量：view_radius ∈ {4, 6, 8}
- 5 seeds × 400 max_steps

## 数据

| radius | median | mean | eat_cow | hp_zero deaths | per_seed |
|---|---|---|---|---|---|
| 4（baseline of H2） | 182 | 185.8 | 100% | 5/5 | 212, 164, 194, 177, 182 |
| 6 | 189 | 192.2 | 80% | 2/5 | 221, 166, 182, 203, 189 |
| **8** | **189** | **205.2** | **100%** | **2/5** | 240, 228, 182, 187, 189 |

## vs Stage 0 baseline（radius=4，没有 threat 核）

| metric | Stage 0 | **stage1_wider_view (r=8)** |
|---|---|---|
| median | 175 | **189** (+8%) |
| mean | 150 | **205.2** (+37%) |
| eat_cow | 100% | **100%** ✓ 完全保住 |
| hp_zero deaths | 4/5 | **2/5** halved |

## 结论

- **radius=8 是当前最佳配置**
- 比 stage1_threat (r=4) 在 mean 上 +10%、hp_zero 减半、eat_cow 100% 完全保住
- 两个 seed 突破 220 步（240/228）

## 为什么 work

更宽视野 = 威胁能在更远距离被识别 = `safe_path` 有更多帧来规划绕路。
radius=4 时，威胁进入视野时往往已经 close，导致只能 flee（被动）。
radius=8 时，威胁在 far/mid 就被看到，agent 在选择 food 路径时可以预先避开它（主动）。

注意 radius=6 的 eat_cow 反而退到 80%——可能是 radius=6 把更多"中距威胁"加入视野，让 threat-penalty 误判过强；radius=8 给了更多 spatial context 让规划平衡。**不是单调函数**——好像有个 sweet spot。

## 边界

- radius=12 / 16 没测——可能更好也可能 noise 太多
- 5 seeds 是小样本，RNG variance 不可忽略
- 这个发现仅针对 stage1_threat 配置——换个 planner 可能 sweet spot 不同
