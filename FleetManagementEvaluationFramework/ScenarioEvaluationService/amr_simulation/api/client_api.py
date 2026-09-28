import json
import os
import requests

from api.client_api_models import AMRBaseDataRequest, HeaderIdRequest
from api.serialization import serialize_json
from api.server_api_models import StateUpdateVDABodyHeader
from data.models import NodeInfoRequest, NewOrderInfo


def get_nodes_info(node_ids: NodeInfoRequest):
    data = json.dumps(
        node_ids.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(str(os.getenv('PATHPLANNING_URL')) + "nodes-info", data=data, timeout=(10, None))


def get_amr_data_base(amr_ids: AMRBaseDataRequest):
    data = json.dumps(
        amr_ids.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(str(os.getenv('BASEDATAMANAGEMENT_URL')) + "base-data", data=data, timeout=(10, None))


def send_order_to_order_management(order_info: NewOrderInfo):
    data = json.dumps(
        order_info.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(str(os.getenv('ORDERMANAGEMENT_URL')) + "new-order", data=data, timeout=(10, None))


def send_last_header_id_simulation_step_to_amr_communication(request_body: HeaderIdRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(str(os.getenv('AMRCOMMUNICATION_URL')) + "last-header-id-simulation-step", data=data,
                        timeout=(10, None))


def send_state_update_to_amr_communication(request_body: StateUpdateVDABodyHeader):
    headers = {'content-type': 'application/json'}
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(str(os.getenv('AMRCOMMUNICATION_URL')) + "state-update", headers=headers, data=data,
                        timeout=(10,  None))


def request_orders_for_amr():
    headers = {'content-type': 'application/json'}
    return requests.post(str(os.getenv('AMRCOMMUNICATION_URL')) + "order-request", headers=headers, data={},
                         timeout=(10, None))
