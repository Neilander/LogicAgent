"""节点图构建：把 raw view + 各识别核的输出，组装成抽象 Graph。

关键转换：
- 相对坐标 (dx, dy) → direction（8 方位）+ distance band（close/mid/far）
- 同类相邻 tile → 聚合成一个节点（"那一片果丛"，不是 5 个独立节点）
- 节点 id 用 "{kind}_{direction}_{distance}" 模板，跨 step 尽量保持稳定
"""

from typing import Any

from .types import Graph, Node


def to_direction(dx: int, dy: int) -> str:
    """(dx, dy) → 8 方位字符串。约定：+x=E, +y=S（与图像坐标一致）。"""
    raise NotImplementedError


def to_distance_band(dx: int, dy: int) -> str:
    """切比雪夫距离 → close/mid/far。"""
    raise NotImplementedError


def cluster_adjacent(positions: list[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    """同类 tile 聚合：相邻（含对角）的归一组。"""
    raise NotImplementedError


def build_graph(raw_obs: Any, self_state: dict) -> Graph:
    """主入口：raw view + agent state → Graph。

    Stage 0 只调用 food_recognizer。后续 stage 会在这里串更多识别核。
    """
    raise NotImplementedError
