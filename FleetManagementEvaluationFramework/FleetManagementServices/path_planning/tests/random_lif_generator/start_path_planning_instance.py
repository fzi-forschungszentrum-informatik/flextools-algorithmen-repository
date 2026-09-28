import json
import logging
import time

from intervaltree import IntervalTree
import config.config_file
from api.server_api_models import LIFObject
from config.config_file import PATH_PLANNING_STRATEGY
from mapf_algorithms.collision_detection.constraints_structure.constraints3d import Constraints3D

from tests.random_lif_generator.lif_generation_config import GENERATE_NEW_DATA, LIF_PATH, SHOW_LIF, PATH_PAIRS_FILE, \
    TEST_PP_LAYOUT_ID
from data.enums import PathPlanningStrategy


from mapf_algorithms.core.path_planning_obj import PathPlanningObj
from mapf_algorithms.methods.class_selection import get_path_planning_interface, get_heuristic_interface
from tests.random_lif_generator.lif_generator import create_lif
from tests.random_lif_generator.lif_show import show_lif, show_lif_animated2, show_lif_animated

from config.config_file import LOGGER_NAME
import log_config.log

logger = log_config.log.set_logger(LOGGER_NAME)

########################################################################################################################

def main():
    if GENERATE_NEW_DATA:
        # 1. Generate lif routing graph and start-goal node pairs
        starts, ends, constraints = create_lif(LIF_PATH)
    else:
        # 2. Load existing node pairs from file
        with open(PATH_PAIRS_FILE, "r") as f:
            pair_data = json.load(f)
            starts = pair_data["start_nodes"]
            ends = pair_data["end_nodes"]
            try:
                constraints = pair_data["constraints"]
            except:
                constraints = set()
    if SHOW_LIF:
        show_lif(LIF_PATH)

    ####################################################################################################################
    # get interfaces, from config file
    ####################################################################################################################
    path_planning_interface = get_path_planning_interface()
    heuristic_interface = get_heuristic_interface()

    tt_obj = PathPlanningObj(
        '',
        path_planning_interface,
        heuristic_interface
    )
    ####################################################################################################################
    # load the LIF-object
    ####################################################################################################################
    with open(LIF_PATH, "r") as f:
        lif_data = json.load(f)

    lif_obj = LIFObject(**lif_data)
    tt_obj.set_layout(lif_obj)

    constraints_set = {
        (node, tuple(value) if isinstance(value, list) else value)
        for node, value in constraints
    }

    paths, costs, path_constraints = tt_obj.compute_path(
        layout_id=TEST_PP_LAYOUT_ID,
        start_node_ids=starts,
        end_node_ids=ends,
        constraints=None,
        tokens=None
    )

    if isinstance(path_constraints, Constraints3D):
        type = 0
        raw_constraints = path_constraints.get_constraints()
    elif isinstance(path_constraints, set):
        # for discrete
        type = 1
        try:
            pre = [(object, interval) for (object , interval) in path_constraints]
        except:
            pre = [(object, interval) for (object, interval, _) in path_constraints]
        raw_constraints = list()
        for o, i in pre:
            if isinstance(o, tuple):
                eid = tt_obj.exgraph[TEST_PP_LAYOUT_ID].get_edge_id([o[0], o[1]])
                raw_constraints.append((eid, (i, i + 1)))
            else:
                raw_constraints.append((o, (i, i+0.001)))
    elif isinstance(path_constraints, dict):
        # for interval with id blocking
        type = 1
        raw_constraints = []
        for oid, itr in path_constraints.items():
            itree: IntervalTree = itr
            for interval in itree.all_intervals:
                raw_constraints.append((oid, (interval.begin, interval.end)))
    else:
        type = -1
        raw_constraints = list()
    if SHOW_LIF:
        logger.info(f'Paths: {paths}')
        if paths is not None:
            if (PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs or
                    PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs):
                show_lif_animated2(LIF_PATH, paths, raw_constraints, type)
            else:
                show_lif_animated(LIF_PATH, paths, raw_constraints, type )


if __name__ == "__main__":
    start = time.time()
    main()
    logger.info(f'Computational Time: {time.time() - start}')















































