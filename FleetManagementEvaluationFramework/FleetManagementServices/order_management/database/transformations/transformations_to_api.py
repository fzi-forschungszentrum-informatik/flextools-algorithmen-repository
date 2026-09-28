import logging

import config.config_file
from api.server_api_models import OrderInfoResponse, SKUInfoResponse, OrderStatusResponse

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def transform_order_info_data_to_api_obj(order_info_data, amr_data):
    response = []
    if len(order_info_data) == len(amr_data):
        for i, item in enumerate(order_info_data):
            if amr_data[i][1] is None:
                start_time = item[2]
            else:
                start_time = amr_data[i][1]
            if amr_data[i][2] is None:
                due_time = item[3]
            else:
                due_time = amr_data[i][2]
            print(item)
            response.append(OrderInfoResponse(orderId=item[0],
                                              amrId=amr_data[i][0],
                                              orderStatus=item[1],
                                              startTime=start_time,
                                              dueTime=due_time,
                                              sourceNodeId=item[4],
                                              sinkNodeId=item[5]))
    else:
        logger.exception(f'Error dimension of data objects does not fit!')
        raise Exception(f'Error dimension of data objects does not fit!')
    return response


def transform_item_sku_info_to_api_obj(item_sku_data):
    response = []
    for item in item_sku_data:
        response.append(SKUInfoResponse(itemSkuId=item[0]))
    return response


def transform_order_status_to_api_obj(order_status_data):
    response = []
    for item in order_status_data:
        response.append(OrderStatusResponse(orderStatus=item[0]))
    return response
