"""Executor：把宏观动作（goto / explore）翻译成 Crafter 原子动作。

Stage 0 用 **确定性 Executor**（不调 LLM），目的是先验证"识别核+节点图+规划核"
这条 pipeline 真的能让 agent 不饿死。LLM Executor 留到 Stage 0b 做对比。

策略：
  - goto(node)：查节点的 _grid_pos (dx, dy)，选 |dx|/|dy| 更大的轴先走一步。
    走到相邻（max(|dx|,|dy|)==1）就触发 'do' 吃 / 收。
  - explore：朝当前未走过最多的方向连走两步（朴素 epsilon-greedy 探索）。
"""

import random
from typing import Optional

import numpy as np

from env.crafter_wrap import TILE_NAME_TO_ID, WALKABLE_TILE_IDS
from .types import Graph, Node


def execute(
    plan: dict,
    graph: Graph,
    semantic: np.ndarray,
    explore_state: Optional[dict] = None,
    rng: Optional[random.Random] = None,
) -> list[str]:
    rng = rng or random.Random()
    player_pos = graph.self_state["world_pos"]
    if plan["action"] == "goto":
        node = graph.by_id(plan["target"])
        if node is None:
            return ["noop"]
        return _atomic_for_goto(node, semantic, player_pos)
    elif plan["action"] == "explore":
        return _atomic_for_explore(semantic, player_pos, rng)
    return ["noop"]


def _atomic_for_goto(node: Node, semantic: np.ndarray, player_pos) -> list[str]:
    dx, dy = node._grid_pos
    # 相邻 → 朝目标方向并触发 do
    if max(abs(dx), abs(dy)) <= 1:
        face_action = _face_dir(dx, dy)
        return [face_action, "do"] if face_action else ["do"]

    # 选大轴先走
    if abs(dx) >= abs(dy):
        primary = "move_right" if dx > 0 else "move_left"
        secondary = "move_down" if dy > 0 else ("move_up" if dy < 0 else None)
    else:
        primary = "move_down" if dy > 0 else "move_up"
        secondary = "move_right" if dx > 0 else ("move_left" if dx < 0 else None)

    # primary 不通就 fall back
    if _tile_after_move(semantic, primary, player_pos) not in WALKABLE_TILE_IDS and secondary:
        if _tile_after_move(semantic, secondary, player_pos) in WALKABLE_TILE_IDS:
            return [secondary]
    return [primary]


def _atomic_for_explore(
    semantic: np.ndarray,
    player_pos,
    rng: random.Random,
) -> list[str]:
    """没看到食物时的探索：朝一个 walkable 方向走 2 步。"""
    candidates = []
    for action in ["move_right", "move_down", "move_left", "move_up"]:
        if _tile_after_move(semantic, action, player_pos) in WALKABLE_TILE_IDS:
            candidates.append(action)
    if not candidates:
        return ["noop"]
    return [rng.choice(candidates), rng.choice(candidates)]


def _face_dir(dx: int, dy: int) -> Optional[str]:
    """把"朝目标走一步 / 转向"映射到 Crafter 动作。Crafter 里 move_* 既转向也移动。"""
    if abs(dx) >= abs(dy):
        if dx > 0:
            return "move_right"
        if dx < 0:
            return "move_left"
    if dy > 0:
        return "move_down"
    if dy < 0:
        return "move_up"
    return None


_DIR_TO_DELTA = {
    "move_right": (1, 0),    # +x
    "move_left": (-1, 0),    # -x
    "move_down": (0, 1),     # +y
    "move_up": (0, -1),      # -y
}


def _tile_after_move(semantic: np.ndarray, action: str, player_pos) -> int:
    """看 player 朝 action 走一步后那个 tile 的 id。semantic 索引是 [x, y]。"""
    if action not in _DIR_TO_DELTA:
        return -1
    ddx, ddy = _DIR_TO_DELTA[action]
    nx, ny = int(player_pos[0]) + ddx, int(player_pos[1]) + ddy
    if 0 <= nx < semantic.shape[0] and 0 <= ny < semantic.shape[1]:
        return int(semantic[nx, ny])
    return -1
