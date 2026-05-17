"""规划核：greedy_nearest。

策略：
  - 如果视野有食物 → 选切比雪夫距离最近的（同距优先 plant 而非 cow，避免战斗）
  - 如果视野没食物 → 输出 explore（让 Executor 自己往一个方向走探索新视野）
"""

from .types import Graph


def greedy_nearest(graph: Graph) -> dict:
    food_nodes = [n for n in graph.nodes if n.kind == "food"]
    if not food_nodes:
        return {"action": "explore", "reason": "视野内无食物，往未知方向移动"}

    def priority(n):
        dx, dy = n._grid_pos
        cheb = max(abs(dx), abs(dy))
        # plant 优先（cow 需要战斗）
        kind_pref = 0 if n.extra.get("raw_kind") == "plant" else 1
        return (cheb, kind_pref)

    target = min(food_nodes, key=priority)
    return {
        "action": "goto",
        "target": target.id,
        "reason": f"最近的食物：{target.description}",
    }
