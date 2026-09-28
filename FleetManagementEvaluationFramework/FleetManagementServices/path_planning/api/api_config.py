import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.config_file import PORT, SCENARIO_LIF_FILE, TEST_LIF_FILE, HOST
import config.config_file
from mapf_algorithms.api_services.general_functions import env_to_bool

###################################
# Host and Network Configurations #
###################################
port = PORT


def set_service_urls(test_mode: bool = False):  # in case the environment variables are not set by gitlab-ci.yml file
    env_docker = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if env_docker == "True":
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = config.config_file.HOST_ADDRESS_PATHPLANNING_DOCKER
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_SYSTEMSTATEMANAGEMENT_DOCKER
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = config.config_file.HOST_ADDRESS_TASK_ASSIGNMENT_DOCKER
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_ORDERMANAGEMENT_DOCKER
        config.config_file.PATH_PLANNING_STRATEGY = os.environ['PATH_PLANNING_STRATEGY']
        config.config_file.CBS_COST_FUNCTION_IMPROVEMENT = True
        if 'DIRECTED_GRAPH' in os.environ:
            config.config_file.DIRECTED_GRAPH = env_to_bool(os.environ['DIRECTED_GRAPH'])
    else:
        if 'PATHPLANNING_URL' not in os.environ:
            os.environ['PATHPLANNING_URL'] = config.config_file.HOST_ADDRESS_PATHPLANNING
        if 'SYSTEMSTATEMANAGEMENT_URL' not in os.environ:
            os.environ['SYSTEMSTATEMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_SYSTEMSTATEMANAGEMENT
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_BASEDATAMANAGEMENT
        if 'TASKASSIGNMENT_URL' not in os.environ:
            os.environ['TASKASSIGNMENT_URL'] = config.config_file.HOST_ADDRESS_TASK_ASSIGNMENT
        if 'ORDERMANAGEMENT_URL' not in os.environ:
            os.environ['ORDERMANAGEMENT_URL'] = config.config_file.HOST_ADDRESS_ORDERMANAGEMENT
    if 'LIF_FILE' not in os.environ:
        if test_mode is True:
            os.environ['LIF_FILE'] = TEST_LIF_FILE
        else:
            os.environ['LIF_FILE'] = SCENARIO_LIF_FILE


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
