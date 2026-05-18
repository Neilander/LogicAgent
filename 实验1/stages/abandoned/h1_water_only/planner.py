"""规划核：need_based_nearest。

策略：
  1. 视为"已饱足"的阈值：stat ≥ 7 就不主动追这类资源（避免站着 drink 浪费时间）
  2. 在 NEEDS 集合里挑更缺的那一类
  3. NEEDS 类目没节点 → 退到另一类（只有它也 needed 时）
  4. 都不需要 / 都没节点 → explore（找新视野 / 新机会）
"""

from .types import Graph

FULL = 9
SATIATED = 7   # ≥ 这个值不主动追


def need_based_nearest(graph: Graph) -> dict:
    s = graph.self_state
    food, drink = s.get("food", FULL), s.get("drink", FULL)
    needs_food = food < SATIATED
    needs_drink = drink < SATIATED
    food_lack, drink_lack = FULL - food, FULL - drink

    food_nodes = [n for n in graph.nodes if n.kind == "food"]
    water_nodes = [n for n in graph.nodes if n.kind == "water"]

    # 都饱了 → 探索（找下一片资源 / 探明威胁未来要躲）
    if not needs_food and not needs_drink:
        return {"action": "explore", "reason": f"food={food}, drink={drink} 都饱足，探索"}

    # 决定 primary kind：只在 needed 之间挑
    if needs_drink and (not needs_food or drink_lack > food_lack):
        primary, primary_kind = water_nodes, "water"
        fallback, fallback_kind = food_nodes, "food"
        fallback_needed = needs_food
        reason_main = f"drink={drink} 比 food={food} 更缺"
    else:
        primary, primary_kind = food_nodes, "food"
        fallback, fallback_kind = water_nodes, "water"
        fallback_needed = needs_drink
        reason_main = f"food={food} 是主要缺口"

    def priority(n):
        dx, dy = n._grid_pos
        cheb = max(abs(dx), abs(dy))
        kind_pref = 0 if n.extra.get("raw_kind") == "plant" else 1
        return (cheb, kind_pref)

    if primary:
        target = min(primary, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"{reason_main} → 去最近的 {primary_kind}：{target.description}",
        }
    if fallback and fallback_needed:
        target = min(fallback, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"视野无 {primary_kind}，退而求 {fallback_kind}：{target.description}",
        }
    return {"action": "explore", "reason": f"视野内无所需资源（needs food={needs_food}, drink={needs_drink}），探索"}


greedy_nearest = need_based_nearest
