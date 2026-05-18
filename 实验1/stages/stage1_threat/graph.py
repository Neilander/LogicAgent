"""节点图构建：food + threat 两个识别核。"""

import numpy as np

from .recognizers.food import recognize_food
from .recognizers.threat import recognize_threats
from .types import Graph, Node


_DIR_LABELS_CN = {
    "N": "北", "NE": "东北", "E": "东", "SE": "东南",
    "S": "南", "SW": "西南", "W": "西", "NW": "西北",
}
_DIST_LABELS_CN = {"close": "近处", "mid": "中距", "far": "远处"}
_KIND_LABELS_CN = {"plant": "果实", "cow": "牛", "zombie": "丧尸", "skeleton": "骷髅", "arrow": "箭矢"}


def to_direction(dx: int, dy: int) -> str:
    if dx == 0 and dy == 0:
        return "self"
    import math
    ang = math.degrees(math.atan2(-dy, dx))
    ang = (ang + 360) % 360
    sectors = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
    return sectors[int((ang + 22.5) // 45) % 8]


def to_distance_band(dx: int, dy: int) -> str:
    cheb = max(abs(dx), abs(dy))
    if cheb <= 2:
        return "close"
    if cheb <= 4:
        return "mid"
    return "far"


def build_graph(semantic: np.ndarray, self_state: dict, view_radius: int = 4) -> Graph:
    food_hits = recognize_food(semantic, self_state["world_pos"], view_radius=view_radius)
    threat_hits = recognize_threats(semantic, self_state["world_pos"], view_radius=view_radius)

    items: list[tuple[int, int, str, str]] = []
    for dx, dy, raw in food_hits:
        items.append((dx, dy, raw, "food"))
    for dx, dy, raw in threat_hits:
        items.append((dx, dy, raw, "threat"))

    buckets: dict[tuple[str, str, str, str], list[tuple[int, int]]] = {}
    for dx, dy, raw, abstract in items:
        key = (to_direction(dx, dy), to_distance_band(dx, dy), raw, abstract)
        buckets.setdefault(key, []).append((dx, dy))

    nodes: list[Node] = []
    for (direction, dist, raw, abstract), positions in sorted(buckets.items()):
        positions.sort(key=lambda p: max(abs(p[0]), abs(p[1])))
        anchor = positions[0]
        count = len(positions)
        desc_kind = _KIND_LABELS_CN.get(raw, raw)
        desc_dir = _DIR_LABELS_CN.get(direction, direction)
        desc_dist = _DIST_LABELS_CN.get(dist, dist)
        if count == 1:
            desc = f"{desc_dist}{desc_dir}方的{desc_kind}"
        else:
            desc = f"{desc_dist}{desc_dir}方的{desc_kind}（共 {count} 处）"
        nodes.append(Node(
            id=f"{raw}_{direction}_{dist}",
            description=desc,
            kind=abstract,
            direction=direction,
            distance=dist,
            _grid_pos=anchor,
            extra={"raw_kind": raw, "cluster_size": count},
        ))

    return Graph(nodes=nodes, self_state=self_state)


def graph_to_text(graph: Graph) -> str:
    s = graph.self_state
    lines = [
        f"当前状态：HP={s['hp']}, food={s['food']}, drink={s['drink']}, energy={s['energy']}",
        f"视野内节点（共 {len(graph.nodes)} 个）：",
    ]
    if not graph.nodes:
        lines.append("  （空——视野内未发现 food/threat）")
    for n in graph.nodes:
        lines.append(f"  - {n.id} [{n.kind}]: {n.description}")
    return "\n".join(lines)
