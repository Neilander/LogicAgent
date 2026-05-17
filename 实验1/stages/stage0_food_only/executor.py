"""Executor：把宏观动作（goto/explore）翻译成 Crafter 原子动作。

设计上 Stage 0 给 LLM 看的是节点的 LLM-facing 字段（id + description），
但 Executor 内部会查目标节点的 _grid_pos 来选移动方向。

LLM 调用：让 Claude 看当前节点图 + 选中的目标节点描述 + Crafter 可用动作列表，
输出未来 N 步的原子动作序列（带短理由）。
"""

from typing import Any

from llm.claude_cli import claude_prompt
from .types import Graph

# Crafter 原子动作 ID（依 crafter.Env.action_names 的顺序）
CRAFTER_ACTIONS = [
    "noop", "move_left", "move_right", "move_up", "move_down",
    "do", "sleep", "place_stone", "place_table", "place_furnace",
    "place_plant", "make_wood_pickaxe", "make_stone_pickaxe",
    "make_wood_sword", "make_stone_sword",
]


def execute(plan: dict, graph: Graph, raw_obs: Any, max_atomic: int = 5) -> list[str]:
    """把 plan（来自规划核）转成最多 max_atomic 个原子动作名。

    Args:
        plan: {"action": "goto", "target": node_id, ...}
        graph: 当前节点图（含隐藏的 _grid_pos）
        raw_obs: 当前 raw observation（给 LLM 更完整上下文）
        max_atomic: 一次最多输出几个原子动作

    Returns:
        list of atomic action names from CRAFTER_ACTIONS
    """
    raise NotImplementedError


def _build_prompt(plan: dict, graph: Graph, raw_obs: Any) -> str:
    """构造给 Claude 的 prompt。要求输出 JSON。"""
    raise NotImplementedError
