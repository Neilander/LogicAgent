"""Stage 0 入口：跑一个 Crafter episode，记录指标和决策 trace。

Pipeline：
    raw obs → 识别核 → Graph → 规划核 → Executor (Claude) → atomic actions → env.step
"""

import argparse
import json
from pathlib import Path

from env.crafter_wrap import CrafterEnv
from .executor import execute
from .graph import build_graph
from .planner import greedy_nearest


def run_episode(seed: int = 0, max_steps: int = 200, log_path: Path | None = None) -> dict:
    env = CrafterEnv(seed=seed)
    obs, self_state = env.reset()

    trace = []
    step = 0
    while step < max_steps:
        graph = build_graph(obs, self_state)
        plan = greedy_nearest(graph)
        atomic_actions = execute(plan, graph, obs)

        for action in atomic_actions:
            obs, self_state, reward, done, info = env.step(action)
            trace.append({
                "step": step,
                "graph": [n.id for n in graph.nodes],
                "plan": plan,
                "action": action,
                "reward": reward,
            })
            step += 1
            if done or step >= max_steps:
                break
        if done:
            break

    metrics = {
        "survived_steps": step,
        "achievements": env.achievements(),
        "died": done and self_state.get("hp", 0) <= 0,
    }
    if log_path:
        log_path.write_text(json.dumps({"metrics": metrics, "trace": trace}, indent=2, ensure_ascii=False))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--log", type=Path, default=None)
    args = parser.parse_args()

    result = run_episode(seed=args.seed, max_steps=args.max_steps, log_path=args.log)
    print(json.dumps(result, indent=2, ensure_ascii=False))
