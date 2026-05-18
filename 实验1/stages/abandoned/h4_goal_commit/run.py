"""H4: food + water + threat 识别核 + committed_safe_need_path 规划核（带 goal commit）。"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from env.crafter_wrap import CrafterEnv
from stages.h4_goal_commit import planner as planner_mod
from stages.h4_goal_commit.executor import execute
from stages.h4_goal_commit.graph import build_graph, graph_to_text
from stages.h4_goal_commit.planner import greedy_nearest


def run_episode(
    seed: int = 0,
    max_steps: int = 200,
    log_path: Path | None = None,
    verbose: bool = False,
) -> dict:
    env = CrafterEnv(seed=seed)
    semantic, self_state = env.reset()
    rng = random.Random(seed)
    planner_mod.reset()   # H4: 清空 commitment 状态

    trace = []
    step = 0
    done = False
    while step < max_steps and not done:
        graph = build_graph(semantic, self_state)
        plan = greedy_nearest(graph)
        atomic_actions = execute(plan, graph, semantic, rng=rng)

        if verbose:
            print(f"\n--- step {step} ---")
            print(graph_to_text(graph))
            print(f"plan: {plan}")
            print(f"actions: {atomic_actions}")

        for action in atomic_actions:
            semantic, self_state, reward, done, info = env.step(action)
            trace.append({
                "step": step,
                "graph_nodes": [n.id for n in graph.nodes],
                "plan": plan,
                "action": action,
                "reward": reward,
                "hp": self_state["hp"],
                "food": self_state["food"],
                "drink": self_state["drink"],
            })
            step += 1
            if done or step >= max_steps:
                break

    achievements = env.achievements()
    metrics = {
        "seed": seed,
        "survived_steps": step,
        "died": done,
        "final_hp": self_state["hp"],
        "final_food": self_state["food"],
        "final_drink": self_state["drink"],
        "achievements_unlocked": [k for k, v in achievements.items() if v],
        "achievement_count": sum(1 for v in achievements.values() if v),
    }
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(
            {"metrics": metrics, "trace": trace}, indent=2, ensure_ascii=False
        ))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    result = run_episode(
        seed=args.seed,
        max_steps=args.max_steps,
        log_path=args.log,
        verbose=args.verbose,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
