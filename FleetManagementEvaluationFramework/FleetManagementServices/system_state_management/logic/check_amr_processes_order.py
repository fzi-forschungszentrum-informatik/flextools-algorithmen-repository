import copy
import datetime
import logging
from typing import List
import numpy as np

from api.client_api import request_order_for_amr, request_routes_for_amrs, request_routes_for_instant_orders, \
    delete_order_from_order_pool, request_routes_for_all_amrs, release_order_in_order_pool
from api.client_api_models import RequestOrderAMR, RoutingForOrdersRequest, Token, RoutingStartGoalRequest, \
    DeleteOrderRequest, RoutingRequestObject, RoutingAMRInfo, ReleaseOrderRequest,  StartGoal

from api.server_api_models import PlannedOrder, InstantOrder, InstantOrders
import config.config_file
import data.enums

import data.db_init
from data.enums import ActionStatus
from data.models import Edge, Order, PlannedOrderInfos, NodeState, \
    EdgeState, ActionState, SystemStateAMR, Route, Node
from logic.general_functions import transform_node_json_to_node_object_list, transform_action_json_to_action_object_list
from logic.general_service_functions import get_system_states_for_all_amrs

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def check_amr_for_process_next_order(amr_id: str):
    """
    easier method for check amr processing order for new planned orders
    :param amr_id: considered amr
    :return: planned order or order updates to execute for amr
    """
    planned_order = None
    process_next_order = check_process_order_from_amr(amr_id)
    if process_next_order is True:
        order = data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders[0].order
        planned_order = get_route_for_orders(amr_id, order)
        if planned_order is None:
            return None
        # Set tokens of amr's with planned orders
        update_tokens_from_planned_orders(planned_order)
    return planned_order


def check_amr_for_processing_order_for_new_planned_orders(amr_id: str):
    """
    Currently not used method
    :param amr_id: considered amr
    :return: planned order or order updates to execute for amr
    """
    planned_orders = None
    process_next_order = check_process_next_order(amr_id)
    if process_next_order is True:  # If amr can process next order
        if (config.config_file.TASK_ASSIGNMENT_STRATEGY is not data.enums.TaskAssignmentStrategy.token_passing and
                config.config_file.TASK_ASSIGNMENT_STRATEGY is not data.enums.TaskAssignmentStrategy.central):
            # Get next order from planned order list
            order = data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders[0].order
        else:  # Token Passing strategy: AMR can self request orders
            system_state_list = get_system_states_for_all_amrs()  # Get system state for all amr's
            # Request order from task assignment service
            order = request_order_from_dispatching_service(amr_id, system_state_list)
        if order is None:
            return None
        logger.debug(f'Order {order}')
        planned_orders = get_route_for_orders(amr_id, order)

        if planned_orders is None:
            return None
        # Set tokens of amr's with planned orders
        update_tokens_from_planned_orders(planned_orders)
    return planned_orders


def check_process_order_from_amr(amr_id: str) -> bool:
    process_next_order = False
    if data.db_init.database['system_state_management'].amr_states[amr_id].amrState.orderId == '' and \
            len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) != 0:
        process_next_order = True
    else:
        if len(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.nodeStates) == 0 and \
                len(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.edgeStates) == 0:
            action_status = True
            for action_state in data.db_init.database['system_state_management'].amr_states[
                    amr_id].amrState.actionStates:
                if action_state.actionStatus is not ActionStatus.FINISHED:
                    action_status = False
                    break
            # And all order states are finished
            if action_status is True:
                if len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) != 0:
                    # If planned order list is not empty or amr can self request orders from order pool (token passing)
                    process_next_order = True
    return process_next_order


def check_process_next_order(amr_id: str) -> bool:
    """
    :param amr_id: considered amr
    :return: boolean, whether process next order
    """
    process_next_order = False
    if data.db_init.database['system_state_management'].amr_states[amr_id].amrState.orderId == '' and \
            (len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) != 0 or
             config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing):
        # If amr has currently no order and planned order list for amr is not empty
        process_next_order = True
    else:
        if len(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.nodeStates) == 0 and \
                len(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.edgeStates) == 0:
            # Else if amr has no open node- and edge states
            action_status = True
            for action_state in data.db_init.database['system_state_management'].amr_states[amr_id].amrState.actionStates:
                if action_state.actionStatus is not ActionStatus.FINISHED:
                    action_status = False
                    break
            # And all order states are finished
            if action_status is True:
                if (len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) != 0 or
                        config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing):
                    # If planned order list is not empty or amr can self request orders from order pool (token passing)
                    process_next_order = True
    if process_next_order is False:
        logger.debug(f'Amr {amr_id} do not process next order')
        logger.debug(str('Order id: ' +
                         str(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.orderId)))
        logger.debug(str('Node states' +
                         str(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.nodeStates)))
        logger.debug(str('Edge states' +
                         str(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.edgeStates)))
    return process_next_order


def get_node_and_edge_list_for_order_with_route(route):
    """
    :param route: route object as json file
    :return: toute object with node and edge objects
    """
    node_list_route = transform_node_json_to_node_object_list(route['nodes'])
    edge_list_route = []
    for edge in route['edges']:
        action_list = transform_action_json_to_action_object_list(edge['actions'])
        edge_list_route.append(Edge(edgeId=edge['edgeId'], sequenceId=edge['sequenceId'],
                                    released=edge['released'], startNodeId=edge['startNodeId'],
                                    endNodeId=edge['endNodeId'], maxSpeed=edge['maxSpeed'],
                                    length=edge['length'], actions=action_list))
    return node_list_route, edge_list_route


def request_order_from_dispatching_service(amr_id: str, system_state_list: List[SystemStateAMR]):
    """
    :param amr_id: amr, which requested for new order
    :param system_state_list: system state data of all AMR
    :return: order from order pool in dispatching service, by using token passing strategy
    """
    order_json = request_order_for_amr(RequestOrderAMR(amrId=amr_id, systemStatesAmr=system_state_list)).json()
    if order_json is None:
        return None
    if 'order' in order_json.keys():
        order_json = order_json['order']
    node_list = transform_node_json_to_node_object_list(order_json['nodes'])
    order = Order(orderId=order_json['orderId'], orderUpdateId=order_json['orderUpdateId'],
                  nodes=node_list, edges=[])
    return order


def request_next_order_from_dispatching_service_with_central(system_state_list: List[SystemStateAMR]):
    """
    :param system_state_list: system state data of all AMR
    :return: routing order object from order pool to pickup locations or delivery locations
    """
    routing_json = request_order_for_amr(RequestOrderAMR(systemStatesAmr=system_state_list)).json()
    if routing_json is not None:
        routing_obj = RoutingRequestObject(**routing_json)
    else:
        return None
    return routing_obj


def get_route_for_orders(amr_id: str, order: Order):
    """
    :param amr_id: amr, which requested for new order
    :param order: new order with relevant information
    :return: exact route for amr's after routing request to travel time service
    """
    token_list, current_order_list = get_token_list_and_order_list_for_routing(amr_id, order)
    route_for_order_request_body = RoutingForOrdersRequest(mapId=order.nodes[0].nodePosition.mapId,
                                                           lastNodeAmrId=
                                                           data.db_init.database['system_state_management'].amr_states[
                                                               amr_id].amrState.lastNodeId,
                                                           orders=current_order_list,
                                                           tokens=token_list,
                                                           amrId=amr_id
                                                           )
    routes = request_routes_for_amrs(route_for_order_request_body).json()
    if len(routes[0]['nodes']) == 0 and len(routes[0]['edges']) == 0:
        # no path found
        return None
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing:
        delete_order_from_order_pool(DeleteOrderRequest(orderId=order.orderId))
    logger.debug(f'Routes: {routes}')
    planned_order_update_list = get_planned_order_update_list(amr_id, order, routes)
    logger.debug(f'Planned order update list: {planned_order_update_list}')
    planned_order_update_list = update_sequence_ids_for_order_updates(planned_order_update_list)
    logger.debug(f'Planned order update list: {planned_order_update_list}')
    update_system_states_for_planned_order_update_list(planned_order_update_list)
    return planned_order_update_list


def update_sequence_ids_for_order_updates(planned_order_update_list: List[PlannedOrder]):
    """
    :param planned_order_update_list: List[PlannedOrder] with new route
    :return: List[PlannedOrder] with updated sequence ids for order updates
    """
    for planned_order in planned_order_update_list:
        if planned_order.order.orderId == data.db_init.database['system_state_management'].amr_states[
                planned_order.amrId].amrState.orderId:  # Check if order already exists
            planned_order.order.orderUpdateId = data.db_init.database['system_state_management'].amr_states[
                planned_order.amrId].amrState.orderUpdateId + 1
            if planned_order.order.nodes[0].nodeId == data.db_init.database['system_state_management'].amr_states[
                    planned_order.amrId].amrState.lastNodeId:
                all_action_finished = True
                for action_state in data.db_init.database['system_state_management'].amr_states[
                        planned_order.amrId].amrState.actionStates:
                    if action_state.actionStatus != ActionStatus.FINISHED:
                        all_action_finished = False
                        break
                if (len(data.db_init.database['system_state_management'].amr_states[
                        planned_order.amrId].amrState.nodeStates) != 0 or
                        len(data.db_init.database['system_state_management'].amr_states[
                        planned_order.amrId].amrState.edgeStates) != 0 or all_action_finished is False):
                    sequence_id_shift = data.db_init.database['system_state_management'].amr_states[
                        planned_order.amrId].amrState.lastNodeSequenceId
                    logger.debug(f'For AMR {planned_order.amrId} with order {planned_order.order.orderId} compute sequence'
                                 f' id shift {sequence_id_shift}')
                    for node in planned_order.order.nodes:
                        node.sequenceId += copy.deepcopy(sequence_id_shift)
                    for edge in planned_order.order.edges:
                        edge.sequenceId += copy.deepcopy(sequence_id_shift)

    return planned_order_update_list


def get_token_list_and_order_list_for_routing(amr_id: str, order: Order):
    """
    :param amr_id: considered amr with new order
    :param order: requested new order
    :return: list of tokens for all amr's and order list for all amr's and the last order is the new requested order
    """
    token_list = []
    current_order_list = []
    for amr in data.db_init.database['system_state_management'].amr_states.keys():
        token_list.append(
            Token(amrId=amr, tokens=data.db_init.database['system_state_management'].amr_states[amr].token))
        if amr != amr_id:
            if len(data.db_init.database['system_state_management'].amr_states[amr].plannedOrders) > 0:
                current_order_list.append(
                    data.db_init.database['system_state_management'].amr_states[amr].plannedOrders[0].order)
            else:
                current_order_list.append(Order(orderId='No order', orderUpdateId=-1, nodes=[], edges=[]))
    current_order_list.append(order)
    return token_list, current_order_list


def get_planned_order_update_list(amr_id: str, order: Order, routes):
    """
    Method currently not used
    :param amr_id: considered amr, which requested new order
    :param order: new request order
    :param routes: computed exact routes from travel time service
    :return: planned order update list
    """
    logger.debug(f'Total routes: {routes}')
    # 1. Add last route from new requested order to planned order update list
    planned_order_update_list = [get_planned_order_from_route(amr_id, order, routes[-1])]
    # 2. Check if exists route updates for other orders
    if len(routes) > 1:  # Then a route update for all other amr's
        amr_shift = 0
        for i, amr in enumerate(data.db_init.database['system_state_management'].amr_states.keys()):
            if amr == amr_id:
                amr_shift += 1
                continue
            if routes[i - amr_shift] is None:
                logger.exception(f'No possible route for AMR {amr} found!')
                raise Exception(f'No possible route for AMR {amr} found!')
            planned_order_update_list.append(
                get_planned_order_from_route(amr,
                                             Order(orderId=data.db_init.database['system_state_management'].
                                                   amr_states[amr].amrState.orderId,
                                                   orderUpdateId=data.db_init.database['system_state_management'].
                                                   amr_states[amr].amrState.orderUpdateId,
                                                   nodes=[], edges=[]),
                                             routes[i-amr_shift]))
    return planned_order_update_list


def get_planned_order_from_route(amr_id: str, order: Order, route):
    """
    :param amr_id: considered amr
    :param order: new order
    :param route: computed route of order
    :return: planned order object
    """
    node_list_route, edge_list_route = get_node_and_edge_list_for_order_with_route(route)
    if (len(node_list_route) == 1 and len(node_list_route[0].actions) == 0 and
            config.config_file.TASK_ASSIGNMENT_STRATEGY != data.enums.TaskAssignmentStrategy.central):
        # order is already finish
        order.orderId = ''  # Because order should not send to amr again!
    node_list_route, edge_list_route = get_node_and_edge_list_for_order_with_route(route)
    order.nodes = node_list_route
    order.edges = edge_list_route
    start_time = get_start_time_for_order(amr_id)
    planned_order = PlannedOrder(timestamp=start_time,
                                 amrId=amr_id, order=order)
    return planned_order


def get_start_time_for_order(amr_id: str):
    """
    :param amr_id: considered amr
    :return: the earliest start time of next order for amr
    """
    logger.debug(f'Get start time for amr {amr_id}')
    system_time = data.db_init.database['system_state_management'].system_time
    if (config.config_file.TASK_ASSIGNMENT_STRATEGY != data.enums.TaskAssignmentStrategy.token_passing
            and len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) > 0):
        start_time = max(data.db_init.database['system_state_management'].amr_states[amr_id].
                         plannedOrders[0].estimatedStartTime, system_time.replace(tzinfo=None))
    else:
        start_time = system_time
    return start_time


def update_system_states_for_planned_order_update_list(planned_order_update_list: List[PlannedOrder]):
    """
    :param planned_order_update_list: planned order update list
    :return: system state update, instead of waiting on a state update from the amr's for token passing strategy
    """
    for planned_order in planned_order_update_list:
        if planned_order.order.orderId == '':
            continue
        logger.debug(f'Set planned order in update system state method: {planned_order}')
        node_state_list = []
        edge_state_list = []
        action_state_list = []
        for node in planned_order.order.nodes:
            node_state_list.append(NodeState(nodeId=node.nodeId, sequenceId=node.sequenceId,
                                             nodePosition=node.nodePosition, released=node.released))
            for action in node.actions:
                action_state_list.append(ActionState(actionId=action.actionId, actionStatus=ActionStatus.WAITING,
                                                     actionType=action.actionType))
        for edge in planned_order.order.edges:
            edge_state_list.append(
                EdgeState(edgeId=edge.edgeId, sequenceId=edge.sequenceId, released=edge.released))
            for action in edge.actions:
                action_state_list.append(ActionState(actionId=action.actionId, actionStatus=ActionStatus.WAITING,
                                                     actionType=action.actionType))
        data.db_init.database['system_state_management'].amr_states[planned_order.amrId].amrState.orderId =\
            planned_order.order.orderId
        data.db_init.database['system_state_management'].amr_states[planned_order.amrId].amrState.orderUpdateId =\
            planned_order.order.orderUpdateId
        data.db_init.database['system_state_management'].amr_states[planned_order.amrId].amrState.nodeStates =\
            node_state_list
        data.db_init.database['system_state_management'].amr_states[planned_order.amrId].amrState.edgeStates =\
            edge_state_list
        data.db_init.database['system_state_management'].amr_states[planned_order.amrId].amrState.actionStates =\
            action_state_list
        if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing:
            if len(data.db_init.database['system_state_management'].amr_states[planned_order.amrId].plannedOrders) > 0:
                if planned_order.order.orderId == data.db_init.database['system_state_management'].amr_states[
                        planned_order.amrId].plannedOrders[0].order.orderId:
                    del data.db_init.database['system_state_management'].amr_states[
                        planned_order.amrId].plannedOrders[0]
            if planned_order.order.orderId != '':
                data.db_init.database['system_state_management'].amr_states[
                    planned_order.amrId].plannedOrders.insert(0, PlannedOrderInfos(order=planned_order.order))
                logger.debug(f'Add order to planned order list in system state management:'
                             f' {PlannedOrderInfos(order=planned_order.order)}')
    return


def update_tokens_from_planned_orders(planned_orders: List[PlannedOrder]):
    """
    :param planned_orders: planned order list
    :return: update tokens in system state
    """
    for planned_order in planned_orders:
        logger.debug(f'Planned order in update tokens: {planned_order}')
        tokens = transform_planned_order_to_token_list(planned_order)
        data.db_init.database['system_state_management'].amr_states[planned_order.amrId].token = tokens
        logger.debug(str(f'Add token to system state of amr {planned_order.amrId},' +
                         str(data.db_init.database['system_state_management'].amr_states[planned_order.amrId].token)))
    return


def transform_planned_order_to_token_list(planned_order: PlannedOrder):
    """
    :param planned_order: planned order list
    :return: transform information of planned order list to tokens for the amr's
    """
    tokens = []
    for node in planned_order.order.nodes:
        tokens.append(node.nodeId)
        if len(node.actions) > 0:
            tokens.append('Event')
    return tokens


def plan_processing_instant_orders(instant_orders: InstantOrders):
    """
    At the moment not used
    :param instant_orders: Instant Order
    :return: List[PlanedOrder]
    """
    # Generate RoutingStartGoalRequest
    start_point_list = determine_start_point_list()
    goal_list, order_list, amr_list = determine_goals_from_instant_orders(instant_orders.instantOrders)
    routing_request = RoutingStartGoalRequest(starts=start_point_list,
                                              goals=goal_list,
                                              orders=order_list,
                                              mapId=instant_orders.instantOrders[0].order.nodes[0].nodePosition.mapId)
    routes = request_routes_for_instant_orders(routing_request).json()
    routes_list = [Route(**route) for route in routes]
    planned_order_list = get_planned_orders_from_routes(routes_list, order_list, amr_list)

    update_tokens_from_planned_orders(planned_order_list)
    return planned_order_list


def determine_start_point_list():
    """
    :return: Determine start point list for routing of all amr
    """
    start_point_list = []
    for amr_id in data.db_init.database['system_state_management'].amr_states.keys():
        start_point_list.append(data.db_init.database['system_state_management'].amr_states[amr_id].amr_state.lastNodeId)
    return start_point_list


def determine_goals_from_instant_orders(instant_orders: List[InstantOrder]):
    """
    Currently not used
    :param instant_orders: List[InstantOrder]
    :return: Determine goals for routing of all amr
    """
    goal_list = []
    order_list = []
    amr_list = []
    for instant_order in instant_orders:
        goal_list.append(instant_order.order.nodes[-1].nodeId)
        order_list.append(instant_order.order)
        amr_list.append(instant_order.amrId)
    return goal_list, order_list, amr_list


def get_planned_orders_from_routes(routes: List[Route], order_list: List[Order], amr_id_list: List[str]):
    """
    :param routes: List[Route]
    :param order_list:  List[Order]
    :param amr_id_list: str
    :return: List[PlannedOrder]
    """
    planned_order_list = []
    for index, route in enumerate(routes):
        start_time_order = data.db_init.database['system_state_management'].amr_states[amr_id_list[index]].plannedOrders[0].estimatedStartTime
        start_time_system = data.db_init.database['system_state_management'].system_time + datetime.timedelta(milliseconds=1)
        if start_time_order is not None:
            start_time = max(start_time_order, start_time_system)
        else:
            start_time = start_time_system
        order = Order(orderId=order_list[index].orderId, orderUpdateId=order_list[index].orderUpdateId,
                      nodes=route.nodes, edges=route.edges)
        planned_order_list.append(PlannedOrder(timestamp=start_time,
                                               amrId=amr_id_list[index],
                                               order=copy.deepcopy(order)))
    return planned_order_list


def check_amr_for_execute_new_orders():
    """
    :return: Method to check all amr for plan and execute new orders
             1. Create RoutingRequest Object with new orders, currently executed orders
             2. Get planned order list with routes
             3. Update tokens
    """
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central:
        system_state_list = get_system_states_for_all_amrs()
        routing_request_object = request_next_order_from_dispatching_service_with_central(system_state_list)
        if routing_request_object is None:
            return None

        start_goal_list = []
        for routing_order in routing_request_object.routingAMR:
            start_goal_list.append(StartGoal(start_node_id=routing_order.lastNodeId,
                                             goal_node_id=routing_order.order.nodes[-1].nodeId))

        if (config.config_file.PATH_PLANNING_INTEGRATION == data.enums.
                PathPlanningIntegration.two_stage):
            planned_orders_list_new = two_stage_routing_object(routing_request_object)
        else:  # Else: Always complete CBS instance
            planned_orders_list_new = get_routes_for_all_amr(routing_request=routing_request_object,
                                                             order_index_list=[])
    else:
        routing_amr_info_list = []
        new_planned_order_ids = []
        order_index_list = []
        mapId = None
        for amr_id, amr_state in data.db_init.database['system_state_management'].amr_states.items():
            process_next_order = check_process_next_order(amr_id)
            logger.info(f'Process next order AMR {amr_id}: {process_next_order}')
            if process_next_order is True:  # If amr can process next order
                order = None
                if config.config_file.TASK_ASSIGNMENT_STRATEGY != data.enums.TaskAssignmentStrategy.token_passing:
                    # Get next order from planned order list
                    if len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) > 0:
                        order = copy.deepcopy(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders[0].order)
                        new_planned_order_ids.append(order.orderId)
                        order_index_list.append(order.orderId)
                else:  # Token Passing strategy: AMR can self request orders
                    system_state_list = get_system_states_for_all_amrs()  # Get system state for all amr's
                    # Request order from dispatching service
                    order = request_order_from_dispatching_service(amr_id, system_state_list)
                    if order is not None:
                        new_planned_order_ids.append(order.orderId)
                        order_index_list.append(order.orderId)
                if mapId is None and order is not None:
                    mapId = order.nodes[0].nodePosition.mapId
            else:
                if len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders) > 0:
                    order = copy.deepcopy(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders[0].order)
                    order_index_list.append(order.orderId)
                    if mapId is None:
                        mapId = order.nodes[0].nodePosition.mapId
                else:
                    order = Order(orderId='No order', orderUpdateId=-1, nodes=[], edges=[])
                    order_index_list.append(order.orderId)
            if order is None:
                order = Order(orderId='No order', orderUpdateId=-1, nodes=[], edges=[])
                order_index_list.append(order.orderId)
            routing_amr_info_list.append(RoutingAMRInfo(amrId=amr_id,
                                                        lastNodeId=amr_state.amrState.lastNodeId,
                                                        order=order,
                                                        token=Token(amrId=amr_id,
                                                                    tokens=data.db_init.database[
                                                                        'system_state_management'].amr_states[amr_id].token)
                                                        ))
        if mapId is None:  # No new order available
            return None
        routing_request_object = RoutingRequestObject(mapId=mapId, routingAMR=routing_amr_info_list,
                                                      newOrderIds=new_planned_order_ids)
        if len(new_planned_order_ids) > 0:
            planned_orders_list_new = get_routes_for_all_amr(routing_request=routing_request_object,
                                                             order_index_list=order_index_list)
        else:
            planned_orders_list_new = None

    if planned_orders_list_new is None:
        return None
    # Set tokens of amr's with planned orders
    update_tokens_from_planned_orders(planned_orders_list_new)
    return planned_orders_list_new


def get_routes_for_all_amr(routing_request: RoutingRequestObject, order_index_list: List[str]):
    """
    :param routing_request:  RoutingRequestObject
    :param order_index_list: List[str]
    :return: 1. Request routes for RoutingRequestObject
             2. Release order in order pool if no path found or delete order from order pool if path planned
             3. Get planned order update list
             4. Update sequence ids
             5. Update system states
    """
    routes = request_routes_for_all_amrs(routing_request).json()
    terminate = True
    # for central
    # if routing_request.planOrderIds is not None:
    #     new_planned_orders = routing_request.planOrderIds + routing_request.newOrderIds
    # else:
    #     new_planned_orders = routing_request.newOrderIds
    for index, route in enumerate(routes):
        if len(route['nodes']) == 0 and len(route['edges']) == 0:
            # no path found
            if (config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing
                    and order_index_list[index] in routing_request.newOrderIds):
                release_order_in_order_pool(ReleaseOrderRequest(orderId=order_index_list[index]))
            elif (config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central and
                  index < len(order_index_list)):
                for j in range(len(order_index_list)):
                    release_order_in_order_pool(ReleaseOrderRequest(orderId=order_index_list[j]))
                logger.info(f'Release Order {routing_request.planOrderIds[index]} in order pool after'
                            f' path planning failed')
        elif (config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing
              and order_index_list[index] in routing_request.newOrderIds):
            terminate = False
            delete_order_from_order_pool(DeleteOrderRequest(orderId=order_index_list[index]))
        else:
            terminate = False
    if terminate is True:
        return None

    logger.debug(f'Routes: {routes}')

    planned_order_update_list = get_planned_order_update_list_for_all_amr(routes, routing_request)
    logger.debug(f'Planned order update list: {planned_order_update_list}')

    planned_order_update_list = update_sequence_ids_for_order_updates(planned_order_update_list)
    logger.debug(f'Planned order update list: {planned_order_update_list}')
    update_system_states_for_planned_order_update_list(planned_order_update_list)
    return planned_order_update_list


def get_planned_order_update_list_for_all_amr(routes, routing_request: RoutingRequestObject):
    """
    :param routes: List[Route]
    :param routing_request: RoutingRequestObject
    :return: List[PlannedOrder] with new routes
    """
    planned_order_update_list = []
    for index, route in enumerate(routes):
        if len(route['nodes']) == 0 and len(route['edges']) == 0:
            continue
        planned_order = get_planned_order_from_route(amr_id=routing_request.routingAMR[index].amrId,
                                                     order=routing_request.routingAMR[index].order,
                                                     route=routes[index])
        if planned_order.order.orderId != '':
            logger.debug(f'Add planned order to list: {planned_order}')
            planned_order_update_list.append(planned_order)
    return planned_order_update_list


def two_stage_routing_object(routing_request: RoutingRequestObject):
    """
    :param routing_request: routing request object from dispatching service for central
    :return: planned order list with two stage routing
    """
    found_all_paths = True
    tokens_for_constraints = []
    for routing_amr in routing_request.routingAMR:
        if (routing_amr.order.orderId not in routing_request.newOrderIds and
                routing_amr.order.orderId in routing_request.deliveryOrderIds):
            tokens_for_constraints.append(routing_amr.token)
    if len(tokens_for_constraints) > 0:
        constraints_for_new_orders = get_constraints_from_tokens(tokens_for_constraints)
    else:
        constraints_for_new_orders = None
    # 1. Routing for delivery orders
    routing_amr_list_new = []
    for routing_amr in routing_request.routingAMR:
        if routing_amr.order.orderId in routing_request.newOrderIds:  # or delivery order ids
            routing_amr_list_new.append(routing_amr)
    if len(routing_amr_list_new) >= 1:
        new_routing_request = RoutingRequestObject(mapId=routing_request.mapId,
                                                   routingAMR=routing_amr_list_new,
                                                   newOrderIds=routing_request.newOrderIds,
                                                   deliveryOrderIds=routing_request.deliveryOrderIds,
                                                   planOrderIds=routing_request.planOrderIds,
                                                   constraints=constraints_for_new_orders)
        logger.debug(f'First Stage routing request: {new_routing_request}')
        planned_orders_list_new = get_routes_for_all_amr(routing_request=new_routing_request,
                                                         order_index_list=routing_request.newOrderIds)
        if planned_orders_list_new is None and found_all_paths is True:
            found_all_paths = False
            data.db_init.database['system_state_management'].number_found_no_path += 1

    else:
        planned_orders_list_new = None
    tokens_delivery_orders = []
    for routing_amr in routing_request.routingAMR:
        if (routing_amr.order.orderId in routing_request.deliveryOrderIds and
                routing_amr.order.orderId not in routing_request.newOrderIds):
            tokens_delivery_orders.append(routing_amr.token)
    if planned_orders_list_new is None:
        if len(tokens_delivery_orders) > 0:
            constraints = get_constraints_from_tokens(tokens_delivery_orders)
        else:
            constraints = None
    else:
        if len(tokens_delivery_orders) > 0:
            constraints_new = get_constraints_from_tokens(tokens_delivery_orders)
            constraints_from_planned_orders = get_constraints_for_planned_orders(planned_orders_list_new)
            constraints = constraints_new | constraints_from_planned_orders
        else:
            constraints = get_constraints_for_planned_orders(planned_orders_list_new)
    # 2. Get planned orders to pickup locations and parking nodes
    routing_amr_list_new = []
    order_index_list = []
    for routing_amr in routing_request.routingAMR:
        if routing_amr.order.orderId not in routing_request.deliveryOrderIds:
            routing_amr_list_new.append(routing_amr)
            order_index_list.append(routing_amr.order.orderId)
    if len(routing_amr_list_new) >= 1:
        new_routing_request = RoutingRequestObject(mapId=routing_request.mapId,
                                                   routingAMR=routing_amr_list_new,
                                                   newOrderIds=routing_request.newOrderIds,
                                                   deliveryOrderIds=routing_request.deliveryOrderIds,
                                                   planOrderIds=routing_request.planOrderIds,
                                                   constraints=constraints)
        logger.debug(f'Second stage routing request: {new_routing_request}')
        planned_orders_list_second = get_routes_for_all_amr(routing_request=new_routing_request,
                                                            order_index_list=[])
        if planned_orders_list_second is None and found_all_paths is True:
            found_all_paths = False
            data.db_init.database['system_state_management'].number_found_no_path += 1
    else:
        planned_orders_list_second = None
    if found_all_paths is True and data.db_init.database['system_state_management'].number_found_no_path > 0:
        data.db_init.database['system_state_management'].number_to_find_path_again.append(
            copy.deepcopy(data.db_init.database['system_state_management'].number_found_no_path)
        )
        data.db_init.database['system_state_management'].number_found_no_path = 0
    if planned_orders_list_new is None and planned_orders_list_second is None:
        return None
    elif planned_orders_list_new is not None and planned_orders_list_second is None:
        return planned_orders_list_new
    elif planned_orders_list_new is None and planned_orders_list_second is not None:
        return planned_orders_list_second
    else:
        return planned_orders_list_new + planned_orders_list_second


def get_constraints_for_planned_orders(planned_orders: List[PlannedOrder]):
    constraints = set()
    for planned_order in planned_orders:
        for i, node in enumerate(planned_order.order.nodes):
            if i == len(planned_order.order.nodes)-1:
                if config.config_file.INFINITY_CONSTRAINT is True:
                    constraints.add((node.nodeId, (i, np.inf)))
                else:
                    constraints.add((node.nodeId, i))
            else:
                constraints.add((node.nodeId, i))
        for i, edge in enumerate(planned_order.order.edges):
            constraints.add(((edge.startNodeId, edge.endNodeId), i))
    return constraints


def get_constraints_from_tokens(token_list: List[Token]):
    tokens_without_events = copy.deepcopy(token_list)
    for token in tokens_without_events:
        while 'Event' in token.tokens:
            token.tokens.remove('Event')
    constraints = set()
    for token in tokens_without_events:
        for t, node in enumerate(token.tokens):
            if t == len(token.tokens) - 1:
                if config.config_file.INFINITY_CONSTRAINT is True:
                    constraints.add((node, (t, np.inf)))
                else:
                    constraints.add((node, t))
            else:
                constraints.add((node, t))
            if t != len(token.tokens)-1:
                if node != token.tokens[t+1]:
                    constraints.add(((node, token.tokens[t+1]), t))
    return constraints


