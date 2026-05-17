"""节点图构建：把识别核的输出（相对坐标 + kind）变成抽象节点图。

每个节点带：
  - id (稳定 token)
  - description (自然语言)
  - kind, direction, distance
  - 隐藏字段 _grid_pos（相对玩家的 dx, dy，给 Executor 用）

节点 id 的稳定性：同方向同距离的同类节点共享一个 id 后缀，必要时加 #序号。
"""

import numpy as np

from .recognizers.food import recognize_food
from .types import Graph, Node


_DIR_LABELS_CN = {
    "N": "北", "NE": "东北", "E": "东", "SE": "东南",
    "S": "南", "SW": "西南", "W": "西", "NW": "西北",
}
_DIST_LABELS_CN = {"close": "近处", "mid": "中距", "far": "远处"}
_KIND_LABELS_CN = {"plant": "果实", "cow": "牛"}


def to_direction(dx: int, dy: int) -> str:
    """(dx, dy) → 8 方位。+x=E, +y=S。"""
    if dx == 0 and dy == 0:
        return "self"
    import math
    # 屏幕坐标 +y 向下 = 南。换算到极角时把 y 翻一下做"+y 向上"。
    ang = math.degrees(math.atan2(-dy, dx))  # -180..180, 0=E, 90=N
    # 转成 0..360
    ang = (ang + 360) % 360
    sectors = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
    idx = int((ang + 22.5) // 45) % 8
    return sectors[idx]


def to_distance_band(dx: int, dy: int) -> str:
    cheb = max(abs(dx), abs(dy))
    if cheb <= 2:
        return "close"
    if cheb <= 4:
        return "mid"
    return "far"


def build_graph(semantic: np.ndarray, self_state: dict) -> Graph:
    """主入口：识别核 → 节点列表 → Graph。"""
    food_hits = recognize_food(semantic, self_state["world_pos"], view_radius=4)

    # 按 (direction, distance, kind) 桶分组，让节点 id 稳定 + 减少重复
    buckets: dict[tuple[str, str, str], list[tuple[int, int]]] = {}
    for dx, dy, kind in food_hits:
        key = (to_direction(dx, dy), to_distance_band(dx, dy), kind)
        buckets.setdefault(key, []).append((dx, dy))

    nodes: list[Node] = []
    for (direction, dist, kind), positions in sorted(buckets.items()):
        # 一个桶里多个 tile → 选最近的当 anchor，描述里说"那一片"
        positions.sort(key=lambda p: max(abs(p[0]), abs(p[1])))
        anchor = positions[0]
        count = len(positions)
        desc_kind = _KIND_LABELS_CN.get(kind, kind)
        desc_dir = _DIR_LABELS_CN.get(direction, direction)
        desc_dist = _DIST_LABELS_CN.get(dist, dist)
        if count == 1:
            desc = f"{desc_dist}{desc_dir}方的{desc_kind}"
        else:
            desc = f"{desc_dist}{desc_dir}方的{desc_kind}（共 {count} 处）"
        nodes.append(Node(
            id=f"{kind}_{direction}_{dist}",
            description=desc,
            kind="food",
            direction=direction,
            distance=dist,
            _grid_pos=anchor,
            extra={"raw_kind": kind, "cluster_size": count},
        ))

    return Graph(nodes=nodes, self_state=self_state)


def graph_to_text(graph: Graph) -> str:
    """给 LLM / 人看的序列化（不暴露 _grid_pos）。"""
    s = graph.self_state
    lines = [
        f"当前状态：HP={s['hp']}, food={s['food']}, drink={s['drink']}, energy={s['energy']}",
        f"视野内节点（共 {len(graph.nodes)} 个）：",
    ]
    if not graph.nodes:
        lines.append("  （空——视野内未发现食物）")
    for n in graph.nodes:
        lines.append(f"  - {n.id}: {n.description}")
    return "\n".join(lines)
