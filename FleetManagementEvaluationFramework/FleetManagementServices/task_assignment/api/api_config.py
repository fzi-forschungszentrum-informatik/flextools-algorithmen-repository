import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config_file import (PORT, HOST, HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER,
                                HOST_ADDRESS_AMRCOMMUNICATION_DOCKER, HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER,
                                HOST_ADDRESS_PATHPLANNING_DOCKER, HOST_ADDRESS_TASKASSIGNMENT_DOCKER,
                                HOST_ADDRESS_SYSTEMSTATEMANAGEMENT, HOST_ADDRESS_AMRCOMMUNICATION,
                                HOST_ADDRESS_BASEDATAMANAGEMENT, HOST_ADDRESS_PATHPLANNING, HOST_ADDRESS_TASKASSIGNMENT,
                                HOST_ADDRESS_ORDERMANAGEMENT_DOCKER, HOST_ADDRESS_ORDERMANAGEMENT)
import config.config_file
from logic.api_services.general_functions import env_to_bool

###################################
# Host and Network Configurations #
###################################
port = PORT


def set_service_urls():  # in case the environment variables are not set by gitlab-ci.yml file
    ENV_DOCKER = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if ENV_DOCKER == "True":
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION_DOCKER
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = HOST_ADDRESS_PATHPLANNING_DOCKER
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = HOST_ADDRESS_TASKASSIGNMENT_DOCKER
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT_DOCKER
        # Set default parameters from docker .env file
        config.config_file.TASK_ASSIGNMENT_STRATEGY = os.environ['TASK_ASSIGNMENT_STRATEGY']
        config.config_file.USE_IMPROVEMENT = env_to_bool(os.environ['USE_IMPROVEMENT'])
    else:
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = HOST_ADDRESS_SYSTEMSTATEMANAGEMENT
        if 'AMRCOMMUNICATION_URL' not in os.environ:
            os.environ['AMRCOMMUNICATION_URL'] = HOST_ADDRESS_AMRCOMMUNICATION
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = HOST_ADDRESS_BASEDATAMANAGEMENT
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = HOST_ADDRESS_PATHPLANNING
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = HOST_ADDRESS_TASKASSIGNMENT
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT


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
