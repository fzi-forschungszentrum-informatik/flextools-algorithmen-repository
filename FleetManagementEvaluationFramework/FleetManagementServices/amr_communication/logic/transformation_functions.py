from api.client_api_models import SetAMRStateRequest, \
    SetAMRConnectionStateRequest, StateUpdateVDABodyHeader, ConnectionStateVDABodyHeader
from data.enums import ConnectionState
from logic.general_functions import transform_str_to_datetime


def transform_amr_state_vda_to_set_amr_state_request(request_body: StateUpdateVDABodyHeader) -> SetAMRStateRequest:
    """
    :param request_body: mqtt message
    :return: AMRState object for in the fleet management software system
    """
    if 'paused' not in request_body:
        request_body.paused = False
    if 'distanceSinceLastNode' not in request_body:
        request_body.distanceSinceLastNode = 0

    amr_state_request = SetAMRStateRequest(timestamp=transform_str_to_datetime(request_body.timestamp),
                                           amrId=request_body.serialNumber,
                                           connectionState=ConnectionState.ONLINE,
                                           orderId=request_body.orderId,
                                           orderUpdateId=request_body.orderUpdateId,
                                           lastNodeId=request_body.lastNodeId,
                                           lastNodeSequenceId=request_body.lastNodeSequenceId,
                                           driving=request_body.driving,
                                           paused=request_body.paused,
                                           distanceSinceLastNode=request_body.distanceSinceLastNode,
                                           operatingMode=request_body.operatingMode,
                                           amrPosition=request_body.agvPosition,
                                           velocity=request_body.velocity,
                                           loads=request_body.loads,
                                           batteryState=request_body.batteryState,
                                           nodeStates=request_body.nodeStates,
                                           edgeStates=request_body.edgeStates,
                                           actionStates=request_body.actionStates
                                           )
    return amr_state_request


def transform_amr_connection_vda_to_set_amr_connection_state_request(request_body: ConnectionStateVDABodyHeader)\
        -> SetAMRConnectionStateRequest:
    """
    :param request_body: Mqtt message
    :return:  ConnectionState object for in the fleet management software system
    """
    amr_connection_state_request = SetAMRConnectionStateRequest(timestamp=transform_str_to_datetime(request_body.timestamp),
                                                                amrId=request_body.serialNumber,
                                                                connectionState=request_body.connectionState)
    return amr_connection_state_request


