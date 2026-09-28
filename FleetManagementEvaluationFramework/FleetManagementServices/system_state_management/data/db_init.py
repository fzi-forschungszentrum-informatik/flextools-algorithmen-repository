import os

from api.api_config import app
from data.system_state_management_db import SystemStateManagementDb

###################
# Initialize data #
###################
database = {}


@app.on_event("startup")
async def startup_initialize_event():
    database['system_state_management'] = SystemStateManagementDb(os.environ['STATE_FILE'])
