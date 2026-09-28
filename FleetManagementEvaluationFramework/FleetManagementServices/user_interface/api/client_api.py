import json

import requests
import os

from data.models import NewOrderInfo, OrderInfoRequest, MapInfoRequest, AMRRequests, SystemTimeRequest, \
    NewAMRRequest, NewAMRSystemRequest, AMRPauseRequest, \
    MakeSpanRequest, DispatchingStrategy, PathPlanningStrategy, CollisionDetection, \
    AMRPathRequest, AMRPORequest, SystemTimeResponse, LIFObject, Layout

from api.serialization import serialize_json


def send_new_order_info(order_info: NewOrderInfo):
    data = json.dumps(
        order_info.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "new-order", data=data)


def send_new_order_info_to_simulation(order_info: NewOrderInfo):
    data = json.dumps(
        order_info.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['AMRSIMULATION_URL'] + "new-order", headers=headers, data=data)


def get_order_info(order_ids: OrderInfoRequest):
    data = json.dumps(
        order_ids.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['ORDERMANAGEMENT_URL'] + "order-infos", data=data)


def get_next_order_id_simulation():
    return requests.get(os.environ['AMRSIMULATION_URL'] + "next-order", data={})


def get_map_info(map_info: MapInfoRequest):
    data = json.dumps(
        map_info.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "map-info", data=data, timeout=10)


def get_amr_data(amrs: AMRRequests):
    data = json.dumps(
        amrs.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-data", data=data)


def get_system_time():
    system_time_request = SystemTimeRequest(sysTime='*')
    data = json.dumps(
        system_time_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "system-time", data=data, timeout=10)


def add_amr_basedatamanagement_api(request_body: NewAMRRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "new-amr", data=data, timeout=10)


def add_amr_systemdatamanagement_api(request_body: NewAMRSystemRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "new-amr", data=data, timeout=10)


def add_amr_simulation_api(request_body: NewAMRSystemRequest):
    try:
        data = json.dumps(
            request_body.dict(exclude_none=True),
            default=lambda o: serialize_json(o)
        )
        headers = {'content-type': 'application/json'}
        return requests.post(os.environ['AMRSIMULATION_URL'] + "new-amr", headers=headers, data=data)
    except:
        # Do nothing, because no simulation exists
        return None


def set_amr_to_pause_system_api(request_body: AMRPauseRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "pause-amr", data=data, timeout=10)


def set_amr_to_pause_sim_api(request_body: AMRPauseRequest):
    try:
        data = json.dumps(
            request_body.dict(exclude_none=True),
            default=lambda o: serialize_json(o)
        )
        return requests.post(os.environ['AMRSIMULATION_URL'] + "pause-amr", data=data, timeout=10)
    except Exception as e:
        # Do nothing, because no simulation exists
        return None


def get_make_span_api(request_body: MakeSpanRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['AMRSIMULATION_URL'] + "makespan", data=data)


def set_dispatching_strategy_api(request_body: DispatchingStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['TASKASSIGNMENT_URL'] + "dispatching-strategy", data=data, timeout=10)


def set_path_planning_strategy_api(request_body: PathPlanningStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "path-planning-strategy", data=data, timeout=10)


def set_collision_detection_api(request_body: CollisionDetection):
    try:
        data = json.dumps(
            request_body.dict(exclude_none=True),
            default=lambda o: serialize_json(o)
        )
        return requests.put(os.environ['AMRSIMULATION_URL'] + "collision-detection", data=data, timeout=10)
    except Exception as e:
        # Do nothing, because no simulation exists
        return None


def reset_order_management():
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "reset", data={}, timeout=10)


def reset_amr_simulation():
    try:
        return requests.post(os.environ['AMRSIMULATION_URL'] + "reset", data={}, timeout=10)
    except Exception as e:
        # Do nothing, because no simulation exists
        return None


def reset_system_state_management():
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "reset", data={}, timeout=10)


def reset_base_data_management():
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "reset", data={}, timeout=10)


def reset_task_assignment():
    return requests.post(os.environ['TASKASSIGNMENT_URL'] + "reset", data={}, timeout=10)


def reset_travel_time():
    return requests.post(os.environ['PATHPLANNING_URL'] + "reset", data={}, timeout=10)


def reset_cpu_time_measurement():
    return requests.post(os.environ['PATHPLANNING_URL'] + "reset-time", data={}, timeout=10)


def get_items_from_storage_location_tracking():
    headers = {'content-type': 'application/json'}
    return requests.get(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "items", headers=headers, data={}, timeout=10)


def remove_item_from_storage_location_tracking(item_id: str):
    headers = {'content-type': 'application/json'}
    parameter = {'id': item_id}
    return requests.delete(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "items", headers=headers, params=parameter,
                           data={}, timeout=10)


def get_skus_from_storage_location_tracking():
    headers = {'content-type': 'application/json'}
    return requests.get(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skus", headers=headers, data={}, timeout=10)


def remove_skus_from_storage_location_tracking(sku_id: str):
    parameter = {'skuId': sku_id}
    headers = {'content-type': 'application/json'}
    return requests.delete(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skus", headers=headers, params=parameter,
                           data={}, timeout=10)


def get_records_from_storage_location_tracking():
    headers = {'content-type': 'application/json'}
    return requests.get(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skuRecords", headers=headers, data={},
                        timeout=10)


def remove_records_from_storage_location_tracking(record_id: str):
    parameter = {'id': record_id}
    headers = {'content-type': 'application/json'}
    return requests.delete(os.environ['STORAGE_LOCATION_TRACKING_URL'] + "skuRecords", headers=headers,
                           params=parameter, data={}, timeout=10)


def get_computational_time():
    return requests.get(os.environ['PATHPLANNING_URL'] + "computational-time", data={}, timeout=10)


def set_lif_object(request_body: LIFObject):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "lif", data=data)


def get_amr_path_info(request_body: AMRPathRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-path", data=data, timeout=10)


def get_amr_planned_orders(request_body: AMRPORequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-planned-orders", data=data, timeout=10)


def get_current_map_id():
    return requests.get(os.environ['PATHPLANNING_URL'] + "map-id", data={}, timeout=10)


def run_simulation_step():
    headers = {'content-type': 'application/json'}
    try:
        return requests.post(os.environ['AMRSIMULATION_URL'] + "step", headers=headers, data={})
    except:
        return None


def set_dispatching_strategy_in_system_state_management(request_body: DispatchingStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "dispatching-strategy", data=data, timeout=10)


def set_dispatching_strategy_in_amr_simulation(request_body: DispatchingStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['AMRSIMULATION_URL'] + "dispatching-strategy", data=data)


def visualize_full_mapd_scenario(request_body: Layout):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['AMRSIMULATION_URL'] + "visualization-scenario", data=data)


def set_system_time_from_extern_in_system_state_management(system_time_request: SystemTimeResponse):
    data = json.dumps(
        system_time_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "system-time-extern", data=data)


def set_system_time_from_extern_in_amr_simulation(system_time_request: SystemTimeResponse):
    data = json.dumps(
        system_time_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['AMRSIMULATION_URL'] + "system-time", data=data)
