from typing import List, Tuple
import copy
import logging

import numpy as np

from api.server_api_models import Token
from config.config_file import DURATION_EDGE, LOGGER_NAME
import config.config_file
from mapf_algorithms.collision_detection.detectors.collision_detection import detect_collision_earliest

logger = logging.getLogger(LOGGER_NAME)


def get_constraints_from_tokens(tokens: List[Token], amr_id: str, len_path: int = 0):
    """
    :param tokens: list of tokens, planned paths for other amr`s
    :param amr_id: current amr for path planning in coopeartive a star
    :param len_path: length of the current path in optimization
    :return: set of position and time range constraints based on the tokens
    """
    logger.info(f'Tokens to get Constraints: {tokens}, len current path: {len_path}')
    constraints = set()
    for token in tokens:
        if token.amrId == amr_id:
            continue
        path = token.tokens[min(len_path, len(token.tokens)-1):]
        for t, pos in enumerate(path):
            if t == (len(path) - 1):
                constraints.add((pos, (t*DURATION_EDGE, np.inf)))
            else:
                constraints.add((pos, (t*DURATION_EDGE, (t+1)*DURATION_EDGE)))
    return constraints


def check_is_problem_solvable(time, current_position, graph, tokens, goal):
    """
    :param time: current time point
    :param current_position: current position considered amr
    :param graph: extended graph object from the layout
    :param tokens: list of tokens, planned paths for other amr`s
    :param goal: target position to reach from the current node
    :return: delete last node of all tokens from all other amr's from the graph based on the time,
             which amr don`t move more and check is graph from the current node to the goal node still connected
    """
    graph_test = copy.deepcopy(graph)
    remove_node_list = []
    for token in tokens:
        if len(token) <= time:
            remove_node_list.append(token[-1])
    if current_position in remove_node_list or goal in remove_node_list:
        return True
    for node in remove_node_list:
        graph_test.remove_node(node)
    # check it exists a connection to the goal location from the current time point and location
    connected = graph_test.are_connected(current_position, goal)
    return connected


def remove_segment(path, segment):
    """
    :param path: List[str]
    :param segment: List[str]
    :return: Method to remove path segment of path
    """
    for i in range(0, (len(path)-len(segment)+1)):
        remove = True
        for j, item in enumerate(segment):
            if path[i+j] != item:
                remove = False
                break
        if remove is True:
            del path[i:i+len(segment)]
            return path
    return path


def find_cycle(path):
    """
    :param path: List[str]
    :return: Method to find cycles in path
    """
    cycles = []
    for i, item in enumerate(path):
        for j, item2 in enumerate(path[i+2:]):  # cycle length with a minimum of 2
            if item == item2:
                no_cycle = False
                for k in range(i+1, i+2+j):
                    if path[k] == item:
                        no_cycle = True
                        break
                if no_cycle is False:
                    cycles.append((i, j+i+1, path[i:j+i+3]))
    return cycles


def get_costs_for_path(way):
    """
    :param way: path
    :return: get costs of path with a secondary goal
    """
    path = copy.deepcopy(way)
    costs = (len(way) - 1) * 1
    if config.config_file.CBS_COST_FUNCTION_IMPROVEMENT is False:
        return costs
    else:
        for i, item in enumerate(path[:-1]):
            if item == path[i+1]:
                costs -= 0.001
        return costs

def get_interval_costs_for_path(way: List[Tuple[str, Tuple[float, float]]]):
    """
    :param way: path
    :return: get costs of path
    """
    if len(way) > 1:
        if way[-1][1][1] == np.inf:
            return way[-1][1][0] - way[0][1][0]
        else:
            return way[-1][1][1] - way[0][1][0]
    else:
        return 0


def get_interval_costs_for_path_one_dimensional(path: List[Tuple[str, Tuple[float, float]]]):
    """
    :param way: path
    :return: get costs of path
    """
    if len(path) > 1:
        return path[-1][1]
    else:
        return 0


def post_process_paths(ways: List[List[str]]):
    """
    Method at the moment not used
    :param ways: paths of the amr
    :return: paths without cycles if possible
    """
    fix_paths = copy.deepcopy(ways)
    paths = copy.deepcopy(ways)
    for path in paths:
        while 'Event' in path:
            path.remove('Event')
    for i, path in enumerate(paths):
        cycles = find_cycle(path)
        cycles.sort(key=lambda s: len(s[2]))
        for cycle in cycles:
            path_copy = copy.deepcopy(path)
            len_cycle = len(cycle)
            path = remove_segment(path, cycle[2])
            for j in range(len_cycle):
                path.insert(cycle[0], cycle[2][0])
            collisions = detect_collision_earliest(paths)
            if collisions is None:
                shift = 0
                for k, node in enumerate(fix_paths[i]):
                    if k == 0:
                        continue
                    if node == 'Event' and fix_paths[i][k-1] == path[k-1-shift]:
                        shift += 1
                        path.insert(k, 'Event')
                fix_paths[i] = copy.deepcopy(path)
            else:
                path = path_copy
    logger.info(f'Post-Process wit routes: {fix_paths}')
    return fix_paths
