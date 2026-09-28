import heapq
import logging
import math
import time

import numpy as np
import config.config_file

from config.config_file import MAX_A_STAR_TIME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic
from data.data_structures.graph import Graph


logger = logging.getLogger(config.config_file.LOGGER_NAME)


class FocalSearch(LowLevelSearchInterface):
    def __init__(self, graph: ExtendedGraph, layout_id: str, start: str, goal: str, heuristic: Heuristic, vio_cons,
                 has_inf):
        super().__init__()
        self.h_time = 0
        self.graph = graph.graph
        self.start = start
        self.goal = goal
        self.number_of_agents = len(self.start)

        self.w_low = math.inf
        self.focal_heuristic = None
        self.paths = []
        self.expanded_nodes = 0
        self.open_list = []
        self.focal_list = []
        self.current_f_min_value = np.inf

        self.id_to_focal_costs = {}
        self.focal_id_counter = 0

        self.heuristic_values = heuristic.heuristic_costs_to_goal(graph, goal, layout_id)

        self.violates_constraints = vio_cons
        self.has_infinite_interval = has_inf

    def init_focal(self, b_low, focal_heuristic, paths):
        self.w_low = b_low
        self.focal_heuristic = focal_heuristic
        self.paths = paths
        self.id_to_focal_costs = {}

    def compute_path(self):
        """
        :param: parameter initialized over init
        :return: Computed path with constraints for multi_agent_path_planning
        """
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        path = []
        # (f = g + h, g, position, path)
        elem = (0 + (self.heuristic_values[self.start] * (1 / config.config_file.DURATION_EDGE)),
                0, self.start, path, self.focal_id_counter)
        heapq.heappush(self.open_list, elem)
        self.update_focal_list()

        visited = set()

        while self.open_list and round(elapsed) < MAX_A_STAR_TIME:  # While open set includes elements
            self.focal_id_counter += 1
            self.expanded_nodes += 1
            focal_cost, f, g, current, path, f_id = heapq.heappop(self.focal_list)
            self.open_list.remove((f, g, current, path, f_id))
            self.id_to_focal_costs.pop(f_id, None)

            if len(self.open_list) > 0:
                if self.open_list[0][0] > self.current_f_min_value:
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()

            if self.violates_constraints(current, g):  # Check if node don't violate constraint
                logger.exception(f'Error: Start node violates constraints,'
                                 f' it follows path planning problem not solvable!')
                return None, None, self.expanded_nodes

            if current == self.goal:  # Check if goal reached
                if g == 0:
                    if (not self.violates_constraints(current, 1) and
                            not self.has_infinite_interval(current, start_time=1)):
                        return path + [current], 1, self.expanded_nodes
                else:
                    if not self.violates_constraints(current, g) and not self.has_infinite_interval(location=current,
                                                                                                    start_time=g):
                        return path + [current], g, self.expanded_nodes

            if (current, g) in visited:  # Check if node for the time point g already visited
                if len(self.focal_list) == 0 and len(self.open_list) > 0:
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()
                continue
            visited.add((current, g))  # Add node with the time point g to the visited node set

            neighbors = self.graph.get_neighbors(current)  # get neighbors of the investigated node
            neighbors.insert(0, current)  # add current node also to the neighbor set, because amr can also do nothing

            for neighbor in neighbors:
                if neighbor == current:  # if the current node would be investigated
                    if (self.violates_constraints(neighbor, g+1) or
                            self.has_infinite_interval(neighbor, start_time=g+1)):
                        continue  # The current node is for the next timestep not in constraints
                    elem = (g + 1 + self.heuristic_values[neighbor], g + 1, neighbor, path + [current],
                            self.focal_id_counter)
                    heapq.heappush(self.open_list, elem)
                    if (g + 1 + (self.heuristic_values[neighbor]*(1/config.config_file.DURATION_EDGE))
                            < self.current_f_min_value):
                        self.current_f_min_value = (g + 1 + (self.heuristic_values[neighbor] *
                                                             (1/config.config_file.DURATION_EDGE)))
                        self.update_focal_list()
                else:  # else for neighbors
                    t = (self.graph.value(current, neighbor))*(1/config.config_file.DURATION_EDGE)
                    if (self.violates_constraints(neighbor, g + t) or
                            self.violates_constraints((current, neighbor), g) or
                            self.violates_constraints((neighbor, current), g) or
                            self.has_infinite_interval(neighbor, start_time=g+t)):
                        continue  # if no constraints are violated
                    elem = (g + (self.graph.value(current, neighbor) * (1 / config.config_file.DURATION_EDGE)) +
                                (self.heuristic_values[neighbor] * (1 / config.config_file.DURATION_EDGE)),
                                 g + (self.graph.value(current, neighbor) * (1 / config.config_file.DURATION_EDGE)),
                                 neighbor, path + [current], self.focal_id_counter)
                    heapq.heappush(self.open_list, elem)

                    if ((g + (self.graph.value(current, neighbor) * (1 / config.config_file.DURATION_EDGE)) +
                            (self.heuristic_values[neighbor] * (1 / config.config_file.DURATION_EDGE))) <
                            self.current_f_min_value):
                        self.current_f_min_value = (g + (self.graph.value(current, neighbor) *
                                                         (1 / config.config_file.DURATION_EDGE)) +
                                                    (self.heuristic_values[neighbor] *
                                                     (1 / config.config_file.DURATION_EDGE)))
                        self.update_focal_list()

            elapsed = time.monotonic() - start_time

            if len(self.focal_list) == 0 and len(self.open_list) > 0:
                self.current_f_min_value = self.open_list[0][0]
                self.update_focal_list()

        logger.debug(f'Time finished current path: {path}')
        return None, None, self.expanded_nodes

    def update_focal_list(self):
        self.focal_list = []
        bound = self.w_low * self.current_f_min_value
        # (f = g + h, g, position, path)
        for elem in self.open_list:
            if elem[0] <= bound:
                if elem[4] not in self.id_to_focal_costs.keys():
                    combined = self.paths + [list(elem[3])]
                    self.id_to_focal_costs[elem[4]] = self.focal_heuristic(combined)
                heapq.heappush(self.focal_list, (self.id_to_focal_costs[elem[4]], elem[0], elem[1],
                                                 elem[2], elem[3], elem[4]))
        return
