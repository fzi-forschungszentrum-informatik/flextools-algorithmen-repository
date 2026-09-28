import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mqtt import MQTTConfig, FastMQTT

from config.config_file import HOST, PORT, MQTT_BROKER_PORT, MQTT_RECONNECT_RETRIES, HOST_ADDRESS_MQTT_BROKER, \
    HOST_ADDRESS_AMRSIMULATION, HOST_ADDRESS_MQTT_BROKER_DOCKER, HOST_ADDRESS_AMRSIMULATION_DOCKER, \
    HOST_ADDRESS_PATHPLANNING, HOST_ADDRESS_PATHPLANNING_DOCKER, HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER, \
    HOST_ADDRESS_BASEDATAMANAGEMENT, TEST_MODUS, HOST_ADDRESS_ORDERMANAGEMENT_DOCKER, HOST_ADDRESS_ORDERMANAGEMENT, \
    HOST_ADDRESS_AMRCOMMUNICATION_DOCKER, HOST_ADDRESS_AMRCOMMUNICATION,HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER, \
    HOST_ADDRESS_SYSTEMSTATEMANAGEMENT
import config.config_file
from logic.general_functions import env_to_bool

###################################
# Host and Network Configurations #
###################################
host = HOST
port = PORT
mqtt_broker_port = MQTT_BROKER_PORT


def set_service_urls():  # in case the environment variables are not set by gitlab-ci.yml file
    ENV_DOCKER = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if 'MQTT_RECEIVE_ORDER_TOPIC' not in os.environ:
        os.environ['MQTT_RECEIVE_ORDER_TOPIC'] = config.config_file.MQTT_RECEIVE_ORDER_TOPIC
    if ENV_DOCKER == "True":
        if 'AMRSIMULATION_URL' not in os.environ:
            os.environ['AMRSIMULATION_URL'] = HOST_ADDRESS_AMRSIMULATION_DOCKER
        if 'MQTTBROKER_HOST' not in os.environ:
            os.environ['MQTTBROKER_HOST'] = HOST_ADDRESS_MQTT_BROKER_DOCKER
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = HOST_ADDRESS_PATHPLANNING_DOCKER
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT_DOCKER
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION_DOCKER
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER
        config.config_file.INITIAL_STATE_FILE_SCENARIO = os.environ['SYSTEM_STATE_FILE']
        config.config_file.CHECK_COLLISIONS = env_to_bool(os.environ['COLLISION_DETECTION'])
        if 'CHARGE_MANAGEMENT_ACTIVE' not in os.environ:
            config.config_file.CHARGE_MANAGEMENT_ACTIVE = False
        else:
            config.config_file.CHARGE_MANAGEMENT_ACTIVE = env_to_bool(os.environ['CHARGE_MANAGEMENT_ACTIVE'])
        if 'USE_MQTT' in os.environ:
            config.config_file.USE_MQTT = env_to_bool(os.environ['USE_MQTT'])
        if 'SIMULATION_ACTIVE' in os.environ:
            config.config_file.SIMULATION_ACTIVE = env_to_bool(os.environ['SIMULATION_ACTIVE'])
    else:
        if 'AMRSIMULATION_URL' not in os.environ:
            os.environ['AMRSIMULATION_URL'] = HOST_ADDRESS_AMRSIMULATION
        if 'MQTTBROKER_HOST' not in os.environ:
            os.environ['MQTTBROKER_HOST'] = HOST_ADDRESS_MQTT_BROKER
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = HOST_ADDRESS_PATHPLANNING
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = HOST_ADDRESS_BASEDATAMANAGEMENT
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT
    if 'TEST_MODUS' not in os.environ:
        os.environ['TEST_MODUS'] = str(TEST_MODUS)


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
    port=mqtt_broker_port,
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
