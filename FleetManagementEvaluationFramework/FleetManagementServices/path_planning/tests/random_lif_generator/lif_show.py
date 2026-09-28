import json, numpy
import networkx as nx
from typing import Dict, List, Tuple, Optional

import plotly.graph_objects as go

from data.models import Layout

PATH_COLORS = [
    "red", "blue", "green", "orange", "purple", "brown", "pink", "olive",
    "cyan", "magenta", "lime", "teal", "indigo", "gold", "coral", "darkblue",
    "darkgreen", "maroon", "navy", "chocolate", "darkviolet", "dodgerblue",
    "crimson", "sienna", "slateblue", "tomato", "mediumseagreen", "firebrick",
    "deepskyblue", "hotpink", "darkturquoise", "orangered"
]

NUM_STEPS = 150

def load_lif_file(filename: str) -> Dict:
    with open(filename, "r") as f:
        return json.load(f)


def build_graph(data: Dict) -> nx.Graph:
    G = nx.Graph()
    layout = data["layouts"][0]
    for node in layout["nodes"]:
        pos = node.get("nodePosition", {})
        G.add_node(node["nodeId"], pos=(float(pos.get("x", 0.0)), float(pos.get("y", 0.0))))
    for edge in layout["edges"]:
        G.add_edge(edge["startNodeId"], edge["endNodeId"], edgeId=edge["edgeId"])
    return G

def build_graph_lif_object(lif_object: Layout):
    G = nx.Graph()
    for node in lif_object.nodes:
        pos = node.nodePosition
        G.add_node(node.nodeId, pos=(pos.x, pos.y))
    for edge in lif_object.edges:
        G.add_edge(edge.startNodeId, edge.endNodeId, edgeId=edge.edgeId)
    return G


def create_edge_trace(G, pos):
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    return go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='gray'),
                      name='Edges', hoverinfo='none')


def create_node_trace(G, pos):
    node_x, node_y = [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    return go.Scatter(
        x=node_x, y=node_y, mode='markers',
        text=[str(n) for n in G.nodes()],
        marker=dict(color='lightgray', size=6, line=dict(width=0.5, color='black')),
        hoverinfo='text', name='Nodes'
    )


def extract_time_steps(paths):
    times = set()
    for path in paths:
        for node, (t0, t1) in path:
            times.add(round(t0, 4))
            if t1 != float('inf'):
                times.add(round(t1, 4))
    return sorted(times)


def interpolate_pos(pos, start_node, end_node, t0, t1, t):
    """linear interpolation between time points"""
    x0, y0 = pos[start_node]
    x1, y1 = pos[end_node]
    frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
    x = x0 + frac * (x1 - x0)
    y = y0 + frac * (y1 - y0)
    return x, y


def create_path_traces(paths: List[List[str]], pos: Dict, with_markers=True) -> List[go.Scatter]:
    traces = []
    for i, path in enumerate(paths):
        if not path:
            continue
        color = PATH_COLORS[i % len(PATH_COLORS)]
        x, y = [], []
        for j in range(len(path) - 1):
            if path[j] in pos and path[j + 1] in pos:
                x0, y0 = pos[path[j]]
                x1, y1 = pos[path[j + 1]]
                x += [x0, x1, None]
                y += [y0, y1, None]
        traces.append(go.Scatter(x=x, y=y, mode='lines', line=dict(width=4, color=color),
                                 name=f'Path AMR {i}', hoverinfo='none'))
        if with_markers:
            if path[0] in pos:
                x0, y0 = pos[path[0]]
                traces.append(go.Scatter(
                    x=[x0], y=[y0], mode='markers',
                    marker=dict(color=color, size=14, symbol='cross', line=dict(width=2, color='black')),
                    text=[f"Start AMR {i}: {path[0]}"], hoverinfo='text', name=f'Start AMR {i}'
                ))
            if path[-1] in pos:
                x1, y1 = pos[path[-1]]
                traces.append(go.Scatter(
                    x=[x1], y=[y1], mode='markers',
                    marker=dict(color=color, size=14, symbol='square', line=dict(width=2, color='black')),
                    text=[f"End AMR {i}: {path[-1]}"], hoverinfo='text', name=f'End AMR {i}'
                ))
    return traces


def draw_static_graph(G: nx.Graph, paths: List[List[str]]):
    pos = nx.get_node_attributes(G, "pos") or nx.spring_layout(G, seed=42)
    traces = [create_edge_trace(G, pos), create_node_trace(G, pos)] + create_path_traces(paths, pos)
    fig = go.Figure(data=traces, layout=go.Layout(
        title="LIF Layout Graph with AMR-Paths + start/endpositions",
        title_x=0.5, showlegend=True, hovermode='closest',
        margin=dict(t=40, b=20, l=20, r=20),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        width=1000, height=800
    ))
    fig.show()

def draw_animated_graph(G: nx.Graph, paths: list, raw_constraints, type: int):
    if type == 0:
        draw_animated_graph_type0(G, paths, raw_constraints)
    else:
        draw_animated_graph_type1(G, paths, raw_constraints)

def draw_animated_graph_type1(G: nx.Graph, paths: list, raw_constraints):
    pos = nx.get_node_attributes(G, "pos") or nx.spring_layout(G, seed=42)

    raw_times = extract_time_steps(paths)
    min_t, max_t = raw_times[0], raw_times[-1]
    duration = max_t - min_t
    NUM_STEPS = int(duration * 30)
    time_steps = numpy.linspace(min_t, max_t, NUM_STEPS)

    base_traces = [create_edge_trace(G, pos), create_node_trace(G, pos)]

    start_markers, end_markers = [], []
    for i, path in enumerate(paths):
        color = PATH_COLORS[i % len(PATH_COLORS)]
        if not path:
            continue

        start_id = path[0][0]
        end_id = path[-1][0]

        if start_id in pos:
            x, y = pos[start_id]
            start_markers.append(go.Scatter(
                x=[x], y=[y], mode='markers',
                marker=dict(color=color, size=14, symbol='cross', line=dict(width=2, color='black')),
                text=[f"Start AMR {i}: {start_id}"], hoverinfo='text', name=f'Start AMR {i}'
            ))

        if end_id in pos:
            x, y = pos[end_id]
            end_markers.append(go.Scatter(
                x=[x], y=[y], mode='markers',
                marker=dict(color=color, size=14, symbol='square', line=dict(width=2, color='black')),
                text=[f"End AMR {i}: {end_id}"], hoverinfo='text', name=f'End AMR {i}'
            ))

    # === Constraint Base-Traces ===
    node_ids = [cid for cid, _ in raw_constraints if cid.startswith("N")]
    edge_ids = [cid for cid, _ in raw_constraints if cid.startswith("E-")]

    node_constraint_trace = go.Scatter(
        x=[numpy.nan] * len(node_ids),
        y=[numpy.nan] * len(node_ids),
        mode="markers",
        marker=dict(color="red", size=28, symbol="pentagon"),
        text=[f"Blocked Node: {cid}" for cid in node_ids],
        name="Node Constraints",
        hoverinfo="text",
        showlegend=False
    )

    edge_constraint_trace = go.Scatter(
        x=[numpy.nan] * (3 * len([cid for cid, _ in raw_constraints if cid.startswith("E-")])),
        y=[numpy.nan] * (3 * len([cid for cid, _ in raw_constraints if cid.startswith("E-")])),
        mode="lines",
        line=dict(color="red", width=10),
        text=[f"Blocked Edge: {cid}" for cid, _ in raw_constraints if cid.startswith("E-")],
        name="Edge Constraints",
        hoverinfo="text",
        showlegend=False
    )

    # AMR Base Trace
    amr_trace = go.Scatter(
        x=[], y=[], mode='markers',
        marker=dict(size=14, symbol='circle'),
        name="AMR Paths",
        hoverinfo='text',
        showlegend=False
    )

    # === Intervall-Preprocessing ===
    intervals = []
    for path in paths:
        p_intervals = []
        for j in range(len(path)):
            node, (t0, t1) = path[j]
            p_intervals.append((t0, t1-0.001, ("node", node)))
            if j < len(path) - 1:
                next_node, (nt0, nt1) = path[j + 1]
                p_intervals.append((t1-0.001, nt0, ("edge", node, next_node)))

        intervals.append(p_intervals)

    # === Create Frames ===
    frames = []


    for t in time_steps:
        # === Constraint Updates ===
        node_xs, node_ys, opacities = [], [], []

        for cid in node_ids:
            cstart, cend = dict(raw_constraints)[cid]

            node_xs.append(pos[cid][0])
            node_ys.append(pos[cid][1])

            if cstart-0.3 <= t <= cend+0.3:
                opacities.append(1.0)
            else:
                opacities.append(0.0)

        edge_xs, edge_ys = [], []
        for cid in edge_ids:
            cstart, cend = dict(raw_constraints)[cid]
            u, v = cid[2:].split("-")
            u, v = "N_" + u, "N_" + v
            if cstart <= t <= cend:
                edge_xs.extend([pos[u][0], pos[v][0], None])
                edge_ys.extend([pos[u][1], pos[v][1], None])
            else:
                edge_xs.extend([numpy.nan, numpy.nan, None])
                edge_ys.extend([numpy.nan, numpy.nan, None])

        # === AMR Updates ===
        xs, ys, texts, colors, sizes = [], [], [], [], []
        for i, path_intervals in enumerate(intervals):
            x, y = None, None
            current_node_id = ""
            for t0, t1, obj in path_intervals:
                if t0 <= t <= t1:
                    if obj[0] == "node":
                        node = obj[1]
                        x, y = pos[node]
                        current_node_id = node
                    elif obj[0] == "edge":
                        u, v = obj[1], obj[2]
                        x0, y0 = pos[u]
                        x1, y1 = pos[v]
                        alpha = (t - t0) / (t1 - t0)
                        x = x0 + alpha * (x1 - x0)
                        y = y0 + alpha * (y1 - y0)
                        current_node_id = f"{u}->{v}"
                    break
            if x is not None and y is not None:
                xs.append(x)
                ys.append(y)
                texts.append(f"AMR {i}: {current_node_id} [{t:.1f}]")
                colors.append(PATH_COLORS[i % len(PATH_COLORS)])
                sizes.append(14)

        frames.append(go.Frame(
            data=[
                go.Scatter(x=node_xs, y=node_ys, marker=dict(opacity=opacities)),   # Node constraints
                go.Scatter(x=edge_xs, y=edge_ys),   # Edge constraints
                go.Scatter(x=xs, y=ys, marker=dict(color=colors, size=sizes))  # AMRs
            ],
            traces=[len(base_traces), len(base_traces)+1, len(base_traces)+2],
            name=str(t)
        ))

    # === Slider Steps ===
    slider_steps = [dict(
        method='animate',
        args=[[str(t)], dict(mode='immediate', frame=dict(duration=0, redraw=False), transition=dict(duration=0))],
        label=f"{t:.1f}"
    ) for t in time_steps]

    fig = go.Figure(
        data=base_traces + [node_constraint_trace, edge_constraint_trace, amr_trace] + start_markers + end_markers,
        layout=go.Layout(
            title_x=0.5, showlegend=True, hovermode='closest',
            width=1000, height=800,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
            margin=dict(t=100, b=20, l=20, r=20),
            legend=dict(x=1.02, y=0.05, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1),
            updatemenus=[dict(
                type='buttons', showactive=False, direction="right",
                x=1.05, y=1.15, xanchor='left', yanchor='bottom',
                buttons=[
                    dict(label='Play', method='animate',
                         args=[None, dict(frame=dict(duration=33, redraw=False), fromcurrent=True, mode='immediate')]),
                    dict(label='Pause', method='animate',
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')])
                ]
            )],
            sliders=[dict(active=0, currentvalue={"prefix": "Zeit: "},
                          pad={"b": 10, "t": 20}, steps=slider_steps,
                          x=0, len=1, y=1.05, yanchor='bottom')]
        ),
        frames=frames
    )

    fig.show()

def draw_animated_graph_type0(G: nx.Graph, paths: list, raw_constraints):
    pos = nx.get_node_attributes(G, "pos") or nx.spring_layout(G, seed=42)

    # Time Points
    raw_times = extract_time_steps(paths)
    min_t, max_t = raw_times[0], raw_times[-1]
    duration = max_t - min_t
    NUM_STEPS = int(duration * 30)
    time_steps = numpy.linspace(min_t, max_t, NUM_STEPS)

    base_traces = [create_edge_trace(G, pos), create_node_trace(G, pos)]

    start_markers, end_markers = [], []
    for i, path in enumerate(paths):
        color = PATH_COLORS[i % len(PATH_COLORS)]
        if not path:
            continue

        start_id = path[0][0]
        end_id = path[-1][0]

        if start_id in pos:
            x, y = pos[start_id]
            start_markers.append(go.Scatter(
                x=[x], y=[y], mode='markers',
                marker=dict(color=color, size=14, symbol='cross', line=dict(width=2, color='black')),
                text=[f"Start AMR {i}: {start_id}"], hoverinfo='text', name=f'Start AMR {i}'
            ))

        if end_id in pos:
            x, y = pos[end_id]
            end_markers.append(go.Scatter(
                x=[x], y=[y], mode='markers',
                marker=dict(color=color, size=14, symbol='square', line=dict(width=2, color='black')),
                text=[f"End AMR {i}: {end_id}"], hoverinfo='text', name=f'End AMR {i}'
            ))

    # === Constraint Base-Traces ===
    zone_constraint_trace = go.Scatter(
        x=[],
        y=[],
        mode="lines",
        fill="toself",
        fillcolor="rgba(255,0,0,0.3)",
        line=dict(color="red", width=2),
        name="Zone Constraints",
        hoverinfo="skip",
        showlegend=False
    )

    # AMR Base Trace
    amr_trace = go.Scatter(
        x=[], y=[], mode='markers',
        marker=dict(size=14, symbol='circle'),
        name="AMR Paths",
        hoverinfo='text',
        showlegend=False
    )

    # === Intervall-Preprocessing ===
    intervals = []
    for path in paths:
        p_intervals = []
        for j in range(len(path)):
            node, (t0, t1) = path[j]
            p_intervals.append((t0, t1 - 0.001, ("node", node)))
            if j < len(path) - 1:
                next_node, (nt0, nt1) = path[j + 1]
                p_intervals.append((t1 - 0.001, nt0, ("edge", node, next_node)))

        intervals.append(p_intervals)

    # === Create Frames===
    frames = []

    for t in time_steps:
        # === Constraint Updates ===
        zone_xs, zone_ys = [], []

        for (cstart, cend, corners) in raw_constraints:
            if cstart -0.3  <= t <= cend+ 0.3:
                xs = [p[0] for p in corners] + [corners[0][0]]
                ys = [p[1] for p in corners] + [corners[0][1]]

                zone_xs.extend(xs + [None])
                zone_ys.extend(ys + [None])
            else:
                zone_xs.extend([numpy.nan] * 5 + [None])
                zone_ys.extend([numpy.nan] * 5 + [None])

        # === AMR Updates ===
        xs, ys, texts, colors, sizes = [], [], [], [], []
        for i, path_intervals in enumerate(intervals):
            x, y = None, None
            current_node_id = ""
            for t0, t1, obj in path_intervals:
                if t0 <= t <= t1:
                    if obj[0] == "node":
                        node = obj[1]
                        x, y = pos[node]
                        current_node_id = node
                    elif obj[0] == "edge":
                        u, v = obj[1], obj[2]
                        x0, y0 = pos[u]
                        x1, y1 = pos[v]
                        alpha = (t - t0) / (t1 - t0)
                        x = x0 + alpha * (x1 - x0)
                        y = y0 + alpha * (y1 - y0)
                        current_node_id = f"{u}->{v}"
                    break
            if x is not None and y is not None:
                xs.append(x)
                ys.append(y)
                texts.append(f"AMR {i}: {current_node_id} [{t:.1f}]")
                colors.append(PATH_COLORS[i % len(PATH_COLORS)])
                sizes.append(14)

        frames.append(go.Frame(
            data=[
                go.Scatter(x=zone_xs, y=zone_ys),
                go.Scatter(x=xs, y=ys, marker=dict(color=colors, size=sizes))
            ],
            traces=[len(base_traces), len(base_traces) + 1],
            name=str(t)
        ))

    # === Slider Steps ===
    slider_steps = [dict(
        method='animate',
        args=[[str(t)], dict(mode='immediate', frame=dict(duration=0, redraw=False), transition=dict(duration=0))],
        label=f"{t:.1f}"
    ) for t in time_steps]

    fig = go.Figure(
        data=base_traces + [zone_constraint_trace, amr_trace] + start_markers + end_markers,
        layout=go.Layout(
            title_x=0.5, showlegend=True, hovermode='closest',
            width=1000, height=800,
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
            margin=dict(t=100, b=20, l=20, r=20),
            legend=dict(x=1.02, y=0.05, bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1),
            updatemenus=[dict(
                type='buttons', showactive=False, direction="right",
                x=1.05, y=1.15, xanchor='left', yanchor='bottom',
                buttons=[
                    dict(label='Play', method='animate',
                         args=[None,
                               dict(frame=dict(duration=33, redraw=False), fromcurrent=True, mode='immediate')]),
                    dict(label='Pause', method='animate',
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')])
                ]
            )],
            sliders=[dict(active=0, currentvalue={"prefix": "Zeit: "},
                          pad={"b": 10, "t": 20}, steps=slider_steps,
                          x=0, len=1, y=1.05, yanchor='bottom')]
        ),
        frames=frames
    )

    fig.show()

# === Interface ===

def show_lif(lif_path: str | Layout, amr_paths: Optional[List[List[str]]] = None):
    if isinstance(lif_path, Layout) is True:
        g = build_graph_lif_object(lif_path)
    else:
        g = build_graph(load_lif_file(lif_path))
    draw_static_graph(g, amr_paths or [])



def show_lif_animated(lif_path: str | Layout, amr_paths: Optional[List[List[str]]] = None, constraints = [],
                      type: int = -1 ):
    show_lif(lif_path, amr_paths)
    if isinstance(lif_path, str):
        g = build_graph(load_lif_file(lif_path))
    else:
        g = build_graph_lif_object(lif_path)
    anim_paths = []
    for p in amr_paths or []:
        path_with_intervals = []
        for i, n in enumerate(p):
            if i < len(p) - 1:
                path_with_intervals.append((n, (i, i + 0.001)))
            else:
                # Last interval until infinity
                path_with_intervals.append((n, (i, float('inf'))))
        anim_paths.append(path_with_intervals)
    draw_animated_graph(g, anim_paths, constraints, type)



def show_lif_animated2(lif: str | Layout, amr_paths: Optional[List[List[Tuple[str, Tuple[float, float]]]]] = None,
                       constraints = [] , type = -1):
    show_lif(lif, [[node_id for node_id, _ in path] for path in amr_paths])
    if isinstance(lif, str):
        g = build_graph(load_lif_file(lif))
    else:
        g = build_graph_lif_object(lif)
    draw_animated_graph(g, amr_paths or [], constraints, type)


if __name__ == "__main__":
    paths = [[('N_28_14', (1, 1.1)), ('N_28_15', (2.0, 2.1)), ('N_28_16', (3.0, 3.1)), ('N_28_17', (4.0, 4.1)), ('N_29_17', (5.0, numpy.inf))], [('N_12_15', (1, 1.1)), ('N_13_15', (2.0, 2.1)), ('N_14_15', (3.0, 3.1)), ('N_15_15', (4.0, 4.1)), ('N_15_16', (5.0, 5.1)), ('N_16_16', (6.0, 6.1)), ('N_17_16', (7.0, 7.1)), ('N_17_17', (8.0, 8.1)), ('N_18_17', (9.0, 9.1)), ('N_19_17', (10.0, 10.1)), ('N_19_16', (11.0, 11.1)), ('N_19_15', (12.0, 12.1)), ('N_20_15', (13.0, 13.1)), ('N_21_15', (14.0, 14.1)), ('N_22_15', (15.0, 15.1)), ('N_23_15', (16.0, 16.1)), ('N_24_15', (17.0, 17.1)), ('N_24_14', (18.0, 18.1)), ('N_24_13', (19.0, 19.1)), ('N_25_13', (20.0, 20.1)), ('N_26_13', (21.0, 21.1)), ('N_27_13', (22.0, 22.1)), ('N_28_13', (23.0, 23.1)), ('N_28_12', (24.0, 24.1)), ('N_28_11', (25.0, 25.1)), ('N_28_10', (26.0, 26.1)), ('N_29_10', (27.0, 27.1)), ('N_29_9', (28.0, 28.1)), ('N_29_8', (29.0, 29.1)), ('N_30_8', (30.0, 30.1)), ('N_31_8', (31.0, 31.1)), ('N_31_7', (32.0, 32.1)), ('N_31_6', (33.0, 33.1)), ('N_30_6', (34.0, 34.1)), ('N_30_5', (35.0, numpy.inf))], [('N_5_12', (1, 1.1)), ('N_5_13', (2.0, 2.1)), ('N_5_14', (3.0, 3.1)), ('N_5_15', (4.0, 4.1)), ('N_5_16', (5.0, 5.1)), ('N_5_17', (6.0, 6.1)), ('N_5_18', (7.0, 7.1)), ('N_5_19', (8.0, 8.1)), ('N_5_20', (9.0, 9.1)), ('N_5_21', (10.0, 10.1)), ('N_5_22', (11.0, 11.1)), ('N_5_23', (12.0, 12.1)), ('N_6_23', (13.0, 13.1)), ('N_6_24', (14.0, 14.1)), ('N_6_25', (15.0, 15.1)), ('N_6_26', (16.0, 16.1)), ('N_7_26', (17.0, 17.1)), ('N_7_27', (18.0, 18.1)), ('N_7_28', (19.0, 19.1)), ('N_7_29', (20.0, 20.1)), ('N_8_29', (21.0, 21.1)), ('N_9_29', (22.0, 22.1)), ('N_10_29', (23.0, 23.1)), ('N_11_29', (24.0, 24.1)), ('N_12_29', (25.0, 25.1)), ('N_13_29', (26.0, 26.1)), ('N_14_29', (27.0, 27.1)), ('N_15_29', (28.0, 28.1)), ('N_15_30', (29.0, 29.1)), ('N_16_30', (30.0, 30.1)), ('N_17_30', (31.0, 31.1)), ('N_17_31', (32.0, 32.1)), ('N_18_31', (33.0, 33.1)), ('N_19_31', (34.0, 34.1)), ('N_20_31', (35.0, numpy.inf))], [('N_2_16', (1, 1.1)), ('N_3_16', (2.0, 2.1)), ('N_3_17', (3.0, 3.1)), ('N_3_18', (4.0, 4.1)), ('N_3_19', (5.0, 5.1)), ('N_4_19', (6.0, 6.1)), ('N_5_19', (7.0, 7.1)), ('N_5_20', (8.0, 8.1)), ('N_5_21', (9.0, 9.1)), ('N_5_22', (10.0, 10.1)), ('N_5_23', (11.0, 11.1)), ('N_6_23', (12.0, 12.1)), ('N_6_24', (13.0, 13.1)), ('N_6_25', (14.0, 14.1)), ('N_6_26', (15.0, 15.1)), ('N_7_26', (16.0, 16.1)), ('N_7_27', (17.0, 17.1)), ('N_8_27', (18.0, numpy.inf))], [('N_14_23', (1, 1.1)), ('N_15_23', (2.0, 2.1)), ('N_15_22', (3.0, 3.1)), ('N_16_22', (4.0, 4.1)), ('N_16_21', (5.0, 5.1)), ('N_16_20', (6.0, 6.1)), ('N_16_19', (7.0, 7.1)), ('N_17_19', (8.0, 8.1)), ('N_18_19', (9.0, 9.1)), ('N_18_18', (10.0, 10.1)), ('N_18_17', (11.0, 11.1)), ('N_19_17', (12.0, 12.1)), ('N_19_16', (13.0, 13.1)), ('N_19_15', (14.0, 14.1)), ('N_20_15', (15.0, 15.1)), ('N_21_15', (16.0, 16.1)), ('N_22_15', (17.0, 17.1)), ('N_23_15', (18.0, 18.1)), ('N_24_15', (19.0, 19.1)), ('N_24_14', (20.0, 20.1)), ('N_24_13', (21.0, 21.1)), ('N_25_13', (22.0, 22.1)), ('N_26_13', (23.0, 23.1)), ('N_27_13', (24.0, 24.1)), ('N_28_13', (25.0, 25.1)), ('N_28_12', (26.0, 26.1)), ('N_28_11', (27.0, 27.1)), ('N_28_10', (28.0, 28.1)), ('N_29_10', (29.0, 29.1)), ('N_29_9', (30.0, 30.1)), ('N_29_8', (31.0, 31.1)), ('N_30_8', (32.0, 32.1)), ('N_31_8', (33.0, 33.1)), ('N_31_7', (34.0, numpy.inf))], [('N_31_3', (1, 1.1)), ('N_30_3', (2.0, 2.1)), ('N_29_3', (3.0, 3.1)), ('N_28_3', (4.0, 4.1)), ('N_27_3', (5.0, 5.1)), ('N_26_3', (6.0, 6.1)), ('N_25_3', (7.0, 7.1)), ('N_24_3', (8.0, 8.1)), ('N_23_3', (9.0, 9.1)), ('N_22_3', (10.0, 10.1)), ('N_22_4', (11.0, 11.1)), ('N_22_5', (12.0, 12.1)), ('N_22_6', (13.0, 13.1)), ('N_22_7', (14.0, numpy.inf))], [('N_6_16', (1, 1.1)), ('N_6_15', (2.0, 2.1)), ('N_6_14', (3.0, 3.1)), ('N_7_14', (4.0, 4.1)), ('N_7_13', (5.0, 5.1)), ('N_7_12', (6.0, 6.1)), ('N_7_11', (7.0, 7.1)), ('N_7_10', (8.0, 8.1)), ('N_7_9', (9.0, 9.1)), ('N_7_8', (10.0, 10.1)), ('N_8_8', (11.0, 11.1)), ('N_8_7', (12.0, 12.1)), ('N_8_6', (13.0, 13.1)), ('N_9_6', (14.0, 14.1)), ('N_10_6', (15.0, 15.1)), ('N_11_6', (16.0, 16.1)), ('N_12_6', (17.0, 17.1)), ('N_13_6', (18.0, 18.1)), ('N_14_6', (19.0, 19.1)), ('N_15_6', (20.0, 20.1)), ('N_16_6', (21.0, 21.1)), ('N_16_5', (22.0, 22.1)), ('N_17_5', (23.0, 23.1)), ('N_17_4', (24.0, 24.1)), ('N_17_3', (25.0, 25.1)), ('N_18_3', (26.0, 26.1)), ('N_19_3', (27.0, 27.1)), ('N_19_2', (28.0, 28.1)), ('N_20_2', (29.0, 29.1)), ('N_21_2', (30.0, 30.1)), ('N_22_2', (31.0, 31.1)), ('N_22_3', (32.0, 32.1)), ('N_22_4', (33.0, 33.1)), ('N_22_5', (34.0, 34.1)), ('N_22_6', (35.0, 35.1)), ('N_23_6', (36.0, 36.1)), ('N_23_7', (37.0, numpy.inf))], [('N_30_11', (1, 1.1)), ('N_29_11', (2.0, 2.1)), ('N_28_11', (3.0, 3.1)), ('N_28_12', (4.0, 4.1)), ('N_28_13', (5.0, 5.1)), ('N_27_13', (6.0, 6.1)), ('N_26_13', (7.0, 7.1)), ('N_25_13', (8.0, 8.1)), ('N_24_13', (9.0, 9.1)), ('N_24_14', (10.0, 10.1)), ('N_24_15', (11.0, 11.1)), ('N_23_15', (12.0, 12.1)), ('N_22_15', (13.0, 13.1)), ('N_22_16', (14.0, 14.1)), ('N_21_16', (15.0, 15.1)), ('N_20_16', (16.0, 16.1)), ('N_19_16', (17.0, 17.1)), ('N_19_17', (18.0, 18.1)), ('N_18_17', (19.0, 19.1)), ('N_17_17', (20.0, 20.1)), ('N_17_16', (21.0, 21.1)), ('N_16_16', (22.0, 22.1)), ('N_15_16', (23.0, 23.1)), ('N_15_15', (24.0, 24.1)), ('N_14_15', (25.0, 25.1)), ('N_13_15', (26.0, 26.1)), ('N_12_15', (27.0, 27.1)), ('N_12_16', (28.0, 28.1)), ('N_11_16', (29.0, 29.1)), ('N_11_17', (30.0, 30.1)), ('N_11_18', (31.0, numpy.inf))], [('N_24_2', (1, 1.1)), ('N_24_3', (2.0, 2.1)), ('N_24_4', (3.0, 3.1)), ('N_25_4', (4.0, 4.1)), ('N_25_5', (5.0, 5.1)), ('N_26_5', (6.0, 6.1)), ('N_27_5', (7.0, 7.1)), ('N_27_6', (8.0, 8.1)), ('N_27_7', (9.0, 9.1)), ('N_27_8', (10.0, 10.1)), ('N_28_8', (11.0, 11.1)), ('N_29_8', (12.0, 12.1)), ('N_29_9', (13.0, 13.1)), ('N_29_10', (14.0, 14.1)), ('N_28_10', (15.0, 15.1)), ('N_28_11', (16.0, 16.1)), ('N_28_12', (17.0, 17.1)), ('N_28_13', (18.0, 18.1)), ('N_28_14', (19.0, 19.1)), ('N_28_15', (20.0, 20.1)), ('N_28_16', (21.0, 21.1)), ('N_28_17', (22.0, 22.1)), ('N_28_18', (23.0, 23.1)), ('N_28_19', (24.0, 24.1)), ('N_28_20', (25.0, 25.1)), ('N_29_20', (26.0, 26.1)), ('N_29_21', (27.0, 27.1)), ('N_29_22', (28.0, 28.1)), ('N_28_22', (29.0, numpy.inf))], [('N_28_17', (1, 1.1)), ('N_27_17', (2.0, 2.1)), ('N_27_16', (3.0, 3.1)), ('N_26_16', (4.0, 4.1)), ('N_25_16', (5.0, 5.1)), ('N_24_16', (6.0, 6.1)), ('N_23_16', (7.0, 7.1)), ('N_22_16', (8.0, 8.1)), ('N_21_16', (9.0, 9.1)), ('N_21_17', (10.0, 10.1)), ('N_21_18', (11.0, 11.1)), ('N_20_18', (12.0, 12.1)), ('N_19_18', (13.0, 13.1)), ('N_18_18', (14.0, 14.1)), ('N_18_17', (15.0, 15.1)), ('N_17_17', (16.0, 16.1)), ('N_17_16', (17.0, 17.1)), ('N_16_16', (18.0, 18.1)), ('N_15_16', (19.0, 19.1)), ('N_15_15', (20.0, 20.1)), ('N_14_15', (21.0, 21.1)), ('N_13_15', (22.0, 22.1)), ('N_12_15', (23.0, 23.1)), ('N_12_16', (24.0, 24.1)), ('N_11_16', (25.0, 25.1)), ('N_10_16', (26.0, 26.1)), ('N_10_17', (27.0, 27.1)), ('N_9_17', (28.0, 28.1)), ('N_8_17', (29.0, 29.1)), ('N_7_17', (30.0, 30.1)), ('N_7_16', (31.0, 31.1)), ('N_6_16', (32.0, 32.1)), ('N_5_16', (33.0, 33.1)), ('N_4_16', (34.0, 34.1)), ('N_3_16', (35.0, 35.1)), ('N_2_16', (36.0, 36.1)), ('N_1_16', (37.0, 37.1)), ('N_1_15', (38.0, numpy.inf))], [('N_8_3', (1, 1.1)), ('N_7_3', (2.0, 2.1)), ('N_6_3', (3.0, 3.1)), ('N_5_3', (4.0, 4.1)), ('N_5_4', (5.0, 5.1)), ('N_5_5', (6.0, 6.1)), ('N_5_6', (7.0, 7.1)), ('N_5_7', (8.0, 8.1)), ('N_5_8', (9.0, 9.1)), ('N_5_9', (10.0, 10.1)), ('N_5_10', (11.0, 11.1)), ('N_5_11', (12.0, 12.1)), ('N_5_12', (13.0, 13.1)), ('N_5_13', (14.0, 14.1)), ('N_5_14', (15.0, 15.1)), ('N_5_15', (16.0, 16.1)), ('N_5_16', (17.0, 17.1)), ('N_5_17', (18.0, 18.1)), ('N_6_17', (19.0, numpy.inf))], [('N_13_21', (1, 1.1)), ('N_12_21', (2.0, 2.1)), ('N_11_21', (3.0, 3.1)), ('N_10_21', (4.0, 4.1)), ('N_10_22', (5.0, 5.1)), ('N_10_23', (6.0, 6.1)), ('N_9_23', (7.0, 7.1)), ('N_8_23', (8.0, 8.1)), ('N_7_23', (9.0, 9.1)), ('N_6_23', (10.0, 10.1)), ('N_5_23', (11.0, 11.1)), ('N_4_23', (12.0, 12.1)), ('N_3_23', (13.0, 13.1)), ('N_3_22', (14.0, numpy.inf))], [('N_26_28', (1, 1.1)), ('N_25_28', (2.0, 2.1)), ('N_24_28', (3.0, 3.1)), ('N_23_28', (4.0, 4.1)), ('N_22_28', (5.0, 5.1)), ('N_21_28', (6.0, 6.1)), ('N_21_27', (7.0, 7.1)), ('N_20_27', (8.0, 8.1)), ('N_19_27', (9.0, 9.1)), ('N_18_27', (10.0, 10.1)), ('N_17_27', (11.0, 11.1)), ('N_16_27', (12.0, 12.1)), ('N_15_27', (13.0, 13.1)), ('N_14_27', (14.0, 14.1)), ('N_14_26', (15.0, 15.1)), ('N_13_26', (16.0, 16.1)), ('N_12_26', (17.0, 17.1)), ('N_12_25', (18.0, 18.1)), ('N_11_25', (19.0, 19.1)), ('N_10_25', (20.0, 20.1)), ('N_10_24', (21.0, 21.1)), ('N_10_23', (22.0, 22.1)), ('N_9_23', (23.0, 23.1)), ('N_8_23', (24.0, 24.1)), ('N_7_23', (25.0, 25.1)), ('N_6_23', (26.0, 26.1)), ('N_5_23', (27.0, 27.1)), ('N_5_22', (28.0, 28.1)), ('N_5_21', (29.0, 29.1)), ('N_5_20', (30.0, 30.1)), ('N_5_19', (31.0, 31.1)), ('N_5_18', (32.0, 32.1)), ('N_5_17', (33.0, 33.1)), ('N_5_16', (34.0, 34.1)), ('N_5_15', (35.0, 35.1)), ('N_5_14', (36.0, 36.1)), ('N_5_13', (37.0, 37.1)), ('N_5_12', (38.0, 38.1)), ('N_5_11', (39.0, 39.1)), ('N_5_10', (40.0, 40.1)), ('N_5_9', (41.0, 41.1)), ('N_5_8', (42.0, 42.1)), ('N_5_7', (43.0, 43.1)), ('N_5_6', (44.0, 44.1)), ('N_5_5', (45.0, 45.1)), ('N_5_4', (46.0, 46.1)), ('N_5_3', (47.0, 47.1)), ('N_4_3', (48.0, 48.1)), ('N_3_3', (49.0, 49.1)), ('N_3_2', (50.0, 50.1)), ('N_3_1', (51.0, 51.1)), ('N_3_0', (52.0, numpy.inf))], [('N_3_24', (1, 1.1)), ('N_3_25', (2.0, 2.1)), ('N_3_26', (3.0, 3.1)), ('N_4_26', (4.0, 4.1)), ('N_5_26', (5.0, 5.1)), ('N_6_26', (6.0, 6.1)), ('N_7_26', (7.0, 7.1)), ('N_8_26', (8.0, 8.1)), ('N_9_26', (9.0, 9.1)), ('N_10_26', (10.0, 10.1)), ('N_11_26', (11.0, 11.1)), ('N_12_26', (12.0, 12.1)), ('N_13_26', (13.0, 13.1)), ('N_13_27', (14.0, 14.1)), ('N_14_27', (15.0, 15.1)), ('N_15_27', (16.0, 16.1)), ('N_16_27', (17.0, 17.1)), ('N_17_27', (18.0, 18.1)), ('N_18_27', (19.0, 19.1)), ('N_19_27', (20.0, 20.1)), ('N_20_27', (21.0, 21.1)), ('N_21_27', (22.0, 22.1)), ('N_21_28', (23.0, 23.1)), ('N_22_28', (24.0, 24.1)), ('N_23_28', (25.0, 25.1)), ('N_24_28', (26.0, 26.1)), ('N_25_28', (27.0, 27.1)), ('N_26_28', (28.0, 28.1)), ('N_27_28', (29.0, 29.1)), ('N_27_29', (30.0, 30.1)), ('N_28_29', (31.0, 31.1)), ('N_29_29', (32.0, 32.1)), ('N_30_29', (33.0, numpy.inf))], [('N_5_11', (1, 1.1)), ('N_5_12', (2.0, 2.1)), ('N_5_13', (3.0, 3.1)), ('N_5_14', (4.0, 4.1)), ('N_5_15', (5.0, 5.1)), ('N_4_15', (6.0, 6.1)), ('N_4_16', (7.0, 7.1)), ('N_3_16', (8.0, 8.1)), ('N_3_17', (9.0, 9.1)), ('N_3_18', (10.0, 10.1)), ('N_3_19', (11.0, 11.1)), ('N_2_19', (12.0, 12.1)), ('N_2_20', (13.0, 13.1)), ('N_2_21', (14.0, 14.1)), ('N_2_22', (15.0, 15.1)), ('N_2_23', (16.0, 16.1)), ('N_2_24', (17.0, numpy.inf))], [('N_21_2', (1, 1.1)), ('N_20_2', (2.0, 2.1)), ('N_19_2', (3.0, 3.1)), ('N_19_3', (4.0, 4.1)), ('N_18_3', (5.0, 5.1)), ('N_17_3', (6.0, 6.1)), ('N_17_4', (7.0, 7.1)), ('N_17_5', (8.0, 8.1)), ('N_16_5', (9.0, 9.1)), ('N_16_6', (10.0, 10.1)), ('N_15_6', (11.0, 11.1)), ('N_14_6', (12.0, 12.1)), ('N_13_6', (13.0, 13.1)), ('N_13_7', (14.0, 14.1)), ('N_13_8', (15.0, 15.1)), ('N_12_8', (16.0, 16.1)), ('N_12_9', (17.0, 17.1)), ('N_12_10', (18.0, 18.1)), ('N_13_10', (19.0, 19.1)), ('N_13_11', (20.0, 20.1)), ('N_13_12', (21.0, 21.1)), ('N_12_12', (22.0, 22.1)), ('N_12_13', (23.0, 23.1)), ('N_12_14', (24.0, 24.1)), ('N_12_15', (25.0, 25.1)), ('N_12_16', (26.0, 26.1)), ('N_11_16', (27.0, 27.1)), ('N_11_17', (28.0, 28.1)), ('N_11_18', (29.0, 29.1)), ('N_11_19', (30.0, 30.1)), ('N_11_20', (31.0, 31.1)), ('N_11_21', (32.0, 32.1)), ('N_10_21', (33.0, 33.1)), ('N_10_22', (34.0, 34.1)), ('N_10_23', (35.0, 35.1)), ('N_10_24', (36.0, 36.1)), ('N_10_25', (37.0, 37.1)), ('N_10_26', (38.0, 38.1)), ('N_9_26', (39.0, 39.1)), ('N_8_26', (40.0, numpy.inf))], [('N_2_0', (1, 1.1)), ('N_2_1', (2.0, 2.1)), ('N_2_2', (3.0, 3.1)), ('N_2_3', (4.0, 4.1)), ('N_3_3', (5.0, 5.1)), ('N_4_3', (6.0, 6.1)), ('N_5_3', (7.0, 7.1)), ('N_5_4', (8.0, 8.1)), ('N_5_5', (9.0, 9.1)), ('N_4_5', (10.0, 10.1)), ('N_4_6', (11.0, 11.1)), ('N_4_7', (12.0, 12.1)), ('N_4_8', (13.0, 13.1)), ('N_4_9', (14.0, 14.1)), ('N_4_10', (15.0, 15.1)), ('N_4_11', (16.0, 16.1)), ('N_4_12', (17.0, 17.1)), ('N_4_13', (18.0, 18.1)), ('N_4_14', (19.0, 19.1)), ('N_4_15', (20.0, 20.1)), ('N_4_16', (21.0, 21.1)), ('N_3_16', (22.0, 22.1)), ('N_3_17', (23.0, 23.1)), ('N_3_18', (24.0, 24.1)), ('N_3_19', (25.0, 25.1)), ('N_2_19', (26.0, numpy.inf))], [('N_21_9', (1, 1.1)), ('N_20_9', (2.0, 2.1)), ('N_19_9', (3.0, 3.1)), ('N_18_9', (4.0, 4.1)), ('N_17_9', (5.0, 5.1)), ('N_16_9', (6.0, 6.1)), ('N_15_9', (7.0, 7.1)), ('N_15_8', (8.0, 8.1)), ('N_14_8', (9.0, 9.1)), ('N_13_8', (10.0, 10.1)), ('N_12_8', (11.0, 11.1)), ('N_11_8', (12.0, 12.1)), ('N_10_8', (13.0, 13.1)), ('N_9_8', (14.0, 14.1)), ('N_9_9', (15.0, 15.1)), ('N_9_10', (16.0, 16.1)), ('N_8_10', (17.0, 17.1)), ('N_7_10', (18.0, 18.1)), ('N_7_11', (19.0, 19.1)), ('N_7_12', (20.0, 20.1)), ('N_7_13', (21.0, 21.1)), ('N_7_14', (22.0, 22.1)), ('N_7_15', (23.0, 23.1)), ('N_8_15', (24.0, numpy.inf))], [('N_8_17', (1, 1.1)), ('N_8_18', (2.0, 2.1)), ('N_9_18', (3.0, 3.1)), ('N_10_18', (4.0, 4.1)), ('N_10_19', (5.0, 5.1)), ('N_11_19', (6.0, 6.1)), ('N_11_20', (7.0, 7.1)), ('N_11_21', (8.0, 8.1)), ('N_10_21', (9.0, 9.1)), ('N_9_21', (10.0, 10.1)), ('N_8_21', (11.0, numpy.inf))], [('N_0_14', (1, 1.1)), ('N_1_14', (2.0, 2.1)), ('N_2_14', (3.0, 3.1)), ('N_3_14', (4.0, 4.1)), ('N_4_14', (5.0, 5.1)), ('N_4_13', (6.0, 6.1)), ('N_4_12', (7.0, 7.1)), ('N_4_11', (8.0, 8.1)), ('N_4_10', (9.0, 9.1)), ('N_4_9', (10.0, 10.1)), ('N_5_9', (11.0, 11.1)), ('N_6_9', (12.0, 12.1)), ('N_7_9', (13.0, 13.1)), ('N_7_8', (14.0, 14.1)), ('N_8_8', (15.0, 15.1)), ('N_9_8', (16.0, 16.1)), ('N_10_8', (17.0, 17.1)), ('N_11_8', (18.0, numpy.inf))], [('N_20_22', (1, 1.1)), ('N_19_22', (2.0, 2.1)), ('N_18_22', (3.0, 3.1)), ('N_17_22', (4.0, 4.1)), ('N_16_22', (5.0, 5.1)), ('N_16_21', (6.0, 6.1)), ('N_16_20', (7.0, 7.1)), ('N_15_20', (8.0, 8.1)), ('N_14_20', (9.0, 9.1)), ('N_14_21', (10.0, 10.1)), ('N_13_21', (11.0, 11.1)), ('N_12_21', (12.0, 12.1)), ('N_11_21', (13.0, 13.1)), ('N_11_20', (14.0, 14.1)), ('N_11_19', (15.0, 15.1)), ('N_10_19', (16.0, 16.1)), ('N_10_18', (17.0, 17.1)), ('N_10_17', (18.0, 18.1)), ('N_9_17', (19.0, 19.1)), ('N_8_17', (20.0, 20.1)), ('N_7_17', (21.0, 21.1)), ('N_7_16', (22.0, 22.1)), ('N_6_16', (23.0, 23.1)), ('N_5_16', (24.0, 24.1)), ('N_4_16', (25.0, 25.1)), ('N_4_15', (26.0, 26.1)), ('N_4_14', (27.0, 27.1)), ('N_4_13', (28.0, 28.1)), ('N_4_12', (29.0, 29.1)), ('N_4_11', (30.0, 30.1)), ('N_3_11', (31.0, 31.1)), ('N_3_10', (32.0, 32.1)), ('N_3_9', (33.0, 33.1)), ('N_3_8', (34.0, 34.1)), ('N_3_7', (35.0, numpy.inf))], [('N_28_10', (1, 1.1)), ('N_28_11', (2.0, 2.1)), ('N_28_12', (3.0, 3.1)), ('N_28_13', (4.0, 4.1)), ('N_27_13', (5.0, 5.1)), ('N_26_13', (6.0, 6.1)), ('N_25_13', (7.0, 7.1)), ('N_24_13', (8.0, 8.1)), ('N_24_14', (9.0, 9.1)), ('N_24_15', (10.0, 10.1)), ('N_23_15', (11.0, 11.1)), ('N_22_15', (12.0, 12.1)), ('N_21_15', (13.0, 13.1)), ('N_21_16', (14.0, 14.1)), ('N_20_16', (15.0, 15.1)), ('N_19_16', (16.0, 16.1)), ('N_19_17', (17.0, 17.1)), ('N_18_17', (18.0, 18.1)), ('N_17_17', (19.0, 19.1)), ('N_17_16', (20.0, 20.1)), ('N_16_16', (21.0, 21.1)), ('N_15_16', (22.0, 22.1)), ('N_15_15', (23.0, 23.1)), ('N_14_15', (24.0, 24.1)), ('N_13_15', (25.0, 25.1)), ('N_12_15', (26.0, 26.1)), ('N_12_16', (27.0, 27.1)), ('N_11_16', (28.0, 28.1)), ('N_10_16', (29.0, 29.1)), ('N_10_17', (30.0, 30.1)), ('N_9_17', (31.0, 31.1)), ('N_8_17', (32.0, 32.1)), ('N_7_17', (33.0, 33.1)), ('N_7_16', (34.0, 34.1)), ('N_6_16', (35.0, 35.1)), ('N_5_16', (36.0, 36.1)), ('N_4_16', (37.0, 37.1)), ('N_3_16', (38.0, 38.1)), ('N_2_16', (39.0, 39.1)), ('N_1_16', (40.0, 40.1)), ('N_0_16', (41.0, 41.1)), ('N_0_15', (42.0, numpy.inf))], [('N_9_27', (1, 1.1)), ('N_10_27', (2.0, 2.1)), ('N_10_26', (3.0, 3.1)), ('N_10_25', (4.0, 4.1)), ('N_10_24', (5.0, 5.1)), ('N_11_24', (6.0, 6.1)), ('N_11_23', (7.0, 7.1)), ('N_11_22', (8.0, 8.1)), ('N_11_21', (9.0, 9.1)), ('N_11_20', (10.0, 10.1)), ('N_11_19', (11.0, 11.1)), ('N_11_18', (12.0, 12.1)), ('N_11_17', (13.0, 13.1)), ('N_11_16', (14.0, 14.1)), ('N_12_16', (15.0, 15.1)), ('N_12_15', (16.0, 16.1)), ('N_12_14', (17.0, 17.1)), ('N_12_13', (18.0, 18.1)), ('N_12_12', (19.0, 19.1)), ('N_13_12', (20.0, 20.1)), ('N_14_12', (21.0, 21.1)), ('N_15_12', (22.0, 22.1)), ('N_16_12', (23.0, 23.1)), ('N_17_12', (24.0, 24.1)), ('N_18_12', (25.0, numpy.inf))], [('N_28_29', (1, 1.1)), ('N_27_29', (2.0, 2.1)), ('N_27_28', (3.0, 3.1)), ('N_26_28', (4.0, 4.1)), ('N_25_28', (5.0, 5.1)), ('N_24_28', (6.0, 6.1)), ('N_23_28', (7.0, 7.1)), ('N_22_28', (8.0, 8.1)), ('N_21_28', (9.0, 9.1)), ('N_21_27', (10.0, 10.1)), ('N_20_27', (11.0, 11.1)), ('N_19_27', (12.0, 12.1)), ('N_18_27', (13.0, 13.1)), ('N_18_26', (14.0, 14.1)), ('N_18_25', (15.0, 15.1)), ('N_17_25', (16.0, 16.1)), ('N_17_24', (17.0, 17.1)), ('N_17_23', (18.0, 18.1)), ('N_16_23', (19.0, 19.1)), ('N_15_23', (20.0, 20.1)), ('N_14_23', (21.0, 21.1)), ('N_14_24', (22.0, 22.1)), ('N_13_24', (23.0, 23.1)), ('N_12_24', (24.0, 24.1)), ('N_11_24', (25.0, 25.1)), ('N_10_24', (26.0, 26.1)), ('N_10_23', (27.0, 27.1)), ('N_9_23', (28.0, 28.1)), ('N_8_23', (29.0, 29.1)), ('N_7_23', (30.0, 30.1)), ('N_6_23', (31.0, 31.1)), ('N_5_23', (32.0, 32.1)), ('N_5_22', (33.0, 33.1)), ('N_5_21', (34.0, 34.1)), ('N_5_20', (35.0, 35.1)), ('N_5_19', (36.0, 36.1)), ('N_4_19', (37.0, 37.1)), ('N_4_18', (38.0, 38.1)), ('N_4_17', (39.0, 39.1)), ('N_4_16', (40.0, 40.1)), ('N_4_15', (41.0, 41.1)), ('N_4_14', (42.0, 42.1)), ('N_3_14', (43.0, numpy.inf))], [('N_10_14', (1, 1.1)), ('N_9_14', (2.0, 2.1)), ('N_9_15', (3.0, 3.1)), ('N_8_15', (4.0, 4.1)), ('N_7_15', (5.0, 5.1)), ('N_6_15', (6.0, 6.1)), ('N_5_15', (7.0, 7.1)), ('N_5_16', (8.0, 8.1)), ('N_5_17', (9.0, 9.1)), ('N_5_18', (10.0, 10.1)), ('N_5_19', (11.0, 11.1)), ('N_5_20', (12.0, 12.1)), ('N_5_21', (13.0, 13.1)), ('N_5_22', (14.0, 14.1)), ('N_5_23', (15.0, 15.1)), ('N_6_23', (16.0, 16.1)), ('N_6_24', (17.0, 17.1)), ('N_6_25', (18.0, 18.1)), ('N_6_26', (19.0, 19.1)), ('N_7_26', (20.0, 20.1)), ('N_7_27', (21.0, 21.1)), ('N_7_28', (22.0, 22.1)), ('N_7_29', (23.0, 23.1)), ('N_7_30', (24.0, 24.1)), ('N_7_31', (25.0, numpy.inf))], [('N_15_22', (1, 1.1)), ('N_16_22', (2.0, 2.1)), ('N_16_21', (3.0, 3.1)), ('N_16_20', (4.0, 4.1)), ('N_15_20', (5.0, 5.1)), ('N_14_20', (6.0, 6.1)), ('N_14_21', (7.0, 7.1)), ('N_13_21', (8.0, 8.1)), ('N_12_21', (9.0, 9.1)), ('N_11_21', (10.0, 10.1)), ('N_11_22', (11.0, 11.1)), ('N_11_23', (12.0, 12.1)), ('N_11_24', (13.0, 13.1)), ('N_11_25', (14.0, 14.1)), ('N_11_26', (15.0, numpy.inf))], [('N_17_10', (1, 1.1)), ('N_16_10', (2.0, 2.1)), ('N_15_10', (3.0, 3.1)), ('N_15_9', (4.0, 4.1)), ('N_15_8', (5.0, 5.1)), ('N_14_8', (6.0, 6.1)), ('N_13_8', (7.0, 7.1)), ('N_12_8', (8.0, 8.1)), ('N_11_8', (9.0, 9.1)), ('N_11_9', (10.0, numpy.inf))], [('N_5_6', (1, 1.1)), ('N_6_6', (2.0, 2.1)), ('N_7_6', (3.0, 3.1)), ('N_8_6', (4.0, 4.1)), ('N_9_6', (5.0, 5.1)), ('N_10_6', (6.0, 6.1)), ('N_11_6', (7.0, 7.1)), ('N_12_6', (8.0, 8.1)), ('N_13_6', (9.0, 9.1)), ('N_13_7', (10.0, 10.1)), ('N_13_8', (11.0, 11.1)), ('N_14_8', (12.0, 12.1)), ('N_15_8', (13.0, 13.1)), ('N_15_9', (14.0, 14.1)), ('N_16_9', (15.0, 15.1)), ('N_17_9', (16.0, 16.1)), ('N_18_9', (17.0, 17.1)), ('N_19_9', (18.0, 18.1)), ('N_20_9', (19.0, 19.1)), ('N_20_10', (20.0, 20.1)), ('N_21_10', (21.0, numpy.inf))], [('N_30_23', (1, 1.1)), ('N_29_23', (2.0, 2.1)), ('N_29_22', (3.0, 3.1)), ('N_29_21', (4.0, 4.1)), ('N_29_20', (5.0, 5.1)), ('N_28_20', (6.0, 6.1)), ('N_27_20', (7.0, 7.1)), ('N_26_20', (8.0, 8.1)), ('N_25_20', (9.0, 9.1)), ('N_24_20', (10.0, 10.1)), ('N_23_20', (11.0, 11.1)), ('N_22_20', (12.0, 12.1)), ('N_22_19', (13.0, numpy.inf))], [('N_3_3', (1, 1.1)), ('N_4_3', (2.0, 2.1)), ('N_5_3', (3.0, 3.1)), ('N_5_4', (4.0, 4.1)), ('N_5_5', (5.0, 5.1)), ('N_5_6', (6.0, 6.1)), ('N_5_7', (7.0, 7.1)), ('N_5_8', (8.0, 8.1)), ('N_5_9', (9.0, 9.1)), ('N_5_10', (10.0, 10.1)), ('N_5_11', (11.0, 11.1)), ('N_5_12', (12.0, 12.1)), ('N_5_13', (13.0, 13.1)), ('N_5_14', (14.0, 14.1)), ('N_5_15', (15.0, 15.1)), ('N_5_16', (16.0, 16.1)), ('N_5_17', (17.0, 17.1)), ('N_5_18', (18.0, 18.1)), ('N_5_19', (19.0, 19.1)), ('N_5_20', (20.0, 20.1)), ('N_5_21', (21.0, 21.1)), ('N_5_22', (22.0, 22.1)), ('N_5_23', (23.0, 23.1)), ('N_6_23', (24.0, 24.1)), ('N_6_24', (25.0, 25.1)), ('N_6_25', (26.0, 26.1)), ('N_7_25', (27.0, 27.1)), ('N_8_25', (28.0, 28.1)), ('N_9_25', (29.0, 29.1)), ('N_10_25', (30.0, 30.1)), ('N_11_25', (31.0, 31.1)), ('N_12_25', (32.0, 32.1)), ('N_12_26', (33.0, 33.1)), ('N_13_26', (34.0, 34.1)), ('N_13_27', (35.0, 35.1)), ('N_14_27', (36.0, 36.1)), ('N_15_27', (37.0, 37.1)), ('N_16_27', (38.0, 38.1)), ('N_17_27', (39.0, 39.1)), ('N_18_27', (40.0, 40.1)), ('N_19_27', (41.0, 41.1)), ('N_20_27', (42.0, 42.1)), ('N_21_27', (43.0, 43.1)), ('N_21_28', (44.0, 44.1)), ('N_22_28', (45.0, 45.1)), ('N_23_28', (46.0, 46.1)), ('N_24_28', (47.0, 47.1)), ('N_25_28', (48.0, numpy.inf))]]
    p = [('N_4_6', (0, 0.1)), ('N_4_7', (1.2649110640673518, 1.3649110640673519)), ('N_12_7', (2.5452619142656276, 2.6452619142656277)), ('N_13_7', (2.642879610605931, 2.742879610605931)), ('N_14_7', (2.740497306946234, 2.8404973069462343)), ('N_15_7', (2.8381150032865374, 2.9381150032865375)), ('N_15_8', (2.9357326996268407, 3.035732699626841)), ('N_15_9', (3.033350395967144, 3.133350395967144)), ('N_15_10', (3.130968092307447, 3.2309680923074473)), ('N_15_11', (3.2285857886477505, 3.3285857886477506)), ('N_15_12', (3.3262034849880537, 3.426203484988054)), ('N_15_13', (3.423821181328357, 3.523821181328357)), ('N_15_14', (3.5214388776686603, 3.6214388776686603)), ('N_15_15', (3.6190565740089635, 3.7190565740089636)), ('N_15_16', (3.716674270349267, 3.816674270349267)), ('N_15_17', (3.81429196668957, 3.91429196668957)), ('N_15_18', (3.9119096630298733, 4.011909663029873)), ('N_15_19', (4.009527359370177, 4.109527359370176)), ('N_15_20', (4.10714505571048, 4.2071450557104795)), ('N_16_20', (4.204762752050783, 4.304762752050783)), ('N_16_21', (4.302380448391086, 4.402380448391086)), ('N_25_21', (5.05919019880913, 5.15919019880913)), ('N_26_21', (5.156807895149433, 5.256807895149433)), ('N_26_22', (5.254425591489737, 5.354425591489736)), ('N_26_23', (5.35204328783004, 5.4520432878300396)), ('N_26_24', (5.449660984170343, 5.549660984170343)), ('N_26_25', (5.547278680510646, 5.647278680510646)), ('N_26_26', (5.64489637685095, 5.744896376850949)), ('N_26_27', (7.25734792651095, numpy.inf))]
    p2 = [('N_4_6', (0, 0.1)), ('N_4_7', (2.0, 2.1)), ('N_4_8', (3.0, 3.1)), ('N_12_8', (5.82842712474619, 5.9284271247461895)), ('N_13_8', (6.82842712474619, 6.9284271247461895)), ('N_14_8', (7.82842712474619, 7.9284271247461895)), ('N_15_8', (8.82842712474619, 8.92842712474619)), ('N_16_8', (9.82842712474619, 9.92842712474619)), ('N_25_8', (12.82842712474619, 12.92842712474619)), ('N_26_8', (14.67610698216252, 14.776106982162519)), ('N_26_9', (15.67610698216252, 15.776106982162519)), ('N_26_10', (15.776106982162519, 15.876106982162518)), ('N_26_11', (15.876106982162518, 15.976106982162518)), ('N_26_12', (15.976106982162518, 16.076106982162518)), ('N_26_13', (16.076106982162518, 16.17610698216252)), ('N_26_14', (16.17610698216252, 16.27610698216252)), ('N_26_15', (16.27610698216252, 16.376106982162522)), ('N_26_16', (16.376106982162522, 16.476106982162523)), ('N_26_17', (16.476106982162523, 16.576106982162525)), ('N_26_18', (16.576106982162525, 16.676106982162526)), ('N_26_19', (16.676106982162526, 16.776106982162528)), ('N_26_20', (16.776106982162528, 16.87610698216253)), ('N_26_21', (16.87610698216253, 16.97610698216253)), ('N_26_22', (16.97610698216253, 17.076106982162532)), ('N_26_23', (17.076106982162532, 17.176106982162533)), ('N_26_24', (17.176106982162533, 17.276106982162535)), ('N_26_25', (17.276106982162535, 17.376106982162536)), ('N_26_26', (17.376106982162536, 17.476106982162538)), ('N_26_27', (19.876106982162536, numpy.inf))]
    p3 = [[('N_2_2', (0, 0.1)), ('N_3_2', (2.5, 2.6)), ('N_4_2', (3.5, 3.6)), ('N_5_2', (4.5, 4.6)), ('N_6_2', (5.7, 5.8)), ('N_9_2', (9.100000000000001, 9.200000000000001)), ('N_10_2', (10.3, 10.4)), ('N_11_2', (11.3, 11.4)), ('N_12_2', (12.3, 12.4)), ('N_13_2', (13.3, 13.4)), ('N_14_2', (14.3, 14.4)), ('N_15_2', (15.3, 15.4)), ('N_16_2', (16.3, 16.400000000000002)), ('N_17_2', (17.3, 17.400000000000002)), ('N_18_2', (18.3, 18.400000000000002)), ('N_19_2', (19.5, 19.6)), ('N_19_1', (20.7, 20.8)), ('N_19_0', (21.9, 22.0)), ('N_22_0', (26.15, numpy.inf))], [('N_15_5', (0, 0.1)), ('N_14_5', (2.5, 2.6)), ('N_13_5', (3.7, 3.8000000000000003)), ('N_13_4', (4.9, 5.0)), ('N_13_3', (5.9, 6.0)), ('N_13_2', (7.1000000000000005, 7.2)), ('N_12_2', (8.3, 8.4)), ('N_11_2', (9.3, 9.4)), ('N_10_2', (10.3, 10.4)), ('N_9_2', (11.5, 11.6)), ('N_6_2', (14.9, 15.0)), ('N_5_2', (16.1, 16.200000000000003)), ('N_4_2', (17.1, 17.200000000000003)), ('N_3_2', (18.1, 18.200000000000003)), ('N_2_2', (19.1, 19.200000000000003)), ('N_1_2', (20.3, 20.400000000000002)), ('N_1_3', (22.8, numpy.inf))], [('N_1_29', (0, 0.1)), ('N_1_28', (2.5, 2.6)), ('N_1_27', (3.5, 3.6)), ('N_1_26', (4.5, 4.6)), ('N_1_25', (5.5, 5.6)), ('N_1_24', (6.5, 6.6)), ('N_1_23', (7.5, 7.6)), ('N_1_22', (8.5, 8.6)), ('N_1_21', (9.5, 9.6)), ('N_1_20', (10.5, 10.6)), ('N_1_19', (11.5, 11.6)), ('N_1_18', (12.5, 12.6)), ('N_1_17', (13.5, 13.6)), ('N_1_16', (14.5, 14.6)), ('N_1_15', (15.5, 15.6)), ('N_1_14', (16.5, 16.6)), ('N_1_13', (17.5, 17.6)), ('N_1_12', (18.5, 18.6)), ('N_1_11', (19.5, 19.6)), ('N_1_10', (20.5, 20.6)), ('N_1_9', (21.5, 21.6)), ('N_1_8', (22.5, 22.6)), ('N_1_7', (23.5, 23.6)), ('N_1_6', (24.5, 24.6)), ('N_1_5', (25.5, 25.6)), ('N_1_4', (26.5, 26.6)), ('N_1_3', (27.5, 27.6)), ('N_1_2', (28.5, 28.6)), ('N_1_1', (29.5, 29.6)), ('N_1_0', (30.7, 30.8)), ('N_2_0', (31.9, 32.0)), ('N_3_0', (32.9, 33.0)), ('N_4_0', (33.9, 34.0)), ('N_5_0', (34.9, 35.0)), ('N_6_0', (36.1, 36.2)), ('N_9_0', (39.5, 39.6)), ('N_10_0', (40.7, 40.800000000000004)), ('N_11_0', (41.7, 41.800000000000004)), ('N_12_0', (42.7, 42.800000000000004)), ('N_13_0', (43.7, 43.800000000000004)), ('N_14_0', (44.7, 44.800000000000004)), ('N_15_0', (45.7, 45.800000000000004)), ('N_16_0', (46.7, 46.800000000000004)), ('N_17_0', (47.7, 47.800000000000004)), ('N_18_0', (48.7, 48.800000000000004)), ('N_19_0', (49.900000000000006, 50.00000000000001)), ('N_22_0', (53.300000000000004, 53.400000000000006)), ('N_23_0', (54.50000000000001, 54.60000000000001)), ('N_24_0', (55.50000000000001, 55.60000000000001)), ('N_25_0', (56.50000000000001, 56.60000000000001)), ('N_26_0', (57.50000000000001, 57.60000000000001)), ('N_27_0', (58.50000000000001, 58.60000000000001)), ('N_28_0', (59.50000000000001, 59.60000000000001)), ('N_29_0', (62.00000000000001, numpy.inf))], [('N_3_6', (0, 0.1)), ('N_2_6', (2.5, 2.6)), ('N_1_6', (3.5, 3.6)), ('N_0_6', (4.7, 4.8)), ('N_0_7', (5.9, 6.0)), ('N_0_8', (8.4, numpy.inf))], [('N_2_24', (0, 0.1)), ('N_2_23', (2.5, 2.6)), ('N_2_22', (3.5, 3.6)), ('N_2_21', (4.7, 4.8)), ('N_3_21', (5.9, 6.0)), ('N_4_21', (7.1000000000000005, 7.2)), ('N_12_21', (15.5, 15.6)), ('N_13_21', (16.7, 16.8)), ('N_14_21', (17.7, 17.8)), ('N_15_21', (18.7, 18.8)), ('N_16_21', (19.9, 20.0)), ('N_25_21', (29.299999999999997, 29.4)), ('N_26_21', (30.499999999999996, 30.599999999999998)), ('N_27_21', (33.0, numpy.inf))], [('N_16_1', (0, 0.1)), ('N_17_1', (2.5, 2.6)), ('N_18_1', (3.5, 3.6)), ('N_19_1', (4.7, 4.8)), ('N_22_1', (8.100000000000001, 8.200000000000001)), ('N_23_1', (9.3, 9.4)), ('N_24_1', (10.3, 10.4)), ('N_25_1', (11.3, 11.4)), ('N_26_1', (12.5, 12.6)), ('N_26_2', (13.7, 13.799999999999999)), ('N_26_3', (14.7, 14.799999999999999)), ('N_26_4', (15.7, 15.799999999999999)), ('N_26_5', (16.7, 16.8)), ('N_26_6', (17.7, 17.8)), ('N_26_7', (18.7, 18.8)), ('N_26_8', (21.2, numpy.inf))], [('N_2_25', (0, 0.1)), ('N_2_26', (2.5, 2.6)), ('N_2_27', (3.7, 3.8000000000000003)), ('N_3_27', (4.9, 5.0)), ('N_4_27', (5.9, 6.0)), ('N_5_27', (6.9, 7.0)), ('N_6_27', (8.100000000000001, 8.200000000000001)), ('N_9_27', (11.500000000000002, 11.600000000000001)), ('N_10_27', (12.700000000000003, 12.800000000000002)), ('N_11_27', (15.200000000000003, numpy.inf))], [('N_25_23', (0, 0.1)), ('N_25_22', (2.5, 2.6)), ('N_25_21', (3.5, 3.6)), ('N_25_20', (4.7, 4.8)), ('N_26_20', (5.9, 6.0)), ('N_27_20', (6.9, 7.0)), ('N_28_20', (8.100000000000001, 8.200000000000001)), ('N_28_19', (9.3, 9.4)), ('N_28_18', (10.3, 10.4)), ('N_28_17', (11.3, 11.4)), ('N_28_16', (12.3, 12.4)), ('N_28_15', (13.3, 13.4)), ('N_28_14', (14.5, 14.6)), ('N_29_14', (17.0, numpy.inf))], [('N_1_13', (0, 0.1)), ('N_1_12', (2.5, 2.6)), ('N_1_11', (3.5, 3.6)), ('N_1_10', (4.5, 4.6)), ('N_1_9', (5.5, 5.6)), ('N_1_8', (6.5, 6.6)), ('N_1_7', (7.5, 7.6)), ('N_1_6', (8.5, 8.6)), ('N_1_5', (9.5, 9.6)), ('N_1_4', (10.5, 10.6)), ('N_1_3', (11.5, 11.6)), ('N_1_2', (12.5, 12.6)), ('N_1_1', (13.7, 13.799999999999999)), ('N_2_1', (16.2, numpy.inf))], [('N_25_29', (0, 0.1)), ('N_25_28', (2.5, 2.6)), ('N_25_27', (3.7, 3.8000000000000003)), ('N_24_27', (4.9, 5.0)), ('N_23_27', (5.9, 6.0)), ('N_22_27', (7.1000000000000005, 7.2)), ('N_19_27', (10.5, 10.6)), ('N_18_27', (11.7, 11.799999999999999)), ('N_17_27', (12.7, 12.799999999999999)), ('N_16_27', (13.7, 13.799999999999999)), ('N_15_27', (14.7, 14.799999999999999)), ('N_14_27', (15.7, 15.799999999999999)), ('N_13_27', (16.9, 17.0)), ('N_13_26', (18.099999999999998, 18.2)), ('N_13_25', (19.099999999999998, 19.2)), ('N_13_24', (20.099999999999998, 20.2)), ('N_13_23', (21.099999999999998, 21.2)), ('N_13_22', (22.099999999999998, 22.2)), ('N_13_21', (23.099999999999998, 23.2)), ('N_13_20', (24.099999999999998, 24.2)), ('N_13_19', (25.099999999999998, 25.2)), ('N_13_18', (26.099999999999998, 26.2)), ('N_13_17', (27.099999999999998, 27.2)), ('N_13_16', (28.099999999999998, 28.2)), ('N_13_15', (29.099999999999998, 29.2)), ('N_13_14', (30.099999999999998, 30.2)), ('N_13_13', (31.099999999999998, 31.2)), ('N_13_12', (32.099999999999994, 32.199999999999996)), ('N_13_11', (33.099999999999994, 33.199999999999996)), ('N_13_10', (34.099999999999994, 34.199999999999996)), ('N_13_9', (35.099999999999994, 35.199999999999996)), ('N_13_8', (36.099999999999994, 36.199999999999996)), ('N_13_7', (37.099999999999994, 37.199999999999996)), ('N_13_6', (38.099999999999994, 38.199999999999996)), ('N_13_5', (39.099999999999994, 39.199999999999996)), ('N_13_4', (40.099999999999994, 40.199999999999996)), ('N_13_3', (41.099999999999994, 41.199999999999996)), ('N_13_2', (42.3, 42.4)), ('N_12_2', (43.5, 43.6)), ('N_11_2', (44.5, 44.6)), ('N_10_2', (45.5, 45.6)), ('N_9_2', (46.7, 46.800000000000004)), ('N_6_2', (50.1, 50.2)), ('N_5_2', (52.6, numpy.inf))], [('N_9_2', (0, 0.1)), ('N_10_2', (2.5, 2.6)), ('N_11_2', (3.5, 3.6)), ('N_12_2', (4.5, 4.6)), ('N_13_2', (5.5, 5.6)), ('N_14_2', (6.5, 6.6)), ('N_15_2', (7.5, 7.6)), ('N_16_2', (8.5, 8.6)), ('N_17_2', (9.5, 9.6)), ('N_18_2', (10.5, 10.6)), ('N_19_2', (11.7, 11.799999999999999)), ('N_22_2', (15.1, 15.2)), ('N_23_2', (16.3, 16.400000000000002)), ('N_24_2', (17.3, 17.400000000000002)), ('N_25_2', (18.3, 18.400000000000002)), ('N_26_2', (19.3, 19.400000000000002)), ('N_27_2', (20.5, 20.6)), ('N_27_3', (21.7, 21.8)), ('N_27_4', (22.7, 22.8)), ('N_27_5', (23.7, 23.8)), ('N_27_6', (24.7, 24.8)), ('N_27_7', (25.7, 25.8)), ('N_27_8', (26.7, 26.8)), ('N_27_9', (27.7, 27.8)), ('N_27_10', (28.7, 28.8)), ('N_27_11', (29.7, 29.8)), ('N_27_12', (30.7, 30.8)), ('N_27_13', (31.7, 31.8)), ('N_27_14', (32.7, 32.800000000000004)), ('N_27_15', (33.7, 33.800000000000004)), ('N_27_16', (34.7, 34.800000000000004)), ('N_27_17', (37.2, numpy.inf))], [('N_29_21', (0, 0.1)), ('N_28_21', (2.5, 2.6)), ('N_27_21', (3.5, 3.6)), ('N_26_21', (4.5, 4.6)), ('N_25_21', (5.7, 5.8)), ('N_16_21', (15.099999999999998, 15.199999999999998)), ('N_15_21', (16.299999999999997, 16.4)), ('N_14_21', (17.299999999999997, 17.4)), ('N_13_21', (18.299999999999997, 18.4)), ('N_12_21', (19.499999999999996, 19.599999999999998)), ('N_4_21', (27.9, 28.0)), ('N_3_21', (29.099999999999998, 29.2)), ('N_2_21', (30.099999999999998, 30.2)), ('N_1_21', (31.099999999999998, 31.2)), ('N_0_21', (32.3, 32.4)), ('N_0_20', (33.5, 33.6)), ('N_0_19', (34.5, 34.6)), ('N_0_18', (35.5, 35.6)), ('N_0_17', (36.5, 36.6)), ('N_0_16', (37.5, 37.6)), ('N_0_15', (38.5, 38.6)), ('N_0_14', (39.5, 39.6)), ('N_0_13', (40.5, 40.6)), ('N_0_12', (41.5, 41.6)), ('N_0_11', (44.0, numpy.inf))], [('N_14_10', (0, 0.1)), ('N_14_9', (2.5, 2.6)), ('N_14_8', (3.5, 3.6)), ('N_14_7', (4.5, 4.6)), ('N_14_6', (5.7, 5.8)), ('N_13_6', (6.9, 7.0)), ('N_12_6', (7.9, 8.0)), ('N_11_6', (8.9, 9.0)), ('N_10_6', (11.4, numpy.inf))], [('N_29_5', (0, 0.1)), ('N_29_6', (2.5, 2.6)), ('N_29_7', (3.5, 3.6)), ('N_29_8', (4.5, 4.6)), ('N_29_9', (5.5, 5.6)), ('N_29_10', (6.5, 6.6)), ('N_29_11', (7.5, 7.6)), ('N_29_12', (8.5, 8.6)), ('N_29_13', (9.5, 9.6)), ('N_29_14', (10.5, 10.6)), ('N_29_15', (11.5, 11.6)), ('N_29_16', (12.5, 12.6)), ('N_29_17', (13.5, 13.6)), ('N_29_18', (14.5, 14.6)), ('N_29_19', (15.5, 15.6)), ('N_29_20', (16.5, 16.6)), ('N_29_21', (17.5, 17.6)), ('N_29_22', (18.7, 18.8)), ('N_28_22', (19.9, 20.0)), ('N_27_22', (20.9, 21.0)), ('N_26_22', (21.9, 22.0)), ('N_25_22', (23.099999999999998, 23.2)), ('N_16_22', (32.5, 32.6)), ('N_15_22', (33.7, 33.800000000000004)), ('N_14_22', (34.900000000000006, 35.00000000000001)), ('N_14_23', (36.10000000000001, 36.20000000000001)), ('N_14_24', (37.10000000000001, 37.20000000000001)), ('N_14_25', (39.60000000000001, numpy.inf))], [('N_29_18', (0, 0.1)), ('N_29_17', (2.5, 2.6)), ('N_29_16', (3.5, 3.6)), ('N_29_15', (4.5, 4.6)), ('N_29_14', (5.5, 5.6)), ('N_29_13', (6.7, 6.8)), ('N_28_13', (7.9, 8.0)), ('N_27_13', (8.9, 9.0)), ('N_26_13', (9.9, 10.0)), ('N_25_13', (12.4, numpy.inf))], [('N_14_17', (0, 0.1)), ('N_14_16', (2.5, 2.6)), ('N_14_15', (3.5, 3.6)), ('N_14_14', (4.5, 4.6)), ('N_14_13', (5.5, 5.6)), ('N_14_12', (6.5, 6.6)), ('N_14_11', (7.5, 7.6)), ('N_14_10', (8.5, 8.6)), ('N_14_9', (9.7, 9.799999999999999)), ('N_13_9', (10.899999999999999, 10.999999999999998)), ('N_12_9', (11.899999999999999, 11.999999999999998)), ('N_11_9', (12.899999999999999, 12.999999999999998)), ('N_10_9', (13.899999999999999, 13.999999999999998)), ('N_9_9', (16.4, numpy.inf))], [('N_6_16', (0, 0.1)), ('N_9_16', (4.45, 4.55)), ('N_10_16', (5.65, 5.75)), ('N_11_16', (6.65, 6.75)), ('N_12_16', (7.65, 7.75)), ('N_13_16', (8.65, 8.75)), ('N_14_16', (9.850000000000001, 9.950000000000001)), ('N_14_17', (11.05, 11.15)), ('N_14_18', (12.05, 12.15)), ('N_14_19', (13.05, 13.15)), ('N_14_20', (14.05, 14.15)), ('N_14_21', (15.05, 15.15)), ('N_14_22', (16.05, 16.150000000000002)), ('N_14_23', (17.05, 17.150000000000002)), ('N_14_24', (18.05, 18.150000000000002)), ('N_14_25', (19.05, 19.150000000000002)), ('N_14_26', (20.05, 20.150000000000002)), ('N_14_27', (22.55, numpy.inf))], [('N_3_5', (0, 0.1)), ('N_3_6', (2.5, 2.6)), ('N_3_7', (3.5, 3.6)), ('N_3_8', (4.5, 4.6)), ('N_3_9', (5.5, 5.6)), ('N_3_10', (6.5, 6.6)), ('N_3_11', (7.5, 7.6)), ('N_3_12', (8.5, 8.6)), ('N_3_13', (9.5, 9.6)), ('N_3_14', (10.5, 10.6)), ('N_3_15', (11.7, 11.799999999999999)), ('N_4_15', (14.2, numpy.inf))], [('N_29_27', (0, 0.1)), ('N_29_26', (2.5, 2.6)), ('N_29_25', (3.5, 3.6)), ('N_29_24', (4.5, 4.6)), ('N_29_23', (5.5, 5.6)), ('N_29_22', (6.5, 6.6)), ('N_29_21', (7.5, 7.6)), ('N_29_20', (8.5, 8.6)), ('N_29_19', (9.5, 9.6)), ('N_29_18', (10.5, 10.6)), ('N_29_17', (11.5, 11.6)), ('N_29_16', (12.5, 12.6)), ('N_29_15', (13.5, 13.6)), ('N_29_14', (14.5, 14.6)), ('N_29_13', (15.5, 15.6)), ('N_29_12', (16.5, 16.6)), ('N_29_11', (17.5, 17.6)), ('N_29_10', (18.5, 18.6)), ('N_29_9', (19.5, 19.6)), ('N_29_8', (20.5, 20.6)), ('N_29_7', (21.5, 21.6)), ('N_29_6', (22.5, 22.6)), ('N_29_5', (23.5, 23.6)), ('N_29_4', (24.5, 24.6)), ('N_29_3', (25.5, 25.6)), ('N_29_2', (26.5, 26.6)), ('N_29_1', (29.0, numpy.inf))], [('N_11_23', (0, 0.1)), ('N_12_23', (2.5, 2.6)), ('N_13_23', (3.7, 3.8000000000000003)), ('N_13_24', (4.9, 5.0)), ('N_13_25', (5.9, 6.0)), ('N_13_26', (6.9, 7.0)), ('N_13_27', (8.100000000000001, 8.200000000000001)), ('N_12_27', (9.3, 9.4)), ('N_11_27', (10.3, 10.4)), ('N_10_27', (11.3, 11.4)), ('N_9_27', (12.5, 12.6)), ('N_6_27', (16.75, numpy.inf))], [('N_13_11', (0, 0.1)), ('N_13_12', (2.5, 2.6)), ('N_13_13', (3.5, 3.6)), ('N_13_14', (4.5, 4.6)), ('N_13_15', (5.5, 5.6)), ('N_13_16', (6.7, 6.8)), ('N_12_16', (7.9, 8.0)), ('N_11_16', (8.9, 9.0)), ('N_10_16', (9.9, 10.0)), ('N_9_16', (11.100000000000001, 11.200000000000001)), ('N_6_16', (14.500000000000002, 14.600000000000001)), ('N_5_16', (17.0, numpy.inf))], [('N_23_23', (0, 0.1)), ('N_22_23', (3.1097722286464435, 3.2097722286464436)), ('N_19_23', (6.509772228646444, 6.6097722286464435)), ('N_18_23', (7.709772228646444, 7.809772228646444)), ('N_17_23', (8.709772228646443, 8.809772228646443)), ('N_16_23', (9.709772228646443, 9.809772228646443)), ('N_15_23', (10.709772228646443, 10.809772228646443)), ('N_14_23', (11.709772228646443, 11.809772228646443)), ('N_13_23', (12.909772228646442, 13.009772228646442)), ('N_13_22', (14.109772228646442, 14.209772228646441)), ('N_13_21', (15.109772228646442, 15.209772228646441)), ('N_13_20', (16.10977222864644, 16.209772228646443)), ('N_13_19', (17.10977222864644, 17.209772228646443)), ('N_13_18', (18.10977222864644, 18.209772228646443)), ('N_13_17', (19.10977222864644, 19.209772228646443)), ('N_13_16', (20.10977222864644, 20.209772228646443)), ('N_13_15', (21.10977222864644, 21.209772228646443)), ('N_13_14', (22.10977222864644, 22.209772228646443)), ('N_13_13', (23.30977222864644, 23.409772228646442)), ('N_12_13', (24.50977222864644, 24.60977222864644)), ('N_11_13', (25.50977222864644, 25.60977222864644)), ('N_10_13', (26.50977222864644, 26.60977222864644)), ('N_9_13', (27.70977222864644, 27.80977222864644)), ('N_6_13', (31.95977222864644, numpy.inf))], [('N_15_23', (0, 0.1)), ('N_16_23', (2.5, 2.6)), ('N_17_23', (3.5, 3.6)), ('N_18_23', (4.5, 4.6)), ('N_19_23', (5.7, 5.8)), ('N_22_23', (9.100000000000001, 9.200000000000001)), ('N_23_23', (10.3, 10.4)), ('N_24_23', (11.3, 11.4)), ('N_25_23', (12.3, 12.4)), ('N_26_23', (13.5, 13.6)), ('N_26_24', (14.7, 14.799999999999999)), ('N_26_25', (17.2, numpy.inf))], [('N_14_16', (0, 0.1)), ('N_13_16', (2.5, 2.6)), ('N_12_16', (3.7, 3.8000000000000003)), ('N_12_15', (4.9, 5.0)), ('N_12_14', (6.1000000000000005, 6.2)), ('N_4_14', (14.5, 14.6)), ('N_3_14', (17.0, numpy.inf))], [('N_24_0', (0, 0.1)), ('N_24_1', (2.5, 2.6)), ('N_24_2', (3.7, 3.8000000000000003)), ('N_25_2', (4.9, 5.0)), ('N_26_2', (6.1000000000000005, 6.2)), ('N_26_3', (7.300000000000001, 7.4)), ('N_26_4', (8.3, 8.4)), ('N_26_5', (9.3, 9.4)), ('N_26_6', (10.3, 10.4)), ('N_26_7', (11.3, 11.4)), ('N_26_8', (12.3, 12.4)), ('N_26_9', (13.3, 13.4)), ('N_26_10', (14.3, 14.4)), ('N_26_11', (15.3, 15.4)), ('N_26_12', (16.3, 16.400000000000002)), ('N_26_13', (17.3, 17.400000000000002)), ('N_26_14', (18.5, 18.6)), ('N_25_14', (21.0, numpy.inf))]]
    #for i, path in enumerate(p3):
    #    print(f"________ {i} _________")
    #    for el in path:
    #        print(el)
    show_lif(lif_path="data/colldet_tests/small_test_close_diag.json")
