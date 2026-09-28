import json
import os

import requests

from api.client_api_models import NewAMRRequest, NewAMRSystemRequest
from api.serialization import serialize_json


def add_amr_basedatamanagement_api(request_body: NewAMRRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "new-amr", data=data, timeout=(10, None))


def add_amr_systemdatamanagement_api(request_body: NewAMRSystemRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "new-amr", data=data, timeout=(10, None))


def reset_order_management():
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "reset", data={}, timeout=(10, None))


def reset_system_state_management():
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "reset", data={}, timeout=(10, None))


def reset_dispatching():
    return requests.post(os.environ['TASKASSIGNMENT_URL'] + "reset", data={}, timeout=(10, None))


def reset_base_data_management():
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "reset", data={}, timeout=(10, None))
