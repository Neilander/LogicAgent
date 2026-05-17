"""Crafter 环境包装。

Crafter 给的：
  - obs: 64×64×3 图像（我们不用，识别核走 semantic）
  - info['semantic']: 64×64 tile-id 矩阵，player 在 (32, 32) 中心
  - info['inventory']: 含 health/food/drink/energy + 各种资源
  - info['player_pos']: 世界绝对坐标（这里我们只用相对坐标做决策）

识别核直接消费 semantic tile id，所以不用做视觉感知。
"""

from typing import Any

import crafter
import numpy as np


# Crafter 的 tile id ↔ 名字（从 env._sem_view._mat_ids / _obj_ids 抽出的常量）
TILE_ID_TO_NAME = {
    0: "void", 1: "water", 2: "grass", 3: "stone", 4: "path",
    5: "sand", 6: "tree", 7: "lava", 8: "coal", 9: "iron",
    10: "diamond", 11: "table", 12: "furnace",
    13: "player", 14: "cow", 15: "zombie", 16: "skeleton",
    17: "arrow", 18: "plant",
}
TILE_NAME_TO_ID = {v: k for k, v in TILE_ID_TO_NAME.items()}
WALKABLE_TILE_IDS = {TILE_NAME_TO_ID[n] for n in ["grass", "path", "sand"]}
PLAYER_CENTER = (32, 32)


class CrafterEnv:
    """薄包装，把 step / reset 的返回拍成 (obs, self_state, ...)。"""

    def __init__(self, seed: int = 0):
        self._env = crafter.Env(seed=seed)
        self._last_info: dict = {}
        self._step_count = 0

    @property
    def action_names(self) -> list[str]:
        return list(self._env.action_names)

    def reset(self) -> tuple[np.ndarray, dict]:
        img = self._env.reset()
        # crafter 的 reset 不返回 info，我们 step 一个 noop 拿到 semantic
        img, reward, done, info = self._env.step(0)
        self._last_info = info
        self._step_count = 1
        return info["semantic"], self._self_state(info)

    def step(self, action_name: str) -> tuple[np.ndarray, dict, float, bool, dict]:
        action_id = self._env.action_names.index(action_name)
        img, reward, done, info = self._env.step(action_id)
        self._last_info = info
        self._step_count += 1
        return info["semantic"], self._self_state(info), float(reward), bool(done), info

    def achievements(self) -> dict[str, bool]:
        return dict(self._last_info.get("achievements", {}))

    def step_count(self) -> int:
        return self._step_count

    @staticmethod
    def _self_state(info: dict) -> dict:
        inv = info.get("inventory", {})
        return {
            "hp": inv.get("health", 0),
            "food": inv.get("food", 0),
            "drink": inv.get("drink", 0),
            "energy": inv.get("energy", 0),
            "inventory": {k: v for k, v in inv.items() if k not in ("health", "food", "drink", "energy")},
            "world_pos": tuple(info.get("player_pos", (0, 0))),
        }
