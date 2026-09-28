import logging

from data.enums import TaskAssignmentStrategy

########################################################
# AMR Simulation Service Configurations and Parameters #
########################################################

###########################
# Start-Up Configurations #
###########################
PORT = 3011
HOST = '0.0.0.0'
MQTT_BROKER_PORT = 1883
MQTT_RECONNECT_RETRIES = 3

USE_MQTT = False
SIMULATION_ACTIVE = True

INITIAL_STATE_FILE_SCENARIO = ''
CHECK_COLLISIONS = True
BATTERY_MAX_REACH_BY_INITIALIZATION = 10000.0
WAITING_TIME_ON_NODE = 1
TASK_ASSIGNMENT_STRATEGY = TaskAssignmentStrategy.central

VISUALIZE_SCENARIO = True
DEMO_BACKGROUND = False

DEMO_IMAGE = r'./visualization/vis_backgrounds/HollLayout.png'
DEMO_LENGTH = 60
DEMO_WIDTH = 37

##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./amr_simulation.log'
LOGGER_NAME = 'root'

AMR_STATISTIC_DATA_FILE = r'./statistic_data/amr_data.csv'
GRAPH_STATISTIC_DATA_FILE = r'./statistic_data/graph_data_50.csv'
#######################
# Test Configurations #
#######################
TEST_MODUS = False
CHARGE_MANAGEMENT_ACTIVE = False
INITIAL_STATE_FILE_TEST = r'./testing_data/logic_test/amrs.json'

###############################
# Microservice Configurations #
###############################
PORT_PATHPLANNING = 3006
PORT_BASEDATAMANAGEMENT = 3005
PORT_ORDERMANAGEMENT = 3002
PORT_AMRCOMMUNICATION = 3003
PORT_SYSTEMSTATEMANAGEMENT = 3001

HOST_ADDRESS_AMRSIMULATION = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_AMRSIMULATION_DOCKER = "http://amrsimulation:" + str(PORT) + "/"
HOST_ADDRESS_PATHPLANNING = "http://127.0.0.1:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_PATHPLANNING_DOCKER = "http://pathplanning:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT = "http://127.0.0.1:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER = "http://basedatamanagement:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_MQTT_BROKER = "127.0.0.1"
HOST_ADDRESS_MQTT_BROKER_DOCKER = "mqttbroker"
HOST_ADDRESS_ORDERMANAGEMENT = "http://127.0.0.1:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT_DOCKER = "http://ordermanagement:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_AMRCOMMUNICATION = "http://127.0.0.1:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_AMRCOMMUNICATION_DOCKER = "http://amrcommunication:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"


MQTT_RECEIVE_ORDER_TOPIC = "flextools/v2/fzi/new-order"
