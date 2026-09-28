import json
import os
import requests

from api.client_api_models import SetAMRConnectionStateRequest, OrderUpdateRequest, SetAMRStateRequest, \
    OrderFinishRequest, SystemTimeRequest, SkusRetrieveRequestBody, \
    SkusStoreRequestBody, OrderInfoRequest, StationInfoRequest
from api.serialization import serialize_json


def set_amr_connection_state(set_amr_connection_state_request: SetAMRConnectionStateRequest):
    data = json.dumps(
        set_amr_connection_state_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-connection-state", data=data, timeout=(10, None))


def set_amr_state_with_response(set_amr_state_request: SetAMRStateRequest):
    data = json.dumps(
        set_amr_state_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-state-with-response", data=data,
                        timeout=(10, None))


def set_order_update(order_update_outgoing_request: OrderUpdateRequest):
    data = json.dumps(
        order_update_outgoing_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
        )
    return requests.put(os.environ['ORDERMANAGEMENT_URL'] + "order-update", data=data, timeout=(10,None))


def delete_finished_order_from_planned_order_list(order_info_request: OrderFinishRequest):
    data = json.dumps(
        order_info_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.delete(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "finished-order", data=data, timeout=(10, None))


def set_system_time(system_time_request: SystemTimeRequest):
    data = json.dumps(
        system_time_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "system-time", data=data, timeout=(10, None))


def retrieve_skus(request_body: SkusRetrieveRequestBody):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skus/retrieve", headers=headers, data=data,
                         timeout=(10, None))


def store_skus(request_body: SkusStoreRequestBody):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skus/store", headers=headers, data=data,
                         timeout=(10, None))


def get_item_sku_infos(request_body: OrderInfoRequest):
    data = json.dumps(
        request_body.dict(exclude_none=False),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['ORDERMANAGEMENT_URL'] + "item-sku-info", data=data, timeout=(10, None))


def get_order_status(request_body: OrderInfoRequest):
    data = json.dumps(
        request_body.dict(exclude_none=False),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['ORDERMANAGEMENT_URL'] + "last-order-status", data=data, timeout=(10, None))


def get_goal_station_for_order(request_body: StationInfoRequest):
    data = json.dumps(
        request_body.dict(exclude_none=False),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['ORDERMANAGEMENT_URL'] + "stations-for-order", data=data, timeout=(10, None))


def set_amr_state(set_amr_state_request: SetAMRStateRequest):
    data = json.dumps(
        set_amr_state_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-state", data=data, timeout=(10, None))


def request_orders_for_amrs():
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "order-request", data={}, timeout=(10, None))

