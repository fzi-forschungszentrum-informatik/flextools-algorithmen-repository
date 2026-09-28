import logging
##########################################################
# Order Management Service Configurations and Parameters #
##########################################################

###########################
# Start-Up Configurations #
###########################
PORT = 3002
HOST = '0.0.0.0'

LOAD_LAST_STATUS = True  # only possible, if database is not in in-memory status

STORAGE_LOCATION_ALGORITHM = "random_pick"
STORAGE_LOCATION_TRACKING = False

##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./order_management.log'
LOGGER_NAME = 'root'

#######################
# Test Configurations #
#######################

TEST_ORDERS_FILE = r'./data/order_files_test/new_orders.json'  # add point to run tests with code coverage manually!

###############################
# Microservice Configurations #
###############################
PORT_TASK_ASSIGNMENT = 3000
PORT_AUTONOMOUS_DECISION_MAKING = 5001
PORT_STORAGE_LOCATION_TRACKING = 5000
PORT_SYSTEMSTATEMANAGEMENT = 3001

HOST_ADDRESS_ORDERMANAGEMENT = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_ORDERMANAGEMENT_DOCKER = "http://ordermanagement:" + str(PORT) + "/"  # Name of microservices in docker compose
HOST_ADDRESS_TASK_ASSIGNMENT = "http://127.0.0.1:" + str(PORT_TASK_ASSIGNMENT) + "/"
HOST_ADDRESS_TASK_ASSIGNMENT_DOCKER = "http://taskassignment:" + str(PORT_TASK_ASSIGNMENT) + "/"
HOST_ADDRESS_AUTONOMOUS_DECISION_MAKING = "http://localhost:" + str(PORT_AUTONOMOUS_DECISION_MAKING) + "/api/v1/"
HOST_ADDRESS_AUTONOMOUS_DECISION_MAKING_DOCKER = ("http://adm:" +
                                                  str(PORT_AUTONOMOUS_DECISION_MAKING) + "/api/v1/")
HOST_ADDRESS_STORAGE_LOCATION_TRACKING = "http://localhost:" + str(PORT_STORAGE_LOCATION_TRACKING) + "/api/v1/"
HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER = ("http://slt:" + str(PORT_STORAGE_LOCATION_TRACKING)
                                                 + "/api/v1/")
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT = "http://127.0.0.1:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"
HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER = "http://systemstatemanagement:" + str(PORT_SYSTEMSTATEMANAGEMENT) + "/"

###########################
# Database Configurations #
###########################

DATABASE_FILE = 'sqlite:///:memory:'  # For in-memory database
# DATABASE_FILE = 'sqlite:///database.db' # For in operation modus with database to store data
