"""扫描脚本：对 view_radius ∈ {4, 6, 8} 各跑 5 seeds × 400 steps，输出对比。"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stages.h5_view_radius import run as run_module

SEEDS = [0, 1, 2, 3, 4]
MAX_STEPS = 400
RADII = [4, 6, 8]


def summarize(results):
    surv = [r["survived_steps"] for r in results]
    deaths = sum(1 for r in results if r["died"])
    all_achs = set()
    for r in results:
        all_achs.update(r["achievements_unlocked"])
    ach_rates = {a: sum(1 for r in results if a in r["achievements_unlocked"]) / len(results)
                 for a in sorted(all_achs)}
    final_hp = [r["final_hp"] for r in results]
    final_food = [r["final_food"] for r in results]
    final_drink = [r["final_drink"] for r in results]
    death_cause = {"hp_zero": 0, "starve_or_thirst": 0, "timeout_alive": 0}
    for r in results:
        if not r["died"]:
            death_cause["timeout_alive"] += 1
        elif r["final_hp"] <= 0 and r["final_food"] > 0 and r["final_drink"] > 0:
            death_cause["hp_zero"] += 1
        else:
            death_cause["starve_or_thirst"] += 1
    return {
        "median": statistics.median(surv),
        "mean": round(statistics.mean(surv), 1),
        "death_rate": deaths / len(results),
        "death_cause": death_cause,
        "ach_rates": ach_rates,
        "final_mean": {"hp": round(statistics.mean(final_hp), 1),
                       "food": round(statistics.mean(final_food), 1),
                       "drink": round(statistics.mean(final_drink), 1)},
        "per_seed": [(r["seed"], r["survived_steps"]) for r in results],
    }


def main():
    table = {}
    for r in RADII:
        run_module.VIEW_RADIUS = r
        results = [run_module.run_episode(seed=s, max_steps=MAX_STEPS) for s in SEEDS]
        table[r] = summarize(results)

    out_path = Path(__file__).parent / "results" / "scan_4_6_8.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(table, indent=2, ensure_ascii=False))

    print(f"{'radius':>8} {'median':>8} {'mean':>8} {'eat_cow':>8} {'hp_zero':>8} {'per_seed'}")
    for r, s in table.items():
        per = ",".join(f"{p[1]}" for p in s["per_seed"])
        print(f"{r:>8} {s['median']:>8} {s['mean']:>8.1f} {s['ach_rates'].get('eat_cow', 0):>8.0%} "
              f"{s['death_cause']['hp_zero']:>8} [{per}]")


if __name__ == "__main__":
    main()
