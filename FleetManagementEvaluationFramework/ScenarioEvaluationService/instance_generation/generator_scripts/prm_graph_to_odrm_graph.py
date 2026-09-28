import copy
import logging
from collections import defaultdict
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import log_config.config

import cv2
import torch
import numpy as np
import networkx as nx
import imageio

import warnings
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt

from scipy.spatial import Delaunay
from skimage.draw import line

from routing_graph_generation_methods.general_graph_embedding_methods.geometric_nodes_and_edge_checking import \
    distance_to_nearest_obstacle_fast_meter
import matplotlib

warnings.filterwarnings('ignore')

logger = logging.getLogger(log_config.config.LOGGER_NAME)
matplotlib.use("TkAgg")


def euclidean_weight(u, v, pos, temp_positions=None):
    def get_pos(n):
        if temp_positions and n in temp_positions:
            return temp_positions[n]
        return pos[n]

    diff = get_pos(u) - get_pos(v)
    return torch.norm(diff).item()


def relaxed_weight(u, v, alpha_direction, s_map, pos, temp_positions):
    dist = euclidean_weight(u, v, pos, temp_positions)

    if (u, v) in s_map:
        s = s_map[(u, v)]
    elif (v, u) in s_map:
        s = -s_map[(v, u)]
    else:
        return dist

    return dist * (1 + alpha_direction * torch.sigmoid(-s)).item()


def create_graph(prm_graph, endpoints, length, width, image_file, gray_mask, obstacle_mask, px_per_meter_x,
                 px_per_meter_y, layout_name,
                 iter=200, batch_size=256, lr=0.05, lr_end=0.001, amr_radius=0.5, num_val_paths=300,
                 max_edge_length=10):
    """
    Create an Optimized Directed Roadmap (ODRM) from a PRM graph using SGD.

    Algorithm:
    1. Extract PRM nodes and edges
    2. Initialize edge direction parameters s_e uniformly
    3. For each iteration:
       a. Sample random start/goal positions
       b. Find path in PRM using A* with current s_e values
       c. Compute path cost and gradients
       d. Accumulate gradients over batch
       e. Update parameters using Adam optimizer
    4. Build final directed graph based on learned s_e values

    Args:
        prm_graph: Input PRM graph (networkx.Graph)
        length: Workspace length
        width: Workspace width
        min_s: Threshold for edge directionality (|s_e| > min_s required for directed edge)
        iter: Number of iterations (default: 2000)
        batch_size: Paths sampled per iteration (default: 256)
        alpha: Connection cost weight (default: 3.0)
        lambda_dir: Direction penalty weight (default: 2.0)
        lambda_len: Edge length weight (default: 1.0)
        lr_pos: Learning rate for node positions (default: 1e-3)
        lr_s: Learning rate for s_e parameters (default: 1e-2)
        amr_radius: Robot clearance (unused but kept for API compatibility)

    Returns:
        (odrm, nodes_pos): Directed roadmap as DiGraph and optimized node positions array
    """
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None, None
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)

    binary_map = (binary > 0).astype(np.uint8)

    free_pixels = np.argwhere(binary_map == 1)
    gray_pixels = np.argwhere((img >= 140) & (img <= 180))
    free_pixels = np.vstack([free_pixels, gray_pixels])

    dist_map_m = distance_transform_edt(obstacle_mask == 0,
                                        sampling=[float(1 / px_per_meter_y), float(1 / px_per_meter_x)])

    graph = copy.deepcopy(prm_graph)

    neighbors = defaultdict(list)
    for u, v in graph.edges():
        neighbors[u].append(v)
        neighbors[v].append(u)

    s_map = {}
    s_map_glob = {}
    for u, v in graph.edges():
        value_rand = (torch.rand(1) * 0.2 - 0.1).requires_grad_()
        value = torch.tensor(value_rand, requires_grad=True)
        s_map[(u, v)] = value
        s_map_glob[(u, v)] = value

    pos = {n: torch.tensor(np.array(n, dtype=np.float32), requires_grad=True)
           for n in graph.nodes()}

    optimizer = torch.optim.Adam(list(list(pos.values()) + list(s_map.values())), lr=lr)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=iter,
        eta_min=lr_end
    )

    logger.info(
        f"Creating ODRM from PRM with {prm_graph.number_of_nodes()} nodes and {prm_graph.number_of_edges()} edges")

    val_pairs = [
        sample_start_and_goal(free_pixels, px_per_meter_x, px_per_meter_y, dist_map_m, amr_radius)
        for _ in range(num_val_paths)
    ]

    best_solution = (None, None, None, None, None, None)  # Iteration, costs, num_paths, pos, s_map
    frames = []

    # ========== STEP 7: Training loop ==========
    for iteration in range(iter):
        batch_cost = torch.zeros(1)
        paths_found = 0
        active_nodes_in_batch = set()
        for _ in range(batch_size):
            start, goal = sample_start_and_goal(free_pixels, px_per_meter_x, px_per_meter_y, dist_map_m, amr_radius)

            g_rel = nx.Graph()
            g_rel.add_nodes_from(graph.nodes())
            g_rel.add_edges_from(graph.edges())

            start_node = (round(start[0], 2), round(start[1], 2))
            goal_node = (round(goal[0], 2), round(goal[1], 2))

            connection_start_nodes = get_three_closest_nodes(start_node, pos)
            connection_goal_nodes = get_three_closest_nodes(goal_node, pos)

            g_rel.add_node(start_node)
            g_rel.add_node(goal_node)

            for node in connection_start_nodes:
                if edge_clear_fast(start_node, node, px_per_meter_x, px_per_meter_y, binary, amr_radius, dist_map_m):
                    g_rel.add_edge(start_node, node)

            for node in connection_goal_nodes:
                if edge_clear_fast(goal_node, node, px_per_meter_x, px_per_meter_y, binary, amr_radius, dist_map_m):
                    g_rel.add_edge(node, goal_node)

            if start_node == goal_node:
                continue
            temp_positions = {
                start_node: torch.tensor(start, dtype=torch.float32, requires_grad=False),
                goal_node: torch.tensor(goal, dtype=torch.float32, requires_grad=False)
            }

            try:
                path = nx.shortest_path(g_rel, start_node, goal_node,
                                        weight=lambda u, v, d: relaxed_weight(u, v, alpha_direction=2,
                                                                              s_map=s_map, pos=pos,
                                                                              temp_positions=temp_positions),
                                        method='dijkstra')
            except:
                continue

            if path is None or len(path) < 2:
                continue

            for node in path:
                active_nodes_in_batch.add(node)

            costs = path_cost_gradient(path, pos, s_map, temp_positions)

            batch_cost = batch_cost + costs
            paths_found += 1

        old_pos = {n: pos[n].detach().clone() for n in graph.nodes()}
        optimizer.zero_grad()
        batch_cost.backward()
        optimizer.step()

        with torch.no_grad():
            for n in graph.nodes():
                candidate = pos[n]
                if check_valid_node_position(n, candidate.cpu().numpy(), graph, pos, px_per_meter_x, px_per_meter_y,
                                             binary, amr_radius, dist_map_m):
                    graph.nodes[n]["pos"] = candidate.cpu().numpy()
                else:
                    # Node reset to old position
                    if check_valid_node_position(n, old_pos[n].cpu().numpy(), graph, pos, px_per_meter_x,
                                                 px_per_meter_y, binary, amr_radius, dist_map_m):
                        pos[n].copy_(old_pos[n])
                    else:
                        graph.nodes[n]["pos"] = candidate.cpu().numpy()
                    # Only reset if old position valid

        graph, s_map, s_map_glob = update_delaunay_edges(graph, pos, s_map, s_map_glob,
                                                         px_per_meter_x, px_per_meter_y, binary, obstacle_mask,
                                                         amr_radius, dist_map_m, max_edge_length)

        refresh_optimizer(optimizer, pos, s_map, lr)

        scheduler.step()

        # Progress report
        if (iteration + 1) % 1 == 0 or iteration == 0:
            odrm = create_odrm(graph, pos, s_map_glob, px_per_meter_x, px_per_meter_y, binary, dist_map_m,
                               amr_radius, max_edge_length)

            # visualize_failed_query(odrm, None, None, length, width, binary)
            cost, num_paths, max_cost = evaluate_cost_odrm(odrm, val_pairs, px_per_meter_x, px_per_meter_y, binary,
                                                           amr_radius, dist_map_m)
            avg_cost = cost / max(1, num_paths) if num_paths > 0 else 0.0
            cost_avg_normalized = avg_cost * (num_paths / len(val_pairs)) + max_cost * (
                    (len(val_pairs) - num_paths) / len(val_pairs))
            total_cost = cost + (len(val_pairs) - num_paths) * max_cost
            cost_rel, num_paths_rel = evaluate_cost(graph, pos, s_map, val_pairs, px_per_meter_x, px_per_meter_y,
                                                    binary,
                                                    obstacle_mask, amr_radius, dist_map_m)
            avg_cost_rel = cost_rel / max(1, num_paths_rel) if num_paths_rel > 0 else 0.0
            logger.info(f"Iteration {iteration + 1}/{iter} - Avg cost: {cost_avg_normalized:.4f} - Total costs:"
                        f" {total_cost:.4f} - Paths: {num_paths}/{num_val_paths} - Avg. costs relaxed graph: {avg_cost_rel}"
                        f" - Total costs relaxed graph: {cost_rel} - Paths relaxed graph: {num_paths_rel}")
            if best_solution[0] is None or (best_solution[1] >= cost_rel and num_paths >= best_solution[2]):
                best_solution = (iteration + 1, cost_rel, num_paths, copy.deepcopy(graph), copy.deepcopy(pos),
                                 copy.deepcopy(s_map_glob))

        if (iteration + 1) % 200 == 0 or iteration == 0:
            odrm = create_odrm(graph, pos, s_map_glob, px_per_meter_x, px_per_meter_y, binary, dist_map_m,
                               amr_radius, max_edge_length)
            plot_odrm(odrm, length, width, image_file, gray_mask, px_per_meter_x, px_per_meter_y)

        if (iteration + 1) % 1 == 0:
            odrm = create_odrm(graph, pos, s_map_glob, px_per_meter_x, px_per_meter_y, binary, dist_map_m,
                               amr_radius, max_edge_length)
            frame = render_graph_frame(odrm, length, width, image_file, gray_mask, px_per_meter_x, px_per_meter_y,
                                       f'ODRM: Iteration {iteration + 1}', len(frames) + 1)
            frames.append(frame)

    # Cut animation after best solution
    frames = frames[:(best_solution[0])]

    logger.info("\nBuilding final ODRM...")
    imageio.mimsave(f"./odrm_training_visualization/data/odrm_training_{layout_name}_"
                    f"nodes_{len(prm_graph.nodes)}.gif", frames, fps=5)
    show_odrm_training(f"./odrm_training_visualization/data/odrm_training_{layout_name}_"
                       f"nodes_{len(prm_graph.nodes)}.gif")

    # ========== STEP 8: Build final directed graph ==========

    logger.info(f'Bets solution found in iteration: {best_solution[0]}')
    odrm = create_odrm(best_solution[3], best_solution[4], best_solution[5], px_per_meter_x,
                       px_per_meter_y, binary, dist_map_m, amr_radius, max_edge_length)
    gray_nodes = plot_odrm(odrm, length, width, image_file, gray_mask, px_per_meter_x, px_per_meter_y)

    return odrm, gray_nodes


def path_cost_gradient(path, pos, s_map, temp_positions=None, alpha_tail=10, alpha_direction=2):
    def get_pos(n):
        if temp_positions and n in temp_positions:
            return temp_positions[n]
        return pos[n]

    cost = torch.zeros(1)

    # First edge #
    u, v = path[0], path[1]
    diff = get_pos(u) - get_pos(v)
    dist = torch.norm(diff)
    cost += cost + alpha_tail * (dist ** 2 + dist)

    # Last edge #
    u, v = path[-2], path[-1]
    diff = get_pos(u) - get_pos(v)
    dist = torch.norm(diff)
    cost += cost + alpha_tail * (dist ** 2 + dist)

    for i in range(1, len(path) - 2):
        u, v, w = path[i - 1], path[i], path[i + 1]

        diff = get_pos(v) - get_pos(w)
        dist = torch.norm(diff)
        if (v, w) in s_map:
            s = s_map[(v, w)]
        elif (w, v) in s_map:
            s = -s_map[(w, v)]
        else:
            continue
        direction_penalty = 1 + alpha_direction * torch.sigmoid(-s)
        edge_cost = dist * direction_penalty

        cost += edge_cost

    return cost


def create_odrm(graph, pos, s_map_glob, px_per_meter_x, px_per_meter_y, binary, dist_map_m, amr_radius,
                max_edge_length):
    odrm = nx.DiGraph()

    # Add all nodes with optimized positions
    old_to_new = {}
    new_to_old = {}
    for n in graph.nodes():
        new_pos = pos[n].detach().cpu().numpy()
        new_node = (round(float(new_pos[0]), 2), round(float(new_pos[1]), 2))
        old_to_new[n] = new_node
        new_to_old[new_node] = n

        odrm.add_node(new_node)

    nodes = list(pos.keys())
    points = np.array([pos[n].detach().cpu().numpy() for n in nodes])  # new

    tri = Delaunay(points)
    candidate_edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            u = nodes[simplex[i]]
            v = nodes[simplex[(i + 1) % 3]]
            if u != v:
                candidate_edges.add((old_to_new[u], old_to_new[v]))

    valid_edges = set()
    for u, v in candidate_edges:
        if edge_clear_fast(u, v, px_per_meter_x, px_per_meter_y, binary, amr_radius, dist_map_m):
            if compute_length_edge(u, v) <= max_edge_length:
                valid_edges.add((u, v))

    for (u, v) in valid_edges:  # new node ids
        u_old, v_old = new_to_old[u], new_to_old[v]

        if (u_old, v_old) in s_map_glob.keys():
            if s_map_glob[(u_old, v_old)] > 0:
                odrm.add_edge(u, v)
            else:
                odrm.add_edge(v, u)
        elif (v_old, u_old) in s_map_glob.keys():
            if s_map_glob[(v_old, u_old)] > 0:
                odrm.add_edge(v, u)
            else:
                odrm.add_edge(u, v)
        else:
            direction_found = False
            for x in graph.nodes():
                if (u_old, x) in s_map_glob and (x, v_old) in s_map_glob:
                    if s_map_glob[(u_old, x)] > 0 and s_map_glob[(x, v_old)] > 0:
                        odrm.add_edge(u, v)
                        direction_found = True
                        break
                    elif s_map_glob[(u_old, x)] < 0 and s_map_glob[(x, v_old)] < 0:
                        odrm.add_edge(v, u)
                        direction_found = True
                        break
                elif (v_old, x) in s_map_glob and (x, u_old) in s_map_glob:
                    if s_map_glob[(v_old, x)] > 0 and s_map_glob[(x, u_old)] > 0:
                        odrm.add_edge(v, u)
                        direction_found = True
                        break
                    elif s_map_glob[(v_old, x)] < 0 and s_map_glob[(x, u_old)] < 0:
                        odrm.add_edge(u, v)
                        direction_found = True
                        break

            if direction_found is False:
                odrm.add_edge(u, v)

    # Delete isolated nodes with no neighbors
    isolated_nodes = list(nx.isolates(odrm))
    odrm.remove_nodes_from(isolated_nodes)

    return odrm


def plot_odrm(odrm_graph, length, width, image_file, gray_mask, px_per_meter_x, px_per_meter_y):
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None, None
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    debug_img = cv2.cvtColor(binary.copy(), cv2.COLOR_GRAY2BGR)

    plt.clf()
    plt.close('all')
    plt.figure(figsize=(12, 6))
    extent = [0, length, width, 0]
    plt.imshow(debug_img, cmap='gray', extent=extent)

    pos = {n: (n[0], n[1]) for n in odrm_graph.nodes}

    gray_nodes = []
    normal_nodes = []

    for n, p in pos.items():
        if is_node_on_gray(p, gray_mask, px_per_meter_x, px_per_meter_y):
            gray_nodes.append(n)
        else:
            normal_nodes.append(n)

    nx.draw_networkx_nodes(odrm_graph, pos=pos, nodelist=normal_nodes, node_size=5, node_color='red')
    nx.draw_networkx_nodes(odrm_graph, pos=pos, nodelist=gray_nodes, node_size=5, node_color='blue')

    nx.draw_networkx_edges(odrm_graph, pos=pos, node_size=5, arrowstyle='->', arrowsize=10, edge_color='lime')

    plt.title(f"ODRM with {odrm_graph.number_of_nodes()} vertices")
    plt.xlabel("Length")
    plt.ylabel("Width")
    plt.show()

    return gray_nodes


def is_node_on_gray(node_pos, gray_mask, px_per_meter_x, px_per_meter_y):
    x_m, y_m = node_pos
    x_px = int(x_m * px_per_meter_x)
    y_px = int(y_m * px_per_meter_y)

    h, w = gray_mask.shape

    if 0 <= y_px < h and 0 <= x_px < w:
        return gray_mask[y_px, x_px]
    return False


def check_valid_node_position(node_id, node_pos, graph, pos, px_per_meter_x, px_per_meter_y, binary,
                              amr_rad, dist_map_m):
    valid_node_position = True
    if (distance_to_nearest_obstacle_fast_meter((node_pos[0], node_pos[1]), dist_map_m, px_per_meter_x, px_per_meter_y)
            <= amr_rad):
        return False

    number_valid_edges = 0
    for nb in graph.neighbors(node_id):
        if edge_clear_fast(node_pos,
                           pos[nb].detach().cpu().numpy(),
                           px_per_meter_x, px_per_meter_y,
                           binary, amr_rad, dist_map_m):
            number_valid_edges += 1
    if number_valid_edges < 2:
        return False

    return valid_node_position


def edge_clear_fast(start_pos, end_pos, px_per_meter_x, px_per_meter_y, binary, amr_rad, dist_map_m):
    """
    Check if edge free between obstacles
    """
    image_h, image_w = binary.shape
    x1_px, y1_px = int(start_pos[0] * px_per_meter_x), int(start_pos[1] * px_per_meter_y)
    x2_px, y2_px = int(end_pos[0] * px_per_meter_x), int(end_pos[1] * px_per_meter_y)

    rr, cc = line(y1_px, x1_px, y2_px, x2_px)

    if (rr.min() < 0 or rr.max() >= image_h or cc.min() < 0 or cc.max() >= image_w):
        return False

    if not np.all(binary[rr, cc] == 255):
        return False

    # min_clearance_px = amr_rad * px_per_meter_x
    if np.any(dist_map_m[rr, cc] < amr_rad):
        return False

    return True


def get_three_closest_nodes(query_xy, pos_dict, k=3):
    q = torch.tensor(query_xy, dtype=torch.float32)
    nodes = list(pos_dict.keys())
    coords = torch.stack([pos_dict[n] for n in nodes])
    dists = torch.norm(coords - q, dim=1)
    nearest_idx = torch.topk(-dists, k).indices
    nearest_nodes = [nodes[i] for i in nearest_idx]
    return nearest_nodes


def sample_start_and_goal(free_pixels, px_per_meter_x, px_per_meter_y, dist_map_m, amr_rad, attempts=100):
    if len(free_pixels) == 0:
        raise ValueError("Keine freien Pixel vorhanden!")

    a = 0
    valid_range = False
    while a < attempts and valid_range is False:
        idx_start = np.random.randint(len(free_pixels))
        y_idx, x_idx = free_pixels[idx_start]

        x_m_start = x_idx / px_per_meter_x
        y_m_start = y_idx / px_per_meter_y

        if (distance_to_nearest_obstacle_fast_meter((x_m_start, y_m_start), dist_map_m, px_per_meter_x, px_per_meter_y)
                > amr_rad):
            valid_range = True

    a = 0
    valid_range = False
    while a < attempts and valid_range is False:
        idx_goal = np.random.randint(len(free_pixels))
        y_idx_goal, x_idx_goal = free_pixels[idx_goal]

        x_m_goal = x_idx_goal / px_per_meter_x
        y_m_goal = y_idx_goal / px_per_meter_y
        if (distance_to_nearest_obstacle_fast_meter((x_m_goal, y_m_goal), dist_map_m, px_per_meter_x, px_per_meter_y)
                > amr_rad):
            valid_range = True

    if valid_range is False:
        logger.info('Sample pair in invalid range!')

    return [x_m_start, y_m_start], [x_m_goal, y_m_goal]


def update_delaunay_edges(graph, pos, s_map, s_map_glob, px_per_meter_x, px_per_meter_y, binary, obstacle_mask,
                          amr_radius, dist_map_px, max_edge_length):
    nodes = list(pos.keys())
    points = np.array([pos[n].detach().cpu().numpy() for n in nodes])

    s_map_new = {}

    new_graph = nx.Graph()
    new_graph.add_nodes_from(nodes)

    if len(points) < 3:
        return graph, s_map

    tri = Delaunay(points)

    candidate_edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            u = nodes[simplex[i]]
            v = nodes[simplex[(i + 1) % 3]]
            if (v, u) in s_map_glob.keys():
                if u != v and (v, u) not in candidate_edges and (u, v) not in candidate_edges:
                    candidate_edges.add((v, u))
            else:
                if u != v and (u, v) not in candidate_edges and (v, u) not in candidate_edges:
                    candidate_edges.add((u, v))

    valid_edges = set()
    for u, v in candidate_edges:
        if (edge_clear_fast(pos[u].detach().cpu().numpy(), pos[v].detach().cpu().numpy(), px_per_meter_x,
                            px_per_meter_y,
                            binary, amr_radius, dist_map_px) is True):
            if compute_length_edge(pos[u].detach().cpu().numpy(), pos[v].detach().cpu().numpy()) <= max_edge_length:
                valid_edges.add((u, v))

    # Graph reset
    for u, v in valid_edges:
        new_graph.add_edge(u, v)
        key = (u, v)
        if key not in s_map_glob:
            s_map_glob[key] = torch.tensor(0.0, requires_grad=True)
        else:
            if key in s_map:
                s_map_glob[key] = s_map[key]

        s_map_new[key] = s_map_glob[key]

    return new_graph, s_map_new, s_map_glob


@torch.no_grad()
def evaluate_cost(graph, pos, s_map, val_pairs, px_per_meter_x, px_per_meter_y, binary, obstacle_mask, amr_radius,
                  dist_map_px):
    total_cost = 0.0
    paths_found = 0

    for start, goal in val_pairs:
        g_rel = graph.copy()

        start_node = (round(start[0], 2), round(start[1], 2))
        goal_node = (round(goal[0], 2), round(goal[1], 2))

        connection_start_nodes = get_three_closest_nodes(start_node, pos)
        connection_goal_nodes = get_three_closest_nodes(goal_node, pos)

        g_rel.add_node(start_node)
        g_rel.add_node(goal_node)

        for node in connection_start_nodes:
            if edge_clear_fast(start_node, node, px_per_meter_x, px_per_meter_y, binary, amr_radius,
                               dist_map_px):
                g_rel.add_edge(start_node, node)

        for node in connection_goal_nodes:
            if edge_clear_fast(goal_node, node, px_per_meter_x, px_per_meter_y, binary, amr_radius,
                               dist_map_px):
                g_rel.add_edge(node, goal_node)

        if start_node == goal_node:
            continue

        temp_positions = {
            start_node: torch.tensor(start, dtype=torch.float32),
            goal_node: torch.tensor(goal, dtype=torch.float32)
        }

        try:
            path = nx.shortest_path(
                g_rel,
                start_node,
                goal_node,
                weight=lambda u, v, d: relaxed_weight(u, v, alpha_direction=2,
                                                      s_map=s_map, pos=pos,
                                                      temp_positions=temp_positions),
                method='dijkstra'
            )
        except:
            continue

        if path is None or len(path) < 2:
            continue

        cost = path_cost_gradient(path, pos, s_map, temp_positions)
        total_cost += cost.item()
        paths_found += 1

    if paths_found == 0:
        return float("inf"), 0

    return total_cost, paths_found


def refresh_optimizer(optimizer, pos, s_map, lr):
    """
    Aktualisiert den Optimizer:
    - fügt neue Parameter hinzu
    - entfernt Parameter, die nicht mehr benötigt werden
    - behält bereits existierende Parametergruppen bei
    """
    current_params = set()
    for group in optimizer.param_groups:
        current_params.update(group['params'])

    new_params = set(list(pos.values()) + list(s_map.values()))

    # Parameter hinzufügen, die noch nicht im Optimizer sind
    for p in new_params - current_params:
        optimizer.add_param_group({'params': [p], 'lr': lr})

    # Parameter entfernen, die nicht mehr benötigt werden
    for group in optimizer.param_groups:
        group['params'][:] = [p for p in group['params'] if p in new_params]

    # Optional: leere Gruppen löschen
    optimizer.param_groups[:] = [g for g in optimizer.param_groups if len(g['params']) > 0]


def render_graph_frame(odrm_graph, length, width, image_file, gray_mask, px_per_meter_x, px_per_meter_y, title, i):
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None, None
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    debug_img = cv2.cvtColor(binary.copy(), cv2.COLOR_GRAY2BGR)

    plt.clf()
    plt.close('all')
    plt.figure(figsize=(10, 10))
    extent = [0, length, width, 0]
    plt.imshow(debug_img, cmap='gray', extent=extent)

    pos = {n: (n[0], n[1]) for n in odrm_graph.nodes}

    gray_nodes = []
    normal_nodes = []

    for n, p in pos.items():
        if is_node_on_gray(p, gray_mask, px_per_meter_x, px_per_meter_y):
            gray_nodes.append(n)
        else:
            normal_nodes.append(n)

    nx.draw_networkx_nodes(odrm_graph, pos=pos, nodelist=normal_nodes, node_size=5, node_color='red')
    nx.draw_networkx_nodes(odrm_graph, pos=pos, nodelist=gray_nodes, node_size=5, node_color='blue')

    nx.draw_networkx_edges(odrm_graph, pos=pos, node_size=5, arrowstyle='->', arrowsize=10, edge_color='lime')

    plt.title(title)
    plt.axis("off")

    filename = f"./odrm_training_visualization/data_creation/frame_{i}.png"
    plt.savefig(filename)
    plt.close()
    return imageio.imread(filename)


def show_odrm_training(file):
    root = tk.Tk()
    root.title("ODRM Training")

    # open GIF
    im = Image.open(file)
    frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(im)]

    label = tk.Label(root)
    label.pack()

    playing = False
    current_frame = 0

    def play_gif(ind):
        nonlocal current_frame, playing  # <-- hier
        if not playing:
            return
        label.configure(image=frames[ind])
        current_frame = ind
        ind += 1
        if ind < len(frames):
            root.after(100, play_gif, ind)
        else:
            playing = False
            logger.info("Animation finish. Push Play to restart animation!")

    def toggle_play():
        nonlocal playing, current_frame  # <-- hier
        if not playing:
            playing = True
            play_gif(0)

    # Play-Button
    btn = tk.Button(root, text="Play", command=toggle_play)
    btn.pack()

    root.mainloop()
    return


def compute_length_edge(pos_u, pos_v):
    dx = pos_u[0] - pos_v[0]
    dy = pos_u[1] - pos_v[1]
    length = np.sqrt(dx ** 2 + dy ** 2)
    return length


@torch.no_grad()
def evaluate_cost_odrm(graph: nx.DiGraph(), val_pairs, px_per_meter_x, px_per_meter_y, binary, amr_radius, dist_map_m):
    total_cost = 0
    paths_found = 0
    max_cost = 0
    for start, goal in val_pairs:
        start_node = (round(start[0], 2), round(start[1], 2))
        goal_node = (round(goal[0], 2), round(goal[1], 2))

        g_rel = graph.copy()
        pos_ev = {n: torch.tensor(np.array(n, dtype=np.float32), requires_grad=True)
                  for n in graph.nodes()}

        connection_start_nodes = get_three_closest_nodes(start_node, pos_ev)
        connection_goal_nodes = get_three_closest_nodes(goal_node, pos_ev)

        pos_ev[start_node] = torch.tensor(start_node, dtype=torch.float32)
        pos_ev[goal_node] = torch.tensor(goal_node, dtype=torch.float32)

        g_rel.add_node(start_node)
        g_rel.add_node(goal_node)
        if len(connection_start_nodes) == 0:
            logger.info('No connection to start node found')
        if len(connection_goal_nodes) == 0:
            logger.info('No connection to goal node found')

        for node in connection_start_nodes:
            if edge_clear_fast(start_node, node, px_per_meter_x, px_per_meter_y, binary, amr_radius,
                               dist_map_m):
                g_rel.add_edge(start_node, node)

        for node in connection_goal_nodes:
            if edge_clear_fast(goal_node, node, px_per_meter_x, px_per_meter_y, binary, amr_radius,
                               dist_map_m):
                g_rel.add_edge(node, goal_node)

        try:
            path = nx.shortest_path(
                g_rel,
                start_node,
                goal_node,
                weight=lambda u, v, d: euclidean_weight(u, v, pos_ev),
                method='dijkstra'
            )
        except:
            continue

        if path is None or len(path) < 2:
            continue

        path_length = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            path_length += float(torch.norm(torch.tensor(pos_ev[u]) - torch.tensor(pos_ev[v])))

        total_cost += path_length
        if path_length > max_cost:
            max_cost = path_length
        paths_found += 1

    return total_cost, paths_found, max_cost


def visualize_failed_query(graph, start_node, goal_node, length, width, binary=None):
    if binary is not None:
        debug_img = cv2.cvtColor(binary.copy(), cv2.COLOR_GRAY2BGR)
        extent = [0, length, width, 0]
        plt.imshow(debug_img, cmap='gray', extent=extent)

    # Knoten plotten
    pos = {n: (n[0], n[1]) for n in graph.nodes}

    nx.draw_networkx_nodes(graph, pos=pos, node_size=5, node_color='blue')

    # plot edge
    nx.draw_networkx_edges(graph, pos=pos, node_size=5, arrowstyle='->', arrowsize=10, edge_color='lime')
    if start_node is not None:
        # mark start and goal
        plt.scatter(start_node[0], start_node[1], c='orange', s=30, label='Start')
    if goal_node is not None:
        plt.scatter(goal_node[0], goal_node[1], c='red', s=30, label='Goal')

    plt.legend()
    plt.title("Failed Path Query")
    plt.show()
