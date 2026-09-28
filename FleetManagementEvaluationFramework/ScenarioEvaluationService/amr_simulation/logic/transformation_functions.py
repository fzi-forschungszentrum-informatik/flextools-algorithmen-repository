from api.server_api_models import OrderStateRequest, OrderUpdateVDABodyHeader
from data.models import Order
from logic.general_functions import transform_str_to_datetime


def transform_order_to_order_state_request(request_body: OrderUpdateVDABodyHeader) -> OrderStateRequest:
    order_state_request = OrderStateRequest(timestamp=transform_str_to_datetime(request_body.timestamp),
                                            amrId=request_body.serialNumber,
                                            order=Order(orderId=request_body.orderId,
                                                        orderUpdateId=request_body.orderUpdateId,
                                                        nodes=request_body.nodes,
                                                        edges=request_body.edges))

    return order_state_request
