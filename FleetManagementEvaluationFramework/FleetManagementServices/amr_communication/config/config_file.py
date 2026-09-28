import logging
##########################################################
# AMRCommunication Service Configurations and Parameters #
##########################################################

###########################
# Start-Up Configurations #
###########################
PORT = 3003
HOST = '0.0.0.0'
MQTT_BROKER_PORT = '1883'
MQTT_RECONNECT_RETRIES = 3

STORAGE_LOCATION_TRACKING = False

#############################
# Simulation Configurations #
#############################
# Parameter setting automatic, no configuration
LAST_PROCESSED_HEADER = 0
LAST_HEADER_SIMULATION_STEP = None

AMR_SIMULATION_ACTIVE = True
USE_MQTT = False
##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./amr_communication.log'
LOGGER_NAME = 'root'

###############################
# Microservice Configurations #
###############################

PORT_SYSTEMSTATEMANAGEMENT = 3001
PORT_ORDERMANAGEMENT = 3002
PORT_AMRSIMULATION = 3011
PORT_STATISTICS_EVALUATION = 3012
PORT_STORAGE_LOCATION_TRACKING = 5000

HOST_ADDRESS_AMRCOMMUNICATION = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_AMRCOMMUNICATION_DOCKER = "http://amrcommunication:" + str(PORT) + "/"  # Name of microservices in docker compose
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT = "http://127.0.0.1:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT_DOCKER = "http://ordermanagement:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_AMRSIMULATION = "http://127.0.0.1:" + str(PORT_AMRSIMULATION) + "/"
HOST_ADDRESS_AMRSIMULATION_DOCKER = "http://amrsimulation:" + str(PORT_AMRSIMULATION) + "/"
HOST_ADDRESS_MQTT_BROKER = "127.0.0.1"
HOST_ADDRESS_MQTT_BROKER_DOCKER = "mqttbroker"
HOST_ADDRESS_STATISTICS_EVALUATION = "http://127.0.0.1:" + str(PORT_STATISTICS_EVALUATION) + "/"
HOST_ADDRESS_STATISTICS_EVALUATION_DOCKER = ("http://statisticsevaluationservice:" + str(PORT_STATISTICS_EVALUATION) +
                                             "/")
HOST_ADDRESS_STORAGE_LOCATION_TRACKING = "http://localhost:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/"
HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER = ("http://slt:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/")

MQTT_ORDER_TOPIC = ""
MQTT_CONNECTION_TOPIC = "flextools/v2/fzi/+/connection"
MQTT_STATE_TOPIC = "flextools/v2/fzi/+/state"
