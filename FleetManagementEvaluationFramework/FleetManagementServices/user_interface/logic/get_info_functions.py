import networkx as nx
import pandas as pd

from api.client_api import get_map_info
import config.config_file
from data.models import MapInfoRequest, AMRRequests, OrderInfoRequest, StationPosition, Station, NodePosition, Node
import api.client_api


def create_networkx_graph():
    """
    :return: Create network as networkx graph object
    """
    graph = nx.Graph()
    map_request = MapInfoRequest(mapId=config.config_file.MAP_ID_DEFAULT)
    try:
        map = api.client_api.get_map_info(map_request).json()
    except:
        return graph
    for node in map['nodes']:
        graph.add_node(node['nodeId'],
                       pos=(node['nodePosition']['x'], node['nodePosition']['y']),
                       data=Node(nodeId=node['nodeId'],  # instantiate data as node object for full data access
                                 sequenceId=node['sequenceId'],
                                 nodeDescription=node['nodeDescription'],
                                 released=node['released'],
                                 nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                           y=node['nodePosition']['y'],
                                                           theta=node['nodePosition']['theta'],
                                                           mapId=node['nodePosition']['mapId']),
                                 actions=node['actions']),
                       colour=None,
                       text=None,
                       shape="circle")

    for edge in map['edges']:
        if edge['startNodeId'][0] != 'S' and edge['endNodeId'][0] != 'S':
            graph.add_edge(edge['startNodeId'], edge['endNodeId'], colour="black", text="")

    return graph


def get_interaction_nodes():
    """
    :return: Request interaction nodes from stations
    """
    map_request = MapInfoRequest(mapId=config.config_file.MAP_ID_DEFAULT)
    map = get_map_info(map_request).json()
    interaction_nodes = []
    for station in map['stations']:
         for e in station['interactionNodeIds']:  # remembers the station-interaction node ids
            interaction_nodes.append(e)  # and their station types
    return interaction_nodes


def get_station_types():
    """
    :return: get types of stations in the current considered layout
    """
    map_request = MapInfoRequest(mapId=config.config_file.MAP_ID_DEFAULT)
    map = get_map_info(map_request).json()
    stations_type = {}
    for station in map['stations']:
         for e in station['interactionNodeIds']:  # remembers the station-interaction node ids
            stations_type[e] = station['stationName']
    return stations_type


def get_node_and_stations_list():
    """
    :return: request node and station list from the layout
    """
    map_request = MapInfoRequest(mapId=config.config_file.MAP_ID_DEFAULT)
    map = get_map_info(map_request).json()
    node_station_id_list = []
    for node in map['nodes']:
        node_station_id_list.append(node['nodeId'])
    for station in map['stations']:
        node_station_id_list.append(station['stationId'])

    return node_station_id_list


def get_amr_list():
    """
    :return: request amr list from system state management
    """
    amr_id_list = []
    amr_data = api.client_api.get_amr_data(AMRRequests(amrIds=['*'])).json()
    for amr in amr_data:
        amr_id_list.append('AMR ' + amr['amrId'])
    return amr_id_list


def get_next_amr_id():
    """
    :return: get next amr id to add new amr
    """
    amr_data = api.client_api.get_amr_data(AMRRequests(amrIds=['*'])).json()
    if len(amr_data) == 0:
        next_amr_id = 1
    else:
        try:
            next_amr_id = str(int(amr_data[-1]['amrId']) + 1)
        except:
            next_amr_id = str(amr_data[-1]['amrId'] + 'i')
    return next_amr_id


def get_next_order_id():
    """
    :return: get next order id to add new order
    """
    next_order_id = '1'
    if config.config_file.SIMULATION_ACTIVE is True:
        resp = api.client_api.get_next_order_id_simulation().json()
        next_order_id = resp['next_order_id']
    else:
        response = api.client_api.get_order_info(OrderInfoRequest(orderIds=['*'])).json()
        if len(response) > 0:
            try:
                next_order_id = str(int(response[-1]['orderId']) + 1)
            except:
                next_order_id = str(len(response) + 1)
    return next_order_id


def get_order_id_list():
    """
    :return: List[str], request order id list
    """
    response = api.client_api.get_order_info(OrderInfoRequest(orderIds=['*'])).json()
    order_id_list = ['All']
    for item in response:
        order_id_list.append(item['orderId'])
    return order_id_list


def get_amr_list_for_map():
    """
    :return: List[str]
    """
    amr_data = api.client_api.get_amr_data(AMRRequests(amrIds=['*'])).json()
    amr_id_list = ['All AMRs']
    for amr in amr_data:
        amr_id_list.append(amr['amrId'])

    return amr_id_list


def check_all_orders_finish(until_order_id: str):
    """
    :param until_order_id: last order id [str]
    :return: check if all orders finish simulated until given order id
    """
    if until_order_id == 'All':
        request_body = OrderInfoRequest(orderIds=['*'])
    else:
        request_body = OrderInfoRequest(orderIds=[until_order_id])
    response = api.client_api.get_order_info(request_body).json()
    df_orders = pd.DataFrame(response)
    all_orders_finish = True
    if not df_orders.empty:
        for i in range(len(df_orders['orderStatus'])):
            if df_orders['orderStatus'][i] != 'FINISHED':
                all_orders_finish = False
                break
    return all_orders_finish
