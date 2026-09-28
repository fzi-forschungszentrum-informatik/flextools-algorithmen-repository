import heapq

import time
import logging

import config.config_file
from config.config_file import MAX_A_STAR_TIME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic


logger = logging.getLogger(config.config_file.LOGGER_NAME)


class AStar(LowLevelSearchInterface):

    def __init__(self, graph: ExtendedGraph, layout_id: str, start: str, goal: str, heuristic: Heuristic, vio_cons,
                 has_inf, constraints=None, time_shift=0):
        super().__init__()
        self.graph = graph.graph
        self.start = start
        self.goal = goal
        self.number_of_agents = len(self.start)
        self.constraints = constraints
        self.heuristic_values = heuristic.heuristic_costs_to_goal(graph.graph, goal, layout_id)

        self.violates_constraints = vio_cons
        self.has_infinite_interval = has_inf

        self.expanded_nodes = 0
        self.time_shift = time_shift

    def compute_path(self):
        """
        :param: parameter initialized over init
        :return: Computed path with constraints for multi_agent_path_planning
        """
        # Initialize Open set with start node
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time

        open_set = []
        path = []
        heapq.heappush(open_set, (0 + (self.heuristic_values[self.start]), 0, self.start, path))
        # (f = g + h, g, position, path)
        visited = set()

        while open_set and round(elapsed) < MAX_A_STAR_TIME:  # While open set includes elements
            self.expanded_nodes += 1

            (f, g, current, path) = heapq.heappop(open_set)  # Get node with the minimal costs f = g + h

            if self.violates_constraints(current, g):
                logger.info(f'Error: Start nodes {current} violates constraints at {g}'
                            f' it follows path planning problem not solvable')
                return None, None, self.expanded_nodes
            if current == self.goal:  # Check if goal reached
                if g == 0:
                    if not self.violates_constraints(current, 1) and not self.has_infinite_interval(location=current,
                                                                                                    start_time=1):
                        return path + [current], 1, self.expanded_nodes
                else:
                    if not self.violates_constraints(current, g) and not self.has_infinite_interval(location=current,
                                                                                                    start_time=g):
                        return path + [current], g, self. expanded_nodes

            if (current, g) in visited:  # Check if node for the time point g already visited
                continue
            visited.add((current, g))  # Add node with the time point g to the visited node set

            neighbors = self.graph.get_neighbors(current)  # get neighbors of the investigated node
            neighbors.insert(0, current)  # add current node also to the neighbor set, because amr can also do nothing
            for neighbor in neighbors:
                if neighbor == current:  # if the current node would be investigated
                    if (self.violates_constraints(neighbor, g+1) or
                            self.has_infinite_interval(location=neighbor, start_time=g+1)):
                        continue  # The current node is for the next timestep in constraints
                    heapq.heappush(open_set, (g + 1 + (self.heuristic_values[neighbor]),
                                              g + 1, neighbor, path + [current]))
                    # Add current node for the next timestamp in open list
                else:  # else for neighbors
                    t = (self.graph.value(current, neighbor) * (1/config.config_file.DURATION_EDGE))
                    if (self.violates_constraints(neighbor, g+t) or
                            self.violates_constraints((current, neighbor), g) or
                            self.violates_constraints((neighbor, current), g) or
                            self.has_infinite_interval(location=neighbor, start_time=g+t)):
                        continue  # if constraints are violated
                    heapq.heappush(open_set, (g + t + (self.heuristic_values[neighbor]), g + t, neighbor,
                                                    path + [current]))

            elapsed = time.monotonic() - start_time
        logger.debug(f'Time finished current path: {path}')
        return None, None, self.expanded_nodes



