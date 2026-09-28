import math
import random
import time
from typing import List

import cv2


def image_to_tasks_coordinates(num_orders: List[int], length: float, width: float,
                               image_file: str,  max_num_amrs: int, seed: int, split_x: List[float],
                               split_y: List[float], distance_between_start_and_goal: float,
                               distance_start_positions: float, max_time_start_positions):
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

    if len(split_y) > 0:
        regions = split_coordinates_y(coordinates, split_y)
    elif len(split_x) > 0:
        regions = split_coordinates_x(coordinates, split_x)
    else:
        regions = [coordinates, coordinates]  # from coordinates to coordinates

    order_coordinates_all = []
    start_position_coordinates = []
    other_positions = []
    if len(coordinates) > 0:
        for no in num_orders:
            order_coordinates = []
            for i in range(no):
                k = (2 * no) / len(regions)
                index = int((i // k))
                start = random.choice(regions[index])
                while True:
                    end = random.choice(regions[index+1])
                    if math.dist(start, end) >= distance_between_start_and_goal:
                        order_coordinates.append((start, end))
                        break
            order_coordinates_all.append(order_coordinates)

        start_time = time.time()

        for i in range(max_num_amrs):
            while True and time.time() - start_time < max_time_start_positions:
                pos = random.choice(coordinates)
                pos_found = True
                for start_pos in start_position_coordinates:
                    if math.dist(pos, start_pos) <= distance_start_positions:
                        pos_found = False
                        break
                if pos_found is True:
                    start_position_coordinates.append(pos)
                    break
            if time.time() - start_time > max_time_start_positions:
                break

        if len(start_position_coordinates) != max_num_amrs:
            start_time = time.time()
            for i in range(max_num_amrs-len(start_position_coordinates)):
                while True and time.time() - start_time < max_time_start_positions:
                    pos = random.choice(no_endpoint_coordinates)
                    pos_found = True
                    for start_pos in start_position_coordinates:
                        if math.dist(pos, start_pos) <= distance_start_positions:
                            pos_found = False
                            break
                    for start_pos in other_positions:
                        if math.dist(pos, start_pos) <= distance_start_positions:
                            pos_found = False
                            break
                    if pos_found is True:
                        other_positions.append(pos)
                        break
                if time.time() - start_time > max_time_start_positions:
                    break

    return order_coordinates_all, start_position_coordinates, other_positions, gray_placing


def split_coordinates_y(coordinate_list, split_y: List[float]):
    list_regions = [[] for _ in range(len(split_y) + 1)]
    for coord in coordinate_list:
        y = coord[1]
        placed = False
        for idx, boundary in enumerate(split_y):
            if y < boundary:
                list_regions[idx].append(coord)
                placed = True
                break
        if not placed:
            list_regions[-1].append(coord)
    return list_regions


def split_coordinates_x(coordinate_list, split_x: List[float]):
    list_regions = [[] for _ in range(len(split_x) + 1)]
    for coord in coordinate_list:
        x = coord[0]
        placed = False
        for idx, boundary in enumerate(split_x):
            if x < boundary:
                list_regions[idx].append(coord)
                placed = True
                break
        if not placed:
            list_regions[-1].append(coord)
    return list_regions
