"""跨 stage 通用 benchmark：对一个 stage 跑 N 个 seed × max_steps 步，汇总指标。

用法：
    python3 evals/benchmark.py stages.stage0_food_only
    python3 evals/benchmark.py stages.stage1_water --seeds 0,1,2,3,4 --max-steps 200

每个 stage 模块必须暴露 run_episode(seed, max_steps) -> dict。

输出指标：
  - survived_steps: median / mean / min / max
  - death_rate: 死亡的 seed 占比
  - achievements: 每个成就的解锁率
  - final_state: 平均 HP / food / drink
"""

import argparse
import importlib
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def benchmark(stage_module: str, seeds: list[int], max_steps: int) -> dict:
    mod = importlib.import_module(stage_module + ".run")
    run_fn = mod.run_episode
    results = []
    for s in seeds:
        r = run_fn(seed=s, max_steps=max_steps)
        results.append(r)
    return summarize(stage_module, results, max_steps)


def summarize(stage_module: str, results: list[dict], max_steps: int) -> dict:
    surv = [r["survived_steps"] for r in results]
    deaths = sum(1 for r in results if r["died"])
    final_hp = [r.get("final_hp", 0) for r in results]
    final_food = [r.get("final_food", 0) for r in results]
    final_drink = [r.get("final_drink", 0) for r in results]

    # union of all achievements seen
    all_achs: set[str] = set()
    for r in results:
        all_achs.update(r.get("achievements_unlocked", []))
    ach_rates = {}
    for a in sorted(all_achs):
        ach_rates[a] = sum(1 for r in results if a in r.get("achievements_unlocked", [])) / len(results)

    # death by cause approximation
    death_cause = {"hp_zero": 0, "starve_or_thirst": 0, "timeout_alive": 0}
    for r in results:
        if not r["died"]:
            death_cause["timeout_alive"] += 1
        elif r.get("final_hp", 0) <= 0 and r.get("final_food", 9) > 0 and r.get("final_drink", 9) > 0:
            death_cause["hp_zero"] += 1
        else:
            death_cause["starve_or_thirst"] += 1

    return {
        "stage": stage_module,
        "n_seeds": len(results),
        "max_steps": max_steps,
        "survived_steps": {
            "median": statistics.median(surv),
            "mean": round(statistics.mean(surv), 1),
            "min": min(surv),
            "max": max(surv),
        },
        "death_rate": deaths / len(results),
        "death_cause": death_cause,
        "final_state_mean": {
            "hp": round(statistics.mean(final_hp), 1),
            "food": round(statistics.mean(final_food), 1),
            "drink": round(statistics.mean(final_drink), 1),
        },
        "achievement_rates": ach_rates,
        "per_seed": [{"seed": r["seed"], "survived": r["survived_steps"], "died": r["died"],
                      "ach": r.get("achievements_unlocked", [])} for r in results],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", help="模块路径，如 stages.stage0_food_only")
    parser.add_argument("--seeds", default="0,1,2,3,4")
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--out", type=Path, default=None, help="将结果 JSON 写到这里")
    args = parser.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    r = benchmark(args.stage, seeds, args.max_steps)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(r, indent=2, ensure_ascii=False))
