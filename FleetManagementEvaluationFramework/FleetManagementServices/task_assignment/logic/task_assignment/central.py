import copy
from typing import List
import logging

from scipy.optimize import linear_sum_assignment
from api.client_api import get_travel_time_matrix, get_parking_nodes, set_reposition_order
from api.client_api_models import OrderUpdateRequest, TravelTimeMatrixRequest, ParkingNodesRequest, RepositionOrder
from api.server_api_models import NewOrderInfo, StoredOrderInfo
from data.models import ActionIdCounter, Order, Node, RoutingRequestObject, RoutingAMRInfo, Token, \
    SystemStateAMR, NodePosition
from interfaces.task_assignment_interface import TaskAssignment
from logic.api_services.general_task_assignment_functions import transform_order_info_to_order,  \
     setup_ttm

import config.config_file

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class Central(TaskAssignment):
    def __init__(self, action_id_counter: ActionIdCounter):
        self.stored_orders = {}
        self.action_id_counter = action_id_counter
        self.ttm_layouts = {}
        self.ttm = None
        self.layout_id = None
        self.reposition_order_id = 1
        self.assigned_tasks = []
        self.executed_tasks = {}  # {orderId: amrId}
        self.executed_delivery_positions = {}  # {orderId: delivery_node_id}
        self.free_agents = []
        self.parking_nodes = []
        self.endpoints = []
        self.subset_unexecuted_tasks = []
        self.amr_states = {}
        self.reserved_nodes = {}

    def dispatch(self, new_order_info: NewOrderInfo):
        """
        :param new_order_info: info about new order
        :return: add new order to order pool, where amr's can request orders
        """
        # get order from new_order_info object
        order = transform_order_info_to_order(new_order_info, action_id=self.action_id_counter.nextActionId).dict()
        order = Order(**order)
        if new_order_info.layoutId not in self.ttm_layouts.keys():  # Load ttm
            self.ttm_layouts[new_order_info.layoutId] = setup_ttm(
                get_travel_time_matrix(TravelTimeMatrixRequest(
                    mapId=new_order_info.layoutId)).json())
        # set ttm used for dispatch order
        self.ttm = self.ttm_layouts[new_order_info.layoutId]

        self.layout_id = new_order_info.layoutId


        self.stored_orders[order.orderId] = StoredOrderInfo(order=order, orderInfo=new_order_info)
        self.action_id_counter.nextActionId += 2

        planned_order_update = OrderUpdateRequest(amrId=None,
                                                  order=order,
                                                  index=None,
                                                  estimatedStartTime=None,
                                                  estimatedEndTime=None)
        return planned_order_update

    def process_central_after_timestep(self, all_amr_states: List[SystemStateAMR]):
        logger.info(f'Start requesting order; Executed task at the moment: {self.executed_tasks};'
                    f' Free agents: {self.free_agents}')
        new_order_list = {}
        delivery_order_list = []
        plan_order_ids = []
        new_order_ids = []
        # Update system state for each request in this class
        for amr_state in all_amr_states:
            if (amr_state.amrState.amrId not in self.executed_tasks.values() and amr_state.amrState.amrId
                    not in self.free_agents):
                self.free_agents.append(amr_state.amrState.amrId)
            self.amr_states[amr_state.amrState.amrId] = amr_state
        logger.info(f'Free agents: {self.free_agents}')
        if len(self.executed_tasks.keys()) > 0:
            for executed_order_id in self.executed_tasks.keys():
                node_list_of_order = []
                for node in self.stored_orders[executed_order_id].order.nodes:
                    if len(node.actions) > 0:
                        for action in node.actions:
                            # if action.actionType == 'pick':
                            #     node_list_of_order.append(node)
                            if action.actionType == 'drop':
                                node_list_of_order.append(node)

                new_order_list[self.executed_tasks[executed_order_id]] = Order(orderId=executed_order_id,
                                                                               orderUpdateId=0,
                                                                               nodes=node_list_of_order,
                                                                               edges=[])
                plan_order_ids.append(executed_order_id)
                delivery_order_list.append(executed_order_id)

        if len(self.stored_orders.keys()) > 0:
            # iterate over state of all amr
            for amr_state in all_amr_states:
                # Check amr_position is pickup location of unexecuted task and task not assigned to other agents
                for order_id, order_info in self.stored_orders.items():
                    if (amr_state.amrState.lastNodeId == order_info.orderInfo.sourceId and
                            order_id not in self.executed_tasks and
                            amr_state.amrState.amrId not in self.executed_tasks.values() and
                            order_info.orderInfo.sinkId not in self.executed_delivery_positions.values()):
                        self.executed_tasks[order_id] = amr_state.amrState.amrId
                        self.executed_delivery_positions[order_id] = order_info.orderInfo.sinkId
                        node_list_of_order = []
                        for node in order_info.order.nodes:
                            if len(node.actions) > 0:
                                for action in node.actions:
                                    if action.actionType == 'pick':
                                        node_list_of_order.append(node)
                                    if action.actionType == 'drop':
                                        node_list_of_order.append(node)
                        new_order_list[amr_state.amrState.amrId] = Order(orderId=order_id, orderUpdateId=0,
                                                                         nodes=node_list_of_order, edges=[])
                        # delete agent from free agent list
                        self.free_agents.remove(amr_state.amrState.amrId)
                        delivery_order_list.append(order_id)
                        plan_order_ids.append(order_id)
                        new_order_ids.append(order_id)
                        break

        if len(self.free_agents) > 0 and self.layout_id is not None:
            self.create_subset_unexecuted_tasks()
            # Create Endpoint set
            self.create_endpoint_set()
            # Build cost matrix
            cost_matrix = self.build_cost_matrix()
            # Assign Endpoints to free agents with hungarian method
            assignment, cost_matrix = self.hungarian_method(cost_matrix)
            # The form with assignments order objects
            for agent_endpoint_tuple in assignment:
                logger.debug(f'Agent endpoint tuple: {agent_endpoint_tuple},'
                             f' parking node: {self.endpoints[agent_endpoint_tuple[1]]}, '
                             f'AMR {self.free_agents[agent_endpoint_tuple[0]]}'
                             f'Costs {cost_matrix[agent_endpoint_tuple[0]][agent_endpoint_tuple[1]]}')
                if self.endpoints[agent_endpoint_tuple[1]] in self.parking_nodes:
                    node_position_parts = str(self.endpoints[agent_endpoint_tuple[1]]).split('_')
                    node_position = NodePosition(x=float(node_position_parts[1]), y=float(node_position_parts[2]),
                                                 mapId=self.layout_id)
                    new_order_list[self.free_agents[agent_endpoint_tuple[0]]] =\
                        Order(orderId=f'RePo{self.reposition_order_id}',
                              orderUpdateId=0,
                              nodes=[Node(nodeId=self.endpoints[agent_endpoint_tuple[1]],
                                          sequenceId=0, released=True, nodePosition=node_position, actions=[])],
                              edges=[])

                    set_reposition_order(RepositionOrder(amrId=self.free_agents[agent_endpoint_tuple[0]],
                                                         order=new_order_list[
                                                             self.free_agents[agent_endpoint_tuple[0]]]))
                    plan_order_ids.append(f'RePo{self.reposition_order_id}')
                    self.reposition_order_id += 1
                else:
                    logger.info(f'Subset unexecuted tasks: {self.subset_unexecuted_tasks};'
                                f' Agent endpoint index: {agent_endpoint_tuple[1]},'
                                f'Index 0: {agent_endpoint_tuple[0]}')
                    node_position_parts = str(self.endpoints[agent_endpoint_tuple[1]]).split('_')
                    node_position = NodePosition(x=float(node_position_parts[1]), y=float(node_position_parts[2]),
                                                 mapId=self.layout_id)
                    node_list_of_order = [Node(nodeId=self.endpoints[agent_endpoint_tuple[1]],
                                          sequenceId=0, released=True, nodePosition=node_position, actions=[])]
                    new_order_list[self.free_agents[agent_endpoint_tuple[0]]] =\
                        Order(orderId=self.subset_unexecuted_tasks[agent_endpoint_tuple[1]],
                              orderUpdateId=0, nodes=node_list_of_order, edges=[])
                    plan_order_ids.append(self.subset_unexecuted_tasks[agent_endpoint_tuple[1]])

        if len(new_order_list.keys()) > 0:
            routing_object = self.get_routing_object(new_order_list, delivery_order_list, plan_order_ids, new_order_ids)
        else:
            routing_object = None
        logger.info(f'Finish requesting order, executed task after routing request: {self.executed_tasks}')
        return routing_object

    def create_subset_unexecuted_tasks(self):
        executed_tasks_sinks = [self.stored_orders[order_id].orderInfo.sinkId for order_id in self.executed_tasks]
        unexecuted_tasks = {
            order_id: order_info for order_id, order_info in self.stored_orders.items() if
            order_id not in self.executed_tasks
        }
        subset_unexecuted_tasks = set()

        for order_id, order_info in unexecuted_tasks.items():
            sink, source = order_info.orderInfo.sinkId, order_info.orderInfo.sourceId
            if sink in executed_tasks_sinks or source in executed_tasks_sinks:
                continue
            if any(
                    sink == self.stored_orders[unexecuted_order_id].orderInfo.sinkId or
                    sink == self.stored_orders[unexecuted_order_id].orderInfo.sourceId or
                    source == self.stored_orders[unexecuted_order_id].orderInfo.sinkId or
                    source == self.stored_orders[unexecuted_order_id].orderInfo.sourceId
                    for unexecuted_order_id in subset_unexecuted_tasks
            ):
                continue
            subset_unexecuted_tasks.add(order_id)

        self.subset_unexecuted_tasks = list(subset_unexecuted_tasks)

    def create_endpoint_set(self):
        self.endpoints = []
        for order_id in self.subset_unexecuted_tasks:
            self.endpoints.append(self.stored_orders[order_id].orderInfo.sourceId)
        # for order_id in self.executed_delivery_positions.keys():
        #     print(self.executed_delivery_positions[order_id])
        #     self.endpoints.append(self.executed_delivery_positions[order_id])
        logger.info(f'Task End points: {self.endpoints}')
        if len(self.free_agents) > len(self.endpoints):
            needed_parking_points = len(self.free_agents) - len(self.endpoints)
            order_endpoints = copy.deepcopy(self.endpoints)
            # for order_id in self.executed_delivery_positions.keys():
            #     order_endpoints.append(self.executed_delivery_positions[order_id])

            self.parking_nodes = self.get_best_parking_nodes(number_of_parking_nodes=needed_parking_points,
                                                             order_endpoints=order_endpoints)
            logger.info(f'Parking nodes: {self.parking_nodes}')
            for parking_node in self.parking_nodes:
                if self.is_parking_node_reserved(parking_node) is False:
                    self.endpoints.append(parking_node)


    def get_best_parking_nodes(self, number_of_parking_nodes: int, order_endpoints: List[str]) -> List[str]:
        executed_tasks_sinks = [self.stored_orders[order_id].orderInfo.sinkId for order_id in self.executed_tasks]
        no_parking_location_node_ids = executed_tasks_sinks + order_endpoints
        parking_node_res = get_parking_nodes(ParkingNodesRequest(layoutId=self.layout_id,
                                                                 endpoints=no_parking_location_node_ids,
                                                                 numberOfParkingNodes=number_of_parking_nodes)).json()
        parking_nodes_list = parking_node_res['parkingNodes']
        return parking_nodes_list

    def build_cost_matrix(self):
        logger.info(f'Build cost matrix, Free agents: {self.free_agents}')
        logger.debug(f'Endpoints: {self.endpoints}')
        cost_matrix = [[self.compute_costs(free_agent, endpoint) for endpoint in self.endpoints]
                       for free_agent in self.free_agents]
        return cost_matrix

    def compute_costs(self, free_agent: str, endpoint: str) -> float:
        cost_constant = 10000
        base_cost = self.ttm[(self.amr_states[free_agent].amrState.lastNodeId, endpoint)]
        if self.endpoint_is_pickup_location(endpoint):
            cost = len(self.free_agents) * cost_constant * base_cost
        else:
            cost = len(self.free_agents) * cost_constant**2 + base_cost
        return cost

    def endpoint_is_pickup_location(self, endpoint: str) -> bool:
        if endpoint not in self.parking_nodes:
            return True
        else:
            return False

    def hungarian_method(self, cost_matrix):
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        assignment = list(zip(row_ind, col_ind))
        return assignment, cost_matrix

    def get_routing_object(self, new_order_list: dict, delivery_orders: List[str],
                           plan_order_ids: List[str], new_delivery_order_ids: List[str]) -> RoutingRequestObject:
        logger.debug(f'In get routing object, new order list: {new_order_list}; Delivery orders: {delivery_orders};'
                    f' Plan order ids: {plan_order_ids}')
        routing_amr_info_list = []
        for amr_key in new_order_list.keys():
            logger.debug(f'Add routing amr {amr_key} with order {new_order_list[amr_key]}')
            routing_amr_info_list.append(RoutingAMRInfo(amrId=amr_key,
                                                        lastNodeId=self.amr_states[amr_key].amrState.lastNodeId,
                                                        order=new_order_list[amr_key],
                                                        token=Token(amrId=amr_key,
                                                                    tokens=self.amr_states[amr_key].token)))
        routing_object_with_orders = RoutingRequestObject(mapId=self.layout_id, routingAMR=routing_amr_info_list,
                                                          newOrderIds=new_delivery_order_ids,
                                                          planOrderIds=plan_order_ids,
                                                          deliveryOrderIds=delivery_orders)
        logger.debug(f'Routing object: {routing_object_with_orders}')
        return routing_object_with_orders

    def remove_finish_executed_task(self, order_id):
        logger.info(f'In remove order, executed task: {self.executed_tasks}, remove order {order_id}')
        self.free_agents.append(self.executed_tasks[order_id])  # Append agent to set of free agents
        del self.executed_tasks[order_id]
        del self.stored_orders[order_id]
        del self.executed_delivery_positions[order_id]
        return

    def release_order_again(self, order_id):
        logger.info(f'Release order from order {order_id} pool for amr {self.executed_tasks[order_id]}')
        self.free_agents.append(self.executed_tasks[order_id])  # Append agent to set of free agents
        del self.executed_tasks[order_id]
        del self.executed_delivery_positions[order_id]
        return

    def set_reserved_nodes(self, amr_id: str, nodes: List[str]):
        self.reserved_nodes[amr_id] = nodes
        return

    def is_parking_node_reserved(self, node_id: str):
        for amr_id, path in self.reserved_nodes.items():
            if node_id in path:
                return True
        return False
