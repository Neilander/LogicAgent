"""规划核：safe_path。

策略（优先级从高到低）：
  1. 视野内有 close 威胁（cheb ≤ 2）→ flee_from（远离最近威胁）
  2. 视野内有 food → goto 最近且**远离威胁方向**的 food
  3. 没有 food → explore
"""

from .types import Graph


def safe_path(graph: Graph) -> dict:
    food_nodes = [n for n in graph.nodes if n.kind == "food"]
    threat_nodes = [n for n in graph.nodes if n.kind == "threat"]
    close_threats = [t for t in threat_nodes if t.distance == "close"]

    if close_threats:
        nearest_threat = min(close_threats, key=lambda t: max(abs(t._grid_pos[0]), abs(t._grid_pos[1])))
        return {
            "action": "flee_from",
            "threat": nearest_threat.id,
            "reason": f"近距威胁 {nearest_threat.description}，先撤退",
        }

    if food_nodes:
        def priority(n):
            dx, dy = n._grid_pos
            cheb = max(abs(dx), abs(dy))
            # 威胁在该 food 方向上 → 加 penalty
            threat_penalty = 0
            for t in threat_nodes:
                tdx, tdy = t._grid_pos
                if dx * tdx + dy * tdy > 0:
                    tcheb = max(abs(tdx), abs(tdy))
                    if tcheb <= cheb:
                        threat_penalty += 3
            kind_pref = 0 if n.extra.get("raw_kind") == "plant" else 1
            return (cheb + threat_penalty, kind_pref)

        target = min(food_nodes, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"无近距威胁，去食物：{target.description}",
        }

    return {"action": "explore", "reason": "视野内无 food/threat，往未知方向移动"}


# 兼容 run.py 的旧名字
greedy_nearest = safe_path
