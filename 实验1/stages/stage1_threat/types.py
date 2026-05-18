"""Stage 0 数据结构：Node 和 Graph。

设计要点：节点的 LLM-facing 字段（id, description, kind, direction, distance）
是抽象自然语言，决策时只看这些；_grid_pos 是隐藏字段，只在 Executor 把宏观
动作翻译成原子动作时用。
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

Direction = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW", "self"]
DistanceBand = Literal["close", "mid", "far", "self"]
NodeKind = Literal["self", "food", "water", "threat", "obstacle", "resource"]


@dataclass
class Node:
    id: str                              # "food_NW_close" — 稳定 token，给 LLM 看
    description: str                     # "近处西北方的果树"
    kind: NodeKind
    direction: Direction
    distance: DistanceBand
    _grid_pos: tuple[int, int]           # 隐藏字段：视野内的相对坐标 (dx, dy)
    extra: dict = field(default_factory=dict)   # 扩展属性（HP/food/品类细节等）


@dataclass
class Graph:
    nodes: list[Node]
    self_state: dict                     # {hp, food, drink, energy, facing, ...}

    def by_id(self, node_id: str) -> Optional[Node]:
        return next((n for n in self.nodes if n.id == node_id), None)

    def by_kind(self, kind: NodeKind) -> list[Node]:
        return [n for n in self.nodes if n.kind == kind]

    def to_llm_view(self) -> str:
        """序列化成给 LLM 看的文本表示。不暴露 _grid_pos。"""
        raise NotImplementedError
