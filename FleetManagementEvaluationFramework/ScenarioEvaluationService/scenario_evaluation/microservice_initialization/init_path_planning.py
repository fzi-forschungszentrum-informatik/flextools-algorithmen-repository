import json

from api.client_api import set_lif_object
from config.evaluation_config import LIF_FILE
from data.enums import BlockingType
from data.models import Action, Node, NodePosition, Edge, Station, StationPosition, Layout, LIFObject
from logic.help_functions import compute_length_edge, compute_edge_list
import config.config_file
import config.evaluation_config


def set_lif_object_from_file_in_travel_time_service(configs=None):
    """
    :param configs: config file parameters
    :return: Method to create LIF object and set LIF object in travel time service for path planning
    """
    if configs is None:
        f = open(LIF_FILE, "r")
        data = json.load(f)
        f.close()
    else:
        f = open(configs.get_lif_file(), "r")
        data = json.load(f)
        f.close()

    layout_list = []
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
        config.config_file.MAP_ID_DEFAULT = item['layoutId']
        layout_list.append(Layout(layoutId=item['layoutId'], nodes=node_list, edges=edge_list, stations=station_list))
        request_obj = LIFObject(layouts=layout_list)
        set_lif_object(request_obj)
        if config.evaluation_config.MAP_ID is None:
            config.evaluation_config.MAP_ID = item['layoutId']
        return layout_list[0]
