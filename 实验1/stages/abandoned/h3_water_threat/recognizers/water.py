"""水识别核：在 semantic 视图里找所有水 tile（id=1）。

Crafter 里：站在 water 相邻 tile，朝它 face 后 do → drink +1。
"""

import numpy as np

WATER_TILE_ID = 1


def recognize_water(
    semantic: np.ndarray,
    player_pos: tuple[int, int],
    view_radius: int = 4,
) -> list[tuple[int, int]]:
    """返回 [(dx, dy), ...]，dx/dy 是相对玩家的偏移。"""
    px, py = int(player_pos[0]), int(player_pos[1])
    results: list[tuple[int, int]] = []
    xmin = max(0, px - view_radius)
    xmax = min(semantic.shape[0], px + view_radius + 1)
    ymin = max(0, py - view_radius)
    ymax = min(semantic.shape[1], py + view_radius + 1)

    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            if int(semantic[x, y]) == WATER_TILE_ID:
                dx, dy = x - px, y - py
                if dx == 0 and dy == 0:
                    continue
                results.append((dx, dy))
    return results
