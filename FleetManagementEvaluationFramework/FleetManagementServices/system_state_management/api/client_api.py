import json
import os
import requests

from api.client_api_models import Station, RequestOrderAMR, RoutingForOrdersRequest, RoutingStartGoalRequest, \
    DeleteOrderRequest, RoutingRequestObject, ReleaseOrderRequest, LayoutInformation, \
    ReservedNodeRequest
from api.serialization import serialize_json
from api.server_api_models import PlannedOrder
from data.models import NodeInfoRequest


###########################################
# SEND-PLANNED-ORDER-TO-AMR-COMMUNICATION #
###########################################

def send_planned_order_to_amr_communication(planned_order_outgoing_request_body: PlannedOrder):
    data = json.dumps(
        planned_order_outgoing_request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['AMRCOMMUNICATION_URL'] + "send-planned-order-to-amr", data=data, timeout=(10, None))


def request_routes_for_amrs(route_for_amrs_request_body: RoutingForOrdersRequest):
    data = json.dumps(
        route_for_amrs_request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "routing-for-amrs", data=data, timeout=(10, None))


def get_nodes_info(node_ids: NodeInfoRequest):
    data = json.dumps(
        node_ids.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "nodes-info", data=data, timeout=(10, None))


def get_system_time():
    return requests.get(os.environ['AMRSIMULATION_URL'] + "system-time", data={}, timeout=(10, None))


def set_amr_location_in_storage_management(amr_location: Station):
    data = json.dumps(
        amr_location.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "locations", headers=headers, data=data, timeout=(10, None))


def request_order_for_amr(amr: RequestOrderAMR):
    data = json.dumps(
        amr.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['TASKASSIGNMENT_URL'] + "order-from-order-pool", data=data, timeout=(10, None))


def request_routes_for_instant_orders(request_body: RoutingStartGoalRequest):  # delete maybe
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "/routing-for-instant-orders", data=data, timeout=(10, None))


def delete_order_from_order_pool(request_body: DeleteOrderRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.delete(os.environ['TASKASSIGNMENT_URL'] + "delete-order-from-order-pool", data=data, timeout=(10, None))


def request_routes_for_all_amrs(routing_request: RoutingRequestObject):
    data = json.dumps(
        routing_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "routing-for-all-amrs", data=data, timeout=(10, None))


def release_order_in_order_pool(request_body: ReleaseOrderRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['TASKASSIGNMENT_URL'] + "release-order-in-order-pool", data=data, timeout=(10, None))


def send_tokens_to_central(request_body: ReservedNodeRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['TASKASSIGNMENT_URL'] + "reserved-nodes-central", data=data, timeout=(10, None))
