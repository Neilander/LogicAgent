"""食物识别核：扫 raw view 找出所有"可吃"的 tile。

Crafter 里能直接吃的：plant（成熟果树）、cow（杀掉吃肉）。
Stage 0 我们先只识别 plant，避免引入"杀生物"动作。
"""

from typing import Any

FOOD_TILE_TYPES = {"plant"}   # Stage 0 范围内的食物种类


def recognize_food(raw_obs: Any) -> list[tuple[int, int]]:
    """从 Crafter 的 raw observation 里抽出所有食物 tile 的相对坐标。

    Args:
        raw_obs: Crafter env.step() 返回的 observation
                 （格式由 env/crafter_wrap.py 标准化后决定）

    Returns:
        list of (dx, dy) — 相对于 agent 的视野内偏移
    """
    raise NotImplementedError
