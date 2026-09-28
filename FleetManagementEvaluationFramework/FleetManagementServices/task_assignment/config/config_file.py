import logging

from data.enums import TaskAssignmentStrategy

#####################################################
# Dispatching Service Configurations and Parameters #
#####################################################

###########################
# Start-Up Configurations #
###########################
PORT = 3000
HOST = '0.0.0.0'


TASK_ASSIGNMENT_STRATEGY = TaskAssignmentStrategy.push_back
USE_IMPROVEMENT = True  # 2-opt
MAX_IMPROVEMENT_TIME = 2  # s

BUFFER_TIME_PRO_ORDER = 0  # s

##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./taskassignment.log'
LOGGER_NAME = 'root'


###############################
# Microservice Configurations #
###############################

PORT_SYSTEMSTATEMANAGEMENT = 3001
PORT_AMRCOMMUNICATION = 3003
PORT_BASEDATAMANAGEMENT = 3005
PORT_PATHPLANNING = 3006
PORT_ORDERMANAGEMENT = 3002

HOST_ADDRESS_TASKASSIGNMENT = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_TASKASSIGNMENT_DOCKER = "http://taskassignment:" + str(PORT) + "/"  # Name of microservices in docker compose
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_AMRCOMMUNICATION = "http://127.0.0.1:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_AMRCOMMUNICATION_DOCKER = "http://amrcommunication:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT = "http://127.0.0.1:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER = "http://basedatamanagement:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_PATHPLANNING = "http://127.0.0.1:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_PATHPLANNING_DOCKER = "http://pathplanning:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_ORDERMANAGEMENT = "http://127.0.0.1:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT_DOCKER = "http://ordermanagement:" + str(PORT_ORDERMANAGEMENT) + "/"

###############################
# Test Configurations #
###############################

TASK_ASSIGNMENT_STRATEGY_GREEDY = 'greedy'
TASK_ASSIGNMENT_STRATEGY_PUSHBACK = 'push-back'
