import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config_file import PORT, HOST, HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER, HOST_ADDRESS_BASEDATAMANAGEMENT, \
    BASE_DATA_FILE_TEST, SCENARIO_BASE_DATA_FILE

###################################
# Host and Network Configurations #
###################################
port = PORT


def set_service_urls(test_mode: bool = False):  # in case the environment variables are not set by gitlab-ci.yml file
    ENV_DOCKER = os.environ.get('ENV_IN_DOCKER', False)
    if 'HOST' not in os.environ:
        os.environ['HOST'] = HOST
    if ENV_DOCKER == "True":
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = HOST_ADDRESS_BASEDATAMANAGEMENT_DOCKER
    else:
        if 'BASEDATAMANAGEMENT_URL' not in os.environ:
            os.environ['BASEDATAMANAGEMENT_URL'] = HOST_ADDRESS_BASEDATAMANAGEMENT
    if 'BASE_DATA_FILE' not in os.environ:
        if test_mode is True:
            os.environ['BASE_DATA_FILE'] = BASE_DATA_FILE_TEST
        else:
            os.environ['BASE_DATA_FILE'] = SCENARIO_BASE_DATA_FILE

#########################
# FastAPI Configuration #
#########################

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
