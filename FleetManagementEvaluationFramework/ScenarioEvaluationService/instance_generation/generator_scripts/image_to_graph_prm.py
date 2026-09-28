import copy
import logging
import log_config.config

import cv2
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from skimage.draw import line
from scipy.spatial import Delaunay

matplotlib.use("TkAgg")


logger = logging.getLogger(log_config.config.LOGGER_NAME)


def create_graph(length: float, width: float, num_vertices: int, image_file: str, amr_rad: float = 0,
                 endpoint_distance=1, seed=1):
    np.random.seed(seed)
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None, None

    gray_mask = (img >= 140) & (img <= 180)

    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    obstacle_mask = (binary == 0)

    debug_img = cv2.cvtColor(binary.copy(), cv2.COLOR_GRAY2BGR)

    image_h, image_w = binary.shape

    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width

    G = nx.Graph()

    G, gray_nodes = add_gray_grid_nodes(G, gray_mask, obstacle_mask, px_per_meter_x, px_per_meter_y, amr_rad,
                                        endpoint_distance)

    sampled_vertices = copy.deepcopy(gray_nodes)

    max_attempts = num_vertices * 1000
    attempts = 0
    while len(sampled_vertices) < num_vertices and attempts < max_attempts:
        attempts += 1
        x_m = np.random.uniform(0, length)
        y_m = np.random.uniform(0, width)
        x_px = int(x_m * px_per_meter_x)
        y_px = int(y_m * px_per_meter_y)
        if 0 <= x_px < image_w and 0 <= y_px < image_h:
            if binary[y_px, x_px] == 255:
                if distance_to_nearest_obstacle((x_px, y_px), obstacle_mask, px_per_meter_x, px_per_meter_y) >= amr_rad:
                    if check_distance_to_other_endpoints(sampled_vertices, (x_px, y_px), px_per_meter_x,
                                                         px_per_meter_y, amr_rad) is True:
                        sampled_vertices.append((round(x_m, 2), round(y_m, 2)))
                        G.add_node((round(x_m, 2), round(y_m, 2)))
    
    actual_vertices = len(sampled_vertices)
    
    if actual_vertices < 3:
        logger.info("Not enough vertices sampled")
        return None, None, None

    vertices_array = np.array(sampled_vertices)

    try:
        delaunay = Delaunay(vertices_array)
    except Exception as e:
        logger.exception(f'Error: {e}')
        return None, None, None
    
    edges_set = set()
    for simplex in delaunay.simplices:
        for i in range(len(simplex)):
            for j in range(i + 1, len(simplex)):
                edge = tuple(sorted([simplex[i], simplex[j]]))
                edges_set.add(edge)
    
    valid_edges = 0
    for idx1, idx2 in edges_set:
        v1 = sampled_vertices[idx1]
        v2 = sampled_vertices[idx2]
        
        x1_px, y1_px = int(v1[0] * px_per_meter_x), int(v1[1] * px_per_meter_y)
        x2_px, y2_px = int(v2[0] * px_per_meter_x), int(v2[1] * px_per_meter_y)
        
        rr, cc = line(y1_px, x1_px, y2_px, x2_px)
        
        valid = all(0 <= r < image_h and 0 <= c < image_w and binary[r, c] == 255 
                   for r, c in zip(rr, cc))
        
        if valid:
            G.add_edge(v1, v2)
            valid_edges += 1
            for r, c in zip(rr, cc):
                if 0 <= r < image_h and 0 <= c < image_w:
                    debug_img[r, c] = (0, 255, 0)


    isolated_nodes = [n for n in G.nodes if len(list(G.neighbors(n))) == 0]
    add_new_node = False
    for n in isolated_nodes:
        new_pos = move_node_locally(n, G, obstacle_mask, px_per_meter_x, px_per_meter_y, amr_rad)
        if new_pos is not None:
            G.add_node((round(new_pos[0], 2), round(new_pos[1], 2)))
            sampled_vertices.append((round(new_pos[0], 2), round(new_pos[1], 2)))
            G.remove_node(n)
            sampled_vertices.remove(n)
            add_new_node = True
            if n in gray_nodes:
                gray_nodes.remove(n)
        else:
            G.remove_node(n)

    if add_new_node is True:
        if len(G.nodes) >= 3:
            G.clear_edges()
            vertices_array = np.array(list(G.nodes))
            try:
                delaunay = Delaunay(vertices_array)
            except Exception as e:
                logger.exception(f'Error: {e}')
                return None, None, None
            edges_set = set()
            for simplex in delaunay.simplices:
                for i in range(len(simplex)):
                    for j in range(i + 1, len(simplex)):
                        edge = tuple(sorted([simplex[i], simplex[j]]))
                        edges_set.add(edge)

            valid_edges = 0

            for idx1, idx2 in edges_set:
                v1 = sampled_vertices[idx1]
                v2 = sampled_vertices[idx2]

                x1_px, y1_px = int(v1[0] * px_per_meter_x), int(v1[1] * px_per_meter_y)
                x2_px, y2_px = int(v2[0] * px_per_meter_x), int(v2[1] * px_per_meter_y)

                rr, cc = line(y1_px, x1_px, y2_px, x2_px)

                valid = all(0 <= r < image_h and 0 <= c < image_w and binary[r, c] == 255
                            for r, c in zip(rr, cc))

                if valid:
                    G.add_edge(v1, v2)
                    valid_edges += 1
                    for r, c in zip(rr, cc):
                        if 0 <= r < image_h and 0 <= c < image_w:
                            debug_img[r, c] = (0, 255, 0)



    plt.figure(figsize=(12, 6))
    extent = [0, length, width, 0]
    plt.imshow(debug_img, cmap='gray', extent=extent)
    
    pos = {n: (n[0], n[1]) for n in G.nodes}
    normal_nodes = [n for n in G.nodes if n not in gray_nodes]


    nx.draw_networkx_nodes(G, pos=pos, nodelist=normal_nodes, node_size=5, node_color='red')
    nx.draw_networkx_nodes(G, pos=pos, nodelist=gray_nodes, node_size=5, node_color='blue')
    nx.draw_networkx_edges(G, pos=pos, edge_color='lime')
    
    plt.title(f"PRM with {actual_vertices} vertices (Delaunay Triangulation)")
    plt.xlabel("Length")
    plt.ylabel("Width")
    plt.show()
    
    return G, gray_nodes, pos, debug_img, gray_mask, obstacle_mask, px_per_meter_x, px_per_meter_y


def distance_to_nearest_obstacle(point, obstacle_mask, px_per_meter_x, px_per_meter_y):
    """
    point: (x, y)
    obstacle_mask: 2D numpy array, 1=obstacle, 0=free
    returns distance in pixels/meters
    """
    x, y = point  # pixel
    ys, xs = np.where(obstacle_mask == 1)

    dx_m = (xs - x) / px_per_meter_x
    dy_m = (ys - y) / px_per_meter_y

    if len(xs) == 0:
        return np.inf  # no obstacle
    distances = np.sqrt(dx_m ** 2 + dy_m ** 2)
    return np.min(distances)


def check_distance_to_other_endpoints(gray_endpoints, point, px_per_m_x, px_per_m_y, endpoint_distance):
    for end_point in gray_endpoints:
        if metric_distance_px(end_point, point, px_per_m_x, px_per_m_y) < endpoint_distance:
            return False
    return True


def metric_distance_px(p1, p2, px_per_m_x, px_per_m_y):
    dx = (p1[0] - (p2[0]/ px_per_m_x))
    dy = (p1[1] - (p2[1]/ px_per_m_y))
    return np.hypot(dx, dy)


def add_gray_grid_nodes(G, gray_mask, obstacle_mask, px_per_meter_x, px_per_meter_y, amr_rad, endpoint_distance):
    h, w = gray_mask.shape
    step_x = int(px_per_meter_x)
    step_y = int(px_per_meter_y)
    gray_nodes = []

    for y in range(0, h, step_y):
        for x in range(0, w, step_x):
            cx = x + step_x // 2
            cy = y + step_y // 2
            if cx >= w or cy >= h:
                continue
            if not gray_mask[cy, cx]:
                continue
            x_m = cx / px_per_meter_x
            y_m = cy / px_per_meter_y

            gray_nodes.append((round(x_m, 2), round(y_m, 2)))
            G.add_node((round(x_m, 2) ,round(y_m,2)))

    return G, gray_nodes


def move_node_locally(n_pos, G, obstacle_mask, px_per_meter_x, px_per_meter_y, amr_rad, r_max=0.5, max_attempts=20):
    x_old, y_old = n_pos
    for _ in range(max_attempts):
        dx = np.random.uniform(-r_max, r_max)
        dy = np.random.uniform(-r_max, r_max)
        x_new, y_new = x_old + dx, y_old + dy
        if x_new < 0 or y_new < 0:
            continue
        x_px = int(x_new * px_per_meter_x)
        y_px = int(y_new * px_per_meter_y)
        h, w = obstacle_mask.shape
        if x_px >= w or y_px >= h:
            continue
        if obstacle_mask[y_px, x_px]:
            continue
        can_connect = False
        for v in G.nodes:
            if v == n_pos:
                continue
            if edge_clear((x_new,y_new), v, obstacle_mask, px_per_meter_x, px_per_meter_y, amr_rad):
                can_connect = True
                break
        if can_connect:
            return (round(x_new,2), round(y_new,2))
    return None


def edge_clear(start_pos, end_pos, obstacle_mask, px_per_meter_x, px_per_meter_y, amr_rad):
    start_px = np.array([start_pos[0]*px_per_meter_x, start_pos[1]*px_per_meter_y])
    end_px = np.array([end_pos[0]*px_per_meter_x, end_pos[1]*px_per_meter_y])
    num_samples = int(np.linalg.norm(end_px - start_px)) * 2
    for t in np.linspace(0, 1,num_samples):
        point = (1-t)*start_px + t*end_px
        x, y = int(point[0]), int(point[1])
        h, w = obstacle_mask.shape
        if 0 <= y < h and 0 <= x < w:
            if obstacle_mask[y, x]:
                return False
    return True
