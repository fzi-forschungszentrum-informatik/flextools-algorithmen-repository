import base64
from typing import Optional, List, Dict, Tuple

import networkx as nx

from data.models import Layout
import plotly.graph_objects as go
import plotly.io as pio


import matplotlib
matplotlib.use('TkAgg')
pio.renderers.default = "browser"

PATH_COLORS = [
    "red", "blue", "green", "orange", "purple", "brown", "pink", "olive",
    "cyan", "magenta", "lime", "teal", "indigo", "gold", "coral", "darkblue",
    "darkgreen", "maroon", "navy", "chocolate", "darkviolet", "dodgerblue",
    "crimson", "sienna", "slateblue", "tomato", "mediumseagreen", "firebrick",
    "deepskyblue", "hotpink", "darkturquoise", "orangered"
]


def show_lif_animated(layout: Layout, amr_paths: Optional[List[List[str]]] = None, orders_dict: Dict = dict,
                      img_path: str = None, length: float=0, width: float=0):
    g = show_lif(layout, amr_paths)
    anim_paths = []
    for p in amr_paths or []:
        p_sec = path_to_relative_seconds(p)
        path_with_intervals = []
        last_order_id = None
        for i, (node, start_time, order) in enumerate(p_sec):
            if i < len(p_sec) - 1:
                end_time = p_sec[i+1][1]
            else:
                end_time = float('inf')
            if len(str(order)) > 4:
                if order[:4] == 'RePo':
                    last_order_id = None
                else:
                    last_order_id = order
            elif order != '':
                last_order_id = order
            path_with_intervals.append((node, (start_time, end_time), last_order_id))
        anim_paths.append(path_with_intervals)
    draw_animated_graph(g, anim_paths, orders_dict, img_path, length, width)
    return


def path_to_relative_seconds(path):
    t_0 = path[0][1]
    return [(node, (t_s- t_0).total_seconds(), order_id) for node, t_s, order_id in path]


def show_lif(layout: Layout, amr_paths: Optional[List[List[str]]] = None):
    g = build_graph_lif_object(layout)
    # draw_static_graph(g, amr_paths or [])
    return g


def build_graph_lif_object(lif_object: Layout):
    g = nx.Graph()
    for node in lif_object.nodes:
        pos = node.nodePosition
        g.add_node(node.nodeId, pos=(pos.x, pos.y))
    for edge in lif_object.edges:
        g.add_edge(edge.startNodeId, edge.endNodeId, edgeId=edge.edgeId)
    return g


def draw_static_graph(g: nx.Graph, paths: List[List[str]]):
    pos = nx.get_node_attributes(g, "pos") or nx.spring_layout(g, seed=42)
    traces = [create_edge_trace(g, pos), create_node_trace(g, pos)] + create_path_traces(paths, pos)
    fig = go.Figure(data=traces, layout=go.Layout(
        title="LIF Layout Graph mit AMR-Pfaden + Start/Endpunkte",
        showlegend=True, hovermode='closest',
        margin=dict(t=40, b=20, l=20, r=20),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        width=1000, height=800
    ))
    fig.show()


def create_edge_trace(g, pos):
    edge_x = []
    edge_y = []
    for edge in g.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    return go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='gray'), name='Edges',
                      hoverinfo='none')


def create_node_trace(g, pos):
    node_x = []
    node_y = []
    for node in g.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    return go.Scatter(
        x=node_x, y=node_y, mode='markers',
        text=[str(n) for n in g.nodes()],
        marker=dict(color='lightgray', size=6, line=dict(width=0.5, color='black')),
        hoverinfo='text', name='Nodes'
    )


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
        traces.append(
            go.Scatter(x=x, y=y, mode='lines', line=dict(width=4, color=color), name=f'Path AMR {i}', hoverinfo='none'))
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


def extract_time_steps(paths):
    times = set()
    for path in paths:
        for node, (t0, t1), _ in path:
            times.add(round(t0*1000, 4)/1000)
            times.add(round(t1*1000, 4)/1000-0.1)
    return sorted(times)


def interpolate_pos(pos, start_node, end_node, t0, t1, t):
    """linear interpolation between two node positions for time t"""
    x0, y0 = pos[start_node]
    x1, y1 = pos[end_node]
    frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
    x = x0 + frac * (x1 - x0)
    y = y0 + frac * (y1 - y0)
    return x, y


def draw_animated_graph(G: nx.Graph, paths: List[List[Tuple[str, Tuple[float, float], str]]], orders_dict: Dict,
                        img_path: str, length: float, width: float):
    pos = nx.get_node_attributes(G, "pos") or nx.spring_layout(G, seed=42)
    time_steps = extract_time_steps(paths)

    base_traces = [create_edge_trace(G, pos), create_node_trace(G, pos)]

    init_traces = []
    for i, path in enumerate(paths):
        color = PATH_COLORS[i % len(PATH_COLORS)]
        start_node = path[0][0] if path else None
        if start_node and start_node in pos:
            x, y = pos[start_node]
        else:
            x, y = None, None

        init_traces.append(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(color=color, size=14, symbol='circle'),
            name=f"AMR {i+1}",
            showlegend=True,
            hoverinfo='text',
            text=[f"AMR {i}: {start_node if start_node else ''}"]
        ))

        init_traces.append(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(color=color, size=16, symbol='cross', line=dict(width=2, color='black')),
            name=f"AMR {i+1}: Pickup",
            showlegend=False,
            visible=False
        ))

        init_traces.append(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(color=color, size=16, symbol='square', line=dict(width=2, color='black')),
            name=f"AMR {i+1}: Dropoff",
            showlegend=False,
            visible=False
        ))

    frames = []
    for t in time_steps:
        frame_data = base_traces.copy()

        current_order_ids = []
        for i, path in enumerate(paths):
            color = PATH_COLORS[i % len(PATH_COLORS)]
            current_pos = None
            current_node_id = None
            current_order_id = None
            for j in range(len(path)):
                node, (t0, t1), order_id = path[j]
                if t0 <= t < t1:
                    current_pos = pos[node]
                    current_node_id = node
                    current_order_id = order_id
                    break

                if j < len(path) - 1:
                    next_node, (nt0, nt1), _ = path[j+1]
                    if t1 <= t < nt0:
                        current_pos = interpolate_pos(pos, node, next_node, t1, nt0, t)
                        current_node_id = f"{node}->{next_node}"
                        break

            if current_order_id and current_order_id in orders_dict:
                show_legend = False
            else:
                show_legend = True
            if current_pos:
                x, y = current_pos
            else:
                x, y = None, None
                show_legend = False

            frame_data.append(dict(x=[x], y=[y], showlegend=show_legend))

            if current_order_id and current_order_id in orders_dict:
                pickup_name = f"AMR {i+1}: Pickup Order {current_order_id}"
                dropoff_name = f"AMR {i+1}: Dropoff Order {current_order_id}"
                px, py = pos[orders_dict[current_order_id]['pickup']]
                dx, dy = pos[orders_dict[current_order_id]['dropoff']]
                show_legend = True
                visible = True
            else:
                pickup_name = f"AMR {i+1}: Pickup"
                dropoff_name = f"AMR {i+1}: Dropoff"
                px, py = None, None
                dx, dy = None, None
                show_legend = False
                visible = False

            frame_data.append(dict(x=[px], y=[py], name=pickup_name, showlegend=show_legend, visible=visible))
            frame_data.append(dict(x=[dx], y=[dy], name=dropoff_name, showlegend=show_legend, visible=visible))

        frames.append(go.Frame(data=frame_data, name=str(t)))

    # create slider steps
    first_frame = str(time_steps[0])
    slider_steps = []
    for t in time_steps:
        slider_steps.append(dict(
            method='animate',
            args=[[str(t)], dict(mode='immediate', frame=dict(duration=0, redraw=True), transition=dict(duration=0))],
            label=f"{t:.1f}"
        ))

    fig = go.Figure(
        data=base_traces + init_traces,
        layout=go.Layout(
            showlegend=True, hovermode='closest',
            width=1400, height=1200,
            xaxis=dict(range=[0, length] if length else None, visible=False, fixedrange=True),
            yaxis=dict(range=[0, width] if width else None, visible=False, fixedrange=True, scaleanchor="x",
                       autorange="reversed"),
            margin=dict(t=200, b=40, l=40, r=40),

            legend=dict(
                x=1.02,
                y=0.05,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='black',
                borderwidth=1
            ),

            updatemenus=[
                dict(
                    type='buttons', showactive=False, direction = "right",
                    x=0, y=1.15, xanchor='left', yanchor='bottom', #1.15
                    buttons=[
                        dict(label='Play', method='animate',
                             args=[None,
                                   dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode='immediate')]),
                        dict(label='Pause', method='animate',
                             args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')]),
                        dict(label='Reset', method='animate',
                             args=[[first_frame], dict(frame=dict(duration=0, redraw=False), mode='immediate')]),
                    ]
                )
            ],

            sliders=[dict(
                active=0,
                currentvalue={"prefix": "Schritt: "},
                pad={"b": 10, "t": 20},
                steps=slider_steps,
                x=0, len=1,
                y=1.05, yanchor='bottom'
            )]
        ),
        frames=frames
    )
    if img_path is not None:

        fig = add_background_image(
            fig,
            img_path=img_path,
            length=length,
            width=width,
            opacity=1.0
        )

    fig.show()
    return


def get_amr_state(path, t, pos):
    for j, (node, (t0, t1), order_id) in enumerate(path):
        if t0 <= t < t1:
            return pos[node], node, order_id
        if j < len(path) - 1:
            next_node, (nt0, _), _ = path[j + 1]
            if t1 <= t < nt0:
                return interpolate_pos(pos, node, next_node, t1, nt0, t), f"{node}->{next_node}", None
    return None, None, None


def draw_animated_graph_(G: nx.Graph, paths: List[List[Tuple[str, Tuple[float, float], str]]], orders_dict: Dict,
                         img_path: str, length: float, width: float):
    pos = nx.get_node_attributes(G, "pos") or nx.spring_layout(G, seed=42)
    time_steps = extract_time_steps(paths)

    base_traces = [create_edge_trace(G, pos), create_node_trace(G, pos)]

    amr_traces = []
    pickup_traces = []
    dropoff_traces = []

    for i, path in enumerate(paths):
        color = PATH_COLORS[i % len(PATH_COLORS)]

        amr_traces.append(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=14, color=color),
            name=f"AMR {i}",
            showlegend=True
        ))

        pickup_traces.append(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(symbol="cross", size=16, color=color),
            name=f"AMR {i}: Pickup",
            visible=False,
            showlegend=True
        ))

        dropoff_traces.append(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(symbol="square", size=16, color=color),
            name=f"AMR {i}: Dropoff",
            visible=False,
            showlegend=True
        ))

    frames = []

    for t in time_steps:
        frame_updates = []

        for i, path in enumerate(paths):
            pos_xy, node_id, order_id = get_amr_state(path, t, pos)

            # AMR
            if pos_xy:
                frame_updates.append(dict(
                    x=[pos_xy[0]], y=[pos_xy[1]],
                    text=[f"AMR {i}: {node_id} [{t:.1f}]"]
                ))
            else:
                frame_updates.append(dict(x=[None], y=[None]))

            # Pickup / Dropoff
            if order_id and order_id in orders_dict:
                p = orders_dict[order_id]["pickup"]
                d = orders_dict[order_id]["dropoff"]

                frame_updates.append(dict(
                    x=[pos[p][0]], y=[pos[p][1]],
                    visible=True,
                    name=f"AMR {i}: Pickup (Order {order_id})"
                ))
                frame_updates.append(dict(
                    x=[pos[d][0]], y=[pos[d][1]],
                    visible=True,
                    name=f"AMR {i}: Dropoff (Order {order_id})"
                ))
            else:
                frame_updates.append(dict(visible=False))
                frame_updates.append(dict(visible=False))

        frames.append(go.Frame(data=frame_updates, name=str(t)))

    fig = go.Figure(
        data=base_traces + amr_traces + pickup_traces + dropoff_traces,
        layout=go.Layout(
            showlegend=True,
            hovermode="closest",
            width=1000,
            height=800,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            updatemenus=[dict(
                type="buttons",
                buttons=[dict(
                    label="Play",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=50, redraw=False),
                        transition=dict(duration=50, easing="linear"),
                        fromcurrent=True
                    )]
                )]
            )],
            sliders=[dict(
                steps=[dict(
                    method="animate",
                    args=[[str(t)], dict(frame=dict(duration=0, redraw=False))],
                    label=f"{t:.1f}"
                ) for t in time_steps]
            )]
        ),
        frames=frames
    )
    if img_path is not None:
        fig = add_background_image(
            fig,
            img_path=img_path,
            length=length,
            width=width,
            opacity=1.0
        )
        fig.update_xaxes(range=[0, length+1], fixedrange=True)
        fig.update_yaxes(range=[0, width+1], fixedrange=True)

    fig.show()


def add_background_image(fig, img_path, length, width, opacity=0.8):
    fig.update_layout(
        images=[dict(
            source=img_to_base64(img_path),
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=length,
            sizey=width,
            sizing="stretch",
            layer="below",
            opacity=opacity
        )]
    )
    fig.add_shape(
        type="rect",
        xref="x",
        yref="y",
        x0=0,
        y0=0,
        x1=length,
        y1=width,
        line=dict(
            color="black",
            width=3
        ),
        layer="above"
    )
    return fig


def img_to_base64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

