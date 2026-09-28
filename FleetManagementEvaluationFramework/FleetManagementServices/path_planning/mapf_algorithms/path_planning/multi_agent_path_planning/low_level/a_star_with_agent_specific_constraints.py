import heapq
import logging
import time
from collections import defaultdict

import numpy as np
import config.config_file

from config.config_file import MAX_A_STAR_TIME
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic
from data.data_structures.graph import Graph


logger = logging.getLogger(config.config_file.LOGGER_NAME)


class AStarDisjointSplitting(LowLevelSearchInterface):

    def __init__(self, graph: Graph, layout_id: str, start: str, goal: str, constraints, heuristic: Heuristic,
                 agent_id, time_shift=0, goal_time=np.inf):
        super().__init__()
        self.graph = graph
        self.start = start
        self.goal = goal
        self.goal_time = goal_time
        self.number_of_agents = len(self.start)
        self.constraints = constraints
        self.heuristic_values = heuristic.heuristic_costs_to_goal(graph, goal, layout_id)
        self.time_shift = time_shift
        self.agent_id = agent_id
        self.expanded_nodes = 0
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

    def compute_path(self):
        """
        :param: parameter initialized over init
        :return: Computed path with constraints for multi_agent_path_planning
        """
        # Initialize Open set with start node
        path = []
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        open_set = []
        # print('Constraints', self.constraints, self.time_shift, 'for Agent ', self.agent_id)
        heapq.heappush(open_set, (0 + (self.heuristic_values[self.start]*(1/config.config_file.DURATION_EDGE)), 0, self.start, []))
        # (f = g + h, g, position, path)
        visited = set()

        while open_set and round(elapsed) < MAX_A_STAR_TIME:  # While open set includes elements
            self.expanded_nodes += 1

            (f, g, current, path) = heapq.heappop(open_set)  # Get node with the minimal costs f = g + h
            if self.goal_time is not np.inf:
                min_dist_to_goal = self.heuristic_values[current]*(1/config.config_file.DURATION_EDGE)
                if g + min_dist_to_goal > self.goal_time:
                    continue

            if self.violates_constraints(current, g):  # Check if node don't violate constraint
                logger.info(f'Error: Start nodes {current} violates constraints at {g}'
                            f' it follows path planning problem not solvable')
                return None, None, self.expanded_nodes

            if current == self.goal:  # Check if goal reached
                if self.goal_time != np.inf and g != self.goal_time:
                    continue
                if g == 0:
                    if not self.violates_constraints(current, 1):
                        return path + [current], 1, self.expanded_nodes
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
                        return path + [current], g, self.expanded_nodes

            if (current, g) in visited:  # Check if node for the time point g already visited
                continue
            visited.add((current, g))  # Add node with the time point g to the visited node set
            neighbors = self.graph.get_neighbors(current)  # get neighbors of the investigated node
            neighbors.insert(0, current)  # add current node also to the neighbor set, because amr can also do nothing
            for neighbor in neighbors:
                heuristic_value = self.heuristic_values[neighbor]*(1/config.config_file.DURATION_EDGE)
                if neighbor == current:  # if the current node would be investigated
                    if not self.violates_constraints(neighbor, g+1):
                        next_g = g + 1
                        if self.goal_time != np.inf:
                            min_dist_to_goal = heuristic_value + next_g
                            if min_dist_to_goal > self.goal_time:
                                continue
                        heapq.heappush(open_set, ((g + 1 + heuristic_value), next_g, neighbor, path + [current]))

                    # Add current node for the next timestamp in open list
                else:  # else for neighbors
                    edge_cost = (self.graph.value(current, neighbor))*(1/config.config_file.DURATION_EDGE)
                    if (not self.violates_constraints(neighbor, g + edge_cost) and not self.violates_constraints(current, g, neighbor)):
                        next_g = g + edge_cost
                        if self.goal_time != np.inf:
                            min_dist_to_goal = heuristic_value + next_g
                            if min_dist_to_goal > self.goal_time:
                                continue
                        heapq.heappush(open_set, (g + edge_cost+heuristic_value, next_g, neighbor, path + [current]))
                        # Add neighbor node to open list
            elapsed = time.monotonic() - start_time
        return None, None, self.expanded_nodes

    def violates_constraints(self, node, time, prev_node=None):
        """
        optimized constraints checking with symmetrically for edges
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




