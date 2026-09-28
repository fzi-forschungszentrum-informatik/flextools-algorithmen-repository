from typing import List
import logging
import heapq

from config.config_file import DURATION_EDGE, LOGGER_NAME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.path_planning_heuristic_interface import Heuristic
from interfaces.path_planning_interface import PathPlanning
from data.data_structures.graph import Graph
from mapf_algorithms.api_services.service_processing_functions import check_is_problem_solvable

logger = logging.getLogger(LOGGER_NAME)


class CooperativeAStar(PathPlanning):

    def path_planning(self, graph: ExtendedGraph, layout_id: str, start_node_ids: List[str], end_node_ids: List[str],
                      constraints, tokens, heuristic: Heuristic):
        """
        :param exgraph: extended Graph object
        :param layout_id: layout identification
        :param start_node_ids: start node list len one
        :param end_node_ids: end node list len one
        :param constraints: (t=range(0,x), node=N_y)
        :param tokens: list of tokens, path of other AMR's
        :param heuristic: heuristic interface to compute the heuristic distance to the goal, e.g. manhattan distance
        :return: [path], [cost of path]
        :algorithm: cooperative a star or prioritized path planning
        :additionally: Line 46 - 52: Check if problem is still solvable, after get a new node from the open set
        """
        # Check assumptions prioritized planning / cooperative a star
        if len(start_node_ids) > 1 or len(end_node_ids) > 1:
            logger.exception("Error: Cooperative A* algorithm can only compute shortest path for single agent with "
                             "paths from other agents as constraints")
            raise Exception("Error: Cooperative A* algorithm can only compute shortest path for single agent with "
                            "paths from other agents as constraints")
        start = start_node_ids[0]
        goal = end_node_ids[0]
        # Initialize heuristic values to the goal
        heuristic_values = heuristic.heuristic_costs_to_goal(graph.graph, goal, layout_id)

        # Start to compute path
        # Initialize Open set with start node
        generated_nodes = 1
        open_set = []
        heapq.heappush(open_set, (0 + heuristic_values[start], 0, start, []))
        # (f = g + h, g, position, path)
        visited = set()
        while open_set:  # While open set includes elements
            f, g, current, path = heapq.heappop(open_set)  # Get node with the minimal costs f
            if len(constraints) > 0:  # ADDITIONALLY TO A* #
                # If constraints exist, check if problem still solvable, with test is start and goal connected
                # with available nodes
                connected = check_is_problem_solvable(g, current, graph.graph, tokens, goal)
                if connected is False:
                    continue
            if current == goal:  # Check if goal reached
                return [path + [current]], [f], generated_nodes, 0, None  # path, costs
            if (current, g) in visited:  # Check if node for the time point g already visited
                continue
            visited.add((current, g))  # Add node with the time point g to the visited node set
            neighbors = graph.graph.get_neighbors(current)  # get neighbors of the investigated node
            neighbors.insert(0, current)  # add current node also to the neighbor set, because amr can also do nothing
            for neighbor in neighbors:
                if neighbor == current:  # if the current node would be investigated
                    constraint_satisfied = True
                    for item in constraints:
                        if item[0] == neighbor and (g+1) in item[1]:
                            constraint_satisfied = False
                            # The current node is for the next timestep not in node and edge constraints
                    if constraint_satisfied is True:
                        generated_nodes += 1
                        # Only if it is possible to reach the goal without violate constraints
                        heapq.heappush(open_set, (g + DURATION_EDGE + heuristic_values[neighbor],
                                       g + DURATION_EDGE, neighbor, path + [current]))
                else:  # else for neighbors
                    constraint_satisfied = True
                    for item in constraints:
                        if ((item[0] == neighbor and g + graph.graph.value(current, neighbor) in item[1]) or
                                (item[0] == (current, neighbor) and g in item[1])):
                            constraint_satisfied = False

                    if constraint_satisfied is True:
                        generated_nodes += 1
                        # Only if it is possible to reach the goal without violate constraints
                        heapq.heappush(open_set, (g + graph.graph.value(current, neighbor) + heuristic_values[neighbor],
                                                  g + graph.graph.value(current, neighbor), neighbor, path + [current]))
                        # Add neighbor node to open list
        return None, None, generated_nodes, 0, None


