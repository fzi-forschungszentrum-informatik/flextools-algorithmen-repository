########################################################
# User Interface Service Configurations and Parameters #
########################################################
import logging

###########################
# Start-Up Configurations #
###########################
PORT = 3010
HOST = '0.0.0.0'


MAP_ID_DEFAULT = 'map1'  # Is set automatically

STORAGE_LOCATION_TRACKING = False
SIMULATION_ACTIVE = True
MAX_SPEED_EDGE = 1

MAX_EVALUATION_TIME = 3600

##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./user_interface.log'
LOGGER_NAME = 'root'

###############################
# Microservice Configurations #
###############################
PORT_SYSTEMSTATEMANAGEMENT = 3001
PORT_PATHPLANNING = 3006
PORT_ORDERMANAGEMENT = 3002
PORT_AMRSIMULATION = 3011
PORT_BASEDATAMANAGEMENT = 3005
PORT_TASK_ASSIGNMENT = 3000
PORT_AMRCOMMUNICATION = 3003
PORT_STORAGE_LOCATION_TRACKING = 5000

HOST_ADDRESS_ORDERMANAGEMENT = "http://127.0.0.1:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT_DOCKER = "http://ordermanagement:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_PATHPLANNING = "http://127.0.0.1:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_PATHPLANNING_DOCKER = "http://pathplanning:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_AMRSIMULATION = "http://127.0.0.1:" + str(PORT_AMRSIMULATION) + "/"
HOST_ADDRESS_AMRSIMULATION_DOCKER = "http://amrsimulation:" + str(PORT_AMRSIMULATION) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT = "http://127.0.0.1:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER = "http://basedatamanagement:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_TASK_ASSIGNMENT = "http://127.0.0.1:" + str(PORT_TASK_ASSIGNMENT) + "/"
HOST_ADDRESS_TASK_ASSIGNMENT_DOCKER = "http://taskassignment:" + str(PORT_TASK_ASSIGNMENT) + "/"
HOST_ADDRESS_AMRCOMMUNICATION = "http://127.0.0.1:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_AMRCOMMUNICATION_DOCKER = "http://amrcommunication:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_STORAGE_LOCATION_TRACKING = "http://localhost:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/"
HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER = ("http://slt:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/")