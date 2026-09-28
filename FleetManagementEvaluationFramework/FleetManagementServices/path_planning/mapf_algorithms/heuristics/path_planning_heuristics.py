import heapq

import numpy as np
import math

from config.config_file import EIG_ALPHA, EIG_BETA
from interfaces.path_planning_heuristic_interface import Heuristic


class HeuristicDijkstra(Heuristic):
    def heuristic_costs_to_goal(self, graph, goal, layout_id):
        """
        :param graph: Graph object
        :param goal: goal node id
        :param layout_id: layout identification
        :return: dictionary with the distance from each node in the graph to the goal location computed with
                 the dijkstra algorithm
        """
        # Use Dijkstra to build a shortest-path tree rooted at the goal location
        unvisited_nodes_list = list(graph.get_nodes())
        costs_to_reach_node = {}
        predecessors = {}
        for node in unvisited_nodes_list:
            costs_to_reach_node[node] = np.inf

        costs_to_reach_node[goal] = 0

        priority_queue = [(0, goal)]
        while priority_queue:
            current_cost, current_min_node = heapq.heappop(priority_queue)
            if current_cost > costs_to_reach_node[current_min_node]:
                continue
            for neighbor in graph.get_neighbors(current_min_node):
                edge_cost = graph.value(current_min_node, neighbor)
                if edge_cost is None or edge_cost == np.inf:
                    continue
                new_cost = current_cost + edge_cost
                if new_cost < costs_to_reach_node[neighbor]:
                    costs_to_reach_node[neighbor] = new_cost
                    predecessors[neighbor] = current_min_node
                    heapq.heappush(priority_queue, (new_cost, neighbor))
        return costs_to_reach_node


class HeuristicManhattanDistance(Heuristic):
    def heuristic_costs_to_goal(self, graph, goal: str, layout_id: str):
        """
        :param graph: Graph object
        :param goal: goal node id
        :param layout_id: layout identification
        :return: dictionary with Manhattan distance from each node in the graph to the goal location
        """
        costs_to_reach = {}
        goal_node_obj = self.get_node_infos_node_id(goal, layout_id)
        goal_x_position = goal_node_obj.nodePosition.x
        goal_y_position = goal_node_obj.nodePosition.y
        for node in graph.nodes:
            node_obj = self.get_node_infos_node_id(node, layout_id)
            node_x = node_obj.nodePosition.x
            node_y = node_obj.nodePosition.y
            dist = abs(goal_x_position-node_x) + abs(goal_y_position-node_y)
            costs_to_reach[node] = dist
        return costs_to_reach


class HeuristicEuclideanDistance(Heuristic):
    def heuristic_costs_to_goal(self, graph, goal: str, layout_id: str):
        """
        :param graph: Graph object
        :param goal: goal node id
        :param layout_id: layout identification
        :return: dictionary with Euclidean distance from each node in the graph to the goal location
        """
        costs_to_reach = {}
        goal_node_obj = self.get_node_infos_node_id(goal, layout_id)
        goal_x_position = goal_node_obj.nodePosition.x
        goal_y_position = goal_node_obj.nodePosition.y
        for node in graph.nodes:
            node_obj = self.get_node_infos_node_id(node, layout_id)
            node_x = node_obj.nodePosition.x
            node_y = node_obj.nodePosition.y
            dist = math.sqrt((goal_x_position-node_x)**2 + (goal_y_position-node_y)**2)
            costs_to_reach[node] = dist
        return costs_to_reach


class HeuristicSkewedEuclideanDistance(Heuristic):
    def heuristic_costs_to_goal(self, graph, goal: str, layout_id: str):
        """
        :param graph: Graph object
        :param goal: goal node id
        :param layout_id: layout identification
        :return: dictionary with Euclidean distance from each node in the graph to the goal location
        """

        assert 0 <= EIG_ALPHA <= 1 and 0 <= EIG_BETA <= 1
        costs_to_reach = {}
        goal_node_obj = self.get_node_infos_node_id(goal, layout_id)
        goal_x_position = goal_node_obj.nodePosition.x
        goal_y_position = goal_node_obj.nodePosition.y
        for node in graph.nodes:
            node_obj = self.get_node_infos_node_id(node, layout_id)
            node_x = node_obj.nodePosition.x
            node_y = node_obj.nodePosition.y
            dist = math.sqrt(EIG_ALPHA * (goal_x_position-node_x)**2 + EIG_BETA * (goal_y_position-node_y)**2)
            costs_to_reach[node] = dist
        return costs_to_reach
