"""Topology builder: turn a tile grid (with obstacles + POIs) into a node graph.

Inputs
------
- grid: 2D numpy array of tile IDs (任意大小，典型是 7×7)
- walkable_ids: set of tile IDs the agent can stand on
- poi_specs: dict {tile_id: label}, e.g. {18: "plant", 14: "cow", 1: "water"}
- agent_pos (optional): (x, y) tuple; if given, agent is added as a "self" node

Output
------
- Topology with:
    nodes: list of {id, label, pos}
    edges: list of {src, dst, distance}  — undirected, only reachable pairs
    grid_shape: tuple

Algorithm
---------
1. Find all POI cells (and optionally agent's cell) → these become nodes.
2. For each node, BFS through cells that are walkable OR POI (POIs are treated
   as traversable for distance computation — i.e. you can "pass through" a POI
   on your way somewhere else, even though in reality you'd interact with it).
3. Distance between two nodes = shortest BFS path length (number of moves,
   4-connected by default).
4. Unreachable pairs are NOT in the edges list — that's the signal of an
   obstacle wall separating them.

This is the algorithmic core of "Layer 2: cognitive map" in the 4-layer agent
architecture, but kept standalone and testable.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class TopologyNode:
    id: str                    # stable token, e.g. "plant_1", "cow_2", "self"
    label: str                 # human-readable kind, e.g. "plant", "cow", "self"
    pos: tuple[int, int]       # (x, y) in grid coords


@dataclass
class TopologyEdge:
    src: str
    dst: str
    distance: int


@dataclass
class Topology:
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    grid_shape: tuple[int, int]

    def by_id(self, node_id: str) -> Optional[TopologyNode]:
        return next((n for n in self.nodes if n.id == node_id), None)

    def neighbors(self, node_id: str) -> list[tuple[str, int]]:
        """Return [(other_id, distance), ...] for the given node, sorted by distance."""
        out = []
        for e in self.edges:
            if e.src == node_id:
                out.append((e.dst, e.distance))
            elif e.dst == node_id:
                out.append((e.src, e.distance))
        return sorted(out, key=lambda x: x[1])


def build_topology(
    grid: np.ndarray,
    walkable_ids: set[int],
    poi_specs: dict[int, str],
    agent_pos: Optional[tuple[int, int]] = None,
    connectivity: int = 4,
) -> Topology:
    H, W = grid.shape

    # 1. find all POI positions → make nodes
    nodes: list[TopologyNode] = []
    poi_positions: set[tuple[int, int]] = set()
    counter: dict[str, int] = {}

    for x in range(H):
        for y in range(W):
            tile_id = int(grid[x, y])
            if tile_id in poi_specs:
                label = poi_specs[tile_id]
                counter[label] = counter.get(label, 0) + 1
                nodes.append(TopologyNode(
                    id=f"{label}_{counter[label]}",
                    label=label,
                    pos=(x, y),
                ))
                poi_positions.add((x, y))

    if agent_pos is not None:
        nodes.append(TopologyNode(id="self", label="self", pos=tuple(agent_pos)))

    # 2. movement deltas
    if connectivity == 8:
        deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # 3. helper: is a cell traversable?
    def passable(pos: tuple[int, int]) -> bool:
        x, y = pos
        if not (0 <= x < H and 0 <= y < W):
            return False
        if pos == agent_pos:
            return True   # agent can occupy its own cell
        if pos in poi_positions:
            return True   # treat POIs as passable for distance computation
        return int(grid[x, y]) in walkable_ids

    # 4. BFS distances from every node, then derive edges
    def bfs(start: tuple[int, int]) -> dict[tuple[int, int], int]:
        dist = {start: 0}
        q = deque([start])
        while q:
            cur = q.popleft()
            for dx, dy in deltas:
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in dist:
                    continue
                if not passable(nxt):
                    continue
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
        return dist

    edges: list[TopologyEdge] = []
    seen_pairs: set[tuple[str, str]] = set()
    pos_to_node = {n.pos: n.id for n in nodes}

    for src_node in nodes:
        dists = bfs(src_node.pos)
        for pos, d in dists.items():
            if pos == src_node.pos:
                continue
            if pos not in pos_to_node:
                continue
            other_id = pos_to_node[pos]
            pair = tuple(sorted([src_node.id, other_id]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            edges.append(TopologyEdge(src=src_node.id, dst=other_id, distance=d))

    return Topology(nodes=nodes, edges=edges, grid_shape=(H, W))


# ---------- Visualization helpers ----------

def grid_to_ascii(
    grid: np.ndarray,
    walkable_ids: set[int],
    poi_specs: dict[int, str],
    agent_pos: Optional[tuple[int, int]] = None,
) -> str:
    """Pretty-print the grid. Legend: @ = agent, # = obstacle, . = walkable, first letter (upper) = POI."""
    H, W = grid.shape
    lines = []
    for x in range(H):
        row = []
        for y in range(W):
            tile_id = int(grid[x, y])
            if agent_pos and (x, y) == tuple(agent_pos):
                row.append("@")
            elif tile_id in poi_specs:
                row.append(poi_specs[tile_id][0].upper())
            elif tile_id in walkable_ids:
                row.append(".")
            else:
                row.append("#")
        lines.append(" ".join(row))
    return "\n".join(lines)


def topology_to_text(topo: Topology) -> str:
    lines = ["nodes:"]
    for n in topo.nodes:
        lines.append(f"  - {n.id:<12s} [{n.label}] @ {n.pos}")
    if not topo.edges:
        lines.append("edges: (none — all nodes isolated)")
        return "\n".join(lines)
    lines.append(f"edges ({len(topo.edges)}):")
    for e in sorted(topo.edges, key=lambda x: (x.distance, x.src, x.dst)):
        lines.append(f"  {e.src:<12s} <--> {e.dst:<12s}  dist = {e.distance}")
    return "\n".join(lines)


def topology_to_dot(topo: Topology) -> str:
    """Graphviz DOT format. Pipe into `dot -Tpng > out.png` for visualization."""
    lines = ["graph topology {", "  layout=neato;", "  node [shape=circle, fontname=monospace];"]
    color = {"plant": "#6fcf97", "cow": "#f2c94c", "water": "#56ccf2",
             "zombie": "#eb5757", "skeleton": "#bb86fc", "self": "#ffffff"}
    for n in topo.nodes:
        c = color.get(n.label, "#cccccc")
        lines.append(f'  "{n.id}" [label="{n.id}", style=filled, fillcolor="{c}"];')
    for e in topo.edges:
        lines.append(f'  "{e.src}" -- "{e.dst}" [label="{e.distance}"];')
    lines.append("}")
    return "\n".join(lines)


_COLOR = {
    "plant": "#6fcf97", "cow": "#f2c94c", "water": "#56ccf2",
    "zombie": "#eb5757", "skeleton": "#bb86fc", "self": "#ffffff",
    "obstacle": "#444", "walkable": "#1a1d24",
}


def map_to_svg(
    grid: np.ndarray,
    walkable_ids: set[int],
    poi_specs: dict[int, str],
    agent_pos: Optional[tuple[int, int]] = None,
    cell: int = 44,
) -> str:
    """Render JUST the grid map: obstacles, walkable, POIs as labeled cells, agent marker."""
    H, W = grid.shape
    pad = 12
    width = W * cell + pad * 2
    height = H * cell + pad * 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'style="background:#0f1115;font-family:-apple-system,sans-serif">']
    for x in range(H):
        for y in range(W):
            tid = int(grid[x, y])
            cx = pad + y * cell
            cy = pad + x * cell
            is_agent = agent_pos is not None and (x, y) == tuple(agent_pos)
            if tid in poi_specs:
                label = poi_specs[tid]
                fill = _COLOR.get(label, "#ccc")
                out.append(f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" '
                           f'fill="{fill}" stroke="#2a2f3a" opacity="0.85"/>')
                out.append(f'<text x="{cx + cell/2}" y="{cy + cell/2 + 4}" '
                           f'text-anchor="middle" font-size="14" fill="#0f1115" '
                           f'font-weight="bold">{label[0].upper()}</text>')
            elif tid in walkable_ids:
                out.append(f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" '
                           f'fill="#1a1d24" stroke="#2a2f3a"/>')
            else:
                out.append(f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" '
                           f'fill="#3a3f4a" stroke="#2a2f3a"/>')
            if is_agent:
                out.append(f'<circle cx="{cx + cell/2}" cy="{cy + cell/2}" '
                           f'r="{cell*0.28}" fill="#ffffff" stroke="#f2c94c" stroke-width="3"/>')
                out.append(f'<text x="{cx + cell/2}" y="{cy + cell/2 + 4}" '
                           f'text-anchor="middle" font-size="13" fill="#0f1115" '
                           f'font-weight="bold">ME</text>')
    out.append('</svg>')
    return "\n".join(out)


def radial_to_svg(
    topo: Topology,
    size: int = 420,
) -> str:
    """Spider/radial diagram: self in center, POIs placed at (bearing, distance) from self.

    Bearings computed from grid (x, y) deltas. Radius = scaled distance.
    Only self↔POI edges drawn (radial spokes), so no crisscrossing.
    """
    import math
    self_node = next((n for n in topo.nodes if n.id == "self"), None)
    if self_node is None:
        return f'<svg viewBox="0 0 {size} {size}"><text x="10" y="20" fill="#fff">no self node</text></svg>'

    sx, sy = self_node.pos
    cx, cy = size / 2, size / 2

    # Compute polar positions for each non-self node
    others = [n for n in topo.nodes if n.id != "self"]
    self_edges = {nid: d for nid, d in topo.neighbors("self")}
    max_dist = max(self_edges.values(), default=1)
    reachable = [n for n in others if n.id in self_edges]
    unreachable = [n for n in others if n.id not in self_edges]

    # Radius scaling: closest POI at 60px, furthest at size/2 - 30
    r_min, r_max = 55, size / 2 - 35
    pos = {"self": (cx, cy)}
    for n in reachable:
        d = self_edges[n.id]
        if max_dist > 0:
            r = r_min + (r_max - r_min) * (d / max(max_dist, 1))
        else:
            r = r_min
        # Bearing in grid: dx = y - sy (col delta = east), dy = -(x - sx) (negative because +x is south, but we want screen y up = north)
        dy_grid = n.pos[0] - sx   # +x in grid = south (screen down = positive y)
        dx_grid = n.pos[1] - sy   # +y in grid = east
        # Angle in screen coords: 0 = east, increases clockwise (screen)
        if dx_grid == 0 and dy_grid == 0:
            angle = 0
        else:
            angle = math.atan2(dy_grid, dx_grid)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        pos[n.id] = (px, py)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
           f'style="background:#0f1115;font-family:-apple-system,sans-serif">']

    # distance rings (visual guide)
    for ratio, label_dist in [(0.25, "近"), (0.55, "中"), (0.95, "远")]:
        rr = r_min + (r_max - r_min) * (ratio - 0.05)
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" '
                   f'stroke="#2a2f3a" stroke-dasharray="3,4"/>')
        out.append(f'<text x="{cx}" y="{cy - rr - 4}" text-anchor="middle" '
                   f'fill="#5a6070" font-size="10">{label_dist}</text>')

    # spokes (self → reachable POI)
    for n in reachable:
        px, py = pos[n.id]
        d = self_edges[n.id]
        opacity = max(0.4, 1.0 - d / (max_dist * 1.5))
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" '
                   f'stroke="#5ee0a1" stroke-width="2" opacity="{opacity:.2f}"/>')
        # distance label, offset toward POI
        lx = cx + (px - cx) * 0.55
        ly = cy + (py - cy) * 0.55
        out.append(f'<rect x="{lx - 14}" y="{ly - 10}" width="28" height="16" rx="3" '
                   f'fill="#0f1115" stroke="#5ee0a1" opacity="0.9"/>')
        out.append(f'<text x="{lx}" y="{ly + 4}" text-anchor="middle" '
                   f'fill="#5ee0a1" font-size="11" font-weight="bold">{d}</text>')

    # nodes
    node_r = 26
    for n in reachable:
        px, py = pos[n.id]
        fill = _COLOR.get(n.label, "#ccc")
        out.append(f'<circle cx="{px}" cy="{py}" r="{node_r}" fill="{fill}" '
                   f'stroke="#fff" stroke-width="2"/>')
        out.append(f'<text x="{px}" y="{py - 1}" text-anchor="middle" '
                   f'fill="#0f1115" font-size="11" font-weight="bold">{n.label}</text>')
        suffix = n.id.rsplit("_", 1)[-1]
        out.append(f'<text x="{px}" y="{py + 13}" text-anchor="middle" '
                   f'fill="#0f1115" font-size="10">#{suffix}</text>')

    # self in center
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{node_r + 2}" fill="#ffffff" '
               f'stroke="#f2c94c" stroke-width="3"/>')
    out.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" '
               f'fill="#0f1115" font-size="13" font-weight="bold">ME</text>')

    # unreachable list (top-left corner)
    if unreachable:
        out.append(f'<text x="14" y="20" fill="#eb5757" font-size="12" font-weight="bold">'
                   f'unreachable ({len(unreachable)}):</text>')
        for i, n in enumerate(unreachable):
            out.append(f'<text x="14" y="{38 + i*16}" fill="#eb5757" font-size="11">'
                       f'• {n.id}</text>')

    out.append('</svg>')
    return "\n".join(out)


# Legacy: combined viz, kept for backward compat
def topology_to_svg(
    topo: Topology,
    grid: np.ndarray,
    walkable_ids: set[int],
    poi_specs: dict[int, str],
    agent_pos: Optional[tuple[int, int]] = None,
    cell: int = 50,
) -> str:
    """Combined grid + edges viz. Kept for backward-compat — prefer map_to_svg + radial_to_svg."""
    return map_to_svg(grid, walkable_ids, poi_specs, agent_pos, cell)


def topology_to_html(
    topo: Topology,
    grid: np.ndarray,
    walkable_ids: set[int],
    poi_specs: dict[int, str],
    agent_pos: Optional[tuple[int, int]] = None,
    title: str = "Topology",
) -> str:
    """Self-contained HTML page: SVG on left, edge list on right."""
    svg = topology_to_svg(topo, grid, walkable_ids, poi_specs, agent_pos)
    edge_rows = "".join(
        f"<tr><td>{e.src}</td><td>↔</td><td>{e.dst}</td><td style='text-align:right'>{e.distance}</td></tr>"
        for e in sorted(topo.edges, key=lambda x: x.distance)
    )
    node_rows = ""
    for n in topo.nodes:
        c = _COLOR.get(n.label, "#ccc")
        node_rows += (f"<tr><td><span class='dot' style='background:{c}'></span>{n.id}</td>"
                      f"<td>{n.label}</td><td>{n.pos}</td></tr>")
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>
body {{ background:#0f1115; color:#e6e6e6; font-family:-apple-system,monospace; margin:0; padding:20px; }}
h1 {{ font-size:18px; margin:0 0 16px 0; }}
.container {{ display:grid; grid-template-columns:auto 1fr; gap:24px; }}
table {{ border-collapse:collapse; width:100%; font-family:ui-monospace,monospace; font-size:12px; }}
th, td {{ padding:4px 10px; text-align:left; border-bottom:1px solid #2a2f3a; }}
th {{ color:#8b95a7; font-weight:500; text-transform:uppercase; font-size:10px; }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:8px; vertical-align:middle; }}
.section {{ margin-bottom:24px; }}
.section h2 {{ font-size:12px; color:#8b95a7; text-transform:uppercase; margin:0 0 8px 0; font-weight:500; letter-spacing:0.5px; }}
</style></head><body>
<h1>{title}</h1>
<div class="container">
  <div>{svg}</div>
  <div>
    <div class="section">
      <h2>Nodes ({len(topo.nodes)})</h2>
      <table><tr><th>ID</th><th>Label</th><th>Pos</th></tr>{node_rows}</table>
    </div>
    <div class="section">
      <h2>Edges ({len(topo.edges)})</h2>
      <table><tr><th>Source</th><th></th><th>Target</th><th style='text-align:right'>Dist</th></tr>{edge_rows}</table>
    </div>
  </div>
</div>
</body></html>"""


# ---------- Demo ----------

if __name__ == "__main__":
    # A 7×7 sample world
    #   0 = walkable, 1 = obstacle
    #   2 = plant (POI), 3 = cow (POI), 4 = water (POI)
    grid = np.array([
        [0, 0, 0, 1, 1, 0, 2],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 1, 1, 0],
        [3, 0, 0, 0, 0, 1, 0],
        [0, 0, 1, 1, 0, 1, 0],
        [4, 4, 1, 0, 0, 0, 0],
        [4, 4, 0, 0, 1, 0, 2],
    ])
    walkable = {0}
    pois = {2: "plant", 3: "cow", 4: "water"}
    agent_pos = (1, 2)   # agent stands here

    print("=== Grid (7×7) ===")
    print("Legend: @ agent  # obstacle  . walkable  P plant  C cow  W water")
    print(grid_to_ascii(grid, walkable, pois, agent_pos))
    print()

    topo = build_topology(grid, walkable, pois, agent_pos)
    print("=== Topology ===")
    print(topology_to_text(topo))

    print()
    print("=== Neighbors of 'self' (sorted by distance) ===")
    for nid, d in topo.neighbors("self"):
        print(f"  → {nid} (dist {d})")

    print()
    print("=== Same, but with an obstacle wall splitting the map ===")
    grid2 = grid.copy()
    grid2[:, 3] = 1   # build a vertical wall down column 3
    # need a gap so agent (col 2) can't reach east half
    grid2[3, 3] = 1   # ensure wall is solid
    print(grid_to_ascii(grid2, walkable, pois, agent_pos))
    topo2 = build_topology(grid2, walkable, pois, agent_pos)
    print()
    print(topology_to_text(topo2))
    print()
    print("=== Reachable from 'self' ===")
    for nid, d in topo2.neighbors("self"):
        print(f"  → {nid} (dist {d})")
    unreachable = set(n.id for n in topo2.nodes if n.id != "self") - set(nid for nid, _ in topo2.neighbors("self"))
    if unreachable:
        print(f"  unreachable from self: {sorted(unreachable)}")

    # Write a side-by-side HTML for visual preview
    from pathlib import Path

    def panel(title, grid_, topo_):
        m = map_to_svg(grid_, walkable, pois, agent_pos)
        r = radial_to_svg(topo_)
        nbrs = topo_.neighbors("self")
        unreach = sorted(set(n.id for n in topo_.nodes if n.id != "self")
                         - set(nid for nid, _ in nbrs))
        rows = "".join(
            f'<tr><td style="color:{_COLOR.get(topo_.by_id(nid).label,"#ccc")}">●</td>'
            f'<td>{nid}</td><td style="text-align:right;color:#5ee0a1;font-weight:bold">{d} 步</td></tr>'
            for nid, d in nbrs
        )
        for nid in unreach:
            rows += (f'<tr><td style="color:#eb5757">✗</td>'
                     f'<td style="color:#eb5757">{nid}</td>'
                     f'<td style="text-align:right;color:#eb5757">不可达</td></tr>')
        return f"""<div class="panel">
  <h2>{title}</h2>
  <div class="cols">
    <div>
      <div class="cap">世界地图</div>
      {m}
    </div>
    <div>
      <div class="cap">从 ME 出发的拓扑（自己在中心，距离=半径）</div>
      {r}
    </div>
    <div>
      <div class="cap">距离表</div>
      <table>{rows}</table>
    </div>
  </div>
</div>"""

    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset='UTF-8'><title>Topology Demo</title>
<style>
body {{ background:#0f1115; color:#e6e6e6; font-family:-apple-system,sans-serif; padding:24px; margin:0; }}
h1 {{ font-size:20px; margin:0 0 8px 0; }}
p.subtitle {{ color:#8b95a7; font-size:13px; margin:0 0 20px 0; }}
.legend {{ display:flex; gap:18px; font-size:12px; color:#8b95a7; margin-bottom:24px; align-items:center; }}
.legend span {{ display:inline-flex; align-items:center; gap:6px; }}
.legend .sw {{ width:14px; height:14px; display:inline-block; border-radius:50%; }}
.legend .swsq {{ width:14px; height:14px; display:inline-block; }}
.panel {{ background:#1a1d24; border:1px solid #2a2f3a; border-radius:8px; padding:20px; margin-bottom:24px; }}
.panel h2 {{ font-size:14px; margin:0 0 16px 0; color:#5ee0a1; font-weight:600; }}
.cols {{ display:grid; grid-template-columns:auto auto 1fr; gap:24px; align-items:start; }}
.cap {{ font-size:11px; color:#8b95a7; margin-bottom:8px; text-transform:uppercase; letter-spacing:0.5px; }}
table {{ border-collapse:collapse; font-family:ui-monospace,monospace; font-size:12px; width:100%; }}
td {{ padding:6px 10px; border-bottom:1px solid #2a2f3a; }}
</style></head><body>
<h1>topology builder — 把 grid 算成"我能去哪里"</h1>
<p class="subtitle">左边是世界，右边是从 ME（玩家）视角的拓扑图：自己在中心、其他点按"方向 + 距离"摆放，连线 = 最短走的步数。</p>
<div class="legend">
  <span><span class="sw" style="background:#f2c94c"></span>cow</span>
  <span><span class="sw" style="background:#6fcf97"></span>plant</span>
  <span><span class="sw" style="background:#56ccf2"></span>water</span>
  <span><span class="sw" style="background:#fff;border:2px solid #f2c94c"></span>ME (玩家)</span>
  <span><span class="swsq" style="background:#3a3f4a"></span>障碍</span>
  <span><span class="swsq" style="background:#1a1d24"></span>可走</span>
</div>
{panel("Demo 1 — 开放地图", grid, topo)}
{panel("Demo 2 — 列 3 被墙挡住", grid2, topo2)}
</body></html>"""
    out = Path(__file__).parent / "topology_demo.html"
    out.write_text(html)
    print(f"\nWrote visual demo → {out}")
