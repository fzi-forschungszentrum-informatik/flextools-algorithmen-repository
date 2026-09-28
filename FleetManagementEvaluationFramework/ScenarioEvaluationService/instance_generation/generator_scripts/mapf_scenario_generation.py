import json
from typing import List, Tuple
import math
import cv2
import networkx as nx
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors

from methods.serialization import serialize_json


def generate_mapf_scenario(graph, mapf_coordinates: List[List[Tuple[Tuple[float, float], Tuple[float, float]]]],
                           file_name: str, image_file: str, length: float, width: float, gray_placing=True,
                           visualize=False):

    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    image_h, image_w = img.shape
    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width

    def is_gray_area(node):
        """Check if node lies on a gray area in the layout."""
        x_m, y_m = node
        x_px = int(x_m * px_per_meter_x)
        y_px = int(y_m * px_per_meter_y)
        if 0 <= x_px < image_w and 0 <= y_px < image_h:
            pixel = img[y_px, x_px]
            return 140 < pixel < 180
        return False

    mapf_instance = []
    for coordinates in mapf_coordinates:
        start_points = []
        end_points = []
        for i in range(len(coordinates)):
            coordinate_start = coordinates[i][0]
            coordinate_goal = coordinates[i][1]
            closest_node_start = (None, np.inf)
            closest_node_goal = (None, np.inf)
            for node in graph.nodes():
                if not is_gray_area(node) and gray_placing is True:
                    continue
                if math.dist(coordinate_start, node) < closest_node_start[1]:
                    if node not in start_points:
                        closest_node_start = (node, math.dist(coordinate_start, node))
                if math.dist(coordinate_goal, node) < closest_node_goal[1]:
                    if node not in end_points:
                        closest_node_goal = (node, math.dist(coordinate_goal, node))
            start_points.append(f'N_{round(closest_node_start[0][0], 2)}_{round(closest_node_start[0][1], 2)}')
            end_points.append(f'N_{round(closest_node_goal[0][0], 2)}_{round(closest_node_goal[0][1], 2)}')
        mapf_dict = {"start_nodes": start_points, "end_nodes": end_points}
        mapf_instance.append(mapf_dict)
        if visualize:
            img_color = cv2.imread(image_file)
            img_color = cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB)
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(img_color)
            pos_px = {}
            for n in graph.nodes():
                x_m, y_m = n
                x_px = x_m * px_per_meter_x
                y_px = y_m * px_per_meter_y
                pos_px[n] = (x_px, y_px)
            nx.draw_networkx(
                graph,
                pos=pos_px,
                ax=ax,
                node_size=20,
                node_color="green",
                edge_color="black",
                with_labels=False
            )
            colors = list(mcolors.TABLEAU_COLORS.values())
            if len(start_points) > len(colors):
                colors = list(mcolors.CSS4_COLORS.values())

            for idx, (s, g) in enumerate(zip(start_points, end_points)):
                if s is None or g is None:
                    continue

                color = colors[idx % len(colors)]

                nx.draw_networkx_nodes(graph, pos_px,
                                       nodelist=[s],
                                       node_size=50,
                                       node_color=color,
                                       edgecolors="black")

                nx.draw_networkx_nodes(graph, pos_px,
                                       nodelist=[g],
                                       node_size=50,
                                       node_color=color,
                                       node_shape="s",
                                       edgecolors="black")

                try:
                    path = nx.shortest_path(graph, s, g)
                except nx.NetworkXNoPath:
                    continue

                edges_path = list(zip(path[:-1], path[1:]))

                nx.draw_networkx_edges(
                    graph,
                    pos=pos_px,
                    edgelist=edges_path,
                    width=3,
                    edge_color=color
                )

            plt.title("Start-Goal MAPF Instance over Layout")
            plt.axis("off")
            plt.show()

        data_json = json.dumps(mapf_instance, indent=4, default=lambda o: serialize_json(o))
        with open(file_name, 'w') as f:
            f.write(data_json)
    return
