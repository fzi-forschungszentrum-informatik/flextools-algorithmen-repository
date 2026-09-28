from api.api_config import app
from api.server_api_models import GetAMRStateRequest, SetAMRConnectionStateRequest, \
    AMRRequest, PlannedOrderIncoming, OrderFinishRequest, SystemTimeResponse, \
    SystemTimeRequest, AMRPauseRequest, PathRequest, AMRPathRequest, AMRPORequest, \
    InstantOrders, DispatchingStrategy

from data.models import PlannedOrderSequenceIncoming, NewAMRSystemRequest, AMRState
from logic.services import service_get_amr_state, service_set_amr_connection_state, \
    service_set_planned_order_in_queue, service_get_amr_data, service_remove_finished_order_from_queue, \
    service_update_planned_order_sequence, service_set_system_time, service_get_system_time, service_add_new_amr, \
    service_set_amr_to_pause, service_reset_system_state_management, service_set_system_state_file_new, \
    service_get_amr_path, service_get_amr_planned_orders, \
    service_get_instant_order_for_execution, service_set_amr_state, \
    service_request_orders, service_set_amr_state_with_response, service_set_dispatching_strategy, \
    service_set_system_time_from_extern, service_get_path_planning_information


######################
# Rest-API Endpoints #
######################
@app.get("/amr-state")
async def get_amr_state_request(request_body: GetAMRStateRequest):
    return service_get_amr_state(request_body)


@app.put("/amr-state-with-response")
async def set_amr_state_with_response(request_body: AMRState):
    return service_set_amr_state_with_response(request_body)


@app.put("/amr-connection-state")
async def set_amr_connection_state_request(request_body: SetAMRConnectionStateRequest):
    return service_set_amr_connection_state(request_body)


@app.post("/planned-order")
async def set_planned_order_request(request_body: PlannedOrderIncoming):
    return service_set_planned_order_in_queue(request_body)


@app.post("/update-planned-order-sequence")
async def set_planned_order_request(request_body: PlannedOrderSequenceIncoming):
    return service_update_planned_order_sequence(request_body)


@app.get("/amr-data")
async def get_amr_data_request(request_body: AMRRequest):
    return service_get_amr_data(request_body)


@app.delete("/finished-order")
async def remove_finished_order_from_queue(request_body: OrderFinishRequest):
    return service_remove_finished_order_from_queue(request_body)


@app.put("/system-time")
async def set_system_time_request(request_body: SystemTimeResponse):
    return service_set_system_time(request_body)


@app.put("/system-time-extern")
async def set_system_time_request(request_body: SystemTimeResponse):
    return service_set_system_time_from_extern(request_body)


@app.get("/system-time")
async def get_system_time_request(request_body: SystemTimeRequest):
    return service_get_system_time(request_body)


@app.post("/new-amr")
async def add_new_amr(request_body: NewAMRSystemRequest):
    return service_add_new_amr(request_body)


@app.post("/pause-amr")
async def set_amr_to_pause(request_body: AMRPauseRequest):
    return service_set_amr_to_pause(request_body)


@app.post("/reset")
async def reset_system_state_management():
    return service_reset_system_state_management()


@app.get('/health')
async def health():
    pass


@app.put("/system-state-file")
async def set_system_state_file_new(request_body: PathRequest):
    return service_set_system_state_file_new(request_body)


@app.get("/amr-path")
async def get_amr_path_request(request_body: AMRPathRequest):
    return service_get_amr_path(request_body)


@app.get("/amr-planned-orders")
async def get_amr_planned_orders_request(request_body: AMRPORequest):
    return service_get_amr_planned_orders(request_body)


@app.post("/instant-orders")
async def get_instant_order_for_execution(request_body: InstantOrders):
    return service_get_instant_order_for_execution(request_body)


@app.put("/amr-state")
async def set_amr_state_request_without_response(request_body: AMRState):
    return service_set_amr_state(request_body)


@app.post("/order-request")
async def request_orders():
    return service_request_orders()


@app.put("/dispatching-strategy")
async def set_dispatching_strategy_request(request_body: DispatchingStrategy):
    return service_set_dispatching_strategy(request_body)


@app.get("/path-planning-information")
async def get_path_planning_information():
    return service_get_path_planning_information()
