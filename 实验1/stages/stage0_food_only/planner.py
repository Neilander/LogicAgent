"""规划核：在节点图上选下一步宏观行动。

Stage 0 只实现 greedy_nearest：在所有 food 节点里挑最近的，输出 goto。
如果视野里没有食物 → 输出 explore（让 Executor 自由走动找新视野）。
"""

from .types import Graph


def greedy_nearest(graph: Graph) -> dict:
    """挑最近的食物节点。

    Returns:
        {"action": "goto", "target": node_id, "reason": "最近的食物"} 或
        {"action": "explore", "reason": "视野内无食物"}
    """
    raise NotImplementedError
