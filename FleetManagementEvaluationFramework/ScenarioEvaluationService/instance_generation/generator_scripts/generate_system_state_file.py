import json
import logging
import math
from typing import List, Tuple
import log_config.config

import cv2
import numpy as np

from data.models import SystemStateFile, AMRPositionFile, BatteryStateFile
from methods.serialization import serialize_json

logger = logging.getLogger(log_config.config.LOGGER_NAME)


def generate_system_state_file_new(graph, number_amr: int, initial_locations: List[Tuple[float, float]],
                                   other_nodes: List[Tuple[float, float]], name_file: str, reach: int,
                                   image_file: str, length: float, width: float, gray_placing: bool = True):
    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    image_h, image_w = img.shape
    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width

    def is_gray_area(node):
        x_m, y_m = node
        x_px = int(x_m * px_per_meter_x)
        y_px = int(y_m * px_per_meter_y)
        if 0 <= x_px < image_w and 0 <= y_px < image_h:
            pixel = img[y_px, x_px]
            return 140 < pixel < 180
        return False

    system_state_list = []
    nodes = []
    for i in range(number_amr):
        if i < len(initial_locations):
            coordinate = initial_locations[i]
            closest_node = (None, np.inf)
            for node in graph.nodes():
                if not is_gray_area(node) and gray_placing is True:
                    continue
                if math.dist(coordinate, node) < closest_node[1] and node not in nodes:
                    closest_node = (node, math.dist(coordinate, node))
            nodes.append(closest_node[0])
            system_state_list.append(SystemStateFile(amr_id=str(i + 1),
                                                     last_node_id=f'N_{round(closest_node[0][0], 2)}_{round(closest_node[0][1], 2)}',
                                                     AMRPosition=AMRPositionFile(x=round(closest_node[0][0], 2),
                                                                                 y=round(closest_node[0][1], 2)),
                                                     BatteryState=BatteryStateFile(reach=reach)))
        else:
            coordinate = other_nodes[i-len(initial_locations)]
            closest_node = (None, np.inf)
            for node in graph.nodes():
                if math.dist(coordinate, node) < closest_node[1] and node not in nodes:
                    closest_node = (node, math.dist(coordinate, node))
            nodes.append(closest_node[0])
            _, x, y = closest_node[0].split("_")
            system_state_list.append(SystemStateFile(amr_id=str(i + 1),
                                                     last_node_id=f'N_{round(closest_node[0][0], 2)}_{round(closest_node[0][1], 2)}',
                                                     AMRPosition=AMRPositionFile(x=round(closest_node[0][0], 2),
                                                                                 y=round(closest_node[0][1], 2)),
                                                     BatteryState=BatteryStateFile(reach=reach)))
    data_json = json.dumps(system_state_list, indent=4, default=lambda o: serialize_json(o))
    with open(name_file, 'w') as f:
        f.write(data_json)
    logger.info(f'System state file {name_file} finish generated with {number_amr} AMR!')