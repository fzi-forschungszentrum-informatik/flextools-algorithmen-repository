import json
from typing import List

from api.client_api import set_lif_object, add_amr_basedatamanagement_api, add_amr_systemdatamanagement_api, \
    add_amr_simulation_api, reset_amr_simulation, reset_system_state_management
import config.config_file
from data.enums import BlockingType
from data.models import Action, Node, NodePosition, Edge, Station, StationPosition, Layout, LIFObject
from data.models import NewAMRSystemRequest, NewAMRRequest, LoadDimension
from logic.set_input_data_help_functions import compute_length_edge, compute_edge_list


def set_lif_object_from_file_in_travel_time_service(data):
    """
    :param data: json object
    :return: Method to create LIF object and set LIF object in travel time service for path planning
    """
    data = json.load(data)
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
        config.config_file.MAP_ID_DEFAULT = item['layoutId']  # ToDo Map selection with different layout ids
        layout_list.append(Layout(layoutId=item['layoutId'], nodes=node_list, edges=edge_list, stations=station_list))
        request_obj = LIFObject(layouts=layout_list)
        set_lif_object(request_obj)
        return layout_list


def create_system_state_and_base_state_object_from_file(data_sys, data_base):
    """
    :param data_sys: json object of system data state file
    :param data_base: json object of base data state file
    :return: Method to initialize system state management and base data management service
    """
    data_sys = json.load(data_sys)
    data_base = json.load(data_base)
    system_state_objects = []
    base_state_objects = []
    for i, item in enumerate(data_sys):
        new_amr_request = NewAMRSystemRequest(amrId=item['amr_id'], lastNodeId=item['last_node_id'],
                                              layoutId=config.config_file.MAP_ID_DEFAULT,
                                              maxReachBattery=int(item['BatteryState']['reach']))  # data_base[i]
        new_amr_base_data_request = NewAMRRequest(amrId=data_base[i]['amr_id'],
                                                  seriesName=data_base[i]['type_specification']['series_name'],
                                                  agvClass=data_base[i]['type_specification']['agv_class'],
                                                  maxLoadMass=data_base[i]['type_specification']['max_load_mass'],
                                                  maxSpeed=data_base[i]['physical_parameters']['speed_max'],
                                                  loadDimension=LoadDimension(length=data_base[i]['load_specification']['load_dimension']['length'],
                                                                              width=data_base[i]['load_specification']['load_dimension']['width'],
                                                                              height=data_base[i]['load_specification']['load_dimension']['height']),
                                                  length=data_base[i]['physical_parameters']['length'],
                                                  width=data_base[i]['physical_parameters']['width'],
                                                  height=data_base[i]['physical_parameters']['height_max'])
        system_state_objects.append(new_amr_request)
        base_state_objects.append(new_amr_base_data_request)
    return system_state_objects, base_state_objects


def create_system_state_object_from_file(data_sys):
    """
    :param data_sys: json object with system state data
    :return: Method to create system state data from json file
    """
    data_sys = json.load(data_sys)
    system_state_objects = []
    for item in data_sys:
        new_amr_request = NewAMRSystemRequest(amrId=item['amr_id'], lastNodeId=item['last_node_id'],
                                              layoutId=config.config_file.MAP_ID_DEFAULT,
                                              maxReachBattery=int(item['BatteryState']['reach']))  # data_base[i]

        system_state_objects.append(new_amr_request)
    return system_state_objects


def send_system_state_objects(system_state_objects: List[NewAMRSystemRequest], base_state_objects: List[NewAMRRequest]):
    """
    :param system_state_objects: List[NewAMRSystemRequest]
    :param base_state_objects: List[NewAMRRequest]
    :return: Method to set system state objects for initializing services
    """
    reset_amr_simulation()
    reset_system_state_management()
    for i, system_state_object in enumerate(system_state_objects):
        add_amr_basedatamanagement_api(base_state_objects[i])
        add_amr_systemdatamanagement_api(system_state_object)
        add_amr_simulation_api(system_state_object)
    return
