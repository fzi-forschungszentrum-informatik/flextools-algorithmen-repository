from typing import List
import logging

from config.config_file import LOGGER_NAME
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.path_planning_heuristic_interface import Heuristic
from interfaces.path_planning_interface import PathPlanning

logger = logging.getLogger(LOGGER_NAME)


class Dijkstra(PathPlanning):

    def path_planning(self, graph: ExtendedGraph, layout_id: str, start_node_ids: List[str], end_node_ids: List[str],
                      constraints, tokens, heuristic: Heuristic):
        """
        :param graph: Graph object
        :param layout_id: layout identification
        :param start_node_ids: start node
        :param end_node_ids: goal
        :param constraints: not needed
        :param tokens: not needed
        :param heuristic: heuristic interface to compute the heuristic distance to the goal, e.g. manhattan distance
        :return: [path], [cost to reach goal]
        :algorithm: Dijkstra algorithm
        """
        if len(start_node_ids) > 1 or len(end_node_ids) > 1:
            logger.exception("Error: Dijkstra algorithm can only compute shortest path for single agent")
            raise Exception("Error: Dijkstra algorithm can only compute shortest path for single agent")
        start_node_id = start_node_ids[0]
        end_node_id = end_node_ids[0]

        unvisited_nodes_list = list(graph.graph.get_nodes())
        predecessors = {}

        # initialize unvisited nodes with infinity and starting node with 0
        costs_to_reach_node = {
            node: float("inf")
            for node in unvisited_nodes_list
        }
        costs_to_reach_node[start_node_id] = 0

        # The algorithm executes until all nodes are visited
        while unvisited_nodes_list:
            current = min(unvisited_nodes_list, key=lambda n: costs_to_reach_node[n])
            if current == end_node_id:
                break
            neighbors = graph.graph.get_neighbors(current)
            for neighbor in neighbors:
                edge_cost = graph.graph.value(current, neighbor)
                new_cost = costs_to_reach_node[current] + edge_cost

                if new_cost < costs_to_reach_node[neighbor]:
                    costs_to_reach_node[neighbor] = new_cost
                    predecessors[neighbor] = current

            unvisited_nodes_list.remove(current)

        path = []
        current_node_id = end_node_id
        while current_node_id in predecessors:
            path.append(current_node_id)
            current_node_id = predecessors[current_node_id]
        path.append(start_node_id)

        path.reverse()
        return [path], [costs_to_reach_node[end_node_id]], 0, 0, None
