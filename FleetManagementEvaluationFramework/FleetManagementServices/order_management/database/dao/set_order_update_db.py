import logging
import data.enums as enums

import config.config_file
from api.server_api_models import OrderUpdateRequest
from database.db_init import Session
from database.models.db_order_management_models import OrderManagement, OrderInfo

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def set_amr_id_update_db(request_body: OrderUpdateRequest):
    with Session() as session:
        data = session.query(OrderManagement).filter(OrderManagement.order_id == request_body.orderId).first()

        if data:
            data.amr_id = request_body.amrId
            if request_body.estimatedStartTime is not None:
                data.estimated_start_time = request_body.estimatedStartTime
            if request_body.estimatedEndTime is not None:
                data.estimated_end_time = request_body.estimatedEndTime
            session.commit()
        else:
            logger.exception(f'Error Dataset for Order {request_body.orderId} not found!')
            raise Exception(f'Error Dataset for Order {request_body.orderId} not found!')
    return


def set_order_status_update_db(request_body: OrderUpdateRequest):
    with (Session() as session):
        data = session.query(OrderInfo).filter(OrderInfo.order_id == request_body.orderId).first()
        if data:
            if data.status == enums.OrderStatus.NEW:
                data.status = request_body.orderStatus
            if data.status == enums.OrderStatus.PLANNED:
                data.status = request_body.orderStatus
            if data.status == enums.OrderStatus.STARTED:
                data.status = request_body.orderStatus
            if data.status == enums.OrderStatus.PICKUP:
                if (request_body.orderStatus == enums.OrderStatus.PICKUP
                        or request_body.orderStatus == enums.OrderStatus.DROPOFF or
                        request_body.orderStatus == enums.OrderStatus.FINISHED):
                    data.status = request_body.orderStatus
            if data.status == enums.OrderStatus.DROPOFF:
                if (request_body.orderStatus == enums.OrderStatus.DROPOFF or
                        request_body.orderStatus == enums.OrderStatus.FINISHED):
                    data.status = request_body.orderStatus
            if data.status == enums.OrderStatus.FINISHED:
                if (request_body.orderStatus == enums.OrderStatus.FINISHED):
                    data.status = request_body.orderStatus
            session.commit()
        else:
            logger.exception(f'Error Dataset for Order {request_body.orderId} not found!')
            raise Exception(f'Error Dataset for Order {request_body.orderId} not found!')
    return

