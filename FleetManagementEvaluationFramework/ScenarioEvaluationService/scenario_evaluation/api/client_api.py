import json
import os

import requests

from api.client_api_models import SystemTimeRequest, NewOrderInfo, OrderInfoRequest, \
    MakeSpanRequest, TaskAssignmentStrategy, PathPlanningStrategy, CollisionDetection, \
    WaitingTimeRequest, HeuristicRequest, CBSImprovementRequest, SetParkingNodesRequest, SystemTimeResponse, \
    DurationEdgeRequest, FocalHeuristicRequest, StatisticFileNames
from api.serialization import serialize_json

from data.models import LIFObject, NewAMRRequest, NewAMRSystemRequest, PathPlanningRequest, Layout


def get_system_time():
    system_time_request = SystemTimeRequest(sysTime='*')
    data = json.dumps(
        system_time_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "system-time", data=data)


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


def send_new_order_info(order_info: NewOrderInfo):
    data = json.dumps(
        order_info.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "new-order", data=data)


def get_order_info(order_ids: OrderInfoRequest):
    data = json.dumps(
        order_ids.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['ORDERMANAGEMENT_URL'] + "order-infos", data=data)


def get_make_span_api(request_body: MakeSpanRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['AMRSIMULATION_URL'] + "makespan", data=data)



def set_task_assignment_strategy_api(request_body: TaskAssignmentStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['TASKASSIGNMENT_URL'] + "dispatching-strategy", data=data)


def set_path_planning_strategy_api(request_body: PathPlanningStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "path-planning-strategy", data=data)


def set_collision_detection_api(request_body: CollisionDetection):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['AMRSIMULATION_URL'] + "collision-detection", data=data)


def set_lif_object(request_body: LIFObject):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "lif", data=data)


def reset_amr_simulation():
    return requests.post(os.environ['AMRSIMULATION_URL'] + "reset", data={})


def reset_system_state_management():
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "reset", data={})


def reset_base_data_management():
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "reset", data={})


def reset_task_assignment():
    return requests.post(os.environ['TASKASSIGNMENT_URL'] + "reset", data={})


def reset_path_planning_time():
    return requests.post(os.environ['PATHPLANNING_URL'] + "reset", data={})


def reset_time_measurement():
    return requests.post(os.environ['PATHPLANNING_URL'] + "reset-time", data={})


def reset_order_management():
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "reset", data={})


def add_amr_basedatamanagement_api(request_body: NewAMRRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "new-amr", data=data)


def add_amr_systemdatamanagement_api(request_body: NewAMRSystemRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "new-amr", data=data)


def add_amr_simulation_api(request_body: NewAMRSystemRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['AMRSIMULATION_URL'] + "new-amr", headers=headers, data=data)


def send_new_order_info_to_simulation(order_info: NewOrderInfo):
    data = json.dumps(
        order_info.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['AMRSIMULATION_URL'] + "new-order", headers=headers, data=data)


def run_simulation_step():
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['AMRSIMULATION_URL'] + "step", headers=headers, data={})


def check_execution_simulation_step():
    headers = {'content-type': 'application/json'}
    return requests.post(os.environ['AMRCOMMUNICATION_URL'] + "next-simulation-step", headers=headers, data={})


def set_waiting_time_in_simulation(request_body: WaitingTimeRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['AMRSIMULATION_URL'] + "waiting-time-node", data=data)


def set_duration_edge_in_path_planning(request_body: DurationEdgeRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "duration-edge", data=data)


def set_heuristic_for_a_star(request_body: HeuristicRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "heuristic", data=data)


def set_cbs_improvement_cost_function(request_body: CBSImprovementRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "cbs-improvement", data=data)


def set_dispatching_strategy_in_system_state_management(request_body: TaskAssignmentStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "dispatching-strategy", data=data)


def set_dispatching_strategy_in_amr_simulation(request_body: TaskAssignmentStrategy):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['AMRSIMULATION_URL'] + "dispatching-strategy", data=data)


def get_statistic_time_parameter_from_path_planning():
    return requests.get(os.environ['PATHPLANNING_URL'] + "statistic-time-data", data={}, timeout=5)


def set_parking_nodes_for_layout(request_body: SetParkingNodesRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "parking-nodes", data=data)


def get_statistic_information_from_system_state_management():
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "path-planning-information", data={})


def get_statistic_information_from_amr_simulation():
    return requests.get(os.environ['AMRSIMULATION_URL'] + "driving-times", data={})


def set_focal_heuristic(request_body: FocalHeuristicRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['PATHPLANNING_URL'] + "focal-heuristic", data=data)


def set_name_of_statistic_files(request_body: StatisticFileNames):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.put(os.environ['AMRSIMULATION_URL'] + "statistic-files", data=data)


def solve_mapf_instances(request_body: PathPlanningRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "solve-path-planning-request", data=data)


def visualize_full_mapd_scenario(request_body: Layout):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['AMRSIMULATION_URL'] + "visualization-scenario", data=data)
