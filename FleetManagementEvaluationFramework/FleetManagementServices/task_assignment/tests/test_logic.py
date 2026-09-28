import datetime
import json
from unittest import mock

from api.serialization import serialize_json
from api.server_api_models import NewOrderInfo
from config.config_file import TASK_ASSIGNMENT_STRATEGY_PUSHBACK, TASK_ASSIGNMENT_STRATEGY_GREEDY
from data.enums import BlockingType, ConnectionState, OperatingMode, OrderStatus
from data.models import Order, Node, NodePosition, Action, ActionParameter, AMRState, SystemStateAMR, PlannedOrderInfo, \
    AMRPosition, BatteryState, Dimension, ActionIdCounter
from logic.api_services.general_task_assignment_functions import get_general_duration_for_actions_from_order
from logic.api_services.general_functions import transform_str_to_datetime
from logic.task_assignment.greedy import Greedy
from logic.task_assignment.pushback import PushBack


def test_get_general_duration_from_actions_for_order():
    order = Order(
            orderId='1', orderUpdateId=0,
            nodes=[
                Node(
                    nodeId="A",
                    sequenceId=1,
                    released=True,
                    nodePosition=NodePosition(x=60, y=0, mapId='map1'),
                    actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                    actionParameters=[ActionParameter(key='duration', value=90)])]
                ),
                Node(
                    nodeId="H",
                    sequenceId=1,
                    released=True,
                    nodePosition=NodePosition(x=120, y=30, mapId='map1'),
                    actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                    actionParameters=[ActionParameter(key='duration', value=175)])]
                ),
            ],
            edges=[]
        ).dict(exclude_none=True)

    duration = get_general_duration_for_actions_from_order(order)

    assert duration == datetime.timedelta(seconds=265)


@mock.patch("logic.task_assignment.pushback.get_general_duration_for_actions_from_order",
            return_value=datetime.timedelta(seconds=280))
def test_closest_amr_final_position_pushback_single_amr(general_duration_mock):
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=00, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="H",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='drop', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    planned_order_list = [PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                           estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                           order=order1)
                          ]

    amr_states = [SystemStateAMR(amrState=AMRState(amrId='1',
                                                   connectionState=ConnectionState.ONLINE,
                                                   orderUpdateId=0,
                                                   orderId='',
                                                   lastNodeId='B',
                                                   lastNodeSequenceId=0,
                                                   nodeStates=[],
                                                   edgeStates=[],
                                                   actionStates=[],
                                                   driving=False,
                                                   distanceSinceLastNode=0,
                                                   operatingMode=OperatingMode.AUTOMATIC,
                                                   amrPosition=AMRPosition(x=50, y=0, mapId='map1',
                                                                            positionInitialized=True),
                                                   batteryState=BatteryState(batteryCharge=100, charging=False)),
                                 plannedOrders=planned_order_list,
                                 token=['B'])]
    data_amr_states = json.dumps(
        amr_states,
        default=lambda o: serialize_json(o)
    )
    amr_states_dict = json.loads(data_amr_states)

    order_info = NewOrderInfo(orderId='2', sourceId='C', sinkId='F',
                              startTime=datetime.datetime(2024, 8, 28, 9, 30),
                              dueTime=datetime.datetime(2024, 8, 28, 10, 30),
                              dimension=Dimension(x=20, y=20, z=20, weight=0.4),
                              pickupTime=60, dropoffTime=60, status=OrderStatus.NEW)

    order = Order(
        orderId='2', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="C",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="F",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
        ],
        edges=[]
    )

    dispatching_strategies = {}
    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_PUSHBACK] = PushBack(ActionIdCounter(nextActionId=1))
    ttm = {('A', 'A'): 0, ('A', 'B'): 25, ('A', 'C'): 40, ('A', 'D'): 40, ('A', 'E'): 65, ('A', 'F'): 65,
           ('A', 'G'): 90, ('A', 'H'): 90, ('A', 'I'): 105, ('B', 'A'): 25, ('B', 'B'): 0, ('B', 'C'): 15,
           ('B', 'D'): 15, ('B', 'E'): 40, ('B', 'F'): 40, ('B', 'G'): 65, ('B', 'H'): 65, ('B', 'I'): 80,
           ('C', 'A'): 40, ('C', 'B'): 15, ('C', 'C'): 0, ('C', 'D'): 30, ('C', 'E'): 25, ('C', 'F'): 55,
           ('C', 'G'): 50, ('C', 'H'): 80, ('C', 'I'): 65, ('D', 'A'): 40, ('D', 'B'): 15, ('D', 'C'): 30,
           ('D', 'D'): 0, ('D', 'E'): 55, ('D', 'F'): 25, ('D', 'G'): 80, ('D', 'H'): 50, ('D', 'I'): 65,
           ('E', 'A'): 65, ('E', 'B'): 40, ('E', 'C'): 25, ('E', 'D'): 55, ('E', 'E'): 0, ('E', 'F'): 30,
           ('E', 'G'): 25, ('E', 'H'): 55, ('E', 'I'): 40, ('F', 'A'): 65, ('F', 'B'): 40, ('F', 'C'): 55,
           ('F', 'D'): 25, ('F', 'E'): 30, ('F', 'F'): 0, ('F', 'G'): 55, ('F', 'H'): 25, ('F', 'I'): 40,
           ('G', 'A'): 90, ('G', 'B'): 65, ('G', 'C'): 50, ('G', 'D'): 80, ('G', 'E'): 25, ('G', 'F'): 55,
           ('G', 'G'): 0, ('G', 'H'): 30, ('G', 'I'): 15, ('H', 'A'): 90, ('H', 'B'): 65, ('H', 'C'): 80,
           ('H', 'D'): 50, ('H', 'E'): 55, ('H', 'F'): 25, ('H', 'G'): 30, ('H', 'H'): 0, ('H', 'I'): 15,
           ('I', 'A'): 105, ('I', 'B'): 80, ('I', 'C'): 65, ('I', 'D'): 65, ('I', 'E'): 40, ('I', 'F'): 40,
           ('I', 'G'): 15, ('I', 'H'): 15, ('I', 'I'): 0}

    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_PUSHBACK].ttm = ttm
    (state_closest_amr, reference_node_amr, estimated_start_time, estimated_end_time) = (
        dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_PUSHBACK].get_closest_amr_final_position(amr_states_dict, order,
                                                                                                 order_info))
    assert reference_node_amr == 'H'
    assert estimated_start_time == datetime.datetime(2024, 8, 28, 9, 40)
    assert estimated_end_time == datetime.datetime(2024, 8, 28, 9, 46, 55)


@mock.patch("logic.task_assignment.greedy.get_general_duration_for_actions_from_order",
            return_value=datetime.timedelta(seconds=280))
def test_get_best_greedy_insertion_single_amr(general_duration_mock):
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="E",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order2 = Order(
        orderId='2', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="B",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="H",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    planned_order_list = [PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                           estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                           order=order1),
                          PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 40),
                                           estimatedEndTime=datetime.datetime(2024, 8, 28, 10),
                                           order=order2),
                          ]

    amr_states = [SystemStateAMR(amrState=AMRState(amrId='1',
                                                   connectionState=ConnectionState.ONLINE,
                                                   orderUpdateId=0,
                                                   orderId='',
                                                   lastNodeId='B',
                                                   lastNodeSequenceId=0,
                                                   nodeStates=[],
                                                   edgeStates=[],
                                                   actionStates=[],
                                                   driving=False,
                                                   distanceSinceLastNode=0,
                                                   operatingMode=OperatingMode.AUTOMATIC,
                                                   amrPosition=AMRPosition(x=50, y=0, mapId='map1',
                                                                            positionInitialized=True),
                                                   batteryState=BatteryState(batteryCharge=100, charging=False)),
                                 plannedOrders=planned_order_list,
                                 token=['B'])]
    data_amr_states = json.dumps(
        amr_states,
        default=lambda o: serialize_json(o)
    )
    amr_states_dict = json.loads(data_amr_states)

    order_info = NewOrderInfo(orderId='3', sourceId='G', sinkId='D',
                              startTime=datetime.datetime(2024, 8, 28, 9, 30),
                              dueTime=datetime.datetime(2024, 8, 28, 10, 30),
                              dimension=Dimension(x=20, y=20, z=20, weight=0.4),
                              pickupTime=60, dropoffTime=60, status=OrderStatus.NEW)

    order = Order(
        orderId='3', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="G",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="D",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
        ],
        edges=[]
    ).dict(exclude_none=True)

    dispatching_strategies = {}
    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY] = Greedy(ActionIdCounter(nextActionId=1))
    ttm = {('A', 'A'): 0, ('A', 'B'): 25, ('A', 'C'): 40, ('A', 'D'): 40, ('A', 'E'): 65, ('A', 'F'): 65,
           ('A', 'G'): 90, ('A', 'H'): 90, ('A', 'I'): 105, ('B', 'A'): 25, ('B', 'B'): 0, ('B', 'C'): 15,
           ('B', 'D'): 15, ('B', 'E'): 40, ('B', 'F'): 40, ('B', 'G'): 65, ('B', 'H'): 65, ('B', 'I'): 80,
           ('C', 'A'): 40, ('C', 'B'): 15, ('C', 'C'): 0, ('C', 'D'): 30, ('C', 'E'): 25, ('C', 'F'): 55,
           ('C', 'G'): 50, ('C', 'H'): 80, ('C', 'I'): 65, ('D', 'A'): 40, ('D', 'B'): 15, ('D', 'C'): 30,
           ('D', 'D'): 0, ('D', 'E'): 55, ('D', 'F'): 25, ('D', 'G'): 80, ('D', 'H'): 50, ('D', 'I'): 65,
           ('E', 'A'): 65, ('E', 'B'): 40, ('E', 'C'): 25, ('E', 'D'): 55, ('E', 'E'): 0, ('E', 'F'): 30,
           ('E', 'G'): 25, ('E', 'H'): 55, ('E', 'I'): 40, ('F', 'A'): 65, ('F', 'B'): 40, ('F', 'C'): 55,
           ('F', 'D'): 25, ('F', 'E'): 30, ('F', 'F'): 0, ('F', 'G'): 55, ('F', 'H'): 25, ('F', 'I'): 40,
           ('G', 'A'): 90, ('G', 'B'): 65, ('G', 'C'): 50, ('G', 'D'): 80, ('G', 'E'): 25, ('G', 'F'): 55,
           ('G', 'G'): 0, ('G', 'H'): 30, ('G', 'I'): 15, ('H', 'A'): 90, ('H', 'B'): 65, ('H', 'C'): 80,
           ('H', 'D'): 50, ('H', 'E'): 55, ('H', 'F'): 25, ('H', 'G'): 30, ('H', 'H'): 0, ('H', 'I'): 15,
           ('I', 'A'): 105, ('I', 'B'): 80, ('I', 'C'): 65, ('I', 'D'): 65, ('I', 'E'): 40, ('I', 'F'): 40,
           ('I', 'G'): 15, ('I', 'H'): 15, ('I', 'I'): 0}

    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].ttm = ttm
    amr_id, insertion_position, estimated_start_time, estimated_end_time = (
        dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].get_greedy_best_insertion(amr_states_dict, order,
                                                                                          order_info))
    assert amr_id == '1'
    assert insertion_position == 1
    assert estimated_start_time == datetime.datetime(2024,8, 28, 9, 40)
    assert estimated_end_time == datetime.datetime(2024, 8, 28, 9, 46, 25)


@mock.patch("logic.task_assignment.greedy.get_general_duration_for_actions_from_order",
            return_value=datetime.timedelta(seconds=280))
def test_get_best_greedy_insertion_multiple_amrs(general_duration_mock):
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="H",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )


    order3 = Order(
        orderId='3', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="G",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    planned_order_list_amr1 = [PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                                estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                                order=order1)
                              ]

    planned_order_list_amr2 = [PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                                estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                                order=order3),
                               ]

    amr_states = [SystemStateAMR(amrState=AMRState(amrId='1',
                                                   connectionState=ConnectionState.ONLINE,
                                                   orderUpdateId=0,
                                                   orderId='',
                                                   lastNodeId='B',
                                                   lastNodeSequenceId=0,
                                                   nodeStates=[],
                                                   edgeStates=[],
                                                   actionStates=[],
                                                   driving=False,
                                                   distanceSinceLastNode=0,
                                                   operatingMode=OperatingMode.AUTOMATIC,
                                                   amrPosition=AMRPosition(x=50, y=0, mapId='map1',
                                                                            positionInitialized=True),
                                                   batteryState=BatteryState(batteryCharge=100, charging=False)),
                                 plannedOrders=planned_order_list_amr1,
                                 token=['B']),
                  SystemStateAMR(amrState=AMRState(amrId='2',
                                                   connectionState=ConnectionState.ONLINE,
                                                   orderUpdateId=0,
                                                   orderId='',
                                                   lastNodeId='G',
                                                   lastNodeSequenceId=0,
                                                   nodeStates=[],
                                                   edgeStates=[],
                                                   actionStates=[],
                                                   driving=False,
                                                   distanceSinceLastNode=0,
                                                   operatingMode=OperatingMode.AUTOMATIC,
                                                   amrPosition=AMRPosition(x=150, y=30, mapId='map1',
                                                                            positionInitialized=True),
                                                   batteryState=BatteryState(batteryCharge=100, charging=False)),
                                 plannedOrders=planned_order_list_amr2,
                                 token=['G'])
                  ]
    data_amr_states = json.dumps(
        amr_states,
        default=lambda o: serialize_json(o)
    )
    amr_states_dict = json.loads(data_amr_states)

    order_info = NewOrderInfo(orderId='4', sourceId='G', sinkId='D',
                              startTime=datetime.datetime(2024, 8, 28, 9, 30),
                              dueTime=datetime.datetime(2024, 8, 28, 10, 30),
                              dimension=Dimension(x=20, y=20, z=20, weight=0.4),
                              pickupTime=60, dropoffTime=60, status=OrderStatus.NEW)

    order = Order(
        orderId='4', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="G",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="D",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
        ],
        edges=[]
    ).dict(exclude_none=True)

    dispatching_strategies = {}
    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY] = Greedy(ActionIdCounter(nextActionId=1))
    ttm = {('A', 'A'): 0, ('A', 'B'): 25, ('A', 'C'): 40, ('A', 'D'): 40, ('A', 'E'): 65, ('A', 'F'): 65,
           ('A', 'G'): 90, ('A', 'H'): 90, ('A', 'I'): 105, ('B', 'A'): 25, ('B', 'B'): 0, ('B', 'C'): 15,
           ('B', 'D'): 15, ('B', 'E'): 40, ('B', 'F'): 40, ('B', 'G'): 65, ('B', 'H'): 65, ('B', 'I'): 80,
           ('C', 'A'): 40, ('C', 'B'): 15, ('C', 'C'): 0, ('C', 'D'): 30, ('C', 'E'): 25, ('C', 'F'): 55,
           ('C', 'G'): 50, ('C', 'H'): 80, ('C', 'I'): 65, ('D', 'A'): 40, ('D', 'B'): 15, ('D', 'C'): 30,
           ('D', 'D'): 0, ('D', 'E'): 55, ('D', 'F'): 25, ('D', 'G'): 80, ('D', 'H'): 50, ('D', 'I'): 65,
           ('E', 'A'): 65, ('E', 'B'): 40, ('E', 'C'): 25, ('E', 'D'): 55, ('E', 'E'): 0, ('E', 'F'): 30,
           ('E', 'G'): 25, ('E', 'H'): 55, ('E', 'I'): 40, ('F', 'A'): 65, ('F', 'B'): 40, ('F', 'C'): 55,
           ('F', 'D'): 25, ('F', 'E'): 30, ('F', 'F'): 0, ('F', 'G'): 55, ('F', 'H'): 25, ('F', 'I'): 40,
           ('G', 'A'): 90, ('G', 'B'): 65, ('G', 'C'): 50, ('G', 'D'): 80, ('G', 'E'): 25, ('G', 'F'): 55,
           ('G', 'G'): 0, ('G', 'H'): 30, ('G', 'I'): 15, ('H', 'A'): 90, ('H', 'B'): 65, ('H', 'C'): 80,
           ('H', 'D'): 50, ('H', 'E'): 55, ('H', 'F'): 25, ('H', 'G'): 30, ('H', 'H'): 0, ('H', 'I'): 15,
           ('I', 'A'): 105, ('I', 'B'): 80, ('I', 'C'): 65, ('I', 'D'): 65, ('I', 'E'): 40, ('I', 'F'): 40,
           ('I', 'G'): 15, ('I', 'H'): 15, ('I', 'I'): 0}

    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].ttm = ttm
    amr_id, insertion_position, estimated_start_time, estimated_end_time = (
        dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].get_greedy_best_insertion(amr_states_dict, order,
                                                                                          order_info))
    assert amr_id == '2'
    assert insertion_position == 1
    assert estimated_start_time == datetime.datetime(2024, 8, 28, 9, 40)
    assert estimated_end_time == datetime.datetime(2024, 8, 28, 9, 46)


def test_optimize_by_swapping():
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="B",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order2 = Order(
        orderId='2', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="I",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="F",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order3 = Order(
        orderId='3', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="C",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="I",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order_sequence = [PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       order=order1),
                      PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 50),
                                       order=order2),
                      PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 50),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 10),
                                       order=order3)
                      ]
    order_sequence = json.dumps(
        order_sequence,
        default=lambda o: serialize_json(o)
    )
    order_sequence = json.loads(order_sequence)

    dispatching_strategies = {}
    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY] = Greedy(ActionIdCounter(nextActionId=1))
    ttm = {('A', 'A'): 0, ('A', 'B'): 25, ('A', 'C'): 40, ('A', 'D'): 40, ('A', 'E'): 65, ('A', 'F'): 65,
           ('A', 'G'): 90, ('A', 'H'): 90, ('A', 'I'): 105, ('B', 'A'): 25, ('B', 'B'): 0, ('B', 'C'): 15,
           ('B', 'D'): 15, ('B', 'E'): 40, ('B', 'F'): 40, ('B', 'G'): 65, ('B', 'H'): 65, ('B', 'I'): 80,
           ('C', 'A'): 40, ('C', 'B'): 15, ('C', 'C'): 0, ('C', 'D'): 30, ('C', 'E'): 25, ('C', 'F'): 55,
           ('C', 'G'): 50, ('C', 'H'): 80, ('C', 'I'): 65, ('D', 'A'): 40, ('D', 'B'): 15, ('D', 'C'): 30,
           ('D', 'D'): 0, ('D', 'E'): 55, ('D', 'F'): 25, ('D', 'G'): 80, ('D', 'H'): 50, ('D', 'I'): 65,
           ('E', 'A'): 65, ('E', 'B'): 40, ('E', 'C'): 25, ('E', 'D'): 55, ('E', 'E'): 0, ('E', 'F'): 30,
           ('E', 'G'): 25, ('E', 'H'): 55, ('E', 'I'): 40, ('F', 'A'): 65, ('F', 'B'): 40, ('F', 'C'): 55,
           ('F', 'D'): 25, ('F', 'E'): 30, ('F', 'F'): 0, ('F', 'G'): 55, ('F', 'H'): 25, ('F', 'I'): 40,
           ('G', 'A'): 90, ('G', 'B'): 65, ('G', 'C'): 50, ('G', 'D'): 80, ('G', 'E'): 25, ('G', 'F'): 55,
           ('G', 'G'): 0, ('G', 'H'): 30, ('G', 'I'): 15, ('H', 'A'): 90, ('H', 'B'): 65, ('H', 'C'): 80,
           ('H', 'D'): 50, ('H', 'E'): 55, ('H', 'F'): 25, ('H', 'G'): 30, ('H', 'H'): 0, ('H', 'I'): 15,
           ('I', 'A'): 105, ('I', 'B'): 80, ('I', 'C'): 65, ('I', 'D'): 65, ('I', 'E'): 40, ('I', 'F'): 40,
           ('I', 'G'): 15, ('I', 'H'): 15, ('I', 'I'): 0}

    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].ttm = ttm
    new_order_sequence, optimization_found = (
        dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].optimize_by_swapping(order_sequence))
    order_sequence_id_list = []
    for item in new_order_sequence:
        order_sequence_id_list.append(item['order']['orderId'])

    assert optimization_found is True
    assert order_sequence_id_list == ['1', '3', '2']


def test_update_planned_order_times():
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="B",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order2 = Order(
        orderId='2', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="I",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="F",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order3 = Order(
        orderId='3', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="C",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="I",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='pick', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order_sequence = [PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       order=order1),
                      PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 50),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 10),
                                       order=order3),
                      PlannedOrderInfo(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 50),
                                       order=order2)
                      ]
    order_sequence = json.dumps(
        order_sequence,
        default=lambda o: serialize_json(o)
    )
    order_sequence = json.loads(order_sequence)

    dispatching_strategies = {}
    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY] = Greedy(ActionIdCounter(nextActionId=1))

    ttm = {('A', 'A'): 0, ('A', 'B'): 25, ('A', 'C'): 40, ('A', 'D'): 40, ('A', 'E'): 65, ('A', 'F'): 65,
           ('A', 'G'): 90, ('A', 'H'): 90, ('A', 'I'): 105, ('B', 'A'): 25, ('B', 'B'): 0, ('B', 'C'): 15,
           ('B', 'D'): 15, ('B', 'E'): 40, ('B', 'F'): 40, ('B', 'G'): 65, ('B', 'H'): 65, ('B', 'I'): 80,
           ('C', 'A'): 40, ('C', 'B'): 15, ('C', 'C'): 0, ('C', 'D'): 30, ('C', 'E'): 25, ('C', 'F'): 55,
           ('C', 'G'): 50, ('C', 'H'): 80, ('C', 'I'): 65, ('D', 'A'): 40, ('D', 'B'): 15, ('D', 'C'): 30,
           ('D', 'D'): 0, ('D', 'E'): 55, ('D', 'F'): 25, ('D', 'G'): 80, ('D', 'H'): 50, ('D', 'I'): 65,
           ('E', 'A'): 65, ('E', 'B'): 40, ('E', 'C'): 25, ('E', 'D'): 55, ('E', 'E'): 0, ('E', 'F'): 30,
           ('E', 'G'): 25, ('E', 'H'): 55, ('E', 'I'): 40, ('F', 'A'): 65, ('F', 'B'): 40, ('F', 'C'): 55,
           ('F', 'D'): 25, ('F', 'E'): 30, ('F', 'F'): 0, ('F', 'G'): 55, ('F', 'H'): 25, ('F', 'I'): 40,
           ('G', 'A'): 90, ('G', 'B'): 65, ('G', 'C'): 50, ('G', 'D'): 80, ('G', 'E'): 25, ('G', 'F'): 55,
           ('G', 'G'): 0, ('G', 'H'): 30, ('G', 'I'): 15, ('H', 'A'): 90, ('H', 'B'): 65, ('H', 'C'): 80,
           ('H', 'D'): 50, ('H', 'E'): 55, ('H', 'F'): 25, ('H', 'G'): 30, ('H', 'H'): 0, ('H', 'I'): 15,
           ('I', 'A'): 105, ('I', 'B'): 80, ('I', 'C'): 65, ('I', 'D'): 65, ('I', 'E'): 40, ('I', 'F'): 40,
           ('I', 'G'): 15, ('I', 'H'): 15, ('I', 'I'): 0}

    dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].ttm = ttm

    new_order_sequence = (
        dispatching_strategies[TASK_ASSIGNMENT_STRATEGY_GREEDY].update_planned_orders_time(order_sequence))
    assert transform_str_to_datetime(new_order_sequence[0]['estimatedStartTime']) == datetime.datetime(2024, 8, 28, 9, 30)
    assert transform_str_to_datetime(new_order_sequence[0]['estimatedEndTime']) == datetime.datetime(2024, 8, 28, 9, 40)
    assert transform_str_to_datetime(new_order_sequence[1]['estimatedStartTime']) == datetime.datetime(2024, 8, 28, 9, 40)
    # Time shift is ok , because in order planning function before time will be updated already
    assert transform_str_to_datetime(new_order_sequence[1]['estimatedEndTime']) == datetime.datetime(2024, 8, 28, 9, 45, 45)
    assert transform_str_to_datetime(new_order_sequence[2]['estimatedStartTime']) == datetime.datetime(2024, 8, 28, 9, 45, 45)
    assert transform_str_to_datetime(new_order_sequence[2]['estimatedEndTime']) == datetime.datetime(2024, 8, 28, 9, 50, 50)

