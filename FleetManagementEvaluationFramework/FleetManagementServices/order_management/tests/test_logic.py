import datetime
import json
from unittest import mock

from api.client_api_models import OrderUpdateResponse
from api.serialization import serialize_json
from api.server_api_models import OrderUpdateRequest, OrderInfoRequest
from data.enums import OrderStatus, BlockingType
from data.models import NewOrderInfo, Dimension, Order, Node, Action, NodePosition, ActionParameter
from logic.services import service_get_new_order, service_set_order_update, service_get_order_infos
from logic.transform_new_order import transform_new_order


def test_transform_new_order():
    new_order_info = NewOrderInfo(orderId='1', sourceId='C', sinkId='F',
                                  startTime=datetime.datetime(2024, 8, 28, 9, 30),
                                  dueTime=datetime.datetime(2024, 8, 28, 10, 30),
                                  dimension=Dimension(x=20, y=20, z=20, weight=0.4),
                                  pickupTime=60, dropoffTime=60, status=OrderStatus.NEW)
    order = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="C",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="F",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=-30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
        ],
        edges=[]
    )
    order_update = OrderUpdateResponse(amrId='1', order=order, estimatedStartTime=datetime.datetime.now(),
                                       estimatedEndTime=datetime.datetime.now())
    order_update = json.dumps(
        order_update,
        default=lambda o: serialize_json(o)
    )
    order_update = json.loads(order_update)
    response = transform_new_order(new_order_info, order_update)

    assert response.amrId == '1'
    assert response.newOrderInfo.status == OrderStatus.PLANNED
    assert response.order.orderId == '1'
    assert len(response.order.nodes) == 2


def test_service_get_new_order_and_order_update_with_info(order_management_db_mock):
    new_order_info = NewOrderInfo(orderId='1', sourceId='C', sinkId='F',
                                  startTime=datetime.datetime(2024, 8, 28, 9, 30),
                                  dueTime=datetime.datetime(2024, 8, 28, 10, 30),
                                  dimension=Dimension(x=20, y=20, z=20, weight=0.4),
                                  pickupTime=60, dropoffTime=60, status=OrderStatus.NEW)
    order = Order(
        orderId='1', orderUpdateId=0,
        nodes=[
            Node(
                nodeId="C",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=50, y=30, mapId='map1'),
                actions=[Action(actionId='1', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
            Node(
                nodeId="F",
                sequenceId=1,
                released=True,
                nodePosition=NodePosition(x=100, y=-30, mapId='map1'),
                actions=[Action(actionId='2', actionType='Pickup', blockingType=BlockingType.HARD,
                                actionParameters=[ActionParameter(key='duration', value=90)])]
            ),
        ],
        edges=[]
    )
    order_update_request = OrderUpdateRequest(amrId='1', orderStatus=OrderStatus.PICKUP, orderId='1',
                                              estimatedStartTime=datetime.datetime.now(),
                                              estimatedEndTime=datetime.datetime.now())
    with mock.patch("logic.services.start_to_plan_order") as mock_start_to_plan_order:
        mock_response = mock.Mock()
        mock_response.json.return_value = OrderUpdateResponse(amrId='1', order=order,
                                                              estimatedStartTime=datetime.datetime.now(),
                                                              estimatedEndTime=datetime.datetime.now()
                                                              ).dict(exclude_none=True)
        mock_start_to_plan_order.return_value = mock_response
        service_get_new_order(new_order_info)
        service_set_order_update(order_update_request)
        order_info_request = OrderInfoRequest(orderIds=['1'])
        response = service_get_order_infos(order_info_request)
        assert response[0].orderId == '1'
        assert response[0].amrId == '1'
        assert response[0].orderStatus == OrderStatus.PICKUP

