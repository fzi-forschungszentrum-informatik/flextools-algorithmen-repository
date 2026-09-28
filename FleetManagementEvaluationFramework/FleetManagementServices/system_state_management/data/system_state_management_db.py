import datetime
import json
import logging

from api.client_api import get_system_time, set_amr_location_in_storage_management
from api.client_api_models import Station, StationPosition
from data.enums import ConnectionState, OperatingMode
from data.models import BatteryState, AMRPosition, SystemStateAMR, AMRState
from logic.general_functions import transform_str_to_datetime
import config.config_file

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class SystemStateManagementDb:
    ##########
    # public #
    ##########
    def __init__(self, file: str):  # also one data file for initialization
        try:
            timestamp = get_system_time().json()
            self.system_time = transform_str_to_datetime(timestamp['systemTime']) + datetime.timedelta(milliseconds=1)
        except Exception as e:
            logger.info(f'Error in setting system time from simulation, set system time to now: {e}')
            self.system_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
        self.amr_states = {}  # Dict('AMR_id': AmrState)
        self.last_orders = {}  # List of Dicts for current[1] and last[0] orders
        self.__initialize_system(file)
        if config.config_file.STORAGE_LOCATION_TRACKING is True:
            self.__initialize_amrs_in_storage_location_tracking()
        self.number_to_find_path_again = []
        self.number_found_no_path = 0

    def add_amr_state(self, system_state: SystemStateAMR):
        if system_state.amrState.amrId not in self.amr_states.keys():
            self.amr_states[system_state.amrState.amrId] = system_state

    ###########
    # private #
    ###########

    def __initialize_system(self, file: str):
        if file == '':  # empty initialization
            return
        self.amr_states = {}
        f = open(file, "r")
        data = json.load(f)
        f.close()
        for item in data:
            amr_state = AMRState(timestamp=self.system_time,
                                 amrId=item['amr_id'], connectionState=ConnectionState.ONLINE,
                                 orderId=item['order_id'], orderUpdateId=item['order_update_id'],
                                 lastNodeId=item['last_node_id'],
                                 lastNodeSequenceId=item['last_node_sequence_id'],
                                 driving=item['driving'],
                                 paused=item['paused'],
                                 distanceSinceLastNode=item['distance_since_last_node'],
                                 operatingMode=OperatingMode.AUTOMATIC,
                                 amrPosition=AMRPosition(x=item['AMRPosition']['x'], y=item['AMRPosition']['y'],
                                                         theta=item['AMRPosition']['theta'],
                                                         mapId=item['AMRPosition']['map_id'],
                                                         positionInitialized=item['AMRPosition']['position_initialized']),
                                 batteryState=BatteryState(batteryCharge=item['BatteryState']['battery_charge'],
                                                           charging=item['BatteryState']['charging'],
                                                           reach=item['BatteryState']['reach']),
                                 nodeStates=item['node_states'], edgeStates=item['edge_states'],
                                 actionStates=item['action_states'])
            system_state_amr = SystemStateAMR(amrState=amr_state, plannedOrders=[], token=[item['last_node_id']])
            self.add_amr_state(system_state_amr)

    def __initialize_amrs_in_storage_location_tracking(self):
        logger.info('Initialize Storage Location Tracking')
        for amr_id in self.amr_states.keys():
            amr_station = Station(stationId=amr_id, stationName=f'AMR{amr_id}', stationDescription='AMR',
                                  interactionNodeIds=[],
                                  stationPosition=StationPosition(x=self.amr_states[amr_id].amrState.amrPosition.x,
                                                                  y=self.amr_states[amr_id].amrState.amrPosition.y,
                                                                  theta=self.amr_states[amr_id].amrState.amrPosition.theta),
                                  type='vehicle'
                                  )
            set_amr_location_in_storage_management(amr_station)
