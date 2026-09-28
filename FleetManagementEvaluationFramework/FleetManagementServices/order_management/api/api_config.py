import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config_file import HOST, PORT, HOST_ADDRESS_ORDERMANAGEMENT, HOST_ADDRESS_TASK_ASSIGNMENT, \
    HOST_ADDRESS_ORDERMANAGEMENT_DOCKER, HOST_ADDRESS_TASK_ASSIGNMENT_DOCKER, \
    HOST_ADDRESS_AUTONOMOUS_DECISION_MAKING_DOCKER, HOST_ADDRESS_AUTONOMOUS_DECISION_MAKING, \
    HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER, HOST_ADDRESS_STORAGE_LOCATION_TRACKING
import config.config_file
from logic.general_functions import env_to_bool

###################################
# Host and Network Configurations #
###################################

port = PORT


def set_service_urls():  # in case the environment variables are not set by gitlab-ci.yml file
    ENV_DOCKER = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if ENV_DOCKER == "True":
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = HOST_ADDRESS_TASK_ASSIGNMENT_DOCKER
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT_DOCKER
        if 'AUTONOMOUS_DECISION_MAKING_URL' not in os.environ:
            os.environ['AUTONOMOUS_DECISION_MAKING_URL'] = HOST_ADDRESS_AUTONOMOUS_DECISION_MAKING_DOCKER
        if 'STORAGE_LOCATION_TRACKING_URL' not in os.environ:
            os.environ['STORAGE_LOCATION_TRACKING_URL'] = HOST_ADDRESS_STORAGE_LOCATION_TRACKING_DOCKER
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER
        config.config_file.STORAGE_LOCATION_TRACKING = env_to_bool(os.environ['STORAGE_LOCATION_TRACKING'])
    else:
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = HOST_ADDRESS_TASK_ASSIGNMENT
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = HOST_ADDRESS_ORDERMANAGEMENT
        if 'AUTONOMOUS_DECISION_MAKING_URL' not in os.environ:
            os.environ['AUTONOMOUS_DECISION_MAKING_URL'] = HOST_ADDRESS_AUTONOMOUS_DECISION_MAKING
        if 'STORAGE_LOCATION_TRACKING_URL' not in os.environ:
            os.environ['STORAGE_LOCATION_TRACKING_URL'] = HOST_ADDRESS_STORAGE_LOCATION_TRACKING
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_SYSTEMSTATEMANAGEMENT

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