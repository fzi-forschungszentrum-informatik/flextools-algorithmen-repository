import logging

from api.client_api import start_to_plan_order, get_free_storage_location, get_items_from_storage_location_tracking, \
    set_new_item_in_storage_location_tracking, store_skus, store_skus
from api.client_api_models import StorageLocationRequest, NewItemRequest, SkusStoreRequestBody
from api.server_api_models import OrderUpdateRequest, OrderInfoRequest, SetSKURequest, StationInfoRequest, \
    StationIdResponse, RepositionOrder
from config.config_file import STORAGE_LOCATION_ALGORITHM

from data.models import NewOrderInfo
from database.dao.add_order_state_to_db import add_order_state_to_db
from database.dao.order_info_dao import get_order_info_from_db, get_order_state_info_from_db

from database.dao.set_order_update_db import set_amr_id_update_db, set_order_status_update_db
from database.dao.item_sku_info_dao import get_item_sku_info, set_sku_id_in_db
from database.dao.station_info_dao import get_station_ids_for_order_from_db
from database.reset_database import reset_database
from database.transformations.transformations_to_api import transform_order_info_data_to_api_obj, \
    transform_item_sku_info_to_api_obj, transform_order_status_to_api_obj

from logic.transform_new_order import transform_new_order, transform_reposition_order
import config.config_file

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def service_get_new_order(request_body: NewOrderInfo):
    logger.debug(f'Get new order with infos: {request_body}')
    if request_body.sinkId is None:
        if config.config_file.STORAGE_LOCATION_TRACKING is True:
            response = get_free_storage_location(StorageLocationRequest(inputData="Hello", algorithm=
                                                                        STORAGE_LOCATION_ALGORITHM)).json()
            request_body.sinkId = response['decision']['stationId']
    if config.config_file.STORAGE_LOCATION_TRACKING is True and request_body.itemSkuId is not None:
        item_list = get_items_from_storage_location_tracking().json()
        item_initialized = False
        for item in item_list:
            if item['number'] == request_body.itemSkuId:
                item_initialized = True
                request_body.itemSkuId = item['id']
                break
        if item_initialized is False and request_body.sourceId[0] == 'S':
            response = set_new_item_in_storage_location_tracking(NewItemRequest(number=request_body.itemSkuId,
                                                                                description='Item')).json()
            request_body.itemSkuId = response['id']
            response = store_skus(SkusStoreRequestBody(locationId=request_body.sourceId,
                                                       itemId=request_body.itemSkuId)).json()
            request_body.itemSkuId = response['skuId']
    order_update = start_to_plan_order(request_body).json()
    if order_update is None:
        logger.exception(f'Error in Dispatching for order {request_body.orderId}')
        raise Exception(f'Error in Dispatching for order {request_body.orderId}')
    order_state = transform_new_order(request_body, order_update)
    add_order_state_to_db(order_state)
    return


def service_set_order_update(request_body: OrderUpdateRequest):
    set_amr_id_update_db(request_body)
    set_order_status_update_db(request_body)
    logger.info(f'Order Update: {request_body}')
    return


def service_get_order_infos(requests_body: OrderInfoRequest):
    order_info_data, amr_data = get_order_info_from_db(requests_body)
    response = transform_order_info_data_to_api_obj(order_info_data, amr_data)
    logger.debug(f'Get Order Infos: {response}')
    return response


def service_reset_order_database():
    reset_database()
    return


def service_get_item_sku_info(request_body: OrderInfoRequest):
    item_sku_infos = get_item_sku_info(request_body)
    response = transform_item_sku_info_to_api_obj(item_sku_infos)
    return response


def service_set_item_sku_info(request_body: SetSKURequest):
    set_sku_id_in_db(request_body)
    return


def service_get_last_order_status(request_body: OrderInfoRequest):
    order_status = get_order_state_info_from_db(request_body)
    response = transform_order_status_to_api_obj(order_status)
    if len(response) == 0:
        logger.info('Error in last order status:', request_body)
    return response


def service_get_locations_for_order(request_body: StationInfoRequest):
    stations = get_station_ids_for_order_from_db(request_body)
    response = StationIdResponse(pickupStationId=stations[0], dropoffStationId=stations[1])
    return response


def service_set_reposition_order(request_body: RepositionOrder):
    order_state = transform_reposition_order(request_body)
    add_order_state_to_db(order_state)
    return

