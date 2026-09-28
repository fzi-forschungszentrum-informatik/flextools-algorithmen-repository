import cv2
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from skimage.draw import line

matplotlib.use("TkAgg")


def create_graph(length: float, width: float, distance_bet_nodes: float, image_file: str, min_s: float,
                 rad_amr: float = 0):
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    obstacle_mask = (binary == 0)

    image_h, image_w = binary.shape

    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width
    min_distance_m = rad_amr
    min_distance_s = max(min_s, rad_amr)
    min_distance_px = int(min_distance_m * min(px_per_meter_x, px_per_meter_y))

    inv_binary = cv2.bitwise_not(binary)

    coords = np.argwhere(binary == 255)

    start_y_px, start_x_px = coords[0]
    end_y_px, end_x_px = coords[-1]

    start_x_m = start_x_px / px_per_meter_x
    start_y_m = start_y_px / px_per_meter_y

    end_x_m = end_x_px / px_per_meter_x
    end_y_m = end_y_px / px_per_meter_y

    G = nx.Graph()
    gray_nodes = []
    xs_m = np.arange(start_x_m + min_distance_s, length, distance_bet_nodes)
    ys_m = np.arange(start_y_m + min_distance_s, width, distance_bet_nodes)

    for y_m in ys_m:
        for x_m in xs_m:
            x_px = int(x_m * px_per_meter_x)
            y_px = int(y_m * px_per_meter_y)
            if 0 <= x_px < image_w and 0 <= y_px < image_h:
                if binary[y_px, x_px] == 255 and distance_to_nearest_obstacle((y_px, x_px), obstacle_mask) >= min_distance_px:
                    G.add_node((x_m, y_m))
                pixel_value = img[y_px, x_px]
                if 140 < pixel_value < 180 and distance_to_nearest_obstacle((y_px, x_px), obstacle_mask) >= min_distance_px:
                    gray_nodes.append((x_m, y_m))

    for x_m, y_m in G.nodes:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (x_m + dx * distance_bet_nodes, y_m + dy * distance_bet_nodes)
            if neighbor in G.nodes:
                x1_px, y1_px = int(x_m * px_per_meter_x), int(y_m * px_per_meter_y)
                x2_px, y2_px = int(neighbor[0] * px_per_meter_x), int(neighbor[1] * px_per_meter_y)
                rr, cc = line(y1_px, x1_px, y2_px, x2_px)
                if all(0 <= r < image_h and 0 <= c < image_w and binary[r, c] == 255 for r, c in zip(rr, cc)):
                    G.add_edge((x_m, y_m), neighbor)

    plt.figure(figsize=(12, 6))
    extent = [0, length, width, 0]
    plt.imshow(binary, cmap='gray', extent=extent)

    pos = {n: (n[0], n[1]) for n in G.nodes}
    normal_nodes = [n for n in G.nodes if n not in gray_nodes]

    nx.draw_networkx_nodes(G, pos=pos, nodelist=normal_nodes, node_size=5, node_color='red')
    nx.draw_networkx_nodes(G, pos=pos, nodelist=gray_nodes, node_size=5, node_color='blue')
    nx.draw_networkx_edges(G, pos=pos, edge_color='lime')
    plt.title(f"Quadratic Grid Graph {distance_bet_nodes} Meter")
    plt.show()
    return G, gray_nodes, pos


def distance_to_nearest_obstacle(point, obstacle_mask):
    """
    point: (x, y)
    obstacle_mask: 2D numpy array, 1=obstacle, 0=free
    returns distance in pixels/meters
    """
    y, x = point
    ys, xs = np.where(obstacle_mask == 1)
    if len(xs) == 0:
        return np.inf
    distances = np.sqrt((xs - x)**2 + (ys - y)**2)
    return np.min(distances)


def get_neighbors(x, y, skel):
    neighbors = [(x + dx, y + dy)
                 for dx in [-1, 0, 1]
                 for dy in [-1, 0, 1]
                 if not (dx == 0 and dy == 0)]
    return [(nx, ny) for nx, ny in neighbors
            if 0 <= nx < skel.shape[0] and 0 <= ny < skel.shape[1] and skel[nx, ny]]

