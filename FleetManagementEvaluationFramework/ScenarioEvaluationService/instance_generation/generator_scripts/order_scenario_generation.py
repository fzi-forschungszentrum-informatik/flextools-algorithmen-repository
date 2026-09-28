import json
import logging
from typing import List, Tuple
import datetime
import math
import log_config.config

import cv2
import numpy as np

from data.models import Dimension, NewOrderInfo, OrderStatus
from methods.serialization import serialize_json

logger = logging.getLogger(log_config.config.LOGGER_NAME)


def generate_order_scenario(graph, number_orders: int,
                            order_coordinates: List[Tuple[Tuple[float, float], Tuple[float, float]]], file_name: str,
                            layout_id: str, pickup_time: int, dropoff_time : int, task_frequence: float, timestep: int,
                            image_file: str, length: float, width: float, gray_placing: bool = True):
    order_list = []
    timestamp = 0

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
            return 140 < pixel < 180  # Grau-Bereich
        return False

    reference_datetime = datetime.datetime.now().replace(microsecond=0)

    for i in range(number_orders):
        publish_time = reference_datetime + datetime.timedelta(
            seconds=int(math.ceil(timestamp))) + datetime.timedelta(days=1000)
        start_time = publish_time
        due_time = start_time + datetime.timedelta(days=1)
        coordinate_pickup = order_coordinates[i][0]
        coordinate_dropoff = order_coordinates[i][1]

        closest_node_pickup = (None, np.inf)
        closest_node_dropoff = (None, np.inf)
        for node in graph.nodes():
            if not is_gray_area(node) and gray_placing is True:
                continue
            if math.dist(coordinate_pickup, node) < closest_node_pickup[1]:
                closest_node_pickup = (node, math.dist(coordinate_pickup, node))
            if math.dist(coordinate_dropoff, node) < closest_node_dropoff[1]:
                closest_node_dropoff = (node, math.dist(coordinate_dropoff, node))
        dimension = Dimension(x=30, y=30, z=20, weight=2.5)
        order_list.append(NewOrderInfo(orderId=str(i + 1),
                                       sourceId=f'N_{round(closest_node_pickup[0][0], 2)}_{round(closest_node_pickup[0][1], 2)}',
                                       sinkId=f'N_{round(closest_node_dropoff[0][0], 2)}_{round(closest_node_dropoff[0][1], 2)}',
                                       startTime=start_time, dueTime=due_time, publishTime=publish_time,
                                       layoutId=layout_id,
                                       pickupTime=pickup_time, dropoffTime=dropoff_time, dimension=dimension,
                                       status=OrderStatus.NEW))
        timestamp += timestep / task_frequence

    data_json = json.dumps(order_list, indent=4, default=lambda o: serialize_json(o))
    with open(file_name, 'w') as f:
        f.write(data_json)
    logger.info(f'Order scenario {file_name} finish generated with {number_orders} orders!')
    return


