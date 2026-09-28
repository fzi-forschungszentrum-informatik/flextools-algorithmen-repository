import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config_file import (PORT, HOST, HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER,
                                HOST_ADDRESS_AMRCOMMUNICATION_DOCKER, HOST_ADDRESS_PATHPLANNING_DOCKER,
                                HOST_ADDRESS_SYSTEMSTATEMANAGEMENT,
                                HOST_ADDRESS_AMRCOMMUNICATION, HOST_ADDRESS_PATHPLANNING, SYSTEM_STATE_FILE_TEST,
                                SYSTEM_STATE_FILE_SCENARIO,
                                HOST_ADDRESS_AMRSIMULATION_DOCKER, HOST_ADDRESS_AMRSIMULATION,
                                HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER,
                                HOST_ADDRESS_STORAGE_LOCATION_TRACKING, HOST_ADDRESS_TASKASSIGNMENT_DOCKER,
                                HOST_ADDRESS_TASKASSIGNMENT)
import config.config_file
from logic.general_functions import env_to_bool

###################################
# Host and Network Configurations #
###################################

port = PORT


def set_service_urls(test_mode: bool = False):  # in case the environment variables are not set by gitlab-ci.yml file
    ENV_DOCKER = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if ENV_DOCKER == "True":
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION_DOCKER
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = HOST_ADDRESS_PATHPLANNING_DOCKER
        if 'AMRSIMULATION_URL' not in os.environ:
            os.environ['AMRSIMULATION_URL'] = HOST_ADDRESS_AMRSIMULATION_DOCKER
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = HOST_ADDRESS_TASKASSIGNMENT_DOCKER
        if 'STORAGE_LOCATION_TRACKING_URL' not in os.environ:
            os.environ['STORAGE_LOCATION_TRACKING_URL'] = HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER
        config.config_file.SYSTEM_STATE_FILE_SCENARIO = os.environ['STATE_FILE']
        config.config_file.STORAGE_LOCATION_TRACKING = env_to_bool(os.environ['STORAGE_LOCATION_TRACKING'])
        config.config_file.SIMULATION_ACTIVE = env_to_bool(os.environ['SIMULATION_ACTIVE'])
    else:
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = HOST_ADDRESS_PATHPLANNING
        if 'AMRSIMULATION_URL' not in os.environ:
            os.environ['AMRSIMULATION_URL'] = HOST_ADDRESS_AMRSIMULATION
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = HOST_ADDRESS_TASKASSIGNMENT
        if 'STORAGE_LOCATION_TRACKING_URL' not in os.environ:
            os.environ['STORAGE_LOCATION_TRACKING_URL'] = HOST_ADDRESS_STORAGE_LOCATION_TRACKING
    if 'STATE_FILE' not in os.environ:
        if test_mode is True:
            os.environ['STATE_FILE'] = SYSTEM_STATE_FILE_TEST
        else:
            os.environ['STATE_FILE'] = SYSTEM_STATE_FILE_SCENARIO


#########################
# FastAPI Configuration #
#########################
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
