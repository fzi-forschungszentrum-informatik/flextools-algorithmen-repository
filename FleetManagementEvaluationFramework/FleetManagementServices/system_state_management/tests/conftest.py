import pytest
import datetime
from unittest import mock

from config.config_file import SYSTEM_STATE_FILE_TEST
from data.enums import BlockingType, ConnectionState, ActionStatus, OperatingMode
from data.models import Order, Node, NodePosition, Action, ActionParameter, PlannedOrderInfos, AMRState, \
    NodeState, ActionState, BatteryState
from data.system_state_management_db import SystemStateManagementDb


@pytest.fixture()
def system_state_management_db_mock_empty():
    database = {}
    with mock.patch('data.system_state_management_db.get_system_time') as mock_system_time:
        mock_response = mock.Mock()
        mock_response.json.return_value = {'systemTime': datetime.datetime.now()}
        mock_system_time.return_value = mock_response
        database['system_state_management'] = SystemStateManagementDb(SYSTEM_STATE_FILE_TEST)
        return database


@pytest.fixture()
def system_state_management_db_mock_with_orders():
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="H",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order2 = Order(
        orderId='2', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="E",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="D",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=-30, mapId='map1'),
                actions=[Action(actionId='2', actionType='Dropoff', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    planned_order1 = PlannedOrderInfos(estimatedStartTime=datetime.datetime(2030, 8, 28, 9, 30),
                                       estimatedEndTime=datetime.datetime(2030, 8, 28, 9, 40),
                                       order=order1)
    planned_order2 = PlannedOrderInfos(estimatedStartTime=datetime.datetime(2030, 8, 28, 9, 40),
                                       estimatedEndTime=datetime.datetime(2030, 8, 28, 9, 50),
                                       order=order2)

    database = {}
    with mock.patch('data.system_state_management_db.get_system_time') as mock_system_time:
        mock_response = mock.Mock()
        mock_response.json.return_value = {'systemTime': datetime.datetime.now()}
        mock_system_time.return_value = mock_response
        database['system_state_management'] = SystemStateManagementDb(SYSTEM_STATE_FILE_TEST)
        database['system_state_management'].amr_states['1'].plannedOrders.insert(0, planned_order1)
        database['system_state_management'].amr_states['1'].plannedOrders.insert(1, planned_order2)
        return database


@pytest.fixture()
def system_state_management_db_mock_with_orders_amr():
    order1 = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="A",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="H",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=150, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    order2 = Order(
        orderId='2', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="E",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="D",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=-30, mapId='map1'),
                actions=[Action(actionId='2', actionType='Dropoff', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )

    planned_order1 = PlannedOrderInfos(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       order=order1)
    planned_order2 = PlannedOrderInfos(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 50),
                                       order=order2)

    database = {}
    with mock.patch('data.system_state_management_db.get_system_time') as mock_system_time:
        mock_response = mock.Mock()
        mock_response.json.return_value = {'systemTime': datetime.datetime.now()}
        mock_system_time.return_value = mock_response
        database['system_state_management'] = SystemStateManagementDb(SYSTEM_STATE_FILE_TEST)
        database['system_state_management'].amr_states['1'].plannedOrders.insert(0, planned_order1)
        database['system_state_management'].amr_states['1'].plannedOrders.insert(1, planned_order2)

        amr_state = AMRState(timestamp=datetime.datetime(2024, 8, 28, 9, 30),
                             amrId='1',
                             connectionState=ConnectionState.ONLINE,
                             orderId='1',
                             orderUpdateId=0,
                             lastNodeId='B',
                             lastNodeSequenceId=0,
                             driving=True,
                             distanceSinceLastNode=30,
                             operatingMode=OperatingMode.AUTOMATIC,
                             batteryState=BatteryState(batteryCharge=100, charging=False),
                             nodeStates=[NodeState(nodeId='D', sequenceId=0,
                                                           nodePosition=NodePosition(x=50, y=-30, mapId='map1'),
                                                           released=True)],
                             edgeStates=[],
                             actionStates=[ActionState(actionId='1', actionStatus=ActionStatus.FINISHED,
                                                               actionType='Pickup'),
                                                   ActionState(actionId='2', actionStatus=ActionStatus.WAITING,
                                                                actionType='Dropoff')]
                             )
        database['system_state_management'].amr_states['1'].amrState = amr_state
        return database
