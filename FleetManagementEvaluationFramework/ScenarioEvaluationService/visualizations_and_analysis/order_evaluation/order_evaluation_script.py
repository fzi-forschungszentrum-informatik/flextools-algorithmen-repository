import copy
import datetime
import json
import logging
import math
import os
from typing import List
import glob
import config.config_file

import pandas as pd
from joblib import Memory

from order_evaluation.dijkstra import path_planning

from order_evaluation.data_models.models import Action, BlockingType, Node, NodePosition, Edge, Station, \
    StationPosition, Layout
from order_evaluation.graph import Graph


memory = Memory(location=os.path.join('.', 'detour_cache'), verbose=0)
logger = logging.getLogger(config.config_file.LOGGER_NAME)


def compute_service_times_without_collisions():
    file_name_results = 'order_evaluation_results_without_collisions_200.csv'
    layout_name = 'warehouse_35x21'
    form = 'triangle'
    distance = 1
    tf = 1

    layout_file = rf'./lif_files/LIF_{layout_name}_dist_{distance}_{form}.json'
    layout = initialize_layout(layout_file)
    graph = initialize_graph_with_layout(layout)

    order_file = f'./order_files/orders_scenario_{layout_name}_{form}_{distance}_200_seed_1_fq_{tf}.json'

    f = open(order_file, "r")
    data = json.load(f)
    f.close()

    total_loaded_path_length = 0
    start_and_end_time = []

    for i, order in enumerate(data):
        _, costs, _ = path_planning(graph, [order['sourceId']], [order['sinkId']])
        total_loaded_path_length += costs[0]
        start_and_end_time.append((datetime.datetime.strptime(order['startTime'], '%Y-%m-%d %H:%M:%S.%f'),
                                   datetime.datetime.strptime(order['startTime'], '%Y-%m-%d %H:%M:%S.%f') +
                                   datetime.timedelta(seconds=costs[0])))
        logger.info(f'Path computed for order {i+1}, with length {costs[0]}')

    events = []
    for start, end in start_and_end_time:
        events.append((start, +1))
        events.append((end, -1))

    events.sort(key=lambda x: (x[0], x[1]))

    current = 0
    max_active = 0
    min_active = float('inf')

    for time, change in events:
        current += change
        if current > 0:
            min_active = min(min_active, current)
        max_active = max(max_active, current)

    if min_active == float('inf'):
        min_active = 0

    logger.info(f"Maximal Anzahl Orders gleichzeitig: {max_active}")
    logger.info(f"Minimal Anzahl Orders gleichzeitig (wenn aktiv): {min_active}")
    logger.info(f"Gesamte beladene Pfadlänge ohne Umwege: {total_loaded_path_length}")

    results_df = pd.DataFrame({'Layout': [layout_name], 'TF': [tf], 'Graph': [form], 'Distance': [distance],
                               'Loaded Service Time': [total_loaded_path_length], 'Min. Number of equals orders':
                               [min_active], 'Max. Number of equals orders': [max_active]})
    file_exists = os.path.exists(file_name_results)
    results_df.to_csv(
        file_name_results,
        mode='a' if file_exists else 'w',
        header=not file_exists,
        index=False,
        sep=';',
        decimal=','
    )
    return


def initialize_layout(layout_file: str):
    f = open(layout_file, "r")
    data = json.load(f)
    f.close()
    for item in data['layouts']:
        node_list = []
        for node in item['nodes']:
            action_list = []
            for action in node['vehicleTypeNodeProperties'][0]['actions']:
                action_list.append(Action(actionId='',
                                          actionType=action['actionType'],
                                          blockingType=BlockingType.HARD))
            node_list.append(Node(nodeId=node['nodeId'], sequenceId=0, released=True,
                                  nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                            y=node['nodePosition']['y'],
                                                            mapId=node['mapId']),
                                  actions=action_list))
        if 'edges' in item.keys():
            if len(item['edges']) > 0:
                edge_list = []
                for edge in item['edges']:
                    action_list_edge = []
                    for action in edge['vehicleTypeEdgeProperties'][0]['actions']:
                        action_list_edge.append(Action(actionId='',
                                                       actionType=action['actionType'],
                                                       blockingType=BlockingType.HARD))
                    length = compute_length_edge(edge['startNodeId'], edge['endNodeId'], node_list)
                    edge_list.append(Edge(edgeId=edge['edgeId'], sequenceId=0, released=True,
                                          startNodeId=edge['startNodeId'],
                                          endNodeId=edge['endNodeId'],
                                          maxSpeed=edge['vehicleTypeEdgeProperties'][0]['maxSpeed'],
                                          length=length, actions=action_list_edge))
            else:
                edge_list = compute_edge_list(node_list)
        else:
            edge_list = compute_edge_list(node_list)
        station_list = []
        for station in item['stations']:
            station_list.append(Station(stationId=station['stationId'],
                                        interactionNodeIds=station['interactionNodeIds'],
                                        stationName=station['stationName'],
                                        stationPosition=StationPosition(x=station['stationPosition']['x'],
                                                                        y=station['stationPosition']['y'])))

        layout = Layout(layoutId=item['layoutId'], nodes=node_list, edges=edge_list, stations=station_list)
        return layout
    return None


def compute_edge_list(node_list: List[Node]):
    """
    :param node_list: List[node]
    :return: Method to computes edges for a layout between all nodes
    """
    max_speed_edge = 1
    edge_list = []
    for i, node in enumerate(node_list):
        for j, node2 in enumerate(node_list[i:]):
            length = compute_length_edge(node.nodeId, node2.nodeId, node_list)
            edge_list.append(Edge(edgeId=str(f'E-{node.nodeId}-{node2.nodeId}'),
                                  sequenceId=0,
                                  released=True,
                                  startNodeId=node.nodeId,
                                  endNodeId=node2.nodeId,
                                  maxSpeed=max_speed_edge,
                                  length=length,
                                  actions=[]))
    return edge_list


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


def initialize_graph_with_layout(layout: Layout):
    edge_list = copy.deepcopy(layout.edges)
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
    graph = Graph(nodes_and_stations, init_graph)
    return graph


def compute_detour(layout_name: str, form: str, distance: float, service_time_list: List[float] | None):
    total_loaded_path_length = compute_total_loaded_path_length(layout_name, form, distance)

    if service_time_list is not None:
        if isinstance(service_time_list, list):
            detour_times = [time-total_loaded_path_length for time in service_time_list]
        elif isinstance(service_time_list, float):
            detour_times = service_time_list - total_loaded_path_length

    else:
        detour_times = total_loaded_path_length
    return detour_times


@memory.cache
def compute_total_loaded_path_length(layout_name: str, form: str, distance: float) -> float:
    dist_str = str(distance).replace('.0', '')
    layout_file = rf'./order_evaluation/lif_files/LIF_{layout_name}_dist_{dist_str}_{form}.json'
    layout = initialize_layout(layout_file)
    graph = initialize_graph_with_layout(layout)
    tf = 1
    order_file = f'./order_evaluation/order_files/orders_scenario_{layout_name}_{form}_{dist_str}_200_fq_{tf}.json'
    order_file = glob.glob(order_file)
    f = open(order_file[0], "r")
    data = json.load(f)
    f.close()
    total_loaded_path_length = 0

    for i, order in enumerate(data):
        _, costs, _ = path_planning(graph, [order['sourceId']], [order['sinkId']])
        total_loaded_path_length += costs[0]

    return total_loaded_path_length


if __name__ == "__main__":
    compute_service_times_without_collisions()
