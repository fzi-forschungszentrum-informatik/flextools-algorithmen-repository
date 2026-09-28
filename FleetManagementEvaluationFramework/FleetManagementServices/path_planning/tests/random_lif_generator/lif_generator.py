import json
import logging
import random
from collections import defaultdict
from typing import List, Tuple, Dict
import networkx as nx
import numpy as np
import config.config_file

from api.server_api_models import LIFObject
from tests.random_lif_generator.lif_generation_config import (GRID_HEIGHT, GRID_WIDTH, SPACING, GRID_TYPE, \
    ROTATION_ALLOWED, MAX_SPEED, REMOVE_NODE_PROBABILITY, RECONNECT_DIAGONAL_PROBABILITY, TEST_PP_LAYOUT_ID, \
    PATH_PAIRS_FILE, NUMBER_OF_PATHS, SHOW_LIF, RECONNECT_PROBABILITY, MAP_ID_DEFAULT, LIF_PATH)
from data.models import NodePosition, Node, Edge, Layout
from tests.random_lif_generator.lif_show import show_lif

logger = logging.getLogger(config.config_file.LOGGER_NAME)

# -------------------------------
# HELPERS
# -------------------------------

def node_id(x: int, y: int) -> str:
    return f"N_{x}_{y}"


def edge_id(x1: int, y1: int, x2: int, y2: int) -> str:
    return f"E-{x1}_{y1}-{x2}_{y2}"


# -------------------------------
# GENERATION LOGIC
# -------------------------------

# ---- STEP 1: Create full node and edge grid ----
def create_full_grid(map_id: str) -> Tuple[Dict[str, Node], List[Edge]]:
    nodes = {}
    edges = []
    sequence_id = 0
    edge_sequence = 0

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            nid = node_id(x, y)
            position = NodePosition(x=x * SPACING, y=y * SPACING, theta=0.0, mapId=map_id)
            node = Node(nodeId=nid, sequenceId=sequence_id, released=True,
                        nodeDescription=None, nodePosition=position, actions=[])
            nodes[nid] = node
            sequence_id += 1

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            current_id = node_id(x, y)
            if current_id not in nodes:
                continue

            # Right
            if x < GRID_WIDTH - 1:
                right_id = node_id(x + 1, y)
                if right_id in nodes:
                    edges.append(create_edge(current_id, right_id, edge_sequence))
                    edge_sequence += 1

            # Down
            if y < GRID_HEIGHT - 1:
                down_id = node_id(x, y + 1)
                if down_id in nodes:
                    edges.append(create_edge(current_id, down_id, edge_sequence))
                    edge_sequence += 1

            # Optional: Diagonal for triangular grid
            if GRID_TYPE == "triangular":
                diag_id = None
                if y % 2 == 0 and x < GRID_WIDTH - 1:
                    diag_id = node_id(x + 1, y + 1)
                elif y % 2 != 0 and x > 0:
                    diag_id = node_id(x - 1, y + 1)

                if diag_id and diag_id in nodes:
                    edges.append(create_edge(current_id, diag_id, edge_sequence))
                    edge_sequence += 1

    return nodes, edges


# ---- Helper to create an edge ----
def create_edge(start_id: str, end_id: str, sequence_id: int) -> Edge:
    x1, y1 = map(int, start_id.split("_")[1:])
    x2, y2 = map(int, end_id.split("_")[1:])
    return Edge(
        edgeId=edge_id(x1, y1, x2, y2),
        sequenceId=sequence_id,
        released=True,
        edgeDescription=None,
        startNodeId=start_id,
        endNodeId=end_id,
        maxSpeed=MAX_SPEED,
        length = SPACING,
        rotationAllowed=ROTATION_ALLOWED,
        actions=[]
    )


# ---- STEP 2: Randomly remove nodes (and associated edges) ----
def remove_and_reconnect_nodes(
    nodes: Dict[str, Node],
    edges: List[Edge],
    map_id: str
) -> Tuple[Dict[str, Node], List[Edge]]:

    pos_map = {n.nodeId: (n.nodePosition.x, n.nodePosition.y) for n in nodes.values()}
    grid_map = {
        (int(n.nodePosition.x / SPACING), int(n.nodePosition.y / SPACING)): n.nodeId
        for n in nodes.values()
    }

    # Search edge
    edge_lookup = defaultdict(list)
    for e in edges:
        edge_lookup[e.startNodeId].append((e.endNodeId, e))
        edge_lookup[e.endNodeId].append((e.startNodeId, e))

    new_edges = []
    new_nodes = dict(nodes)
    removed_nodes = []

    edge_seq = len(edges)

    for node_id, node in list(nodes.items()):
        if random.random() >= REMOVE_NODE_PROBABILITY:
            continue

        if RECONNECT_PROBABILITY <= 0:
            removed_nodes.append(node_id)
            del new_nodes[node_id]
            continue

        x = int(node.nodePosition.x / SPACING)
        y = int(node.nodePosition.y / SPACING)

        neighbor_pairs = [
            ((x - 1, y), (x + 1, y)),
            ((x, y - 1), (x, y + 1)),
        ]

        if RECONNECT_DIAGONAL_PROBABILITY >= 0:
            if y % 2 == 0:
                neighbor_pairs.append(((x - 1, y - 1), (x + 1, y + 1)))
            else:
                neighbor_pairs.append(((x - 1, y + 1), (x + 1, y - 1)))

        for (pos1, pos2) in neighbor_pairs:
            n1 = grid_map.get(pos1)
            n2 = grid_map.get(pos2)

            if n1 in new_nodes and n2 in new_nodes and node_id in edge_lookup:
                if n1 not in removed_nodes and n2 not in removed_nodes:
                    len1 = next((e.length or 1.0 for nbr, e in edge_lookup[node_id] if nbr == n1), 1.0)
                    len2 = next((e.length or 1.0 for nbr, e in edge_lookup[node_id] if nbr == n2), 1.0)
                    total_length = len1 + len2

                    new_edge = Edge(
                        edgeId=f"{node_id}_reconnect_{edge_seq}",
                        sequenceId=edge_seq,
                        released=True,
                        edgeDescription=f"Reconnected via {node_id}",
                        startNodeId=n1,
                        endNodeId=n2,
                        maxSpeed=MAX_SPEED,
                        rotationAllowed=ROTATION_ALLOWED,
                        length=total_length,
                        actions=[]
                    )
                    new_edges.append(new_edge)
                    edge_seq += 1

        # Remove nodes and edges
        removed_nodes.append(node_id)
        del new_nodes[node_id]

    # Remove edges after removing nodes
    filtered_edges = [
        e for e in edges if e.startNodeId not in removed_nodes and e.endNodeId not in removed_nodes
    ]
    filtered_edges.extend(new_edges)

    valid_node_ids = set(new_nodes.keys())
    filtered_edges = [
        e for e in filtered_edges
        if e.startNodeId in valid_node_ids and e.endNodeId in valid_node_ids
    ]

    return new_nodes, filtered_edges

# ---- STEP 4: Filter to largest connected component ----
def filter_largest_connected(nodes: Dict[str, Node], edges: List[Edge]) -> Tuple[List[Node], List[Edge]]:
    G = nx.Graph()
    for n in nodes.values():
        G.add_node(n.nodeId)
    for e in edges:
        G.add_edge(e.startNodeId, e.endNodeId)

    components = list(nx.connected_components(G))

    if not components:
        return [], []

    largest = max(components, key=len)
    filtered_nodes = [nodes[node_id] for node_id in largest if node_id in nodes]
    valid_ids = set(n.nodeId for n in filtered_nodes)
    filtered_edges = [e for e in edges if e.startNodeId in valid_ids and e.endNodeId in valid_ids]
    return filtered_nodes, filtered_edges


def edit_graph_gui(nodes, edges):
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from scipy.spatial import KDTree
    import math

    G = nx.Graph()
    pos = {}
    for n in nodes.values():
        G.add_node(n.nodeId)
        pos[n.nodeId] = (n.nodePosition.x, n.nodePosition.y)
    for e in edges:
        G.add_edge(e.startNodeId, e.endNodeId, length=e.length or 1.0)

    node_ids = list(G.nodes())
    node_positions = [pos[nid] for nid in node_ids]
    kdtree = KDTree(node_positions) if node_positions else None

    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 8))
    plt.title("Graph Editor\nLeft click: Remove Node | Right Click and Drag: Add Edge | 's': Save")

    node_scatter = ax.scatter([x for x, y in node_positions],
                              [y for x, y in node_positions],
                              s=50, c='skyblue', zorder=2)
    edge_collection = LineCollection([(pos[u], pos[v]) for u, v in G.edges()],
                                     colors='gray', linewidths=1, zorder=1)
    ax.add_collection(edge_collection)
    fig.canvas.draw()
    fig.canvas.flush_events()
    background = fig.canvas.copy_from_bbox(ax.bbox)

    # Drag / Selection
    selected_node = [None]
    drag_line = [None]
    region_start = [None]
    rect_artist = [None]

    def update_view():
        fig.canvas.restore_region(background)
        node_coords = [pos[nid] for nid in G.nodes()]
        node_scatter.set_offsets(node_coords)
        ax.draw_artist(node_scatter)
        edges_xy = [(pos[u], pos[v]) for u, v in G.edges()]
        edge_collection.set_segments(edges_xy)
        ax.draw_artist(edge_collection)
        fig.canvas.blit(ax.bbox)
        fig.canvas.flush_events()

    def find_nearest_node(x, y, tol=50):
        if not kdtree or len(G.nodes()) == 0:
            return None
        dist, idx = kdtree.query([x, y])
        if dist < tol:
            return node_ids[idx]
        return None

    # ----------------- Events -----------------
    def on_press(event):
        nonlocal kdtree
        if event.xdata is None or event.ydata is None:
            return

        if event.button == 1:
            region_start[0] = (event.xdata, event.ydata)
            rect_artist[0] = ax.add_patch(
                plt.Rectangle((event.xdata, event.ydata), 0, 0,
                              linewidth=1, edgecolor='red', facecolor='red', alpha=0.3)
            )
            fig.canvas.draw()
        elif event.button == 3:
            node = find_nearest_node(event.xdata, event.ydata)
            if node:
                selected_node[0] = node
                drag_line[0] = ax.plot([pos[node][0], event.xdata],
                                       [pos[node][1], event.ydata],
                                       'r--', linewidth=2, zorder=3)[0]
                fig.canvas.draw()

    def on_motion(event):
        if event.xdata is None or event.ydata is None:
            return
        if region_start[0] and rect_artist[0]:
            x0, y0 = region_start[0]
            rect_artist[0].set_width(event.xdata - x0)
            rect_artist[0].set_height(event.ydata - y0)
            fig.canvas.draw_idle()
        if selected_node[0] and drag_line[0]:
            drag_line[0].set_data([pos[selected_node[0]][0], event.xdata],
                                  [pos[selected_node[0]][1], event.ydata])
            fig.canvas.draw_idle()

    def on_release(event):
        nonlocal kdtree
        if event.xdata is None or event.ydata is None:
            return

        if region_start[0] and rect_artist[0]:
            x0, y0 = region_start[0]
            x1, y1 = event.xdata, event.ydata
            xmin, xmax = sorted([x0, x1])
            ymin, ymax = sorted([y0, y1])
            to_delete = [nid for nid, (x, y) in pos.items() if xmin <= x <= xmax and ymin <= y <= ymax]
            for nid in to_delete:
                if nid in G:
                    G.remove_node(nid)
                    pos.pop(nid)
                    node_ids.remove(nid)
            node_positions[:] = [pos[nid] for nid in node_ids]
            kdtree = KDTree(node_positions) if node_positions else None
            rect_artist[0].remove()
            rect_artist[0] = None
            region_start[0] = None
            update_view()

        if selected_node[0] and drag_line[0]:
            end_node = find_nearest_node(event.xdata, event.ydata)
            if end_node and end_node != selected_node[0]:
                length = math.dist(pos[selected_node[0]], pos[end_node])
                G.add_edge(selected_node[0], end_node, length=length)
                logger.info(f"New Layout {selected_node[0]} <-> {end_node} (L={length:.2f})")
                update_view()
            drag_line[0].remove()
            drag_line[0] = None
            selected_node[0] = None
            fig.canvas.draw_idle()

    def on_key(event):
        if event.key == 's':
            logger.info("Save and Close")
            plt.close(fig)

    # ----------------- Connect Events -----------------
    fig.canvas.mpl_connect('button_press_event', on_press)
    fig.canvas.mpl_connect('motion_notify_event', on_motion)
    fig.canvas.mpl_connect('button_release_event', on_release)
    fig.canvas.mpl_connect('key_press_event', on_key)

    plt.show(block=True)

    new_nodes = {nid: nodes[nid] for nid in G.nodes() if nid in nodes}
    new_edges = []
    seq = 0
    for u, v, data in G.edges(data=True):
        e = Edge(startNodeId=u, endNodeId=v, sequenceId=seq, edgeId=f"{u}_{v}_{seq}",
                 released=True, edgeDescription=None, maxSpeed=MAX_SPEED,
                 rotationAllowed=ROTATION_ALLOWED, length=data.get('length', 1.0), actions=[])
        new_edges.append(e)
        seq += 1

    return new_nodes, new_edges



# ---- MAIN ENTRYPOINT ----#
def generate_grid_layout(map_id: str = "map1") -> tuple[list[Node], list[Edge]]:
    nodes, edges = create_full_grid(map_id)
    nodes, edges = remove_and_reconnect_nodes(nodes, edges, map_id)
    return filter_largest_connected(nodes, edges)

def generate_grid_layout_man(map_id: str = "map1") -> tuple[list[Node], list[Edge]]:
    nodes, edges = create_full_grid(map_id)
    # nodes, edges = remove_and_reconnect_nodes(nodes, edges, map_id)
    nodes, edges = edit_graph_gui(nodes, edges)
    return filter_largest_connected(nodes, edges)




def generate_start_end_pairs(nodes: List[Node], count: int) -> Tuple[List[str], List[str]]:
    """
    Creates two list with randomly selected start and end nodes.
    :param nodes: List with nodes
    :param count: Number of pairs
    :return: (start_nodes, end_nodes) – jeweils eine Liste von nodeId-Strings
    """
    if len(nodes) < 3 * count:
        raise ValueError("No enough nodes for the desired number od node pairs!")

    node_ids = [node.nodeId for node in nodes]
    random.shuffle(node_ids)

    selected = node_ids[:3 * count]
    start_nodes = selected[:count]
    end_nodes = selected[count:2*count]
    cons_nodes = selected[2*count:]

    return start_nodes, end_nodes, cons_nodes



# -------------------------------
# MAIN EXECUTION
# -------------------------------

def create_lif(p = None, p2 = None, randomly = True ):
    if p is None:
        p = "generated_lif.json"
    if TEST_PP_LAYOUT_ID is None:
        lid = MAP_ID_DEFAULT
    else:
        lid = TEST_PP_LAYOUT_ID

    if p2 is None:
        p2 = PATH_PAIRS_FILE
    if randomly:
        nodes, edges = generate_grid_layout(lid)
    else:
        nodes, edges = generate_grid_layout_man(lid)



    layout = Layout(
        layoutId=lid,
        layoutName="Demo Layout",
        layoutVersion=1,
        layoutDescription="Generated layout with grid and random node removal.",
        nodes=nodes,
        edges=edges,
        stations=[]
    )

    lif_obj = LIFObject(layouts=[layout])
    start_nodes, end_nodes, cons_nodes = [], [], []
    constraints = set()
    try:
        start_nodes, end_nodes, cons_nodes = generate_start_end_pairs(nodes, NUMBER_OF_PATHS)
        constraints = set()
        for node in cons_nodes:
            number = random.randint(1, 20)
            constraints.add((node, number))
            constraints.add((node, (number + random.randint(4, 7), np.inf)))

        with open(p2, "w") as f:
            json.dump({
                "start_nodes": start_nodes,
                "end_nodes": end_nodes,
                "constraints": list(constraints)
            }, f, indent=2)

        if SHOW_LIF:
            logger.info(f"Start nodes: {start_nodes}")
            logger.info(f"End nodes: {end_nodes}")

    except ValueError as ve:
        logger.exception(f"Error: Can not create start/goal nodes: {ve}")

    with open(p, "w") as f:
        json.dump(lif_obj.dict(), f, indent=2)

    return start_nodes, end_nodes, constraints



if __name__ == "__main__":
    create_lif(LIF_PATH, PATH_PAIRS_FILE, randomly=False)
    show_lif(LIF_PATH)
