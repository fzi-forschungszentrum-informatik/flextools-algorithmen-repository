import math
from typing import List

from api.client_api_models import OrderInfoRequest
from config.config_file import MAX_SPEED_EDGE
from data.models import Node, Edge

import api.client_api


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
    :param node_list: List[Node]
    :return: Method to compute edges between all nodes in a graph
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


def get_next_order_id():
    """
    :return: get next order id to add new order
    """
    next_order_id = '1'
    response = api.client_api.get_order_info(OrderInfoRequest(orderIds=['*'])).json()
    if len(response) > 0:
        next_order_id = str(int(response[-1]['orderId']) + 1)
    return next_order_id
