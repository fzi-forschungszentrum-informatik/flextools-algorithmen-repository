###################
# Initialize data #
###################
import config.config_file
from api.api_config import app
from data.models import ActionIdCounter
from logic.core.class_selection import get_dispatching_interface

task_assignment_strategies = {}


@app.on_event("startup")
async def startup_initialize_dispatching_strategies():
    action_id_counter = ActionIdCounter(nextActionId=1)
    dispatching_interface = get_dispatching_interface(action_id_counter)
    task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY] = dispatching_interface
