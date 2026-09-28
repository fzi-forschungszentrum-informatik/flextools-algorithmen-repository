import copy
import math
import random
from typing import List

import cv2

from configs_scenario_generation.warehouse_35x21_config import DISTANCE_BETWEEN_START_AND_GOAL


def image_to_mapf_coordinates(number_paths: List[int], length: float, width: float,
                              image_file: str, seed: int, number_mapf_instances):
    random.seed(seed)
    gray_placing = True

    img = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
    _, binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)

    image_h, image_w = binary.shape

    px_per_meter_x = image_w / length
    px_per_meter_y = image_h / width

    coordinates = []
    no_endpoint_coordinates = []

    for y_px in range(image_h):
        for x_px in range(image_w):
            pixel_value = img[y_px, x_px]
            if 140 < pixel_value < 180:
                x_m = x_px / px_per_meter_x
                y_m = y_px / px_per_meter_y
                coordinates.append((x_m, y_m))
            elif pixel_value == 255:
                x_m = x_px / px_per_meter_x
                y_m = y_px / px_per_meter_y
                no_endpoint_coordinates.append((x_m, y_m))

    if len(coordinates) == 0 and len(no_endpoint_coordinates) > 0:
        gray_placing = False
        coordinates = no_endpoint_coordinates

    coordinates_list = []
    if len(coordinates) > 0:
        for j in range(number_mapf_instances):
            all_coordinates = copy.deepcopy(coordinates)
            for n_p in number_paths:
                order_coordinates = []
                for i in range(n_p):
                    start = random.choice(all_coordinates)
                    while True:
                        end = random.choice(all_coordinates)
                        if math.dist(start, end) >= DISTANCE_BETWEEN_START_AND_GOAL:
                            order_coordinates.append((start, end))
                            break
                coordinates_list.append(order_coordinates)
    return coordinates_list, gray_placing
