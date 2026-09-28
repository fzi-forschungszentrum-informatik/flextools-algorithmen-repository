import logging
##############################################################
# Base data management Service Configurations and Parameters #
##############################################################

###########################
# Start-Up Configurations #
###########################
PORT = 3005
HOST = '0.0.0.0'

SCENARIO_BASE_DATA_FILE = ''

LOAD_LAST_STATUS = True  # only possible, if database is not in in-memory status

##########################
# Logging Configurations #
##########################
LOGGING_LEVEL = logging.INFO
LOGGING_FILE = r'./base_data_management.log'
LOGGER_NAME = 'root'


#######################
# Test Configurations #
#######################
TEST_MODUS = False  # relevant for api tests
BASE_DATA_FILE_TEST = r'./tests/base_data_test/base_data.json'  # add point to run tests with code coverage manually!

###############################
# Microservice Configurations #
###############################

HOST_ADDRESS_BASEDATAMANAGEMENT = "http://127.0.0.1:" + str(PORT) + "/"
HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER = "http://basedatamanagement:" + str(PORT) + "/"
# Name of microservices in docker compose

###########################
# Database Configurations #
###########################

DATABASE_FILE = 'sqlite:///:memory:'  # For in-memory database
# DATABASE_FILE = 'sqlite:///database.db'  # For in operation modus with database to store data

