"""规划核：safe_need_path —— safe_path + need_based 的组合。

优先级：
  1. 视野内有 close 威胁 → flee_from
  2. 都饱足（food, drink ≥ SATIATED=7）→ explore
  3. 选 most-lacking 类目（food/water），目标节点用 threat-aware priority
  4. primary 没节点 → fallback（如果 fallback 也需要）
  5. 都没节点 → explore
"""

from .types import Graph

FULL = 9
SATIATED = 7


def safe_need_path(graph: Graph) -> dict:
    s = graph.self_state
    food, drink = s.get("food", FULL), s.get("drink", FULL)
    food_lack, drink_lack = FULL - food, FULL - drink
    needs_food = food < SATIATED
    needs_drink = drink < SATIATED

    food_nodes = [n for n in graph.nodes if n.kind == "food"]
    water_nodes = [n for n in graph.nodes if n.kind == "water"]
    threat_nodes = [n for n in graph.nodes if n.kind == "threat"]
    close_threats = [t for t in threat_nodes if t.distance == "close"]

    if close_threats:
        nearest = min(close_threats, key=lambda t: max(abs(t._grid_pos[0]), abs(t._grid_pos[1])))
        return {
            "action": "flee_from",
            "threat": nearest.id,
            "reason": f"近距威胁 {nearest.description}，撤退",
        }

    if not needs_food and not needs_drink:
        return {"action": "explore", "reason": f"food={food}, drink={drink} 都饱足，探索"}

    if needs_drink and (not needs_food or drink_lack > food_lack):
        primary_nodes, primary_kind = water_nodes, "water"
        fallback_nodes, fallback_kind = food_nodes, "food"
        fallback_needed = needs_food
        reason_main = f"drink={drink} 更缺"
    else:
        primary_nodes, primary_kind = food_nodes, "food"
        fallback_nodes, fallback_kind = water_nodes, "water"
        fallback_needed = needs_drink
        reason_main = f"food={food} 是主要缺口"

    def priority(n):
        dx, dy = n._grid_pos
        cheb = max(abs(dx), abs(dy))
        threat_penalty = 0
        for t in threat_nodes:
            tdx, tdy = t._grid_pos
            if dx * tdx + dy * tdy > 0:
                tcheb = max(abs(tdx), abs(tdy))
                if tcheb <= cheb:
                    threat_penalty += 3
        kind_pref = 0 if n.extra.get("raw_kind") == "plant" else 1
        return (cheb + threat_penalty, kind_pref)

    if primary_nodes:
        target = min(primary_nodes, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"{reason_main} → {primary_kind}：{target.description}",
        }
    if fallback_nodes and fallback_needed:
        target = min(fallback_nodes, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"无 {primary_kind}，退而求 {fallback_kind}：{target.description}",
        }
    return {"action": "explore", "reason": "视野内无所需资源，探索"}


greedy_nearest = safe_need_path
