import logging
import config.config_file
from api.server_api_models import OrderInfoRequest, SetSKURequest
from database.db_init import Session
from database.models.db_order_management_models import OrderInfo

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def get_item_sku_info(request_body: OrderInfoRequest):
    with Session() as session:
        item_sku_infos = session.query(OrderInfo.item_sku_id).filter(OrderInfo.order_id.in_(request_body.orderIds)).all()

    return item_sku_infos


def set_sku_id_in_db(request_body: SetSKURequest):
    with Session() as session:
        order_info = session.query(OrderInfo).filter(OrderInfo.order_id == request_body.orderId).first()
        if order_info:
            order_info.itemSkuId = request_body.skuId
            session.commit()
        else:
            logger.exception('No suitable dataset found')
            raise Exception('No suitable dataset found')
    return
