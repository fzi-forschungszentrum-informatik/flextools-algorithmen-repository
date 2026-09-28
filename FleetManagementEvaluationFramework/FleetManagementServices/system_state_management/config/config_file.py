import logging

from data.enums import TaskAssignmentStrategy, PathPlanningIntegration

#################################################################
# System State Management Service Configurations and Parameters #
#################################################################

###########################
# Start-Up Configurations #
###########################

PORT = 3001
HOST = '0.0.0.0'

SYSTEM_STATE_FILE_SCENARIO = ''

TASK_ASSIGNMENT_STRATEGY = TaskAssignmentStrategy.push_back
STORAGE_LOCATION_TRACKING = False

PATH_PLANNING_INTEGRATION = PathPlanningIntegration.two_stage

INFINITY_CONSTRAINT = False  # improves path planning speed with False
SIMULATION_ACTIVE = True

MAX_NUMBER_OF_FAILED_PATH_PLANNING = 10  # Termination condition MAPD Scenario

##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./system_state_management.log'
LOGGER_NAME = 'root'

#######################
# Test Configurations #
#######################

TEST_MODUS = False
SYSTEM_STATE_FILE_TEST = r'./tests/system_state_file_test/initial_state.json'
# add point to run tests with code coverage manually!

###############################
# Microservice Configurations #
###############################

PORT_AMRCOMMUNICATION = 3003
PORT_PATHPLANNING = 3006
PORT_AMRSIMULATION = 3011
PORT_TASKASSIGNMENT = 3000
PORT_STORAGE_LOCATION_TRACKING = 5000
PORT_STATISTICS_EVALUATION = 3012

HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT) + "/"
HOST_ADDRESS_AMRCOMMUNICATION = "http://127.0.0.1:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_AMRCOMMUNICATION_DOCKER = "http://amrcommunication:" + str(PORT_AMRCOMMUNICATION) + "/"
HOST_ADDRESS_PATHPLANNING = "http://127.0.0.1:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_PATHPLANNING_DOCKER = "http://pathplanning:" + str(PORT_PATHPLANNING) + "/"
HOST_ADDRESS_AMRSIMULATION = "http://127.0.0.1:" + str(PORT_AMRSIMULATION) + "/"
HOST_ADDRESS_AMRSIMULATION_DOCKER = "http://amrsimulation:" + str(PORT_AMRSIMULATION) + "/"
HOST_ADDRESS_TASKASSIGNMENT = "http://127.0.0.1:" + str(PORT_TASKASSIGNMENT) + "/"
HOST_ADDRESS_TASKASSIGNMENT_DOCKER = "http://taskassignment:" + str(PORT_TASKASSIGNMENT) + "/"
HOST_ADDRESS_STORAGE_LOCATION_TRACKING = "http://localhost:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/"
HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER = ("http://slt:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/")
HOST_ADDRESS_STATISTICS_EVALUATION = "http://127.0.0.1:" + str(PORT_STATISTICS_EVALUATION) + "/"
HOST_ADDRESS_STATISTICS_EVALUATION_DOCKER = ("http://statisticsevaluationservice:" + str(PORT_STATISTICS_EVALUATION) +
                                             "/")

