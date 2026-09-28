import logging
import os
import json
import requests
import config.config_file

from api.client_api_models import (OrderDimensionRequest, PossibleAMRsRequest,
                                   RouteRequest, OrderUpdateRequest, NodeInfoRequest, TravelTimeMatrixRequest,
                                   SystemTimeRequest, StationInfoRequest, AssignedOrderUpdateRequest, RepositionOrder,
                                   TokensEndPositionsRequest, ParkingNodesRequest)
from api.serialization import serialize_json
from data.models import OrderSequenceUpdateRequest


logger = logging.getLogger(config.config_file.LOGGER_NAME)


#####################
# GET-POSSIBLE-AMRS #
#####################
def get_possible_amrs(order_dimension_outgoing_request: OrderDimensionRequest):
    data = json.dumps(
        order_dimension_outgoing_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['BASEDATAMANAGEMENT_URL'] + "possible-amrs", data=data, timeout=(10, None))


################
# GET-ALL-AMRS #
################
def get_all_amrs():
    return requests.get(os.environ['BASEDATAMANAGEMENT_URL'] + "all-amrs", data={}, timeout=(10, None))


################
# GET-AMR-DATA #
################
def get_amr_states(possible_amrs_outgoing_requests: PossibleAMRsRequest):
    data = json.dumps(
        possible_amrs_outgoing_requests.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "amr-state", data=data, timeout=(10, None))


##################
# GET-Node-Infos #
##################
def get_nodes_for_order(node_ids: NodeInfoRequest):
    data = json.dumps(
        node_ids.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "nodes-info", data=data, timeout=(10, None))


####################
# GET-Required-TTM #
####################
def get_travel_time_matrix(travelTimeMatrixRequest: TravelTimeMatrixRequest):
    data = json.dumps(
        travelTimeMatrixRequest.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "travel-time-matrix", data=data, timeout=(10, None))


#######################
# GET-ROUTE-FOR-ORDER #
#######################
def get_route_for_order(route_outgoing_request_body: RouteRequest):
    data = json.dumps(
        route_outgoing_request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['PATHPLANNING_URL'] + "routing-for-order", data=data, timeout=(10, None))


################################################
# SEND-PLANNED-ORDER-TO-SYSTEM-STATE-MANAGEMENT#
################################################

def set_planned_order_in_system_state_management(planned_order_outgoing_request_body: OrderUpdateRequest):
    data = json.dumps(
        planned_order_outgoing_request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    try:
        return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "planned-order", data=data, timeout=(10, None))
    except Exception as e:
        logger.info(f'Set planned order in system state management failed: {e}')
        return None

################################################
# SEND-PLANNED-ORDER-TO-SYSTEM-STATE-MANAGEMENT#
################################################


def update_planned_order_sequence_in_system_state_management(
        planned_order_outgoing_request_body: OrderSequenceUpdateRequest):
    data = json.dumps(
        planned_order_outgoing_request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "update-planned-order-sequence", data=data, timeout=(10, None))


###################
# GET-SYSTEM-TIME #
###################

def get_current_system_time():
    system_time_request_body = SystemTimeRequest(sysTime='*')
    data = json.dumps(
        system_time_request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['SYSTEMSTATEMANAGEMENT_URL'] + "system-time", data=data, timeout=(10, None))


def get_station_infos(request_body: StationInfoRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "stations-info", data=data, timeout=(10, None))


def set_order_update(order_update_outgoing_request: AssignedOrderUpdateRequest):
    data = json.dumps(
        order_update_outgoing_request.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
        )
    return requests.put(os.environ['ORDERMANAGEMENT_URL'] + "order-update", data=data, timeout=(10, None))


def set_reposition_order(reposition_order: RepositionOrder):
    data = json.dumps(
        reposition_order.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.post(os.environ['ORDERMANAGEMENT_URL'] + "set-reposition-order", data=data, timeout=(10, None))


def check_start_and_goal_are_connected(token_end_position: TokensEndPositionsRequest):
    data = json.dumps(
        token_end_position.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "info-graph-connected", data=data, timeout=(10, None))


def get_parking_nodes(request_body: ParkingNodesRequest):
    data = json.dumps(
        request_body.dict(exclude_none=True),
        default=lambda o: serialize_json(o)
    )
    return requests.get(os.environ['PATHPLANNING_URL'] + "parking-nodes", data=data, timeout=(10, None))

