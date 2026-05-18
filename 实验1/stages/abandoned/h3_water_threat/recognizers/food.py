"""食物识别核：在 semantic 视图里找所有"可吃"的 tile。

Crafter 约定（反直觉，要记住）：
  - world_pos = (x, y)，semantic 索引 sem[x, y]
  - move_right 让 x 增加，move_down 让 y 增加
  - player 在 sem 里的位置 = world_pos，不是固定 (32, 32)

可吃：
  - plant (id=18): 成熟果实，按 'do' 吃 → food +1
  - cow   (id=14): 杀掉 → food +6
"""

import numpy as np

FOOD_TILE_IDS = {
    18: "plant",
    14: "cow",
}


def recognize_food(
    semantic: np.ndarray,
    player_pos: tuple[int, int],
    view_radius: int = 4,
) -> list[tuple[int, int, str]]:
    """返回 [(dx, dy, kind), ...]，dx/dy 是相对玩家的偏移。

    view_radius=4 → 9×9 视野（人能"看见"的近场）。
    """
    px, py = int(player_pos[0]), int(player_pos[1])
    results: list[tuple[int, int, str]] = []
    xmin = max(0, px - view_radius)
    xmax = min(semantic.shape[0], px + view_radius + 1)
    ymin = max(0, py - view_radius)
    ymax = min(semantic.shape[1], py + view_radius + 1)

    for x in range(xmin, xmax):
        for y in range(ymin, ymax):
            tile_id = int(semantic[x, y])
            if tile_id in FOOD_TILE_IDS:
                dx, dy = x - px, y - py
                if dx == 0 and dy == 0:
                    continue
                results.append((dx, dy, FOOD_TILE_IDS[tile_id]))
    return results
