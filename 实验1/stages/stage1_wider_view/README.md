# Stage 1: wider view (H5)

**One-line：把 `stage1_threat` 的 `view_radius` 从 4 调到 8——纯参数调优，无新核。**

不复制代码，直接 import `stage1_threat` 的所有组件，只覆盖 `VIEW_RADIUS` 全局。

## 文件

- `run.py` — `run_episode(seed, max_steps)` 调用 stage1_threat 组件，但传 view_radius=8
- `scan.py` — 复现 H5 实验：扫描 view_radius ∈ {4, 6, 8} × 5 seeds，输出对比表
- `results/scan_4_6_8.json` — 扫描原始数据

## 跑

```
python stages/stage1_wider_view/scan.py       # 完整扫描
python stages/stage1_wider_view/run.py        # 单次（默认 radius=8）
python evals/benchmark.py stages.stage1_wider_view --seeds 0,1,2,3,4 --max-steps 400
```
