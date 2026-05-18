"""规划核：committed_safe_need_path —— H3 + 目标 commit 机制。

H3 失败的根因：每帧重新选 primary kind，agent 在 food/water 间震荡。
H4 引入：选定 kind 后承诺 COMMIT_STEPS 步不再换（除非威胁打断或饱足）。

模块级状态：reset() 在 episode 开头调用。
"""

from .types import Graph

FULL = 9
SATIATED = 7
COMMIT_STEPS = 12

_state = {"committed_kind": None, "steps_left": 0}


def reset():
    _state["committed_kind"] = None
    _state["steps_left"] = 0


def committed_safe_need_path(graph: Graph) -> dict:
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
        _state["committed_kind"] = None
        _state["steps_left"] = 0
        nearest = min(close_threats, key=lambda t: max(abs(t._grid_pos[0]), abs(t._grid_pos[1])))
        return {
            "action": "flee_from",
            "threat": nearest.id,
            "reason": f"close 威胁 {nearest.description}，break commitment 撤退",
        }

    if not needs_food and not needs_drink:
        _state["committed_kind"] = None
        _state["steps_left"] = 0
        return {"action": "explore", "reason": f"food={food}, drink={drink} 饱足，探索"}

    # 决定/沿用 committed kind
    if _state["committed_kind"] is None or _state["steps_left"] <= 0 or \
       (_state["committed_kind"] == "food" and not needs_food) or \
       (_state["committed_kind"] == "water" and not needs_drink):
        if needs_drink and (not needs_food or drink_lack > food_lack):
            _state["committed_kind"] = "water"
        else:
            _state["committed_kind"] = "food"
        _state["steps_left"] = COMMIT_STEPS

    primary_kind = _state["committed_kind"]
    primary_nodes = water_nodes if primary_kind == "water" else food_nodes
    fallback_kind = "food" if primary_kind == "water" else "water"
    fallback_nodes = food_nodes if primary_kind == "water" else water_nodes
    fallback_needed = needs_food if primary_kind == "water" else needs_drink

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

    _state["steps_left"] -= 1

    if primary_nodes:
        target = min(primary_nodes, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"committed to {primary_kind}（剩 {_state['steps_left']} 步）：{target.description}",
        }
    if fallback_nodes and fallback_needed:
        target = min(fallback_nodes, key=priority)
        return {
            "action": "goto",
            "target": target.id,
            "reason": f"committed {primary_kind} 但视野没有，退而求 {fallback_kind}：{target.description}",
        }
    return {"action": "explore", "reason": f"committed {primary_kind} 但找不到，探索"}


greedy_nearest = committed_safe_need_path
