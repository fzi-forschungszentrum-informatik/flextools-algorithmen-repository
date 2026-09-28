import math
import cv2
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from skimage.draw import line

matplotlib.use("TkAgg")


def create_graph(length: float, width: float, distance_bet_nodes: float, image_file: str, min_s: float):
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)

    image_h, image_w = binary.shape

    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width
    min_distance_m = 0
    min_distance_s = min_s
    min_distance_px = int(min_distance_m * (px_per_meter_x + px_per_meter_y) / 2)

    inv_binary = cv2.bitwise_not(binary)
    dist_transform = cv2.distanceTransform(inv_binary, cv2.DIST_L2, 5)

    dx = distance_bet_nodes
    dy = distance_bet_nodes * math.sqrt(3) / 2

    G = nx.Graph()
    gray_nodes = []

    rows = int(width / dy)
    cols = int(length / dx)

    debug_img = cv2.cvtColor(binary.copy(), cv2.COLOR_GRAY2BGR)

    for row in range(rows):
        for col in range(cols):
            if row % 2 == 0:
                if col % 3 == 2:
                    continue
            elif row % 2 == 1:
                if col % 3 == 0:
                    continue
            x_m = col * dx + min_distance_s
            y_m = row * dy + min_distance_s
            if row % 2 == 1:
                x_m += dx / 2

            x_px = int(x_m * px_per_meter_x)
            y_px = int(y_m * px_per_meter_y)
            if 0 <= x_px < image_w and 0 <= y_px < image_h:
                if binary[y_px, x_px] == 255 and dist_transform[y_px, x_px] >= min_distance_px:
                    G.add_node((x_m, y_m))
                pixel_value = img[y_px, x_px]
                if 140 < pixel_value < 180:
                    gray_nodes.append((x_m, y_m))
    directions = [
        (dx, 0), (-dx, 0),
        (dx / 2, dy), (-dx / 2, dy),
        (dx / 2, -dy), (-dx / 2, -dy)
    ]
    for x_m, y_m in G.nodes:
        for dx_n, dy_n in directions:  # in meter
            neighbor = find_nearby_node((x_m + dx_n, y_m + dy_n), G.nodes)
            if neighbor:
                x1_px, y1_px = int(x_m * px_per_meter_x), int(y_m * px_per_meter_y)
                x2_px, y2_px = int(neighbor[0] * px_per_meter_x), int(neighbor[1] * px_per_meter_y)
                rr, cc = line(y1_px, x1_px, y2_px, x2_px)
                valid = all(0 <= r < image_h and 0 <= c < image_w and binary[r, c] == 255 for r, c in zip(rr, cc))

                color = (0, 255, 0) if valid else (0, 0, 255)
                for r, c in zip(rr, cc):
                    if 0 <= r < image_h and 0 <= c < image_w:
                        debug_img[r, c] = color

                if valid:
                    G.add_edge((x_m, y_m), neighbor)

    plt.figure(figsize=(12, 6))
    extent = [0, length, width, 0]
    plt.imshow(debug_img, cmap='gray', extent=extent)

    pos = {n: (n[0], n[1]) for n in G.nodes}
    normal_nodes = [n for n in G.nodes if n not in gray_nodes]

    nx.draw_networkx_nodes(G, pos=pos, nodelist=normal_nodes, node_size=5, node_color='red')
    nx.draw_networkx_nodes(G, pos=pos, nodelist=gray_nodes, node_size=5, node_color='blue')
    nx.draw_networkx_edges(G, pos=pos, edge_color='lime')
    plt.title(f"Hexagonal Grid Graph {distance_bet_nodes} Meter")
    plt.show()
    return G, gray_nodes, pos

def get_neighbors(x, y, skel):
    neighbors = [(x + dx, y + dy)
                 for dx in [-1, 0, 1]
                 for dy in [-1, 0, 1]
                 if not (dx == 0 and dy == 0)]
    return [(nx, ny) for nx, ny in neighbors
            if 0 <= nx < skel.shape[0] and 0 <= ny < skel.shape[1] and skel[nx, ny]]


def find_nearby_node(node, nodes, tol=1e-2):
    x0, y0 = node
    for x, y in nodes:
        if (x - x0)**2 + (y - y0)**2 < tol**2:
            return (x, y)
    return None
