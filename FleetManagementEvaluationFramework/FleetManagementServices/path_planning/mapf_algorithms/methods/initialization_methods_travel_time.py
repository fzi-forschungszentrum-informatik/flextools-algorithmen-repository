import math
from typing import List

from config.config_file import MAX_SPEED_EDGE
from data.models import Node, Edge, Layout
from data.data_structures.extended_graph import ExtendedGraph
from data.data_structures.graph import Graph
import config.config_file


def init_graph_with_edges(edge_list):
    """
    :param edge_list: List[Edge]
    :return: Method to initialize graph with edges
    """
    init_graph = {}
    nodes_and_stations = []
    for edge in edge_list:
        if edge.startNodeId not in nodes_and_stations:
            nodes_and_stations.append(edge.startNodeId)
            init_graph[edge.startNodeId] = {}
        if edge.endNodeId not in nodes_and_stations:
            nodes_and_stations.append(edge.endNodeId)
            init_graph[edge.endNodeId] = {}
        init_graph[edge.startNodeId][edge.endNodeId] = round(edge.length / edge.maxSpeed, 2)
        # maybe other direction is required
    graph = Graph(nodes_and_stations, init_graph, config.config_file.DIRECTED_GRAPH)
    return graph


def init_extended_graph(layout : Layout):
    """
    :param edge_list: List[Edge]
    :return: Method to initialize graph with edges
    """
    init_graph = {}
    nodes_and_stations = []
    for edge in layout.edges:
        if edge.startNodeId not in nodes_and_stations:
            nodes_and_stations.append(edge.startNodeId)
            init_graph[edge.startNodeId] = {}
        if edge.endNodeId not in nodes_and_stations:
            nodes_and_stations.append(edge.endNodeId)
            init_graph[edge.endNodeId] = {}
        init_graph[edge.startNodeId][edge.endNodeId] = round(edge.length / edge.maxSpeed, 2)

    return ExtendedGraph(nodes_and_stations, init_graph, layout.nodes, layout.edges, layout.stations)


def compute_length_edge(start_node_id: str, end_node_id: str, node_list: List[Node]):
    """
    :param start_node_id: str
    :param end_node_id: str
    :param node_list: List[Node]
    :return: computed manhattan distance
    """
    start_node = None
    end_node = None
    for node in node_list:
        if node.nodeId == start_node_id:
            start_node = node
        if node.nodeId == end_node_id:
            end_node = node

    start_node_x, start_node_y = start_node.nodePosition.x, start_node.nodePosition.y
    end_node_x, end_node_y = end_node.nodePosition.x, end_node.nodePosition.y
    dist = math.sqrt((end_node_x-start_node_x)**2 + (end_node_y-start_node_y)**2)
    return dist


def compute_edge_list(node_list: List[Node]):
    """
    :param node_list: List[node]
    :return: Method to computes edges for a layout between all ndoes
    """
    edge_list = []
    for i, node in enumerate(node_list):
        for j, node2 in enumerate(node_list[i:]):
            length = compute_length_edge(node.nodeId, node2.nodeId, node_list)
            edge_list.append(Edge(edgeId=str(f'E-{node.nodeId}-{node2.nodeId}'),
                                  sequenceId=0,
                                  released=True,
                                  startNodeId=node.nodeId,
                                  endNodeId=node2.nodeId,
                                  maxSpeed=MAX_SPEED_EDGE,
                                  length=length,
                                  actions=[]))
    return edge_list
