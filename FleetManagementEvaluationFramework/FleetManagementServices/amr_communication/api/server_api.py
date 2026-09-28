from datetime import datetime
import api.api_config

from api.api_config import app, mqtt_send_planned_order_to_amr
from api.client_api_models import StateUpdateVDABodyHeader
from api.server_api_models import OrderAMRRequest, SimulationRunUntilOrderRequest, HeaderIdRequest, \
    NextSimulationStepResponse
from data.enums import BlockingType
from data.models import Order, Node, NodePosition, Action, ActionParameter, Edge
from logic.services import service_send_planned_order_to_amr
import config.config_file
from logic.transformation_functions import transform_amr_state_vda_to_set_amr_state_request


######################
# Rest-API Endpoints #
######################
@app.post("/send-planned-order-to-amr")
async def send_planned_order_to_amr_request(request_body: OrderAMRRequest):
    return service_send_planned_order_to_amr(request_body)


@app.post("/run-simulation-until-order")
async def set_parameter_run_simulation_until_order(request_body: SimulationRunUntilOrderRequest):
    api.api_config.RUN_SIMULATION_UNTIL_ORDER = request_body.orderId
    return


@app.put("/last-header-id-simulation-step")
async def set_last_header_id_simulation_step(request_body: HeaderIdRequest):
    config.config_file.LAST_HEADER_SIMULATION_STEP = request_body.headerId
    return


@app.post("/next-simulation-step")
async def check_for_execution_next_simulation_step():
    if config.config_file.LAST_HEADER_SIMULATION_STEP is not None:
        if config.config_file.LAST_PROCESSED_HEADER >= config.config_file.LAST_HEADER_SIMULATION_STEP:
            next_simulation_step_response = NextSimulationStepResponse(nextSimulationStep=True)
            config.config_file.LAST_HEADER_SIMULATION_STEP = None
        else:
            next_simulation_step_response = NextSimulationStepResponse(nextSimulationStep=False)
    else:
        next_simulation_step_response = NextSimulationStepResponse(nextSimulationStep=True)
    return next_simulation_step_response


@app.put("/state-update")
async def set_state_update_via_api_call(request_body: StateUpdateVDABodyHeader):
    amr_state_to_process = transform_amr_state_vda_to_set_amr_state_request(request_body)
    res = api.api_config.get_state_update_from_amr(amr_state_to_process, request_body.headerId)
    return res


@app.post("/order-request")
async def request_orders_for_amr():
    return api.api_config.request_orders_for_amr()


# Only for testing mqtt
@app.post("/test_mqtt_order")
async def test_mqtt_order():
    order = Order(orderId='TestOrder1', orderUpdateId=0,
                  nodes=[Node(nodeId='A', sequenceId=0, released=True, nodePosition=NodePosition(x=0, y=0, mapId='map1'),
                              actions=[]),
                         Node(nodeId='B', sequenceId=0, released=True, nodePosition=NodePosition(x=5, y=0, mapId='map1'),
                              actions=[Action(actionId='Test1', actionType='PickUp', blockingType=BlockingType.HARD,
                                              actionParameters=[ActionParameter(key='Duration', value=60)])])],
                  edges=[Edge(edgeId='AB', sequenceId=0, released=True, startNodeId='A', endNodeId='B',
                              maxSpeed=1, length=5, actions=[])])
    amr_id = '1'
    time = datetime.now()
    mqtt_send_planned_order_to_amr(order, amr_id, time)

