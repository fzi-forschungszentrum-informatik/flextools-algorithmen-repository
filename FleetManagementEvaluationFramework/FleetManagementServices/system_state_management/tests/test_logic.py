import datetime
from unittest import mock

import data.db_init
from api.client_api_models import NodesResponse
from api.server_api_models import GetAMRStateRequest, SetAMRConnectionStateRequest, \
    SystemTimeResponse, SystemTimeRequest, PlannedOrderIncoming, AMRRequest, OrderFinishRequest, AMRPauseRequest
from data.enums import BlockingType, ConnectionState, OperatingMode, ActionStatus
from data.models import Route, Node, Action, NodePosition, ActionParameter, Edge, BatteryState, ActionState, \
    Order, PlannedOrderInfos, PlannedOrderSequenceIncoming, AMRPosition, AMRState, NewAMRSystemRequest
from logic.check_amr_processes_order import check_amr_for_processing_order_for_new_planned_orders, \
    check_process_next_order
from logic.services import (service_get_amr_state, service_set_amr_state_with_response, service_set_amr_connection_state,
                            service_set_system_time, service_get_system_time, service_set_planned_order_in_queue,
                            service_update_planned_order_sequence, service_get_amr_data,
                            service_remove_finished_order_from_queue, service_add_new_amr, service_set_amr_to_pause)


def test_check_amr_for_processing_order_for_new_planned_orders_empty(system_state_management_db_mock_empty, monkeypatch):
    monkeypatch.setattr("data.db_init.database", system_state_management_db_mock_empty)
    planned_order = check_amr_for_processing_order_for_new_planned_orders(amr_id='1')
    assert planned_order is None


def test_check_amr_for_processing_order_for_new_planned_orders(system_state_management_db_mock_with_orders,
                                                               monkeypatch):
    node_list = [Node(
        nodeId="A",
        sequenceId=1,
        released=True,
        nodePosition=NodePosition(x=0, y=0, theta=0, mapId='map1'),
        actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                        actionParameters=[ActionParameter(key='duration', value=90)])]
    ),
        Node(
            nodeId="B",
            sequenceId=1,
            released=True,
            nodePosition=NodePosition(x=50, y=0, theta=0, mapId='map1'),
            actions=[]
        ),
        Node(
            nodeId="H",
            sequenceId=1,
            released=True,
            nodePosition=NodePosition(x=150, y=-30, theta=0, mapId='map1'),
            actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                            actionParameters=[ActionParameter(key='duration', value=175)])]
        )]

    edge_list = [Edge(edgeId='ab', sequenceId=0, released=True, startNodeId='A', endNodeId='B', maxSpeed=2,
                      length=50, actions=[]),
                 Edge(edgeId='ah', sequenceId=0, released=True, startNodeId='B', endNodeId='H', maxSpeed=2,
                      length=50, actions=[])]

    with mock.patch("logic.check_amr_processes_order.request_routes_for_amrs") as mock_request_route_for_order:
        mock_response = mock.Mock()
        mock_response.json.return_value = [Route(nodes=node_list, edges=edge_list).dict(exclude_none=True)]
        mock_request_route_for_order.return_value = mock_response
        monkeypatch.setattr("data.db_init.database", system_state_management_db_mock_with_orders)
        planned_orders = check_amr_for_processing_order_for_new_planned_orders(amr_id='1')
        assert planned_orders[0].timestamp == datetime.datetime(2030, 8, 28, 9, 30)
        assert planned_orders[0].order.orderId == '1'
        assert len(planned_orders[0].order.nodes) == 3
        assert len(planned_orders[0].order.edges) == 2


def test_check_process_next_order(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)
    next_order_bool = check_process_next_order(amr_id='1')
    assert next_order_bool is False


def test_service_get_amr_state(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)
    amr_state_request = GetAMRStateRequest(amrIds=['1', '2'])
    response = service_get_amr_state(amr_state_request)
    assert response[0].amrState.amrId == '1'
    assert response[0].amrState.orderId == '1'
    assert len(response[0].amrState.actionStates) == 2
    assert response[1].amrState.amrId == '2'
    assert response[1].amrState.orderId == ''
    assert response[1].amrState.lastNodeId == 'D'
    assert len(response[1].amrState.nodeStates) == 0


def test_service_set_and_get_amr_state(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)
    set_amr_state_request = AMRState(
        timestamp=datetime.datetime(2024, 8, 28, 9, 30),
        amrId='1',
        connectionState=ConnectionState.ONLINE,
        orderId='1',
        orderUpdateId=0,
        lastNodeId='I',
        lastNodeSequenceId=0,
        driving=False,
        paused=False,
        distanceSinceLastNode=0,
        operatingMode=OperatingMode.AUTOMATIC,
        amrPosition=AMRPosition(x=150, y=0, mapId='map1', positionInitialized=False),
        batteryState=BatteryState(batteryCharge=100, charging=False),
        nodeStates=[],
        edgeStates=[],
        actionStates=[ActionState(actionId='1', actionStatus=ActionStatus.FINISHED,
                                  actionType='Pickup'),
                      ActionState(actionId='2', actionStatus=ActionStatus.FAILED,
                                   actionType='Dropoff')]
    )
    response = service_set_amr_state_with_response(set_amr_state_request)
    assert response.plannedOrders == []

    response = service_get_amr_data(AMRRequest(amrIds=['*']))
    assert len(response) == 3
    assert response[0].lastNodeId == 'I'


def test_service_set_amr_connection_state(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)
    service_set_amr_connection_state(SetAMRConnectionStateRequest(timestamp=datetime.datetime(2024, 8, 28, 10),
                                                                  amrId='1',
                                                                  connectionState=ConnectionState.OFFLINE))


def test_set_and_get_system_time(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)

    set_system_time = SystemTimeResponse(timestamp=datetime.datetime(2030, 8, 30, 13))
    service_set_system_time(set_system_time)
    get_system_time = SystemTimeRequest(sysTime='*')
    response = service_get_system_time(get_system_time)
    assert response.timestamp == datetime.datetime(2030, 8, 30, 13)


def test_service_set_planned_order(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)
    order = Order(
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
                actions=[Action(actionId='2', actionType='Dropoff', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=175)])]
            ),
        ],
        edges=[]
    )
    planned_order_incoming = PlannedOrderIncoming(amrId='1', order=order, index=1,
                                                  estimatedStartTime=datetime.datetime(2024, 8, 29, 9),
                                                  estimatedEndTime=datetime.datetime(2024, 8, 29, 9, 10))
    service_set_planned_order_in_queue(planned_order_incoming)


def test_service_update_planned_order_sequence(system_state_management_db_mock_with_orders_amr, monkeypatch):
    monkeypatch.setattr("data.db_init.database",
                        system_state_management_db_mock_with_orders_amr)
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
                actions=[Action(actionId='2', actionType='Pickup', blockingType=BlockingType.HARD,
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

    planned_order1 = PlannedOrderInfos(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 50),
                                       order=order1)
    planned_order2 = PlannedOrderInfos(estimatedStartTime=datetime.datetime(2024, 8, 28, 9, 30),
                                       estimatedEndTime=datetime.datetime(2024, 8, 28, 9, 40),
                                       order=order2)

    planned_order_sequence = PlannedOrderSequenceIncoming(amrId='1', orders=[planned_order2, planned_order1])
    service_update_planned_order_sequence(planned_order_sequence)


def test_service_add_new_amr(system_state_management_db_mock_empty, monkeypatch):
    node_list = NodesResponse(nodes=[
        Node(
            nodeId="A",
            sequenceId=1,
            released=True,
            nodePosition=NodePosition(x=0, y=0, mapId='map1'),
            actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                            actionParameters=[ActionParameter(key='duration', value=90)])]
        ),
        Node(
            nodeId="B",
            sequenceId=1,
            released=True,
            nodePosition=NodePosition(x=50, y=0, mapId='map1'),
            actions=[]
        ),
        Node(
            nodeId="H",
            sequenceId=1,
            released=True,
            nodePosition=NodePosition(x=150, y=-30, mapId='map1'),
            actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                            actionParameters=[ActionParameter(key='duration', value=175)])]
        )]).dict()

    with mock.patch("logic.services.get_nodes_info") as mock_get_nodes_info:
        mock_response = mock.Mock()
        mock_response.json.return_value = node_list
        mock_get_nodes_info.return_value = mock_response
        monkeypatch.setattr("data.db_init.database", system_state_management_db_mock_empty)
        service_add_new_amr(
            NewAMRSystemRequest(amrId="5", lastNodeId="A", layoutId="map1", maxReachBattery=5000))
        check = service_get_amr_data(AMRRequest(amrIds=["5"]))
        assert check[0].amrId == "5"


def test_service_set_amr_to_pause(system_state_management_db_mock_empty, monkeypatch):
    monkeypatch.setattr("data.db_init.database", system_state_management_db_mock_empty)
    service_set_amr_to_pause(AMRPauseRequest(amrId="1", pause=True))
    assert data.db_init.database['system_state_management'].amr_states["1"].amrState.paused is True
    service_set_amr_to_pause(AMRPauseRequest(amrId="1", pause=False))
    assert data.db_init.database['system_state_management'].amr_states["1"].amrState.paused is False

