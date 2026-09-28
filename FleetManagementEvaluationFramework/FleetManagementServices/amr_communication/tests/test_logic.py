import datetime
import json

from api.client_api_models import SetAMRStateRequest
from api.serialization import serialize_json
from data.enums import ConnectionState, OperatingMode, ActionStatus, OrderStatus, BlockingType
from data.models import BatteryState, NodeState, EdgeState, ActionState, AMRStateResponse, Order, Node, Edge, \
    NodePosition, Action, ActionParameter, PlannedOrder
from logic.amr_state_update_functions import determine_order_status_from_amr_state, process_next_order_in_queue


def test_determine_order_status_from_amr_state_pickup():
    node_states_list = []
    edge_states_list = []
    action_states_list = []

    node_states_list.append(NodeState(nodeId='E', sequenceId=0, released=True))
    edge_states_list.append(EdgeState(edgeId='ce', sequenceId=0, released=True))
    action_states_list.append(ActionState(actionId='1', actionStatus=ActionStatus.FINISHED, actionType='pick'))
    action_states_list.append(ActionState(actionId='2', actionStatus=ActionStatus.WAITING, actionType='drop'))

    amr_state_request = SetAMRStateRequest(timestamp=datetime.datetime(2024,8,30,9,30),
                                           amrId='1',
                                           connectionState=ConnectionState.ONLINE,
                                           orderId='1',
                                           orderUpdateId=1,
                                           lastNodeId='C',
                                           lastNodeSequenceId=0,
                                           driving=True,
                                           paused=False,
                                           distanceSinceLastNode=23.4,
                                           operatingMode=OperatingMode.AUTOMATIC,
                                           batteryState=BatteryState(batteryCharge=100, charging=False),
                                           nodeStates=node_states_list,
                                           edgeStates=edge_states_list,
                                           actionStates=action_states_list)
    order_state = determine_order_status_from_amr_state(amr_state_request)
    assert order_state == OrderStatus.PICKUP


def test_determine_order_status_from_amr_state_finnish():
    node_states_list = []
    edge_states_list = []
    action_states_list = []
    action_states_list.append(ActionState(actionId='1', actionStatus=ActionStatus.FINISHED, actionType='pick'))
    action_states_list.append(ActionState(actionId='2', actionStatus=ActionStatus.FINISHED, actionType='drop'))

    amr_state_request = SetAMRStateRequest(timestamp=datetime.datetime(2024, 8, 30, 9, 30),
                                           amrId='1',
                                           connectionState=ConnectionState.ONLINE,
                                           orderId='1',
                                           orderUpdateId=1,
                                           lastNodeId='C',
                                           lastNodeSequenceId=0,
                                           driving=True,
                                           paused=False,
                                           distanceSinceLastNode=23.4,
                                           operatingMode=OperatingMode.AUTOMATIC,
                                           batteryState=BatteryState(batteryCharge=100, charging=False),
                                           nodeStates=node_states_list,
                                           edgeStates=edge_states_list,
                                           actionStates=action_states_list)
    order_state = determine_order_status_from_amr_state(amr_state_request)
    assert order_state == OrderStatus.FINISHED


def test_process_next_order_in_queue():
    node_list = [Node(nodeId='A', sequenceId=0, released=True, nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                      actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                      actionParameters=[ActionParameter(key='duration', value=65)])]),
                 Node(nodeId='B', sequenceId=0, released=True, nodePosition=NodePosition(x=50, y=0, mapId='map1'),
                      actions=[]),
                 Node(nodeId='D', sequenceId=0, released=True, nodePosition=NodePosition(x=50, y=-30, mapId='map1'),
                      actions=[Action(actionId='2', actionType='drop', blockingType=BlockingType.HARD,
                                      actionParameters=[ActionParameter(key='duration', value=75)])]),
                 ]
    edge_list = [Edge(edgeId='ab', sequenceId=0, released=True, startNodeId='A', endNodeId='B', maxSpeed=3,
                      length=50, actions=[]),
                 Edge(edgeId='bc', sequenceId=0, released=True, startNodeId='B', endNodeId='C', maxSpeed=3,
                      length=30, actions=[])
                 ]
    planned_order_obj = AMRStateResponse(plannedOrder=PlannedOrder(timestamp=datetime.datetime(2024, 8, 30, 9, 30),
                                                                   amrId='1',
                                                                   order=Order(orderId='1', orderUpdateId=0,
                                                                               nodes=node_list, edges=edge_list)))

    planned_order_obj = json.dumps(
        planned_order_obj,
        default=lambda o: serialize_json(o)
    )
    planned_order_obj = json.loads(planned_order_obj)
    order_amr_request = process_next_order_in_queue(planned_order_obj['plannedOrder'])

    assert order_amr_request.amrId == '1'
    assert order_amr_request.order.orderId == '1'
    assert len(order_amr_request.order.nodes) == 3
    assert len(order_amr_request.order.edges) == 2
    assert order_amr_request.order.nodes[2].actions[0].actionParameters[0].key == 'duration'
    assert order_amr_request.order.nodes[2].actions[0].actionParameters[0].value == 75
