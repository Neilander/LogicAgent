"""跑一个 episode，把每一步的可视化数据 dump 成 JSON。

输出字段（每个 step）：
  - step: int
  - image_b64: base64 PNG，Crafter 当前帧（64×64 → 显示时放大）
  - self_state: {hp, food, drink, energy, world_pos}
  - graph: [{id, description, kind, direction, distance, dx, dy}, ...]
  - plan: {action, target?, reason}
  - atomic_actions: [str, ...]
  - reward: float
"""

import argparse
import base64
import io
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from env.crafter_wrap import CrafterEnv
from stages.stage0_food_only.executor import execute
from stages.stage0_food_only.graph import build_graph
from stages.stage0_food_only.planner import greedy_nearest


def image_to_b64(img: np.ndarray) -> str:
    pil = Image.fromarray(img.astype(np.uint8))
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def graph_to_dict(graph) -> list[dict]:
    return [
        {
            "id": n.id,
            "description": n.description,
            "kind": n.kind,
            "direction": n.direction,
            "distance": n.distance,
            "dx": int(n._grid_pos[0]),
            "dy": int(n._grid_pos[1]),
            "extra": n.extra,
        }
        for n in graph.nodes
    ]


def dump_episode(seed: int, max_steps: int, out_path: Path) -> dict:
    env = CrafterEnv(seed=seed)
    semantic, self_state = env.reset()
    rng = random.Random(seed)

    # 第一帧图像：reset 后从 env 内部拿
    img = env._env.render()

    steps_data = []
    step = 0
    done = False
    last_plan = None
    last_atomic_queue: list[str] = []

    while step < max_steps and not done:
        graph = build_graph(semantic, self_state)
        plan = greedy_nearest(graph)
        atomic_actions = execute(plan, graph, semantic, rng=rng)
        last_plan = plan

        for action in atomic_actions:
            steps_data.append({
                "step": step,
                "image_b64": image_to_b64(img),
                "self_state": {
                    "hp": self_state["hp"], "food": self_state["food"],
                    "drink": self_state["drink"], "energy": self_state["energy"],
                    "world_pos": list(map(int, self_state["world_pos"])),
                },
                "graph": graph_to_dict(graph),
                "plan": plan,
                "action_this_step": action,
                "atomic_queue": list(atomic_actions),
            })

            semantic, self_state, reward, done, info = env.step(action)
            img = env._env.render()
            steps_data[-1]["reward"] = float(reward)
            step += 1
            if done or step >= max_steps:
                break

    final = {
        "seed": seed,
        "survived_steps": step,
        "died": done,
        "final_state": {
            "hp": self_state["hp"], "food": self_state["food"],
            "drink": self_state["drink"], "energy": self_state["energy"],
        },
        "achievements_unlocked": [k for k, v in env.achievements().items() if v],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(
        {"meta": final, "steps": steps_data},
        ensure_ascii=False,
    ))
    print(f"Wrote {len(steps_data)} steps → {out_path}")
    print(f"Meta: {final}")
    return final


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "trace.json")
    args = parser.parse_args()
    dump_episode(args.seed, args.max_steps, args.out)
