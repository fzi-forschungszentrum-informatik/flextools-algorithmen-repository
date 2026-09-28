from typing import List
import datetime
import numpy as np
import logging

import config.config_file
from api.client_api import get_possible_amrs, get_amr_states, get_nodes_for_order, get_station_infos
from api.client_api_models import OrderDimensionRequest, PossibleAMRsRequest, NodeInfoRequest, StationInfoRequest
from api.server_api_models import NewOrderInfo
from config.config_file import BUFFER_TIME_PRO_ORDER
from data.enums import BlockingType
from data.models import SystemStateAMR, Order, Action, ActionParameter

logger = logging.getLogger(config.config_file.LOGGER_NAME)

#############
# FUNCTIONS #
#############


def setup_ttm(ttm_from_rest_api):
    ttm = {}
    for k, v in list(ttm_from_rest_api.items()):
        if v[0] is None:
            ttm[eval(k)] = np.inf
        else:
            ttm[eval(k)] = np.mean(v)  # keys are given as string tuples, values as list
    return ttm


def load_capable_amrs_state(new_order_info: NewOrderInfo):
    """
    :param new_order_info: order info object
    :return: amr states of all available amr's for order, which satisfy requirements
    """
    # load considered amrs
    order_dimension = OrderDimensionRequest(x=new_order_info.dimension.x, y=new_order_info.dimension.y,
                                            z=new_order_info.dimension.z, weight=new_order_info.dimension.weight)
    capable_amrs = get_possible_amrs(order_dimension).json()
    considered_amrs = []
    if new_order_info.amrIds is not None:
        for amr in capable_amrs:
            if amr in new_order_info.amrIds:
                considered_amrs.append(amr)
    else:
        considered_amrs = capable_amrs
    if len(considered_amrs) == 0:
        logger.exception('System-Error: No possible AMRs found to satisfy the order!')
        raise Exception('System-Error: No possible AMRs found to satisfy the order!')
    logger.debug(f'Set possible AMRs: {capable_amrs}')

    # 2. get states of all considered amr which are online and not in pause mode
    return get_amr_states(PossibleAMRsRequest(amrIds=considered_amrs)).json()


def load_all_amr_states() -> List[SystemStateAMR]:
    """
    :return: amr states of all amrs registered in the system
    """
    amr_states_json = get_amr_states(PossibleAMRsRequest(amrIds=['*'])).json()
    list_system_state_amrs = []
    for amr in amr_states_json:
        list_system_state_amrs.append(SystemStateAMR(**amr))
    return list_system_state_amrs


def get_id_closest_amr_current_position(considered_amrs: List[SystemStateAMR], order: Order):
    """
    :param considered_amrs: list of states, for considered amr's
    :param order: new order
    :return: get closest amr to order start position
    """
    order_position = (order.nodes[0].nodePosition.x, order.nodes[0].nodePosition.y)
    start_position_order_map = order.nodes[0].nodePosition.mapId

    # INITIALIZE TUPLE FOR CLOSEST AMR
    closest_amr = (None, None, np.inf)  # Tuple(amr_state, reference_node_id, distance to start position order)

    for amr in considered_amrs:
        if amr['amr_state']['amr_position']['map_id'] == start_position_order_map:  # only if amr uses same map
            amr_reference_position = (amr['amr_state']['amr_position'].x, amr['amr_state']['amr_position'].y)
            reference_node_id = amr['amr_state']['last_node_id']
            manh_dist = compute_manhattan_dist(amr_reference_position, order_position)
            if manh_dist < closest_amr[2]:
                closest_amr = (amr, reference_node_id, manh_dist)

    return closest_amr[0], closest_amr[1]  #closest amr and reference node id as predecessor for insertion


def get_amrs_minimum_number_of_orders(considered_amrs: List[SystemStateAMR]):
    """
    :param considered_amrs: list of states, for considered amr's
    :return: get set of amr states, with the minimum number of planned orders at the moment
    """
    subset_amr_minimum_number_orders = []
    number_planned_orders = np.inf
    for amr in considered_amrs:
        if number_planned_orders > len(amr['planned_orders']):
            subset_amr_minimum_number_orders = []
            subset_amr_minimum_number_orders.append(amr)
            number_planned_orders = len(amr['planned_orders'])
        elif number_planned_orders == len(amr['planned_orders']):
            subset_amr_minimum_number_orders.append(amr)
            number_planned_orders = len(amr['planned_orders'])
    return subset_amr_minimum_number_orders


def compute_manhattan_dist(start_position, end_position):
    '''
    :param start_position: tuple (x, y)
    :param end_position: tuple (x, y)
    :return: manhattan distance between start_position and end_position
    '''
    return abs(end_position[0] - start_position[0]) + abs(end_position[1] - start_position[1])


def transform_order_info_to_order(order_info: NewOrderInfo, action_id: int = 1):
    """
    :param order_info: object with infos about order
    :param action_id: action id counter
    :return: order object, with relevant nodes and actions for pickup and dropoff
    """
    if order_info.sourceId is not None and order_info.sinkId is not None:
        node_info_request = NodeInfoRequest(nodeIds=[order_info.sourceId, order_info.sinkId],
                                            layoutId=order_info.layoutId)
    elif order_info.sourceId is None and order_info.sinkId is not None:
        node_info_request = NodeInfoRequest(nodeIds=[order_info.sinkId],
                                            layoutId=order_info.layoutId)
    elif order_info.sourceId is not None and order_info.sinkId is None:
        node_info_request = NodeInfoRequest(nodeIds=[order_info.sourceId], layoutId=order_info.layoutId)
    else:
        node_info_request = NodeInfoRequest(nodeIds=[], layoutId=order_info.layoutId)
    node_response_obj = get_nodes_for_order(node_info_request).json()
    node_list = [node for node in node_response_obj['nodes']]
    if order_info.pickupTime is None:
        pickup_duration = 60
    else:
        pickup_duration = order_info.pickupTime
    if order_info.dropoffTime is None:
        dropoff_duration = 60
    else:
        dropoff_duration = order_info.dropoffTime

    station_info_list = []
    for node in node_info_request.nodeIds:
        if node[0] == 'S':
            station_info_list.append(node)
    station_infos = get_station_infos(StationInfoRequest(layoutId=order_info.layoutId,
                                                         stationIds=station_info_list)).json()

    pickup_already = False
    dropoff_already = False
    for i, node in enumerate(node_list):
        if node['nodeId'] == order_info.sourceId and pickup_already is False:
            action_parameters = [ActionParameter(key='duration', value=pickup_duration)]
            if order_info.itemSkuId is not None:
                action_parameters.append(ActionParameter(key='itemSkuId', value=order_info.itemSkuId))
            if order_info.sourceHandover is not None:
                action_parameters.append(ActionParameter(key='sourceHandover', value=order_info.sourceHandover))
            node_list[i]['actions'].append(Action(actionId=str(action_id), actionType='pick',
                                                  blockingType=BlockingType.HARD,
                                                  actionParameters=action_parameters))  # in s
            pickup_already = True
        elif node['nodeId'] == order_info.sinkId and dropoff_already is False:
            action_parameters = [ActionParameter(key='duration', value=dropoff_duration)]
            if order_info.itemSkuId is not None:
                action_parameters.append(ActionParameter(key='itemSkuId', value=order_info.itemSkuId))
            if order_info.sinkHandover is not None:
                action_parameters.append(ActionParameter(key='sinkHandover', value=order_info.sinkHandover))
            node_list[i]['actions'].append(Action(actionId=str(action_id + 1), actionType='drop',
                                                  blockingType=BlockingType.HARD,
                                                  actionParameters=action_parameters))
            dropoff_already = True
        else:
            for station in station_infos:
                if (station['stationId'] == order_info.sourceId and node['nodeId'] in station['interactionNodes'] and
                        pickup_already is False):
                    node_list[i]['actions'].append(Action(actionId=str(action_id), actionType='pick',
                                                          blockingType=BlockingType.HARD,
                                                          actionParameters=[ActionParameter(key='duration',
                                                                                            value=pickup_duration)]))
                    pickup_already = True
                elif (station['stationId'] == order_info.sinkId and node['nodeId'] in station['interactionNodes'] and
                        dropoff_already is False):
                    node_list[i]['actions'].append(Action(actionId=str(action_id + 1), actionType='drop',
                                                          blockingType=BlockingType.HARD,
                                                          actionParameters=[ActionParameter(key='duration',
                                                                                            value=dropoff_duration)]))
                    dropoff_already = True

    order = Order(orderId=order_info.orderId, orderUpdateId=0, nodes=node_list, edges=[])
    return order


def get_general_duration_for_actions_from_order(order: Order, buffer_time: int = BUFFER_TIME_PRO_ORDER):
    """
    :param order: order object
    :param buffer_time: default buffer time between orders
    :return: estimated time to execute all actions of an order
    """
    duration = buffer_time  # buffer, plus additional action durations

    for node in order['nodes']:
        for action in node['actions']:
            for action_pm in action['actionParameters']:
                if action_pm['key'] == 'duration':
                    duration += action_pm['value']

    for edge in order['edges']:
        for action in edge['actions']:
            for action_pm in action['actionParameters']:
                if action_pm['key'] == 'duration':
                    duration += action_pm['value']

    order_buffer_time = datetime.timedelta(seconds=duration)
    return order_buffer_time
