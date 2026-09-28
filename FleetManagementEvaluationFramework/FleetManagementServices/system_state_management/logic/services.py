import copy
import os
import logging

import config.config_file
import data.enums

from api.client_api import send_planned_order_to_amr_communication, get_nodes_info, delete_order_from_order_pool, \
    send_tokens_to_central
from api.client_api_models import DeleteOrderRequest, ReservedNodeRequest
from api.server_api_models import GetAMRStateRequest, SetAMRConnectionStateRequest, \
    AMRRequest, PlannedOrderIncoming, OrderFinishRequest, \
    SystemTimeResponse, SystemTimeRequest, SetAMRStateResponse, AMRPauseRequest, PathRequest, \
    AMRPathRequest, AMRPORequest, InstantOrders, DispatchingStrategy, PathPlanningInformation
from data.enums import ConnectionState, OperatingMode
from data.models import PlannedOrderInfos, PlannedOrderSequenceIncoming, NewAMRSystemRequest, AMRState, \
    BatteryState, SystemStateAMR, AMRPosition, NodeInfoRequest, AMRDataResponse
from data.system_state_management_db import SystemStateManagementDb
from logic.check_amr_processes_order import check_amr_for_processing_order_for_new_planned_orders, \
    plan_processing_instant_orders, check_amr_for_execute_new_orders, check_amr_for_process_next_order
import data.db_init
from logic.general_service_functions import transform_node_states_to_tokens

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def service_get_amr_state(request_body: GetAMRStateRequest):
    """
    :param request_body: GetAMRStateRequest
    :return: Get states of all amr or of selected amr back to requested service
    """
    response = []
    if request_body.amrIds[0] == '*':  # Get states of all amr's
        for key, amr_state in data.db_init.database['system_state_management'].amr_states.items():
            response.append(amr_state)
    else:
        for entry in request_body.amrIds:
            if entry in data.db_init.database['system_state_management'].amr_states.keys():
                if data.db_init.database['system_state_management'].amr_states[entry].amrState.connectionState == \
                        ConnectionState.ONLINE and \
                        data.db_init.database['system_state_management'].amr_states[entry].amrState.paused is not True:
                    response.append(data.db_init.database['system_state_management'].amr_states[entry])
    return response


def service_set_amr_state_with_response(request_body: AMRState):
    """
    Currently not used
    :param request_body: AMRState
    :return: Set amr state and get response in form of a planned order list
    """
    if request_body.amrId not in data.db_init.database['system_state_management'].amr_states.keys():
        logger.exception(f'Error: AMR {request_body.amrId} does not exist!')
        raise Exception(f'Error: AMR {request_body.amrId} does not exist!')
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].amrState = request_body
    # Update token, planned path of amr
    token_list = transform_node_states_to_tokens(request_body.nodeStates, request_body.lastNodeId)
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].token = token_list
    planned_order = check_amr_for_processing_order_for_new_planned_orders(amr_id=request_body.amrId)
    if planned_order is not None:
        response = SetAMRStateResponse(plannedOrders=planned_order)
    else:
        response = SetAMRStateResponse(plannedOrders=[])
    return response


def service_set_amr_connection_state(request_body: SetAMRConnectionStateRequest):
    """
    :param request_body: SetAMRConnectionStateRequest
    :return: Set connection state of an amr
    """
    if request_body.amrId not in data.db_init.database['system_state_management'].amr_states.keys():
        logger.exception(f'Error: AMR {request_body.amrId} does not exist!')
        raise Exception(f'Error: AMR {request_body.amrId} does not exist!')
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].amrState.connectionState = (
        request_body.connectionState)
    return


def service_set_planned_order_in_queue(request_body: PlannedOrderIncoming):
    """
    :param request_body: PlannedOrderIncoming
    :return: Set planned order in queue. Important for greedy and push-back dispatching
    """
    # add order to the queue of planned orders
    if request_body.amrId not in data.db_init.database['system_state_management'].amr_states.keys():
        logger.exception(f'Error: AMR {request_body.amrId} does not exist in system database!')
        raise Exception(f'Error: AMR {request_body.amrId} does not exist in system database!')
    planned_order = PlannedOrderInfos(estimatedStartTime=request_body.estimatedStartTime,
                                      estimatedEndTime=request_body.estimatedEndTime,
                                      order=request_body.order)
    logger.info(f'Service set planned order in queue: {planned_order.order.orderId} for amr {request_body.amrId}')
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders.insert(
        request_body.index,
        planned_order)
    if config.config_file.SIMULATION_ACTIVE is False:
        planned_order = check_amr_for_process_next_order(request_body.amrId)
        if planned_order is not None:
            logger.info(f'Send planned order {planned_order[0].order.orderId}')
            send_planned_order_to_amr_communication(planned_order[0])
    return


def service_update_planned_order_sequence(request_body: PlannedOrderSequenceIncoming):
    """
    :param request_body: PlannedOrderSequenceIncoming
    :return: Set a new sequence as planned order list. Important for greedy and push-back dispatching
    """
    # order to the queue of planned orders
    if request_body.amrId not in data.db_init.database['system_state_management'].amr_states.keys():
        logger.exception(f'Error: AMR {request_body.amrId} does not exist in system database!')
        raise Exception(f'Error: AMR {request_body.amrId} does not exist in system database!')
    logger.info(f'Service update planned order sequence for amr {request_body.amrId}: {request_body.orders}')
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders = request_body.orders
    if config.config_file.SIMULATION_ACTIVE is False:
        planned_order = check_amr_for_process_next_order(request_body.amrId)
        if planned_order is not None:
            send_planned_order_to_amr_communication(planned_order[0])
    return


def service_get_amr_data(request_body: AMRRequest):
    """
    :param request_body: AMRRequest
    :return: Get system state data for user interface request
    """
    # Service get amr data for the userinterface
    response = []
    if request_body.amrIds[0] == '*':  # Get data of all amr's
        for amr_id, amr_data in data.db_init.database['system_state_management'].amr_states.items():
            response.append(AMRDataResponse(amrId=amr_id, lastNodeId=amr_data.amrState.lastNodeId,
                                            driving=amr_data.amrState.driving,
                                            connectionState=amr_data.amrState.connectionState,
                                            currentOrder=amr_data.amrState.orderId,
                                            numberOfPlannedOrders=int(len(amr_data.plannedOrders)),
                                            pause=amr_data.amrState.paused,
                                            plannedOrders=amr_data.plannedOrders,
                                            batteryState=amr_data.amrState.batteryState,
                                            actionsCurrentOrder=amr_data.amrState.actionStates,
                                            x=int(amr_data.amrState.amrPosition.x),
                                            y=int(amr_data.amrState.amrPosition.y)))
    else:
        for amr_id in request_body.amrIds:
            response.append(AMRDataResponse(amrId=amr_id,
                                            lastNodeId=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.lastNodeId,
                                            driving=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.driving,
                                            connectionState=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.connectionState,
                                            currentOrder=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.orderId,
                                            numberOfPlannedOrders=int(len(data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders)),
                                            pause=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.paused,
                                            plannedOrders=data.db_init.database['system_state_management'].amr_states[amr_id].plannedOrders,
                                            batteryState=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.batteryState,
                                            actionsCurrentOrder=data.db_init.database['system_state_management'].amr_states[amr_id].amrState.actionStates,
                                            x=int(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.amrPosition.x),
                                            y=int(data.db_init.database['system_state_management'].amr_states[amr_id].amrState.amrPosition.y)
                                            ))
    return response


def service_remove_finished_order_from_queue(request_body: OrderFinishRequest):
    """
    :param request_body:  OrderFinishRequest
    :return: Remove finished simulated order from planned order list
    """
    logger.info(f'Remove order {request_body.orderId} after finish for amr {request_body.amrId}')
    logger.debug(str('Before queue: ' +
                     str(data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders)))
    if len(data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders) != 0:
        if (data.db_init.database['system_state_management'].amr_states[
                request_body.amrId].plannedOrders[0].order.orderId == request_body.orderId):
            logger.info(f'Remove planned order {request_body.orderId} from amr {request_body.amrId}')

            data.db_init.database['system_state_management'].last_orders[request_body.amrId] = \
            data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders[0]

            del data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders[0]
    logger.debug(str('After queue: ' +
                     str(data.db_init.database['system_state_management'].amr_states[request_body.amrId].plannedOrders)))
    if (config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central and
            str(request_body.orderId)[0:4] != 'RePo'):
        delete_order_from_order_pool(DeleteOrderRequest(orderId=request_body.orderId))
        logger.info(f'Delete order {request_body.orderId} from order pool')
    return


def service_set_system_time(request_body: SystemTimeResponse):
    """
    :param request_body:  SystemTimeResponse
    :return: Set system time
    """
    # only go in the future
    timestamp = request_body.timestamp.replace(tzinfo=None)
    if data.db_init.database['system_state_management'].system_time < timestamp:
        data.db_init.database['system_state_management'].system_time = timestamp
    logger.debug(f'System time update at {timestamp}')
    return


def service_get_system_time(request_body: SystemTimeRequest):
    """
    :param request_body: SystemTimeRequest
    :return: Get system time
    """
    response = None
    if request_body.sysTime == '*':
        response = SystemTimeResponse(timestamp=data.db_init.database['system_state_management'].system_time)
    return response


def service_add_new_amr(request_body: NewAMRSystemRequest):
    """
    :param request_body: NewAMRSystemRequest
    :return: Add new AMR to fleet management system
    """
    # Add new amr to the system
    node_response_obj = get_nodes_info(NodeInfoRequest(nodeIds=[request_body.lastNodeId],
                                                       layoutId=request_body.layoutId)).json()
    node_list = [node for node in node_response_obj['nodes']]
    amr_position = AMRPosition(x=node_list[0]['nodePosition']['x'], y=node_list[0]['nodePosition']['y'],
                               mapId=request_body.layoutId, positionInitialized=True)
    amr_state = AMRState(timestamp=data.db_init.database['system_state_management'].system_time,
                         amrId=request_body.amrId,
                         connectionState=ConnectionState.ONLINE,
                         orderId='', orderUpdateId=0,
                         lastNodeId=request_body.lastNodeId,
                         lastNodeSequenceId=0,
                         driving=False,
                         paused=False,
                         distanceSinceLastNode=0,
                         operatingMode=OperatingMode.AUTOMATIC,
                         amrPosition=amr_position,
                         batteryState=BatteryState(batteryCharge=100, charging=False,
                                                   reach=request_body.maxReachBattery),
                         nodeStates=[], edgeStates=[], actionStates=[]
                         )
    system_state_amr = SystemStateAMR(amrState=amr_state, plannedOrders=[], token=[request_body.lastNodeId])
    data.db_init.database['system_state_management'].add_amr_state(system_state_amr)
    return


def service_set_amr_to_pause(request_body: AMRPauseRequest):
    """
    :param request_body: AMRPauseRequest
    :return: Set state of an amr to pause, this means further order can not dispatch to this amr
    """
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].amrState.paused = request_body.pause
    return


def service_reset_system_state_management():
    """
    :return: Reset system state management service
    """
    data.db_init.database['system_state_management'] = SystemStateManagementDb(os.environ['STATE_FILE'])
    return


def service_set_system_state_file_new(request_body: PathRequest):
    config.config_file.SYSTEM_STATE_FILE_SCENARIO = request_body.path
    os.environ['STATE_FILE'] = request_body.path
    data.db_init.database['system_state_management'] = SystemStateManagementDb(request_body.path)
    return


def service_get_amr_path(request_body: AMRPathRequest):
    """
    :param request_body: AMRPathRequest
    :return: Get current path of an amr for visualization in the user interface
    """
    response = {}
    if not request_body.prev:
        if request_body.amrId == '*':
            for key, amr_state in data.db_init.database['system_state_management'].amr_states.items():
                if len(amr_state.plannedOrders) > 0:
                    response[amr_state.amrState.amrId] = amr_state.plannedOrders[0]
        else:
            for key, amr_state in data.db_init.database['system_state_management'].amr_states.items():
                if amr_state.amrState.amrId == request_body.amrId:
                    if len(amr_state.plannedOrders) > 0:
                        response[amr_state.amrState.amrId] = amr_state.plannedOrders[0]
    else:
        response = data.db_init.database['system_state_management'].last_orders
    return response


def service_get_amr_planned_orders(request_body: AMRPORequest):
    """
    :param request_body: AMRPORequest
    :return: get planned order for the user interface
    """
    response = {}
    for key, amr_state in data.db_init.database['system_state_management'].amr_states.items():
        if amr_state.amrState.amrId == request_body.amrId:
            if len(amr_state.plannedOrders) > 0:
                response[amr_state.amrState.amrId] = amr_state.plannedOrders
    return response


def service_get_instant_order_for_execution(request_body: InstantOrders):
    """
    :param request_body: InstantOrders
    :return: Service to get instant order for execution now
    """
    planned_orders = plan_processing_instant_orders(request_body)
    if planned_orders is not None:
        for planned_order in planned_orders:
            send_planned_order_to_amr_communication(planned_order)
    return


def service_request_orders():
    """
    :return: Service to request orders for amr
             1. Check all amr for new orders
             2. return a list of planned orders and order updates
    """
    planned_orders_list_new = check_amr_for_execute_new_orders()
    logger.debug(f'New orders response: {planned_orders_list_new}')
    if planned_orders_list_new is not None:
        response = SetAMRStateResponse(plannedOrders=planned_orders_list_new)
    else:
        response = SetAMRStateResponse(plannedOrders=[])
    if (data.db_init.database['system_state_management'].number_found_no_path >=
            config.config_file.MAX_NUMBER_OF_FAILED_PATH_PLANNING):
        response.terminate = True
    return response


def service_set_amr_state(request_body: AMRState):
    """
    :param request_body:  AMRState
    :return: Set an amr state in system state management service
    """
    if request_body.amrId not in data.db_init.database['system_state_management'].amr_states.keys():
        logger.exception(f'Error: AMR {request_body.amrId} does not exist!')
        raise Exception(f'Error: AMR {request_body.amrId} does not exist!')
    if request_body.lastNodeId == "":
        logger.exception(f'Error: AMR {request_body.amrId} has no valid lastNodeId!')
        raise Exception(f'Error: AMR {request_body.amrId} has no valid lastNodeId!')
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].amrState = request_body
    # Update token, planned path of amr
    logger.info(f'Set AMR State for AMR {request_body.amrId} for order {request_body.orderId} at timestamp {request_body.timestamp}')
    logger.debug(f'Set system state: {request_body}')
    token_list = transform_node_states_to_tokens(request_body.nodeStates, request_body.lastNodeId)
    data.db_init.database['system_state_management'].amr_states[request_body.amrId].token = token_list
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central:
        reserved_nodes = copy.deepcopy(token_list)
        del reserved_nodes[0]
        if len(reserved_nodes) > 0:
            del reserved_nodes[-1]
        send_tokens_to_central(ReservedNodeRequest(amrId=request_body.amrId, nodes=reserved_nodes))
    return


def service_set_dispatching_strategy(request_body: DispatchingStrategy):
    config.config_file.TASK_ASSIGNMENT_STRATEGY = data.enums.TaskAssignmentStrategy(request_body.dispatchingStrategy)
    return


def service_set_system_time_from_extern(request_body: SystemTimeResponse):
    """
    :param request_body:  SystemTimeResponse
    :return: Set system time
    """
    # go in the future and past for initialization
    data.db_init.database['system_state_management'].system_time = request_body.timestamp
    logger.debug(f'System reset to {request_body.timestamp} for evaluation!')
    return


def service_get_path_planning_information():
    path_planning_information = PathPlanningInformation(number_to_find_path_again=
                                                        data.db_init.database['system_state_management'].number_to_find_path_again)
    return path_planning_information
