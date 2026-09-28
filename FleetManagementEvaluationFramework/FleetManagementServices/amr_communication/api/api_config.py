import json
import os

from contextlib import asynccontextmanager
from typing import Any
from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mqtt import MQTTConfig, FastMQTT
from gmqtt import Client as MQTTClient
import config.config_file

from api.client_api import set_amr_connection_state, set_order_update, \
    delete_finished_order_from_planned_order_list, set_system_time, \
    retrieve_skus, store_skus, get_item_sku_infos, \
    get_order_status, get_goal_station_for_order, set_amr_state, \
    request_orders_for_amrs
from api.client_api_models import SetAMRStateRequest, OrderUpdateRequest, \
    OrderFinishRequest, SystemTimeRequest, SkusRetrieveRequestBody, \
    SkusStoreRequestBody, OrderInfoRequest, StationInfoRequest, \
    StateUpdateVDABodyHeader, ConnectionStateVDABodyHeader, OrderUpdateVDABodyHeader
from api.serialization import serialize_json

from config.config_file import HOST, MQTT_BROKER_PORT, PORT, HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER, \
    HOST_ADDRESS_ORDERMANAGEMENT_DOCKER, HOST_ADDRESS_AMRCOMMUNICATION_DOCKER, HOST_ADDRESS_MQTT_BROKER_DOCKER, \
    HOST_ADDRESS_SYSTEMSTATEMANAGEMENT, HOST_ADDRESS_ORDERMANAGEMENT, HOST_ADDRESS_AMRCOMMUNICATION, \
    HOST_ADDRESS_MQTT_BROKER, MQTT_RECONNECT_RETRIES, HOST_ADDRESS_AMRSIMULATION_DOCKER, HOST_ADDRESS_AMRSIMULATION, \
    HOST_ADDRESS_STATISTICS_EVALUATION_DOCKER, HOST_ADDRESS_STATISTICS_EVALUATION, \
    HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER, HOST_ADDRESS_STORAGE_LOCATION_TRACKING
from data.enums import OrderStatus
from data.models import Order
from logic.amr_state_update_functions import (determine_order_status_from_amr_state,
                                              process_next_order_in_queue)
from logic.general_functions import env_to_bool
from logic.transformation_functions import transform_amr_state_vda_to_set_amr_state_request, \
    transform_amr_connection_vda_to_set_amr_connection_state_request

###################################
# Host and Network Configurations #
###################################
host = HOST
port = PORT

HEADER_ID = 0
RUN_SIMULATION_UNTIL_ORDER = None
LAST_PROCESSED_HEADER = 0

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def set_service_urls():  # in the case the environment variables are not set by gitlab-ci.yml file
    ENV_DOCKER = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if 'MQTT_ORDER_TOPIC' not in os.environ:
        os.environ['MQTT_ORDER_TOPIC'] = config.config_file.MQTT_ORDER_TOPIC
    if 'MQTT_CONNECTION_TOPIC' not in os.environ:
        os.environ['MQTT_CONNECTION_TOPIC'] = config.config_file.MQTT_CONNECTION_TOPIC
    if 'MQTT_STATE_TOPIC' not in os.environ:
        os.environ['MQTT_STATE_TOPIC'] = config.config_file.MQTT_STATE_TOPIC
    if 'AMR_SIMULATION_ACTIVE' in os.environ:
        config.config_file.AMR_SIMULATION_ACTIVE = env_to_bool(os.environ['AMR_SIMULATION_ACTIVE'])
    if ENV_DOCKER == "True":
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT_DOCKER
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION_DOCKER
        if 'MQTTBROKER_HOST' not in os.environ:
            os.environ['MQTTBROKER_HOST'] = HOST_ADDRESS_MQTT_BROKER_DOCKER
        if 'MQTTBROKER_PORT' not in os.environ:
            os.environ['MQTTBROKER_PORT'] = MQTT_BROKER_PORT
        if 'AMRSIMULATION_URL' not in os.environ:
            os.environ['AMRSIMULATION_URL'] = HOST_ADDRESS_AMRSIMULATION_DOCKER
        if 'STATISTIC_EVALUATION_URL' not in os.environ:
            os.environ['STATISTIC_EVALUATION_URL'] = HOST_ADDRESS_STATISTICS_EVALUATION_DOCKER
        if 'STORAGE_LOCATION_TRACKING_URL' not in os.environ:
            os.environ['STORAGE_LOCATION_TRACKING_URL'] = HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER
        # Set default parameters from docker .env file
        config.config_file.STORAGE_LOCATION_TRACKING = env_to_bool(os.environ['STORAGE_LOCATION_TRACKING'])
        if 'USE_MQTT' in os.environ:
            config.config_file.USE_MQTT = env_to_bool(os.environ['USE_MQTT'])
    else:
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION
        if 'MQTTBROKER_HOST' not in os.environ:
            os.environ['MQTTBROKER_HOST'] = HOST_ADDRESS_MQTT_BROKER
        if 'MQTTBROKER_PORT' not in os.environ:
            os.environ['MQTTBROKER_PORT'] = MQTT_BROKER_PORT
        if 'AMRSIMULATION_URL' not in os.environ:
            os.environ['AMRSIMULATION_URL'] = HOST_ADDRESS_AMRSIMULATION
        if 'STATISTIC_EVALUATION_URL' not in os.environ:
            os.environ['STATISTIC_EVALUATION_URL'] = HOST_ADDRESS_STATISTICS_EVALUATION
        if 'STORAGE_LOCATION_TRACKING_URL' not in os.environ:
            os.environ['STORAGE_LOCATION_TRACKING_URL'] = HOST_ADDRESS_STORAGE_LOCATION_TRACKING


#########################
# FastAPI Configuration #
#########################
set_service_urls()

if config.config_file.USE_MQTT is False:
    keepalive_value = 0
else:
    keepalive_value = 90

mqtt_config = MQTTConfig(
    host=os.environ['MQTTBROKER_HOST'],
    port=int(os.environ['MQTTBROKER_PORT']),
    reconnect_retries=MQTT_RECONNECT_RETRIES,
    keepalive=keepalive_value
)
fast_mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager  # setup MQTT connection for lifespan of app
async def lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


########
# MQTT #
########
@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    client.subscribe("/mqtt")  # subscribing mqtt topic
    logger.info(f'Connected: {client}, {flags}, {rc}, {properties}')


@fast_mqtt.subscribe(os.environ['MQTT_CONNECTION_TOPIC'])
async def message_to_topic(client, topic, payload, qos, properties):
    logger.debug(f"Received message to specific topic: {topic}, {payload.decode()}, {qos}, {properties}")
    try:
        request_body = ConnectionStateVDABodyHeader.parse_obj(json.loads(payload.decode()))
    except Exception as e:
        logger.exception(f'Incoming payload could not be parsed into SetAMRConnectionStateRequest object.'
                         f' --> Message discarded: {e}')
        raise Exception(f'Incoming payload could not be parsed into SetAMRConnectionStateRequest object.'
                        f' --> Message discarded {e}')
    else:
        connection_state_to_process = transform_amr_connection_vda_to_set_amr_connection_state_request(request_body)
        set_amr_connection_state(connection_state_to_process)


@fast_mqtt.subscribe(os.environ['MQTT_STATE_TOPIC'])
async def message_to_topic(client, topic, payload, qos, properties):
    logger.debug(f"Received message to specific topic: {topic}, {payload.decode()}, {qos}, {properties}")
    try:
        request_body = StateUpdateVDABodyHeader.parse_obj(json.loads(payload.decode()))
    except Exception as e:
        logger.exception(f'Incoming payload could not be parsed into StateUpdateVDA object.'
                         f' --> Message discarded: {e}')
        raise Exception(f'Incoming payload could not be parsed into StateUpdateVDA object.'
                        f' --> Message discarded {e}')
    else:
        amr_state_to_process = transform_amr_state_vda_to_set_amr_state_request(request_body)
        get_state_update_from_amr(amr_state_to_process, request_body.headerId)


def mqtt_send_planned_order_to_amr(request_body: Order, amr_id: str, timestamp: datetime):
    """
    :param request_body: order object
    :param amr_id: amr id
    :param timestamp: start time of the order
    :return: send order according vda to simulation or real robots
    """
    logger.info(f'Send planned order {request_body.orderId} to amr {amr_id}')
    timestamp = timestamp.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    order_update_obj = OrderUpdateVDABodyHeader(headerId=HEADER_ID, timestamp=timestamp,
                                                version='v2', manufacturer='fzi', serialNumber=amr_id,
                                                orderId=request_body.orderId,
                                                orderUpdateId=request_body.orderUpdateId,
                                                nodes=request_body.nodes,
                                                edges=request_body.edges)
    if config.config_file.USE_MQTT is True:
        payload = json.dumps(
            order_update_obj.dict(exclude_none=True),
            default=lambda o: serialize_json(o)
        )
        if os.environ['MQTT_ORDER_TOPIC'] == "":
            fast_mqtt.publish(f"flextools/v2/fzi/{amr_id}/order", payload)  # publishing mqtt topic
        else:
            fast_mqtt.publish(os.environ['MQTT_ORDER_TOPIC'], payload)
        return {"result": True, "message": "Published"}
    else:
        return


def get_state_update_from_amr(request_body: SetAMRStateRequest, header_id: int):
    """
    :param request_body: SetAMRStateRequest
    :param header_id: header id of the state message from the amr
    :return: -
            1. Determine order status from the current processed order
            2. Determine the order status from this order last time
            3. If order status first time finish:
                a. delete order from planned order list
                b. update order management database
            4. Update order management database, also if order not yet finish
            5. Set system time update
            6. Set amr state
            7. Update item in storage location tracking system if activated
            8. Request next orders, if last state update in a simulation step, compared with the header id
    """
    logger.debug(f'Get system state update from amr with header id {header_id}: {request_body}')
    # 1. Determine current order state
    current_order_status = determine_order_status_from_amr_state(request_body)
    # 2. Get last order state
    if request_body.orderId != '':
        last_time_order_status = get_order_status(OrderInfoRequest(orderIds=[request_body.orderId])).json()

        if len(last_time_order_status) == 0 or last_time_order_status is None:
            raise Exception(f'No last time order status for order {request_body.orderId} available')
        # 3. If order state finish and different in compare to last time, the execute order finish request
        if (current_order_status == OrderStatus.FINISHED and
                OrderStatus(last_time_order_status[0]['orderStatus']) != OrderStatus.FINISHED):
            logger.info(f'Order Status {request_body.orderId} from AMR {request_body.amrId} finish.')
            order_finished_request = OrderFinishRequest(amrId=request_body.amrId, orderId=request_body.orderId)
            logger.info(f'Set order {request_body.orderId} of amr {request_body.amrId} in system state'
                        f' management to finish.')
            delete_finished_order_from_planned_order_list(order_finished_request)
            # deletes order in queue in system state management or dispatching
            # send end time to order management, important for token passing and the user interface
            order_update_request = OrderUpdateRequest(amrId=request_body.amrId, orderStatus=OrderStatus.FINISHED,
                                                      orderId=request_body.orderId,
                                                      estimatedEndTime=request_body.timestamp)
            set_order_update(order_update_request)

        # 4. AMR has already an order
        # Send order update to last dispatched order for considered amr
        order_update_request = OrderUpdateRequest(amrId=request_body.amrId, orderStatus=current_order_status,
                                                  orderId=request_body.orderId)
        set_order_update(order_update_request)
        # 8. If storage location tracking activated, set changes in storage location tracking
        if config.config_file.STORAGE_LOCATION_TRACKING is True:
            if (current_order_status == OrderStatus.PICKUP and  # for Pickup Action
                    OrderStatus(last_time_order_status[0]['orderStatus']) != OrderStatus.PICKUP):
                # get goal station for order, where the item must be delivered
                station_ids_order = get_goal_station_for_order(StationInfoRequest(orderId=request_body.orderId)).json()
                if station_ids_order['pickupStationId'][0] == 'S':
                    item_sku_info = get_item_sku_infos(OrderInfoRequest(orderIds=[request_body.orderId])).json()
                    # get sku id information of the item of the order
                    # retrieve item with sku id
                    retrieve_item_sku_response = retrieve_skus(SkusRetrieveRequestBody(
                        locationId=station_ids_order['pickupStationId'],
                        skuId=item_sku_info[0]['itemSkuId'],
                        retrievedAt=str(request_body.timestamp))).json()
                    # store retrieved item with sku id
                    store_sku_response = store_skus(SkusStoreRequestBody(locationId=request_body.amrId,
                                                                         skuId=retrieve_item_sku_response['skuId'],
                                                                         storedAt=str(request_body.timestamp))).json()
            elif (current_order_status == OrderStatus.DROPOFF and  # For Dropoff Action
                  OrderStatus(last_time_order_status[0]['orderStatus']) != OrderStatus.DROPOFF):
                station_ids_order = get_goal_station_for_order(StationInfoRequest(orderId=request_body.orderId)).json()
                if station_ids_order['dropoffStationId'][0] == 'S':
                    # get sku id information of the item of the order
                    item_sku_info = get_item_sku_infos(OrderInfoRequest(orderIds=[request_body.orderId])).json()
                    # retrieve item with sku id
                    retrieve_item_sku_response = retrieve_skus(SkusRetrieveRequestBody(locationId=request_body.amrId,
                                                                                       skuId=item_sku_info[0]['itemSkuId'],
                                                                                       retrievedAt=str(request_body.timestamp))).json()
                    # store retrieved item with sku id
                    store_sku_response = store_skus(SkusStoreRequestBody(locationId=station_ids_order['dropoffStationId'],
                                                                         skuId=retrieve_item_sku_response['skuId'],
                                                                         storedAt=str(request_body.timestamp))).json()
    # 5. Set system time update
    set_system_time(SystemTimeRequest(timestamp=request_body.timestamp))
    # 6. Update amr state
    set_amr_state(request_body)

    ################################################################################################################
    # ALTERNATIVE: TO GET A RESPONSE OF PLANNED ORDERS DEPENDING OF THE STATE UPDATE FROM THE AMR
    ################################################################################################################

    # 9. Check if response from system state update includes new orders for processing
    if ((config.config_file.LAST_HEADER_SIMULATION_STEP == header_id or config.config_file.AMR_SIMULATION_ACTIVE is False)
            and config.config_file.USE_MQTT is True):
        planned_orders_res = request_orders_for_amrs()
        if planned_orders_res is not None:
            planned_orders_res = planned_orders_res.json()
        else:
            planned_orders_res = None
        if planned_orders_res is not None:
            logger.debug(f'Order request response: {planned_orders_res}')
            if planned_orders_res['plannedOrders'] is not None:
                for response_obj in planned_orders_res['plannedOrders']:
                    # transform json in order amr request object
                    order_amr_request = process_next_order_in_queue(response_obj)
                    if order_amr_request.order.orderId != '':
                        # Only transformation from json to order object
                        logger.info(f'Planned order {order_amr_request.order.orderId} successfully sent to amr'
                                    f' {order_amr_request.amrId}, {request_body.amrId} at'
                                    f' timestamp {request_body.timestamp}!')
                        # send order amr request object via mqtt to simulation, robot or digital twin
                        mqtt_send_planned_order_to_amr(order_amr_request.order, order_amr_request.amrId,
                                                       order_amr_request.timestamp)
                        # Only if order id no reposition order
                        order_update_request = OrderUpdateRequest(amrId=order_amr_request.amrId,
                                                                  orderStatus=OrderStatus.PLANNED,
                                                                  orderId=order_amr_request.order.orderId,
                                                                  estimatedStartTime=order_amr_request.timestamp)
                        set_order_update(order_update_request)
    config.config_file.LAST_PROCESSED_HEADER = header_id
    return


def request_orders_for_amr():
    terminate = False
    planned_orders_res = request_orders_for_amrs()
    if planned_orders_res is not None:
        planned_orders_res = planned_orders_res.json()
    else:
        planned_orders_res = None
    order_list_response = []
    if planned_orders_res is not None:
        # logger.info(f'Order request response: {planned_orders_res}')
        terminate = planned_orders_res['terminate']
        if planned_orders_res['plannedOrders'] is not None:
            for response_obj in planned_orders_res['plannedOrders']:
                # transform json in order amr request object
                order_amr_request = process_next_order_in_queue(response_obj)
                if order_amr_request.order.orderId != '':
                    # Only transformation from json to order object
                    # send order amr request object via mqtt to simulation, robot or digital twin
                    timestamp = (order_amr_request.timestamp.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'))
                    order_update_obj = OrderUpdateVDABodyHeader(headerId=HEADER_ID, timestamp=timestamp,
                                                                version='v2', manufacturer='fzi',
                                                                serialNumber=order_amr_request.amrId,
                                                                orderId=order_amr_request.order.orderId,
                                                                orderUpdateId=order_amr_request.order.orderUpdateId,
                                                                nodes=order_amr_request.order.nodes,
                                                                edges=order_amr_request.order.edges)
                    order_list_response.append(order_update_obj)
                    order_update_request = OrderUpdateRequest(amrId=order_amr_request.amrId,
                                                              orderStatus=OrderStatus.PLANNED,
                                                              orderId=order_amr_request.order.orderId,
                                                              estimatedStartTime=order_amr_request.timestamp)
                    set_order_update(order_update_request)

    return order_list_response, terminate
