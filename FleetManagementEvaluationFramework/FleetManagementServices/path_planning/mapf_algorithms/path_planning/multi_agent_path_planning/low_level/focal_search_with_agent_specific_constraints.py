import heapq
import logging
import math
import time
from collections import defaultdict

import numpy as np
import config.config_file

from config.config_file import MAX_A_STAR_TIME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic


logger = logging.getLogger(config.config_file.LOGGER_NAME)


class FocalSearchDisjointSplitting(LowLevelSearchInterface):
    def __init__(self, graph: ExtendedGraph, layout_id: str, start: str, goal: str, constraints, heuristic: Heuristic, agent_id,
                 time_shift=0, goal_time=np.inf):
        super().__init__()
        self.h_time = 0
        self.graph = graph.graph
        self.start = start
        self.goal = goal
        self.goal_time = goal_time
        self.number_of_agents = len(self.start)
        self.constraints = constraints

        self.w_low = math.inf
        self.focal_heuristic = None
        self.paths = []
        self.open_list = []
        self.focal_list = []
        self.current_f_min_value = np.inf

        self.id_to_focal_costs = {}
        self.focal_id_counter = 0
        self.heuristic_values = heuristic.heuristic_costs_to_goal(graph, goal, layout_id)

        self.time_shift = time_shift
        self.agent_id = agent_id
        self.shift_constraints()
        self._build_constraint_index()

    def _build_constraint_index(self):
        self.constraint_index = defaultdict(list)
        for c in self.constraints:
            if len(c) == 2:
                loc, t = c
                agents = None
            elif len(c) == 3:
                loc, t, agents = c
            else:
                continue

            if isinstance(agents, (list, tuple, set)):
                agents = set(agents)
            elif agents is not None:
                agents = [agents]
            self.constraint_index[loc].append((t, agents))

        for loc in self.constraint_index:
            self.constraint_index[loc].sort(key=lambda x: x[0][0] if isinstance(x[0], tuple) else x[0])
        return

    def shift_constraints(self):
        if self.time_shift != 0:
            shifted = set()
            for c in self.constraints:
                if len(c) == 3:
                    el, t, ag = c
                    if isinstance(t, tuple):
                        shifted.add((el, (t[0] - self.time_shift, np.inf), ag))
                    else:
                        shifted.add((el, t - self.time_shift, ag))
                elif len(c) == 2:
                    el, t = c
                    if isinstance(t, tuple):
                        shifted.add((el, (t[0] - self.time_shift, np.inf)))
                    else:
                        shifted.add((el, t - self.time_shift))
                else:
                    shifted.add(c)
            self.constraints = shifted
        return

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
        # Initialize Open set with start node
        expanded_nodes = 0
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        # (f = g + h, g, position, path)
        elem = (0 + (self.heuristic_values[self.start] * (1 / config.config_file.DURATION_EDGE)), 0, self.start, [],
                self.focal_id_counter)
        heapq.heappush(self.open_list, elem)
        self.update_focal_list()

        visited = set()
        #########################################################################################################
        while self.open_list and round(elapsed) < MAX_A_STAR_TIME:  # While open set includes elements or in time
            self.focal_id_counter += 1
            expanded_nodes += 1
            focal_cost, f, g, current, path, f_id = heapq.heappop(self.focal_list)
            self.open_list.remove((f, g, current, path, f_id))
            self.id_to_focal_costs.pop(f_id, None)
            if self.goal_time is not np.inf:
                min_dist_to_goal = self.heuristic_values[current]*(1/config.config_file.DURATION_EDGE)
                if g + min_dist_to_goal > self.goal_time:
                    continue

            if len(self.open_list) > 0:
                if self.open_list[0][0] > self.current_f_min_value:
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()

            if self.violates_constraints(current, g): # Check if node don't violate constraint, important for start node
                logger.info(f'Error: Start nodes {current} violates constraints at {g}'
                            f' it follows path planning problem not solvable')
                return None, None, expanded_nodes
            if current == self.goal:  # Check if goal reached
                if self.goal_time != np.inf and g != self.goal_time:
                    continue
                if g == 0:
                    if not self.violates_constraints(current, 1):
                        return path + [current], 1, expanded_nodes
                else:
                    violates = self.violates_constraints(current, g)
                    if not violates:
                        if current in self.constraint_index:
                            for t, agents in self.constraint_index[current]:
                                if isinstance(t, (int, float)) and g < t:
                                    if agents is None or \
                                            (isinstance(agents, int) and agents == self.agent_id) or \
                                            (isinstance(agents, (list, set, tuple)) and self.agent_id in agents):
                                        violates = True
                                        break
                    if not violates:
                        return path + [current], g, expanded_nodes

            if (current, g) in visited:  # Check if node for the time point g already visited
                if len(self.focal_list) == 0 and len(self.open_list) > 0:
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()
                continue
            visited.add((current, g))  # Add node with the time point g to the visited node set
            neighbors = self.graph.get_neighbors(current)  # get neighbors of the investigated node
            neighbors.insert(0, current)  # add current node also to the neighbor set, because amr can also do nothing
            for neighbor in neighbors:
                heuristic_value = self.heuristic_values[neighbor] * (1 / config.config_file.DURATION_EDGE)
                if neighbor == current:  # if the current node would be investigated
                    if not self.violates_constraints(neighbor, g + 1):
                        next_g = g + 1
                        if self.goal_time != np.inf:
                            min_dist_to_goal = heuristic_value + next_g
                            if min_dist_to_goal > self.goal_time:
                                continue
                        elem = (g + 1 + heuristic_value,
                                g + 1, neighbor, path + [current], self.focal_id_counter)
                        heapq.heappush(self.open_list, elem)
                        if g + 1 + heuristic_value < self.current_f_min_value:
                            self.current_f_min_value = g + 1 + heuristic_value
                            self.update_focal_list()
                else:  # else for neighbors
                    edge_cost = (self.graph.value(current, neighbor)) * (1 / config.config_file.DURATION_EDGE)
                    if (not self.violates_constraints(neighbor, g + edge_cost) and
                            not self.violates_constraints(current, g, neighbor)):
                        next_g = g + edge_cost
                        if self.goal_time != np.inf:
                            min_dist_to_goal = heuristic_value + next_g
                            if min_dist_to_goal > self.goal_time:
                                continue
                        elem = (next_g + heuristic_value, next_g, neighbor, path + [current], self.focal_id_counter)
                        heapq.heappush(self.open_list, elem)
                        if g + edge_cost + heuristic_value < self.current_f_min_value:
                            self.current_f_min_value = g + edge_cost + heuristic_value
                            self.update_focal_list()
            elapsed = time.monotonic() - start_time
            if len(self.focal_list) == 0 and len(self.open_list) > 0:
                self.current_f_min_value = self.open_list[0][0]
                self.update_focal_list()

        return None, None, expanded_nodes


    def update_focal_list(self):
        self.focal_list = []
        # f_min_val = self.open_list[0][0]
        bound = self.w_low * self.current_f_min_value
        # (f = g + h, g, position, path)
        for elem in self.open_list:
            if elem[0] <= bound:
                if elem[4] not in self.id_to_focal_costs.keys():
                    combined = self.paths + [list(elem[3])]
                    self.id_to_focal_costs[elem[4]] = self.focal_heuristic(combined)
                heapq.heappush(self.focal_list,
                               (self.id_to_focal_costs[elem[4]], elem[0], elem[1], elem[2], elem[3], elem[4]))
        return

    def violates_constraints(self, node, time, prev_node=None):
        """
        optimized constraints checking
        """
        relevant = list(self.constraint_index.get(node, []))
        if prev_node is not None:
            relevant.extend(self.constraint_index.get((prev_node, node), []))
            relevant.extend(self.constraint_index.get((node, prev_node), []))

        for t, agents in relevant:
            if isinstance(t, tuple):
                if not (t[0] <= time < t[1]):
                    continue
            else:
                if t != time:
                    continue

            if agents is None:
                agent_list = None
            elif isinstance(agents, int):
                agent_list = [agents]
            else:
                agent_list = agents

            if agent_list is not None and self.agent_id not in agent_list:
                continue
            return True

        return False

