from api.server_api_models import OrderInfoRequest
from database.db_init import Session
from database.models.db_order_management_models import OrderInfo, OrderManagement


def get_order_info_from_db(request_body: OrderInfoRequest):
    with (Session() as session):
        if request_body.orderIds == ['*']:
            order_info_data = session.query(OrderInfo.order_id,
                                            OrderInfo.status,
                                            OrderInfo.start_time,
                                            OrderInfo.due_time,
                                            OrderInfo.source_id,
                                            OrderInfo.sink_id).all()
            amr_data = session.query(OrderManagement.amr_id, OrderManagement.estimated_start_time,
                                     OrderManagement.estimated_end_time).all()
        else:
            order_info_data = session.query(OrderInfo.order_id,
                                            OrderInfo.status,
                                            OrderInfo.start_time,
                                            OrderInfo.due_time,
                                            OrderInfo.source_id,
                                            OrderInfo.sink_id).filter(OrderInfo.order_id.in_(request_body.orderIds)).all()
            amr_data = session.query(OrderManagement.amr_id,  OrderManagement.estimated_start_time,
                                     OrderManagement.estimated_end_time).filter(OrderManagement.order_id.in_(request_body.orderIds)).all()
    return order_info_data, amr_data


def get_order_state_info_from_db(request_body: OrderInfoRequest):
    with Session() as session:
        order_status_data = session.query(OrderInfo.status).filter(OrderInfo.order_id.in_(request_body.orderIds)).all()
    return order_status_data


def get_last_order_info_from_db():
    with Session() as session:
        order_id_data = session.query(OrderInfo.order_id).all()
    return order_id_data

