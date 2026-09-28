import heapq
import json
import datetime
import os
from collections import defaultdict
from typing import Any
import logging

import pandas as pd
from pydantic import ValidationError
from pathlib import Path

from agents.amr import AMR
from agents.customer import Customer
from api.client_api import get_nodes_info, get_amr_data_base, send_order_to_order_management, \
    send_last_header_id_simulation_step_to_amr_communication, request_orders_for_amr
from api.client_api_models import AMRBaseDataRequest, HeaderIdRequest
from api.server_api_models import SystemTimeRequest, CollisionDetection, PathRequest, \
    OrderUpdateVDABodyHeader, DispatchingStrategy, SystemTimeResponse, SimulationStepResponse, DrivingTimeResponse, \
    StatisticFileNames
from config.config_file import INITIAL_STATE_FILE_SCENARIO
from data.enums import ConnectionState, OperatingMode
from data.models import AMRPosition, BatteryState, NewAMRSystemRequest, NodeInfoRequest, \
    AMRPauseRequest, CollisionCheckObject, HeaderId, NewOrderInfo, WaitingTimeRequest, Layout, MakeSpanRequest, MakeSpanResponse
from logic.general_functions import transform_str_to_datetime
from logic.transformation_functions import transform_order_to_order_state_request
from api.api_config import fast_mqtt, app  # import app important for main to import over AMRsDb
from gmqtt import Client as MQTTClient

import config.config_file
import data.enums
from visualization.visualization_pipeline import show_lif_animated

logger = logging.getLogger(config.config_file.LOGGER_NAME)

########
# MQTT #
########


@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    client.subscribe("/mqtt")  # subscribing mqtt topic
    logger.debug(f"Connected: {client}, {flags}, {rc}, {properties}")


@fast_mqtt.subscribe("flextools/v2/fzi/+/order")
async def message_to_topic(client, topic, payload, qos, properties):
    logger.debug(f"Received message to specific topic: {topic}, {payload.decode()}, {qos}, {properties}")
    try:
        request_body = OrderUpdateVDABodyHeader.parse_obj(json.loads(payload.decode()))
    except Exception as e:
        logger.exception(f'Incoming payload could not be parsed into SetAMRConnectionStateRequest object.'
                         f' --> Message discarded {e}')
        raise Exception(f'Incoming payload could not be parsed into SetAMRConnectionStateRequest object.'
                        f' --> Message discarded {e}')
    else:
        order_state_request = transform_order_to_order_state_request(request_body)
        database['amrs']._amrs[request_body.serialNumber].plan_to_process_order(order_state_request)


@fast_mqtt.subscribe(os.environ['MQTT_RECEIVE_ORDER_TOPIC'])
async def message_to_topic(client, topic, payload, qos, properties):
    logger.debug(f"Received message to specific topic: {topic}, {payload.decode()}, {qos}, {properties}")
    try:
        request_body = NewOrderInfo.parse_obj(json.loads(payload.decode()))
    except Exception as e:
        logger.exception(f"Incoming payload could not be parsed into NewOrderInfo object."
                         f" --> Message discarded {e}")
        raise Exception(f"Incoming payload could not be parsed into NewOrderInfo object."
                        f" --> Message discarded {e}")
    else:
        try:
            database['amrs'].add_new_order(request_body)
            database['amrs']._number_total_orders += 1
        except ValidationError as e:
            return logger.info(f'Validation error order {e}')
        return None


@app.post("/step")
async def simulate_next_timestep():
    res = database['amrs'].simulate_next_timestep()
    return res


@app.post("/new-order")
async def add_new_order(request_body: NewOrderInfo):
    try:
        database['amrs'].add_new_order(request_body)
        database['amrs']._number_total_orders += 1
    except ValidationError as e:
        return logger.info(f'Validation error order {e}')
    return None


@app.post("/new-amr")
async def add_new_amr(request_body: NewAMRSystemRequest):
    node_response_obj = get_nodes_info(NodeInfoRequest(nodeIds=[request_body.lastNodeId],
                                                       layoutId=request_body.layoutId)).json()
    node_list = [node for node in node_response_obj['nodes']]
    amr_position = AMRPosition(x=node_list[0]['nodePosition']['x'], y=node_list[0]['nodePosition']['y'],
                               mapId=request_body.layoutId, positionInitialized=True)
    amr_base_data_request = AMRBaseDataRequest(amrIds=[request_body.amrId])
    base_data_response = get_amr_data_base(amr_base_data_request).json()

    amr = AMR(fast_mqtt=fast_mqtt, header_id=database['amrs'].header_id, occupied_graph_ids=database['amrs'].occupied_graph_ids,
              amr_id=request_body.amrId, connection_state=ConnectionState.ONLINE,
              order_id='', order_update_id=0, last_node_id=request_body.lastNodeId, last_node_sequence_id=0,
              driving=False, distance_since_last_node=0, operating_mode=OperatingMode.AUTOMATIC,
              amr_position=amr_position,
              battery_state=BatteryState(batteryCharge=100, charging=False, reach=request_body.maxReachBattery),
              node_states=[], edge_states=[], action_states=[], orders_dict=database['amrs'].orders_dict,
              speed_max=base_data_response[0]['maxSpeed'],
              acceleration_max=base_data_response[0]['accelerationMax'],
              deceleration_max=base_data_response[0]['decelerationMax'],
              battery_max_reach=request_body.maxReachBattery
              )
    database['amrs'].add_amr(amr)
    return


@app.get("/system-time")
async def get_system_time():
    response = SystemTimeRequest(systemTime=max(database['amrs'].get_time(), datetime.datetime.now()))
    return response


@app.put("/system-time")
async def set_system_time_from_extern_for_initialization(system_time_request: SystemTimeResponse):
    system_time = transform_str_to_datetime(system_time_request.timestamp)
    database['amrs'].set_time(system_time)
    return


@app.post("/pause-amr")
async def set_pause_amr(request_body: AMRPauseRequest):
    database['amrs']._amrs[request_body.amrId].pause = request_body.pause
    logger.info(f'Set AMR {request_body.amrId} pause modus: {request_body.pause}')
    return


@app.put("/collision-detection")
async def set_collision_detection(request_body: CollisionDetection):
    database['amrs'].occupied_graph_ids.checkCollisions = request_body.collisionDetection
    config.config_file.CHECK_COLLISIONS = request_body.collisionDetection
    return


@app.put("/dispatching-strategy")
async def set_dispatching_strategy_request(request_body: DispatchingStrategy):
    config.config_file.TASK_ASSIGNMENT_STRATEGY = data.enums.TaskAssignmentStrategy(request_body.dispatchingStrategy)
    return


@app.post("/reset")
async def reset_amr_simulation():
    database['amrs'].__init__(config.config_file.INITIAL_STATE_FILE_SCENARIO)
    return


@app.put("/statistic-files")
async def set_statistic_files(request_body: StatisticFileNames):
    config.config_file.AMR_STATISTIC_DATA_FILE = request_body.AMRStatisticDataFileName
    config.config_file.GRAPH_STATISTIC_DATA_FILE = request_body.GraphStatisticDataFileName
    Path(request_body.AMRStatisticDataFileName).parent.mkdir(parents=True, exist_ok=True)
    Path(request_body.GraphStatisticDataFileName).parent.mkdir(parents=True, exist_ok=True)
    return


@app.get('/health')
async def health():
    pass


@app.put("/system-state-file")
async def set_system_state_file_new(request_body: PathRequest):
    config.config_file.INITIAL_STATE_FILE_SCENARIO = request_body.path
    database['amrs'].__init__(request_body.path)
    return


@app.put("/waiting-time-node")
async def set_waiting_time_node(request_body: WaitingTimeRequest):
    config.config_file.WAITING_TIME_ON_NODE = request_body.waitingTime
    return


@app.get("/driving-times")
async def get_service_times():
    resp_obj = DrivingTimeResponse(drivingTimeLoaded=database['amrs'].service_time_loaded.total_seconds(),
                                   drivingTimeUnloaded=database['amrs'].service_time_unloaded.total_seconds())
    return resp_obj


@app.post("/visualization-scenario")
async def visualize_full_mapd_scenario(request_body: Layout):
    database['amrs'].visualize_scenario(request_body)
    return


@app.get("/makespan")
async def compute_makespan(request_body: MakeSpanRequest):
    end_time = datetime.datetime(1500, 1, 1)
    start_time = datetime.datetime(2999, 12, 31)
    for i in range(int(request_body.earliestOrderId), int(request_body.latestOrderId) + 1):
        try:
            if database['amrs'].orders_dict[str(i)]['dropoff_time'] > end_time:
                end_time = database['amrs'].orders_dict[str(i)]['dropoff_time']
        except:
            pass
        try:
            if database['amrs'].orders_dict[str(i)]['pickup_time'] < start_time:
                start_time = database['amrs'].orders_dict[str(i)]['pickup_time']
        except:
            pass
    time = (end_time - start_time).total_seconds()
    response = MakeSpanResponse(time=int(time))
    return response


@app.get("/next-order")
async def get_next_order_id_for_user_interface():
    if database['amrs'].orders_dict:
        max_order_id = max(int(order_id) for order_id in database['amrs'].orders_dict.keys())
        next_order_id = max_order_id + 1
    else:
        next_order_id = 1
    return {'next_order_id': str(next_order_id)}


class Simulation:
    def __init__(self, file):
        self._order_queue = []
        self._amrs = {}
        self._customers = {}
        self.orders_dict = defaultdict(dict)
        self.file = file
        self.occupied_graph_ids = CollisionCheckObject(nodeIds=[], edgeIds=[],
                                                       checkCollisions=config.config_file.CHECK_COLLISIONS)
        self.number_state_updates = 0
        self.header_id = HeaderId(id=1)
        self.node_and_edge_dict = {}
        self.__initialize_system(file)
        self._init_customer()
        self._simulate_nothing_steps = 0
        self._number_total_orders = 0
        self._number_finished_orders = 0
        self._number_no_new_order = 0
        self.service_time_unloaded = datetime.timedelta(seconds=0)
        self.service_time_loaded = datetime.timedelta(seconds=0)
        self.current_waiting_number_of_orders_in_system = 0
        self.current_working_order_ids = []
        self.current_working_number_of_orders_in_system = 0
        self.amr_statistics_df = pd.DataFrame()

    def _init_customer(self):
        """
        :return: Init customer method for publish orders
        """
        self._customers['customer'] = Customer(self._order_queue)

    def add_amr(self, amr: AMR):
        """
        :param amr: AMR object
        :return: add amr to simulation scenario
        """
        if amr.amr_id not in self._amrs.keys():
            self._amrs[amr.amr_id] = amr
        self.amr_statistics_df = pd.DataFrame(
            columns=(['Start Time', 'End Time', 'Number of current waiting orders', 'Number of current working orders']
                     + list(self._amrs.keys())))

    def add_new_order(self, request_body: NewOrderInfo):
        """
        :param request_body: NeworderInfo object
        :return: add order to queue for customer
        """
        if config.config_file.SIMULATION_ACTIVE is True:
            self.orders_dict[str(request_body.orderId)]['pickup'] = request_body.sourceId
            self.orders_dict[str(request_body.orderId)]['dropoff'] = request_body.sinkId
            self._customers['customer'].add_order_to_queue(request_body)
        else:  # send order direct to order management
            send_order_to_order_management(request_body)

    def get_time(self) -> datetime.datetime:
        """
        :return: get current simulation time
        """
        amr_time = datetime.datetime(1990, 1, 1, 0, 0)
        for amr_id in self._amrs.keys():
            if self._amrs[amr_id].current_time is not None:
                if amr_time <= self._amrs[amr_id].current_time:
                    amr_time = self._amrs[amr_id].current_time
        return amr_time

    def set_time(self, timestamp: datetime.datetime):
        for amr_id in self._amrs.keys():
            if self._amrs[amr_id].current_time is not None:
                self._amrs[amr_id].current_time = timestamp

    def simulate_next_timestep(self):
        """
        :return: Method for simulate next timestep
                 1. publish orders for order with publish time before simulation time
                 2. Initialize map object to avoid conflict with node ids from amr with wait on the same node
                 3. process simulation step for all amr and update simulation time
                 4. send last header_id of this simulation step to the amr communication service
                 5. send state updates for all amr according vda5050

        """
        sys_time = self.get_time()
        new_amr_data_row = [sys_time]
        while True:
            if len(self._order_queue) > 0:
                publish_time, len_queue, next_order = heapq.heappop(self._order_queue)
            else:
                break
            if publish_time <= sys_time:
                send_order_to_order_management(next_order)
                self.current_waiting_number_of_orders_in_system += 1
            else:
                heapq.heappush(self._order_queue, (publish_time, len_queue, next_order))
                break
        self.occupied_graph_ids.nodeIds = []
        self.occupied_graph_ids.edgeIds = []
        for amr_id in self._amrs.keys():
            node = self._amrs[amr_id].get_nodes_for_staying()
            if node is not None:
                self.occupied_graph_ids.nodeIds.append(node)
        simulate_something = False
        for amr_id in self._amrs.keys():
            logger.info(f'Current node amr {amr_id}: {self._amrs[amr_id].last_node_id}; Order id:'
                        f' {self._amrs[amr_id].order_id}; Action States: {self._amrs[amr_id].action_states}; Next node'
                        f' states: {self._amrs[amr_id].node_states}')
            (simulation_amr, finished_orders, service_time_loaded, service_time_unloaded, visited_edge_ids,
                visited_node_ids) = self._amrs[amr_id].simulation_step()
            self.service_time_unloaded += service_time_unloaded
            self.service_time_loaded += service_time_loaded
            if finished_orders > 0:
                self._number_finished_orders = self._number_finished_orders + finished_orders
                self.current_working_number_of_orders_in_system = self.current_working_number_of_orders_in_system - finished_orders
            if simulation_amr is True:
                simulate_something = True
            if self._amrs[amr_id].current_time is not None:
                if sys_time <= self._amrs[amr_id].current_time:
                    sys_time = self._amrs[amr_id].current_time
            if service_time_loaded > datetime.timedelta(seconds=0):
                new_amr_data_row.append('DRIVING')
            elif service_time_unloaded > datetime.timedelta(seconds=0):
                new_amr_data_row.append('EMPTY_DRIVING')
            elif service_time_loaded == datetime.timedelta(seconds=0) and service_time_unloaded == datetime.timedelta(seconds=0):
                new_amr_data_row.append('WAITING')

            for vis_edge in visited_edge_ids:
                if vis_edge in self.node_and_edge_dict.keys():
                    self.node_and_edge_dict[vis_edge] += 1
                else:
                    self.node_and_edge_dict[vis_edge] = 1
            for vis_node in visited_node_ids:
                if vis_node in self.node_and_edge_dict.keys():
                    self.node_and_edge_dict[vis_node] += 1
                else:
                    self.node_and_edge_dict[vis_node] = 1

        new_amr_data_row.insert(1, sys_time)
        new_amr_data_row.insert(2, self.current_waiting_number_of_orders_in_system)
        new_amr_data_row.insert(3, self.current_working_number_of_orders_in_system)
        if self.amr_statistics_df.empty:
            column_list = ['Start Time', 'End Time', 'Number of current waiting orders', 'Number of current working orders'] + [str(i+1) for i in range(len(self._amrs.keys()))]
            self.amr_statistics_df = pd.DataFrame([new_amr_data_row], columns=column_list)
        else:
            self.amr_statistics_df = pd.concat([self.amr_statistics_df, pd.DataFrame([new_amr_data_row], columns=self.amr_statistics_df.columns)], ignore_index=True)

        # send last header id to amr_communication
        if config.config_file.USE_MQTT is True:
            send_last_header_id_simulation_step_to_amr_communication(HeaderIdRequest(headerId=self.header_id.id - 1 +
                                                                                     len(self._amrs.keys())))
        for amr_id in self._amrs.keys():
            self._amrs[amr_id].send_state_update()
        logger.debug(f'send header id {self.header_id.id-1+len(self._amrs.keys())}')

        if simulate_something is False:
            if len(self._order_queue) > 0:
                publish_time, len_queue, next_order = heapq.heappop(self._order_queue)
                for amr_id in self._amrs.keys():
                    if self._amrs[amr_id].current_time is not None:
                        if publish_time >= self._amrs[amr_id].current_time:
                            self._amrs[amr_id].current_time = publish_time
                heapq.heappush(self._order_queue, (publish_time, len_queue, next_order))
        new_orders = request_orders_for_amr().json()
        if new_orders is not None:
            for new_order in new_orders[0]:
                new_order_obj = OrderUpdateVDABodyHeader(**new_order)
                order_state_request = transform_order_to_order_state_request(new_order_obj)
                if len(order_state_request.order.nodes[-1].actions) > 0:
                    if order_state_request.order.nodes[-1].actions[-1].actionType == 'drop':
                        if order_state_request.order.orderId not in self.current_working_order_ids:
                            self.current_working_order_ids.append(order_state_request.order.orderId)
                            self.current_waiting_number_of_orders_in_system -= 1
                            self.current_working_number_of_orders_in_system += 1
                database['amrs']._amrs[new_order_obj.serialNumber].plan_to_process_order(order_state_request)
                self._number_no_new_order = 0
        else:
            self._number_no_new_order += 1

        if self._number_total_orders == 0:
            percentage_finish = 0
        else:
            percentage_finish = round((self._number_finished_orders/self._number_total_orders)*100, 2)
        if simulate_something is True:
            self._simulate_nothing_steps = 0
            if percentage_finish == 100:
                res = SimulationStepResponse(simulationFinish=True, percentageFinish=percentage_finish)
                df_graph_statistics = pd.DataFrame(list(self.node_and_edge_dict.items()), columns=['Key', 'Value'])
                df_graph_statistics.to_csv(config.config_file.GRAPH_STATISTIC_DATA_FILE, sep=';', header= True, index=False)
                self.amr_statistics_df.to_csv(config.config_file.AMR_STATISTIC_DATA_FILE, sep=';', header=True, index=False)
            else:
                res = SimulationStepResponse(simulationFinish=False, percentageFinish=percentage_finish)
        else:
            if self._simulate_nothing_steps == 3 or self._number_no_new_order == 3:  # Simulation finish
                res = SimulationStepResponse(simulationFinish=True, percentageFinish=percentage_finish)
            else:
                res = SimulationStepResponse(simulationFinish=False, percentageFinish=percentage_finish)
                self._simulate_nothing_steps += 1
        if new_orders[1] is True:
            res.simulationFinish = True

        return res

    def visualize_scenario(self, layout: Layout):
        if config.config_file.VISUALIZE_SCENARIO is True:
            all_paths = []
            for amr_id in self._amrs.keys():
                all_paths.append(self._amrs[amr_id].path)
            if config.config_file.DEMO_BACKGROUND is True:
                show_lif_animated(layout, all_paths, self.orders_dict, config.config_file.DEMO_IMAGE,
                                  config.config_file.DEMO_LENGTH, config.config_file.DEMO_WIDTH)
            else:
                show_lif_animated(layout, all_paths, self.orders_dict)
        return

    ###########
    # private #
    ###########

    def __initialize_system(self, file: str):
        """
        :param file: file with json of system state
        :return: if file is empty, initialize simulation empty without amr
        """
        if file == '':
            return
        f = open(file, "r")
        data = json.load(f)
        f.close()
        amr_base_data_request = AMRBaseDataRequest(amrIds=['*'])
        base_data_response = get_amr_data_base(amr_base_data_request).json()

        for i, item in enumerate(data):
            amr = AMR(fast_mqtt=fast_mqtt, header_id=self.header_id, occupied_graph_ids=self.occupied_graph_ids,
                      amr_id=item['amr_id'], connection_state=ConnectionState.ONLINE,
                      order_id=item['order_id'], order_update_id=item['order_update_id'],
                      last_node_id=item['last_node_id'], last_node_sequence_id=item['last_node_sequence_id'],
                      driving=item['driving'], distance_since_last_node=item['distance_since_last_node'],
                      operating_mode=OperatingMode.AUTOMATIC,
                      amr_position=AMRPosition(x=item['AMRPosition']['x'], y=item['AMRPosition']['y'],
                                               theta=item['AMRPosition']['theta'],
                                               mapId=item['AMRPosition']['map_id'],
                                               positionInitialized=item['AMRPosition']['position_initialized']),
                      battery_state=BatteryState(batteryCharge=item['BatteryState']['battery_charge'],
                                                 charging=item['BatteryState']['charging'],
                                                 reach=item['BatteryState']['reach']),
                      node_states=item['node_states'], edge_states=item['edge_states'],
                      action_states=item['action_states'],
                      orders_dict=self.orders_dict,
                      speed_max=base_data_response[i]['maxSpeed'],
                      acceleration_max=base_data_response[i]['accelerationMax'],
                      deceleration_max=base_data_response[i]['decelerationMax'])
            self.add_amr(amr)

            if item['last_node_id'] not in self.node_and_edge_dict.keys():
                self.node_and_edge_dict[item['last_node_id']] = 1
            else:
                self.node_and_edge_dict[item['last_node_id']] += 1


database = {'amrs': Simulation(INITIAL_STATE_FILE_SCENARIO)}
