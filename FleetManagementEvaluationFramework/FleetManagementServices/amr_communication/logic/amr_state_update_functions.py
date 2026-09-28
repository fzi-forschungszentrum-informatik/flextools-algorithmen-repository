import logging

import config.config_file
from api.client_api_models import SetAMRStateRequest
from api.server_api_models import OrderAMRRequest
from data.enums import OrderStatus, ActionStatus, BlockingType
from data.models import ActionParameter, Action, NodePosition, Node, Edge, Order

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def determine_order_status_from_amr_state(request_body: SetAMRStateRequest):
    """
    :param request_body: AMRState object
    :return: order status from amr, depends on action-, edge-, and node states
    """
    current_order_status = OrderStatus.PLANNED
    all_actions_finished = True
    for action in request_body.actionStates:
        if action.actionStatus == ActionStatus.FINISHED:
            if action.actionType == "pick":
                current_order_status = OrderStatus.PICKUP
            elif action.actionType == "drop":
                current_order_status = OrderStatus.DROPOFF
        elif action.actionStatus == ActionStatus.INITIALIZING or action.actionStatus == ActionStatus.RUNNING:
            if current_order_status != OrderStatus.PICKUP and current_order_status != OrderStatus.DROPOFF:
                current_order_status = OrderStatus.STARTED
            all_actions_finished = False
        else:
            all_actions_finished = False
    if (len(request_body.nodeStates) == 0 and len(request_body.edgeStates) == 0 and all_actions_finished is True and
            request_body.orderId != ''):
        if current_order_status == OrderStatus.PICKUP:
            current_order_status = OrderStatus.PICKUP
        elif current_order_status == OrderStatus.DROPOFF:
            current_order_status = OrderStatus.FINISHED

    logger.debug(f'Current order status  {request_body.orderId} is {current_order_status}')
    return current_order_status


def process_next_order_in_queue(response):
    """
    :param response: json of order for processing
    :return: order amr request, for start processing order
    """
    node_list_order = []
    edge_list_order = []
    for node in response['order']['nodes']:
        action_list_node = []
        for action in node['actions']:
            action_parameter_list = []
            for act_pm in action['actionParameters']:
                action_parameter_list.append(ActionParameter(key=act_pm['key'], value=act_pm['value']))
            action_list_node.append(Action(actionId=action['actionId'], actionType=action['actionType'],
                                           blockingType=BlockingType(action['blockingType']),
                                           actionParameters=action_parameter_list))
        node_list_order.append(Node(nodeId=node['nodeId'], sequenceId=node['sequenceId'], released=node['released'],
                                    nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                              y=node['nodePosition']['y'],
                                                              mapId=node['nodePosition']['mapId']),
                                    actions=action_list_node))
    for edge in response['order']['edges']:
        action_list_edge = []
        for action in edge['actions']:
            action_parameter_list = []
            for act_pm in action['actionParameters']:
                action_parameter_list.append(ActionParameter(key=act_pm['key'], value=act_pm['value']))
            action_list_edge.append(Action(actionId=action['actionId'], actionType=action['actionType'],
                                           blockingType=BlockingType(action['blockingType']),
                                           actionParameters=action_parameter_list))
        edge_list_order.append(Edge(edgeId=edge['edgeId'], sequenceId=edge['sequenceId'], released=edge['released'],
                                    startNodeId=edge['startNodeId'], endNodeId=edge['endNodeId'],
                                    maxSpeed=edge['maxSpeed'], length=edge['length'],
                                    actions=action_list_edge))

    order_amr_request = OrderAMRRequest(timestamp=response['timestamp'],
                                        amrId=response['amrId'],
                                        order=Order(orderId=response['order']['orderId'],
                                                    orderUpdateId=response['order']['orderUpdateId'],
                                                    nodes=node_list_order, edges=edge_list_order))
    return order_amr_request
