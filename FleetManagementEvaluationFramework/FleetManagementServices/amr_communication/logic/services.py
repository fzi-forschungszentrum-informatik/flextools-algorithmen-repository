import logging

import config.config_file
from api.api_config import mqtt_send_planned_order_to_amr
from api.server_api_models import OrderAMRRequest

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def service_send_planned_order_to_amr(request_body: OrderAMRRequest):
    logger.info(f'Planned order {request_body.order.orderId} successfully sent to amr at timestamp'
                f' {request_body.timestamp}!')
    mqtt_send_planned_order_to_amr(request_body.order, request_body.amrId, request_body.timestamp)
    return
