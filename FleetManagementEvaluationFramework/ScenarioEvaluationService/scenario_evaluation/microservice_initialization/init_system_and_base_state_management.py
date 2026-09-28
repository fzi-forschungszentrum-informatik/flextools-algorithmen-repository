import json
from typing import List

import config.config_file
from api.client_api import reset_amr_simulation, reset_system_state_management, add_amr_basedatamanagement_api, \
    add_amr_systemdatamanagement_api, add_amr_simulation_api
from config.evaluation_config import BASE_DATA_FILE, SYSTEM_STATE_FILE
from data.models import NewAMRSystemRequest, NewAMRRequest, LoadDimension


def create_system_state_and_base_state_object_from_file(configs=None):
    """
    :return: Method to initialize system state management and base data management service
    """
    if configs is None:
        f = open(SYSTEM_STATE_FILE, "r")
        data_sys = json.load(f)
        f.close()
        f = open(BASE_DATA_FILE, "r")
        data_base = json.load(f)
        f.close()
    else:
        f = open(configs.get_system_state_file(), "r")
        data_sys = json.load(f)
        f.close()
        f = open(configs.get_base_data_file(), "r")
        data_base = json.load(f)
        f.close()

    system_state_objects = []
    base_state_objects = []
    for i, item in enumerate(data_sys):
        new_amr_request = NewAMRSystemRequest(amrId=item['amr_id'], lastNodeId=item['last_node_id'],
                                              layoutId=config.config_file.MAP_ID_DEFAULT,
                                              maxReachBattery=int(item['BatteryState']['reach']))
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
