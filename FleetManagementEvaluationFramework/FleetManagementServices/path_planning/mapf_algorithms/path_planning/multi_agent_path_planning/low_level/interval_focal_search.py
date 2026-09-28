import heapq
import math
import time
import logging
from collections.abc import Callable

import numpy as np

from config.config_file import LOGGER_NAME

from config.config_file import MAX_A_STAR_TIME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic

logger = logging.getLogger(LOGGER_NAME)


class IntervalFocalSearch(LowLevelSearchInterface):

    def __init__(self, exgraph: ExtendedGraph, layout_id: str, start: str, goal: str,
                 heuristic: Heuristic, vio_cons: Callable, has_inf: Callable):
        super().__init__()
        # Problem Data ################################
        self.extended_graph = exgraph
        self.start = start
        self.goal = goal
        self.heuristic_values = heuristic.heuristic_costs_to_goal(exgraph.graph, goal, layout_id)

        # Runtime Data ################################
        self.current_f_min_value = np.inf
        self.expanded_nodes = 0
        self.open_list = []

        # New fields for ID management & caching ######
        self.focal_id_counter = 0
        self.h_time = 0
        self.id_to_focal_costs = {}

        # Focal values ################################
        self.focal_list = []
        self.w_low = math.inf
        self.focal_heuristic = None
        self.other_paths = []

        # Constraint verification Functions ###########
        self.violates_constraints = vio_cons
        self.has_infinite_interval = has_inf
        #################################################################

    def init_focal(self, b_low, focal_heuristic, other_paths):
        """
        :param b_low: focal bound value
        :param focal_heuristic: used focal heuristic
        :param other_paths:
        -> initialises the necessary values for the focal list
        """
        self.w_low = b_low
        self.focal_heuristic = focal_heuristic
        self.other_paths = other_paths
        self.id_to_focal_costs = {}

    def compute_path(self):
        self.expanded_nodes = 0
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        f_id = self.focal_id_counter
        f = self.heuristic_values[self.start]

        #######################################################
        # elements in the open list look like this:
        # (f = heuristics costs to end ,
        #  g = costs at current node,
        #  current_node, current path,
        #  focal_id to make computation faster )
        ########################################################
        # create first element and push to list

        # the start was not valid the problem is not solvable
        if self.violates_constraints(self.start, (0, 0.001)):
            logger.info(f'Error: Start node violates constraints, path planning problem not solvable!')
            return None, None, self.expanded_nodes

        elem = (f, 0, self.start, [(self.start, (0, 0.001))], f_id)
        heapq.heappush(self.open_list, elem)
        self.update_focal_list()

        # dict to save all visited nodes and their current optimal value
        visited = dict()

        while self.open_list and round(elapsed) < MAX_A_STAR_TIME:
            self.focal_id_counter += 1
            self.expanded_nodes += 1
            ############################################################################################################
            # get the next node from focal search
            focal_cost, f, g, current, path, f_id = heapq.heappop(self.focal_list)
            # remove the node from the open list
            self.open_list.remove((f, g, current, path, f_id))
            # remove the focal costs from the dict since the id does no longer exist
            self.id_to_focal_costs.pop(f_id, None)
            ############################################################################################################
            # this is for assuring the focal invariant, but this should not happen
            if len(self.open_list) > 0 and self.open_list[0][0] > self.current_f_min_value:
                self.current_f_min_value = self.open_list[0][0]
                self.update_focal_list()

            ############################################################################################################
            if current == self.goal:
                # the current-node is the goal node
                if g == 0:
                    # if constraints are not violated the AMR stays on the same node
                    if not self.violates_constraints(current, (0, np.inf)) and not self.has_infinite_interval(current, 0):
                        return [(current, (0, np.inf))], 0, self.expanded_nodes
                else:
                    # check if constraints are violated on the edge and on the end node
                    if (not self.violates_constraints(current, (g, np.inf)) and
                            not self.has_infinite_interval(current, g)):
                        return path + [(current, (g, np.inf))], g, self.expanded_nodes

            ############################################################################################################
            if current in visited and visited[current] <= g:
                # skip, there is an already known better way
                if len(self.focal_list) == 0 and len(self.open_list) > 0:
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()
                continue
            visited[current] = g
            ############################################################################################################
            # add the current node to the visited nodes the value may need to be changed
            neighbors = self.extended_graph.graph.get_neighbors(current)
            # the system should be allowed to stay on a node if the constraints are not violated
            neighbors.insert(0, current)
            ############################################################################################################
            # expand the neighbouring nodes
            for neighbor in neighbors:
                ########################################################################################################
                # if the expanded node is the current node add staying on the node as possibility
                if neighbor == current:
                    f_id = self.focal_id_counter
                    if len(path) > 0:
                        # if the current node has already a path leading there, elongate the last nodes time interval
                        # copies the current path and changes last node, removes side effects
                        node, (start, end) = path[-1]
                        cp_path = path[:-1] + [(node, (start, end + 1))]
                        # check if the current node and its interval elongated by one would violate constraints
                        if self.violates_constraints(current, (start, end + 1)) or self.has_infinite_interval(current,
                                                                                                              end + 1):
                            continue
                        elem = (g + 1 + self.heuristic_values[neighbor], g + 1, neighbor, cp_path, f_id)
                    else:
                        if self.violates_constraints(current, (0, 1.001)) or self.has_infinite_interval(current, 0):
                            continue
                        # if there is not a path, start with the current node
                        elem = (g + 1 + self.heuristic_values[neighbor], g + 1, neighbor, [(current, (0, 1.001))], f_id)

                    # push to open list and update the id counter
                    self.focal_id_counter += 1
                    heapq.heappush(self.open_list, elem)
                    # if minimal focal value changed, focal and the minimal focal value must be updated
                    temp = g + 1 + (self.heuristic_values[neighbor])
                    if temp < self.current_f_min_value:
                        self.current_f_min_value = temp
                        self.update_focal_list()
                else:
                    t = self.extended_graph.graph.value(current, neighbor)  # driving time t from current to neighbour
                    # visiting interval on neighbour
                    g_new = g + t
                    interval = (g_new, g_new + 0.001)
                    edge_id = self.extended_graph.get_edge_id([current, neighbor])
                    if (self.violates_constraints(neighbor, interval) or self.violates_constraints(edge_id, (g, g+t)) or
                            self.has_infinite_interval(neighbor, g_new)):
                        continue
                    f_id = self.focal_id_counter
                    self.focal_id_counter += 1
                    # create expanded nodes element in open list
                    f_val = g_new + (self.heuristic_values[neighbor])
                    new_path = path + [(neighbor, (g, g + 0.001))]
                    elem = (f_val, g_new, neighbor, new_path, f_id)
                    heapq.heappush(self.open_list, elem)
                    # if minimal focal value changed, focal and the minimal focal value must be updated
                    if f_val < self.current_f_min_value:
                        self.current_f_min_value = f_val
                        self.update_focal_list()

            ############################################################################################################
            elapsed = time.monotonic() - start_time
            ############################################################################################################
            if len(self.focal_list) == 0 and len(self.open_list) > 0:
                self.current_f_min_value = self.open_list[0][0]
                self.update_focal_list()

        return None, None, self.expanded_nodes

    def update_focal_list(self):
        self.focal_list = []
        bound = self.w_low * self.current_f_min_value

        for elem in self.open_list:
            f_val, g, pos, path, f_id = elem
            if f_val <= bound:
                if f_id not in self.id_to_focal_costs:
                    combined = self.other_paths + [list(path)]
                    start = time.monotonic()
                    self.id_to_focal_costs[f_id] = self.focal_heuristic(combined)
                    self.h_time += time.monotonic() - start

                focal_cost = self.id_to_focal_costs[f_id]
                heapq.heappush(self.focal_list, (focal_cost, f_val, g, pos, path, f_id))


