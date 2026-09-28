import copy
import datetime
import json
import logging

from typing import List, Union
from datetime import timezone

import config.config_file
from api.client_api import send_state_update_to_amr_communication

from api.client_api_models import AMRStateVDA, SafetyState, ConnectionStateVDA
from fastapi_mqtt import FastMQTT

from api.serialization import serialize_json
from api.server_api_models import OrderStateRequest, StateUpdateVDABodyHeader, ConnectionStateVDABodyHeader
from config.config_file import BATTERY_MAX_REACH_BY_INITIALIZATION
from data.enums import ConnectionState, OperatingMode, ActionStatus, EStop, TaskAssignmentStrategy
from data.models import CollisionCheckObject, AMRPosition, BatteryState, NodeState, EdgeState, \
    ActionState, Velocity, Node, HeaderId

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class AMR:
    def __init__(self,
                 fast_mqtt: FastMQTT,
                 header_id: HeaderId,
                 occupied_graph_ids: CollisionCheckObject,
                 amr_id: str,
                 connection_state: ConnectionState,
                 order_id: str,
                 order_update_id: int,
                 last_node_id: str,
                 last_node_sequence_id: int,
                 driving: bool,
                 distance_since_last_node: float,
                 operating_mode: OperatingMode,
                 amr_position: AMRPosition,
                 battery_state: BatteryState,
                 node_states: List[NodeState],
                 edge_states: List[EdgeState],
                 action_states: List[ActionState],
                 orders_dict: {},
                 speed_max: float = 1,
                 acceleration_max: float = 1,
                 deceleration_max: float = 1,
                 battery_max_reach=BATTERY_MAX_REACH_BY_INITIALIZATION):
        self.occupied_graph_ids = occupied_graph_ids
        self.amr_id = amr_id
        self.header_id = header_id
        self.fast_mqtt = fast_mqtt
        self.connection_state = connection_state
        self.order_id = order_id
        self.order_update_id = order_update_id
        self.last_node_id = last_node_id
        self.last_node_sequence_id = last_node_sequence_id
        self.driving = driving
        self.paused = False
        self.distance_since_last_node = distance_since_last_node
        self.operating_mode = operating_mode
        self.amr_position = amr_position
        self.velocity = Velocity(vx=0, vy=0, omega=0)
        self.loads = []
        self.battery_state = battery_state
        self.node_states = node_states
        self.edge_states = edge_states
        self.action_states = action_states
        self.speed_max = speed_max
        self.acceleration_max = acceleration_max
        self.deceleration_max = deceleration_max
        self.finished_action_in_step = 0
        self.order: Union[OrderStateRequest, None] = None
        self.current_node: Union[Node, None] = None
        self.action_duration = datetime.timedelta(minutes=1)
        self.battery_max_reach = battery_max_reach
        self.time_simulation_step = datetime.timedelta(seconds=0)
        self.current_time: Union[datetime.datetime, None] = datetime.datetime.now()
        self.drive_time = datetime.timedelta(seconds=0)
        self.loaded = False
        self.visited_edge_ids = []
        self.visited_node_ids = []
        self.path = []
        self.orders_dict = orders_dict

    def plan_to_process_order(self, request_body: OrderStateRequest):
        """
        :param request_body: Get OrderStateRequest for execute a new order received via mqtt according vda5050
        :return: select order planning method
        """
        logger.info(f' AMR {self.amr_id} get new order Order: {request_body.order.orderId} at time {self.current_time}'
                    f' with timestamp {request_body.timestamp}')
        logger.debug(f'Get new order amr {self.amr_id}: {request_body}')
        logger.debug(f'Current order amr {self.amr_id}: {self.order}')
        if self.current_time is None:
            self.current_time = request_body.timestamp
        elif self.current_time < request_body.timestamp:
            self.current_time = request_body.timestamp
        else:
            # best case
            pass

        all_action_states_finish = True
        for action_state in self.action_states:
            if action_state.actionStatus != ActionStatus.FINISHED:
                all_action_states_finish = False
                break
        if config.config_file.CHARGE_MANAGEMENT_ACTIVE:
            if self.order == request_body.order.orderId:
                self.plan_order_update(request_body)
            else:
                self.plan_order_new(request_body)
            return
        # 1 Initial no Order
        if self.order_id == '':
            self.plan_order_new(request_body)
        # 2 Finish order, but get same orderId
        elif (len(self.node_states) == 0 and len(self.edge_states) == 0 and all_action_states_finish is True and
              self.order_id == request_body.order.orderId and len(self.action_states) > 1):
            logger.info('Order is already finish!')
            logger.info(f'Get same order {self.order_id} after finishing again. Do not process order!')
        # 3 Finish order
        elif ((len(self.node_states) == 0 and len(self.edge_states) == 0 and all_action_states_finish is True) or
              (config.config_file.TASK_ASSIGNMENT_STRATEGY == TaskAssignmentStrategy.central)):
            self.plan_order_new(request_body)
        else:
            self.plan_order_update(request_body)
        return

    def plan_order_new(self, request_body: OrderStateRequest):
        """
        :param request_body: Get OrderStateRequest for execute a new order received via mqtt according vda5050
        :return: plan order new after finish a previous order or get the first order
        """
        # 1. Set order to process
        self.order = request_body.order
        # 2. transform order route to states & update information
        self.order_id = request_body.order.orderId
        self.order_update_id = request_body.order.orderUpdateId
        self.last_node_sequence_id = request_body.order.nodes[0].sequenceId
        node_states_list = []
        action_states_list = []
        edge_states_list = []
        for node in request_body.order.nodes:
            node_states_list.append(NodeState(nodeId=node.nodeId, sequenceId=node.sequenceId,
                                              nodePosition=node.nodePosition, released=node.released))
            for action in node.actions:
                node_states_list[-1].nodeDescription = 'Action'
                action_states_list.append(ActionState(actionId=action.actionId,
                                                      actionStatus=ActionStatus.WAITING,
                                                      actionType=action.actionType))
        for edge in request_body.order.edges:
            edge_states_list.append(EdgeState(edgeId=edge.edgeId, sequenceId=edge.sequenceId,
                                              released=edge.released))
            for action in edge.actions:
                action_states_list.append(ActionState(actionId=action.actionId,
                                                      actionStatus=ActionStatus.WAITING,
                                                      actionType=action.actionType))
        self.node_states = node_states_list
        self.edge_states = edge_states_list
        self.action_states = action_states_list
        if 'pickup_time' not in self.orders_dict[self.order_id]:
            self.orders_dict[self.order_id]['pickup_time'] = self.current_time + self.time_simulation_step
        return

    def plan_order_update(self, request_body: OrderStateRequest):
        """
        :param request_body: Get OrderStateRequest for execute a new order received via mqtt according vda5050
        :return: plan order new during execution for an order update
        """
        if (self.last_node_sequence_id == request_body.order.nodes[0].sequenceId and
                request_body.order.nodes[0].nodeId == self.last_node_id):
            self.plan_order_new(request_body)
        elif self.last_node_sequence_id > request_body.order.nodes[0].sequenceId:
            for index, node in enumerate(request_body.order.nodes):
                if node.sequenceId < self.last_node_sequence_id:
                    del request_body.order.nodes[index]
            for index, edge in enumerate(request_body.order.edges):
                if edge.sequenceId < self.last_node_sequence_id:
                    del request_body.order.edges[index]
            if len(request_body.order.nodes) > 0:
                if self.last_node_id == request_body.order.nodes[0].nodeId:
                    self.plan_order_new(request_body)
        else:  # Missing order steps
            logger.info(f'New order {request_body}')
            logger.info(f'Current order: {self.order}')
            logger.info(f'Last node information: {self.last_node_id}, {self.last_node_sequence_id}')
            raise Exception(f'Error: Missing order steps for order {request_body.order.orderId}, '
                            f'because first sequence id is higher as last sequence id here')

    def simulation_step(self):
        """
        :return: Execute one simulation step of the scenario
                 1. Execute all actions of the current node (important for the first node of an order)
                 2. AMR drive to the next node
                 3. Execute all actions of the next node
        """
        if len(self.path) == 0:
            self.path.append((self.last_node_id, self.current_time, self.order_id))
        self.drive_time = datetime.timedelta(seconds=0)
        self.finished_action_in_step = 0
        self.time_simulation_step = datetime.timedelta(seconds=0)
        loaded_time = datetime.timedelta(seconds=0)
        unloaded_time = datetime.timedelta(seconds=0)
        self.visited_edge_ids = []
        self.visited_node_ids = []
        # 1. Check if amr has order to execute and also check that order is not finish
        all_action_states_finish = True
        for action_state in self.action_states:
            if action_state.actionStatus != ActionStatus.FINISHED:
                all_action_states_finish = False
                break
        if self.order is None or (len(self.node_states) == 0 and len(self.edge_states) == 0 and
                                  all_action_states_finish is True):
            self.current_time += datetime.timedelta(seconds=config.config_file.WAITING_TIME_ON_NODE)
            return (False, self.finished_action_in_step, datetime.timedelta(seconds=0), datetime.timedelta(seconds=0),
                    [], [])
        else:
            # 2. Check if last node id equal to current node id of order
            if len(self.order.nodes) > 0:
                if self.last_node_id == self.order.nodes[0].nodeId:
                    self.current_node = self.order.nodes[0]
                    # 3. Execute Actions on current node at the beginning
                    self.execute_actions_on_current_node()
                    self.current_time += self.time_simulation_step
                    self.time_simulation_step = datetime.timedelta(seconds=0)
                    # self.send_state_update()
                    # 4. Drive to next node
                    self.simulate_movement_amr()  # One timestep
                    # 5 For statistics compute service time based on drive time
                    if self.loaded is True:
                        loaded_time = self.drive_time
                    else:
                        unloaded_time = self.drive_time

                    self.current_time += self.time_simulation_step
                    self.time_simulation_step = datetime.timedelta(seconds=0)
                    logger.info(f'AMR {self.amr_id} arrives next node at {self.current_time}')

                    # 6. Execute Actions on next node
                    self.execute_actions_on_current_node()
                    # for last node
                    if len(self.order.nodes) == 1 and len(self.node_states) == 1:
                        del self.order.nodes[0]
                        del self.node_states[0]
                else:
                    self.time_simulation_step += datetime.timedelta(seconds=config.config_file.WAITING_TIME_ON_NODE)
                    logger.info(f'Error: AMR {self.amr_id} stay not on the right node and do nothing')
            else:
                self.time_simulation_step += datetime.timedelta(seconds=config.config_file.WAITING_TIME_ON_NODE)
                logger.info(f'AMR {self.amr_id} stay not on the right node and do nothing for order {self.order_id}')
                logger.info(f'AMR {self.amr_id} Problem, Order {self.order}, Node States: {self.node_states},'
                            f' Edge States: {self.edge_states}, Action States: {self.action_states}')
            # 7. Update current time
            self.current_time += self.time_simulation_step
            self.path.append((self.last_node_id, self.current_time, self.order_id))
        return (True, self.finished_action_in_step, loaded_time, unloaded_time, self.visited_edge_ids,
                self.visited_node_ids)

    def execute_actions_on_current_node(self):
        """
        :return: Method for execute all actions of the current node
        """
        next_action_index = self.get_next_action_index()
        if next_action_index is not None:
            self.action_states[next_action_index].actionStatus = ActionStatus.INITIALIZING
        while len(self.current_node.actions) > 0:
            self.driving = False  # AMR must stop to execute actions
            self.velocity = Velocity(vx=0, vy=0, omega=0)
            logger.info(f'AMR {self.amr_id} started to execute Action {self.current_node.actions[0].actionId} for '
                        f'{self.current_node.actions[0].actionType} on node {self.current_node.nodeId} for order '
                        f'{self.order_id}')
            self.action_states[next_action_index].actionStatus = ActionStatus.RUNNING
            for action_param in self.current_node.actions[0].actionParameters:
                if action_param.key == 'duration':
                    self.time_simulation_step += datetime.timedelta(seconds=action_param.value)
                if action_param.key == "goal_charge":
                    mpp = self.battery_state.reach /self.battery_state.batteryCharge
                    self.battery_state.batteryCharge = float(action_param.value)
                    self.battery_state.reach = float(min(self.battery_max_reach, action_param.value * mpp))
            logger.info(f'AMR {self.amr_id} finished Action {self.current_node.actions[0].actionId} for '
                        f'{self.current_node.actions[0].actionType} on node {self.current_node.nodeId} for order '
                        f'{self.order_id}')
            if self.current_node.actions[0].actionType == 'pick':
                self.loaded = True
            if self.current_node.actions[0].actionType == 'drop':
                self.loaded = False
                self.finished_action_in_step += 1
                if 'dropoff_time' not in self.orders_dict[self.order_id]:
                    self.orders_dict[self.order_id]['dropoff_time'] = self.current_time + self.time_simulation_step
            del self.current_node.actions[0]
            self.action_states[next_action_index].actionStatus = ActionStatus.FINISHED
            next_action_index = self.get_next_action_index()
            if next_action_index is not None:
                self.action_states[next_action_index].actionStatus = ActionStatus.INITIALIZING
            else:
                # If last action finish, set sequence id to 0
                self.last_node_sequence_id = 0

    def simulate_movement_amr(self):
        """
        :return: Method for simulate movement of the amr, this means drive to the next node
        """
        logger.debug(f'Delete Node states {self.order.nodes[0].nodeId}')
        node_copy = copy.deepcopy(self.order.nodes[0])
        node_state_copy = copy.deepcopy(self.node_states[0])
        if config.config_file.CHARGE_MANAGEMENT_ACTIVE and self.order.edges[0].length > self.battery_state.reach:
            logger.info(f"ERROR: The amr {self.amr_id} has not enough reach to drive to its destination.")
            return
        del self.order.nodes[0]
        del self.node_states[0]
        if len(self.order.nodes) > 0:
            if (self.order.nodes[0].released is True and self.order.nodes[0].nodeId == self.last_node_id):
                # Stay on the same node for one time step + waiting time
                self.wait_on_current_node()
            elif (self.order.nodes[0].released is True and self.order.edges[0].released is True and
                    self.check_collisions(self.order.edges[0].edgeId, 'edge') is False and
                    self.check_collisions(self.order.nodes[0].nodeId, 'node') is False): # and check collisions
                # Drive to next node
                self.drive_to_next_node()
            else:
                # Do nothing, maybe the same as first
                self.visited_node_ids.append(self.last_node_id)
                self.order.nodes.insert(0, node_copy)
                self.node_states.insert(0, node_state_copy)
                self.time_simulation_step += datetime.timedelta(seconds=config.config_file.WAITING_TIME_ON_NODE)

    def wait_on_current_node(self):
        """
        :return: Wait on the current node to avoid conflict one timestep
        """
        self.time_simulation_step += datetime.timedelta(seconds=config.config_file.WAITING_TIME_ON_NODE)
        logger.info(f'AMR {self.amr_id} stay on same node {self.order.nodes[0].nodeId}')
        self.current_node = self.order.nodes[0]
        self.last_node_id = self.order.nodes[0].nodeId
        self.last_node_sequence_id = self.order.nodes[0].sequenceId
        self.visited_node_ids.append(self.last_node_id)
        self.amr_position = AMRPosition(x=self.order.nodes[0].nodePosition.x,
                                        y=self.order.nodes[0].nodePosition.y,
                                        mapId=self.order.nodes[0].nodePosition.mapId,
                                        positionInitialized=False)

    def drive_to_next_node(self):
        """
        :return: Method to drive to the next node
        """
        # Drive to next node
        if self.order.nodes[0].released is True and self.check_collisions(self.order.nodes[0].nodeId, 'node') is False:
            drive_time_edge = datetime.timedelta(seconds=self.order.edges[0].length /
                                                 min(self.order.edges[0].maxSpeed, self.speed_max))
            self.time_simulation_step += drive_time_edge
            self.drive_time = drive_time_edge
            self.battery_state.reach -= int(self.order.edges[0].length)
            self.battery_state.batteryCharge = int(
                (self.battery_state.reach / self.battery_max_reach) * 100)
            self.occupied_graph_ids.edgeIds.append(self.order.edges[0].edgeId)
            self.visited_edge_ids.append(self.order.edges[0].edgeId)
            del self.edge_states[0]
            del self.order.edges[0]
            logger.info(f'AMR {self.amr_id} arrives next node {self.order.nodes[0].nodeId} for order {self.order_id}')
            self.occupied_graph_ids.nodeIds.append(self.order.nodes[0].nodeId)
            self.visited_node_ids.append(self.order.nodes[0].nodeId)
            self.current_node = self.order.nodes[0]
            self.last_node_id = self.order.nodes[0].nodeId
            self.last_node_sequence_id = self.order.nodes[0].sequenceId
            self.amr_position = AMRPosition(x=self.order.nodes[0].nodePosition.x,
                                            y=self.order.nodes[0].nodePosition.y,
                                            mapId=self.order.nodes[0].nodePosition.mapId,
                                            positionInitialized=False)
        else:
            self.time_simulation_step += datetime.timedelta(seconds=config.config_file.WAITING_TIME_ON_NODE)
            self.visited_node_ids.append(self.last_node_id)

    def send_state_update(self):
        """
        :return: Method to send state update via vda5050
        """
        amr_state_request = AMRStateVDA(orderId=self.order_id,
                                        orderUpdateId=self.order_update_id,
                                        lastNodeId=self.last_node_id,
                                        lastNodeSequenceId=self.last_node_sequence_id,
                                        driving=self.driving,
                                        paused=self.paused,
                                        distanceSinceLastNode=self.distance_since_last_node,
                                        operatingMode=self.operating_mode,
                                        agvPosition=self.amr_position,
                                        velocity=self.velocity,
                                        loads=self.loads,
                                        batteryState=self.battery_state,
                                        nodeStates=self.node_states,
                                        edgeStates=self.edge_states,
                                        actionStates=self.action_states,
                                        errors=[],
                                        safetyState=SafetyState(eStop=EStop.AUTOACK, fieldViolation=False))
        self.mqtt_send_state_to_amr_com(amr_state_request)

    def send_connection_update(self):
        """
        :return: : Method to send connection state update via vda5050
        """
        connection_state_request = ConnectionStateVDA(connectionState=self.connection_state)
        self.mqtt_send_connection_state_to_amr_com(connection_state_request)

    def get_next_action_index(self):
        """
        :return: Method to get the index of the action state list for the next action
        """
        action_state_index = None
        # search action index next action on current node
        if len(self.current_node.actions) > 0:
            for i, action_state in enumerate(self.action_states):
                if action_state.actionId == self.current_node.actions[0].actionId:
                    action_state_index = i
        else:  # search action index next action on next available action oin order
            for node in self.order.nodes:
                if len(node.actions) > 0:
                    for i, action_state in enumerate(self.action_states):
                        if action_state.actionId == node.actions[0].actionId:
                            action_state_index = i
        return action_state_index

    def mqtt_send_state_to_amr_com(self, request_body: AMRStateVDA):
        """
        :return: Method to send state update via vda5050
        """
        timestamp = self.current_time.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00',
                                                                                                              'Z')
        amr_state_obj = StateUpdateVDABodyHeader(headerId=self.header_id.id,
                                                 timestamp=timestamp,
                                                 version='v2',
                                                 manufacturer='fzi',
                                                 serialNumber=self.amr_id,
                                                 orderId=request_body.orderId,
                                                 orderUpdateId=request_body.orderUpdateId,
                                                 zoneId=request_body.zoneId,
                                                 lastNodeId=request_body.lastNodeId,
                                                 lastNodeSequenceId=request_body.lastNodeSequenceId,
                                                 driving=request_body.driving,
                                                 paused=request_body.paused,
                                                 newBaseRequest=request_body.newBaseRequest,
                                                 distanceSinceLastNode=request_body.distanceSinceLastNode,
                                                 operatingMode=request_body.operatingMode,
                                                 nodeStates=request_body.nodeStates,
                                                 edgeStates=request_body.edgeStates,
                                                 agvPosition=request_body.agvPosition,
                                                 velocity=request_body.velocity,
                                                 loads=request_body.loads,
                                                 actionStates=request_body.actionStates,
                                                 batteryState=request_body.batteryState,
                                                 errors=request_body.errors,
                                                 information=request_body.information,
                                                 safetyState=request_body.safetyState)
        self.header_id.id += 1
        logger.debug(f'AMR {self.amr_id} send AMR State to Fleet-Management-System at {self.current_time}'
                     f' with header id {self.header_id.id - 1}')
        if config.config_file.USE_MQTT is True and config.config_file.SIMULATION_ACTIVE is True:
            payload = json.dumps(
                amr_state_obj.dict(exclude_none=True),
                default=lambda o: serialize_json(o)
            )
            self.fast_mqtt.publish(f"flextools/v2/fzi/{self.amr_id}/state", payload)  # publishing mqtt topic
            return {"result": True, "message": "Published"}
        else:
            send_state_update_to_amr_communication(amr_state_obj)
            return

    def mqtt_send_connection_state_to_amr_com(self, request_body: ConnectionStateVDA):
        """
        :return: Method to send connection state update via vda5050
        """
        timestamp = self.current_time.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00',
                                                                                                              'Z')
        connections_state_obj = ConnectionStateVDABodyHeader(headerId=self.header_id.id,
                                                             timestamp=timestamp,
                                                             version='v2',
                                                             manufacturer='fzi',
                                                             serialNumber=self.amr_id,
                                                             connectionState=request_body.connectionState)
        self.header_id.id += 1
        payload = json.dumps(
            connections_state_obj.dict(exclude_none=True),
            default=lambda o: serialize_json(o)
        )

        logger.debug(f'AMR {self.amr_id} send connection update to Fleet-Management-System')
        if config.config_file.USE_MQTT is True and config.config_file.SIMULATION_ACTIVE is True:
            self.fast_mqtt.publish(f"flextools/v2/fzi/{self.amr_id}/connection", payload)  # publishing mqtt topic
        return {"result": True, "message": "Published"}

    def get_nodes_for_staying(self):
        """
        :return: Method to get nodes for waiting amr in the next simulation step, important to avoid conflicts
        """
        if self.order is not None:
            if len(self.order.nodes) > 1:
                if self.order.nodes[0].nodeId == self.order.nodes[1].nodeId:
                    return self.order.nodes[0].nodeId
                else:
                    return None
            else:
                return self.last_node_id  # stay on this position
        else:
            return self.last_node_id

    def check_collisions(self, part_id: str, node_or_edge: str) -> bool:
        """
        :param part_id: node_id or edge_id for check collision
        :param node_or_edge: node or edge
        :return: bool, true for a conflict
        """
        if self.occupied_graph_ids.checkCollisions is False:
            return False
        else:
            if node_or_edge == 'node':
                if part_id in self.occupied_graph_ids.nodeIds:
                    logger.info(f'Collision detected on Node {part_id} AMR {self.amr_id} waiting!')
                    return True
                else:
                    return False
            elif node_or_edge == 'edge':
                if part_id in self.occupied_graph_ids.edgeIds:
                    logger.info(f'Collision detected on Edge {part_id}, AMR {self.amr_id} waiting!')
                    return True
                else:
                    return False
            else:
                return False
