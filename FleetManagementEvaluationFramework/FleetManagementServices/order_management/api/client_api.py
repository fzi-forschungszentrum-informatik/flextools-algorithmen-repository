import json
import requests
import os

from api.client_api_models import StorageLocationRequest, NewItemRequest, SkusStoreRequestBody
from api.serialization import serialize_json
from data.models import NewOrderInfo


#######################
# START-TO-PLAN-ORDER #
#######################
def start_to_plan_order(order_info_outgoing_request: NewOrderInfo):
    data = json.dumps(
        order_info_outgoing_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['TASKASSIGNMENT_URL'] + "new-order", data=data, timeout=(10, None))


def reset_database_api_call():
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "reset", data={}, timeout=(10, None))


def get_free_storage_location(request_body: StorageLocationRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['AUTONOMOUS_DECISION_MAKING_URL'] + "slap", headers=headers, data=data,
                         timeout=(10, None))


def get_items_from_storage_location_tracking():
    headers = {'content-type': 'application/json'}
    return requests.get(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "items", headers=headers, data={},
                        timeout=(10, None))


def set_new_item_in_storage_location_tracking(request_body: NewItemRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "items", headers=headers, data=data,
                         timeout=(10, None))


def store_skus(request_body: SkusStoreRequestBody):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skus/store", headers=headers, data=data,
                         timeout=(10, None))
