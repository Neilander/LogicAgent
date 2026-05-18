"""威胁识别核：在 semantic 视图里找所有威胁（zombie / skeleton / arrow）。

Crafter 里：
  - zombie (id=15): 近战，相邻时攻击，造成 2 伤害
  - skeleton (id=16): 远程，会射箭
  - arrow (id=17): 飞行中的箭，碰到 player 也会伤害
"""

import numpy as np

THREAT_TILE_IDS = {
    15: "zombie",
    16: "skeleton",
    17: "arrow",
}


def recognize_threats(
    semantic: np.ndarray,
    player_pos: tuple[int, int],
    view_radius: int = 4,
) -> list[tuple[int, int, str]]:
    """返回 [(dx, dy, kind), ...]，dx/dy 是相对玩家的偏移。"""
    px, py = int(player_pos[0]), int(player_pos[1])
    results: list[tuple[int, int, str]] = []
    xmin = max(0, px - view_radius)
    xmax = min(semantic.shape[0], px + view_radius + 1)
    ymin = max(0, py - view_radius)
    ymax = min(semantic.shape[1], py + view_radius + 1)

    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            tile_id = int(semantic[x, y])
            if tile_id in THREAT_TILE_IDS:
                dx, dy = x - px, y - py
                if dx == 0 and dy == 0:
                    continue
                results.append((dx, dy, THREAT_TILE_IDS[tile_id]))
    return results
