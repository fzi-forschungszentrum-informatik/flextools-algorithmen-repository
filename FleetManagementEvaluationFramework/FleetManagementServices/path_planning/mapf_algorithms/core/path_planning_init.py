import os

from api.api_config import app
from mapf_algorithms.methods.class_selection import get_path_planning_interface, get_heuristic_interface
from mapf_algorithms.core.path_planning_obj import PathPlanningObj
import config.config_file

###################
# Initialize data #
###################
path_planning_strategies = {}


@app.on_event("startup")
async def startup_initialize_event():
    path_planning_interface = get_path_planning_interface()
    heuristic_interface = get_heuristic_interface()
    path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY] = PathPlanningObj(
        os.environ['LIF_FILE'],
        path_planning_interface,
        heuristic_interface
    )

