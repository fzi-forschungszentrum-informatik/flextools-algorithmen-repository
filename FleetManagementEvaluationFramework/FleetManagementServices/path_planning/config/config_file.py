import logging

from data.enums import PathPlanningStrategy, PathPlanningHeuristic, ECBSHeuristic, CostFunction, \
    CollisionDetectionStrategy

####################################################
# Traveltime Service Configurations and Parameters #
####################################################

###########################
# Start-Up Configurations #
###########################
PORT = 3006
HOST = '0.0.0.0'

MAX_TIME_ROUTING = 190
MAX_TIME_CBS = 180  # seconds
MAX_GENERATED_NODES_CBS = 9999999999999
MAX_A_STAR_TIME = 10  # seconds
SCENARIO_LIF_FILE = ''

PATH_PLANNING_STRATEGY = PathPlanningStrategy.dijkstra
PATH_PLANNING_HEURISTIC = PathPlanningHeuristic.euclidean  # For a star
COLLISION_DETECTION_STRATEGY = CollisionDetectionStrategy.classical_discrete_id

OPTIMALITY_BOUND = 1.3
ECBS_HEURISTIC = ECBSHeuristic.h1
FOCAL_RANDOM_SEED = 42
H4_MULT = 3
EIG_ALPHA = 1
EIG_BETA = 0.9

DIRECTED_GRAPH = False

COST_FUNCTION = CostFunction.sum_of_costs

DURATION_EDGE = 1
MAX_SPEED_EDGE = 1
AMR_RADIUS = 0.4

CBS_COST_FUNCTION_IMPROVEMENT = False
PATH_POST_PROCESSING = False

#######################
# Statistic Parameter #
#######################

REAL_TIME_ROUTING_THRESHOLD = 1


##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./path_planning.log'
LOGGER_NAME = 'root'

#######################
# Test Configurations #
#######################
TEST_MODUS = False
TEST_LIF_FILE = r'./tests/test_data/LIF_test.json'
TEST_LIF_FILE_MAPF = r'./tests/test_data/LIF_4_4_MAPF.json'
TEST_LIF_FILE_WAREHOUSE = r'./tests/test_data/LIF_14_5_MAPF.json'

###############################
# Microservice Configurations #
###############################
PORT_BASEDATAMANAGEMENT = 3005
PORT_SYSTEMSTATEMANAGEMENT = 3001
PORT_ORDERMANAGEMENT = 3002
PORT_TASKASSIGNMENT = 3000

HOST_ADDRESS_PATHPLANNING = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_PATHPLANNING_DOCKER = "http://pathplanning:" + str(PORT) + "/"  # Name of microservices in docker compose
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT = "http://127.0.0.1:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER = "http://basedatamanagement:" + str(PORT_BASEDATAMANAGEMENT) + "/"
HOST_ADDRESS_TASK_ASSIGNMENT = "http://127.0.0.1:" + str(PORT_TASKASSIGNMENT) + "/"
HOST_ADDRESS_TASK_ASSIGNMENT_DOCKER = "http://taskassignment:" + str(PORT_TASKASSIGNMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT = "http://127.0.0.1:" + str(PORT_ORDERMANAGEMENT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT_DOCKER = "http://ordermanagement:" + str(PORT_ORDERMANAGEMENT) + "/"
