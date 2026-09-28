import heapq
import logging

import time


from config.config_file import LOGGER_NAME

import numpy as np

from config.config_file import MAX_A_STAR_TIME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic


logger = logging.getLogger(LOGGER_NAME)


class IntervalAStar(LowLevelSearchInterface):

    def __init__(self, exgraph: ExtendedGraph, layout_id: str, start: str, goal: str, heuristic: Heuristic, vio_cons,
                 has_inf, constraints=None):
        super().__init__()
        self.start = start
        self.goal = goal
        self.number_of_agents = len(self.start)
        self.heuristic_values = heuristic.heuristic_costs_to_goal(exgraph.graph, goal, layout_id)
        self.expanded_nodes = 0

        self.extended_graph = exgraph
        self._id_counter = 0
        ################################################################################################################
        # These are functions
        self.violates_constraints = vio_cons
        self.has_infinite_interval = has_inf

    def compute_path(self):
        """
        :param: parameter initialized over init
        :return: Computed path with constraints for multi_agent_path_planning
        """
        assert self.extended_graph is not None

        self.expanded_nodes = 0
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time

        ####################################################
        # Initialize Open set with start node
        ####################################################

        path = []
        open_set = []
        ##############################################################################################################
        # elements in the open set look like this:
        # (f = guessed remaining costs to end , g = costs at current node, current_node, current path )
        ##############################################################################################################
        heapq.heappush(open_set, (self.heuristic_values[self.start], 0, self.start, path, 0))
        visited = dict()

        ##############################################################################################################

        while open_set and round(elapsed) < MAX_A_STAR_TIME:  # While open set includes elements
            self.expanded_nodes += 1
            f, g, current, path, f_id = heapq.heappop(open_set)  # Get node with the minimal costs f = g + h
            ##########################################################################################################

            if self.violates_constraints(current, (g, g + 0.001)):
                logger.info(f'Error: Start node violates constraints, path planning problem not solvable!')
                return None, None, self.expanded_nodes
            #########################################################
            # check if the current found node is the goal node
            #########################################################
            if current == self.goal:
                if g == 0:
                    # if constraints are not violated the AMR stays on the same node
                    if not self.violates_constraints(current, (0, np.inf)) and not self.has_infinite_interval(current, 0):
                        return path + [(current, (0, np.inf))], 1, self.expanded_nodes
                else:
                    # if AMR first has to drive to the goal node
                    if (not self.violates_constraints(current, (g, np.inf))
                            and not self.has_infinite_interval(current, g)):
                        return path + [(current, (g, np.inf))], g, self.expanded_nodes
            ##########################################################################################################
            if current in visited and visited[current] <= g:  # Check if node for the time point g already visited
                # skip, there is an already known better way
                continue
            visited[current] = g  # Add node with the time point g to the visited node set
            neighbors = self.extended_graph.graph.get_neighbors(current)  # get neighbors of the investigated node
            neighbors.insert(0, current)  # add current node also to the neighbor set, because amr can also do nothing
            for neighbor in neighbors:
                if neighbor == current:
                    _id = self._id_counter
                    if len(path) > 0:
                        # if the current node has already a path leading there, elongate the last nodes time interval
                        # copies the current path and changes last node, removes side effects
                        node, (start, end) = path[-1]
                        cp_path = path[:-1] + [(node, (start, end + 1))]
                        # check if the current node and its interval elongated by one would violate constraints
                        if self.violates_constraints(current, (start, end + 1)) or self.has_infinite_interval(current,
                                                                                                              end + 1):
                            continue
                        elem = (g + 1 + self.heuristic_values[neighbor], g + 1, neighbor, cp_path, _id)
                    else:
                        # check if the current node and its interval elongated by one would violate constraints
                        if self.violates_constraints(current, (0, 1.001)) or self.has_infinite_interval(current, 0):
                            continue
                        # if there is not a path, start with the current node
                        elem = (g + 1 + self.heuristic_values[neighbor], g + 1, neighbor, [(current, (0, 1.001))], _id)
                    ##################################################################################################
                    heapq.heappush(open_set, elem)
                    self._id_counter += 1
                ######################################################################################################
                else:
                    # go over an edge
                    # driving time to next node
                    t = self.extended_graph.graph.value(current, neighbor)

                    g_new = g + t
                    interval = (g_new, g_new + 0.001)
                    edge_id = self.extended_graph.get_edge_id([current, neighbor])
                    if (self.violates_constraints(neighbor, interval) or self.violates_constraints(edge_id, (g, g+t)) or
                            self.has_infinite_interval(neighbor, g_new)):
                        continue
                    f_id = self._id_counter
                    f_val = g_new + self.heuristic_values[neighbor]
                    new_path = path + [(current, (g, g + 0.001))]
                    elem = (f_val, g_new, neighbor, new_path, f_id)
                    heapq.heappush(open_set, elem)
                    self._id_counter += 1

            ##########################################################################################################
            elapsed = time.monotonic() - start_time

        return None, None, self.expanded_nodes


