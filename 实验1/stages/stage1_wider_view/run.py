"""H5: 在 stage1_threat 之上扫描 view_radius。

不复制代码：直接复用 stage1_threat 的 graph/planner/executor，只改 view_radius。
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from env.crafter_wrap import CrafterEnv
from stages.stage1_threat.executor import execute
from stages.stage1_threat.graph import build_graph
from stages.stage1_threat.planner import greedy_nearest


# H5 finding: radius=8 dominates. scan.py 改这个变量做对比。
VIEW_RADIUS = 8


def run_episode(
    seed: int = 0,
    max_steps: int = 200,
    log_path: Path | None = None,
    verbose: bool = False,
) -> dict:
    env = CrafterEnv(seed=seed)
    semantic, self_state = env.reset()
    rng = random.Random(seed)

    step = 0
    done = False
    while step < max_steps and not done:
        graph = build_graph(semantic, self_state, view_radius=VIEW_RADIUS)
        plan = greedy_nearest(graph)
        atomic_actions = execute(plan, graph, semantic, rng=rng)
        for action in atomic_actions:
            semantic, self_state, reward, done, info = env.step(action)
            step += 1
            if done or step >= max_steps:
                break

    achievements = env.achievements()
    return {
        "seed": seed,
        "survived_steps": step,
        "died": done,
        "final_hp": self_state["hp"],
        "final_food": self_state["food"],
        "final_drink": self_state["drink"],
        "achievements_unlocked": [k for k, v in achievements.items() if v],
        "achievement_count": sum(1 for v in achievements.values() if v),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--view-radius", type=int, default=4)
    args = parser.parse_args()
    VIEW_RADIUS = args.view_radius
    print(json.dumps(run_episode(seed=args.seed, max_steps=args.max_steps), indent=2))
